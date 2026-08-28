from __future__ import annotations

import os

from memory_pilot.models import ProcessSample, ProcessStatus

CRITICAL_PROCESS_NAMES = frozenset(
    {
        "system idle process",
        "system",
        "registry",
        "memory compression",
        "secure system",
        "smss",
        "csrss",
        "wininit",
        "services",
        "lsass",
        "winlogon",
        "svchost",
        "fontdrvhost",
        "dwm",
        "explorer",
        "sihost",
        "taskhostw",
        "runtimebroker",
        "startmenuexperiencehost",
        "shellexperiencehost",
        "shellhost",
        "searchhost",
        "searchindexer",
        "textinputhost",
        "ctfmon",
        "msmpeng",
        "securityhealthservice",
        "securityhealthsystray",
        "audiodg",
        "spoolsv",
        "wmiprvse",
    }
)


def normalize_process_name(name: str) -> str:
    normalized = name.strip().casefold()
    return normalized[:-4] if normalized.endswith(".exe") else normalized


def protection_reason(sample: ProcessSample, current_pid: int) -> str | None:
    normalized = normalize_process_name(sample.name)
    if sample.pid == current_pid:
        return "本程序正在执行清理"
    if sample.pid in (0, 4):
        return "Windows 核心进程"
    if normalized in CRITICAL_PROCESS_NAMES:
        return "Windows 核心或桌面进程"
    return None


def classify_process(sample: ProcessSample, current_pid: int) -> ProcessStatus:
    if protection_reason(sample, current_pid):
        return ProcessStatus.PROTECTED
    if not sample.accessible:
        return ProcessStatus.RESTRICTED
    if sample.session_id == 0:
        return ProcessStatus.SYSTEM

    system_root = os.environ.get("SystemRoot", r"C:\Windows").rstrip("\\/").casefold()
    if sample.executable_path.casefold().startswith(system_root + "\\"):
        return ProcessStatus.SYSTEM
    return ProcessStatus.USER_APP
