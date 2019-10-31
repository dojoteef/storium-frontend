"""
Operations on suggestion generators
"""
import logging
from typing import List

from databases import Database

from woolgatherer.db.utils import has_postgres
from woolgatherer.db_models.reverie import Reverie

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
        reverie AS r
            LEFT JOIN
        reverie_for_story AS rfs
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


async def select_reveries(*, db: Database) -> List[Reverie]:
    """ Select one generator per suggestion type """
    logging.debug("Selecting active reveries")
    results = await db.fetch_all(LOAD_BALANCE_QUERY)
    return [Reverie.db_construct(row) for row in results]
