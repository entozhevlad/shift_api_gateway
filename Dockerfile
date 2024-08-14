FROM python:3.12-slim

WORKDIR /app

ENV POETRY_VERSION=1.8.3

COPY poetry.lock pyproject.toml ./

RUN apt-get update && \
    apt-get install --no-install-recommends -y && \
    apt-get install -y python3-pip && \
    pip install "poetry==$POETRY_VERSION"

RUN poetry config virtualenvs.create false && poetry install --no-interaction --no-root

COPY src /app/src

ENV PYTHONPATH=/app

EXPOSE 80

ENTRYPOINT ["uvicorn", "src.app.main:app", "--host", "0.0.0.0", "--port", "80"]
