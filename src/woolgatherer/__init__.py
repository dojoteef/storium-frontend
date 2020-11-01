"""
Main entry point for woolgatherer. This is where we setup the app.
"""
import logging
import urllib
from typing import Any, Dict

import aiocache
from fastapi import Depends, FastAPI
from fastapi.exceptions import HTTPException
from fastapi.exception_handlers import http_exception_handler
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.middleware.gzip import GZipMiddleware
from starlette.middleware.authentication import AuthenticationMiddleware
from starlette.middleware.sessions import SessionMiddleware
from starlette.staticfiles import StaticFiles
from starlette.status import (
    HTTP_401_UNAUTHORIZED,
    HTTP_403_FORBIDDEN,
    HTTP_404_NOT_FOUND,
    HTTP_503_SERVICE_UNAVAILABLE,
)
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware

from woolgatherer.db.session import open_connection_pool, close_connection_pool
from woolgatherer.errors import (
    InvalidOperationError,
    InsufficientCapacityError,
    UnauthorizedError,
)
from woolgatherer.metrics import initialize_metrics
from woolgatherer.routers import (
    account,
    dashboard,
    data,
    frontend,
    judgement,
    stories,
    suggestions,
)
from woolgatherer.utils.auth import Requires, TokenAuthBackend
from woolgatherer.utils.settings import Settings


app = FastAPI(debug=Settings.debug)
app.mount("/static", StaticFiles(directory="static"), name="static")
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(
    AuthenticationMiddleware,
    backend=TokenAuthBackend(Settings.access_token),  # type: ignore
)
app.add_middleware(SessionMiddleware, secret_key=Settings.session_token)
app.add_middleware(ProxyHeadersMiddleware, trusted_hosts=Settings.trusted_hosts)

app.include_router(frontend.router, prefix="", tags=["frontend"])
app.include_router(account.router, prefix="/account", tags=["account"])
app.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
app.include_router(
    data.router,
    prefix="/data",
    tags=["data"],
    dependencies=[
        Depends(
            Requires("dataset", status_code=HTTP_401_UNAUTHORIZED, redirect="login")
        )
    ],
)
app.include_router(
    judgement.router,
    prefix="/judgement",
    tags=["judgement"],
    dependencies=[
        Depends(
            Requires("judgement", status_code=HTTP_401_UNAUTHORIZED, redirect="login")
        )
    ],
)
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
app.add_event_handler("startup", frontend.initialize)


@app.on_event("startup")
def initialize_caches():
    """ Initialize the cache """
    url = urllib.parse.urlparse(Settings.cache_url)
    cache_config: Dict[str, Any] = dict(urllib.parse.parse_qsl(url.query))
    cache_class = aiocache.Cache.get_scheme_class(url.scheme)

    if url.path:
        cache_config.update(cache_class.parse_uri_path(url.path))

    if url.hostname:
        cache_config["endpoint"] = url.hostname

    if url.port:
        cache_config["port"] = str(url.port)

    if url.password:
        cache_config["password"] = url.password

    if cache_class == aiocache.Cache.REDIS:
        cache_config["cache"] = "aiocache.RedisCache"
        cache_config["serializer"] = {"class": "aiocache.serializers.PickleSerializer"}
    elif cache_class == aiocache.Cache.MEMORY:
        cache_config["cache"] = "aiocache.SimpleMemoryCache"
        cache_config["serializer"] = {"class": "aiocache.serializers.NullSerializer"}

    aiocache.caches.set_config({"default": cache_config})


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


@app.exception_handler(StarletteHTTPException)
async def override_http_exception_handler(request: Request, exception: HTTPException):
    """ A handler for validation errors """
    if isinstance(exception, UnauthorizedError):
        return exception.redirect

    return await http_exception_handler(request, exception)
