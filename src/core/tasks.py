from celery import shared_task
from django.db import transaction
from src.core.models import EventLogOutbox
from src.core.event_log_client import EventLogClient
import structlog
import json

logger = structlog.get_logger(__name__)


@shared_task
def send_event_logs():
    """
    Задача Celery для отправки событий из Outbox в ClickHouse.

    Описание:
        - Вызывает сервис EventLogService для обработки непрочитанных логов.
    """
    logger.info('Starting to send event logs')

    with transaction.atomic():
        logs = list(EventLogOutbox.objects.filter(processed=False)[:1000])

        if not logs:
            logger.info('No logs to send')
            return

        data = []
        for log in logs:
            data.append({
                'event_type': log.event_type,
                'event_date_time': log.event_date_time,
                'environment': log.environment,
                'event_context': json.dumps(log.event_context),
                'metadata_version': log.metadata_version,
            })

        try:
            with EventLogClient.init() as client:
                client.insert(data=data)
        except Exception as e:
            logger.error('Failed to send logs to ClickHouse', error=str(e))
            return

        EventLogOutbox.objects.filter(id__in=[log.id for log in logs]).update(processed=True)
        logger.info('Event logs sent and marked as processed')
