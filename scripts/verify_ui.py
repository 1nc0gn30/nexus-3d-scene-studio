"""
verify_ui.py
Automated Headless Playwright Verification Harness for Nexus 3D Scene Studio.
Verifies triple-viewport responsiveness, zero console errors, and zero horizontal overflow
on an ephemeral loopback port.
"""

from __future__ import annotations

import os
import sys
import tempfile
import threading
import time
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR / "src"))

from nexus_3d_scene_studio.ui_server import start_ui_server  # noqa: E402


def verify() -> int:
    from playwright.sync_api import sync_playwright

    shot_dir = Path(os.environ.get("NEXUS3D_SHOT_DIR", tempfile.mkdtemp(prefix="nexus3d_shots_")))
    shot_dir.mkdir(parents=True, exist_ok=True)

    server = start_ui_server("127.0.0.1", 0, public_dir=str(ROOT_DIR / "public"))
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base_url = f"http://127.0.0.1:{port}"

    viewports = [
        {"name": "home_mobile.jpg", "width": 390, "height": 844, "device": "Mobile (390x844)"},
        {"name": "home_tablet.jpg", "width": 820, "height": 1180, "device": "Tablet (820x1180)"},
        {"name": "home_desktop.jpg", "width": 1425, "height": 900, "device": "Desktop (1425x900)"},
    ]

    console_errors: list[str] = []
    viewport_results = []

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=["--no-sandbox", "--disable-gpu", "--disable-dev-shm-usage"],
            )
            for vp in viewports:
                page = browser.new_page(viewport={"width": vp["width"], "height": vp["height"]})
                vp_errors: list[str] = []
                page.on("console", lambda msg, errs=vp_errors: errs.append(msg.text) if msg.type == "error" else None)
                page.on("pageerror", lambda err, errs=vp_errors: errs.append(str(err)))

                page.goto(base_url, wait_until="networkidle")
                time.sleep(0.4)

                overflow = page.evaluate(
                    "() => document.documentElement.scrollWidth - document.documentElement.clientWidth"
                )
                page.screenshot(path=str(shot_dir / vp["name"]), full_page=False, type="jpeg", quality=85)

                passed = len(vp_errors) == 0 and overflow <= 1
                console_errors.extend(vp_errors)
                viewport_results.append({"device": vp["device"], "overflow": overflow, "passed": passed})
                page.close()
            browser.close()
    finally:
        server.shutdown()
        server.server_close()

    all_passed = len(console_errors) == 0 and all(v["passed"] for v in viewport_results)
    for v in viewport_results:
        print(f"[VIEWPORT] {v['device']}: overflow={v['overflow']}px -> {'PASS' if v['passed'] else 'FAIL'}")
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(verify())
