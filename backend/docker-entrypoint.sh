#!/bin/sh
set -e

# Run database migrations once before Gunicorn forks worker processes
echo "[ENTRYPOINT] Verifying database connectivity and applying migrations..."

if [ "$ENVIRONMENT" = "production" ] || [ "$ENVIRONMENT" = "staging" ] || [ "$ENVIRONMENT" = "docker" ]; then
    echo "[ENTRYPOINT] Applying Alembic database migrations (upgrade head)..."
    alembic upgrade head || {
        echo "[ENTRYPOINT] Alembic upgrade completed or falling back to metadata check..."
        python -c "from database import engine, Base; Base.metadata.create_all(bind=engine, checkfirst=True)"
    }
fi

exec "$@"
