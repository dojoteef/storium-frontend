"""
This router handles the stories endpoints.
"""
import io
import os
import csv
import json
import logging
from difflib import Differ, SequenceMatcher
from typing import Any, Dict, List, Set, Tuple
from itertools import combinations, groupby

import aiofiles
from rouge import Rouge
from nltk import word_tokenize
from databases import Database
from fastapi import APIRouter, Depends
from scipy.stats import pearsonr
from starlette.requests import Request
from starlette.responses import PlainTextResponse
from starlette.templating import Jinja2Templates

from woolgatherer.db.session import get_db
from woolgatherer.db.utils import load_query
from woolgatherer.models.range import split_sentences
from woolgatherer.utils.routing import CompressibleRoute
from woolgatherer.utils import ngram_overlaps


router = APIRouter()
router.route_class = CompressibleRoute

stopwords: Set[str] = set()
templates = Jinja2Templates(directory="templates")

differ = Differ()
rouge = Rouge(
    metrics=["rouge-n", "rouge-l", "rouge-w"],
    max_n=4,
    limit_length=False,
    apply_avg=False,
    apply_best=False,
    alpha=0.5,
    weight_factor=1.2,
    stemming=False,
)


async def load_stopwords():
    """ Load the stopword list """
    async with aiofiles.open(
        os.path.join("static", "stopwords.txt"), "rt"
    ) as stopword_file:
        stopwords.update(l.strip() for l in await stopword_file.readlines())


async def get_finalized_suggestions(db: Database):
    """ Load the finalized suggestions """
    async with aiofiles.open(
        os.path.join("static", "game_blacklist.txt"), "rt"
    ) as blacklist_file:
        blacklist = [l.strip() for l in await blacklist_file.readlines()]

    return await db.fetch_all(
        await load_query("finalized_suggestions.sql"), {"blacklist": blacklist}
    )


async def select_judgement_contexts(db: Database, limit: int = 100):
    """ Load the finalized suggestions """
    async with aiofiles.open(
        os.path.join("static", "game_blacklist.txt"), "rt"
    ) as blacklist_file:
        blacklist = [l.strip() for l in await blacklist_file.readlines()]

    return await db.fetch_all(
        await load_query("judgement_contexts.sql"),
        {"blacklist": blacklist, "limit": limit},
    )


def get_diff_score(
    hypothesis: str, reference: str
) -> Tuple[List[Tuple[str, str]], Dict[str, float]]:
    """
    Return the op code and text as a tuple.
    """

    # pylint:disable=protected-access
    def get_substring(text: str, text_lc: str, start: int, tokens) -> Tuple[str, int]:
        """
        Get the original substring from the text for the given sequence of tokens
        """
        token = ""
        end = start
        for token in tokens:
            end = text_lc.find(token, end)
        end += len(token)

        return text[start:end], end

    score = 0.0
    reference_index = 0
    hypothesis_index = 0
    reference_lc = reference.lower()
    hypothesis_lc = hypothesis.lower()
    reference_tokens = rouge._preprocess_summary_as_a_whole(reference)[0].split()
    hypothesis_tokens = rouge._preprocess_summary_as_a_whole(hypothesis)[0].split()

    diffs: List[Tuple[str, str]] = []
    matcher = SequenceMatcher(isjunk=None, a=hypothesis_tokens, b=reference_tokens)
    for tag, alo, ahi, blo, bhi in matcher.get_opcodes():
        if tag == "equal":
            diff_text, hypothesis_index = get_substring(
                hypothesis, hypothesis_lc, hypothesis_index, hypothesis_tokens[alo:ahi]
            )
            diff_text, reference_index = get_substring(
                reference, reference_lc, reference_index, reference_tokens[blo:bhi]
            )
            diff_class = "table-default"
            if any(
                token.lower() not in stopwords for token in hypothesis_tokens[alo:ahi]
            ):
                diff_class = "table-warning"
                score += ahi - alo

            diffs.append((diff_class, diff_text))
        else:
            if tag == "delete":
                diff_text, hypothesis_index = get_substring(
                    hypothesis,
                    hypothesis_lc,
                    hypothesis_index,
                    hypothesis_tokens[alo:ahi],
                )
                diffs.append(("table-danger", diff_text))
            elif tag == "insert":
                diff_text, reference_index = get_substring(
                    reference, reference_lc, reference_index, reference_tokens[blo:bhi]
                )
                diffs.append(("table-success", diff_text))
            elif tag == "replace":
                diff_text, hypothesis_index = get_substring(
                    hypothesis,
                    hypothesis_lc,
                    hypothesis_index,
                    hypothesis_tokens[alo:ahi],
                )
                diffs.append(("table-danger", diff_text))
                diff_text, reference_index = get_substring(
                    reference, reference_lc, reference_index, reference_tokens[blo:bhi]
                )
                diffs.append(("table-success", diff_text))

    return (
        diffs,
        rouge._compute_p_r_f_score(
            len(hypothesis_tokens), len(reference_tokens), score
        ),
    )
    # pylint:enable=protected-access


def remove_stopwords(text: str) -> List[str]:
    """ Remove stop words from the given text """
    return [token for token in word_tokenize(text) if token.lower() not in stopwords]


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

    ratings_by_model: Dict[str, Dict[str, Dict[int, float]]] = {}
    for idx, row in enumerate(await get_finalized_suggestions(db)):
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
    for row in await get_finalized_suggestions(db):
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
async def get_judgement_contexts(db: Database = Depends(get_db)):
    """
    This method returns a template for the main dashboard of the woolgatherer
    service.
    """
    judgements_contexts = io.StringIO()
    writer = csv.DictWriter(
        judgements_contexts,
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
    writer.writeheader()
    for row in await select_judgement_contexts(db):
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
                f"Missing character data for {character_id} in suggestion {suggestion_id}"
            )
            continue

        csv_row = {}
        csv_row["model_name"] = model_name
        csv_row["suggestion_id"] = suggestion_id
        csv_row["character_name"] = character["name"]
        csv_row["character_description"] = character["description"]
        csv_row["challenge_name"] = challenge["name"]
        csv_row["challenge_text"] = challenge["description"]
        csv_row["challenge_success_description"] = challenge["success_stakes"]
        csv_row["challenge_failure_description"] = challenge["failure_stakes"]
        csv_row["played_card_1_name"] = cards[0]["name"]
        csv_row["played_card_1_description"] = cards[0]["description"]
        csv_row["suggestion_text"] = generated["description"]
        csv_row["previous_entry_text"] = (
            previous_entry["description"] if previous_entry else ""
        )

        writer.writerow(csv_row)

    return judgements_contexts.getvalue()
