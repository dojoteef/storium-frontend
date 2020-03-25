"""
This router handles the stories endpoints.
"""
from difflib import Differ
from typing import Dict, Tuple
from itertools import groupby

from databases import Database
from fastapi import APIRouter, Depends
from starlette.requests import Request
from starlette.templating import Jinja2Templates

from woolgatherer.db.session import get_db
from woolgatherer.db.utils import load_query
from woolgatherer.models.range import split_sentences
from woolgatherer.utils.routing import CompressibleRoute
from woolgatherer.utils import ngram_overlaps


router = APIRouter()
router.route_class = CompressibleRoute

templates = Jinja2Templates(directory="templates")


def parse_diff(text: str) -> Tuple[str, str]:
    """
    Return the op code and text as a tuple.
    """
    if text.startswith("- "):
        text_class = "table-danger"
    elif text.startswith("+ "):
        text_class = "table-success"
    elif text.startswith("  "):
        text_class = "table-default"
    else:
        raise ValueError(f"Unknown op code for text: {text}")

    return (text_class, text[2:])


@router.get("/", summary="Get the main dashboard for the woolgatherer service")
async def get_dashboard(request: Request, db: Database = Depends(get_db)):
    """
    This method returns a template for the main dashboard of the woolgatherer
    service.
    """
    query = await load_query("suggestion_counts_by_user.sql")
    suggestion_counts = {}
    for c in [1, 5, 10, 20, float("inf")]:
        result = await db.fetch_one(query, values={"suggestion_count": c})
        if not result:
            continue

        suggestion_counts[c] = result["unique_user_count"]

    edits = []
    differ = Differ()
    for row in await db.fetch_all(await load_query("finalized_suggestions.sql")):
        finalized = row["user_text"]
        generated = row["generated_text"]
        model_name = row["model_name"]
        comments = row["comments"]

        diff = [
            parse_diff(word)
            for word in differ.compare(generated.split(), finalized.split())
            if word[0] != "?"
        ]

        finalized_sentences = split_sentences(finalized)
        generated_sentences = split_sentences(generated)
        overlaps = ngram_overlaps(finalized_sentences, generated_sentences)

        edits.append(
            {
                "diff": diff,
                "comments": comments,
                "model_name": model_name,
                "overlaps": len(overlaps),
                "finalized_sentences": len(finalized_sentences),
                "generated_sentences": len(generated_sentences),
            }
        )

    ratings = await db.fetch_all(await load_query("avg_ratings.sql"))
    ratings_by_type = {
        t: [{k: v for k, v in r.items() if k != "type"} for r in g]
        for t, g in groupby(ratings, lambda x: x["type"])
    }

    return templates.TemplateResponse(
        "index.html",
        {
            "edits": edits,
            "request": request,
            "ratings": ratings,
            "ratings_by_type": ratings_by_type,
            "suggestion_counts": suggestion_counts,
        },
    )


@router.get(
    "/sentence/histogram",
    summary="Get the sentence histogram",
    response_description="A dictionary of mapping sentences number to overlap",
)
async def get_sentence_histogram(
    filtered: bool = False, db: Database = Depends(get_db)
):
    """
    This method returns a template for the main dashboard of the woolgatherer
    service.
    """
    histogram: Dict[int, int] = {}
    for row in await db.fetch_all(await load_query("finalized_suggestions.sql")):
        finalized = row["user_text"]
        generated = row["generated_text"]

        finalized_sentences = split_sentences(finalized)
        generated_sentences = split_sentences(generated)
        overlaps = ngram_overlaps(finalized_sentences, generated_sentences)

        if filtered and len(overlaps) == len(generated_sentences):
            continue

        for idx in overlaps:
            histogram[idx] = histogram.get(idx, 0) + 1

    return histogram
