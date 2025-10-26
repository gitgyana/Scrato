#!/bin/bash
source /home/debian/Projects/Scrato/ScratoEnv/bin/activate
python /home/debian/Projects/Scrato/news_scraper.py


#!/bin/bash

LOG_DIR="/home/debian/Projects/Scrato/logs"
LOG_FILE="$LOG_DIR/start_scrato.log"

mkdir -p $LOG_DIR

echo "Activating virtual environment..." >> $LOG_FILE
source /home/debian/Projects/Scrato/ScratoEnv/bin/activate

echo "$(date '+%Y-%m-%d %H:%M:%S') - Starting Scrato..." >> "$LOG_FILE"

python /home/debian/Projects/Scrato/news_scraper.py
STATUS=$?

if [ $STATUS -eq 0 ]; then
    echo "$(date '+%Y-%m-%d %H:%M:%S') - Scrato finished successfully." >> "$LOG_FILE"
else
    echo "$(date '+%Y-%m-%d %H:%M:%S') - Scrato FAILED with code $STATUS." >> "$LOG_FILE"
fi

deactivate

