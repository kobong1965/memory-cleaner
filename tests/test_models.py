from __future__ import annotations

import unittest

from memory_pilot.models import (
    BYTES_PER_MIB,
    MemoryReleaseResult,
    MemorySnapshot,
    ProcessStatus,
    ProcessView,
    ReleaseItemResult,
    ReleaseStatus,
)


class MemorySnapshotTests(unittest.TestCase):
    def test_calculates_usage_and_megabytes(self) -> None:
        snapshot = MemorySnapshot(
            total_bytes=16_000 * BYTES_PER_MIB,
            available_bytes=4_000 * BYTES_PER_MIB,
            timestamp=1.0,
        )

        self.assertEqual(snapshot.used_mb, 12_000)
        self.assertEqual(snapshot.available_mb, 4_000)
        self.assertAlmostEqual(snapshot.used_percent, 75.0)


class ProcessViewTests(unittest.TestCase):
    def test_formats_single_and_grouped_pid_labels(self) -> None:
        single = ProcessView("a", "App", (42,), 0, 0.0, ProcessStatus.USER_APP)
        grouped = ProcessView("b", "Browser", (1, 2, 3), 0, 0.0, ProcessStatus.USER_APP)

        self.assertEqual(single.pid_label, "42")
        self.assertEqual(grouped.pid_label, "3 个进程")


class MemoryReleaseResultTests(unittest.TestCase):
    def test_reports_counts_and_never_reports_negative_release(self) -> None:
        before = MemorySnapshot(1000, 500, 1.0)
        after = MemorySnapshot(1000, 450, 2.0)
        items = (
            ReleaseItemResult(1, "one", ReleaseStatus.PROCESSED, ""),
            ReleaseItemResult(2, "two", ReleaseStatus.SKIPPED, "protected"),
            ReleaseItemResult(3, "three", ReleaseStatus.FAILED, "denied"),
        )

        result = MemoryReleaseResult(before, after, 0.2, items)

        self.assertEqual(result.released_bytes, 0)
        self.assertEqual(result.processed_count, 1)
        self.assertEqual(result.skipped_count, 1)
        self.assertEqual(result.failed_count, 1)


if __name__ == "__main__":
    unittest.main()
