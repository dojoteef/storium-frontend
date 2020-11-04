"""
Operations which can be conducted on stories
"""
from typing import Any, Dict, Optional

from databases import Database

from woolgatherer.db_models.storium import Story, StoryStatus
from woolgatherer.db.utils import json_hash, load_query
from woolgatherer.errors import InsufficientCapacityError
from woolgatherer.tasks import stories
from woolgatherer.ops import figmentator as figmentator_ops
from woolgatherer.utils.logging import get_logger


logger = get_logger()


async def create_story(story_dict: Dict[str, Any], *, db: Database) -> str:
    """ Create a story in the db """
    story_json, story_hash = json_hash(story_dict)
    status = await get_story_status(story_hash, db=db)
    if not status or status == StoryStatus.failed:
        # When receiving a story we want to select the suggestion generators that will
        # preprocess the story (and ultimately generate the suggestion), before
        # acknowledging we have created the story. Otherwise we might not be able to
        # fulfill the suggestion generation request. Better to error out early, rather
        # than wait until the subsequent request to generate a suggestion.
        figmentators = await figmentator_ops.select_figmentators(db=db)
        if not figmentators:
            raise InsufficientCapacityError("No preprocessors available")

        story = Story(story=story_json, hash=story_hash, status=StoryStatus.pending)
        if not status:
            logger.debug("Creating story for story_id: %s", story_hash)
            await story.insert(db)
        else:
            logger.debug(
                "Updating story status to pending for story_id: %s", story_hash
            )
            await story.update(db, where={"hash": story_hash})

        task = stories.process.delay(story_hash, [f.dict() for f in figmentators])
        logger.debug("Started task %s", task.id)

    return story_hash


async def get_story_status(story_hash: str, *, db: Database) -> Optional[StoryStatus]:
    """ Get the current story status """
    logger.debug("Getting story status for story_id: %s", story_hash)
    story = await Story.select(db, "status", {"hash": story_hash})
    return story.status if story else None


async def cleanup_stories(*, db: Database):
    """ Cleanup unused stories """
    query = await load_query("cleanup_stories.sql")

    # Because encode/databases uses a fetch (which causes a prepared statement
    # error in PostgreSQL since the query has multiple statements) rather than
    # an execute when calling db.execute, need to use db.execute_many instead
    # since it actually does an execute.
    await db.execute_many(query, [None])
