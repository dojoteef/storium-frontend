"""
Operations on suggestion generators
"""
import logging
from typing import List

from databases import Database

from woolgatherer.db_models.generator import Reverie

LOAD_BALANCE_QUERY = """
WITH story_totals AS
    (SELECT
       r.id,
       r.url,
       r.name,
       r.type,
       r.status,
       COUNT(rfs.story_hash) AS story_count
    FROM
        reverie AS r
            LEFT JOIN
        reverie_for_story AS rfs
            ON r.id = rfs.model_id
    WHERE
        r.status = "active"
    GROUP BY
        r.id)
SELECT
    id,
    url,
    name,
    type,
    status
FROM
    story_totals
GROUP BY
    type
HAVING
    story_count = MIN(story_count);
"""


async def select_reveries(*, db: Database) -> List[Reverie]:
    """ Select one generator per suggestion type """
    logging.debug("Selecting active generators")
    results = await db.fetch_all(LOAD_BALANCE_QUERY)
    return [Reverie.db_construct(row) for row in results]
