"""
A class wrapping our suggestion generation models in the database
"""
from enum import auto
from typing import Tuple

from aiohttp import ClientSession

# pylint incorrectly complains about unused import for UniqueConstraint... not sure why
from sqlalchemy.schema import (  # pylint:disable=unused-import
    ForeignKey,
    UniqueConstraint,
)

from woolgatherer.db_models.base import DBBaseModel
from woolgatherer.models.suggestion import SuggestionType
from woolgatherer.models.utils import AutoNamedEnum, Field


class ReverieStatus(AutoNamedEnum):
    """
    An enum denoting the states a suggestion generator can be in. One of:

    - **active**: Active and ready to generate suggestions
    - **inactive**: Not currently able to generate suggestions
    """

    active = auto()
    inactive = auto()


class ReverieForStory(
    DBBaseModel, constraints=[UniqueConstraint("model_id", "story_hash")]
):
    """
    This table maps suggestion generators to stories
    """

    model_id: int = Field(..., foreign_key=ForeignKey("model.id"))
    story_hash: str = Field(..., foreign_key=ForeignKey("story.hash"))


class Reverie(DBBaseModel):
    """
    This is the db model for a suggestion generator.
    """

    url: str = Field(..., unique=True)
    name: str = Field(..., index=True)
    type: SuggestionType = Field(...)
    status: ReverieStatus = Field(ReverieStatus.inactive)

    async def preprocess(self, session: ClientSession) -> Tuple[bool, "Reverie"]:
        """ Make a preprocess request """
        async with session.get(self.url) as response:
            return response.status == 200, self
