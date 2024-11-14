# Die Hard

## Attribution

This test task was cloned from [kobzevvv](https://github.com/kobzevvv/backender-challenge/tree/main). The project is based on his design and requirements to demonstrate backend development skills using the following tech stack:
- Python 3.13
- Django 5
- pytest
- Docker & docker-compose
- PostgreSQL
- ClickHouse

All implementations and additions in this repository are contributed by [Nuray Serkali](https://github.com/nuray0) for the purpose of completing the assigned task. 

You can find the documentation about the implemention and a diagram by clicking this link: 
* [Documentation in English](docs/implementation_details.md)


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
