"""
Suggestion tasks
"""
from databases import Database
from asgiref.sync import async_to_sync
from celery.utils.log import get_task_logger

from woolgatherer.tasks import app
from woolgatherer.utils.settings import Settings
from woolgatherer.db_models.suggestion import (
    Suggestion,
    SuggestionStatus,
    SuggestionType,
)


logger = get_task_logger(__name__)


async def _create(story_id: str, suggestion_type: SuggestionType):
    """ Do the actual processing... """
    async with Database(Settings.dsn) as db:
        where = {"story_hash": story_id, "type": suggestion_type}
        suggestion = await Suggestion.select(db, where=where)
        if suggestion:
            suggestion.status = SuggestionStatus.done
            await suggestion.update(db, where=where)
            logger.info("Generated suggestion=%s", story_id)


@app.task
def create(story_id: str, suggestion_type: SuggestionType):
    """ Create a suggestion """
    async_to_sync(_create)(story_id, suggestion_type)
