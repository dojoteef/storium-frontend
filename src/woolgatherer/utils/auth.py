"""
Authentication utils
"""
import base64
import binascii
from typing import Optional, Sequence, Tuple, Union

from fastapi import HTTPException
from starlette.requests import HTTPConnection, Request
from starlette.authentication import (
    has_required_scope,
    AuthenticationBackend,
    AuthenticationError,
    BaseUser,
    SimpleUser,
    AuthCredentials,
)
from starlette.status import HTTP_403_FORBIDDEN


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
            raise HTTPException(self.status_code)


class TokenAuthBackend(AuthenticationBackend):
    """ Backend that uses a shared token for authentication """

    def __init__(self, token: Optional[str]):
        self.token = token

    async def authenticate(
        self, conn: HTTPConnection
    ) -> Optional[Tuple[AuthCredentials, BaseUser]]:
        """ Perform authentication using a shared token """
        if self.token is None:
            # Not setting a token indicates we allow anyone to authenticate.
            # This is useful for dev and staging environments.
            return AuthCredentials(["backend"]), SimpleUser("admin")

        # First try to see if the token has been passed as a query param
        if conn.query_params.get("token", None) == self.token:
            return AuthCredentials(["backend"]), SimpleUser("admin")

        # Otherwise see if it's been passed via HTTP Basic Auth
        if "Authorization" not in conn.headers:
            return None

        auth = conn.headers["Authorization"]
        try:
            scheme, credentials = auth.split()
            if scheme.lower() != "basic":
                return None

            decoded = base64.b64decode(credentials).decode("ascii")
        except (ValueError, UnicodeDecodeError, binascii.Error) as exc:
            raise AuthenticationError("Cannot validate credentials") from exc

        username, _, token = decoded.partition(":")
        if token != self.token:
            return None

        return AuthCredentials(["backend"]), SimpleUser(username)
