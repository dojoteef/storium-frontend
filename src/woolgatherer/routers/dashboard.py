"""
This router handles the stories endpoints.
"""
import io
import os
import csv
import json
import logging
import statistics
from typing import Any, Dict, Mapping, AsyncGenerator
from itertools import combinations, groupby

import aiofiles
from databases import Database
from fastapi import APIRouter, Depends, Header, HTTPException
from scipy.stats import pearsonr
from starlette.requests import Request
from starlette.responses import PlainTextResponse, StreamingResponse
from starlette.templating import Jinja2Templates
from starlette.status import HTTP_406_NOT_ACCEPTABLE

from woolgatherer.db.session import get_db
from woolgatherer.db.utils import load_query
from woolgatherer.metrics import get_diff_score, remove_stopwords, rouge
from woolgatherer.models.range import split_sentences
from woolgatherer.utils.routing import CompressibleRoute
from woolgatherer.utils import ngram_overlaps


router = APIRouter()
router.route_class = CompressibleRoute

templates = Jinja2Templates(directory="templates")


async def get_finalized_suggestions(db: Database) -> AsyncGenerator[Mapping, None]:
    """ Load the finalized suggestions """
    async with aiofiles.open(
        os.path.join("static", "game_blacklist.txt"), "rt"
    ) as blacklist_file:
        blacklist = [l.strip() for l in await blacklist_file.readlines()]

    async for row in db.iterate(
        await load_query("finalized_suggestions.sql"), {"blacklist": blacklist}
    ):
        yield row


async def select_judgement_contexts(
    db: Database, limit: int = 100
) -> AsyncGenerator[Mapping, None]:
    """ Load the finalized suggestions """
    async with aiofiles.open(
        os.path.join("static", "game_blacklist.txt"), "rt"
    ) as blacklist_file:
        blacklist = [l.strip() for l in await blacklist_file.readlines()]

    async for row in db.iterate(
        await load_query("judgement_contexts.sql"),
        {"blacklist": blacklist, "limit": limit},
    ):
        yield row


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
    ratings: Dict[str, Dict[int, float]] = {
        "relevance": {},
        "likeability": {},
        "fluency": {},
        "coherence": {},
        "rouge-1": {},
        "rouge-2": {},
        "rouge-3": {},
        "rouge-4": {},
        "rouge-l": {},
        "rouge-w": {},
        "rouge-d": {},
    }

    idx = -1
    ratings_by_model: Dict[str, Dict[str, Dict[int, float]]] = {}
    async for row in get_finalized_suggestions(db):
        idx += 1
        finalized = row["user_text"]
        generated = row["generated_text"]
        model_name = row["model_name"]
        model_ratings = ratings_by_model.get(
            model_name,
            {
                "relevance": {},
                "likeability": {},
                "fluency": {},
                "coherence": {},
                "rouge-1": {},
                "rouge-2": {},
                "rouge-3": {},
                "rouge-4": {},
                "rouge-l": {},
                "rouge-w": {},
                "rouge-d": {},
            },
        )

        diff, diff_score = get_diff_score(generated, finalized)

        finalized_sentences = split_sentences(finalized)
        generated_sentences = split_sentences(generated)
        overlaps = ngram_overlaps(finalized_sentences, generated_sentences)

        edit = {
            "diff": diff,
            "model_name": model_name,
            "overlaps": len(overlaps),
            "finalized_sentences": len(finalized_sentences),
            "generated_sentences": len(generated_sentences),
        }

        for feedback in (
            "comments",
            "relevance",
            "likeability",
            "fluency",
            "coherence",
        ):
            rating = row[feedback]
            edit[feedback] = rating
            if rating and feedback in ratings:
                ratings[feedback][idx] = float(rating)
                model_feedback = model_ratings.get(feedback, {})
                model_feedback[idx] = float(rating)
                model_ratings[feedback] = model_feedback

        scores = rouge.get_scores(
            [" ".join(remove_stopwords(generated))],
            [" ".join(remove_stopwords(finalized))],
        )
        for score_type in ("l", "w") + tuple(str(i) for i in range(1, rouge.max_n + 1)):
            rouge_type = f"rouge-{score_type}"
            edit[rouge_type] = {
                metric: 100 * scores[rouge_type][0][metric][0]
                for metric in ("p", "r", "f")
            }
            if rouge_type in ratings:
                precision = scores[rouge_type][0]["p"][0]
                ratings[rouge_type][idx] = precision
                model_scores = model_ratings.get(rouge_type, {})
                model_scores[idx] = precision
                model_ratings[rouge_type] = model_scores

        rouge_type = "rouge-d"
        edit[rouge_type] = {
            metric: 100 * diff_score[metric] for metric in ("p", "r", "f")
        }
        if rouge_type in ratings:
            precision = diff_score["p"]
            ratings[rouge_type][idx] = precision
            model_scores = model_ratings.get(rouge_type, {})
            model_scores[idx] = precision
            model_ratings[rouge_type] = model_scores

        edits.append(edit)
        ratings_by_model[model_name] = model_ratings

    correlations: Dict[str, Dict[str, str]] = {k: {} for k in ratings}
    for (k1, v1), (k2, v2) in combinations(ratings.items(), 2):
        r, p = pearsonr([v1[k] for k in v2 if k in v1], [v2[k] for k in v1 if k in v2])

        correlation = f"{r:.2f}"
        if p < 0.05:
            correlation += "*"
        if p < 0.01:
            correlation += "*"
        correlations[k1][k2] = correlation

    correlations_by_model: Dict[str, Dict[str, Dict[str, str]]] = {
        model_name: {k: {} for k in ratings} for model_name in ratings_by_model
    }

    for model_name, model_ratings in ratings_by_model.items():
        for (k1, v1), (k2, v2) in combinations(model_ratings.items(), 2):
            r, p = pearsonr(
                [v1[k] for k in v2 if k in v1], [v2[k] for k in v1 if k in v2]
            )

            correlation = f"{r:.2f}"
            if p < 0.05:
                correlation += "*"
            if p < 0.01:
                correlation += "*"
            correlations_by_model[model_name][k1][k2] = correlation

    avg_ratings = await db.fetch_all(await load_query("avg_ratings.sql"))
    for key in ("l", "w", "d") + tuple(str(i) for i in range(1, rouge.max_n + 1)):
        key = f"rouge-{key}"
        for model_name, model_ratings in ratings_by_model.items():
            scores = model_ratings[key]
            mean = statistics.mean(scores.values())
            stddev = statistics.stdev(scores.values())
            avg_ratings.append(
                {
                    "type": key,
                    "model_name": model_name,
                    "avg_rating": f"{mean:.2f}",
                    "rating_stddev": f"{stddev:.2f}",
                    "feedback_count": len(scores),
                }
            )

    ratings_by_type = {
        t: [{k: v for k, v in r.items() if k != "type"} for r in g]
        for t, g in groupby(avg_ratings, lambda x: x["type"])
    }

    return templates.TemplateResponse(
        "index.html",
        {
            "edits": edits,
            "request": request,
            "ratings": avg_ratings,
            "correlations": correlations,
            "correlations_by_model": correlations_by_model,
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
    async for row in get_finalized_suggestions(db):
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


@router.get(
    "/judgement/contexts",
    summary="Return a CSV file of judgement contexts",
    response_description="A CSV file of judgement contexts",
    response_class=PlainTextResponse,
)
async def get_judgement_contexts(
    accept: str = Header(None), db: Database = Depends(get_db)
):
    """
    This method returns a template for the main dashboard of the woolgatherer
    service.
    """
    # Default to the text/csv
    accept = accept or "text/csv"
    if accept == "*/*" or accept == "text/*":
        accept = "text/csv"

    if accept == "text/csv":
        return await get_judgement_contexts_csv(db)

    if accept == "text/json":
        return await get_judgement_contexts_json(db)

    raise HTTPException(HTTP_406_NOT_ACCEPTABLE, f"Invalid Accept Header: {accept}!")


async def get_judgement_contexts_csv(db: Database):
    """ Get judgement contexts as CSV """

    def create_csv_row():
        csv_row = io.StringIO()
        writer = csv.DictWriter(
            csv_row,
            fieldnames=[
                "suggestion_id",
                "model_name",
                "character_name",
                "character_description",
                "challenge_name",
                "challenge_text",
                "challenge_success_description",
                "challenge_failure_description",
                "played_card_1_name",
                "played_card_1_description",
                "previous_entry_text",
                "suggestion_text",
            ],
        )
        return csv_row, writer

    async def get_as_csv():
        """ Iteratively yield CSV """
        csv_row, writer = create_csv_row()
        writer.writeheader()
        yield csv_row.getvalue()

        async for row in select_judgement_contexts(db):
            csv_row, writer = create_csv_row()
            story = json.loads(row["story"])
            generated = json.loads(row["generated"])
            model_name = row["model_name"]
            suggestion_id = row["suggestion_id"]

            scenes = story["scenes"]
            previous_entry: Dict[str, Any] = {}
            if scenes:
                entries = scenes[-1]["entries"]
                if entries:
                    previous_entry = entries[-1]

            character: Dict[str, Any] = {}
            character_id = generated["character_seq_id"]
            challenge = generated["target_challenge_card"]
            cards = generated["cards_played_on_challenge"]
            for character_info in story["characters"]:
                if character_id == character_info["character_seq_id"]:
                    character = character_info
                    break

            if not cards:
                logging.fatal(f"Missing card data in suggestion {suggestion_id}")
                continue

            if not character:
                logging.fatal(
                    f"Missing character data for {character_id}"
                    f" in suggestion {suggestion_id}"
                )
                continue

            row_data = {}
            row_data["model_name"] = model_name
            row_data["suggestion_id"] = suggestion_id
            row_data["character_name"] = character["name"]
            row_data["character_description"] = character["description"]
            row_data["challenge_name"] = challenge["name"]
            row_data["challenge_text"] = challenge["description"]
            row_data["challenge_success_description"] = challenge["success_stakes"]
            row_data["challenge_failure_description"] = challenge["failure_stakes"]
            row_data["played_card_1_name"] = cards[0]["name"]
            row_data["played_card_1_description"] = cards[0]["description"]
            row_data["suggestion_text"] = generated["description"]
            row_data["previous_entry_text"] = (
                previous_entry["description"] if previous_entry else ""
            )

            writer.writerow(row_data)

            yield csv_row.getvalue()

    return StreamingResponse(get_as_csv(), media_type="text/csv")


async def get_judgement_contexts_json(db: Database):
    """ Get judgement contexts as JSON """

    async def get_as_json():
        """ Iteratively yield JSON """
        yield "["
        idx = -1
        async for row in select_judgement_contexts(db):
            idx += 1
            story = json.loads(row["story"])
            finalized = json.loads(row["finalized"])
            generated = json.loads(row["generated"])
            model_name = row["model_name"]

            yield (",\n" if idx else "\n") + json.dumps(
                {
                    "model_name": model_name,
                    "story": story,
                    "generated": generated,
                    "finalized": finalized,
                },
                indent=2,
            )
        yield "\n]"

    return StreamingResponse(get_as_json(), media_type="text/json")
