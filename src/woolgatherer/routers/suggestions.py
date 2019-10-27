"""
This router handles the suggestion endpoints.
"""
from uuid import UUID
from typing import List
from pydantic import BaseModel
from databases import Database
from fastapi import APIRouter, Body, Path, HTTPException, Depends
from starlette.status import HTTP_202_ACCEPTED, HTTP_404_NOT_FOUND, HTTP_400_BAD_REQUEST

from woolgatherer.db.session import get_db
from woolgatherer.db_models.storium import Suggestion
from woolgatherer.models.utils import Field
from woolgatherer.models.storium import SceneEntry
from woolgatherer.models.suggestion import Feedback, SuggestionType, SuggestionStatus
from woolgatherer.ops import stories as story_ops, suggestions as suggestion_ops


router = APIRouter()


class SuggestionCreatedResponse(BaseModel):
    """ The response for when a suggestion is being created """

    suggestion_id: str = Field(
        ..., description="The id of the suggestion being created"
    )
    required_feedback: List[Feedback] = Field(
        ...,
        description="""A list of feedback required when the user completes their
        move after the receiving the suggestion.""",
    )


class SuggestionResponse(BaseModel):
    """ The response for a story's status """

    status: SuggestionStatus = Field(..., description="The status of the story")
    suggestion: SceneEntry = Field(..., description="""The generated suggestion""")


@router.post(
    "/create",
    status_code=HTTP_202_ACCEPTED,
    summary="Generate a Suggestion",
    response_description="""On success, you should expect to receive an HTTP 202
    response denoting that the long running process of creating a suggestion has been
    accepted, along with a Location that can be used to query for the suggestion.
    Additionally, you will recieve a list of feedback we desire from the user once the
    scene entry is finalized.""",
    response_model=SuggestionCreatedResponse,
)
async def create_suggestion(
    story_id: str = Body(
        ..., description="""The id of the story to create a suggestion for"""
    ),
    context: SceneEntry = Body(
        ..., description="""The current context of the move in progress"""
    ),
    suggestion_type: SuggestionType = Body(
        ..., alias="type", description="""The type of suggestion to create"""
    ),
    db: Database = Depends(get_db),
):
    """
    Use this method to initiate gnerating a new Suggestion. The process of generating a
    suggestion is a long running process. You **MUST** upload the story in full before
    invoking this endpoint.
    """
    story_status = await story_ops.get_story_status(db, story_id)
    if story_status is None:
        raise HTTPException(HTTP_404_NOT_FOUND, detail="Unknown story")

    suggestion = await suggestion_ops.get_or_create_suggestion(
        db, story_id, context, suggestion_type
    )

    if suggestion:
        return SuggestionCreatedResponse(
            suggestion_id=suggestion.get_id_str(), required_feedback=[]
        )
    else:
        raise HTTPException(HTTP_400_BAD_REQUEST, detail="Create request misspecified")


@router.get(
    "/{suggestion_id}",
    summary="Get a generated Suggestion",
    response_description="""Returns the suggestion and its status""",
    response_model=SuggestionResponse,
)
async def get_suggestion(
    suggestion_id: str = Path(
        ...,
        description="""The suggestion_id for the suggestion you want to retrieve.""",
    ),
    db: Database = Depends(get_db),
):
    """
    Query for a Suggestion. If the Suggestion has been successfully generated, it will
    return the suggestion. Otherwise it will return a status message indicating the
    suggestion is still pending.
    """
    suggestion = await suggestion_ops.get_suggestion_by_id(db, UUID(suggestion_id))
    if suggestion is None:
        raise HTTPException(HTTP_404_NOT_FOUND, detail="Unknown suggestion")

    return {"suggestion": suggestion.generated, "status": suggestion.status}


@router.post("/{suggestion_id}/finalize", summary="Finalize a Suggestion")
async def finalize_suggestion(
    entry: SceneEntry, feedback: Feedback, db: Database = Depends(get_db)
):
    """
    Finalize a Suggestion which has been accepted by the user. After providing a
    Suggestion to the user, this endpoint allows for providing the final accepted entry
    context as well as any feedback requested when the Suggestion was generated.
    """
