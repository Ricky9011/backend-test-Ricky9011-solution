import structlog
from logs.models import OutboxLog
from core.event_log_client import EventLogClient
from sentry_sdk import start_transaction, capture_exception

logger = structlog.get_logger(__name__)

def process_logs(batch_size=100) -> int:
    with start_transaction(op="log_processing", name="process_logs") as transaction:
        logs = OutboxLog.objects.filter(processed=False).order_by("event_date_time")[:batch_size]
        if not logs.exists():
            logger.info("No logs to process", transaction_id=transaction.trace_id)
            return 0

        logger.info("Processing logs", transaction_id=transaction.trace_id, log_count=len(logs))
        data_to_insert = [
            {
                "event_type": log.event_type,
                "event_date_time": log.event_date_time,
                "environment": log.environment,
                "event_context": log.event_context,
                "metadata_version": log.metadata_version,
            }
            for log in logs
        ]

        with EventLogClient.init() as client:
            try:
                client.insert(data=data_to_insert)
                logs.update(processed=True)
                logger.info(
                    "Successfully processed logs",
                    transaction_id=transaction.trace_id,
                    processed_count=len(data_to_insert),
                )
                return len(data_to_insert)
            except Exception as e:
                capture_exception(e)
                logger.error("Error processing logs", transaction_id=transaction.trace_id, error=str(e))
                raise
