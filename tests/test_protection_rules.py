from __future__ import annotations

import unittest

from memory_pilot.core.protection import classify_process, protection_reason
from memory_pilot.models import ProcessSample, ProcessStatus


class ProtectionRuleTests(unittest.TestCase):
    def test_current_process_is_protected(self) -> None:
        sample = ProcessSample(123, "MemoryPilot.exe", 100, 0)

        self.assertEqual(classify_process(sample, current_pid=123), ProcessStatus.PROTECTED)
        self.assertIn("本程序", protection_reason(sample, current_pid=123) or "")

    def test_critical_windows_process_is_protected(self) -> None:
        sample = ProcessSample(500, "lsass.exe", 100, 0, r"C:\Windows\System32\lsass.exe")

        self.assertEqual(classify_process(sample, current_pid=123), ProcessStatus.PROTECTED)

    def test_inaccessible_noncritical_process_is_restricted(self) -> None:
        sample = ProcessSample(501, "vendor.exe", 0, 0, accessible=False, error="denied")

        self.assertEqual(classify_process(sample, current_pid=123), ProcessStatus.RESTRICTED)

    def test_regular_program_is_user_application(self) -> None:
        sample = ProcessSample(700, "editor.exe", 100, 0, r"D:\Apps\editor.exe")

        self.assertEqual(classify_process(sample, current_pid=123), ProcessStatus.USER_APP)


if __name__ == "__main__":
    unittest.main()

