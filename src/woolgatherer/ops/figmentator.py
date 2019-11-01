"""
Operations on suggestion generators
"""
import logging
from typing import Any, Dict, List, Tuple

from databases import Database
from aiohttp import ClientSession, client_exceptions

from woolgatherer.db.utils import has_postgres
from woolgatherer.db_models.figmentator import Figmentator

# Need both clauses: one to statisfy PostgreSQL and the other for SQLite
if has_postgres():
    GROUP_BY = ""
    DISTINCT = "DISTINCT ON (st.type)"
else:
    GROUP_BY = "GROUP BY st.type"
    DISTINCT = ""

LOAD_BALANCE_QUERY = f"""
WITH
    story_totals AS
    (SELECT
       r.id,
       r.url,
       r.name,
       r.type,
       r.status,
       COUNT(rfs.story_hash) AS story_count
    FROM
        figmentator AS r
            LEFT JOIN
        figmentator_for_story AS rfs
            ON r.id = rfs.model_id
    WHERE
        r.status = 'active'
    GROUP BY
        r.id),
    min_counts AS
    (SELECT
        type,
        MIN(story_count) as min_count
    FROM
        story_totals
    GROUP BY
        type)
SELECT {DISTINCT}
    st.id,
    st.url,
    st.name,
    st.type,
    st.status
FROM
    story_totals as st
        LEFT JOIN
    min_counts as mc
        ON mc.type = st.type
WHERE
    st.story_count = mc.min_count
{GROUP_BY}
"""


async def select_figmentators(*, db: Database) -> List[Figmentator]:
    """ Select one generator per suggestion type """
    logging.debug("Selecting active figmentators")
    results = await db.fetch_all(LOAD_BALANCE_QUERY)
    return [Figmentator.db_construct(row) for row in results]


async def preprocess(
    context: Dict[str, Any], figmentator: Figmentator, *, session: ClientSession
) -> Tuple[bool, Figmentator]:
    """ Make a preprocess request """
    try:
        async with session.post(figmentator.url, json=context) as response:
            return response.status == 200, figmentator
    except client_exceptions.ClientError:
        return False, figmentator


async def figmentate(
    context: Dict[str, Any], figmentator: Figmentator, *, session: ClientSession
) -> Tuple[int, Dict[str, Any]]:
    """ Make a preprocess request """
    try:
        # TODO: Specify a range in the header
        async with session.post(figmentator.url, json=context) as response:
            return response.status, await response.json()
    except client_exceptions.ClientResponseError as cre:
        return cre.status, context
    except (
        client_exceptions.ClientConnectionError,
        client_exceptions.ClientPayloadError,
    ):
        return 503, context
