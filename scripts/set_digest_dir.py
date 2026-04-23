#!/usr/bin/env python3
"""Set the digest output directory.

Usage: set_digest_dir.py <path>

Expands ~ and env vars, resolves to absolute, creates the directory if
missing, writes to config.notifications.markdown_dir. Fails if the path
cannot be created (permission / invalid parent).
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from lib.config import load_config, save_config


def main() -> None:
    if len(sys.argv) < 2:
        print(json.dumps({"status": "error", "error": "Missing <path>"}))
        sys.exit(2)

    raw = sys.argv[1]
    expanded = Path(os.path.expandvars(os.path.expanduser(raw))).resolve()

    try:
        expanded.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        print(json.dumps({
            "status": "error",
            "error": f"Cannot create directory: {e}",
            "path": str(expanded),
        }))
        sys.exit(1)

    cfg = load_config()
    cfg.setdefault("notifications", {})["markdown_dir"] = str(expanded)
    save_config(cfg)

    print(json.dumps({
        "status": "ok",
        "markdown_dir": str(expanded),
    }, indent=2))


if __name__ == "__main__":
    main()
