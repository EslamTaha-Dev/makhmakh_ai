# syntax=docker/dockerfile:1.7

FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_INPUT=1

COPY requirements.txt requirements-security.txt ./
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --prefer-binary \
    -r requirements.txt \
    -r requirements-security.txt

COPY app ./app
COPY alembic.ini .
COPY alembic ./alembic
COPY arq_worker.py .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
