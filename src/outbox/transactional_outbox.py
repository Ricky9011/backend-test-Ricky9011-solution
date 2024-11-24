from typing import Callable

from django.db import transaction
import structlog

from outbox.models import EventLogOutbox

logger = structlog.get_logger(__name__)


class TransactionalOutbox:
    @staticmethod
    def execute_with_event(
        event_type: str,
        event_payload: dict,
        func: Callable,
        *func_args,
        **func_kwargs,
    ):
        """
        Execute function with event logging

        :param func: function to execute
        :param event_type: type of event
        :param event_payload: payload of event
        :return: result of function
        """
        with transaction.atomic():
            result = func(*func_args, **func_kwargs)
            TransactionalOutbox._log_event(event_type, event_payload)
            return result

    @staticmethod
    def _log_event(event_type: str, payload: dict) -> None:
        """
         Write event to outbox

        :param event_type: Тип события
        :param payload: Данные события
        """
        logger.info("Logging event to outbox", event_type=event_type, payload=payload)
        EventLogOutbox.objects.create(event_type=event_type, payload=payload)
