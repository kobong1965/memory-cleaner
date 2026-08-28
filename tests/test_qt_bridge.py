from __future__ import annotations

import unittest

from memory_pilot.models import BYTES_PER_MIB, ProcessStatus, ProcessView
from memory_pilot.ui.qt_bridge import ProcessListModel


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


if __name__ == "__main__":
    unittest.main()
