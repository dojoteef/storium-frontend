"""
Load all the models
"""
from .base import DBBaseModel
from .storium import Story
from .suggestion import Suggestion
from .feedback import Feedback
from .figmentator import Figmentator, FigmentatorStatus


__all__ = ["DBBaseModel", "Story", "Feedback", "Figmentator", "FigmentatorStatus"]
