#!/bin/bash
# Database restore script for Coffee-Berry Stores Management System
# Usage: ./restore.sh <backup_file.sql.gz>

set -e

if [ -z "$1" ]; then
    echo "Usage: $0 <backup_file.sql.gz>"
    exit 1
fi

BACKUP_FILE="$1"

if [ ! -f "$BACKUP_FILE" ]; then
    echo "Error: Backup file not found: $BACKUP_FILE"
    exit 1
fi

DB_NAME="${POSTGRES_DB:-coffee_berry}"
DB_USER="${POSTGRES_USER:-postgres}"
DB_HOST="${POSTGRES_HOST:-postgres}"
DB_PORT="${POSTGRES_PORT:-5432}"

echo "Warning: This will restore database $DB_NAME from backup!"
echo "Press Ctrl+C to cancel, or Enter to continue..."
read

echo "Restoring database from $BACKUP_FILE..."

# Use docker exec if running in docker, or direct psql
if command -v docker &> /dev/null; then
    gunzip -c "$BACKUP_FILE" | docker exec -i coffee-berry-postgres psql -U "$DB_USER" -d "$DB_NAME"
else
    gunzip -c "$BACKUP_FILE" | PGPASSWORD="${POSTGRES_PASSWORD}" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME"
fi

if [ $? -eq 0 ]; then
    echo "Database restored successfully!"
else
    echo "Restore failed!"
    exit 1
fi
