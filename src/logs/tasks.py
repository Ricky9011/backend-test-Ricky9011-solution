from src.core.celery import app
from src.logs.outbox import OutboxExporter


@app.task(queue="outbox")
def export_outbox() -> None:
    OutboxExporter.export()


@app.task(queue="outbox")
def cleanup_outbox() -> None:
    OutboxExporter.cleanup()
