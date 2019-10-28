"""
Encapsulate the configuration for woolgatherer
"""
from typing import Tuple, Optional

from pydantic import BaseSettings, DSN, SecretStr

from woolgatherer.db.utils import has_postgres
from woolgatherer.models.utils import Field
from woolgatherer.models.feedback import (
    FeedbackEntryType,
    FeedbackType,
    FeedbackPrompt,
    FeedbackScale,
)


class _DevSettings(BaseSettings):
    """ The basic app settings that don't require Postgres """

    db_driver: str = "sqlite"
    db_user: Optional[str] = None
    db_password: Optional[SecretStr] = None
    db_host: Optional[str] = None
    db_port: Optional[int] = None
    db_name: str = "woolgatherer.db"
    db_query: Optional[dict] = None
    dsn: DSN = Field(
        None,
        description="""The data source name, constructed from the various db fields""",
    )

    broker_url: str = "sqla+sqlite:///task_queue.db"

    required_feedback: Tuple[FeedbackPrompt, ...] = (
        FeedbackPrompt(
            choices=FeedbackScale,
            type=FeedbackType.fluency,
            entry_type=FeedbackEntryType.choice,
            title="""Please rate the fluency of the suggestion.""",
        ),
        FeedbackPrompt(
            choices=FeedbackScale,
            type=FeedbackType.relevance,
            entry_type=FeedbackEntryType.choice,
            title="""Please rate the relevance of the suggestion.""",
        ),
        FeedbackPrompt(
            choices=FeedbackScale,
            type=FeedbackType.coherence,
            entry_type=FeedbackEntryType.choice,
            title="""Please rate the coherence of the suggestion.""",
        ),
        FeedbackPrompt(
            type=FeedbackType.comments,
            entry_type=FeedbackEntryType.text,
            title="""Please provide any additional comments you have about the suggestion.""",
        ),
    )

    class Config(object):
        """ Additional configuration for the settings """

        prefix = "GW_"


class _Settings(_DevSettings):
    """ The app settings """

    db_driver: str = "postgresql"
    db_user: Optional[str] = "postgres"
    db_password: Optional[SecretStr] = None
    db_host: Optional[str] = "db"
    db_port: Optional[int] = 5432
    db_name: str = "woolgatherer"
    db_query: Optional[dict] = None

    broker_url: str = "amqp://guest@queue"


# Forward declare Settings to make mypy happy
Settings: _DevSettings
if has_postgres():
    Settings = _Settings()
else:
    Settings = _DevSettings()
