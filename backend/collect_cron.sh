#!/bin/bash
# Cron script for signal collection. Run every 15 minutes:
# */15 * * * * cd /workspace/backend && bash collect_cron.sh >> /tmp/collect_cron.log 2>&1

cd "$(dirname "$0")"
source .venv/bin/activate
export USE_SQLITE=true
export SECRET_KEY="${SECRET_KEY:-dev-key-32chars-minimum-length!!}"

echo "=== $(date) === Collecting signals..."

# Telegram channels
python -m app.tasks.collect_signals 2>&1 | tail -3

# Reddit
python -c "
import asyncio
from app.services.reddit_scraper import collect_all_reddit_signals
r = asyncio.run(collect_all_reddit_signals())
print(f'Reddit: {r[\"signals_found\"]} signals from {r[\"subreddits\"]} subs')
" 2>&1 | tail -1

echo "=== Done ==="
