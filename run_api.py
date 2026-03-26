#!/usr/bin/env python3
"""Launch the WKO5 Analyzer API server."""

import json
import secrets
import socket
import threading
from pathlib import Path
import uvicorn
from wko5.api.app import create_app
from wko5.config import init_config_table


def main():
    init_config_table()
    token = secrets.token_urlsafe(32)
    app = create_app(token=token)

    # Find an available port
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    sock.close()

    # Write runtime config so frontend (Vite proxy) and launcher can discover port/token
    runtime_path = Path(__file__).resolve().parent / ".runtime.json"
    runtime = {
        "port": port,
        "token": token,
        "api_url": f"http://127.0.0.1:{port}",
    }
    runtime_path.write_text(json.dumps(runtime, indent=2) + "\n")

    import sys
    sys.stderr.write(f"\n  WKO5 Analyzer API\n")
    sys.stderr.write(f"  Dashboard: http://127.0.0.1:{port}?token={token}\n")
    sys.stderr.write(f"  Auth token: {token}\n")
    sys.stderr.flush()

    # Start cache warmup in background thread
    from wko5.api.routes import warmup_cache
    sys.stderr.write(f"\n  [warmup] Pre-computing PMC, model, profile, clinical flags...\n")
    sys.stderr.flush()
    warmup_thread = threading.Thread(target=warmup_cache, daemon=True)
    warmup_thread.start()

    uvicorn.run(app, host="127.0.0.1", port=port, log_level="warning")


if __name__ == "__main__":
    main()
