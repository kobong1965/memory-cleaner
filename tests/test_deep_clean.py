from __future__ import annotations

import unittest

from memory_pilot.core.deep_clean import AppUsageTracker, DeepCleanService
from memory_pilot.models import AppWindowInfo, ProcessSample


class ManualClock:
    def __init__(self, value: float = 0.0) -> None:
        self.value = value

    def __call__(self) -> float:
        return self.value


class FakeDeepCleanApi:
    def __init__(self) -> None:
        self.windows: tuple[AppWindowInfo, ...] = ()
        self.foreground_pid = 0
        self.closed_handles: list[int] = []
        self.failing_handles: set[int] = set()

    def get_visible_app_windows(self) -> tuple[AppWindowInfo, ...]:
        return self.windows

    def get_foreground_process_id(self) -> int:
        return self.foreground_pid

    def post_close_window(self, window_handle: int) -> None:
        if window_handle in self.failing_handles:
            raise OSError("close denied")
        self.closed_handles.append(window_handle)


def user_sample(pid: int, name: str) -> ProcessSample:
    return ProcessSample(
        pid=pid,
        name=name,
        working_set_bytes=100,
        cpu_time_100ns=0,
        executable_path=rf"C:\Apps\{name}.exe",
        accessible=True,
        session_id=1,
    )


class AppUsageTrackerTests(unittest.TestCase):
    def test_new_windows_start_from_safe_current_time_baseline(self) -> None:
        clock = ManualClock(100.0)
        tracker = AppUsageTracker(clock)
        windows = (
            AppWindowInfo(1, 10, "App A"),
            AppWindowInfo(2, 20, "App B"),
        )

        tracker.observe(windows, foreground_pid=10)

        self.assertEqual(tracker.snapshot(), {10: 100.0, 20: 100.0})

    def test_foreground_use_refreshes_only_the_active_program(self) -> None:
        clock = ManualClock(0.0)
        tracker = AppUsageTracker(clock)
        windows = (AppWindowInfo(1, 10, "A"), AppWindowInfo(2, 20, "B"))
        tracker.observe(windows, foreground_pid=10)
        clock.value = 30.0

        tracker.observe(windows, foreground_pid=20)

        self.assertEqual(tracker.snapshot(), {10: 0.0, 20: 30.0})


class DeepCleanServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.clock = ManualClock(0.0)
        self.api = FakeDeepCleanApi()
        self.tracker = AppUsageTracker(self.clock)
        self.service = DeepCleanService(self.api, current_pid=99, clock=self.clock)

    def test_sixty_minutes_selects_only_idle_user_apps(self) -> None:
        self.api.windows = (
            AppWindowInfo(1, 10, "Active"),
            AppWindowInfo(2, 20, "Idle"),
            AppWindowInfo(3, 30, "System"),
            AppWindowInfo(4, 99, "Memory Pilot"),
        )
        self.api.foreground_pid = 10
        self.service.observe_usage(self.tracker)
        self.clock.value = 3_600.0
        system_sample = ProcessSample(
            pid=30,
            name="Windows tool",
            working_set_bytes=100,
            cpu_time_100ns=0,
            executable_path=r"C:\Windows\System32\tool.exe",
            accessible=True,
            session_id=1,
        )

        plan = self.service.preview(
            (user_sample(10, "Active"), user_sample(20, "Idle"), system_sample, user_sample(99, "MemoryPilot")),
            self.tracker,
            60,
        )

        self.assertEqual([candidate.pid for candidate in plan.candidates], [20])
        self.assertEqual(plan.candidates[0].idle_minutes, 60)

    def test_zero_minutes_includes_nonforeground_user_apps(self) -> None:
        self.api.windows = (
            AppWindowInfo(1, 10, "Active"),
            AppWindowInfo(2, 20, "Idle"),
        )
        self.api.foreground_pid = 10

        plan = self.service.preview(
            (user_sample(10, "Active"), user_sample(20, "Idle")),
            self.tracker,
            0,
        )

        self.assertEqual([candidate.pid for candidate in plan.candidates], [20])

    def test_program_reactivated_after_preview_is_skipped(self) -> None:
        self.api.windows = (AppWindowInfo(2, 20, "Idle"),)
        self.api.foreground_pid = 0
        preview = self.service.preview((user_sample(20, "Idle"),), self.tracker, 0)
        self.clock.value = 1.0
        self.api.foreground_pid = 20

        result = self.service.execute(preview, (user_sample(20, "Idle"),), self.tracker)

        self.assertEqual(result.requested_count, 0)
        self.assertEqual(result.skipped_count, 1)
        self.assertEqual(self.api.closed_handles, [])

    def test_execute_only_closes_programs_shown_in_preview(self) -> None:
        self.api.windows = (AppWindowInfo(2, 20, "Previewed"),)
        preview = self.service.preview((user_sample(20, "Previewed"),), self.tracker, 0)
        self.api.windows = (
            AppWindowInfo(2, 20, "Previewed"),
            AppWindowInfo(3, 30, "New candidate"),
        )

        result = self.service.execute(
            preview,
            (user_sample(20, "Previewed"), user_sample(30, "New")),
            self.tracker,
        )

        self.assertEqual(result.requested_count, 1)
        self.assertEqual(self.api.closed_handles, [2])

    def test_reused_pid_or_replaced_window_is_not_closed(self) -> None:
        self.api.windows = (AppWindowInfo(2, 20, "Previewed"),)
        preview = self.service.preview((user_sample(20, "Previewed"),), self.tracker, 0)
        self.api.windows = (AppWindowInfo(9, 20, "Replacement"),)
        replacement = ProcessSample(
            pid=20,
            name="Different",
            working_set_bytes=100,
            cpu_time_100ns=0,
            executable_path=r"C:\Other\Different.exe",
            accessible=True,
            session_id=1,
        )

        result = self.service.execute(preview, (replacement,), self.tracker)

        self.assertEqual(result.requested_count, 0)
        self.assertEqual(result.skipped_count, 1)
        self.assertEqual(self.api.closed_handles, [])

    def test_close_request_failures_are_reported(self) -> None:
        self.api.windows = (AppWindowInfo(2, 20, "Idle"),)
        self.api.failing_handles = {2}
        preview = self.service.preview((user_sample(20, "Idle"),), self.tracker, 0)

        result = self.service.execute(preview, (user_sample(20, "Idle"),), self.tracker)

        self.assertEqual(result.requested_count, 0)
        self.assertEqual(result.failed_count, 1)


if __name__ == "__main__":
    unittest.main()
