"""
Storium database models
"""
from uuid import UUID

# pylint incorrectly complains about unused import for UniqueConstraint... not sure why
from sqlalchemy.schema import (  # pylint:disable=unused-import
    ForeignKey,
    UniqueConstraint,
)
from woolgatherer.db.base import DBBaseModel
from woolgatherer.models.stories import StoryStatus
from woolgatherer.models.storium import SceneEntry
from woolgatherer.models.suggestion import SuggestionStatus, SuggestionType
from woolgatherer.models.utils import Field, Json


class Story(DBBaseModel):
    """
    The base model for a story, which is currently just a JSON object with the
    structure defined in:

    https://storium.com/help/export/json/0.9.2
    """

    story: Json = Field(...)
    hash: str = Field(..., unique=True, index=True)
    status: StoryStatus = Field(StoryStatus.pending, server_default=StoryStatus.pending)


class Suggestion(DBBaseModel, constraints=[UniqueConstraint("hash", "story_hash")]):
    """
    This is the db model for a suggestion.
    """

    type: SuggestionType = Field(...)
    hash: str = Field(..., index=True)
    uuid: UUID = Field(..., index=True)
    context: SceneEntry = Field(...)
    generated: SceneEntry = Field(...)
    status: SuggestionStatus = Field(
        SuggestionStatus.pending, server_default=SuggestionStatus.pending
    )
    story_hash: str = Field(..., index=True, foriegn_key=ForeignKey("story.hash"))

    def get_id_str(self):
        """ Return the UUID as a string """
        return str(self.uuid).replace("-", "")
