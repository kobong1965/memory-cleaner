from __future__ import annotations

from pathlib import Path
import unittest

from memory_pilot.ui.mini_mode import (
    MINI_MUTEX_NAME,
    MINI_STOP_EVENT_NAME,
    MiniModeManager,
    mini_mode_command,
    mini_mode_environment,
)


class MiniModeCommandTests(unittest.TestCase):
    def test_frozen_command_reuses_the_main_executable(self) -> None:
        command, working_directory = mini_mode_command(
            frozen=True,
            executable=r"E:\Software\MemoryPilot.exe",
        )

        self.assertEqual(command, [r"E:\Software\MemoryPilot.exe", "--mini"])
        self.assertEqual(working_directory, Path(r"E:\Software"))

    def test_source_command_uses_the_package_entrypoint(self) -> None:
        command, _working_directory = mini_mode_command(
            frozen=False,
            executable=r"C:\Python\python.exe",
        )

        self.assertEqual(
            command,
            [r"C:\Python\python.exe", "-m", "memory_pilot", "--mini"],
        )

    def test_child_process_gets_an_independent_pyinstaller_environment(self) -> None:
        environment = mini_mode_environment()

        self.assertEqual(environment["PYINSTALLER_RESET_ENVIRONMENT"], "1")


class MiniModeManagerTests(unittest.TestCase):
    def test_starts_only_when_not_already_running(self) -> None:
        launches: list[tuple[list[str], Path, dict[str, str]]] = []
        running = False

        def launch(command: list[str], *, cwd: Path, env: dict[str, str]) -> None:
            launches.append((command, cwd, env))

        manager = MiniModeManager(
            launcher=launch,
            command_factory=lambda: (["MemoryPilot.exe", "--mini"], Path("E:/App")),
            environment_factory=lambda: {"PYINSTALLER_RESET_ENVIRONMENT": "1"},
            running_probe=lambda name: running and name == MINI_MUTEX_NAME,
        )

        manager.start()
        self.assertEqual(
            launches,
            [
                (
                    ["MemoryPilot.exe", "--mini"],
                    Path("E:/App"),
                    {"PYINSTALLER_RESET_ENVIRONMENT": "1"},
                )
            ],
        )

        running = True
        manager.start()
        self.assertEqual(len(launches), 1)

    def test_stop_uses_named_event_and_missing_process_is_already_stopped(self) -> None:
        signaled: list[str] = []
        running = True

        def signal(name: str) -> bool:
            signaled.append(name)
            return True

        manager = MiniModeManager(
            running_probe=lambda _name: running,
            stop_signal=signal,
        )

        self.assertTrue(manager.request_stop())
        self.assertEqual(signaled, [MINI_STOP_EVENT_NAME])

        running = False
        self.assertTrue(manager.request_stop())
        self.assertEqual(len(signaled), 1)


if __name__ == "__main__":
    unittest.main()
