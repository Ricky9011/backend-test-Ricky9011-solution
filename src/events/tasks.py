from core.celery import app
from events.use_cases.push_events_log import PushEventsLogToClickhouse, PushEventsLogRequest


@app.task(name="events.push_log_events_to_clickhouse")
def push_events_logs_to_clickhouse(batch: int = 1000) -> None:
    PushEventsLogToClickhouse().execute(PushEventsLogRequest(batch=batch))
