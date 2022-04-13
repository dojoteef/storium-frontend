"""
A class wrapping our suggestion generation models in the database

The term Figmentator is not quite a portmanteau, but similarly it is a made up word. It
stems from the word figment, which is a noun meaning an imaginary construct, combined
with the Latin based suffix: -ator, which itself is a combination of -ate and -or. The
former (-ate) is a suffix occuring in Latin loanwords, like figment, that can be
used to form verbs. The latter (-or) is a suffix denoting a condition or property of
things or persons. In our case it denotes a nonhuman entity that "figmentates", i.e.
comes up with figments.
"""
from enum import auto

# pylint incorrectly complains about unused import for UniqueConstraint... not sure why
from sqlalchemy.schema import (  # pylint:disable=unused-import
    ForeignKey,
    UniqueConstraint,
)
from pydantic import Field

from woolgatherer.db_models.base import DBBaseModel
from woolgatherer.models.suggestion import SuggestionType
from woolgatherer.models.utils import AutoNamedEnum


class FigmentatorStatus(AutoNamedEnum):
    """
    An enum denoting the states a suggestion generator can be in. One of:

    - **active**: Active and ready to generate suggestions
    - **inactive**: Not currently able to generate suggestions
    """

    active = auto()
    inactive = auto()


class FigmentatorForStory(
    DBBaseModel, constraints=[UniqueConstraint("model_id", "story_hash")]
):
    """
    This table maps suggestion generators to stories
    """

    model_id: int = Field(..., foreign_key=ForeignKey("model.id"))
    story_hash: str = Field(..., foreign_key=ForeignKey("story.hash"))


class Figmentator(DBBaseModel):
    """
    This is the db model for a suggestion generator.
    """

    url: str = Field(..., unique=True)
    name: str = Field(..., index=True)
    type: SuggestionType = Field(...)
    status: FigmentatorStatus = Field(FigmentatorStatus.inactive)
    quota: int = Field(-1, server_default="-1")
