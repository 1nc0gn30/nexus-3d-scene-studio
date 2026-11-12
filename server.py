#!/usr/bin/env python3
"""
Nexus 3D Scene Studio — Sovereign Server Launcher.
Zero-dependency 3D WebGL Scene & Procedural Mesh Studio on port 8082.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
SRC_DIR = BASE_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from nexus_3d_scene_studio.ui_server import start_ui_server

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Nexus 3D Scene Studio Server")
    parser.add_argument("--host", default="127.0.0.1", help="Host interface (default: 127.0.0.1)")
    parser.add_argument("--port", "-p", type=int, default=8082, help="Port to listen on (default: 8082)")
    args = parser.parse_args()

    print(f"✦ Starting Nexus 3D Scene Studio on http://{args.host}:{args.port}")
    server = start_ui_server(host=args.host, port=args.port, open_browser=False)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down Nexus 3D Scene Studio server...")
        server.server_close()
