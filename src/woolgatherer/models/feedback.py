"""
Data models for feedback.
"""
from enum import auto
from typing import List, Optional

from pydantic import BaseModel

from woolgatherer.models.utils import AutoNamedEnum, Field


FeedbackScale = tuple(str(i) for i in range(1, 6))


class FeedbackType(AutoNamedEnum):
    """ The possible types of feedback questions. One of:

    - **fluency**: rating fluency
    - **relevance**: rating relevance
    - **coherence**: rating coherence
    - **comments**: written comments
    """

    fluency = auto()
    relevance = auto()
    coherence = auto()
    comments = auto()


class FeedbackEntryType(AutoNamedEnum):
    """ The type of user feedback. One of:

    - **choice**: radio dialog options
    - **text**: a text entry field
    """

    text = auto()
    choice = auto()


class FeedbackPrompt(BaseModel):
    """
    This defines the format of the feedback we require when finalizing a Suggestion.
    """

    type: FeedbackType = Field(
        ..., description="The type of feedback requested. {FeedbackType.__doc__}"
    )

    entry_type: FeedbackEntryType = Field(
        ...,
        description=f"The entry type for the user feedback. {FeedbackEntryType.__doc__}",
    )

    title: str = Field(..., description="The title to display to the user.")

    choices: Optional[List[str]] = Field(
        None, description='A list of strings for use with feedback of type "choice".'
    )


class FeedbackResponse(BaseModel):
    """ This structure is used to provide both the format of the feedback we require when finalizing
    a Suggestion. """

    type: FeedbackType = Field(
        ..., description="The type of feedback requested. {FeedbackType.__doc__}"
    )
    response: str = Field(..., description="The response to the feedback prompt.")
