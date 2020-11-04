"""
Logging utils
"""
import logging
from typing import cast

from woolgatherer.utils.settings import Settings


TRACE_LOG_LEVEL = logging._nameToLevel["TRACE"]  # pylint:disable=protected-access


class Logger(logging.Logger):
    """ Subclass to provide a trace function. Needed to to make mypy happy. """

    def trace(self, message: str, *args, **kwargs):
        """ Trace logging """
        return self.log(TRACE_LOG_LEVEL, message, *args, **kwargs)


def get_logger():
    """ Get the logger """
    # Temporarily set the logging class to our class, then reset it after setting
    # up our logger.
    _logging_cls = logging.getLoggerClass()
    logging.setLoggerClass(Logger)
    logger = cast(Logger, logging.getLogger("woolgatherer"))
    logging.setLoggerClass(_logging_cls)

    try:
        logger.setLevel(Settings.loglevel.upper())
        logging.log(TRACE_LOG_LEVEL, f"Set loglevel=%s", Settings.loglevel)
    except ValueError as exception:
        logging.fatal(str(exception))

    return logger
