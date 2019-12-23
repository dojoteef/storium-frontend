"""
Feedback database model
"""
from uuid import UUID

# pylint incorrectly complains about unused import for UniqueConstraint... not sure why
from sqlalchemy.schema import (  # pylint:disable=unused-import
    ForeignKey,
    UniqueConstraint,
)
from pydantic import Field

from woolgatherer.db_models.base import DBBaseModel
from woolgatherer.models.feedback import FeedbackType


class Feedback(DBBaseModel, constraints=[UniqueConstraint("type", "suggestion_id")]):
    """
    This is the db model for a suggestion.
    """

    response: str = Field(...)
    type: FeedbackType = Field(..., index=True)
    suggestion_id: UUID = Field(
        ..., index=True, foriegn_key=ForeignKey("suggestion.uuid")
    )
