"""
Authentication utils
"""
import logging
from urllib.parse import quote_plus
from typing import List, Optional, Sequence, Tuple, Union

from fastapi import HTTPException
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
        user = conn.session.get("user", {})
        username = user.get("username", username)
        roles.extend(parse_scopes(conn))

        # See if the correct token has been passed as a query param
        if conn.query_params.get("token", None) == self.token:
            roles.append("backend")

        return AuthCredentials(roles), SimpleUser(username)
