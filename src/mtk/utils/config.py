"""Helpers for loading the user configuration file (~/.mtk/config.json)."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

CONFIG_DIR = Path.home() / ".mtk"
CONFIG_FILE = CONFIG_DIR / "config.json"

# Backwards compatibility: the project was previously named "batuta".
# Fall back to the old config location if the new one is absent, so existing
# users keep their settings (e.g. apkeditor_path) after the rename.
LEGACY_CONFIG_FILE = Path.home() / ".batuta" / "config.json"


@lru_cache(maxsize=1)
def load_config() -> dict[str, Any]:
    """Load configuration data from disk (cached)."""

    config_file = CONFIG_FILE
    if not config_file.exists():
        if LEGACY_CONFIG_FILE.exists():
            config_file = LEGACY_CONFIG_FILE
        else:
            return {}

    try:
        raw = config_file.read_text()
    except OSError:
        return {}

    try:
        data = json.loads(raw)
    except ValueError:
        return {}

    if isinstance(data, dict):
        return data

    return {}


def get_config_value(key: str, default: Any | None = None) -> Any | None:
    """Fetch a configuration value by key."""

    return load_config().get(key, default)


def reload_config() -> None:
    """Force the cached configuration to be reloaded on next access."""

    load_config.cache_clear()
