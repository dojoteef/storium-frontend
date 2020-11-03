"""
This router handles the dashboard endpoints.
"""
import os
import statistics
from asyncio import gather
from typing import Any, AsyncGenerator, Dict, List, Mapping, Sequence
from itertools import combinations, groupby

import aiofiles
from aiocache import caches
from databases import Database
from fastapi import APIRouter, Depends
from scipy.stats import pearsonr
from starlette.requests import Request

from woolgatherer.db.session import get_db
from woolgatherer.db.utils import load_query
from woolgatherer.db_models.figmentator import FigmentatorStatus
from woolgatherer.metrics import get_diff_score, remove_stopwords, rouge
from woolgatherer.models.range import split_sentences
from woolgatherer.utils.auth import parse_scopes
from woolgatherer.utils.routing import CompressibleRoute
from woolgatherer.utils.templating import TemplateResponse
from woolgatherer.utils import ngram_overlaps


MAX_PUBLIC_EDITS = 10


router = APIRouter()
router.route_class = CompressibleRoute


async def get_finalized_suggestions(
    db: Database, status: Sequence[FigmentatorStatus] = (FigmentatorStatus.active,)
) -> AsyncGenerator[Mapping, None]:
    """ Load the finalized suggestions """
    async with aiofiles.open(
        os.path.join("static", "game_blacklist.txt"), "rt"
    ) as blacklist_file:
        blacklist = [l.strip() for l in await blacklist_file.readlines()]

    async for row in db.iterate(
        await load_query("finalized_suggestions.sql"),
        {"status": status, "blacklist": blacklist},
    ):
        yield row


# TODO: refactor to make this function more modular
# pylint:disable=too-many-locals
@router.get("/", summary="Get the main dashboard for the woolgatherer service")
async def get_dashboard(
    request: Request,
    status: FigmentatorStatus = FigmentatorStatus.active,
    db: Database = Depends(get_db),
):
    """
    This method returns a template for the main dashboard of the woolgatherer
    service.
    """
    query = await load_query("suggestion_counts_by_user.sql")
    suggestion_counts = {}
    for c in [1, 5, 10, 20, float("inf")]:
        result = await db.fetch_one(
            query, values={"suggestion_count": c, "status": (status,)}
        )
        if not result:
            continue

        suggestion_counts[c] = result["unique_user_count"]

    edits: List[Dict[str, Any]] = []
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
        "user": {},
    }

    idx = -1
    all_models = set()
    cache_updates = []
    cache = caches.get("default")
    scopes = parse_scopes(request)
    ratings_by_model: Dict[str, Dict[str, Dict[int, float]]] = {}
    async for row in get_finalized_suggestions(db, status=(status,)):
        idx += 1
        game_pid = row["game_pid"]
        finalized = row["user_text"]
        generated = row["generated_text"]
        model_name = row["model_name"]
        suggestion_id = row["suggestion_id"]

        all_models.add(model_name)

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
                "user": {},
            },
        )

        cache_key = f"suggestion:{suggestion_id}:metrics"
        suggestion_metrics = await cache.get(cache_key)
        if suggestion_metrics is None:
            suggestion_metrics = {}
            diff, diff_score = get_diff_score(generated, finalized)

            finalized_sentences = split_sentences(finalized)
            generated_sentences = split_sentences(generated)

            rouge_scores = rouge.get_scores(
                [" ".join(remove_stopwords(generated))],
                [" ".join(remove_stopwords(finalized))],
            )

            suggestion_metrics["diff"] = diff
            suggestion_metrics["diff_score"] = diff_score
            suggestion_metrics["rouge_scores"] = rouge_scores
            suggestion_metrics["finalized_sentences"] = finalized_sentences
            suggestion_metrics["generated_sentences"] = generated_sentences
            cache_updates.append(cache.set(cache_key, suggestion_metrics))

        diff = suggestion_metrics["diff"]
        diff_score = suggestion_metrics["diff_score"]
        rouge_scores = suggestion_metrics["rouge_scores"]
        finalized_sentences = suggestion_metrics["finalized_sentences"]
        generated_sentences = suggestion_metrics["generated_sentences"]

        edit = {"diff": diff, "game_pid": game_pid, "model_name": model_name}

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

        for score_type in ("l", "w") + tuple(str(i) for i in range(1, rouge.max_n + 1)):
            rouge_type = f"rouge-{score_type}"
            edit[rouge_type] = {
                metric: 100 * rouge_scores[rouge_type][0][metric][0]
                for metric in ("p", "r", "f")
            }
            if rouge_type in ratings:
                precision = 100 * rouge_scores[rouge_type][0]["p"][0]
                ratings[rouge_type][idx] = precision
                model_scores = model_ratings.get(rouge_type, {})
                model_scores[idx] = precision
                model_ratings[rouge_type] = model_scores

        rouge_type = "user"
        edit[rouge_type] = {
            metric: 100 * diff_score[metric] for metric in ("p", "r", "f")
        }
        if rouge_type in ratings:
            precision = 100 * diff_score["p"]
            ratings[rouge_type][idx] = precision
            model_scores = model_ratings.get(rouge_type, {})
            model_scores[idx] = precision
            model_ratings[rouge_type] = model_scores

        if "user_edits" in scopes or len(edits) < MAX_PUBLIC_EDITS:
            edits.append(edit)

        ratings_by_model[model_name] = model_ratings

    cache_key = f"suggestion:*:metrics:correlations"
    all_correlations: Dict[str, Dict[str, Dict[str, float]]] = await cache.get(
        cache_key
    )
    if cache_updates or all_correlations is None:
        all_correlations = {k: {} for k in ratings}

        for (k1, v1), (k2, v2) in combinations(ratings.items(), 2):
            r, p = pearsonr(
                [v1[k] for k in v2 if k in v1], [v2[k] for k in v1 if k in v2]
            )

            all_correlations[k1][k2] = {"r": r, "p": p}

        cache_updates.append(cache.set(cache_key, all_correlations))

    cache_key = f"suggestion:*:metrics:correlations:by_model"
    correlations_by_model: Dict[
        str, Dict[str, Dict[str, Dict[str, float]]]
    ] = await cache.get(cache_key)
    if cache_updates or correlations_by_model is None:
        correlations_by_model = {
            model_name: {k: {} for k in ratings} for model_name in ratings_by_model
        }

        for model_name, model_ratings in ratings_by_model.items():
            for (k1, v1), (k2, v2) in combinations(model_ratings.items(), 2):
                r, p = pearsonr(
                    [v1[k] for k in v2 if k in v1], [v2[k] for k in v1 if k in v2]
                )

                correlations_by_model[model_name][k1][k2] = {"r": r, "p": p}

        cache_updates.append(cache.set(cache_key, correlations_by_model))

    cache_key = f"suggestion:*:metrics:ratings:avg"
    avg_ratings = await cache.get(cache_key)
    if cache_updates or avg_ratings is None:
        avg_ratings = await db.fetch_all(
            await load_query("avg_ratings.sql"), {"status": (status,)}
        )

        # Convert to an actual dict, since the rows are returned in a "Record"
        avg_ratings = [dict(row) for row in avg_ratings]
        for key in ("user", "rouge-l", "rouge-w") + tuple(
            f"rouge-{i}" for i in range(1, rouge.max_n + 1)
        ):
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

        cache_updates.append(cache.set(cache_key, avg_ratings))

    ratings_by_type = {
        t: [{k: v for k, v in r.items() if k != "type"} for r in g]
        for t, g in groupby(avg_ratings, lambda x: x["type"])
    }

    if cache_updates:
        await gather(*cache_updates)

    return TemplateResponse(
        request,
        "dashboard/index.html",
        {
            "edits": edits,
            "models": all_models,
            "ratings": avg_ratings,
            "all_correlations": all_correlations,
            "correlations_by_model": correlations_by_model,
            "ratings_by_type": ratings_by_type,
            "suggestion_counts": suggestion_counts,
        },
    )


# pylint:enable=too-many-locals


@router.get(
    "/sentence/histogram",
    summary="Get the sentence histogram",
    response_description="A dictionary of mapping sentences number to overlap",
)
async def get_sentence_histogram(
    model: str = None,
    status: FigmentatorStatus = FigmentatorStatus.active,
    db: Database = Depends(get_db),
):
    """
    This method returns a template for the main dashboard of the woolgatherer
    service.
    """
    histogram: Dict[int, int] = {}
    async for row in get_finalized_suggestions(db, status=(status,)):
        # TODO: It would be better to have this filtering in SQL
        if model and model != row["model_name"]:
            continue

        finalized = row["user_text"]
        generated = row["generated_text"]

        finalized_sentences = split_sentences(finalized)
        generated_sentences = split_sentences(generated)
        overlaps = ngram_overlaps(finalized_sentences, generated_sentences)

        for idx in overlaps:
            histogram[idx] = histogram.get(idx, 0) + 1

    return histogram
