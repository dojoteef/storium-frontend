"""
Suggestion tasks
"""
from asyncio import gather
from typing import Any, Dict

from aiohttp import ClientSession
from databases import Database
from asgiref.sync import async_to_sync
from celery.utils.log import get_task_logger
from pydantic import ValidationError

from woolgatherer.db_models.figmentator import Figmentator, FigmentatorForStory
from woolgatherer.db_models.suggestion import (
    Suggestion,
    SuggestionStatus,
    SuggestionType,
)
from woolgatherer.errors import ProcessingError
from woolgatherer.tasks import app
from woolgatherer.models.storium import SceneEntry
from woolgatherer.ops import figmentator as figmentator_ops
from woolgatherer.utils.settings import Settings
from woolgatherer.db.utils import json_dumps


logger = get_task_logger(__name__)


async def _create(story_id: str, context_hash: str, suggestion_type: SuggestionType):
    """ Do the actual processing... """
    async with Database(Settings.dsn) as db:
        logger.debug("Setting up suggestion creation=%s", story_id)
        where = {
            "story_hash": story_id,
            "type": suggestion_type,
            "context_hash": context_hash,
        }
        suggestion, figmentator_mapping = await gather(
            Suggestion.select(db, where=where),
            FigmentatorForStory.select(db, where={"story_hash": story_id}),
        )

        if not suggestion:
            raise ProcessingError("Cannot find suggestion")

        if not figmentator_mapping:
            raise ProcessingError("Cannot find figmentator for story")

        figmentator = await Figmentator.select(
            db, where={"id": figmentator_mapping.model_id}
        )
        if not figmentator:
            raise ProcessingError("Cannot find figmentator")

        suggestion.status = SuggestionStatus.executing
        await suggestion.update(db)

        figmentate.delay(suggestion.dict(), figmentator.dict())


async def _figmentate(suggestion: Suggestion, figmentator: Figmentator):
    async with ClientSession(json_serialize=json_dumps) as session:
        status, entry = await figmentator_ops.figmentate(
            suggestion, figmentator, session=session
        )
        logger.debug("Received figmentator response (status=%s)", status)
        async with Database(Settings.dsn) as db:
            if status >= 200 and status < 300:
                try:
                    suggestion.generated = SceneEntry(**entry)
                except ValidationError:
                    raise ProcessingError(
                        "Invalid suggestion received from figmentator!"
                    )

                if status == 200:
                    suggestion.status = SuggestionStatus.done

                await suggestion.update(db)
                if status == 206:
                    # This indicates we received a partial result, so we need to queue
                    # up another task in order finish generating the suggestion.
                    figmentate.delay(suggestion.dict(), figmentator.dict())
            else:
                logger.error(
                    "Figmentator query failed (status=%s, reponse={%s})",
                    status,
                    str(entry),
                )
                suggestion.status = SuggestionStatus.failed
                await suggestion.update(db)


@app.task(
    autoretry_for=(ProcessingError,),
    retry_kwargs={"max_retries": 3},
    retry_backoff=0.25,
)
def create(story_id: str, context_hash: str, suggestion_type: SuggestionType):
    """ Create a suggestion """
    async_to_sync(_create)(story_id, context_hash, suggestion_type)


@app.task(
    autoretry_for=(ProcessingError,),
    retry_kwargs={"max_retries": 3},
    retry_backoff=0.25,
)
def figmentate(suggestion: Dict[str, Any], figmentator: Dict[str, Any]):
    """ Generate the figment """
    async_to_sync(_figmentate)(Suggestion(**suggestion), Figmentator(**figmentator))
