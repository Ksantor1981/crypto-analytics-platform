#!/bin/bash
# Database backup script. Run daily via cron:
# 0 2 * * * cd /workspace/backend && bash backup_db.sh
BACKUP_DIR="/workspace/backups"
mkdir -p "$BACKUP_DIR"
DATE=$(date +%Y%m%d_%H%M%S)

if [ -f crypto_analytics.db ]; then
    cp crypto_analytics.db "$BACKUP_DIR/crypto_analytics_${DATE}.db"
    echo "$(date) Backup: $BACKUP_DIR/crypto_analytics_${DATE}.db ($(du -h crypto_analytics.db | cut -f1))"
    # Keep last 7 backups
    ls -t "$BACKUP_DIR"/crypto_analytics_*.db | tail -n +8 | xargs rm -f 2>/dev/null
fi
