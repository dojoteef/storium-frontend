"""
Story preprocessing tasks
"""
from typing import cast, Any, Dict
from databases import Database
from asgiref.sync import async_to_sync
from celery.utils.log import get_task_logger

from woolgatherer.tasks import app
from woolgatherer.utils.settings import Settings
from woolgatherer.db_models.storium import Story


logger = get_task_logger(__name__)


async def _process(story_id: str):
    """ Do the actual processing... """
    async with Database(Settings.dsn) as db:
        story = await Story.select(db, where={"hash": story_id})
        if story:
            story_dict = cast(Dict[str, Any], story.story)
            logger.info(
                "Processed story=%s, game_pid=%s", story_id, story_dict["game_pid"]
            )


@app.task
def process(story_id: str):
    """ Preprocess a story """
    async_to_sync(_process)(story_id)
