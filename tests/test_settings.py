from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from memory_pilot.core.deep_clean import DEFAULT_DEEP_CLEAN_MINUTES
from memory_pilot.core.settings import SettingsStore


class SettingsStoreTests(unittest.TestCase):
    def test_missing_or_invalid_settings_use_safe_default(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "settings.json"
            store = SettingsStore(path)
            self.assertEqual(store.load_deep_clean_minutes(), DEFAULT_DEEP_CLEAN_MINUTES)

            path.write_text("not json", encoding="utf-8")
            self.assertEqual(store.load_deep_clean_minutes(), DEFAULT_DEEP_CLEAN_MINUTES)

    def test_value_is_persisted_and_clamped_to_zero_through_sixty(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "settings.json"
            store = SettingsStore(path)

            self.assertEqual(store.save_deep_clean_minutes(-8), 0)
            self.assertEqual(store.load_deep_clean_minutes(), 0)
            self.assertEqual(store.save_deep_clean_minutes(75), 60)
            self.assertEqual(store.load_deep_clean_minutes(), 60)
            self.assertEqual(json.loads(path.read_text(encoding="utf-8"))["deep_clean_minutes"], 60)


if __name__ == "__main__":
    unittest.main()
