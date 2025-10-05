#!/bin/bash

# Configuration
DB_CONTAINER="acm-meeting-records-db"
DB_USER="admin"
DB_NAME="acm-meetings-db"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="db_backup_$DATE.sql"

# Create backup
docker exec -t $DB_CONTAINER pg_dump -U $DB_USER $DB_NAME > $BACKUP_FILE
if [ $? -eq 0 ]; then
    echo "Backup successful: $BACKUP_FILE"
else
    echo "Backup failed"
    exit 1
fi