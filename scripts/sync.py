#!/usr/bin/env python3
"""Fetch all enabled feeds, emit new items (not in seen_guids, within window).

Prints JSON: {"new_items": [...], "stats": {...}, "errors": [...]}
Does NOT flip items to seen until notify/digest runs confirm delivery —
instead, the caller passes --mark to mark them seen when done.

Usage:
  sync.py              fetch + print new items (dry)
  sync.py --mark       fetch + mark newly-found GUIDs as seen in state
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import feedparser

from lib.config import (
    load_config,
    load_state,
    prune_state,
    save_state,
    utc_now_iso,
)
from lib.fetch import fetch_feed


def guid_hash(feed_url: str, entry: Any) -> str:
    raw = entry.get("id") or entry.get("guid") or entry.get("link") or entry.get("title", "")
    h = hashlib.sha1(f"{feed_url}|{raw}".encode("utf-8")).hexdigest()
    return h


def entry_published(entry: Any) -> datetime | None:
    for key in ("published_parsed", "updated_parsed"):
        v = entry.get(key)
        if v:
            try:
                return datetime(*v[:6], tzinfo=timezone.utc)
            except Exception:
                continue
    return None


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mark", action="store_true", help="mark newly-found GUIDs as seen")
    args = ap.parse_args()

    cfg = load_config()
    state = load_state()
    state = prune_state(state, cfg["settings"]["seen_retention_days"])
    seen = state["seen_guids"]

    window_hours = cfg["settings"]["filter_window_hours"]
    cutoff = datetime.now(timezone.utc) - timedelta(hours=window_hours)

    new_items: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    feed_stats: list[dict[str, Any]] = []

    for feed in cfg.get("feeds", []):
        if not feed.get("enabled", True):
            continue
        url = feed["url"]
        override = cfg.get("feed_overrides", {}).get(url, {})
        t0 = time.time()
        try:
            raw = fetch_feed(url, override)
            parsed = feedparser.parse(raw)
        except Exception as e:
            errors.append({"feed": feed["name"], "url": url, "error": str(e)})
            feed_stats.append(
                {"feed": feed["name"], "status": "error", "new": 0, "total": 0}
            )
            continue

        n_new = 0
        for entry in parsed.entries:
            h = guid_hash(url, entry)
            if h in seen:
                continue
            pub = entry_published(entry)
            if pub and pub < cutoff:
                continue

            item = {
                "guid": h,
                "feed": feed["name"],
                "feed_url": url,
                "category": feed.get("category"),
                "title": (entry.get("title") or "").strip(),
                "link": entry.get("link"),
                "authors": [a.get("name") for a in entry.get("authors", []) if a.get("name")]
                or ([entry.get("author")] if entry.get("author") else []),
                "published": pub.isoformat() if pub else None,
                "summary": (entry.get("summary") or "").strip(),
            }
            new_items.append(item)
            n_new += 1

        feed_stats.append(
            {
                "feed": feed["name"],
                "status": "ok",
                "new": n_new,
                "total": len(parsed.entries),
                "elapsed_ms": int((time.time() - t0) * 1000),
            }
        )

    if args.mark:
        now = utc_now_iso()
        for item in new_items:
            seen[item["guid"]] = now
        state["seen_guids"] = seen
        state["last_run"] = now
        save_state(state)

    print(
        json.dumps(
            {
                "new_items": new_items,
                "stats": {"feeds": feed_stats, "new_count": len(new_items)},
                "errors": errors,
                "marked": args.mark,
                "settings": {
                    "filter_window_hours": window_hours,
                    "top_n": cfg["settings"]["top_n"],
                    "min_relevance": cfg["settings"]["min_relevance"],
                },
                "interests": cfg.get("interests", ""),
                "notifications": cfg.get("notifications", {}),
            },
            indent=2,
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
