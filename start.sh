#!/bin/bash
# start.sh — Start backend + frontend dev server
set -e

cd "$(dirname "$0")"

echo "Starting WKO5 backend..."
source /tmp/fitenv/bin/activate
python run_api.py &
BACKEND_PID=$!
sleep 4

# Read runtime config
PORT=$(python3 -c "import json; print(json.load(open('.runtime.json'))['port'])")
TOKEN=$(python3 -c "import json; print(json.load(open('.runtime.json'))['token'])")
echo "Backend running on port $PORT"

echo "Starting frontend dev server..."
cd frontend-v2
npm run dev &
FRONTEND_PID=$!
sleep 2

echo ""
echo "  Dashboard: http://localhost:5173?token=$TOKEN"
echo "  API:       http://127.0.0.1:$PORT"
echo ""
echo "Press Ctrl+C to stop both servers"

trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null" EXIT
wait
