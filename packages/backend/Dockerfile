# syntax=docker/dockerfile:1

FROM docker.io/python:3.12.4-slim-bullseye

LABEL name="WallStr backend" \
      maintainer="Guro Bokum <jiojiajiu@gmail.com>" \
      org.opencontainers.image.source="https://github.com/limanprojects/wallstr" \
      org.opencontainers.image.description="Wallstr.chat" \
      org.opencontainers.image.licenses="Apache-2.0"

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_VERSION=2.1.1 \
    APP_USER=wallstr \
    APP_HOME=/app

RUN useradd --create-home $APP_USER

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        curl \
        build-essential \
        libgl1 libglib2.0-0 \
        libheif-dev qpdf poppler-utils \
    && rm -rf /var/lib/apt/lists/*

ENV PATH="/home/${APP_USER}/.local/bin:${PATH}"
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir poetry==${POETRY_VERSION}

WORKDIR $APP_HOME

COPY --chown=$APP_USER:$APP_USER poetry.lock pyproject.toml ./
RUN poetry install --no-root --no-cache && \
    poetry cache clear pypi --all && rm -r ~/.cache/pypoetry

USER $APP_USER
COPY --chown=$APP_USER:$APP_USER . .
