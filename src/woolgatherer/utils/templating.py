"""
Utilities for Jinja2 templates
"""
from typing import Any, Dict

from starlette.requests import Request
from starlette.templating import Jinja2Templates

from woolgatherer.utils.auth import parse_scopes
from woolgatherer.utils.settings import Settings

templates = Jinja2Templates(directory="templates")
templates.env.add_extension("jinja2.ext.do")
templates.env.globals["gtag_id"] = Settings.gtag_id


def TemplateResponse(
    request: Request, name: str, context: Dict[str, Any], *args, **kwargs
):
    """ Create a template response """
    context = dict(context)
    context["request"] = request
    context["scopes"] = parse_scopes(request)

    return templates.TemplateResponse(name, context, *args, **kwargs)
