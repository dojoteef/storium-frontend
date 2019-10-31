"""
Operations which can be conducted on feedback
"""
import logging
from typing import Sequence

from databases import Database

from woolgatherer.db_models.feedback import Feedback
from woolgatherer.db_models.suggestion import Suggestion
from woolgatherer.errors import InvalidOperationError
from woolgatherer.models.feedback import FeedbackResponse
from woolgatherer.models.suggestion import SuggestionStatus


async def submit_feedback(
    suggestion: Suggestion, responses: Sequence[FeedbackResponse], *, db: Database
) -> None:
    """
    Register the feedback for the suggestion. It assumes you have already verified the
    suggestion is in the database, otherwise an exception for a constraint violation
    will be raised.
    """
    if not suggestion:
        raise InvalidOperationError("Unknown suggestion")

    if suggestion.status is not SuggestionStatus.done:
        raise InvalidOperationError("Suggestion has not completed")

    logging.debug("Registering feedback for suggestion_id: %s", suggestion.context_hash)
    for response in responses:
        await Feedback(
            type=response.type,
            response=response.response,
            suggestion_id=suggestion.uuid,
        ).insert(db)
