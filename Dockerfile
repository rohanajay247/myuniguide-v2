FROM python:3.12-slim

# Docling pulls torch and opencv; these are their runtime system deps
RUN apt-get update && apt-get install -y --no-install-recommends \
        libgl1 libglib2.0-0 curl \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# Dependencies first, so code changes don't invalidate the layer
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project

COPY src/ ./src/
COPY eval/ ./eval/
COPY scripts/ ./scripts/
COPY tests/ ./tests/
RUN uv sync --frozen

ENV PYTHONUNBUFFERED=1

CMD ["uv", "run", "python", "-m", "eval.check_setup"]