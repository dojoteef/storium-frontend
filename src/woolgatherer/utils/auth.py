"""
Authentication utils
"""
import time
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union

from authlib.common.urls import extract_params, add_params_to_qs
from authlib.integrations.base_client import OAuthError
from authlib.integrations.starlette_client import OAuth
from fastapi import HTTPException
from starlette.config import Config
from starlette.requests import HTTPConnection, Request
from starlette.responses import RedirectResponse
from starlette.authentication import (
    has_required_scope,
    AuthenticationBackend,
    BaseUser,
    SimpleUser,
    AuthCredentials,
)
from starlette.status import HTTP_303_SEE_OTHER, HTTP_403_FORBIDDEN

from woolgatherer.errors import UnauthorizedError
from woolgatherer.utils.settings import Settings
from woolgatherer.utils.logging import get_logger


logger = get_logger()


OAUTH_CLIENT_ARGS: Dict[str, Any] = {"scope": "openid email profile roles"}
if Settings.debug:
    from authlib.integrations.httpx_client.utils import (  # pylint:disable=ungrouped-imports
        HTTPX_CLIENT_KWARGS,
    )

    HTTPX_CLIENT_KWARGS.append("event_hooks")

    async def log_auth_request(request):
        """ Log an auth request """
        logger.trace(
            "request: method=%s, url=%s, headers=%s, content=%s",
            request.method,
            request.url.raw,
            request.headers.raw,
            b"".join(iter(request.stream)),
        )

    async def log_auth_response(response):
        """ Log an auth response """
        logger.trace(
            "response: url=%s, headers=%s, content=%s",
            response.url.raw,
            response.headers.raw,
            response.content,
        )

    OAUTH_CLIENT_ARGS["event_hooks"] = {
        "request": [log_auth_request],
        "response": [log_auth_response],
    }


oauth = OAuth(
    Config(
        environ={
            "STORIUM_CLIENT_ID": Settings.oauth_client_id,
            "STORIUM_CLIENT_SECRET": Settings.oauth_client_secret,
        }
    )
)


oauth.register(
    name="storium",
    server_metadata_url=Settings.oauth_url,
    client_kwargs=OAUTH_CLIENT_ARGS,
)


def keycloak_revoke_token_fix(url, headers, body):
    """ Fix keycloak compliance issues """
    params = extract_params(body)
    # the function prepare_revoke_token_request in authlib places the token as
    # the first param, so just pop it and rename it. keycloak does not conform
    # to rfc7009 and instead names the parameter "refresh_token", so we need to
    # change that here
    params.insert(0, ("refresh_token", params.pop(0)[1]))
    return url, headers, add_params_to_qs("", params)


async def keycloak_revoke_token(refresh_token):
    """ Wrapper function to implement the revoke token for keycloak """
    metadata = await oauth.storium.load_server_metadata()
    async with oauth.storium._get_oauth_client(  # pylint:disable=protected-access
        **metadata
    ) as client:
        client.register_compliance_hook(
            "revoke_token_request", keycloak_revoke_token_fix
        )
        await client.revoke_token(
            metadata["end_session_endpoint"],
            token=refresh_token,
            token_type_hint="refresh_token",
        )


# Register the revoke token method
oauth.storium.revoke_token = keycloak_revoke_token


async def validate_refresh_token(conn: HTTPConnection):
    """ Validate the refresh token """
    user = conn.session.get("user", {})
    if user.get("exp", 0) < time.time():
        # User is expired, remove their session
        if user:
            del conn.session["user"]

        # The token is expired, try to refresh
        refresh_token = conn.session.get("refresh_token")
        if refresh_token:
            metadata = await oauth.storium.load_server_metadata()
            async with oauth.storium._get_oauth_client(  # pylint:disable=protected-access
                **metadata
            ) as client:
                try:
                    token = await client.refresh_token(
                        metadata["token_endpoint"], refresh_token
                    )
                    conn.session["refresh_token"] = token.get("refresh_token")

                    # Refresh was successful, set user session
                    user = await oauth.storium.parse_id_token(conn, token)
                    conn.session["user"] = dict(user)
                except OAuthError as exc:
                    # The refresh token has likely expired
                    logger.error(exc)


def parse_scopes(conn: HTTPConnection):
    """ Parse the scopes the user has access to """
    # See if there is a logged in user and what roles they have
    user = conn.session.get("user")
    if user:
        resources = user.get("resource_access", {})
        resource = resources.get(user.get("azp", ""), {})
        return resource.get("roles", [])

    return []


class Requires:
    """ Similar to starlette.authentication.requires """

    def __init__(
        self,
        scopes: Union[str, Sequence[str]],
        status_code: int = HTTP_403_FORBIDDEN,
        redirect: Optional[str] = None,
    ):
        self.redirect = redirect
        self.status_code = status_code
        self.scopes = [scopes] if isinstance(scopes, str) else list(scopes)

    def __call__(self, request: Request):
        if not has_required_scope(request, self.scopes):
            if self.redirect is not None:
                # Ask the top-level router for the app what the url is for the
                # redirect. That's because FastAPI doesn't maintain a router
                # hierarchy like Starlette does
                redirect = request.app.router.url_path_for(self.redirect)
                raise UnauthorizedError(
                    RedirectResponse(url=redirect, status_code=HTTP_303_SEE_OTHER)
                )

            raise HTTPException(self.status_code)


class TokenAuthBackend(AuthenticationBackend):
    """ Backend that uses a shared token for authentication """

    def __init__(self, token: Optional[str]):
        self.token = token

    async def authenticate(
        self, conn: HTTPConnection
    ) -> Optional[Tuple[AuthCredentials, BaseUser]]:
        """ Perform authentication using a shared token """
        roles: List[str] = []
        username = "<unknown>"

        # See if there is a logged in user and what roles they have
        await validate_refresh_token(conn)
        user = conn.session.get("user", {})
        username = user.get("username", username)
        roles.extend(parse_scopes(conn))

        # See if the correct token has been passed as a query param
        if conn.query_params.get("token") == self.token:
            roles.append("backend")

        return AuthCredentials(roles), SimpleUser(username)
