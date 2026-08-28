from __future__ import annotations

import ctypes
from pathlib import Path
import re
import sys

from PySide6.QtCore import QTimer, Qt, QUrl
from PySide6.QtGui import QGuiApplication, QIcon
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuickControls2 import QQuickStyle

from memory_pilot.ui.qt_bridge import DashboardController, MiniController
from memory_pilot.ui.resources import resource_path
from memory_pilot.ui.windowing import (
    NamedMutex,
    apply_native_rounded_corners,
    apply_tool_window_style,
    primary_work_area,
    top_right_geometry,
)

MINI_WIDTH = 286
MINI_HEIGHT = 158


def show_native_error(title: str, message: str) -> None:
    ctypes.windll.user32.MessageBoxW(None, message, title, 0x10)


def _qml_path(filename: str) -> Path:
    source_path = Path(__file__).with_name("qml") / filename
    if source_path.exists():
        return source_path
    return resource_path(f"qml/{filename}")


def _create_app(display_name: str) -> QGuiApplication:
    QGuiApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    app = QGuiApplication(sys.argv)
    app.setApplicationName("MemoryPilot")
    app.setApplicationDisplayName(display_name)
    app.setOrganizationName("Memory Pilot")
    icon_path = resource_path("assets/MemoryPilot.ico")
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))
    QQuickStyle.setStyle("Basic")
    return app


def _load_engine(filename: str, **context: object) -> QQmlApplicationEngine:
    engine = QQmlApplicationEngine()
    root_context = engine.rootContext()
    for name, value in context.items():
        root_context.setContextProperty(name, value)
    engine.load(QUrl.fromLocalFile(str(_qml_path(filename))))
    if not engine.rootObjects():
        raise RuntimeError(f"QML 界面加载失败：{filename}")
    return engine


def run_dashboard() -> None:
    app = _create_app("Memory Pilot · 内存领航员")
    controller = DashboardController(app)
    engine = _load_engine(
        "Main.qml",
        controller=controller,
        processModel=controller.process_model,
    )
    app.aboutToQuit.connect(controller.shutdown)
    QTimer.singleShot(0, controller.refresh)
    app.exec()


def run_mini_widget() -> None:
    mutex = NamedMutex("Local\\MemoryPilotMini.Singleton")
    if not mutex.acquire():
        return
    try:
        app = _create_app("Memory Pilot 迷你悬浮版")
        controller = MiniController(app)
        engine = _load_engine("Mini.qml", controller=controller)
        window = engine.rootObjects()[0]
        x, y = _mini_position()
        window.setPosition(x, y)
        controller.quitRequested.connect(app.quit)
        app.aboutToQuit.connect(controller.shutdown)
        app.aboutToQuit.connect(mutex.close)

        def apply_window_style() -> None:
            handle, _style = apply_tool_window_style(int(window.winId()))
            apply_native_rounded_corners(handle)

        QTimer.singleShot(80, apply_window_style)
        QTimer.singleShot(0, controller.refresh)
        QTimer.singleShot(120, window.requestActivate)
        app.exec()
    finally:
        mutex.close()


def _mini_position() -> tuple[int, int]:
    geometry = top_right_geometry(primary_work_area(), MINI_WIDTH, MINI_HEIGHT)
    match = re.fullmatch(r"\d+x\d+([+-]\d+)([+-]\d+)", geometry)
    if not match:
        return 16, 16
    return int(match.group(1)), int(match.group(2))
