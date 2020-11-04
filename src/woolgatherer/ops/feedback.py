"""
Operations which can be conducted on feedback
"""
from uuid import UUID
from typing import Sequence

from databases import Database

from woolgatherer.db.utils import IntegrityError
from woolgatherer.db_models.feedback import Feedback
from woolgatherer.errors import InvalidOperationError
from woolgatherer.models.feedback import FeedbackResponse
from woolgatherer.models.suggestion import SuggestionStatus
from woolgatherer.ops import suggestions as suggestion_ops
from woolgatherer.utils.settings import Settings
from woolgatherer.utils.logging import get_logger


logger = get_logger()


async def submit_feedback(
    suggestion_id: UUID, responses: Sequence[FeedbackResponse], *, db: Database
) -> None:
    """
    Register the feedback for the suggestion. It assumes you have already verified the
    suggestion is in the database, otherwise an exception for a constraint violation
    will be raised.
    """
    logger.debug("Registering feedback for suggestion_id: %s", suggestion_id)
    suggestion = await suggestion_ops.get_suggestion(suggestion_id, db=db)
    if not suggestion:
        raise InvalidOperationError("Unknown suggestion")

    if suggestion.status is not SuggestionStatus.done:
        raise InvalidOperationError("Suggestion has not completed")

    # Make sure the feedback is valid
    validate_feedback(responses)

    try:
        for response in responses:
            await Feedback(
                type=response.type,
                response=response.response,
                suggestion_id=suggestion.uuid,
            ).insert(db)
    except IntegrityError:
        raise InvalidOperationError("Cannot submit feedback more than once!")


def validate_feedback(responses: Sequence[FeedbackResponse]):
    """
    A function which validates the feedback. Users must fill out all feedback
    and must respect the valid choices of feedback.

    Raises InvalidOperationError in case the feedback is invalid.
    """
    feedback_by_type = {r.type: r for r in responses}
    for feedback_prompt in Settings.required_feedback:
        feedback_type = feedback_prompt.type
        if feedback_type not in feedback_by_type:
            raise InvalidOperationError(f"Missing required feedback: {feedback_type}")

        choices = feedback_prompt.choices
        response = feedback_by_type[feedback_type].response
        if choices and response not in choices:
            raise InvalidOperationError(
                f"Invalid response '{response}' for feedback of type {feedback_type}"
            )

    for feedback_prompt in Settings.optional_feedback:
        feedback_type = feedback_prompt.type
        if feedback_type not in feedback_by_type:
            continue

        choices = feedback_prompt.choices
        response = feedback_by_type[feedback_type].response
        if choices and response not in choices:
            raise InvalidOperationError(
                f"Invalid response '{response}' for feedback of type {feedback_type}"
            )
