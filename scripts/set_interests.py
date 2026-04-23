#!/usr/bin/env python3
"""Set config.interests verbatim.

Usage: set_interests.py <text>
       echo "..." | set_interests.py -

Reads from argv[1] or stdin (when argv[1] is '-'). Writes the string
exactly as given; no paraphrase, no truncation.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from lib.config import load_config, save_config


def main() -> None:
    if len(sys.argv) < 2:
        print(json.dumps({"status": "error", "error": "Missing argument"}))
        sys.exit(2)

    arg = sys.argv[1]
    text = sys.stdin.read() if arg == "-" else arg

    cfg = load_config()
    cfg["interests"] = text.strip()
    save_config(cfg)

    print(json.dumps({
        "status": "ok",
        "interests_chars": len(cfg["interests"]),
    }, indent=2))


if __name__ == "__main__":
    main()
