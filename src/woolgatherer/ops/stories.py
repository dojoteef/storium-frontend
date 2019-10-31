"""
Operations which can be conducted on stories
"""
import logging
from typing import Any, Dict, Optional

from databases import Database

from woolgatherer.db_models.storium import Story, StoryStatus
from woolgatherer.db.utils import json_hash
from woolgatherer.errors import InsufficientCapacityError
from woolgatherer.tasks import stories
from woolgatherer.ops import reverie as reverie_ops


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
        reveries = await reverie_ops.select_reveries(db=db)
        if not reveries:
            raise InsufficientCapacityError("No preprocessors available")

        story = Story(story=story_json, hash=story_hash, status=StoryStatus.pending)
        if not status:
            logging.debug("Creating story for story_id: %s", story_hash)
            await story.insert(db)
        else:
            logging.debug(
                "Updating story status to pending for story_id: %s", story_hash
            )
            await story.update(db, where={"hash": story_hash})

        task = stories.process.delay(story_hash, [r.dict() for r in reveries])
        logging.debug("Started task %s", task.id)

    return story_hash


async def get_story_status(story_hash: str, *, db: Database) -> Optional[StoryStatus]:
    """ Get the current story status """
    logging.debug("Getting story status for story_id: %s", story_hash)
    story = await Story.select(db, "status", {"hash": story_hash})
    return story.status if story else None
