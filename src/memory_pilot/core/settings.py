from __future__ import annotations

import json
import os
from pathlib import Path

from memory_pilot.core.deep_clean import (
    DEFAULT_DEEP_CLEAN_MINUTES,
    clamp_deep_clean_minutes,
)


def default_settings_path() -> Path:
    local_app_data = os.environ.get("LOCALAPPDATA")
    if local_app_data:
        return Path(local_app_data) / "MemoryPilot" / "settings.json"
    return Path.home() / "AppData" / "Local" / "MemoryPilot" / "settings.json"


class SettingsStore:
    def __init__(self, path: Path | None = None) -> None:
        self.path = path or default_settings_path()

    def load_deep_clean_minutes(self) -> int:
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
            value = int(payload.get("deep_clean_minutes", DEFAULT_DEEP_CLEAN_MINUTES))
        except (OSError, ValueError, TypeError):
            return DEFAULT_DEEP_CLEAN_MINUTES
        return clamp_deep_clean_minutes(value)

    def save_deep_clean_minutes(self, minutes: int) -> int:
        value = clamp_deep_clean_minutes(minutes)
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            temporary = self.path.with_suffix(".tmp")
            temporary.write_text(
                json.dumps({"deep_clean_minutes": value}, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            temporary.replace(self.path)
        except OSError:
            pass
        return value
