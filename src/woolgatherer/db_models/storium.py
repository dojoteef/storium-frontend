"""
Storium database models
"""
from sqlalchemy import Column, String, Enum
from woolgatherer.db.base import DBBaseModel
from woolgatherer.db.types import JSON
from woolgatherer.models.stories import StoryStatus


class Story(DBBaseModel):
    """
    The base model for a story, which is currently just a JSON object with the
    structure defined in:

    https://storium.com/help/export/json/0.9.2
    """

    json: Column = Column(JSON, nullable=False)
    json_hash: Column = Column(String, unique=True, index=True, nullable=False)
    status: Column = Column(
        Enum(StoryStatus), server_default=StoryStatus.pending, nullable=False
    )
