from __future__ import annotations

import uuid
import unittest

from memory_pilot.ui.windowing import NamedMutex, top_right_geometry


class TopRightGeometryTests(unittest.TestCase):
    def test_positions_widget_inside_primary_work_area(self) -> None:
        geometry = top_right_geometry((0, 0, 1920, 1040), 240, 112, margin=16)

        self.assertEqual(geometry, "240x112+1664+16")

    def test_respects_nonzero_work_area_origin(self) -> None:
        geometry = top_right_geometry((100, 50, 1500, 900), 240, 112, margin=16)

        self.assertEqual(geometry, "240x112+1244+66")

    def test_keeps_oversized_widget_reachable(self) -> None:
        geometry = top_right_geometry((0, 0, 200, 100), 240, 112, margin=16)

        self.assertEqual(geometry, "240x112+0+0")


class NamedMutexTests(unittest.TestCase):
    def test_rejects_second_live_instance(self) -> None:
        name = f"Local\\MemoryPilotTest-{uuid.uuid4()}"
        first = NamedMutex(name)
        second = NamedMutex(name)
        try:
            self.assertTrue(first.acquire())
            self.assertFalse(second.acquire())
        finally:
            second.close()
            first.close()


if __name__ == "__main__":
    unittest.main()
