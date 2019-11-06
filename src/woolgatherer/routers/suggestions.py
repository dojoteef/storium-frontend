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
from woolgatherer.db.utils import uuid_str
from woolgatherer.db_models.storium import StoryStatus
from woolgatherer.models.utils import Field
from woolgatherer.models.storium import SceneEntry
from woolgatherer.models.feedback import FeedbackPrompt, FeedbackResponse
from woolgatherer.models.suggestion import SuggestionType, SuggestionStatus
from woolgatherer.ops import (
    feedback as feedback_ops,
    stories as story_ops,
    suggestions as suggestion_ops,
)
from woolgatherer.utils.routing import CompressibleRoute


router = APIRouter()
router.route_class = CompressibleRoute


class SuggestionCreatedResponse(BaseModel):
    """ The response for when a suggestion is being created """

    suggestion_id: str = Field(
        ..., description="The id of the suggestion being created"
    )
    required_feedback: List[FeedbackPrompt] = Field(
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
    response_model_skip_defaults=True,
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
    story_status = await story_ops.get_story_status(story_id, db=db)
    if story_status is None:
        raise HTTPException(HTTP_404_NOT_FOUND, detail="Unknown story")

    if story_status is not StoryStatus.ready:
        raise HTTPException(HTTP_404_NOT_FOUND, detail="Story data missing")

    suggestion, required_feedback = await suggestion_ops.get_or_create_suggestion(
        story_id, context, suggestion_type, db=db
    )

    if suggestion:
        return SuggestionCreatedResponse(
            suggestion_id=uuid_str(suggestion.uuid), required_feedback=required_feedback
        )

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
    suggestion = await suggestion_ops.get_suggestion(UUID(suggestion_id), db=db)
    if suggestion is None:
        raise HTTPException(HTTP_404_NOT_FOUND, detail="Unknown suggestion")

    # For some reason FastAPI doesn't like it if I return the SuggestionResponse
    # directly, but if I return it as a dict and have it convert to a SuggestionResponse
    # then it works fine... don't have time to figure out why this is happening right
    # now.
    return {"suggestion": suggestion.generated, "status": suggestion.status}


@router.post("/{suggestion_id}/feedback", summary="Submit feedback")
async def submit_feedback(
    suggestion_id: str = Path(
        ..., description="""The suggestion_id for the suggestion the user evaluated."""
    ),
    feedback: List[FeedbackResponse] = Body(
        ..., description="""The responses to the required feedback."""
    ),
    db: Database = Depends(get_db),
):
    """
    Submit user feedback for a suggestion. After providing a Suggestion to the
    user, this endpoint allows for providing  any feedback requested when the
    Suggestion was generated.
    """
    await feedback_ops.submit_feedback(UUID(suggestion_id), feedback, db=db)


@router.post("/{suggestion_id}/finalize", summary="Finalize a Suggestion")
async def finalize_suggestion(
    suggestion_id: str = Path(
        ..., description="""The suggestion_id for the suggestion the user evaluated."""
    ),
    entry: SceneEntry = Body(..., description="""The move that the user submitted."""),
    db: Database = Depends(get_db),
):
    """
    Finalize a Suggestion which has been accepted by the user. After providing a
    Suggestion to the user, this endpoint allows for providing the final accepted entry
    context.
    """
    await suggestion_ops.finalize_suggestion(UUID(suggestion_id), entry, db=db)
