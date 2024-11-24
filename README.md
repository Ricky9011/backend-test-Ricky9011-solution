# Changes to the Project https://github.com/kobzevvv/backender-challenge.git

## Overview

The following changes were made to implement a transactional outbox pattern for event logging, processing events using Celery, and storing them in ClickHouse. These changes address the following issues:
- Event loss if a worker crashes before writing events to ClickHouse.
- Network errors causing UI degradation.
- High load on ClickHouse due to multiple small inserts.

## Changes Made

### 1. **Outbox pattern and celery**
Created a new app, outbox_pattern, to handle Celery tasks and decouple the core log-processing logic from Celery tasks, improving reusability and maintainability.

For celery work created celery.py in core app  
```python
import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")

app = Celery("core")

app.config_from_object("django.conf:settings", namespace="CELERY")

app.autodiscover_tasks()

@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
```
and in __init__.py of core app added:
```python
from .celery import app as celery_app

__all__ = ('celery_app',)
```
and settings.py(These settings configure Celery to use Redis as the broker and result backend): 
```commandline
CELERY_BROKER_URL = env("CELERY_BROKER_URL", default="redis://redis:6379/0")
CELERY_RESULT_BACKEND = env("CELERY_RESULT_BACKEND", default="redis://redis:6379/0")

```
and docker_compose.yml:
```commandline
celery:
  build: .
  restart: always
  depends_on:
    - redis
    - db
  command: ["celery", "-A", "core", "worker", "--loglevel=info"]
  volumes:
    - .:/srv/app
  networks:
    - default

celery-beat:
  build: .
  restart: always
  depends_on:
    - redis
    - db
  command: ["celery", "-A", "core", "beat", "--loglevel=info"]
  volumes:
    - .:/srv/app
  networks:
    - default

```
A new model `EventOutbox` was created to store events before they are processed and sent to ClickHouse. This ensures that events are reliably stored in a database first, and later processed asynchronously.

```python
class EventOutbox(models.Model):
    event_type = models.CharField(max_length=255)
    event_date_time = models.DateTimeField(auto_now_add=True)
    environment = models.CharField(max_length=100)
    event_context = models.JSONField()
    metadata_version = models.PositiveIntegerField(default=1)
    processed = models.BooleanField(default=False)
    processed_at = models.DateTimeField(null=True, blank=True)
```
- event_type: Type of the event.
- event_date_time: Timestamp of the event.
- environment: Environment where the event occurred.
- event_context: Context or payload of the event in JSON format.
- metadata_version: Version of the event metadata.
- processed: Boolean flag indicating whether the event has been processed.
- processed_at: Timestamp of when the event was processed.

## 2. **Event Logging**

in CreateUser.
Use case, the event logging was modified to store the event in EventOutbox instead of directly sending it to ClickHouse. This ensures the event is safely stored before it is processed.
```python
def _log(self, user: User) -> None:
    # Log the event in EventOutbox
    EventOutbox.objects.create(
        event_type="user has been created",
        environment=settings.ENVIRONMENT,
        event_context={"email": user.email, "first_name": user.first_name, "last_name": user.last_name},
        metadata_version=1,
    )
```

In event_log_event.
Now we have data in dict type thats why we should fix function for converting data for CH:
```
python
def _convert_data(self, data: list[dict]) -> list[tuple[Any]]:
  return [
    (
      event['event_type'],
      event['event_date_time'],
      event['environment'],
      json.dumps(event['event_context']),
      event['metadata_version'],
    )
    for event in data
  ]
```
and change type of data argument in insert() function.
Additionaly adding metadata_version to EVENT_LOG_COLUMNS:
```python
EVENT_LOG_COLUMNS = [
    'event_type',
    'event_date_time',
    'environment',
    'event_context',
    'metadata_version',
]
```

## 3. ***Tests and Lints***

Have fixed existing  test_event_log_entry_published to ensure that data properly goes to CH after using process_outbox_events from outbox_pattern app:
```python
def test_event_log_entry_published(
    f_use_case: CreateUser,
    f_ch_client: Client,
) -> None:
    email = f"test_{uuid.uuid4()}@email.com"
    request = CreateUserRequest(
        email=email, first_name='Test', last_name='Testovich',
    )

    f_use_case.execute(request)

    # Trigger the process to handle events from EventBox and insert them into ClickHouse
    process_outbox_events()

    # Query ClickHouse to retrieve events with the 'user has been created' event type
    log = f_ch_client.query(
        "SELECT * FROM default.event_log WHERE event_type = 'user has been created'",
    )

    # Assert that exactly one event was found in ClickHouse
    assert len(log.result_rows) == 1

    selected_row = log.result_rows[0]
    selected_row_context = json.loads(selected_row[3])

    right_event_context = {
        "email": email,
        "first_name": "Test",
        "last_name": "Testovich",
    }

    # Verify that the context of the log matches the expected event data
    assert selected_row_context == right_event_context
```

and created test_event_created_outbox to check if data written to outbox table:
```python
def test_event_created_outbox(f_use_case: CreateUser) -> None:
    email = "test@example.com"
    request = CreateUserRequest(email=email, first_name="Test", last_name="Testovich")
    f_use_case.execute(request)
    
    event = EventOutbox.objects.get(event_context__email=email)
    assert event.event_type == "user has been created"

```

test: all tests and lints passed successfully 🎉

- Verified code correctness with all tests passing.
- Ensured code quality with linting checks.
