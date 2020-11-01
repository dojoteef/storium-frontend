"""
This router handles the website frontend
"""
from fastapi import APIRouter
from starlette.config import Config
from starlette.requests import Request
from starlette.responses import RedirectResponse
from authlib.integrations.starlette_client import OAuth

from woolgatherer.utils.settings import Settings


oauth = OAuth(
    Config(
        environ={
            "STORIUM_CLIENT_ID": Settings.oauth_client_id,
            "STORIUM_CLIENT_SECRET": Settings.oauth_client_secret,
        }
    )
)
router = APIRouter()

oauth.register(
    name="storium",
    server_metadata_url=Settings.oauth_url,
    client_kwargs={"scope": "openid"},
)


@router.get("/login", summary="Login to the dashboard")
async def login(request: Request):
    """
    This method initiates a login
    """
    redirect = request.url_for("auth")
    return await oauth.storium.authorize_redirect(request, redirect)


@router.get("/auth", summary="Authenticate with the oauth provider")
async def auth(request: Request):
    """
    This method performs authentication with the OAuth provider
    """
    token = await oauth.storium.authorize_access_token(request)
    user = await oauth.storium.parse_id_token(request, token)
    request.session["user"] = dict(user)
    return RedirectResponse(url="/")


@router.get("/logout", summary="Logout of the dashboard")
async def logout(request: Request):
    """
    This method logs a user out
    """
    request.session.pop("user", None)
    return RedirectResponse(url="/")
