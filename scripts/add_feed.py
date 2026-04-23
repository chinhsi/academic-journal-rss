#!/usr/bin/env python3
"""Add a feed to config.json.

Usage: add_feed.py <url> [--name NAME] [--category CAT]

Validates the URL is fetchable and parseable before saving.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import feedparser

from lib.config import load_config, save_config
from lib.fetch import fetch_feed


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("url")
    ap.add_argument("--name", default=None)
    ap.add_argument("--category", default=None)
    ap.add_argument("--skip-validate", action="store_true")
    args = ap.parse_args()

    cfg = load_config()

    for f in cfg["feeds"]:
        if f["url"] == args.url:
            print(
                json.dumps({"status": "duplicate", "feed": f}, indent=2),
                file=sys.stderr,
            )
            sys.exit(2)

    name = args.name
    inferred_title = None
    if not args.skip_validate:
        try:
            raw = fetch_feed(args.url)
            parsed = feedparser.parse(raw)
            if parsed.bozo and not parsed.entries:
                print(
                    json.dumps(
                        {
                            "status": "error",
                            "reason": "unparseable feed",
                            "bozo_exception": str(parsed.bozo_exception),
                        },
                        indent=2,
                    ),
                    file=sys.stderr,
                )
                sys.exit(1)
            inferred_title = (parsed.feed.get("title") or "").strip() or None
        except Exception as e:
            print(
                json.dumps({"status": "error", "reason": str(e)}, indent=2),
                file=sys.stderr,
            )
            sys.exit(1)

    feed = {
        "name": name or inferred_title or args.url,
        "url": args.url,
        "category": args.category,
        "enabled": True,
    }
    cfg["feeds"].append(feed)
    save_config(cfg)

    print(json.dumps({"status": "added", "feed": feed}, indent=2))


if __name__ == "__main__":
    main()
