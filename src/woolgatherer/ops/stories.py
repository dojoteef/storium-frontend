"""
Operations which can be conducted on stories
"""
from typing import Optional

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from woolgatherer.db.utils import json_hash
from woolgatherer.db_models.storium import Story, StoryStatus


def create_story(db: Session, story_dict: dict) -> str:
    """ Create a story in the db """
    story_hash = json_hash(story_dict)
    try:
        db.add(Story(json=story_dict, json_hash=story_hash))
        db.commit()
    except IntegrityError:
        # If they try to create the same story, it will fail the uniqueness check.
        # Simply return the story_hash since we already have it in the db.
        db.rollback()

    return story_hash


def get_story_status(db: Session, story_hash: str) -> Optional[StoryStatus]:
    """ Get the current story status """
    story = db.query(Story).filter(Story.json_hash == story_hash).one_or_none()
    return story.status if story else None
