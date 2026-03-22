FROM python:3.13-slim

WORKDIR /srv

ENV PYTHONPATH=/srv/app

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Copy workspace root files + this package's pyproject for dependency caching
COPY pyproject.toml uv.lock ./
COPY app/pyproject.toml app/pyproject.toml

RUN uv sync --frozen --no-dev --no-install-project --package sullivan-backend

COPY app/ app/

RUN uv sync --frozen --no-dev --package sullivan-backend

EXPOSE 8000

COPY app/entrypoint.sh app/entrypoint.sh
RUN chmod +x app/entrypoint.sh

CMD ["app/entrypoint.sh"]
