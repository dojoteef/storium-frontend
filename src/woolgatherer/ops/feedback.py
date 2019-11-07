"""
Operations which can be conducted on feedback
"""
import logging
from uuid import UUID
from typing import Sequence

from databases import Database

from woolgatherer.db.utils import IntegrityError
from woolgatherer.db_models.feedback import Feedback
from woolgatherer.errors import InvalidOperationError
from woolgatherer.models.feedback import FeedbackResponse
from woolgatherer.models.suggestion import SuggestionStatus
from woolgatherer.ops import suggestions as suggestion_ops


async def submit_feedback(
    suggestion_id: UUID, responses: Sequence[FeedbackResponse], *, db: Database
) -> None:
    """
    Register the feedback for the suggestion. It assumes you have already verified the
    suggestion is in the database, otherwise an exception for a constraint violation
    will be raised.
    """
    logging.debug("Registering feedback for suggestion_id: %s", suggestion_id)
    suggestion = await suggestion_ops.get_suggestion(suggestion_id, db=db)
    if not suggestion:
        raise InvalidOperationError("Unknown suggestion")

    if suggestion.status is not SuggestionStatus.done:
        raise InvalidOperationError("Suggestion has not completed")

    try:
        for response in responses:
            await Feedback(
                type=response.type,
                response=response.response,
                suggestion_id=suggestion.uuid,
            ).insert(db)
    except IntegrityError:
        raise InvalidOperationError("Cannot submit feedback more than once!")
