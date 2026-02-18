"""Entry point for ``python -m tahalilai``."""

from __future__ import annotations

import socket

import uvicorn

from tahalilai.config import get_settings


def main() -> None:
    """Start the TahalilAI uvicorn server."""
    settings = get_settings()
    port = settings.port

    # Warn if port is already occupied
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        if sock.connect_ex(("127.0.0.1", port)) == 0:
            print(f"WARNING: Port {port} is already in use.")
            print("Another instance may be running. Attempting to start anyway...")

    try:
        uvicorn.run(
            "tahalilai.app:app",
            host=settings.host,
            port=port,
            timeout_keep_alive=700,
        )
    except OSError as exc:
        if "10048" in str(exc) or "Address already in use" in str(exc):
            print(f"\nERROR: Port {port} is occupied.")
            print(f"  Windows: netstat -ano | findstr :{port}")
            print("  Then:    taskkill /PID <PID> /F")
        else:
            raise


if __name__ == "__main__":
    main()
