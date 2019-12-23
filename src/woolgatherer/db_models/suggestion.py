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
from pydantic import Field

from woolgatherer.db_models.base import DBBaseModel
from woolgatherer.models.storium import SceneEntry
from woolgatherer.models.suggestion import SuggestionStatus, SuggestionType


class Suggestion(
    DBBaseModel, constraints=[UniqueConstraint("context_hash", "story_hash", "type")]
):
    """
    This is the db model for a suggestion.
    """

    type: SuggestionType = Field(...)
    context_hash: str = Field(..., index=True)
    uuid: UUID = Field(..., index=True, unique=True)
    context: SceneEntry = Field(...)
    generated: SceneEntry = Field(...)
    finalized: Optional[SceneEntry] = Field(None)
    status: SuggestionStatus = Field(
        SuggestionStatus.pending, server_default=SuggestionStatus.pending
    )
    story_hash: str = Field(..., index=True, foriegn_key=ForeignKey("story.hash"))
