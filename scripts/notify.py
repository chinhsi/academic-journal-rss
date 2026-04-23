#!/usr/bin/env python3
"""Write digest markdown + (optional) desktop notification.

Usage: notify.py --digest-file <path> [--title "..."] [--summary "..."]

Email via Claude.ai Gmail MCP is handled by SKILL.md instructing Claude to
call the MCP tool directly — not from this script — so we don't need
credentials here.
"""
from __future__ import annotations

import argparse
import json
import platform
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from lib.config import load_config


def desktop_notify(title: str, message: str) -> dict[str, str]:
    system = platform.system()
    try:
        if system == "Darwin":
            subprocess.run(
                [
                    "osascript",
                    "-e",
                    f'display notification {json.dumps(message)} with title {json.dumps(title)}',
                ],
                check=True,
                timeout=5,
            )
            return {"status": "ok", "method": "osascript"}
        if system == "Linux" and shutil.which("notify-send"):
            subprocess.run(["notify-send", title, message], check=True, timeout=5)
            return {"status": "ok", "method": "notify-send"}
        if system == "Windows":
            ps = (
                "[Windows.UI.Notifications.ToastNotificationManager,"
                "Windows.UI.Notifications,ContentType=WindowsRuntime] | Out-Null;"
                f"$t=[Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent(1);"
                f"$t.GetElementsByTagName('text').Item(0).AppendChild($t.CreateTextNode({json.dumps(title)}))|Out-Null;"
                f"[Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier('rss-tracker').Show([Windows.UI.Notifications.ToastNotification]::new($t))"
            )
            subprocess.run(["powershell", "-Command", ps], check=True, timeout=5)
            return {"status": "ok", "method": "powershell"}
        return {"status": "skipped", "reason": f"no notifier for {system}"}
    except Exception as e:
        return {"status": "error", "reason": str(e)}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--digest-file", required=True)
    ap.add_argument("--title", default="RSS digest ready")
    ap.add_argument("--summary", default="")
    args = ap.parse_args()

    cfg = load_config()
    digest_path = Path(args.digest_file).expanduser()
    result: dict = {"digest": str(digest_path), "desktop": None}

    if not digest_path.exists():
        print(
            json.dumps({"status": "error", "reason": "digest file missing"}, indent=2),
            file=sys.stderr,
        )
        sys.exit(1)

    if cfg["notifications"].get("desktop"):
        summary = args.summary or f"Saved to {digest_path}"
        result["desktop"] = desktop_notify(args.title, summary)

    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
