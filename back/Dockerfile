# syntax=docker/dockerfile:1.7

FROM python:3.12-slim AS common

COPY --from=ghcr.io/astral-sh/uv:0.12.15 /uv /uvx /bin/

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=0 \
    UV_TORCH_BACKEND=cpu \
    UV_HTTP_TIMEOUT=300 \
    UV_HTTP_RETRIES=10

COPY requirements.txt ./
RUN --mount=type=cache,id=makhmakh-uv,target=/root/.cache/uv \
    uv pip install --system -r requirements.txt


FROM common AS api

COPY app ./app
COPY alembic.ini .
COPY alembic ./alembic

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]


FROM common AS material-worker

COPY requirements-material.txt ./
RUN --mount=type=cache,id=makhmakh-uv,target=/root/.cache/uv \
    uv pip install --system -r requirements-material.txt

COPY app ./app
COPY alembic.ini .
COPY alembic ./alembic

CMD ["rq", "worker", "material_processing", "--url", "redis://redis:6379/0"]


FROM common AS video-worker

RUN apt-get update \
    && apt-get install --yes --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*

COPY requirements-video.txt ./
RUN --mount=type=cache,id=makhmakh-uv,target=/root/.cache/uv \
    uv pip install --system -r requirements-video.txt

COPY app ./app
COPY alembic.ini .
COPY alembic ./alembic

CMD ["rq", "worker", "video_generation", "--url", "redis://redis:6379/0"]


FROM api AS default
