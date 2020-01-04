"""
Operations on suggestion generators
"""
import re
import logging
from typing import Any, Dict, List, Tuple
import unicodedata

from yarl import URL
from databases import Database
from aiohttp import ClientSession, client_exceptions

from woolgatherer.db.utils import has_postgres
from woolgatherer.db_models.figmentator import Figmentator
from woolgatherer.db_models.suggestion import Suggestion
from woolgatherer.models.range import Range, Subrange, RangeUnits
from woolgatherer.models.storium import SceneEntry
from woolgatherer.utils.settings import Settings


TOKENIZER_REGEX = re.compile(r"\w+|[^\w\s]+")


def tokenize(text: str) -> List[str]:
    """
    Implement a simple tokenizer that seperates continguous word characters and
    punctuation.
    """
    return TOKENIZER_REGEX.findall(text)


def NFC(text):
    """
    Normalize the unicode string into NFC form

    Read more about that here:
    https://docs.python.org/3/library/unicodedata.html#unicodedata.normalize
    """
    return unicodedata.normalize("NFC", text)


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
        url = URL(figmentator.url)
        async with session.post(url / "story/snapshot", json=context) as response:
            return response.status == 200, figmentator
    except client_exceptions.ClientError:
        return False, figmentator


def compute_range(entry: SceneEntry) -> Range:
    """ Compute the range of the scene entry """
    ranges: List[Subrange] = []
    range_dict = {"unit": Settings.scene_entry_parameters.units, "ranges": ranges}

    entry_len = (
        (
            # Tokenize for computing the number of words in a suggestion.
            len(tokenize(entry.description))
            if Settings.scene_entry_parameters.units == RangeUnits.words
            # Otherwise length is just number of characters
            else len(NFC(entry.description))
        )
        if entry.description
        else 0
    )
    remaining = Settings.scene_entry_parameters.max_length - entry_len
    if remaining > 0:
        end = min(remaining, Settings.scene_entry_parameters.chunk_size)
        start = entry_len if end == remaining else None
        end = start + remaining if start else end

        ranges.append(Subrange(start=start, end=end))

    return Range(**range_dict)


async def figmentate(
    suggestion: Suggestion, figmentator: Figmentator, *, session: ClientSession
) -> Tuple[int, Dict[str, Any]]:
    """ Make a figmentate request """
    try:
        url = URL(figmentator.url)
        url /= f"figment/{suggestion.story_hash}/new"
        computed_range = str(compute_range(suggestion.generated))
        logging.info("Posting range: %s", computed_range)
        async with session.post(
            url.with_query(suggestion_type=suggestion.type.value),
            json=suggestion.generated.dict(),
            headers={"Range": computed_range},
        ) as response:
            return response.status, await response.json()
    except client_exceptions.ClientResponseError as cre:
        return cre.status, suggestion.generated.dict()
    except (
        client_exceptions.ClientConnectionError,
        client_exceptions.ClientPayloadError,
    ):
        return 503, suggestion.generated.dict()
