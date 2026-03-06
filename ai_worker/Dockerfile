FROM python:3.13-slim

WORKDIR /srv

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

COPY pyproject.toml ./
RUN uv sync --frozen --no-dev --no-install-project

COPY . .

CMD ["uv", "run", "arq", "worker.main.WorkerSettings"]
