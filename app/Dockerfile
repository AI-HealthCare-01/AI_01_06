FROM python:3.13-slim

WORKDIR /srv

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Copy workspace root files + this package's pyproject for dependency caching
COPY pyproject.toml uv.lock ./
COPY app/pyproject.toml app/pyproject.toml

RUN uv sync --frozen --no-dev --no-install-project --package sullivan-backend

COPY app/ app/

RUN uv sync --frozen --no-dev --package sullivan-backend

EXPOSE 8000

CMD ["uv", "run", "--package", "sullivan-backend", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
