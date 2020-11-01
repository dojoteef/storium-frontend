"""
This router handles the website frontend
"""
import os

from fastapi import APIRouter, HTTPException
from starlette.status import HTTP_404_NOT_FOUND
from starlette.responses import FileResponse

from woolgatherer.utils.settings import Settings


router = APIRouter()


@router.get("/download", summary="Download the dataset")
async def download():
    """
    Initiate a download if the user is logged in an authorized
    """
    if not Settings.dataset:
        raise HTTPException(HTTP_404_NOT_FOUND, "Dataset path not specified")

    dataset_path = os.path.join("dataset", Settings.dataset)
    if not os.path.isfile(dataset_path):
        raise HTTPException(HTTP_404_NOT_FOUND, f"Cannot find {Settings.dataset}")

    return FileResponse(dataset_path, filename=Settings.dataset)
