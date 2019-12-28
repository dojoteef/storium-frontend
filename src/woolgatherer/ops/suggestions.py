"""
Operations which can be conducted on suggestions
"""
import logging
from uuid import uuid4, UUID
from functools import singledispatch
from typing import Optional, Sequence, Tuple, Union

from databases import Database

from woolgatherer.errors import InvalidOperationError
from woolgatherer.tasks import suggestions
from woolgatherer.models.storium import SceneEntry
from woolgatherer.models.feedback import FeedbackPrompt
from woolgatherer.db.utils import json_hash
from woolgatherer.db_models.suggestion import Suggestion, SuggestionType
from woolgatherer.utils.settings import Settings


async def get_or_create_suggestion(
    story_hash: str,
    context: SceneEntry,
    suggestion_type: SuggestionType,
    *,
    db: Database,
) -> Tuple[Optional[Suggestion], Sequence[FeedbackPrompt]]:
    """ Create a suggestion. First mark it in the db, then create a task. """
    if context.description:
        return None, Settings.required_feedback

    _, context_hash = json_hash(context.dict())
    suggestion = await get_suggestion(
        story_hash, context_or_hash=context_hash, suggestion_type=suggestion_type, db=db
    )
    if suggestion:
        return suggestion, Settings.required_feedback

    logging.debug("Creating suggestion for story_id: %s", story_hash)
    suggestion = Suggestion(
        uuid=uuid4(),
        context=context,
        generated=context,  # default to the passed in context
        type=suggestion_type,
        story_hash=story_hash,
        context_hash=context_hash,
    )
    await suggestion.insert(db)
    task = suggestions.create.delay(story_hash, context_hash, suggestion_type)
    logging.debug("Started task %s", task.id)

    return suggestion, Settings.required_feedback


@singledispatch
async def get_suggestion(
    suggestion_id: UUID, *, db: Database, **kwargs  # pylint:disable=unused-argument
) -> Optional[Suggestion]:
    """ Get the current suggestion """
    logging.debug("Getting suggestion for suggestion_id: %s", suggestion_id)
    suggestion = await Suggestion.select(db, where={"uuid": suggestion_id})
    return suggestion


async def get_suggestion_with_context(
    story_hash: str,
    *,
    suggestion_type: SuggestionType,
    context_or_hash: Union[SceneEntry, str],
    db: Database,
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
        where={
            "context_hash": context_hash,
            "story_hash": story_hash,
            "type": suggestion_type,
        },
    )


# For some reason using 'register' as a decorator is not working properly, but calling
# it as a function seems to work...
get_suggestion.register(str, get_suggestion_with_context)


async def finalize_suggestion(
    suggestion_id: UUID, entry: SceneEntry, *, db: Database
) -> None:
    """ Get the current suggestion """
    logging.debug("Finalizing suggestion for suggestion_id: %s", suggestion_id)
    suggestion = await get_suggestion(suggestion_id, db=db)
    if not suggestion:
        raise InvalidOperationError("Unknown suggestion")

    if suggestion.finalized:
        raise InvalidOperationError("Cannot finalize a suggestion twice")

    suggestion.finalized = entry
    await suggestion.update(
        db, include_columns="finalized", where={"uuid": suggestion_id}
    )
