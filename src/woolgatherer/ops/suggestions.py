"""
Operations which can be conducted on suggestions
"""
import logging
from uuid import uuid4, UUID
from typing import Optional, Union

from databases import Database

from woolgatherer.tasks import suggestions
from woolgatherer.models.storium import SceneEntry
from woolgatherer.db.utils import json_hash
from woolgatherer.db_models.storium import Suggestion, SuggestionType


async def get_or_create_suggestion(
    db: Database, story_hash: str, context: SceneEntry, suggestion_type: SuggestionType
) -> Optional[Suggestion]:
    """ Create a suggestion. First mark it in the db, then create a task. """
    _, context_hash = json_hash(context.dict())
    suggestion = await get_suggestion(db, story_hash, context_hash, suggestion_type)
    if suggestion:
        return suggestion

    logging.debug("Creating suggestion for story_id: %s", story_hash)
    suggestion = Suggestion(
        uuid=uuid4(),
        context=context,
        generated=context,  # default to the passed in context
        hash=context_hash,
        type=suggestion_type,
        story_hash=story_hash,
    )
    await suggestion.insert(db)
    task = suggestions.create.delay(story_hash, suggestion_type)
    logging.debug("Started task %s", task.id)

    return suggestion


async def get_suggestion(
    db: Database,
    story_hash: str,
    context_or_hash: Union[SceneEntry, str],
    suggestion_type: SuggestionType,
) -> Optional[Suggestion]:
    """ Get the current suggestion """
    if isinstance(context_or_hash, SceneEntry):
        _, context_hash = json_hash(context_or_hash.dict())
    else:
        context_hash = context_or_hash

    logging.debug(
        "Getting suggestion of type %s for story_hash: %s", suggestion_type, story_hash
    )

    return await Suggestion.select(
        db,
        where={"hash": context_hash, "story_hash": story_hash, "type": suggestion_type},
    )


async def get_suggestion_by_id(
    db: Database, suggestion_id: UUID
) -> Optional[Suggestion]:
    """ Get the current suggestion """
    logging.debug("Getting suggestion for suggestion_id: %s", suggestion_id)
    suggestion = await Suggestion.select(db, where={"uuid": suggestion_id})
    return suggestion
