FROM python:3.13-slim

WORKDIR /srv

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Copy workspace root files + both packages' pyproject for dependency caching
COPY pyproject.toml uv.lock ./
COPY app/pyproject.toml app/pyproject.toml
COPY ai_worker/pyproject.toml ai_worker/pyproject.toml

RUN uv sync --frozen --no-dev --no-install-project --package sullivan-worker

COPY app/ app/
COPY ai_worker/ ai_worker/

RUN uv sync --frozen --no-dev --package sullivan-worker

ENV PYTHONPATH=/srv/ai_worker:/srv/app

CMD ["uv", "run", "--package", "sullivan-worker", "arq", "worker.main.WorkerSettings"]
