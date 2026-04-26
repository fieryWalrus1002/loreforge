FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv sync --no-dev --frozen

COPY src/ ./src/
COPY data/ ./data/

ENV PYTHONUNBUFFERED=1

CMD ["uv", "run", "python", "src/worker.py"]
