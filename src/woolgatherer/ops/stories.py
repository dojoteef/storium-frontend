"""
Operations which can be conducted on stories
"""
import logging
from typing import Any, Dict, Optional

from databases import Database

from woolgatherer.db.utils import json_hash
from woolgatherer.db_models.storium import Story, StoryStatus


async def create_story(db: Database, story_dict: Dict[str, Any]) -> str:
    """ Create a story in the db """
    story_json, story_hash = json_hash(story_dict)
    story = Story(story=story_json, hash=story_hash)
    try:
        await db.execute(query=story.__table__.insert(), values=story.dict())
    except:
        pass

    return story_hash


async def get_story_status(db: Database, story_hash: str) -> Optional[StoryStatus]:
    """ Get the current story status """
    return await db.fetch_val(
        query=Story.__table__.select().where(Story.__table__.c.hash == story_hash),
        column="status",
    )
