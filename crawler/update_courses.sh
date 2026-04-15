#!/bin/bash

# Course data update script
# This script runs the crawler and redirects output to a log file
# for real-time monitoring via the web interface

# Configuration
LOG_FILE="/tmp/crawler_fetch.log"
CRAWLER_DIR="/home/deploy/xkB/crawler"

# Clear old log and start fresh
> "$LOG_FILE"
echo "[$(date '+%Y-%m-%d %H:%M:%S')] 开始数据更新任务" >> "$LOG_FILE"

# Change to crawler directory
cd "$CRAWLER_DIR" || exit 1

# Activate virtual environment if exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Run crawler and redirect all output to log file
python fetchCourseList.py >> "$LOG_FILE" 2>&1

# Check exit status
if [ $? -eq 0 ]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] 数据更新完成" >> "$LOG_FILE"
else
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] 数据更新失败" >> "$LOG_FILE"
fi

# Log file will be automatically cleared on next run
