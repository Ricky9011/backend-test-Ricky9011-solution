from core.celery import app, log_task
from events.publisher import EventPublisher


@app.task(bind=True)
@log_task
def publish_events(self) -> None:
    EventPublisher.publish()
