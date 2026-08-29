from __future__ import annotations

import unittest

from PySide6.QtCore import QCoreApplication

from memory_pilot.models import BYTES_PER_MIB, ProcessStatus, ProcessView
from memory_pilot.ui.qt_bridge import DashboardController, ProcessListModel


class FakeMiniModeManager:
    def __init__(self, running: bool = False) -> None:
        self.running = running
        self.start_count = 0
        self.stop_count = 0
        self.stop_result = True

    def is_running(self) -> bool:
        return self.running

    def start(self) -> None:
        self.start_count += 1

    def request_stop(self) -> bool:
        self.stop_count += 1
        return self.stop_result


class ProcessListModelTests(unittest.TestCase):
    def setUp(self) -> None:
        self.model = ProcessListModel()
        self.model.set_views(
            (
                ProcessView(
                    key="group:browser",
                    name="Browser",
                    pids=(10, 11),
                    memory_bytes=900 * BYTES_PER_MIB,
                    cpu_percent=3.25,
                    status=ProcessStatus.USER_APP,
                    executable_path=r"C:\Apps\Browser.exe",
                ),
                ProcessView(
                    key="pid:20",
                    name="System helper",
                    pids=(20,),
                    memory_bytes=120 * BYTES_PER_MIB,
                    cpu_percent=0.0,
                    status=ProcessStatus.PROTECTED,
                ),
            )
        )

    def test_exposes_qml_display_roles(self) -> None:
        index = self.model.index(0, 0)

        self.assertEqual(self.model.data(index, self.model.NameRole), "Browser")
        self.assertEqual(self.model.data(index, self.model.PidRole), "2 个进程")
        self.assertEqual(self.model.data(index, self.model.MemoryRole), "900.0 MB")
        self.assertEqual(self.model.data(index, self.model.ToneRole), "normal")

    def test_filters_and_sorts_without_mutating_source(self) -> None:
        self.model.set_query("helper")
        self.assertEqual(self.model.visible_count, 1)
        self.assertEqual(self.model.data(self.model.index(0, 0), self.model.NameRole), "System helper")

        self.model.set_query("")
        self.model.sort_by("name")
        self.assertEqual(self.model.visible_count, 2)

    def test_live_values_update_without_resetting_the_model(self) -> None:
        resets: list[None] = []
        changes: list[None] = []
        self.model.modelReset.connect(lambda: resets.append(None))
        self.model.dataChanged.connect(lambda *_: changes.append(None))

        self.model.set_views(
            (
                ProcessView(
                    key="group:browser",
                    name="Browser",
                    pids=(10, 11),
                    memory_bytes=910 * BYTES_PER_MIB,
                    cpu_percent=4.5,
                    status=ProcessStatus.USER_APP,
                    executable_path=r"C:\Apps\Browser.exe",
                ),
                ProcessView(
                    key="pid:20",
                    name="System helper",
                    pids=(20,),
                    memory_bytes=125 * BYTES_PER_MIB,
                    cpu_percent=0.1,
                    status=ProcessStatus.PROTECTED,
                ),
            )
        )

        self.assertEqual(resets, [])
        self.assertEqual(len(changes), 1)
        self.assertEqual(self.model.data(self.model.index(0, 0), self.model.MemoryRole), "910.0 MB")

    def test_live_reorder_moves_rows_without_resetting_the_model(self) -> None:
        resets: list[None] = []
        moves: list[None] = []
        self.model.modelReset.connect(lambda: resets.append(None))
        self.model.rowsMoved.connect(lambda *_: moves.append(None))

        self.model.set_views(
            (
                ProcessView(
                    key="group:browser",
                    name="Browser",
                    pids=(10, 11),
                    memory_bytes=100 * BYTES_PER_MIB,
                    cpu_percent=3.25,
                    status=ProcessStatus.USER_APP,
                    executable_path=r"C:\Apps\Browser.exe",
                ),
                ProcessView(
                    key="pid:20",
                    name="System helper",
                    pids=(20,),
                    memory_bytes=920 * BYTES_PER_MIB,
                    cpu_percent=0.0,
                    status=ProcessStatus.PROTECTED,
                ),
            )
        )

        self.assertEqual(resets, [])
        self.assertEqual(len(moves), 1)
        self.assertEqual(self.model.data(self.model.index(0, 0), self.model.NameRole), "System helper")

    def test_live_process_addition_and_removal_do_not_reset_the_model(self) -> None:
        resets: list[None] = []
        insertions: list[None] = []
        removals: list[None] = []
        self.model.modelReset.connect(lambda: resets.append(None))
        self.model.rowsInserted.connect(lambda *_: insertions.append(None))
        self.model.rowsRemoved.connect(lambda *_: removals.append(None))

        self.model.set_views(
            (
                ProcessView(
                    key="group:browser",
                    name="Browser",
                    pids=(10, 11),
                    memory_bytes=900 * BYTES_PER_MIB,
                    cpu_percent=3.25,
                    status=ProcessStatus.USER_APP,
                    executable_path=r"C:\Apps\Browser.exe",
                ),
                ProcessView(
                    key="pid:30",
                    name="New app",
                    pids=(30,),
                    memory_bytes=80 * BYTES_PER_MIB,
                    cpu_percent=0.2,
                    status=ProcessStatus.USER_APP,
                ),
            )
        )

        self.assertEqual(resets, [])
        self.assertEqual(len(insertions), 1)
        self.assertEqual(len(removals), 1)
        self.assertEqual(self.model.visible_count, 2)


class DashboardMiniModeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QCoreApplication.instance() or QCoreApplication([])

    def test_switch_starts_same_product_mode_and_reconciles_success(self) -> None:
        manager = FakeMiniModeManager(False)
        controller = DashboardController(mini_mode_manager=manager)
        try:
            controller.setMiniModeEnabled(True)
            self.assertTrue(controller.miniModeEnabled)
            self.assertTrue(controller.miniModePending)
            self.assertEqual(manager.start_count, 1)

            manager.running = True
            controller._sync_mini_mode_state()
            self.assertTrue(controller.miniModeEnabled)
            self.assertFalse(controller.miniModePending)
        finally:
            controller.shutdown()

    def test_switch_requests_graceful_stop_and_tracks_external_exit(self) -> None:
        manager = FakeMiniModeManager(True)
        controller = DashboardController(mini_mode_manager=manager)
        try:
            controller.setMiniModeEnabled(False)
            self.assertFalse(controller.miniModeEnabled)
            self.assertTrue(controller.miniModePending)
            self.assertEqual(manager.stop_count, 1)

            manager.running = False
            controller._sync_mini_mode_state()
            self.assertFalse(controller.miniModePending)

            manager.running = True
            controller._sync_mini_mode_state()
            self.assertTrue(controller.miniModeEnabled)
            manager.running = False
            controller._sync_mini_mode_state()
            self.assertFalse(controller.miniModeEnabled)
        finally:
            controller.shutdown()

    def test_transition_timeout_restores_actual_state(self) -> None:
        now = [0.0]
        manager = FakeMiniModeManager(False)
        controller = DashboardController(
            mini_mode_manager=manager,
            clock=lambda: now[0],
        )
        try:
            controller.setMiniModeEnabled(True)
            now[0] = 16.0
            controller._sync_mini_mode_state()

            self.assertFalse(controller.miniModeEnabled)
            self.assertFalse(controller.miniModePending)
            self.assertIn("超时", controller.statusText)
        finally:
            controller.shutdown()

    def test_stop_signal_is_retried_while_mini_is_starting(self) -> None:
        manager = FakeMiniModeManager(True)
        manager.stop_result = False
        controller = DashboardController(mini_mode_manager=manager)
        try:
            controller.setMiniModeEnabled(False)
            self.assertTrue(controller.miniModePending)
            self.assertEqual(manager.stop_count, 1)

            controller._sync_mini_mode_state()
            self.assertEqual(manager.stop_count, 2)
            self.assertTrue(controller.miniModePending)

            manager.running = False
            controller._sync_mini_mode_state()
            self.assertFalse(controller.miniModePending)
            self.assertFalse(controller.miniModeEnabled)
        finally:
            controller.shutdown()


if __name__ == "__main__":
    unittest.main()
