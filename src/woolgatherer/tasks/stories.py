"""
Story preprocessing tasks
"""
from typing import Any, Dict

from asgiref.sync import async_to_sync
from celery.utils.log import get_task_logger

from woolgatherer.tasks import app
from woolgatherer.db.session import get_async_db
from woolgatherer.db_models.storium import Story


logger = get_task_logger(__name__)


async def _process(story_id: str):
    """ Do the actual processing... """
    async with get_async_db() as db:
        story = await Story.select(db, where={"hash": story_id})
        if story:
            logger.info("Processed story=%s, game_pid=%s", story_id, str(story))


@app.task
def process(story_id: str, story_dict: Dict[str, Any]):
    """ Preprocess a story """
    async_to_sync(_process)(story_id)
