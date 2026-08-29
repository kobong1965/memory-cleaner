from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys
from typing import Callable, Mapping, Sequence

from memory_pilot.ui.windowing import named_mutex_exists, signal_named_event

MINI_MUTEX_NAME = "Local\\MemoryPilotMini.Singleton"
MINI_STOP_EVENT_NAME = "Local\\MemoryPilotMini.Stop"


def mini_mode_command(
    *,
    frozen: bool | None = None,
    executable: str | None = None,
) -> tuple[list[str], Path]:
    is_frozen = getattr(sys, "frozen", False) if frozen is None else frozen
    interpreter = executable or sys.executable
    if is_frozen:
        target = Path(interpreter)
        return [str(target), "--mini"], target.parent
    return [interpreter, "-m", "memory_pilot", "--mini"], Path.cwd()


def mini_mode_environment() -> dict[str, str]:
    environment = os.environ.copy()
    environment["PYINSTALLER_RESET_ENVIRONMENT"] = "1"
    return environment


class MiniModeManager:
    def __init__(
        self,
        launcher: Callable[..., object] = subprocess.Popen,
        command_factory: Callable[[], tuple[Sequence[str], Path]] = mini_mode_command,
        environment_factory: Callable[[], Mapping[str, str]] = mini_mode_environment,
        running_probe: Callable[[str], bool] = named_mutex_exists,
        stop_signal: Callable[[str], bool] = signal_named_event,
    ) -> None:
        self._launcher = launcher
        self._command_factory = command_factory
        self._environment_factory = environment_factory
        self._running_probe = running_probe
        self._stop_signal = stop_signal

    def is_running(self) -> bool:
        return self._running_probe(MINI_MUTEX_NAME)

    def start(self) -> None:
        if self.is_running():
            return
        command, working_directory = self._command_factory()
        self._launcher(
            list(command),
            cwd=working_directory,
            env=dict(self._environment_factory()),
        )

    def request_stop(self) -> bool:
        if not self.is_running():
            return True
        return self._stop_signal(MINI_STOP_EVENT_NAME)
