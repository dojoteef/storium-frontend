"""
Utilities for Jinja2 templates
"""

from starlette.templating import Jinja2Templates

from woolgatherer.utils.settings import Settings

templates = Jinja2Templates(directory="templates")
templates.env.add_extension("jinja2.ext.do")
templates.env.globals["gtag_id"] = Settings.gtag_id
