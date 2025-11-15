#!/bin/bash
# Internal restore script that runs INSIDE the postgres container
# Called with: bash restore_db_internal.sh /path/to/backup.sql

set -e

BACKUP_FILE=$1

if [ -z "$BACKUP_FILE" ]; then
    echo "Error: Backup file path required"
    exit 1
fi

if [ ! -f "$BACKUP_FILE" ]; then
    echo "Error: Backup file not found: $BACKUP_FILE"
    exit 1
fi

export PGPASSWORD=admin

echo "Step 1: Terminating all connections..."
psql -U admin -d postgres -c "
    SELECT pg_terminate_backend(pg_stat_activity.pid)
    FROM pg_stat_activity
    WHERE pg_stat_activity.datname = 'roanes_kitchen'
    AND pid <> pg_backend_pid();
" 2>/dev/null || true

echo "Step 2: Dropping database..."
psql -U admin -d postgres -c "DROP DATABASE IF EXISTS roanes_kitchen;"

echo "Step 3: Creating database..."
psql -U admin -d postgres -c "CREATE DATABASE roanes_kitchen;"

echo "Step 4: Restoring from backup..."
psql -U admin -d roanes_kitchen -f "$BACKUP_FILE"

echo "Restore completed successfully!"
