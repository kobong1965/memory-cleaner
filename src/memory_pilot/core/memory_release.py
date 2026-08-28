from __future__ import annotations

import os
import time
from typing import Protocol, Sequence

from memory_pilot.core.protection import classify_process, protection_reason
from memory_pilot.models import (
    BYTES_PER_MIB,
    MemoryReleaseResult,
    MemorySnapshot,
    ProcessSample,
    ProcessStatus,
    ReleaseItemResult,
    ReleaseStatus,
)

MINIMUM_WORKING_SET_BYTES = 16 * BYTES_PER_MIB


class MemoryApi(Protocol):
    def get_memory_snapshot(self) -> MemorySnapshot: ...

    def trim_working_set(self, pid: int) -> None: ...


class MemoryReleaseService:
    def __init__(
        self,
        api: MemoryApi,
        current_pid: int | None = None,
        settle_seconds: float = 0.25,
    ) -> None:
        self._api = api
        self._current_pid = current_pid or os.getpid()
        self._settle_seconds = max(0.0, settle_seconds)

    def release(self, samples: Sequence[ProcessSample]) -> MemoryReleaseResult:
        before = self._api.get_memory_snapshot()
        started = time.monotonic()
        results: list[ReleaseItemResult] = []

        for sample in sorted(samples, key=lambda item: item.working_set_bytes, reverse=True):
            skip_reason = self._skip_reason(sample)
            if skip_reason:
                results.append(
                    ReleaseItemResult(
                        sample.pid,
                        sample.name,
                        ReleaseStatus.SKIPPED,
                        skip_reason,
                        sample.working_set_bytes,
                    )
                )
                continue

            try:
                self._api.trim_working_set(sample.pid)
            except (OSError, RuntimeError) as exc:
                results.append(
                    ReleaseItemResult(
                        sample.pid,
                        sample.name,
                        ReleaseStatus.FAILED,
                        str(exc),
                        sample.working_set_bytes,
                    )
                )
            else:
                results.append(
                    ReleaseItemResult(
                        sample.pid,
                        sample.name,
                        ReleaseStatus.PROCESSED,
                        "已安全修剪闲置工作集",
                        sample.working_set_bytes,
                    )
                )

        if self._settle_seconds:
            time.sleep(self._settle_seconds)
        after = self._api.get_memory_snapshot()
        return MemoryReleaseResult(
            before=before,
            after=after,
            duration_seconds=time.monotonic() - started,
            items=tuple(results),
        )

    def _skip_reason(self, sample: ProcessSample) -> str | None:
        protected = protection_reason(sample, self._current_pid)
        if protected:
            return protected

        status = classify_process(sample, self._current_pid)
        if status == ProcessStatus.SYSTEM:
            return "Windows 系统进程"
        if status == ProcessStatus.RESTRICTED:
            return sample.error or "访问受限"
        if sample.working_set_bytes < MINIMUM_WORKING_SET_BYTES:
            return "内存占用低于 16 MB"
        return None
