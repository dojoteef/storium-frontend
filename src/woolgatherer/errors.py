"""
Exceptions specifc to feedback
"""
from typing import Union

from starlette.exceptions import HTTPException
from starlette.responses import RedirectResponse


class InvalidOperationError(RuntimeError):
    """ An operational error occurred """


class InsufficientCapacityError(RuntimeError):
    """ Do not have the capacity to complete a requested operation """


class ProcessingError(ValueError):
    """ There was some error in figment generation """


class UnauthorizedError(HTTPException):
    """ User tried to access a resource without proper authorization """

    def __init__(
        self, status_code_or_redirect: Union[int, RedirectResponse], detail: str = None
    ):
        redirect = None
        if isinstance(status_code_or_redirect, RedirectResponse):
            redirect = status_code_or_redirect
            status_code = redirect.status_code
        else:
            status_code = status_code_or_redirect

        super().__init__(status_code, detail=detail)
        self.redirect = redirect
