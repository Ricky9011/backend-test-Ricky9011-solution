# Transactional Outbox Implementation

Previously, the application inserted event logs directly into ClickHouse in a synchronous manner. This led to problems like lost events when workers crashed, UI disruptions due to network issues, and performance degradation from many small inserts. Such issues compromised both reliability and system performance. The Transactional Outbox pattern provides a solution by decoupling event logging from core operations and ensuring atomic transactions.

## What I Did

1. **Transactional Outbox Pattern**  
   To implement this pattern, it was necessary to create a table in PostgreSQL called `OutboxEvent`. I ensured that both the main operation (for example, adding a new user) and its related event log are saved in one atomic transaction.

2. **Batch Processing with Celery Beat**  
   I set up a Celery Beat task to process outbox events at regular intervals.

   - The interval is defined by the environment variable `CH_OUTBOX_PROCESSING_FREQUENCY_SEC` (in seconds).
   - [According to the documentation](https://clickhouse.com/blog/common-getting-started-issues-with-clickhouse#many-small-inserts), to increase the performance of the ClickHouse database, it is recommended to group events into batches of at least 1000. The batch size is configurable via the environment variable `CH_OUTBOX_BATCH_SIZE`.

3. **Infrastructure Setup**

   - Celery runs in a separate worker container in Docker Compose.
   - I used atomic transactions at critical points to ensure data consistency.

4. **Logging and Monitoring**

   - I integrated structured logging using `structlog`.
   - I implemented error tracking and tracing with Sentry.

5. **Testing and CI/CD**
   - I wrote unit tests using `pytest` (with `pytest-django` for fixtures, where needed).
   - I set up GitHub Actions to build the project, run migrations, execute tests, and perform linting checks.

## Below is an example of how the architecture of the implemented pattern is structured.

![The architecture of the implemented pattern](images/Architecture%20schema.jpg)

## The requirements for this task

You can find detailed requirements by clicking the links:

- [English version](docs/task_en.md)
- [Russian version](docs/task_ru.md)

Tech stack:

- Python 3.13
- Django 5
- Celery
- pytest
- Docker & docker-compose
- PostgreSQL
- ClickHouse
- Redis

## Installation

Put a `.env` file into the `src/core` directory. You can start with a template file:

```
cp src/core/.env.ci src/core/.env
```

Run the containers with

```
make run
```

and then run the installation script with:

```
make install
```

## Tests

`make test`

## Linter

`make lint`
