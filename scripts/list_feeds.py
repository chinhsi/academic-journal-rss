#!/usr/bin/env python3
"""List configured feeds."""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from lib.config import load_config


def main() -> None:
    cfg = load_config()
    feeds = cfg.get("feeds", [])
    print(
        json.dumps(
            {"count": len(feeds), "feeds": feeds},
            indent=2,
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
