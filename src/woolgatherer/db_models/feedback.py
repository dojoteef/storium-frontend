"""
Feedback database model
"""
# pylint incorrectly complains about unused import for UniqueConstraint... not sure why
from sqlalchemy.schema import (  # pylint:disable=unused-import
    ForeignKey,
    UniqueConstraint,
)
from woolgatherer.db.base import DBBaseModel
from woolgatherer.models.feedback import FeedbackType
from woolgatherer.models.utils import Field


class Feedback(DBBaseModel, constraints=[UniqueConstraint("type", "suggestion_id")]):
    """
    This is the db model for a suggestion.
    """

    response: str = Field(...)
    type: FeedbackType = Field(..., index=True)
    suggestion_id: str = Field(
        ..., index=True, foriegn_key=ForeignKey("suggestion.hash")
    )
