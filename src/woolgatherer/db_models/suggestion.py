"""
Suggestion database model
"""
from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID

# pylint incorrectly complains about unused import for UniqueConstraint... not sure why
from sqlalchemy.schema import (  # pylint:disable=unused-import
    ForeignKey,
    UniqueConstraint,
)
from sqlalchemy import text
from pydantic import Field

from woolgatherer.db_models.base import DBBaseModel
from woolgatherer.models.storium import SceneEntry
from woolgatherer.models.suggestion import SuggestionStatus, SuggestionType
from woolgatherer.utils.settings import Settings
from woolgatherer.utils.logging import get_logger


logger = get_logger()


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
    timestamp: datetime = Field(None, nullable=False, server_default=text("CURRENT_TIMESTAMP"))

    @property
    def figment_settings(self) -> Dict[str, Any]:
        """
        Get the settings for generating figments
        """
        if self.type == SuggestionType.scene_entry:
            return Settings.scene_entry_parameters.dict()

        logger.error(
            "Suggestion.figment_settings: Unexpected suggestion type %s!", self.type
        )
        return {}
