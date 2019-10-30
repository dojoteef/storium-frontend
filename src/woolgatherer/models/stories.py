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
    - **failed**: the story failed to preprocess; making another call to the create
      story endpoint will retry the preprocessing
    """

    pending = auto()
    ready = auto()
    failed = auto()
