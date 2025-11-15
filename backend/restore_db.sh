#!/bin/bash
# Database restore script that runs in the postgres container
# This avoids connection conflicts with the backend

set -e  # Exit on any error

BACKUP_FILE=$1

if [ -z "$BACKUP_FILE" ]; then
    echo "Error: Backup file path required"
    exit 1
fi

if [ ! -f "$BACKUP_FILE" ]; then
    echo "Error: Backup file not found: $BACKUP_FILE"
    exit 1
fi

echo "Starting database restore from: $BACKUP_FILE"

# Run all commands in the postgres container to avoid backend connection issues
docker exec roanes-kitchen-postgres bash -c "
    export PGPASSWORD=admin

    echo 'Step 1: Terminating all connections...'
    psql -U admin -d postgres -c \"
        SELECT pg_terminate_backend(pg_stat_activity.pid)
        FROM pg_stat_activity
        WHERE pg_stat_activity.datname = 'roanes_kitchen'
        AND pid <> pg_backend_pid();
    \" 2>/dev/null || true

    echo 'Step 2: Dropping database...'
    psql -U admin -d postgres -c 'DROP DATABASE IF EXISTS roanes_kitchen;'

    echo 'Step 3: Creating database...'
    psql -U admin -d postgres -c 'CREATE DATABASE roanes_kitchen;'
"

# Copy backup file into postgres container
echo "Step 4: Copying backup file to postgres container..."
docker cp "$BACKUP_FILE" roanes-kitchen-postgres:/tmp/restore.sql

# Restore from backup
echo "Step 5: Restoring from backup..."
docker exec roanes-kitchen-postgres bash -c "
    export PGPASSWORD=admin
    psql -U admin -d roanes_kitchen -f /tmp/restore.sql
    rm -f /tmp/restore.sql
"

echo "Database restore completed successfully!"
exit 0
