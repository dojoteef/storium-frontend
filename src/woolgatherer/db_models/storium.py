"""
Storium database models
"""
from pydantic import Field

from woolgatherer.db_models.base import DBBaseModel
from woolgatherer.models.stories import StoryStatus
from woolgatherer.models.utils import Json


class Story(DBBaseModel):
    """
    The base model for a story, which is currently just a JSON object with the
    structure defined in:

    https://storium.com/help/export/json/0.9.2
    """

    story: Json = Field(...)
    hash: str = Field(..., unique=True, index=True)
    status: StoryStatus = Field(StoryStatus.pending, server_default=StoryStatus.pending)
