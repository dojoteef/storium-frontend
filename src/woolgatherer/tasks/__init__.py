"""
Initialize the celery task queue
"""
from celery import Celery
from kombu import serialization

from woolgatherer.utils.settings import Settings

app = Celery("woolgatherer", broker=Settings.broker_url)
