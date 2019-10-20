"""
Story preprocessing tasks
"""
from typing import Any, Dict
from celery.utils.log import get_task_logger

from woolgatherer.tasks import app


logger = get_task_logger(__name__)


@app.task
def process(story_id: str, story: Dict[str, Any]):
    """ Preprocess a story """
    logger.info("Processed story=%s, game_pid=%s", story_id, story.get("game_pid"))
