"""Paths, config.json, state.json."""
from __future__ import annotations

import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

DATA_DIR = Path(
    os.environ.get("RSS_TRACKER_HOME")
    or Path.home() / ".claude" / "skills-data" / "academic-journal-rss"
)
CONFIG_PATH = DATA_DIR / "config.json"
STATE_PATH = DATA_DIR / "state.json"

DIGEST_DIR = Path(
    os.environ.get("RSS_TRACKER_DIGEST_DIR") or Path.home() / "rss-digest"
)

DEFAULT_CONFIG: dict[str, Any] = {
    "interests": "",
    "feeds": [],
    "feed_overrides": {},
    "notifications": {
        "markdown_dir": str(DIGEST_DIR),
        "desktop": True,
        "email": {"enabled": False, "to": ""},
    },
    "settings": {
        "filter_window_hours": 48,
        "top_n": 5,
        "min_relevance": 3,
        "seen_retention_days": 30,
    },
}


def ensure_dirs() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    Path(load_config()["notifications"]["markdown_dir"]).expanduser().mkdir(
        parents=True, exist_ok=True
    )


def load_config() -> dict[str, Any]:
    if not CONFIG_PATH.exists():
        return json.loads(json.dumps(DEFAULT_CONFIG))
    cfg = json.loads(CONFIG_PATH.read_text())
    # shallow-merge defaults for forward compat
    for k, v in DEFAULT_CONFIG.items():
        cfg.setdefault(k, v)
    return cfg


def save_config(cfg: dict[str, Any]) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(json.dumps(cfg, indent=2, ensure_ascii=False))


def load_state() -> dict[str, Any]:
    if not STATE_PATH.exists():
        return {"last_run": None, "seen_guids": {}}
    return json.loads(STATE_PATH.read_text())


def save_state(state: dict[str, Any]) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps(state, indent=2, ensure_ascii=False))


def prune_state(state: dict[str, Any], retention_days: int) -> dict[str, Any]:
    cutoff = datetime.now(timezone.utc) - timedelta(days=retention_days)
    kept = {
        g: ts
        for g, ts in state.get("seen_guids", {}).items()
        if _parse_iso(ts) >= cutoff
    }
    state["seen_guids"] = kept
    return state


def _parse_iso(ts: str) -> datetime:
    try:
        dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        return datetime.fromtimestamp(0, tz=timezone.utc)


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")
