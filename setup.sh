#!/usr/bin/env bash
set -e

echo "========================================="
echo "  WKO5 Analyzer — Setup"
echo "========================================="
echo ""

# ── Step 1: Python environment ──────────────────────────────
echo "Step 1/5: Python environment"
if [ -d ".venv" ]; then
    echo "  .venv exists, activating..."
else
    echo "  Creating .venv..."
    python3 -m venv .venv
fi
source .venv/bin/activate
echo "  Installing Python dependencies..."
pip install -q numpy pandas scipy matplotlib fitdecode garth httpx fastapi uvicorn cmdstanpy duckdb
echo "  ✓ Python environment ready"
echo ""

# ── Step 2: Athlete config ──────────────────────────────────
echo "Step 2/5: Athlete configuration"
echo ""
echo "  We need a few details to personalize your analytics."
echo ""

read -p "  Your name: " NAME
read -p "  Weight in kg (e.g. 75): " WEIGHT
read -p "  Sex (male/female): " SEX
read -p "  Max heart rate (e.g. 190, or press Enter to skip): " MAX_HR
read -p "  FTP in watts (e.g. 250, or press Enter to skip): " FTP
read -p "  Bike weight in kg (e.g. 8.5, default 9.0): " BIKE_WEIGHT

WEIGHT=${WEIGHT:-78.0}
SEX=${SEX:-male}
MAX_HR=${MAX_HR:-186}
FTP=${FTP:-250}
BIKE_WEIGHT=${BIKE_WEIGHT:-9.0}

python3 -c "
from wko5.config import init_config_table, set_config
init_config_table()
set_config('name', '$NAME')
set_config('weight_kg', $WEIGHT)
set_config('sex', '$SEX')
set_config('max_hr', $MAX_HR)
set_config('ftp_manual', $FTP)
set_config('bike_weight_kg', $BIKE_WEIGHT)
print('  ✓ Config saved to wko5/cycling_power.duckdb')
"
echo ""

# ── Step 3: Data source ─────────────────────────────────────
echo "Step 3/5: Connect your data"
echo ""
echo "  How do you want to get your ride data?"
echo ""
echo "  1) Garmin Connect (sync via API)"
echo "  2) Strava (sync via API)"
echo "  3) Bulk FIT file import (Garmin export, Wahoo, etc.)"
echo "  4) Skip for now"
echo ""
read -p "  Choose [1-4]: " DATA_SOURCE

case $DATA_SOURCE in
    1)
        echo ""
        echo "  Syncing from Garmin Connect..."
        echo "  You'll be prompted for your Garmin email and password."
        echo "  Tokens are saved to ~/.garth/ for future syncs."
        echo ""
        read -p "  How many days of history? (default: 90): " DAYS
        DAYS=${DAYS:-90}
        python3 wko5/garmin_sync.py --days "$DAYS" --save-fit
        echo "  ✓ Garmin sync complete"
        ;;
    2)
        echo ""
        echo "  Strava API Setup"
        echo "  ─────────────────"
        echo ""
        echo "  You need a free Strava API app (takes 2 minutes):"
        echo ""
        echo "    1. Go to https://www.strava.com/settings/api"
        echo "    2. Fill in the form:"
        echo "       - Application Name: anything (e.g. 'WKO5 Analyzer')"
        echo "       - Category: 'Data Importer'"
        echo "       - Club: leave blank"
        echo "       - Website: http://localhost"
        echo "       - Authorization Callback Domain: localhost"
        echo "    3. Click 'Create'"
        echo "    4. You'll see your Client ID and Client Secret"
        echo ""
        read -p "  Press Enter when you've created the app..."
        echo ""
        read -p "  How many days of history? (default: 90): " DAYS
        DAYS=${DAYS:-90}
        echo "  A browser will open for you to authorize access."
        python3 wko5/strava_sync.py --days "$DAYS"
        echo "  ✓ Strava sync complete"
        ;;
    3)
        echo ""
        echo "  Place your .fit files in the fit-files/ directory."
        echo "  (Works with Garmin export, Wahoo, Hammerhead, etc.)"
        mkdir -p fit-files
        read -p "  Press Enter when files are in fit-files/..."
        python3 wko5/ingest_missing.py
        echo "  ✓ FIT file import complete"
        ;;
    4)
        echo "  Skipping data import. You can run this later:"
        echo "    python wko5/garmin_sync.py --days 90"
        echo "    python wko5/strava_sync.py --days 90"
        echo "    python wko5/ingest_missing.py"
        ;;
    *)
        echo "  Invalid choice, skipping."
        ;;
esac
echo ""

# ── Step 4: Knowledge base (qmd) ───────────────────────────
echo "Step 4/5: Knowledge base setup"
if command -v qmd &>/dev/null; then
    echo "  qmd already installed ($(qmd --version 2>/dev/null | head -1))"
else
    echo "  Installing qmd..."
    if command -v npm &>/dev/null; then
        npm install -g @tobilu/qmd
    elif command -v bun &>/dev/null; then
        bun install -g @tobilu/qmd
    else
        echo "  ⚠ Node.js not found. Install Node.js 20+ then run: npm install -g @tobilu/qmd"
        echo "  Skipping knowledge base setup."
        echo ""
        goto_step5=true
    fi
fi

if [ "$goto_step5" != "true" ]; then
    echo "  Indexing knowledge base..."
    qmd update 2>&1 | tail -3
    echo "  Generating embeddings (this takes ~2 min on first run)..."
    qmd embed 2>&1 | tail -3
    echo "  ✓ Knowledge base ready ($(qmd status 2>/dev/null | grep 'Total:' | head -1))"
fi
echo ""

# ── Step 5: Verify ──────────────────────────────────────────
echo "Step 5/5: Verification"
echo ""

python3 -c "
from wko5.db import get_connection
conn = get_connection()
count = conn.execute('SELECT COUNT(*) FROM activities').fetchone()[0]
print(f'  Activities in database: {count}')
conn.close()
" 2>/dev/null || echo "  Activities in database: 0 (no data imported yet)"

python3 -c "
from wko5.config import get_config
c = get_config()
print(f\"  Athlete: {c.get('name', 'default')} ({c.get('weight_kg')} kg, FTP {c.get('ftp_manual')}W)\")
" 2>/dev/null || echo "  Config: using defaults"

if command -v qmd &>/dev/null; then
    echo "  Knowledge base: $(qmd status 2>/dev/null | grep 'Total:' | head -1 || echo 'not indexed')"
fi

echo ""
echo "========================================="
echo "  Setup complete!"
echo "========================================="
echo ""
echo "Next steps:"
echo "  - Start the API:     source .venv/bin/activate && uvicorn wko5.api.app:app --port 8000"
echo "  - Start qmd daemon:  qmd mcp --http --daemon"
echo "  - Run tests:         python -m pytest tests/ -v"
echo "  - Open notebooks:    jupyter notebook notebooks/"
echo ""
echo "For Claude Code users:"
echo "  The qmd MCP server is auto-configured. Ask about your training"
echo "  and the wiki knowledge base will inform the answers."
echo ""
