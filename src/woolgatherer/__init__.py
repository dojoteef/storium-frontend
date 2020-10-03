"""
Main entry point for woolgatherer. This is where we setup the app.
"""
import os

from fastapi import Depends, FastAPI
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.middleware.gzip import GZipMiddleware
from starlette.middleware.authentication import AuthenticationMiddleware
from starlette.staticfiles import StaticFiles
from starlette.status import (
    HTTP_403_FORBIDDEN,
    HTTP_404_NOT_FOUND,
    HTTP_503_SERVICE_UNAVAILABLE,
)

from woolgatherer.db.session import open_connection_pool, close_connection_pool
from woolgatherer.errors import InvalidOperationError, InsufficientCapacityError
from woolgatherer.metrics import initialize_metrics
from woolgatherer.routers import dashboard, stories, suggestions
from woolgatherer.utils.auth import Requires, TokenAuthBackend


app = FastAPI(debug=bool(int(os.environ.get("DEBUG", 0))))
app.mount("/static", StaticFiles(directory="static"), name="static")
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(
    AuthenticationMiddleware,
    backend=TokenAuthBackend(os.environ.get("GW_ACCESS_TOKEN")),
)

app.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
app.include_router(
    stories.router,
    prefix="/stories",
    tags=["stories"],
    dependencies=[Depends(Requires("backend", status_code=HTTP_404_NOT_FOUND))],
)
app.include_router(
    suggestions.router,
    prefix="/suggestions",
    tags=["suggestions"],
    dependencies=[Depends(Requires("backend", status_code=HTTP_404_NOT_FOUND))],
)

app.add_event_handler("startup", open_connection_pool)
app.add_event_handler("shutdown", close_connection_pool)

app.add_event_handler("startup", initialize_metrics)


@app.exception_handler(InvalidOperationError)
async def invalid_operation_exception_handler(
    request: Request, exception: InvalidOperationError  # pylint:disable=unused-argument
):
    """ A handler for invalid operation errors """
    return JSONResponse(
        status_code=HTTP_403_FORBIDDEN, content={"message": str(exception)}
    )


@app.exception_handler(InsufficientCapacityError)
async def insufficent_capacity_exception_handler(
    request: Request,  # pylint:disable=unused-argument
    exception: InsufficientCapacityError,
):
    """ A handler for invalid operation errors """
    return JSONResponse(
        status_code=HTTP_503_SERVICE_UNAVAILABLE, content={"message": str(exception)}
    )
