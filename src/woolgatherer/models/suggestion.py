"""
Data models for suggestions.
"""
from enum import auto
from pydantic import BaseModel, Field

from woolgatherer.models.range import RangeUnits
from woolgatherer.models.utils import AutoNamedEnum


class SuggestionStatus(AutoNamedEnum):
    """ The status of the current suggestion. One of:

    - **pending**: it still hasn't started excuting
    - **executing**: it is currently being generated, so the suggestion might be
      partially complete
    - **failed**: the suggestion failed to generate
    - **done**: the suggestion has finished being generated
    """

    pending = auto()
    executing = auto()
    failed = auto()
    done = auto()


class SuggestionType(AutoNamedEnum):
    """ The type of suggestion. One of:

    - **scene_entry**: Suggest a scene entry
    """

    scene_entry = auto()


class SceneEntryParameters(BaseModel):
    """ Parameters that guide SceneEntry generation """

    units: RangeUnits = Field(
        RangeUnits.words, description="The type of units to to measure length in."
    )

    max_length: int = Field(
        250, description="Maximum length in units for a scene entry"
    )

    chunk_size: int = Field(
        50,
        description="""
How many units to generate per request to a figmentator. This is used to allow streaming
the generated suggestion.
        """,
    )
