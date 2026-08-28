from __future__ import annotations

import multiprocessing

from memory_pilot.__main__ import _enable_dpi_awareness


def main() -> None:
    multiprocessing.freeze_support()
    _enable_dpi_awareness()
    try:
        from memory_pilot.ui.qt_runtime import run_mini_widget

        run_mini_widget()
    except Exception as exc:
        from memory_pilot.ui.qt_runtime import show_native_error

        show_native_error("Memory Pilot 迷你版", f"程序启动失败：\n{exc}")
        raise


if __name__ == "__main__":
    main()
