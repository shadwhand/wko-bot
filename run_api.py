#!/usr/bin/env python3
"""Launch the WKO5 Analyzer API server."""

import secrets
import socket
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

    print(f"\n  WKO5 Analyzer API running at: http://127.0.0.1:{port}")
    print(f"  Auth token: {token}")
    print(f"\n  Example: curl -H 'Authorization: Bearer {token}' http://127.0.0.1:{port}/api/fitness\n")

    uvicorn.run(app, host="127.0.0.1", port=port, log_level="info")


if __name__ == "__main__":
    main()
