'''
Data models for suggestions.
'''
from enum import auto
from typing import List

from pydantic import BaseModel, Schema

from woolgatherer.models.utils import AutoNamedEnum


class FeedbackType(AutoNamedEnum):
    ''' The type of user feedback. One of:

    * choice - radio dialog options
    * text - a text entry field
    '''
    choice = auto()
    text = auto()


class Feedback(BaseModel):
    ''' This structure is used to provide both the format of the feedback we require when finalizing
    a Suggestion. '''
    type : FeedbackType = Schema(
        ...,
        description='The type of user feedback. ' + FeedbackType.__doc__
    )

    title: str = Schema(
        ...,
        description='The title to display to the user.'
    )

    choices: List[str] = Schema(
        ...,
        description='A list of strings for use with feedback of type "choice".'
    )

    response: str = Schema(
        ...,
        description='The feedback from the user.'
    )
