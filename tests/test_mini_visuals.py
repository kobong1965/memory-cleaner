from __future__ import annotations

import unittest

from memory_pilot.ui.qt_bridge import clamp_percent, format_gb


class MiniVisualHelperTests(unittest.TestCase):
    def test_clamps_memory_percentage(self) -> None:
        self.assertEqual(clamp_percent(-4.0), 0.0)
        self.assertEqual(clamp_percent(51.5), 51.5)
        self.assertEqual(clamp_percent(140.0), 100.0)

    def test_formats_binary_gigabytes_for_qml(self) -> None:
        self.assertEqual(format_gb(8 * 1024 * 1024 * 1024), "8.0 GB")


if __name__ == "__main__":
    unittest.main()
