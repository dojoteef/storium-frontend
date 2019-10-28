"""
Operations which can be conducted on stories
"""
import logging
from typing import Any, Dict, Optional

from databases import Database

from woolgatherer.tasks import stories
from woolgatherer.db.utils import json_hash
from woolgatherer.db_models.storium import Story, StoryStatus


async def create_story(story_dict: Dict[str, Any], *, db: Database) -> str:
    """ Create a story in the db """
    story_json, story_hash = json_hash(story_dict)
    if not await get_story_status(story_hash, db=db):
        logging.debug("Creating story for story_id: %s", story_hash)
        await Story(story=story_json, hash=story_hash).insert(db)
        task = stories.process.delay(story_hash)
        logging.debug("Started task %s", task.id)

    return story_hash


async def get_story_status(story_hash: str, *, db: Database) -> Optional[StoryStatus]:
    """ Get the current story status """
    logging.debug("Getting story status for story_id: %s", story_hash)
    story = await Story.select(db, "status", {"hash": story_hash})
    return story.status if story else None
