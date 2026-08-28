from __future__ import annotations

import unittest

from memory_pilot.core.memory_release import MemoryReleaseService
from memory_pilot.models import BYTES_PER_MIB, MemorySnapshot, ProcessSample, ReleaseStatus


class FakeMemoryApi:
    def __init__(self) -> None:
        self.snapshots = [
            MemorySnapshot(1_000 * BYTES_PER_MIB, 200 * BYTES_PER_MIB, 1.0),
            MemorySnapshot(1_000 * BYTES_PER_MIB, 260 * BYTES_PER_MIB, 2.0),
        ]
        self.trim_calls: list[int] = []

    def get_memory_snapshot(self) -> MemorySnapshot:
        return self.snapshots.pop(0)

    def trim_working_set(self, pid: int) -> None:
        self.trim_calls.append(pid)
        if pid == 77:
            raise RuntimeError("access denied")


class MemoryReleaseServiceTests(unittest.TestCase):
    def test_only_trims_eligible_user_processes(self) -> None:
        api = FakeMemoryApi()
        samples = (
            ProcessSample(10, "MemoryPilot.exe", 100 * BYTES_PER_MIB, 0),
            ProcessSample(20, "lsass.exe", 100 * BYTES_PER_MIB, 0),
            ProcessSample(30, "system-tool.exe", 100 * BYTES_PER_MIB, 0, r"C:\Windows\tool.exe"),
            ProcessSample(40, "locked.exe", 100 * BYTES_PER_MIB, 0, accessible=False),
            ProcessSample(50, "tiny.exe", 2 * BYTES_PER_MIB, 0),
            ProcessSample(60, "editor.exe", 200 * BYTES_PER_MIB, 0, r"D:\Apps\editor.exe"),
            ProcessSample(77, "browser.exe", 150 * BYTES_PER_MIB, 0, r"D:\Apps\browser.exe"),
        )
        service = MemoryReleaseService(api, current_pid=10, settle_seconds=0)

        result = service.release(samples)

        self.assertEqual(api.trim_calls, [60, 77])
        self.assertEqual(result.released_mb, 60)
        self.assertEqual(result.processed_count, 1)
        self.assertEqual(result.failed_count, 1)
        self.assertEqual(result.skipped_count, 5)
        failed = next(item for item in result.items if item.status == ReleaseStatus.FAILED)
        self.assertEqual(failed.pid, 77)

    def test_empty_input_still_returns_measured_result(self) -> None:
        api = FakeMemoryApi()
        service = MemoryReleaseService(api, current_pid=10, settle_seconds=0)

        result = service.release(())

        self.assertEqual(result.processed_count, 0)
        self.assertEqual(result.released_mb, 60)


if __name__ == "__main__":
    unittest.main()
