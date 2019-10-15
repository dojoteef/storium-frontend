"""
This router handles the stories endpoints.
"""
from pydantic import BaseModel
from fastapi import APIRouter, Body, Path, HTTPException
from starlette.status import HTTP_202_ACCEPTED, HTTP_404_NOT_FOUND
from starlette.requests import Request
from starlette.responses import Response

from woolgatherer.models.utils import Field
from woolgatherer.models.stories import StoryStatus


router = APIRouter()


class StoryCreatedResponse(BaseModel):
    """ The response for when a story is created """

    story_id: str = Field(..., description="The id of the story which was created")


class StoryStatusResponse(BaseModel):
    """ The response for a story's status """

    status: StoryStatus = Field(..., description="The status of the story")


@router.post(
    "/create",
    status_code=HTTP_202_ACCEPTED,
    summary="Upload a Story",
    response_description="""On success, you should expect to receive an HTTP 202
    response denoting that the story upload has completed and a long running
    preprocess job has been accepted, along with a Location that can be used to query
    the preprocessing status of the story.""",
    response_model=StoryCreatedResponse,
)
async def create_story(
    request: Request,
    response: Response,
    story: BaseModel = Body(
        ...,
        description="""A story in the [Storium export format]
        (https://storium.com/help/export/json/0.9.2).""",
    ),
):
    """
    Use this method to upload a story to the service. You **MUST** upload the story in full before
    making a request to generate a suggestion. The process of creating a story on the service also
    involves preprocessing to make it quicker to serve suggestions. Therefore it may make sense to
    upload stories well in advance of requesting a suggestion. This may help reduce latency in
    generating a suggestion.
    """
    story_id = "<db_hash>"
    base_path = request.url.path.rstrip("/create")
    response.headers["Location"] = f"{base_path}/{story_id}/status"

    return StoryCreatedResponse(story_id=story_id)


@router.get(
    "/{story_id}/status",
    summary="Check the status of a Story upload",
    response_description="Returns the status of the Story upload",
    response_model=StoryStatusResponse,
)
async def get_story_status(
    story_id: str = Path(
        ...,
        description=""" The story_id for the story you want to check the status of.""",
    ),
):
    """
    This method can be used to see the status of a Story that is currently being preprocessed.
    """
    if story_id == "unknown":
        raise HTTPException(HTTP_404_NOT_FOUND, detail="Unknown story")

    return StoryStatusResponse(status=StoryStatus.pending)
