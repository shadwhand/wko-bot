#!/bin/bash
# Daily Empirical Cycling podcast auto-pull
# Checks RSS feed for new episodes, downloads and transcribes with mlx-whisper
# Add to crontab: 0 6 * * * /Users/jshin/Documents/wko5-experiments/tools/knowledge-scraper/ec_cron.sh

source /tmp/fitenv/bin/activate
cd /Users/jshin/Documents/wko5-experiments
python tools/knowledge-scraper/ec_auto_pull.py >> /tmp/ec_auto_pull.log 2>&1
