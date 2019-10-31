"""
Story preprocessing tasks
"""
from asyncio import as_completed
from typing import Any, Dict, List

from aiohttp import ClientSession
from databases import Database
from asgiref.sync import async_to_sync
from celery.utils.log import get_task_logger

from woolgatherer.db_models.storium import Story, StoryStatus
from woolgatherer.db_models.reverie import Reverie, ReverieForStory
from woolgatherer.tasks import app
from woolgatherer.utils.settings import Settings


logger = get_task_logger(__name__)


async def _process(story_id: str, reveries: List[Reverie]):
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
            for reverie in reveries:
                requests.append(reverie.preprocess(session))

            story.status = StoryStatus.ready
            for result in as_completed(requests):
                completed, reverie = await result
                if completed:
                    await ReverieForStory(
                        model_id=reverie.id, story_hash=story_id
                    ).insert(db)
                else:
                    story.status = StoryStatus.failed

        await story.update(db, where=where)
        logger.info("Processed story=%s, status=%s", story_id, story.status)


@app.task
def process(story_id: str, reveries: List[Dict[str, Any]]):
    """ Preprocess a story """
    async_to_sync(_process)(story_id, [Reverie(**r) for r in reveries])
