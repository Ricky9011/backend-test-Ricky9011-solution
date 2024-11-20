from src.core.celery import app
from src.logs.outbox import OutboxExporter


@app.task
def export_outbox() -> None:
    OutboxExporter.export()


@app.task
def cleanup_outbox() -> None:
    OutboxExporter.cleanup()
