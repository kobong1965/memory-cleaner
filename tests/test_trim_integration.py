from __future__ import annotations

import os
import subprocess
import sys
import time
import unittest

from memory_pilot.platform.windows_api import WindowsApi


@unittest.skipUnless(os.environ.get("MEMORY_PILOT_LIVE_TEST") == "1", "live trim test is opt-in")
@unittest.skipUnless(os.name == "nt", "Windows API tests require Windows")
class WorkingSetTrimIntegrationTests(unittest.TestCase):
    def test_trims_controlled_child_without_terminating_it(self) -> None:
        child_code = (
            "import time; "
            "payload=bytearray(96*1024*1024); "
            "print('ready', flush=True); "
            "time.sleep(30)"
        )
        child = subprocess.Popen(
            [sys.executable, "-c", child_code],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            creationflags=0x08000000,
        )
        try:
            assert child.stdout is not None
            self.assertEqual(child.stdout.readline().strip(), "ready")
            api = WindowsApi()
            before = next(sample for sample in api.iter_process_samples() if sample.pid == child.pid)
            self.assertGreater(before.working_set_bytes, 64 * 1024 * 1024)

            api.trim_working_set(child.pid)
            time.sleep(0.2)

            self.assertIsNone(child.poll(), "working-set trimming must not terminate the process")
            after = next(sample for sample in api.iter_process_samples() if sample.pid == child.pid)
            self.assertLess(after.working_set_bytes, before.working_set_bytes)
        finally:
            child.terminate()
            child.wait(timeout=5)
            if child.stdout:
                child.stdout.close()
            if child.stderr:
                child.stderr.close()


if __name__ == "__main__":
    unittest.main()
