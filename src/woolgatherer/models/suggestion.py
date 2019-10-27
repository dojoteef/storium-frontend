"""
Data models for suggestions.
"""
from enum import auto
from typing import List, Optional

from pydantic import BaseModel

from woolgatherer.models.storium import SceneEntry
from woolgatherer.models.utils import AutoNamedEnum, Field


class FeedbackType(AutoNamedEnum):
    """ The type of user feedback. One of:

    - **choice**: radio dialog options
    - **text**: a text entry field
    """

    choice = auto()
    text = auto()


class Feedback(BaseModel):
    """ This structure is used to provide both the format of the feedback we require when finalizing
    a Suggestion. """

    type: FeedbackType = Field(
        ..., description=f"The type of user feedback. {FeedbackType.__doc__}"
    )

    title: str = Field(..., description="The title to display to the user.")

    choices: List[str] = Field(
        ..., description='A list of strings for use with feedback of type "choice".'
    )

    response: str = Field(..., description="The feedback from the user.")


class SuggestionStatus(AutoNamedEnum):
    """ The status of the current suggestion. One of:

    - **pending**: it still hasn't started excuting
    - **executing**: it is currently being generated, so the suggestion might be
      partially complete
    - **done**: the suggestion has finished being generated
    """

    pending = auto()
    executing = auto()
    done = auto()


class SuggestionType(AutoNamedEnum):
    """ The type of suggestion. One of:

    - **scene_entry**: Suggest a scene entry
    """

    scene_entry = auto()
