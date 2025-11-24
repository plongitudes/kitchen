#!/bin/bash
set -e

echo "Waiting for postgres..."
while ! nc -z postgres 5432; do
  sleep 0.1
done
echo "PostgreSQL started"

echo "Running database migrations..."
alembic upgrade head

# Seed development data (only runs in development mode)
if [ "$ENVIRONMENT" = "development" ]; then
  echo "Seeding development data..."
  python scripts/seed_dev_data.py
fi

echo "Starting application..."
# Use --reload for development, multiple workers for production
if [ "$ENVIRONMENT" = "development" ]; then
  exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
else
  exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 2
fi
