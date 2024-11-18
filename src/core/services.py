from src.core.models import EventLogOutbox
from src.core.event_log_client import EventLogClient
from django.db import transaction
import structlog
import json

logger = structlog.get_logger(__name__)


class EventLogService:
    """
    Сервис для обработки и отправки логов в ClickHouse.

    Методы:
        - send_unprocessed_logs: Отправляет непрочитанные логи из Outbox в ClickHouse.
    """

    def send_unprocessed_logs(self, batch_size=1000):
        """
        Отправляет непрочитанные события из Outbox в ClickHouse пакетами.

        Аргументы:
            - batch_size: Максимальный размер пакета для отправки.

        Логика:
            - Загружает события из таблицы Outbox с processed=False.
            - Формирует данные и отправляет их в ClickHouse.
            - Помечает отправленные события как processed=True.
        """
        logger.info('Fetching unprocessed logs')

        with transaction.atomic():
            logs = list(EventLogOutbox.objects.filter(processed=False)[:batch_size])

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
