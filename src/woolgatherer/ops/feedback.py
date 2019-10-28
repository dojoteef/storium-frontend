"""
Operations which can be conducted on feedback
"""
import logging
from uuid import UUID
from functools import singledispatch
from typing import Sequence

from databases import Database

from woolgatherer.db_models.feedback import Feedback
from woolgatherer.db_models.suggestion import Suggestion
from woolgatherer.errors import InvalidOperationError
from woolgatherer.models.feedback import FeedbackResponse
from woolgatherer.models.suggestion import SuggestionStatus
from woolgatherer.ops import suggestions as suggestion_ops


@singledispatch
async def submit_feedback(
    suggestion_id: UUID, responses: Sequence[FeedbackResponse], *, db: Database
) -> None:
    """
    Register the feedback for the suggestion. First verifies that the suggestion exists.
    """
    suggestion = await suggestion_ops.get_suggestion(suggestion_id, db=db)
    submit_feedback(suggestion, responses, db=db)


async def submit_feedback_validated(
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

    logging.debug("Registering feedback for suggestion_id: %s", suggestion.hash)
    for response in responses:
        await Feedback(
            type=response.type,
            response=response.response,
            suggestion_id=suggestion.uuid,
        ).insert(db)


# For some reason using 'register' as a decorator is not working properly, but calling
# it as a function seems to work...
submit_feedback.register(Suggestion, submit_feedback_validated)
