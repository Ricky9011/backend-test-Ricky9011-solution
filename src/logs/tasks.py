from src.core.celery import app
from src.logs.outbox import OutboxExporter


@app.task(queue="outbox")
def export_outbox_logs() -> None:
    OutboxExporter.export()


@app.task(queue="outbox")
def cleanup_outbox_logs() -> None:
    OutboxExporter.cleanup()
