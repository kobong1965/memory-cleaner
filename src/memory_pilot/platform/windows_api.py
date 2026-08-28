from __future__ import annotations

import ctypes
import os
import time
from ctypes import wintypes
from typing import Iterator

from memory_pilot.models import AppWindowInfo, MemorySnapshot, ProcessSample

if os.name != "nt":
    raise RuntimeError("Memory Pilot only supports Windows.")


TH32CS_SNAPPROCESS = 0x00000002
PROCESS_QUERY_INFORMATION = 0x0400
PROCESS_SET_QUOTA = 0x0100
PROCESS_VM_READ = 0x0010
PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
TOKEN_QUERY = 0x0008
TOKEN_ELEVATION_CLASS = 20
ERROR_NO_MORE_FILES = 18
MAX_PATH_BUFFER = 32_768
INVALID_HANDLE_VALUE = ctypes.c_void_p(-1).value
SYSTEM_PROCESS_INFORMATION_CLASS = 5
STATUS_INFO_LENGTH_MISMATCH = 0xC0000004
GWL_EXSTYLE = -20
GW_OWNER = 4
WS_EX_TOOLWINDOW = 0x00000080
WM_CLOSE = 0x0010

SIZE_T = ctypes.c_size_t
ULONG_PTR = wintypes.WPARAM
WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)


class PROCESSENTRY32W(ctypes.Structure):
    _fields_ = [
        ("dwSize", wintypes.DWORD),
        ("cntUsage", wintypes.DWORD),
        ("th32ProcessID", wintypes.DWORD),
        ("th32DefaultHeapID", ULONG_PTR),
        ("th32ModuleID", wintypes.DWORD),
        ("cntThreads", wintypes.DWORD),
        ("th32ParentProcessID", wintypes.DWORD),
        ("pcPriClassBase", wintypes.LONG),
        ("dwFlags", wintypes.DWORD),
        ("szExeFile", wintypes.WCHAR * 260),
    ]


class PROCESS_MEMORY_COUNTERS_EX(ctypes.Structure):
    _fields_ = [
        ("cb", wintypes.DWORD),
        ("PageFaultCount", wintypes.DWORD),
        ("PeakWorkingSetSize", SIZE_T),
        ("WorkingSetSize", SIZE_T),
        ("QuotaPeakPagedPoolUsage", SIZE_T),
        ("QuotaPagedPoolUsage", SIZE_T),
        ("QuotaPeakNonPagedPoolUsage", SIZE_T),
        ("QuotaNonPagedPoolUsage", SIZE_T),
        ("PagefileUsage", SIZE_T),
        ("PeakPagefileUsage", SIZE_T),
        ("PrivateUsage", SIZE_T),
    ]


class MEMORYSTATUSEX(ctypes.Structure):
    _fields_ = [
        ("dwLength", wintypes.DWORD),
        ("dwMemoryLoad", wintypes.DWORD),
        ("ullTotalPhys", ctypes.c_ulonglong),
        ("ullAvailPhys", ctypes.c_ulonglong),
        ("ullTotalPageFile", ctypes.c_ulonglong),
        ("ullAvailPageFile", ctypes.c_ulonglong),
        ("ullTotalVirtual", ctypes.c_ulonglong),
        ("ullAvailVirtual", ctypes.c_ulonglong),
        ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
    ]


class TOKEN_ELEVATION(ctypes.Structure):
    _fields_ = [("TokenIsElevated", wintypes.DWORD)]


class UNICODE_STRING(ctypes.Structure):
    _fields_ = [
        ("Length", wintypes.USHORT),
        ("MaximumLength", wintypes.USHORT),
        ("Buffer", wintypes.LPWSTR),
    ]


class SYSTEM_PROCESS_INFORMATION_PREFIX(ctypes.Structure):
    _fields_ = [
        ("NextEntryOffset", wintypes.ULONG),
        ("NumberOfThreads", wintypes.ULONG),
        ("WorkingSetPrivateSize", ctypes.c_longlong),
        ("HardFaultCount", wintypes.ULONG),
        ("NumberOfThreadsHighWatermark", wintypes.ULONG),
        ("CycleTime", ctypes.c_ulonglong),
        ("CreateTime", ctypes.c_longlong),
        ("UserTime", ctypes.c_longlong),
        ("KernelTime", ctypes.c_longlong),
        ("ImageName", UNICODE_STRING),
        ("BasePriority", wintypes.LONG),
        ("UniqueProcessId", wintypes.HANDLE),
        ("InheritedFromUniqueProcessId", wintypes.HANDLE),
        ("HandleCount", wintypes.ULONG),
        ("SessionId", wintypes.ULONG),
        ("UniqueProcessKey", ULONG_PTR),
        ("PeakVirtualSize", SIZE_T),
        ("VirtualSize", SIZE_T),
        ("PageFaultCount", wintypes.ULONG),
        ("PeakWorkingSetSize", SIZE_T),
        ("WorkingSetSize", SIZE_T),
    ]


class WindowsApiError(RuntimeError):
    def __init__(self, operation: str, error_code: int | None = None) -> None:
        code = ctypes.get_last_error() if error_code is None else error_code
        message = ctypes.FormatError(code).strip() if code else "未知错误"
        super().__init__(f"{operation}失败（{code}: {message}）")
        self.operation = operation
        self.error_code = code


class WindowsApi:
    """Small ctypes boundary for process and physical-memory operations."""

    def __init__(self) -> None:
        self._kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        self._psapi = ctypes.WinDLL("psapi", use_last_error=True)
        self._advapi32 = ctypes.WinDLL("advapi32", use_last_error=True)
        self._ntdll = ctypes.WinDLL("ntdll", use_last_error=True)
        self._user32 = ctypes.WinDLL("user32", use_last_error=True)
        self._path_cache: dict[int, str] = {}
        self._configure_signatures()

    def _configure_signatures(self) -> None:
        self._kernel32.CreateToolhelp32Snapshot.argtypes = [wintypes.DWORD, wintypes.DWORD]
        self._kernel32.CreateToolhelp32Snapshot.restype = wintypes.HANDLE
        self._kernel32.Process32FirstW.argtypes = [wintypes.HANDLE, ctypes.POINTER(PROCESSENTRY32W)]
        self._kernel32.Process32FirstW.restype = wintypes.BOOL
        self._kernel32.Process32NextW.argtypes = [wintypes.HANDLE, ctypes.POINTER(PROCESSENTRY32W)]
        self._kernel32.Process32NextW.restype = wintypes.BOOL
        self._kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
        self._kernel32.OpenProcess.restype = wintypes.HANDLE
        self._kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
        self._kernel32.CloseHandle.restype = wintypes.BOOL
        self._kernel32.GetProcessTimes.argtypes = [
            wintypes.HANDLE,
            ctypes.POINTER(wintypes.FILETIME),
            ctypes.POINTER(wintypes.FILETIME),
            ctypes.POINTER(wintypes.FILETIME),
            ctypes.POINTER(wintypes.FILETIME),
        ]
        self._kernel32.GetProcessTimes.restype = wintypes.BOOL
        self._kernel32.QueryFullProcessImageNameW.argtypes = [
            wintypes.HANDLE,
            wintypes.DWORD,
            wintypes.LPWSTR,
            ctypes.POINTER(wintypes.DWORD),
        ]
        self._kernel32.QueryFullProcessImageNameW.restype = wintypes.BOOL
        self._kernel32.GlobalMemoryStatusEx.argtypes = [ctypes.POINTER(MEMORYSTATUSEX)]
        self._kernel32.GlobalMemoryStatusEx.restype = wintypes.BOOL
        self._kernel32.GetCurrentProcess.argtypes = []
        self._kernel32.GetCurrentProcess.restype = wintypes.HANDLE
        self._psapi.GetProcessMemoryInfo.argtypes = [
            wintypes.HANDLE,
            ctypes.POINTER(PROCESS_MEMORY_COUNTERS_EX),
            wintypes.DWORD,
        ]
        self._psapi.GetProcessMemoryInfo.restype = wintypes.BOOL
        self._psapi.EmptyWorkingSet.argtypes = [wintypes.HANDLE]
        self._psapi.EmptyWorkingSet.restype = wintypes.BOOL
        self._advapi32.OpenProcessToken.argtypes = [
            wintypes.HANDLE,
            wintypes.DWORD,
            ctypes.POINTER(wintypes.HANDLE),
        ]
        self._advapi32.OpenProcessToken.restype = wintypes.BOOL
        self._advapi32.GetTokenInformation.argtypes = [
            wintypes.HANDLE,
            ctypes.c_int,
            wintypes.LPVOID,
            wintypes.DWORD,
            ctypes.POINTER(wintypes.DWORD),
        ]
        self._advapi32.GetTokenInformation.restype = wintypes.BOOL
        self._ntdll.NtQuerySystemInformation.argtypes = [
            ctypes.c_int,
            wintypes.LPVOID,
            wintypes.ULONG,
            ctypes.POINTER(wintypes.ULONG),
        ]
        self._ntdll.NtQuerySystemInformation.restype = wintypes.LONG
        self._user32.EnumWindows.argtypes = [WNDENUMPROC, wintypes.LPARAM]
        self._user32.EnumWindows.restype = wintypes.BOOL
        self._user32.IsWindowVisible.argtypes = [wintypes.HWND]
        self._user32.IsWindowVisible.restype = wintypes.BOOL
        self._user32.GetWindow.argtypes = [wintypes.HWND, wintypes.UINT]
        self._user32.GetWindow.restype = wintypes.HWND
        self._user32.GetWindowLongW.argtypes = [wintypes.HWND, ctypes.c_int]
        self._user32.GetWindowLongW.restype = wintypes.LONG
        self._user32.GetWindowTextLengthW.argtypes = [wintypes.HWND]
        self._user32.GetWindowTextLengthW.restype = ctypes.c_int
        self._user32.GetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
        self._user32.GetWindowTextW.restype = ctypes.c_int
        self._user32.GetWindowThreadProcessId.argtypes = [
            wintypes.HWND,
            ctypes.POINTER(wintypes.DWORD),
        ]
        self._user32.GetWindowThreadProcessId.restype = wintypes.DWORD
        self._user32.GetForegroundWindow.argtypes = []
        self._user32.GetForegroundWindow.restype = wintypes.HWND
        self._user32.PostMessageW.argtypes = [
            wintypes.HWND,
            wintypes.UINT,
            wintypes.WPARAM,
            wintypes.LPARAM,
        ]
        self._user32.PostMessageW.restype = wintypes.BOOL

    def get_memory_snapshot(self) -> MemorySnapshot:
        status = MEMORYSTATUSEX()
        status.dwLength = ctypes.sizeof(status)
        if not self._kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):
            raise WindowsApiError("读取系统内存")
        return MemorySnapshot(
            total_bytes=int(status.ullTotalPhys),
            available_bytes=int(status.ullAvailPhys),
            timestamp=time.monotonic(),
        )

    def iter_process_samples(self) -> Iterator[ProcessSample]:
        try:
            yield from self._iter_system_process_samples()
        except WindowsApiError:
            yield from self._iter_toolhelp_process_samples()

    def _iter_system_process_samples(self) -> Iterator[ProcessSample]:
        buffer_size = 1 * 1024 * 1024
        while True:
            buffer = ctypes.create_string_buffer(buffer_size)
            returned_length = wintypes.ULONG()
            status = self._ntdll.NtQuerySystemInformation(
                SYSTEM_PROCESS_INFORMATION_CLASS,
                buffer,
                buffer_size,
                ctypes.byref(returned_length),
            )
            unsigned_status = ctypes.c_ulong(status).value
            if unsigned_status == STATUS_INFO_LENGTH_MISMATCH:
                buffer_size = max(buffer_size * 2, int(returned_length.value) + 64 * 1024)
                continue
            if status < 0:
                raise WindowsApiError("读取系统进程信息", unsigned_status)
            break

        offset = 0
        while offset < buffer_size:
            info = ctypes.cast(
                ctypes.byref(buffer, offset), ctypes.POINTER(SYSTEM_PROCESS_INFORMATION_PREFIX)
            ).contents
            pid = int(info.UniqueProcessId or 0)
            if info.ImageName.Buffer and info.ImageName.Length:
                name = ctypes.wstring_at(info.ImageName.Buffer, info.ImageName.Length // 2)
            elif pid == 0:
                name = "[System Process]"
            elif pid == 4:
                name = "System"
            else:
                name = f"PID {pid}"

            path = self._path_cache.get(pid, "")
            if not path and pid > 4:
                path = self._query_process_path_by_pid(pid)
                if path:
                    self._path_cache[pid] = path

            yield ProcessSample(
                pid=pid,
                name=name,
                working_set_bytes=int(info.WorkingSetSize),
                cpu_time_100ns=max(0, int(info.UserTime) + int(info.KernelTime)),
                executable_path=path,
                accessible=True,
                error="",
                session_id=int(info.SessionId),
            )

            next_offset = int(info.NextEntryOffset)
            if next_offset == 0:
                break
            offset += next_offset

    def _iter_toolhelp_process_samples(self) -> Iterator[ProcessSample]:
        snapshot = self._kernel32.CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0)
        if not snapshot or snapshot == INVALID_HANDLE_VALUE:
            raise WindowsApiError("创建进程快照")

        entry = PROCESSENTRY32W()
        entry.dwSize = ctypes.sizeof(entry)
        try:
            if not self._kernel32.Process32FirstW(snapshot, ctypes.byref(entry)):
                raise WindowsApiError("读取首个进程")

            while True:
                pid = int(entry.th32ProcessID)
                name = entry.szExeFile or f"PID {pid}"
                yield self._sample_process(pid, name)

                if not self._kernel32.Process32NextW(snapshot, ctypes.byref(entry)):
                    error_code = ctypes.get_last_error()
                    if error_code not in (0, ERROR_NO_MORE_FILES):
                        raise WindowsApiError("读取进程列表", error_code)
                    break
        finally:
            self._kernel32.CloseHandle(snapshot)

    def _sample_process(self, pid: int, fallback_name: str) -> ProcessSample:
        if pid == 0:
            return ProcessSample(pid, fallback_name, 0, 0, accessible=False, error="系统空闲进程")

        access = PROCESS_QUERY_INFORMATION | PROCESS_VM_READ
        handle = self._kernel32.OpenProcess(access, False, pid)
        if not handle:
            fallback_access = PROCESS_QUERY_LIMITED_INFORMATION | PROCESS_VM_READ
            handle = self._kernel32.OpenProcess(fallback_access, False, pid)
        if not handle:
            return ProcessSample(
                pid,
                fallback_name,
                0,
                0,
                accessible=False,
                error=self._last_error_text(),
            )

        try:
            counters = PROCESS_MEMORY_COUNTERS_EX()
            counters.cb = ctypes.sizeof(counters)
            memory_ok = bool(
                self._psapi.GetProcessMemoryInfo(handle, ctypes.byref(counters), counters.cb)
            )

            creation = wintypes.FILETIME()
            exit_time = wintypes.FILETIME()
            kernel = wintypes.FILETIME()
            user = wintypes.FILETIME()
            times_ok = bool(
                self._kernel32.GetProcessTimes(
                    handle,
                    ctypes.byref(creation),
                    ctypes.byref(exit_time),
                    ctypes.byref(kernel),
                    ctypes.byref(user),
                )
            )

            path = self._query_process_path(handle)
            cpu_time = self._filetime_value(kernel) + self._filetime_value(user) if times_ok else 0
            if not memory_ok and not times_ok:
                return ProcessSample(
                    pid,
                    fallback_name,
                    0,
                    0,
                    path,
                    accessible=False,
                    error=self._last_error_text(),
                )

            return ProcessSample(
                pid=pid,
                name=fallback_name,
                working_set_bytes=int(counters.WorkingSetSize) if memory_ok else 0,
                cpu_time_100ns=cpu_time,
                executable_path=path,
                accessible=True,
                error="" if memory_ok else "无法读取内存占用",
            )
        finally:
            self._kernel32.CloseHandle(handle)

    def trim_working_set(self, pid: int) -> None:
        access = PROCESS_QUERY_INFORMATION | PROCESS_SET_QUOTA
        handle = self._kernel32.OpenProcess(access, False, pid)
        if not handle:
            raise WindowsApiError(f"打开进程 {pid}")
        try:
            if not self._psapi.EmptyWorkingSet(handle):
                raise WindowsApiError(f"修剪进程 {pid} 工作集")
        finally:
            self._kernel32.CloseHandle(handle)

    def get_visible_app_windows(self) -> tuple[AppWindowInfo, ...]:
        windows: list[AppWindowInfo] = []

        @WNDENUMPROC
        def collect(window_handle: wintypes.HWND, _lparam: wintypes.LPARAM) -> bool:
            if not self._user32.IsWindowVisible(window_handle):
                return True
            if self._user32.GetWindow(window_handle, GW_OWNER):
                return True
            extended_style = int(self._user32.GetWindowLongW(window_handle, GWL_EXSTYLE))
            if extended_style & WS_EX_TOOLWINDOW:
                return True

            title_length = int(self._user32.GetWindowTextLengthW(window_handle))
            if title_length <= 0:
                return True
            title_buffer = ctypes.create_unicode_buffer(title_length + 1)
            if self._user32.GetWindowTextW(window_handle, title_buffer, len(title_buffer)) <= 0:
                return True

            pid = wintypes.DWORD()
            self._user32.GetWindowThreadProcessId(window_handle, ctypes.byref(pid))
            if pid.value:
                windows.append(
                    AppWindowInfo(
                        handle=int(window_handle),
                        pid=int(pid.value),
                        title=title_buffer.value.strip(),
                    )
                )
            return True

        ctypes.set_last_error(0)
        if not self._user32.EnumWindows(collect, 0):
            error_code = ctypes.get_last_error()
            if error_code:
                raise WindowsApiError("读取桌面程序窗口", error_code)
        return tuple(windows)

    def get_foreground_process_id(self) -> int:
        window_handle = self._user32.GetForegroundWindow()
        if not window_handle:
            return 0
        pid = wintypes.DWORD()
        self._user32.GetWindowThreadProcessId(window_handle, ctypes.byref(pid))
        return int(pid.value)

    def post_close_window(self, window_handle: int) -> None:
        if not self._user32.PostMessageW(window_handle, WM_CLOSE, 0, 0):
            raise WindowsApiError(f"请求关闭窗口 {window_handle}")

    def _query_process_path_by_pid(self, pid: int) -> str:
        handle = self._kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
        if not handle:
            return ""
        try:
            return self._query_process_path(handle)
        finally:
            self._kernel32.CloseHandle(handle)

    def is_current_process_elevated(self) -> bool:
        token = wintypes.HANDLE()
        if not self._advapi32.OpenProcessToken(
            self._kernel32.GetCurrentProcess(), TOKEN_QUERY, ctypes.byref(token)
        ):
            return False
        try:
            elevation = TOKEN_ELEVATION()
            returned = wintypes.DWORD()
            if not self._advapi32.GetTokenInformation(
                token,
                TOKEN_ELEVATION_CLASS,
                ctypes.byref(elevation),
                ctypes.sizeof(elevation),
                ctypes.byref(returned),
            ):
                return False
            return bool(elevation.TokenIsElevated)
        finally:
            self._kernel32.CloseHandle(token)

    def _query_process_path(self, handle: wintypes.HANDLE) -> str:
        buffer = ctypes.create_unicode_buffer(MAX_PATH_BUFFER)
        size = wintypes.DWORD(len(buffer))
        if not self._kernel32.QueryFullProcessImageNameW(handle, 0, buffer, ctypes.byref(size)):
            return ""
        return buffer.value

    @staticmethod
    def _filetime_value(value: wintypes.FILETIME) -> int:
        return (int(value.dwHighDateTime) << 32) | int(value.dwLowDateTime)

    @staticmethod
    def _last_error_text() -> str:
        code = ctypes.get_last_error()
        if not code:
            return "访问受限"
        return f"{code}: {ctypes.FormatError(code).strip()}"
