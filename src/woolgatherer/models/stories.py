"""
Models used for the stories endpoints
"""
from enum import auto

from woolgatherer.models.utils import AutoNamedEnum


class StoryStatus(AutoNamedEnum):
    """
    Enum describing the status of a story:

    - **pending**: story is still be preprocessed
    - **ready**: story is ready to generate suggestions
    """

    pending = auto()
    read = auto()
