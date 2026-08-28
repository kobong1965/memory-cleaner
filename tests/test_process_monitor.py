from __future__ import annotations

import unittest

from memory_pilot.core.process_monitor import ProcessMonitor, build_process_views, filter_and_sort_views
from memory_pilot.models import MemorySnapshot, ProcessSample, ProcessStatus


class FakeProcessApi:
    def __init__(self) -> None:
        self.tick = 0

    def get_memory_snapshot(self) -> MemorySnapshot:
        self.tick += 1
        return MemorySnapshot(1_000, 500, float(self.tick))

    def iter_process_samples(self):
        cpu_time = 0 if self.tick == 1 else 10_000_000
        return (ProcessSample(10, "App.exe", 100, cpu_time),)


class ProcessViewBuilderTests(unittest.TestCase):
    def test_monitor_calculates_cpu_delta_across_logical_processors(self) -> None:
        monitor = ProcessMonitor(FakeProcessApi(), processor_count=4)

        first = monitor.sample(grouped=False)
        second = monitor.sample(grouped=False)

        self.assertEqual(first.views[0].cpu_percent, 0.0)
        self.assertAlmostEqual(second.views[0].cpu_percent, 25.0)

    def test_groups_same_name_and_sums_resources(self) -> None:
        samples = (
            ProcessSample(10, "Browser.exe", 100, 100),
            ProcessSample(11, "browser.exe", 250, 200),
        )

        views = build_process_views(
            samples,
            cpu_by_pid={10: 1.25, 11: 2.75},
            grouped=True,
            current_pid=999,
        )

        self.assertEqual(len(views), 1)
        self.assertEqual(views[0].memory_bytes, 350)
        self.assertEqual(views[0].cpu_percent, 4.0)
        self.assertEqual(views[0].pids, (10, 11))
        self.assertEqual(views[0].status, ProcessStatus.USER_APP)

    def test_pid_view_keeps_processes_separate(self) -> None:
        samples = (
            ProcessSample(10, "App.exe", 100, 100),
            ProcessSample(11, "App.exe", 200, 200),
        )

        views = build_process_views(samples, {}, grouped=False, current_pid=999)

        self.assertEqual(len(views), 2)
        self.assertEqual({view.key for view in views}, {"pid:10", "pid:11"})

    def test_filters_by_name_or_pid_and_sorts_memory(self) -> None:
        samples = (
            ProcessSample(10, "Alpha.exe", 100, 100),
            ProcessSample(20, "Beta.exe", 500, 200),
        )
        views = build_process_views(samples, {}, grouped=False, current_pid=999)

        by_name = filter_and_sort_views(views, "alp", "memory", descending=True)
        by_pid = filter_and_sort_views(views, "20", "memory", descending=True)
        all_rows = filter_and_sort_views(views, "", "memory", descending=True)

        self.assertEqual([view.name for view in by_name], ["Alpha"])
        self.assertEqual([view.name for view in by_pid], ["Beta"])
        self.assertEqual([view.name for view in all_rows], ["Beta", "Alpha"])


if __name__ == "__main__":
    unittest.main()
