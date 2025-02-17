
### Solution Implementation

1. A table called `EventOutbox` was created in PostgreSQL to store event logs. Events are first logged into this table. For this, an `EventOutboxLogger` was implemented in [event_outbox_logger.py](..%2Fsrc%2Fcore%2Fevent_outbox_logger.py).
2. A periodic Celery task was added in [tasks.py](..%2Fsrc%2Fusers%2Ftasks.py), which batches 1000 records (`settings.CLICKHOUSE_BATCH_SIZE`) at a time and transfers events from the `EventOutbox` table to ClickHouse every 10 minutes (`settings.CLICKHOUSE_UPDATE_INTERVAL`).
   To achieve this, services were added in the compose file: `celery_worker` and `celery_beat`, and the Celery configuration can be found in [celery.py](..%2Fsrc%2Fcore%2Fcelery.py).

#### In the current implementation:
1. The record insertion into ClickHouse is asynchronous.
2. The transaction was used for overwriting records, and errors are allowed to be raised by `EventLogClient` while maintaining logging functionality. No additional logging was added within the overwrite task (just `except: pass`), as logging in `EventLogClient` is sufficient.
3. The problem with writing one record at a time to ClickHouse was resolved, making the process more efficient.
4. Honestly, tests were not modified.

#### In addition:
  - Replaced the custom method for converting to camel case with `underscore` from the `inflection` library.
  - In `conftest`, changed the hardcoded host to `settings.CLICKHOUSE_HOST`.
  - Replaced the `CELERY_BROKER` in [.env.ci](..%2Fsrc%2Fcore%2F.env.ci) with `redis://redis:6379/0`.
