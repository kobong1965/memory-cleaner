from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum

BYTES_PER_MIB = 1024 * 1024


class ProcessStatus(StrEnum):
    USER_APP = "用户应用"
    SYSTEM = "系统进程"
    PROTECTED = "受保护"
    RESTRICTED = "访问受限"


class ReleaseStatus(StrEnum):
    PROCESSED = "已处理"
    SKIPPED = "已跳过"
    FAILED = "失败"


@dataclass(frozen=True, slots=True)
class MemorySnapshot:
    total_bytes: int
    available_bytes: int
    timestamp: float

    @property
    def used_bytes(self) -> int:
        return max(0, self.total_bytes - self.available_bytes)

    @property
    def used_percent(self) -> float:
        if self.total_bytes <= 0:
            return 0.0
        return min(100.0, max(0.0, self.used_bytes / self.total_bytes * 100.0))

    @property
    def total_mb(self) -> int:
        return round(self.total_bytes / BYTES_PER_MIB)

    @property
    def available_mb(self) -> int:
        return round(self.available_bytes / BYTES_PER_MIB)

    @property
    def used_mb(self) -> int:
        return round(self.used_bytes / BYTES_PER_MIB)


@dataclass(frozen=True, slots=True)
class ProcessSample:
    pid: int
    name: str
    working_set_bytes: int
    cpu_time_100ns: int
    executable_path: str = ""
    accessible: bool = True
    error: str = ""
    session_id: int = -1


@dataclass(frozen=True, slots=True)
class ProcessView:
    key: str
    name: str
    pids: tuple[int, ...]
    memory_bytes: int
    cpu_percent: float
    status: ProcessStatus
    executable_path: str = ""

    @property
    def count(self) -> int:
        return len(self.pids)

    @property
    def memory_mb(self) -> float:
        return self.memory_bytes / BYTES_PER_MIB

    @property
    def pid_label(self) -> str:
        if self.count == 1:
            return str(self.pids[0])
        return f"{self.count} 个进程"


@dataclass(frozen=True, slots=True)
class ReleaseItemResult:
    pid: int
    name: str
    status: ReleaseStatus
    reason: str
    working_set_bytes: int = 0


@dataclass(frozen=True, slots=True)
class MemoryReleaseResult:
    before: MemorySnapshot
    after: MemorySnapshot
    duration_seconds: float
    items: tuple[ReleaseItemResult, ...] = field(default_factory=tuple)

    @property
    def released_bytes(self) -> int:
        return max(0, self.after.available_bytes - self.before.available_bytes)

    @property
    def released_mb(self) -> int:
        return round(self.released_bytes / BYTES_PER_MIB)

    @property
    def processed_count(self) -> int:
        return sum(item.status == ReleaseStatus.PROCESSED for item in self.items)

    @property
    def skipped_count(self) -> int:
        return sum(item.status == ReleaseStatus.SKIPPED for item in self.items)

    @property
    def failed_count(self) -> int:
        return sum(item.status == ReleaseStatus.FAILED for item in self.items)
