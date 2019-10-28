"""
Suggestion database model
"""
from uuid import UUID
from typing import Optional

# pylint incorrectly complains about unused import for UniqueConstraint... not sure why
from sqlalchemy.schema import (  # pylint:disable=unused-import
    ForeignKey,
    UniqueConstraint,
)
from woolgatherer.db.base import DBBaseModel
from woolgatherer.models.storium import SceneEntry
from woolgatherer.models.suggestion import SuggestionStatus, SuggestionType
from woolgatherer.models.utils import Field


class Suggestion(DBBaseModel, constraints=[UniqueConstraint("hash", "story_hash")]):
    """
    This is the db model for a suggestion.
    """

    type: SuggestionType = Field(...)
    hash: str = Field(..., index=True)
    uuid: UUID = Field(..., index=True)
    context: SceneEntry = Field(...)
    generated: SceneEntry = Field(...)
    finalized: Optional[SceneEntry] = Field(None)
    status: SuggestionStatus = Field(
        SuggestionStatus.pending, server_default=SuggestionStatus.pending
    )
    story_hash: str = Field(..., index=True, foriegn_key=ForeignKey("story.hash"))
