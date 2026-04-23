#!/usr/bin/env python3
"""First-time setup: create data dir, write initial config.json.

Non-interactive: safe to re-run. Does not overwrite an existing config.
Prints the paths so the skill wrapper can follow up with a Claude-driven
wizard that fills in interests and adds feeds.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from lib.config import (
    CONFIG_PATH,
    DATA_DIR,
    DIGEST_DIR,
    STATE_PATH,
    ensure_dirs,
    load_config,
    save_config,
    save_state,
)


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    if CONFIG_PATH.exists():
        cfg = load_config()
        status = "existing"
    else:
        cfg = load_config()  # returns defaults
        save_config(cfg)
        status = "created"

    if not STATE_PATH.exists():
        save_state({"last_run": None, "seen_guids": {}})

    Path(cfg["notifications"]["markdown_dir"]).expanduser().mkdir(
        parents=True, exist_ok=True
    )

    print(
        json.dumps(
            {
                "status": status,
                "data_dir": str(DATA_DIR),
                "config_path": str(CONFIG_PATH),
                "state_path": str(STATE_PATH),
                "digest_dir": str(Path(cfg["notifications"]["markdown_dir"]).expanduser()),
                "feeds_count": len(cfg.get("feeds", [])),
                "has_interests": bool(cfg.get("interests")),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
