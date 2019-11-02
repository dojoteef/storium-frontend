"""
Data models for suggestions.
"""
from enum import auto

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
