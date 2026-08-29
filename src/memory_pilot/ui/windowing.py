from __future__ import annotations

import ctypes
from ctypes import wintypes

ERROR_ALREADY_EXISTS = 183
ERROR_FILE_NOT_FOUND = 2
SYNCHRONIZE = 0x00100000
EVENT_MODIFY_STATE = 0x0002
WAIT_OBJECT_0 = 0x00000000
WAIT_TIMEOUT = 0x00000102
DWMWA_WINDOW_CORNER_PREFERENCE = 33
DWMWA_BORDER_COLOR = 34
DWMWCP_ROUND = 2
DWMWA_COLOR_NONE = 0xFFFFFFFE
GWL_EXSTYLE = -20
SPI_GETWORKAREA = 0x0030
SWP_NOMOVE = 0x0002
SWP_NOSIZE = 0x0001
SWP_NOZORDER = 0x0004
SWP_FRAMECHANGED = 0x0020
WS_EX_APPWINDOW = 0x00040000
WS_EX_TOOLWINDOW = 0x00000080


class RECT(ctypes.Structure):
    _fields_ = [
        ("left", wintypes.LONG),
        ("top", wintypes.LONG),
        ("right", wintypes.LONG),
        ("bottom", wintypes.LONG),
    ]


_kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
_user32 = ctypes.WinDLL("user32", use_last_error=True)
_dwmapi = ctypes.WinDLL("dwmapi", use_last_error=True)

_kernel32.CreateMutexW.argtypes = [ctypes.c_void_p, wintypes.BOOL, wintypes.LPCWSTR]
_kernel32.CreateMutexW.restype = wintypes.HANDLE
_kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
_kernel32.CloseHandle.restype = wintypes.BOOL
_kernel32.OpenMutexW.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.LPCWSTR]
_kernel32.OpenMutexW.restype = wintypes.HANDLE
_kernel32.CreateEventW.argtypes = [
    ctypes.c_void_p,
    wintypes.BOOL,
    wintypes.BOOL,
    wintypes.LPCWSTR,
]
_kernel32.CreateEventW.restype = wintypes.HANDLE
_kernel32.OpenEventW.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.LPCWSTR]
_kernel32.OpenEventW.restype = wintypes.HANDLE
_kernel32.SetEvent.argtypes = [wintypes.HANDLE]
_kernel32.SetEvent.restype = wintypes.BOOL
_kernel32.ResetEvent.argtypes = [wintypes.HANDLE]
_kernel32.ResetEvent.restype = wintypes.BOOL
_kernel32.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
_kernel32.WaitForSingleObject.restype = wintypes.DWORD

_user32.GetParent.argtypes = [wintypes.HWND]
_user32.GetParent.restype = wintypes.HWND
_user32.GetWindowLongW.argtypes = [wintypes.HWND, ctypes.c_int]
_user32.GetWindowLongW.restype = wintypes.LONG
_user32.SetWindowLongW.argtypes = [wintypes.HWND, ctypes.c_int, wintypes.LONG]
_user32.SetWindowLongW.restype = wintypes.LONG
_user32.SetWindowPos.argtypes = [
    wintypes.HWND,
    wintypes.HWND,
    ctypes.c_int,
    ctypes.c_int,
    ctypes.c_int,
    ctypes.c_int,
    wintypes.UINT,
]
_user32.SetWindowPos.restype = wintypes.BOOL
_user32.SystemParametersInfoW.argtypes = [
    wintypes.UINT,
    wintypes.UINT,
    ctypes.c_void_p,
    wintypes.UINT,
]
_user32.SystemParametersInfoW.restype = wintypes.BOOL
_dwmapi.DwmSetWindowAttribute.argtypes = [
    wintypes.HWND,
    wintypes.DWORD,
    ctypes.c_void_p,
    wintypes.DWORD,
]
_dwmapi.DwmSetWindowAttribute.restype = ctypes.c_long


def top_right_geometry(
    work_area: tuple[int, int, int, int],
    width: int,
    height: int,
    margin: int = 16,
) -> str:
    left, top, right, bottom = work_area
    x = max(left, right - width - margin)
    y = max(top, min(top + margin, bottom - height))
    return f"{width}x{height}{x:+d}{y:+d}"


def primary_work_area() -> tuple[int, int, int, int]:
    rect = RECT()
    if _user32.SystemParametersInfoW(SPI_GETWORKAREA, 0, ctypes.byref(rect), 0):
        return int(rect.left), int(rect.top), int(rect.right), int(rect.bottom)
    return 0, 0, int(_user32.GetSystemMetrics(0)), int(_user32.GetSystemMetrics(1))


def apply_tool_window_style(tk_window_id: int) -> tuple[int, int]:
    parent = _user32.GetParent(tk_window_id)
    window_handle = int(parent or tk_window_id)
    current_style = int(_user32.GetWindowLongW(window_handle, GWL_EXSTYLE))
    tool_style = (current_style | WS_EX_TOOLWINDOW) & ~WS_EX_APPWINDOW
    _user32.SetWindowLongW(window_handle, GWL_EXSTYLE, tool_style)
    _user32.SetWindowPos(
        window_handle,
        0,
        0,
        0,
        0,
        0,
        SWP_NOMOVE | SWP_NOSIZE | SWP_NOZORDER | SWP_FRAMECHANGED,
    )
    return window_handle, tool_style


def apply_native_rounded_corners(window_handle: int) -> bool:
    preference = ctypes.c_int(DWMWCP_ROUND)
    result = _dwmapi.DwmSetWindowAttribute(
        window_handle,
        DWMWA_WINDOW_CORNER_PREFERENCE,
        ctypes.byref(preference),
        ctypes.sizeof(preference),
    )
    border_color = ctypes.c_uint(DWMWA_COLOR_NONE)
    _dwmapi.DwmSetWindowAttribute(
        window_handle,
        DWMWA_BORDER_COLOR,
        ctypes.byref(border_color),
        ctypes.sizeof(border_color),
    )
    return result == 0


def named_mutex_exists(name: str) -> bool:
    ctypes.set_last_error(0)
    handle = _kernel32.OpenMutexW(SYNCHRONIZE, False, name)
    if handle:
        _kernel32.CloseHandle(handle)
        return True
    error_code = ctypes.get_last_error()
    if error_code in (0, ERROR_FILE_NOT_FOUND):
        return False
    raise ctypes.WinError(error_code)


def signal_named_event(name: str) -> bool:
    ctypes.set_last_error(0)
    handle = _kernel32.OpenEventW(EVENT_MODIFY_STATE, False, name)
    if not handle:
        error_code = ctypes.get_last_error()
        if error_code in (0, ERROR_FILE_NOT_FOUND):
            return False
        raise ctypes.WinError(error_code)
    try:
        if not _kernel32.SetEvent(handle):
            raise ctypes.WinError(ctypes.get_last_error())
        return True
    finally:
        _kernel32.CloseHandle(handle)


class NamedMutex:
    def __init__(self, name: str) -> None:
        self._name = name
        self._handle: int | None = None

    def acquire(self) -> bool:
        if self._handle is not None:
            return True
        ctypes.set_last_error(0)
        handle = _kernel32.CreateMutexW(None, False, self._name)
        if not handle:
            raise ctypes.WinError(ctypes.get_last_error())
        if ctypes.get_last_error() == ERROR_ALREADY_EXISTS:
            _kernel32.CloseHandle(handle)
            return False
        self._handle = int(handle)
        return True

    def close(self) -> None:
        if self._handle is not None:
            _kernel32.CloseHandle(self._handle)
            self._handle = None

    def __enter__(self) -> NamedMutex:
        if not self.acquire():
            raise RuntimeError("另一个 Memory Pilot 迷你版已经在运行。")
        return self

    def __exit__(self, _exc_type: object, _exc: object, _traceback: object) -> None:
        self.close()


class NamedEvent:
    def __init__(self, name: str) -> None:
        self._name = name
        self._handle: int | None = None

    def create(self) -> None:
        if self._handle is not None:
            return
        handle = _kernel32.CreateEventW(None, True, False, self._name)
        if not handle:
            raise ctypes.WinError(ctypes.get_last_error())
        self._handle = int(handle)
        if not _kernel32.ResetEvent(handle):
            self.close()
            raise ctypes.WinError(ctypes.get_last_error())

    def is_set(self) -> bool:
        if self._handle is None:
            return False
        result = int(_kernel32.WaitForSingleObject(self._handle, 0))
        if result == WAIT_OBJECT_0:
            return True
        if result == WAIT_TIMEOUT:
            return False
        raise ctypes.WinError(ctypes.get_last_error())

    def close(self) -> None:
        if self._handle is not None:
            _kernel32.CloseHandle(self._handle)
            self._handle = None

    def __enter__(self) -> NamedEvent:
        self.create()
        return self

    def __exit__(self, _exc_type: object, _exc: object, _traceback: object) -> None:
        self.close()
