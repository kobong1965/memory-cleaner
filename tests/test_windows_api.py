from __future__ import annotations

import os
import unittest

from memory_pilot.platform.windows_api import WindowsApi


@unittest.skipUnless(os.name == "nt", "Windows API tests require Windows")
class WindowsApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.api = WindowsApi()

    def test_reads_physical_memory_snapshot(self) -> None:
        snapshot = self.api.get_memory_snapshot()

        self.assertGreater(snapshot.total_bytes, 0)
        self.assertGreater(snapshot.available_bytes, 0)
        self.assertLessEqual(snapshot.available_bytes, snapshot.total_bytes)

    def test_enumerates_current_process(self) -> None:
        samples = tuple(self.api.iter_process_samples())
        current = next((sample for sample in samples if sample.pid == os.getpid()), None)

        self.assertIsNotNone(current)
        assert current is not None
        self.assertTrue(current.accessible)
        self.assertGreater(current.working_set_bytes, 0)
        self.assertGreaterEqual(current.cpu_time_100ns, 0)

    def test_current_process_is_elevated_returns_boolean(self) -> None:
        self.assertIsInstance(self.api.is_current_process_elevated(), bool)

    def test_reads_foreground_pid_and_visible_application_windows(self) -> None:
        foreground_pid = self.api.get_foreground_process_id()
        windows = self.api.get_visible_app_windows()

        self.assertGreaterEqual(foreground_pid, 0)
        self.assertIsInstance(windows, tuple)
        for window in windows:
            self.assertGreater(window.handle, 0)
            self.assertGreater(window.pid, 0)
            self.assertTrue(window.title)


if __name__ == "__main__":
    unittest.main()
