#!/bin/bash
# Database backup script for Coffee-Berry Stores Management System
# This script should be run via cron for automated backups

set -e

# Configuration
BACKUP_DIR="/opt/coffee-berry/backups"
RETENTION_DAYS=7
DATE=$(date +%Y%m%d_%H%M%S)
DB_NAME="${POSTGRES_DB:-coffee_berry}"
DB_USER="${POSTGRES_USER:-postgres}"
DB_HOST="${POSTGRES_HOST:-postgres}"
DB_PORT="${POSTGRES_PORT:-5432}"

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

# Backup database
echo "Starting database backup..."
BACKUP_FILE="$BACKUP_DIR/db_backup_$DATE.sql.gz"

# Use docker exec if running in docker, or direct pg_dump
if command -v docker &> /dev/null; then
    docker exec coffee-berry-postgres pg_dump -U "$DB_USER" -d "$DB_NAME" | gzip > "$BACKUP_FILE"
else
    PGPASSWORD="${POSTGRES_PASSWORD}" pg_dump -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" | gzip > "$BACKUP_FILE"
fi

if [ $? -eq 0 ]; then
    echo "Backup completed: $BACKUP_FILE"
    
    # Compress backup
    if [ -f "$BACKUP_FILE" ]; then
        BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
        echo "Backup size: $BACKUP_SIZE"
    fi
else
    echo "Backup failed!"
    exit 1
fi

# Clean up old backups (keep only last N days)
echo "Cleaning up old backups (keeping last $RETENTION_DAYS days)..."
find "$BACKUP_DIR" -name "db_backup_*.sql.gz" -mtime +$RETENTION_DAYS -delete

# Count remaining backups
REMAINING_BACKUPS=$(find "$BACKUP_DIR" -name "db_backup_*.sql.gz" | wc -l)
echo "Remaining backups: $REMAINING_BACKUPS"

echo "Backup process completed successfully!"
