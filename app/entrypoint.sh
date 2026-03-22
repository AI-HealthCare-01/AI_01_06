#!/bin/sh
set -e

cd /srv/app

# aerich upgrade 시도, stderr를 캡처하여 에러 원인 판별
AERICH_ERR=$(uv run --package sullivan-backend aerich upgrade 2>&1) && {
    echo "[entrypoint] aerich upgrade OK"
} || {
    if echo "$AERICH_ERR" | grep -q "No such table\|doesn't exist\|no such table"; then
        echo "[entrypoint] Fresh DB detected — running aerich init-db"
        uv run --package sullivan-backend aerich init-db
    else
        echo "[entrypoint] aerich upgrade failed with unexpected error:"
        echo "$AERICH_ERR"
        exit 1
    fi
}

cd /srv
exec uv run --package sullivan-backend uvicorn app.main:app --host 0.0.0.0 --port 8000
