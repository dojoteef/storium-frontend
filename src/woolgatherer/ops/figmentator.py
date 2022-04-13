"""
Operations on suggestion generators
"""
from typing import Any, Dict, List, Optional, Tuple

from yarl import URL
from databases import Database
from aiohttp import ClientSession, client_exceptions

from woolgatherer.db.utils import load_query
from woolgatherer.db_models.figmentator import Figmentator, FigmentatorForStory
from woolgatherer.db_models.storium import Story, StoryStatus
from woolgatherer.db_models.suggestion import Suggestion
from woolgatherer.errors import InsufficientCapacityError
from woolgatherer.models.range import compute_next_range
from woolgatherer.utils.logging import get_logger


logger = get_logger()


async def select_figmentators(*, db: Database) -> List[Figmentator]:
    """ Select one generator per suggestion type """
    logger.debug("Selecting active figmentators")
    query = await load_query("load_balance.sql")
    results = await db.fetch_all(query)
    return [Figmentator.db_construct(row) for row in results]


async def preprocess(
    context: Dict[str, Any], figmentator: Figmentator, *, session: ClientSession
) -> Tuple[bool, Figmentator]:
    """ Make a preprocess request """
    try:
        url = URL(figmentator.url)
        async with session.post(url / "story/snapshot", json=context) as response:
            return response.status == 200, figmentator
    except client_exceptions.ClientError:
        return False, figmentator


async def reassign_figmentator(
    suggestion: Suggestion,
    figmentator: Figmentator,
    *,
    db: Database,
    session: ClientSession,
) -> Optional[Figmentator]:
    """ Reassign the story to a new figmentator for the given suggestion """
    story = await Story.select(db, where={"hash": suggestion.story_hash})
    if not story:
        logger.error("Story %s not found in database!", suggestion.story_hash)
        return None

    figmentators = [
        f for f in await select_figmentators(db=db) if f.type == suggestion.type
    ]
    if not figmentators:
        raise InsufficientCapacityError("No preprocessors available")

    story.status = StoryStatus.ready
    context = {"story_id": story.hash, "story": story.story}
    completed, new_figmentator = await preprocess(
        context, figmentators.pop(), session=session
    )
    async with db.transaction():
        if completed:
            where = {"model_id": figmentator.id, "story_hash": story.hash}
            await FigmentatorForStory(**where).delete(db, where=where)
            await FigmentatorForStory(
                model_id=new_figmentator.id, story_hash=story.hash
            ).insert(db)
        else:
            story.status = StoryStatus.failed
        await story.update(db)

    logger.info("Reprocessed story=%s, status=%s", story.hash, story.status)

    return new_figmentator


async def figmentate(
    suggestion: Suggestion, figmentator: Figmentator, *, session: ClientSession
) -> Tuple[int, Dict[str, Any]]:
    """ Make a figmentate request """
    try:
        url = URL(figmentator.url)
        url /= f"figment/{suggestion.story_hash}/new"

        computed_range = compute_next_range(
            suggestion.generated.description or "", **suggestion.figment_settings
        )
        logger.info("Posting range: %s", computed_range)
        async with session.post(
            url.with_query(suggestion_type=suggestion.type.value),
            json=suggestion.generated.dict(),
            headers={"Range": str(computed_range)},
        ) as response:
            return response.status, await response.json()
    except client_exceptions.ClientResponseError as cre:
        return cre.status, suggestion.generated.dict()
    except (
        client_exceptions.ClientConnectionError,
        client_exceptions.ClientPayloadError,
    ):
        return 503, suggestion.generated.dict()
