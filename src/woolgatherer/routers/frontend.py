"""
This router handles the website frontend
"""
from fastapi import APIRouter
from starlette.requests import Request

from woolgatherer.utils.routing import CompressibleRoute
from woolgatherer.utils.templating import templates


router = APIRouter()
router.route_class = CompressibleRoute


@router.get("/", summary="Get the frontend for the woolgatherer service")
async def get_dashboard(request: Request):
    """
    This method returns a template for the website frontend
    """

    return templates.TemplateResponse("frontend/index.html", {"request": request})
