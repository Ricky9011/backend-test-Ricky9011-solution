
## What I did to implement the task (Before the 1'st review)

### 1. models.py (EventOutbox model)
In the core module, I added the EventOutbox model to serve as an intermediary storage for event logs. Each event log entry includes the following:

* event_type: The type of event (e.g., user creation).
* event_context: JSON payload storing details of the event.
* event_date_time: Timestamp of the event.
* environment: Environment (e.g., 'Local').
* metadata_version: Version of the event structure.

### 2. tasks.py (Celery Task for Event Processing)
In core/tasks.py, I implemented the process_event_outbox function:

* Retrieves unprocessed events from EventOutbox.
* Attempts to insert them in batches into ClickHouse.
* Handles network or processing errors gracefully, logging errors to Sentry.
* Deletes events from EventOutbox only if successfully processed.

### 3. src/users/use_cases/create_user_tests.py (Test Cases)
In src/users/use_cases/create_user_tests.py, I edited test_event_log_entry_published and added 2 test cases to validate:

* test_event_log_entry_published: Edited to ensure that a user_created event is added to the EventOutbox table.
* test_process_event_outbox_success: Validates that events are successfully inserted into ClickHouse and removed from EventOutbox.
* test_process_event_outbox_network_error: Tests error handling by simulating a network error during ClickHouse insertion.

### 4. docker-compose.yml and settings.py
Updated docker-compose.yml and settings.py to include ClickHouse, PostgreSQL, and Celery service configurations.


## Corrections after 1'st review

* Deleted "- pip install redis" from Dockerfile
* Replaced hard-coded redis urls with environmental values
* Divided tasks.py into smaller functions
* Added a new file outbox_clickhouse_tests.py for testing Outbox to Clickhouse data inserting
* Removed Clickhouse mock in test_process_event_outbox_success
* Added structlog usage in new files


### Here's a simple diagram that describes the transactional outbox pattern in this solution

![System Architecture Diagram](../images/backend-challenge-diagram.png)

