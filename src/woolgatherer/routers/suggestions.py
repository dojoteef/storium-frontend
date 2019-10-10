'''
This router handles the suggestion endpoints.
'''
from fastapi import APIRouter
from starlette.status import HTTP_202_ACCEPTED

from woolgatherer.models.storium import SceneEntry
from woolgatherer.models.suggestion import Feedback


router = APIRouter()


@router.post(
    '/create',
    status_code=HTTP_202_ACCEPTED,
    summary='Generate a Suggestion',
    response_description='On success, you should expect to receive an HTTP 202 response denoting '
    'that the long running process of creating a suggestion has been accepted, along with a '
    'Location that can be used to query for the suggestion.'
)
async def create_suggestion():
    '''
    Use this method to initiate gnerating a new Suggestion. The process of gnerating a suggestion is
    a long running process. You **MUST** upload the story in full before you invoking this endpoint.
    '''


@router.get(
    '/{suggestion_id}',
    summary='Get a generated Suggestion'
)
async def get_suggestion():
    '''
    Query for a Suggestion. If the Suggestion has been successfully generated, it will return the
    suggestion. Otherwise it will return a status message indicating the suggestion is still
    pending.
    '''


@router.post(
    '/{suggestion_id}/finalize',
    summary='Finalize a Suggestion',
)
async def finalize_suggestion(entry: SceneEntry, feedback: Feedback):
    '''
    Finalize a Suggestion which has been accepted by the user. After providing a Suggestion to the
    user, this endpoint allows for providing the final accepted entry context as well as any
    feedback requested when the Suggestion was generated.
    '''
