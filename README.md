# Die Hard

This is a project with a test task for backend developers.

You can find detailed requirements by clicking the links:
- [English version](docs/task_en.md)
- [Russian version](docs/task_ru.md)

Tech stack:
- Python 3.13
- Django 5
- pytest
- Docker & docker-compose
- PostgreSQL
- ClickHouse
- Celery

This project implements the Transactional Outbox Pattern to ensure reliable event logging. When a user is created, an event is stored in the outbox table in PostgreSQL. A periodic Celery task processes these events and writes logs to ClickHouse.

```mermaid
graph TD
    A[User Creation] --> B[Store Event in Outbox (PostgreSQL)]
    B --> C[Celery Beat Schedules Task]
    C --> D[Celery Worker Processes Outbox]
    D --> E[Write Logs to ClickHouse]
```

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
