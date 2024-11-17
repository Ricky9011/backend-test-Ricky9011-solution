import structlog
from core.celery_app import app
from core.event_log_client import EventLogClient


logger = structlog.get_logger(__name__)


@app.task
def log_batch_events():
    with EventLogClient.init() as client:
        if client.need_to_consume_events():
            logger.info('Sending batch of event logs to clickhouse')
            client.consume_events()


@app.task
def log_failed_events():
    with EventLogClient.init() as client:
        logger.info('Sending failed event logs to clickhouse')
        client.consume_events(send_failed=True)
