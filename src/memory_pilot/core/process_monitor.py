from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Iterable, Protocol, Sequence

from memory_pilot.core.protection import classify_process, normalize_process_name
from memory_pilot.models import MemorySnapshot, ProcessSample, ProcessStatus, ProcessView


class ProcessApi(Protocol):
    def get_memory_snapshot(self) -> MemorySnapshot: ...

    def iter_process_samples(self) -> Iterable[ProcessSample]: ...


@dataclass(frozen=True, slots=True)
class MonitorSnapshot:
    memory: MemorySnapshot
    samples: tuple[ProcessSample, ...]
    views: tuple[ProcessView, ...]


class ProcessMonitor:
    def __init__(self, api: ProcessApi, processor_count: int | None = None) -> None:
        self._api = api
        self._processor_count = max(1, processor_count or os.cpu_count() or 1)
        self._previous_cpu: dict[int, int] = {}
        self._previous_timestamp: float | None = None

    def sample(self, grouped: bool = True) -> MonitorSnapshot:
        memory = self._api.get_memory_snapshot()
        samples = tuple(self._api.iter_process_samples())
        cpu_by_pid = self._calculate_cpu(samples, memory.timestamp)
        views = build_process_views(samples, cpu_by_pid, grouped, os.getpid())
        return MonitorSnapshot(memory, samples, views)

    def _calculate_cpu(
        self, samples: Sequence[ProcessSample], timestamp: float
    ) -> dict[int, float]:
        cpu_by_pid: dict[int, float] = {}
        if self._previous_timestamp is not None:
            elapsed = timestamp - self._previous_timestamp
            if elapsed > 0:
                for sample in samples:
                    previous = self._previous_cpu.get(sample.pid)
                    if previous is None:
                        continue
                    delta_100ns = sample.cpu_time_100ns - previous
                    if delta_100ns <= 0:
                        continue
                    cpu = (delta_100ns / 10_000_000) / elapsed / self._processor_count * 100
                    cpu_by_pid[sample.pid] = min(100.0, max(0.0, cpu))

        self._previous_cpu = {sample.pid: sample.cpu_time_100ns for sample in samples}
        self._previous_timestamp = timestamp
        return cpu_by_pid


def build_process_views(
    samples: Sequence[ProcessSample],
    cpu_by_pid: dict[int, float],
    grouped: bool,
    current_pid: int,
) -> tuple[ProcessView, ...]:
    if not grouped:
        return tuple(
            _view_from_group((sample,), cpu_by_pid, current_pid, f"pid:{sample.pid}")
            for sample in samples
        )

    groups: dict[str, list[ProcessSample]] = {}
    for sample in samples:
        key = normalize_process_name(sample.name) or f"pid-{sample.pid}"
        groups.setdefault(key, []).append(sample)

    return tuple(
        _view_from_group(tuple(group), cpu_by_pid, current_pid, f"group:{key}")
        for key, group in groups.items()
    )


def _view_from_group(
    samples: tuple[ProcessSample, ...],
    cpu_by_pid: dict[int, float],
    current_pid: int,
    key: str,
) -> ProcessView:
    statuses = tuple(classify_process(sample, current_pid) for sample in samples)
    if ProcessStatus.PROTECTED in statuses:
        status = ProcessStatus.PROTECTED
    elif all(item == ProcessStatus.RESTRICTED for item in statuses):
        status = ProcessStatus.RESTRICTED
    elif ProcessStatus.SYSTEM in statuses:
        status = ProcessStatus.SYSTEM
    else:
        status = ProcessStatus.USER_APP

    paths = sorted({sample.executable_path for sample in samples if sample.executable_path})
    display_name = samples[0].name[:-4] if samples[0].name.casefold().endswith(".exe") else samples[0].name
    return ProcessView(
        key=key,
        name=display_name,
        pids=tuple(sorted(sample.pid for sample in samples)),
        memory_bytes=sum(sample.working_set_bytes for sample in samples),
        cpu_percent=sum(cpu_by_pid.get(sample.pid, 0.0) for sample in samples),
        status=status,
        executable_path=paths[0] if paths else "",
    )


def filter_and_sort_views(
    views: Sequence[ProcessView],
    query: str,
    sort_key: str,
    descending: bool,
) -> tuple[ProcessView, ...]:
    needle = query.strip().casefold()
    filtered = tuple(
        view
        for view in views
        if not needle
        or needle in view.name.casefold()
        or any(needle in str(pid) for pid in view.pids)
        or needle in view.executable_path.casefold()
    )

    key_functions = {
        "name": lambda view: view.name.casefold(),
        "pid": lambda view: view.pids[0] if view.pids else 0,
        "status": lambda view: view.status.value,
        "cpu": lambda view: view.cpu_percent,
        "memory": lambda view: view.memory_bytes,
        "path": lambda view: view.executable_path.casefold(),
    }
    selected = key_functions.get(sort_key, key_functions["memory"])
    return tuple(sorted(filtered, key=selected, reverse=descending))
