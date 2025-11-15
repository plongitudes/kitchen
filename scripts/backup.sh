#!/bin/sh
#
# PostgreSQL Backup Script for Roanes Kitchen
# Runs daily at 2:00 AM via cron
# Retains backups for 30 days (configurable via BACKUP_RETENTION_DAYS)
#

set -e

# Configuration
BACKUP_DIR="/backups"
RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-30}"
POSTGRES_HOST="${POSTGRES_HOST:-postgres}"
POSTGRES_USER="${POSTGRES_USER:-admin}"
POSTGRES_DB="${POSTGRES_DB:-roanes_kitchen}"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="${BACKUP_DIR}/roanes_kitchen_${TIMESTAMP}.sql.gz"

echo "=== Roanes Kitchen Database Backup ==="
echo "Started at: $(date)"
echo "Backup file: ${BACKUP_FILE}"

# Create backup directory if it doesn't exist
mkdir -p "${BACKUP_DIR}"

# Perform the backup with compression
echo "Creating backup..."
PGPASSWORD="${POSTGRES_PASSWORD}" pg_dump \
    -h "${POSTGRES_HOST}" \
    -U "${POSTGRES_USER}" \
    -d "${POSTGRES_DB}" \
    --verbose \
    --format=plain \
    | gzip > "${BACKUP_FILE}"

# Check if backup was successful
if [ -f "${BACKUP_FILE}" ]; then
    BACKUP_SIZE=$(du -h "${BACKUP_FILE}" | cut -f1)
    echo "✓ Backup completed successfully (${BACKUP_SIZE})"
else
    echo "✗ Backup failed!"
    exit 1
fi

# Clean up old backups
echo "Cleaning up backups older than ${RETENTION_DAYS} days..."
find "${BACKUP_DIR}" -name "roanes_kitchen_*.sql.gz" -type f -mtime +${RETENTION_DAYS} -delete

# Count remaining backups
BACKUP_COUNT=$(find "${BACKUP_DIR}" -name "roanes_kitchen_*.sql.gz" -type f | wc -l)
echo "Current backup count: ${BACKUP_COUNT}"

echo "Completed at: $(date)"
echo "==================================="
