
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

## Installation

(run project just as it was ran before) Put a `.env` file into the `src/core` directory. You can start with a template file:

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

`make test` (same as before)

## Linter

`make lint` (didn't fix it, sorry)

## Solution explanation

Nothing special, just used transactional outbox pattern as it was stated in the task, for message relay used kind of polling publisher pattern (with update instead of delete because updates should be faster)

### Simple arch diagram:
![Scheme](https://i.ibb.co/zrTm0gq/scheme.png)
