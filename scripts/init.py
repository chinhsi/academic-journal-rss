#!/usr/bin/env python3
"""First-time setup: check deps, create data dir, write initial config.json.

Non-interactive: safe to re-run. Does not overwrite an existing config.
Prints the paths so the skill wrapper can follow up with a Claude-driven
wizard that fills in interests and adds feeds.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SKILL_ROOT))


def _ensure_deps() -> None:
    """Import feedparser + httpx; auto-install from requirements.txt on failure.

    macOS system python throws PEP 668 (externally-managed-environment);
    retry with --break-system-packages.
    """
    try:
        import feedparser  # noqa: F401
        import httpx  # noqa: F401
        return
    except ImportError:
        pass

    req = SKILL_ROOT / "requirements.txt"
    cmd = [sys.executable, "-m", "pip", "install", "--user", "-r", str(req)]

    print(f"Installing dependencies from {req}...", file=sys.stderr)
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0 and "externally-managed-environment" in res.stderr:
        print("Retrying with --break-system-packages (PEP 668)...", file=sys.stderr)
        res = subprocess.run(cmd + ["--break-system-packages"], capture_output=True, text=True)

    if res.returncode != 0:
        print(json.dumps({
            "status": "error",
            "error": "Failed to install dependencies",
            "stderr": res.stderr.strip(),
            "hint": f"Run manually: {sys.executable} -m pip install --user -r {req}",
        }, indent=2))
        sys.exit(1)

    try:
        import feedparser  # noqa: F401
        import httpx  # noqa: F401
    except ImportError as e:
        print(json.dumps({
            "status": "error",
            "error": f"Install reported success but import still fails: {e}",
        }, indent=2))
        sys.exit(1)


_ensure_deps()

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
