from __future__ import annotations

import os
import threading
import time
from collections import defaultdict
from typing import Callable, Mapping, Protocol, Sequence

from memory_pilot.core.protection import classify_process, normalize_process_name
from memory_pilot.models import (
    AppWindowInfo,
    DeepCleanCandidate,
    DeepCleanItemResult,
    DeepCleanPlan,
    DeepCleanResult,
    ProcessSample,
    ProcessStatus,
)

MIN_DEEP_CLEAN_MINUTES = 0
MAX_DEEP_CLEAN_MINUTES = 60
DEFAULT_DEEP_CLEAN_MINUTES = 60
SELF_PROCESS_NAMES = frozenset({"memorypilot", "memorypilotmini"})


def clamp_deep_clean_minutes(value: int) -> int:
    return min(MAX_DEEP_CLEAN_MINUTES, max(MIN_DEEP_CLEAN_MINUTES, int(value)))


class DeepCleanApi(Protocol):
    def get_visible_app_windows(self) -> tuple[AppWindowInfo, ...]: ...

    def get_foreground_process_id(self) -> int: ...

    def post_close_window(self, window_handle: int) -> None: ...


class AppUsageTracker:
    """Tracks foreground use observed during the current application run only."""

    def __init__(self, clock: Callable[[], float] = time.monotonic) -> None:
        self._clock = clock
        self._last_used: dict[int, float] = {}
        self._lock = threading.Lock()

    def observe(
        self,
        windows: Sequence[AppWindowInfo],
        foreground_pid: int,
        *,
        now: float | None = None,
    ) -> None:
        observed_at = self._clock() if now is None else float(now)
        visible_pids = {window.pid for window in windows if window.pid > 0}
        with self._lock:
            self._last_used = {
                pid: self._last_used.get(pid, observed_at)
                for pid in visible_pids
            }
            if foreground_pid in visible_pids:
                self._last_used[foreground_pid] = observed_at

    def snapshot(self) -> dict[int, float]:
        with self._lock:
            return dict(self._last_used)


class DeepCleanService:
    def __init__(
        self,
        api: DeepCleanApi,
        current_pid: int | None = None,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._api = api
        self._current_pid = current_pid or os.getpid()
        self._clock = clock

    def observe_usage(self, tracker: AppUsageTracker) -> None:
        windows = self._api.get_visible_app_windows()
        foreground_pid = self._api.get_foreground_process_id()
        tracker.observe(windows, foreground_pid)

    def preview(
        self,
        samples: Sequence[ProcessSample],
        tracker: AppUsageTracker,
        threshold_minutes: int,
    ) -> DeepCleanPlan:
        threshold = clamp_deep_clean_minutes(threshold_minutes)
        now = self._clock()
        windows = self._api.get_visible_app_windows()
        foreground_pid = self._api.get_foreground_process_id()
        tracker.observe(windows, foreground_pid, now=now)
        return self._build_plan(
            samples,
            windows,
            tracker.snapshot(),
            foreground_pid,
            threshold,
            now,
        )

    def execute(
        self,
        preview: DeepCleanPlan,
        samples: Sequence[ProcessSample],
        tracker: AppUsageTracker,
    ) -> DeepCleanResult:
        fresh = self.preview(samples, tracker, preview.threshold_minutes)
        fresh_by_pid = {candidate.pid: candidate for candidate in fresh.candidates}
        results: list[DeepCleanItemResult] = []

        for preview_candidate in preview.candidates:
            candidate = fresh_by_pid.get(preview_candidate.pid)
            if (
                candidate is None
                or candidate.name.casefold() != preview_candidate.name.casefold()
                or candidate.executable_path.casefold()
                != preview_candidate.executable_path.casefold()
            ):
                results.append(
                    DeepCleanItemResult(
                        pid=preview_candidate.pid,
                        name=preview_candidate.name,
                        requested_window_count=0,
                        failed_window_count=0,
                        reason="预览后被再次使用、已关闭或不再符合保护条件",
                    )
                )
                continue

            preview_windows = {window.handle for window in preview_candidate.windows}
            confirmed_windows = tuple(
                window
                for window in candidate.windows
                if window.handle in preview_windows
            )
            if not confirmed_windows:
                results.append(
                    DeepCleanItemResult(
                        pid=preview_candidate.pid,
                        name=preview_candidate.name,
                        requested_window_count=0,
                        failed_window_count=0,
                        reason="预览中的窗口已关闭或被替换",
                    )
                )
                continue

            requested = 0
            failed = 0
            for window in confirmed_windows:
                try:
                    self._api.post_close_window(window.handle)
                except (OSError, RuntimeError):
                    failed += 1
                else:
                    requested += 1

            if requested and failed:
                reason = "部分窗口已发送正常关闭请求"
            elif requested:
                reason = "已发送正常关闭请求"
            else:
                reason = "无法发送正常关闭请求"
            results.append(
                DeepCleanItemResult(
                    pid=candidate.pid,
                    name=candidate.name,
                    requested_window_count=requested,
                    failed_window_count=failed,
                    reason=reason,
                )
            )

        return DeepCleanResult(
            threshold_minutes=preview.threshold_minutes,
            preview_count=len(preview.candidates),
            items=tuple(results),
        )

    def _build_plan(
        self,
        samples: Sequence[ProcessSample],
        windows: Sequence[AppWindowInfo],
        last_used: Mapping[int, float],
        foreground_pid: int,
        threshold_minutes: int,
        now: float,
    ) -> DeepCleanPlan:
        samples_by_pid = {sample.pid: sample for sample in samples}
        windows_by_pid: dict[int, list[AppWindowInfo]] = defaultdict(list)
        for window in windows:
            windows_by_pid[window.pid].append(window)

        threshold_seconds = threshold_minutes * 60.0
        candidates: list[DeepCleanCandidate] = []
        for pid, app_windows in windows_by_pid.items():
            if pid == foreground_pid:
                continue
            sample = samples_by_pid.get(pid)
            if sample is None or classify_process(sample, self._current_pid) != ProcessStatus.USER_APP:
                continue
            if normalize_process_name(sample.name) in SELF_PROCESS_NAMES:
                continue
            last_used_at = last_used.get(pid, now)
            idle_seconds = max(0.0, now - last_used_at)
            if idle_seconds < threshold_seconds:
                continue
            candidates.append(
                DeepCleanCandidate(
                    pid=pid,
                    name=sample.name,
                    executable_path=sample.executable_path,
                    idle_seconds=idle_seconds,
                    windows=tuple(app_windows),
                )
            )

        candidates.sort(key=lambda candidate: (-candidate.idle_seconds, candidate.name.casefold()))
        return DeepCleanPlan(
            threshold_minutes=threshold_minutes,
            created_at=now,
            candidates=tuple(candidates),
        )
