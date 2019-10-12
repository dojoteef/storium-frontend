"""
This router handles the stories endpoints.
"""
from pydantic import Json
from fastapi import APIRouter, Body
from starlette.status import HTTP_202_ACCEPTED


router = APIRouter()


@router.post(
    "/create",
    status_code=HTTP_202_ACCEPTED,
    summary="Upload a Story",
    response_description="On success, you should expect to receive an HTTP 202 response denoting "
    "that the story upload has completed and a long running preprocess job has been accepted, "
    "along with a Location that can be used to query the preprocessing status of the story.",
)
async def create_story(
    story: Json = Body(
        ...,
        description="A story in the [Storium export format]"
        "(https://storium.com/help/export/json/0.9.2).",
    )
):
    """
    Use this method to upload a story to the service. You **MUST** upload the story in full before
    making a request to generate a suggestion. The process of creating a story on the service also
    involves preprocessing to make it quicker to serve suggestions. Therefore it may make sense to
    upload stories well in advance of requesting a suggestion. This may help reduce latency in
    generating a suggestion.
    """


@router.get(
    "/{story_id}/status",
    summary="Check the status of a Story upload",
    response_description="",
)
async def get_story_status():
    """
    This method can be used to see the status of a Story that is currently being preprocessed.
    """
