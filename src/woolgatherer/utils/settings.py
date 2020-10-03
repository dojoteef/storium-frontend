"""
Encapsulate the configuration for woolgatherer
"""
from typing import Tuple

from pydantic import BaseSettings, Field

from woolgatherer.db.utils import has_postgres
from woolgatherer.models.feedback import (
    FeedbackEntryType,
    FeedbackType,
    FeedbackPrompt,
    FeedbackScale,
)
from woolgatherer.models.suggestion import SceneEntryParameters


class _DevSettings(BaseSettings):
    """ The basic app settings that don't require Postgres """

    cache_url: str = Field("memory://", dsecription="The URL for the cache")

    broker_url: str = Field(
        "sqla+sqlite:///task_queue.db", description="The URL for the task broker"
    )
    dsn: str = Field(
        "sqlite:///woolgatherer.db", description="The URL for the DB connection"
    )

    scene_entry_parameters: SceneEntryParameters = Field(
        SceneEntryParameters(), description=SceneEntryParameters.__doc__
    )

    required_feedback: Tuple[FeedbackPrompt, ...] = ()
    optional_feedback: Tuple[FeedbackPrompt, ...] = (
        FeedbackPrompt(
            choices=FeedbackScale,
            type=FeedbackType.fluency,
            entry_type=FeedbackEntryType.choice,
            title="How grammatically correct is the suggested text? "
            "(on a scale of 1-5, with 1 being the lowest)",
        ),
        FeedbackPrompt(
            choices=FeedbackScale,
            type=FeedbackType.relevance,
            entry_type=FeedbackEntryType.choice,
            title="How relevant is the suggested text to the current story so far? "
            "(on a scale of 1-5, with 1 being the lowest)",
        ),
        FeedbackPrompt(
            choices=FeedbackScale,
            type=FeedbackType.coherence,
            entry_type=FeedbackEntryType.choice,
            title="How well do the sentences in the suggested text fit together? "
            "(on a scale of 1-5, with 1 being the lowest)",
        ),
        FeedbackPrompt(
            choices=FeedbackScale,
            type=FeedbackType.likeability,
            entry_type=FeedbackEntryType.choice,
            title="How enjoyable do you find the suggested text? "
            "(on a scale of 1-5, with 1 being the lowest)",
        ),
        FeedbackPrompt(
            type=FeedbackType.comments,
            entry_type=FeedbackEntryType.text,
            title="Please provide any additional comments you have about "
            "the suggested text.",
        ),
    )

    @property
    def user_feedback(self):
        """
        Return both required and optional feedback
        """
        return self.required_feedback + self.optional_feedback

    class Config:
        """ Additional configuration for the settings """

        env_prefix = "GW_"


class _Settings(_DevSettings):
    """ The app settings """

    broker_url: str = Field(
        "amqp://guest@queue", description="The URL for the task broker"
    )
    dsn: str = Field(
        "postgresql://postgres@db:5432/woolgatherer",
        description="The URL for the DB connection",
    )


# Forward declare Settings to make mypy happy
Settings: _DevSettings
if has_postgres():
    Settings = _Settings()
else:
    Settings = _DevSettings()
