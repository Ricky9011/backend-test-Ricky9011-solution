ARG PYTHON_IMAGE_BASE=python:3.13-slim

ARG RUNTIME_DEPS="\
  libpq-dev \
"

ARG BUILD_DEPS="\
    gcc \
    g++ \
    python3-dev \
    libffi-dev \
    libssl-dev \
    python3-dev \
"

FROM $PYTHON_IMAGE_BASE AS base

ARG RUNTIME_DEPS

RUN apt-get -qq update \
    && apt-get -qqy --no-install-recommends install $RUNTIME_DEPS \
    && apt-get -qy upgrade \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

FROM base AS builder

ARG BUILD_DEPS

RUN apt-get -qq update \
    && apt-get -qqy --no-install-recommends install $BUILD_DEPS \
    && apt-get -qy upgrade \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /srv/app/

COPY requirements.txt ./

RUN python -m venv /venv

RUN /venv/bin/pip install -U setuptools pip wheel build --no-cache-dir && \
    /venv/bin/pip install -r requirements.txt --no-cache-dir

FROM base

ENV PATH=/venv/bin:$PATH
ENV PYTHONPATH=/srv/app:/venv:$PYTHONPATH

WORKDIR /srv/app/

COPY --from=builder /venv /venv

COPY . .

RUN python manage.py collectstatic --noinput
