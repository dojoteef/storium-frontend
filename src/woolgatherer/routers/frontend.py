"""
This router handles the website frontend
"""
import os

import aiofiles
import markdown
from fastapi import APIRouter
from starlette.requests import Request

from woolgatherer.utils.routing import CompressibleRoute
from woolgatherer.utils.templating import TemplateResponse


router = APIRouter()
router.route_class = CompressibleRoute

LICENSE = ""


async def initialize():
    """ Initialize the frontend """
    global LICENSE  # pylint: disable=global-statement
    async with aiofiles.open(
        os.path.join("dataset", "LICENSE.md"), "rt"
    ) as license_file:
        LICENSE = markdown.markdown(await license_file.read())


@router.get("/", summary="Get the frontend for the woolgatherer service")
async def get_frontend(request: Request):
    """
    This method returns a template for the website frontend
    """
    return TemplateResponse(request, "frontend/index.html", {"license": LICENSE})
