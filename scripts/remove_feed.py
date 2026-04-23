#!/usr/bin/env python3
"""Remove a feed from config.json by URL or name.

Usage: remove_feed.py <url-or-name>

Matches against feed `url` first, then `name` (exact match, then
case-insensitive substring). Fails if zero or >1 matches unless
--force picks the first match.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from lib.config import load_config, save_config


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("query")
    ap.add_argument("--force", action="store_true",
                    help="On multiple matches, remove the first.")
    args = ap.parse_args()

    cfg = load_config()
    feeds = cfg.get("feeds", [])
    q = args.query.strip()
    q_low = q.lower()

    exact = [i for i, f in enumerate(feeds) if f.get("url") == q or f.get("name") == q]
    if exact:
        matches = exact
    else:
        matches = [i for i, f in enumerate(feeds)
                   if q_low in (f.get("name", "").lower())
                   or q_low in (f.get("url", "").lower())]

    if not matches:
        print(json.dumps({"status": "error", "error": f"No feed matches '{q}'"}))
        sys.exit(1)

    if len(matches) > 1 and not args.force:
        print(json.dumps({
            "status": "error",
            "error": f"{len(matches)} feeds match '{q}' — be more specific or pass --force",
            "matches": [{"name": feeds[i].get("name"), "url": feeds[i].get("url")}
                        for i in matches],
        }, indent=2))
        sys.exit(1)

    idx = matches[0]
    removed = feeds.pop(idx)
    cfg["feeds"] = feeds
    save_config(cfg)

    print(json.dumps({
        "status": "ok",
        "removed": {"name": removed.get("name"), "url": removed.get("url")},
        "feeds_remaining": len(feeds),
    }, indent=2))


if __name__ == "__main__":
    main()
