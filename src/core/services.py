from core.models import EventLogOutbox
from core.event_log_client import EventLogClient
from django.conf import settings
from django.db import transaction
import structlog

from core.models import EventLog

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
            logger.info(f"Found {len(logs)} unprocessed logs")

            if not logs:
                logger.info('No logs to send')
                return

            data = []
            for log in logs:
                event = EventLog(
                    event_type=log.event_type,
                    event_date_time=log.event_date_time,
                    environment=log.environment,
                    event_context=log.event_context,
                    metadata_version=log.metadata_version
                )
                data.append(event)

            logger.info(f"Prepared data for ClickHouse insertion: {data}")

            try:
                with EventLogClient.init() as client:
                    logger.info(f"Initialized EventLogClient with settings: host={settings.CLICKHOUSE_HOST}, port={settings.CLICKHOUSE_PORT}")
                    client.insert(data=data)
                    logger.info("Data successfully inserted into ClickHouse")
            except Exception as e:
                logger.error('Failed to send logs to ClickHouse', error=str(e), exc_info=True)
                return

            EventLogOutbox.objects.filter(id__in=[log.id for log in logs]).update(processed=True)
            logger.info('Event logs sent and marked as processed')
