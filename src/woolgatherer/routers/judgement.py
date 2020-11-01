"""
This router handles the website frontend
"""
import os
import io
import csv
import json
import logging
from typing import Any, AsyncGenerator, Dict, Mapping, Sequence

import aiofiles
from databases import Database
from fastapi import APIRouter, Depends, Header, HTTPException
from starlette.status import HTTP_401_UNAUTHORIZED, HTTP_406_NOT_ACCEPTABLE
from starlette.responses import PlainTextResponse, StreamingResponse
from starlette.requests import Request

from woolgatherer.db.session import get_db
from woolgatherer.db.utils import load_query
from woolgatherer.db_models.figmentator import FigmentatorStatus


router = APIRouter()


async def select_judgement_contexts(
    db: Database,
    limit: int = 0,
    status: Sequence[FigmentatorStatus] = (FigmentatorStatus.active,),
) -> AsyncGenerator[Mapping, None]:
    """ Load the finalized suggestions """
    async with aiofiles.open(
        os.path.join("static", "game_blacklist.txt"), "rt"
    ) as blacklist_file:
        blacklist = [l.strip() for l in await blacklist_file.readlines()]

    async for row in db.iterate(
        await load_query("judgement_contexts.sql"),
        {
            "status": status,
            "blacklist": blacklist,
            "limit": float("inf") if not limit else limit,
        },
    ):
        yield row


@router.get(
    "/contexts",
    summary="Return a CSV file of judgement contexts",
    response_description="A CSV file of judgement contexts",
    response_class=PlainTextResponse,
)
async def get_judgement_contexts(
    request: Request,
    limit: int = 0,
    status: FigmentatorStatus = FigmentatorStatus.active,
    accept: str = Header(None),
    db: Database = Depends(get_db),
):
    """
    This method returns a template for the main dashboard of the woolgatherer
    service.
    """
    # Default to the text/csv
    accept = accept or "text/csv"
    if accept in ("*/*", "text/*"):
        accept = "text/csv"

    if accept == "text/csv":
        return await get_judgement_contexts_csv(db, limit=limit, status=status)

    if accept == "text/json":
        return await get_judgement_contexts_json(db, limit=limit, status=status)

    raise HTTPException(HTTP_406_NOT_ACCEPTABLE, f"Invalid Accept Header: {accept}!")


async def get_judgement_contexts_csv(
    db: Database, status: FigmentatorStatus, limit: int = 0
):
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

        async for row in select_judgement_contexts(db, limit=limit, status=(status,)):
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


async def get_judgement_contexts_json(
    db: Database, status: FigmentatorStatus, limit: int = 0
):
    """ Get judgement contexts as JSON """

    async def get_as_json():
        """ Iteratively yield JSON """
        yield "["
        idx = -1
        async for row in select_judgement_contexts(db, limit=limit, status=(status,)):
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
