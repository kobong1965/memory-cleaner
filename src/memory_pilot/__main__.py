from __future__ import annotations

import ctypes
import multiprocessing
import sys


def _enable_dpi_awareness() -> None:
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except (AttributeError, OSError):
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except (AttributeError, OSError):
            pass


def main() -> None:
    multiprocessing.freeze_support()
    _enable_dpi_awareness()
    try:
        from memory_pilot.ui.qt_runtime import run_dashboard, run_mini_widget

        if "--mini" in sys.argv[1:]:
            run_mini_widget()
        else:
            run_dashboard()
    except Exception as exc:
        from memory_pilot.ui.qt_runtime import show_native_error

        show_native_error("Memory Pilot", f"程序启动失败：\n{exc}")
        raise


if __name__ == "__main__":
    main()
