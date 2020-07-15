"""
Story preprocessing tasks
"""
from asyncio import as_completed
from typing import Any, Dict, List

from aiohttp import ClientSession
from databases import Database
from asgiref.sync import async_to_sync
from celery.schedules import crontab
from celery.utils.log import get_task_logger

from woolgatherer.db_models.storium import Story, StoryStatus
from woolgatherer.db_models.figmentator import Figmentator, FigmentatorForStory
from woolgatherer.ops import figmentator as figmentator_ops
from woolgatherer.ops import stories as story_ops  # pylint:disable=cyclic-import
from woolgatherer.tasks import app
from woolgatherer.utils.settings import Settings


logger = get_task_logger(__name__)


async def _process(story_id: str, figmentators: List[Figmentator]):
    """ Do the actual processing... """
    async with Database(Settings.dsn) as db:
        where = {"hash": story_id}
        story = await Story.select(db, where=where)
        if not story:
            # This either means we incorrectly added a task before putting the story
            # into the database, we cannot access the database, or something very bad
            # happened, like dropping entries from the database...
            raise LookupError(f"Cannot find story for id={story_id}!")

        async with ClientSession() as session:
            requests = []
            context = {"story_id": story.hash, "story": story.story}
            for figmentator in figmentators:
                requests.append(
                    figmentator_ops.preprocess(context, figmentator, session=session)
                )

            story.status = StoryStatus.ready
            for result in as_completed(requests):
                completed, figmentator = await result
                if completed:
                    await FigmentatorForStory(
                        model_id=figmentator.id, story_hash=story_id
                    ).insert(db)
                else:
                    story.status = StoryStatus.failed

        await story.update(db, where=where)
        logger.info("Processed story=%s, status=%s", story_id, story.status)


async def _cleanup_stories():
    """ Do the actual cleanup... """
    async with Database(Settings.dsn) as db:
        await story_ops.cleanup_stories(db=db)


@app.task(
    autoretry_for=(LookupError,), retry_kwargs={"max_retries": 3}, retry_backoff=0.25
)
def process(story_id: str, figmentators: List[Dict[str, Any]]):
    """ Preprocess a story """
    async_to_sync(_process)(story_id, [Figmentator(**f) for f in figmentators])


@app.task
def cleanup_stories():
    """ Cleanup unused stories """
    async_to_sync(_cleanup_stories)()


@app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):  # pylint:disable=unused-argument
    """ Schedules periodic tasks """
    # Executes every day at midnight
    sender.add_periodic_task(crontab(hour=0, minute=0), cleanup_stories.s())
