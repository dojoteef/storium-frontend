"""
Story preprocessing tasks
"""
from databases import Database
from asgiref.sync import async_to_sync
from celery.utils.log import get_task_logger

from woolgatherer.tasks import app
from woolgatherer.utils.settings import Settings
from woolgatherer.db_models.storium import Story, StoryStatus


logger = get_task_logger(__name__)


async def _process(story_id: str):
    """ Do the actual processing... """
    async with Database(Settings.dsn) as db:
        where = {"hash": story_id}
        story = await Story.select(db, where=where)
        if story:
            story.status = StoryStatus.ready
            await story.update(db, where=where)
            logger.info("Processed story=%s", story_id)


@app.task
def process(story_id: str):
    """ Preprocess a story """
    async_to_sync(_process)(story_id)
