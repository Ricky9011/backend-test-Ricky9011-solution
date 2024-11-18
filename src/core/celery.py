from functools import wraps
import enum
import os
from typing import Callable

from celery import Celery
from celery.signals import after_setup_logger
import structlog


custom_logger = structlog.get_logger(__name__)


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

app = Celery()
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()


@after_setup_logger.connect
def setup_logger(**kwargs):
    app.log.setup_logger = custom_logger


class CeleryQueues(enum.StrEnum):
    PERIODIC = 'periodic'


def log_task(task: Callable):
    @wraps(task)
    def wrapper(self, *args, **kwargs):
        custom_logger.info(f'Call celery task {self.name} with args {args} and kwargs {kwargs}')
        result = task(self, *args, **kwargs)
        custom_logger.info(f'Celery task result is {result}')
        return result
    return wrapper
