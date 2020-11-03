"""
This router handles the website frontend
"""
from fastapi import APIRouter
from starlette.requests import Request
from starlette.responses import RedirectResponse

from woolgatherer.utils.auth import oauth

router = APIRouter()


@router.get("/login", summary="Login to the dashboard")
async def login(request: Request):
    """
    This method initiates a login
    """
    if request.session.get("user"):
        return RedirectResponse(url="/")

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
    request.session["refresh_token"] = token.get("refresh_token")
    return RedirectResponse(url="/")


@router.get("/logout", summary="Logout of the dashboard")
async def logout(request: Request):
    """
    This method logs a user out
    """
    request.session.pop("user", None)
    refresh_token = request.session.pop("refresh_token", None)
    if refresh_token:
        await oauth.storium.revoke_token(refresh_token)

    return RedirectResponse(url="/")
