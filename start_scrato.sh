#!/bin/bash
export PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"

LOG_DIR="/home/debian/Projects/Scrato/logs"
LOG_FILE="$LOG_DIR/start_scrato.log"

mkdir -p "$LOG_DIR"

echo "Activating virtual environment..." >> "$LOG_FILE"
source /home/debian/Projects/Scrato/ScratoEnv/bin/activate

echo "$(/usr/bin/date '+%Y-%m-%d %H:%M:%S') - Starting Scrato..." >> "$LOG_FILE"

python /home/debian/Projects/Scrato/news_scraper.py
STATUS=$?

if [ $STATUS -eq 0 ]; then
    echo "$(/usr/bin/date '+%Y-%m-%d %H:%M:%S') - Scrato finished successfully." >> "$LOG_FILE"
else
    echo "$(/usr/bin/date '+%Y-%m-%d %H:%M:%S') - Scrato FAILED with code $STATUS." >> "$LOG_FILE"
fi

deactivate

