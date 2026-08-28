from __future__ import annotations

import concurrent.futures
import datetime as dt
from pathlib import Path
import subprocess
import sys
from typing import Callable, Sequence

from PySide6.QtCore import (
    QAbstractListModel,
    QModelIndex,
    QObject,
    Property,
    Qt,
    QTimer,
    Signal,
    Slot,
)

from memory_pilot.core.deep_clean import AppUsageTracker, DeepCleanService
from memory_pilot.core.memory_release import MemoryReleaseService
from memory_pilot.core.process_monitor import MonitorSnapshot, ProcessMonitor, filter_and_sort_views
from memory_pilot.core.settings import SettingsStore
from memory_pilot.models import (
    BYTES_PER_MIB,
    DeepCleanPlan,
    DeepCleanResult,
    MemoryReleaseResult,
    MemorySnapshot,
    ProcessStatus,
    ProcessView,
)
from memory_pilot.platform.windows_api import WindowsApi

REFRESH_INTERVAL_MS = 2_000


def format_gb(byte_count: int) -> str:
    return f"{byte_count / BYTES_PER_MIB / 1024:.1f} GB"


def clamp_percent(value: float) -> float:
    return min(100.0, max(0.0, value))


class ProcessListModel(QAbstractListModel):
    NameRole = Qt.UserRole + 1
    PidRole = Qt.UserRole + 2
    StatusRole = Qt.UserRole + 3
    CpuRole = Qt.UserRole + 4
    MemoryRole = Qt.UserRole + 5
    PathRole = Qt.UserRole + 6
    ToneRole = Qt.UserRole + 7
    KeyRole = Qt.UserRole + 8

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._source: tuple[ProcessView, ...] = ()
        self._visible: tuple[ProcessView, ...] = ()
        self._query = ""
        self._sort_key = "memory"
        self._descending = True

    def roleNames(self) -> dict[int, bytes]:
        return {
            self.NameRole: b"processName",
            self.PidRole: b"pidLabel",
            self.StatusRole: b"statusLabel",
            self.CpuRole: b"cpuLabel",
            self.MemoryRole: b"memoryLabel",
            self.PathRole: b"pathLabel",
            self.ToneRole: b"statusTone",
            self.KeyRole: b"processKey",
        }

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return 0 if parent.isValid() else len(self._visible)

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole) -> object:
        if not index.isValid() or not 0 <= index.row() < len(self._visible):
            return None
        view = self._visible[index.row()]
        values = {
            self.NameRole: view.name,
            self.PidRole: view.pid_label,
            self.StatusRole: view.status.value,
            self.CpuRole: f"{view.cpu_percent:.1f}%",
            self.MemoryRole: f"{view.memory_mb:,.1f} MB",
            self.PathRole: view.executable_path or "—",
            self.ToneRole: _status_tone(view.status),
            self.KeyRole: view.key,
        }
        return values.get(role)

    @property
    def visible_count(self) -> int:
        return len(self._visible)

    @property
    def sort_key(self) -> str:
        return self._sort_key

    @property
    def descending(self) -> bool:
        return self._descending

    def set_views(self, views: Sequence[ProcessView]) -> None:
        self._source = tuple(views)
        self._rebuild()

    def set_query(self, query: str) -> None:
        if query == self._query:
            return
        self._query = query
        self._rebuild()

    def sort_by(self, key: str) -> None:
        if key == self._sort_key:
            self._descending = not self._descending
        else:
            self._sort_key = key
            self._descending = key in {"cpu", "memory", "pid"}
        self._rebuild()

    def _rebuild(self) -> None:
        visible = filter_and_sort_views(
            self._source,
            self._query,
            self._sort_key,
            self._descending,
        )
        if visible == self._visible:
            return

        if not self._visible:
            if visible:
                self.beginInsertRows(QModelIndex(), 0, len(visible) - 1)
                self._visible = visible
                self.endInsertRows()
            return

        if not visible:
            self.beginRemoveRows(QModelIndex(), 0, len(self._visible) - 1)
            self._visible = ()
            self.endRemoveRows()
            return

        rows = list(self._visible)
        target_keys = {view.key for view in visible}

        for index in range(len(rows) - 1, -1, -1):
            if rows[index].key not in target_keys:
                self.beginRemoveRows(QModelIndex(), index, index)
                rows.pop(index)
                self._visible = tuple(rows)
                self.endRemoveRows()

        for target_index, target_view in enumerate(visible):
            current_index = next(
                (index for index, row in enumerate(rows) if row.key == target_view.key),
                None,
            )
            if current_index is None:
                self.beginInsertRows(QModelIndex(), target_index, target_index)
                rows.insert(target_index, target_view)
                self._visible = tuple(rows)
                self.endInsertRows()
            elif current_index != target_index:
                destination = target_index if current_index > target_index else target_index + 1
                if not self.beginMoveRows(
                    QModelIndex(),
                    current_index,
                    current_index,
                    QModelIndex(),
                    destination,
                ):
                    raise RuntimeError("无法增量更新进程列表顺序")
                row = rows.pop(current_index)
                rows.insert(target_index, row)
                self._visible = tuple(rows)
                self.endMoveRows()

        self._visible = visible
        self.dataChanged.emit(
            self.index(0, 0),
            self.index(len(visible) - 1, 0),
            list(self.roleNames()),
        )


def _status_tone(status: ProcessStatus) -> str:
    return {
        ProcessStatus.USER_APP: "normal",
        ProcessStatus.SYSTEM: "system",
        ProcessStatus.PROTECTED: "protected",
        ProcessStatus.RESTRICTED: "restricted",
    }[status]


class DashboardController(QObject):
    usageTextChanged = Signal()
    usagePercentChanged = Signal()
    usedTextChanged = Signal()
    availableTextChanged = Signal()
    processCountTextChanged = Signal()
    updatedTextChanged = Signal()
    statusTextChanged = Signal()
    privilegeTextChanged = Signal()
    busyChanged = Signal()
    groupedChanged = Signal()
    tableStateChanged = Signal()
    noticeChanged = Signal()

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self.api = WindowsApi()
        self.monitor = ProcessMonitor(self.api)
        self.release_service = MemoryReleaseService(self.api)
        self.process_model = ProcessListModel(self)
        self._executor = concurrent.futures.ThreadPoolExecutor(max_workers=1, thread_name_prefix="memory-pilot-qt")
        self._future: concurrent.futures.Future[object] | None = None
        self._future_kind = ""
        self._last_snapshot: MonitorSnapshot | None = None
        self._pending_release = False
        self._closed = False

        self._usage_text = "—%"
        self._usage_percent = 0.0
        self._used_text = "正在读取…"
        self._available_text = "—"
        self._process_count_text = "—"
        self._updated_text = "等待首次刷新"
        self._status_text = "正在读取系统状态…"
        self._privilege_text = "管理员模式" if self.api.is_current_process_elevated() else "普通权限"
        self._busy = False
        self._grouped = True
        self._notice_visible = False
        self._notice_title = ""
        self._notice_body = ""

        self._poll_timer = QTimer(self)
        self._poll_timer.setInterval(40)
        self._poll_timer.timeout.connect(self._poll_future)
        self._refresh_timer = QTimer(self)
        self._refresh_timer.setSingleShot(True)
        self._refresh_timer.setInterval(REFRESH_INTERVAL_MS)
        self._refresh_timer.timeout.connect(self.refresh)

    @Property(str, notify=usageTextChanged)
    def usageText(self) -> str:
        return self._usage_text

    @Property(float, notify=usagePercentChanged)
    def usagePercent(self) -> float:
        return self._usage_percent

    @Property(str, notify=usedTextChanged)
    def usedText(self) -> str:
        return self._used_text

    @Property(str, notify=availableTextChanged)
    def availableText(self) -> str:
        return self._available_text

    @Property(str, notify=processCountTextChanged)
    def processCountText(self) -> str:
        return self._process_count_text

    @Property(str, notify=updatedTextChanged)
    def updatedText(self) -> str:
        return self._updated_text

    @Property(str, notify=statusTextChanged)
    def statusText(self) -> str:
        return self._status_text

    @Property(str, notify=privilegeTextChanged)
    def privilegeText(self) -> str:
        return self._privilege_text

    @Property(bool, notify=busyChanged)
    def busy(self) -> bool:
        return self._busy

    @Property(bool, notify=groupedChanged)
    def grouped(self) -> bool:
        return self._grouped

    @Property(str, notify=tableStateChanged)
    def sortKey(self) -> str:
        return self.process_model.sort_key

    @Property(bool, notify=tableStateChanged)
    def sortDescending(self) -> bool:
        return self.process_model.descending

    @Property(int, notify=tableStateChanged)
    def visibleCount(self) -> int:
        return self.process_model.visible_count

    @Property(bool, notify=noticeChanged)
    def noticeVisible(self) -> bool:
        return self._notice_visible

    @Property(str, notify=noticeChanged)
    def noticeTitle(self) -> str:
        return self._notice_title

    @Property(str, notify=noticeChanged)
    def noticeBody(self) -> str:
        return self._notice_body

    @Slot()
    def refresh(self) -> None:
        if self._closed:
            return
        self._refresh_timer.stop()
        if self._future is not None:
            self._schedule_refresh()
            return
        self._start_future(
            "refresh",
            lambda: self.monitor.sample(self._grouped),
            visible_busy=False,
        )

    @Slot(str)
    def setSearch(self, query: str) -> None:
        self.process_model.set_query(query)
        self.tableStateChanged.emit()
        self._update_timestamp_text()

    @Slot(bool)
    def setGrouped(self, grouped: bool) -> None:
        if grouped == self._grouped:
            return
        self._grouped = grouped
        self.groupedChanged.emit()
        self.refresh()

    @Slot(str)
    def sortBy(self, key: str) -> None:
        self.process_model.sort_by(key)
        self.tableStateChanged.emit()
        self._update_timestamp_text()

    @Slot()
    def releaseMemory(self) -> None:
        if self._future is not None:
            if self._future_kind == "refresh":
                self._pending_release = True
            return
        if self._last_snapshot is None:
            self._set_status("等待进程列表首次刷新后再释放内存。")
            return
        self._refresh_timer.stop()
        self._set_status("正在安全修剪用户进程的闲置工作集…")
        samples = self._last_snapshot.samples
        self._start_future(
            "release",
            lambda: self.release_service.release(samples),
            visible_busy=True,
        )

    @Slot()
    def dismissNotice(self) -> None:
        if not self._notice_visible:
            return
        self._notice_visible = False
        self.noticeChanged.emit()

    @Slot()
    def shutdown(self) -> None:
        if self._closed:
            return
        self._closed = True
        self._refresh_timer.stop()
        self._poll_timer.stop()
        self._executor.shutdown(wait=False, cancel_futures=True)

    def _start_future(
        self,
        kind: str,
        operation: Callable[[], object],
        *,
        visible_busy: bool,
    ) -> None:
        if visible_busy:
            self._set_busy(True)
        self._future_kind = kind
        self._future = self._executor.submit(operation)
        self._poll_timer.start()

    @Slot()
    def _poll_future(self) -> None:
        future = self._future
        if future is None or not future.done():
            return
        self._poll_timer.stop()
        kind = self._future_kind
        self._future = None
        self._future_kind = ""
        if kind == "release":
            self._set_busy(False)
        try:
            result = future.result()
        except Exception as exc:
            self._set_status(f"操作失败：{exc}")
            self._show_notice("操作未完成", f"Memory Pilot 无法完成本次操作。\n\n{exc}")
            self._schedule_refresh()
            return

        if kind == "refresh":
            self._finish_refresh(result)
            if self._pending_release:
                self._pending_release = False
                QTimer.singleShot(0, self.releaseMemory)
        elif kind == "release":
            self._finish_release(result)

    def _finish_refresh(self, result: object) -> None:
        if not isinstance(result, MonitorSnapshot):
            raise TypeError("刷新结果类型无效")
        self._last_snapshot = result
        self.process_model.set_views(result.views)
        self._apply_memory(result.memory)
        self._set_text("_process_count_text", f"{len(result.samples)} 个", self.processCountTextChanged)
        self.tableStateChanged.emit()
        self._update_timestamp_text()
        self._set_status("监控正常 · 点击表头排序，Ctrl+F 搜索")
        self._schedule_refresh()

    def _finish_release(self, result: object) -> None:
        if not isinstance(result, MemoryReleaseResult):
            raise TypeError("释放结果类型无效")
        self._apply_memory(result.after)
        self._set_status(
            f"已释放 {result.released_mb:,} MB · 处理 {result.processed_count} · 跳过 {result.skipped_count}"
        )
        self._show_notice(
            "内存释放完成",
            (
                f"本次释放 {result.released_mb:,} MB\n\n"
                f"成功处理  {result.processed_count} 个进程\n"
                f"安全跳过  {result.skipped_count} 个进程\n"
                f"处理失败  {result.failed_count} 个进程\n"
                f"耗时  {result.duration_seconds:.2f} 秒\n\n"
                "Windows 可能按需重新载入页面，数值会随使用继续变化。"
            ),
        )
        QTimer.singleShot(240, self.refresh)

    def _apply_memory(self, memory: MemorySnapshot) -> None:
        percent = clamp_percent(memory.used_percent)
        self._set_text("_usage_text", f"{percent:.0f}%", self.usageTextChanged)
        if percent != self._usage_percent:
            self._usage_percent = percent
            self.usagePercentChanged.emit()
        self._set_text(
            "_used_text",
            f"{format_gb(memory.used_bytes)} / {format_gb(memory.total_bytes)}",
            self.usedTextChanged,
        )
        self._set_text("_available_text", format_gb(memory.available_bytes), self.availableTextChanged)

    def _update_timestamp_text(self) -> None:
        stamp = dt.datetime.now().strftime("%H:%M:%S")
        self._set_text(
            "_updated_text",
            f"{stamp} 更新 · 当前显示 {self.process_model.visible_count} 行",
            self.updatedTextChanged,
        )

    def _show_notice(self, title: str, body: str) -> None:
        self._notice_title = title
        self._notice_body = body
        self._notice_visible = True
        self.noticeChanged.emit()

    def _schedule_refresh(self) -> None:
        if not self._closed:
            self._refresh_timer.start()

    def _set_status(self, text: str) -> None:
        self._set_text("_status_text", text, self.statusTextChanged)

    def _set_busy(self, busy: bool) -> None:
        if busy != self._busy:
            self._busy = busy
            self.busyChanged.emit()

    def _set_text(self, attribute: str, value: str, signal: Signal) -> None:
        if getattr(self, attribute) != value:
            setattr(self, attribute, value)
            signal.emit()


class MiniController(QObject):
    usageTextChanged = Signal()
    usagePercentChanged = Signal()
    availableTextChanged = Signal()
    statusTextChanged = Signal()
    busyChanged = Signal()
    deepCleanStateChanged = Signal()
    quitRequested = Signal()

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self.api = WindowsApi()
        self.monitor = ProcessMonitor(self.api)
        self.release_service = MemoryReleaseService(self.api)
        self.deep_clean_service = DeepCleanService(self.api)
        self.usage_tracker = AppUsageTracker()
        self.settings_store = SettingsStore()
        self._executor = concurrent.futures.ThreadPoolExecutor(max_workers=1, thread_name_prefix="memory-mini-qt")
        self._future: concurrent.futures.Future[object] | None = None
        self._future_kind = ""
        self._pending_release = False
        self._pending_deep_preview = False
        self._deep_clean_plan: DeepCleanPlan | None = None
        self._closed = False
        self._usage_text = "—%"
        self._usage_percent = 0.0
        self._available_text = "正在读取"
        self._status_text = "正在连接系统状态"
        self._busy = False
        self._deep_clean_minutes = self.settings_store.load_deep_clean_minutes()
        self._deep_clean_preview_text = "正在记录程序使用时间"
        self._deep_clean_candidate_names = "启动前的使用历史不会被猜测"
        self._deep_clean_preview_busy = False

        self._poll_timer = QTimer(self)
        self._poll_timer.setInterval(40)
        self._poll_timer.timeout.connect(self._poll_future)
        self._refresh_timer = QTimer(self)
        self._refresh_timer.setInterval(REFRESH_INTERVAL_MS)
        self._refresh_timer.setSingleShot(True)
        self._refresh_timer.timeout.connect(self.refresh)
        self._usage_timer = QTimer(self)
        self._usage_timer.setInterval(1_000)
        self._usage_timer.timeout.connect(self._observe_app_usage)
        self._usage_timer.start()
        QTimer.singleShot(0, self._observe_app_usage)

    @Property(str, notify=usageTextChanged)
    def usageText(self) -> str:
        return self._usage_text

    @Property(float, notify=usagePercentChanged)
    def usagePercent(self) -> float:
        return self._usage_percent

    @Property(str, notify=availableTextChanged)
    def availableText(self) -> str:
        return self._available_text

    @Property(str, notify=statusTextChanged)
    def statusText(self) -> str:
        return self._status_text

    @Property(bool, notify=busyChanged)
    def busy(self) -> bool:
        return self._busy

    @Property(int, notify=deepCleanStateChanged)
    def deepCleanMinutes(self) -> int:
        return self._deep_clean_minutes

    @Property(str, notify=deepCleanStateChanged)
    def deepCleanPreviewText(self) -> str:
        return self._deep_clean_preview_text

    @Property(str, notify=deepCleanStateChanged)
    def deepCleanCandidateNames(self) -> str:
        return self._deep_clean_candidate_names

    @Property(bool, notify=deepCleanStateChanged)
    def deepCleanPreviewBusy(self) -> bool:
        return self._deep_clean_preview_busy

    @Property(bool, notify=deepCleanStateChanged)
    def deepCleanCanRun(self) -> bool:
        plan = self._deep_clean_plan
        return bool(
            plan is not None
            and plan.threshold_minutes == self._deep_clean_minutes
            and plan.candidates
            and not self._deep_clean_preview_busy
            and self._future is None
        )

    @Slot()
    def refresh(self) -> None:
        if self._closed:
            return
        self._refresh_timer.stop()
        if self._future is not None:
            self._schedule_refresh()
            return
        self._start_future(
            "refresh",
            self.api.get_memory_snapshot,
            visible_busy=False,
        )

    @Slot()
    def releaseMemory(self) -> None:
        if self._closed:
            return
        if self._future is not None:
            if self._future_kind in {"refresh", "deep_preview"}:
                self._pending_release = True
            return
        self._refresh_timer.stop()
        self._set_status("正在安全释放…")
        self._start_future("release", self._release, visible_busy=True)

    def _release(self) -> MemoryReleaseResult:
        snapshot = self.monitor.sample(grouped=False)
        return self.release_service.release(snapshot.samples)

    @Slot(int)
    def setDeepCleanMinutes(self, minutes: int) -> None:
        value = self.settings_store.save_deep_clean_minutes(minutes)
        if value == self._deep_clean_minutes:
            return
        self._deep_clean_minutes = value
        self._deep_clean_plan = None
        self._deep_clean_preview_text = "时间已更新，正在重新检查…"
        self._deep_clean_candidate_names = ""
        self.deepCleanStateChanged.emit()

    @Slot()
    def prepareDeepClean(self) -> None:
        if self._closed:
            return
        self._deep_clean_preview_busy = True
        self._deep_clean_preview_text = "正在检查可安全关闭的程序…"
        self._deep_clean_candidate_names = ""
        self.deepCleanStateChanged.emit()
        if self._future is not None:
            self._pending_deep_preview = True
            return
        self._refresh_timer.stop()
        minutes = self._deep_clean_minutes
        self._start_future(
            "deep_preview",
            lambda: self._prepare_deep_clean(minutes),
            visible_busy=False,
        )

    def _prepare_deep_clean(self, minutes: int) -> DeepCleanPlan:
        snapshot = self.monitor.sample(grouped=False)
        return self.deep_clean_service.preview(snapshot.samples, self.usage_tracker, minutes)

    @Slot()
    def runDeepClean(self) -> None:
        if self._closed or self._future is not None:
            return
        plan = self._deep_clean_plan
        if plan is None or plan.threshold_minutes != self._deep_clean_minutes:
            self.prepareDeepClean()
            return
        self._refresh_timer.stop()
        self._set_status("正在发送正常关闭请求…")
        self._start_future(
            "deep_clean",
            lambda: self._run_deep_clean(plan),
            visible_busy=True,
        )

    def _run_deep_clean(self, plan: DeepCleanPlan) -> DeepCleanResult:
        snapshot = self.monitor.sample(grouped=False)
        return self.deep_clean_service.execute(plan, snapshot.samples, self.usage_tracker)

    @Slot()
    def openFullApp(self) -> None:
        if getattr(sys, "frozen", False):
            target = Path(sys.executable).with_name("MemoryPilot.exe")
            command = [str(target)]
            working_directory = target.parent
        else:
            command = [sys.executable, "-m", "memory_pilot"]
            working_directory = Path.cwd()
        try:
            subprocess.Popen(command, cwd=working_directory)
            self._set_status("已打开完整版")
        except OSError as exc:
            self._set_status(f"无法打开：{exc}")

    @Slot()
    def quit(self) -> None:
        self.shutdown()
        self.quitRequested.emit()

    @Slot()
    def shutdown(self) -> None:
        if self._closed:
            return
        self._closed = True
        self._refresh_timer.stop()
        self._usage_timer.stop()
        self._poll_timer.stop()
        self._executor.shutdown(wait=False, cancel_futures=True)

    def _start_future(
        self,
        kind: str,
        operation: Callable[[], object],
        *,
        visible_busy: bool,
    ) -> None:
        if visible_busy:
            self._set_busy(True)
        self._future_kind = kind
        self._future = self._executor.submit(operation)
        self.deepCleanStateChanged.emit()
        self._poll_timer.start()

    @Slot()
    def _poll_future(self) -> None:
        future = self._future
        if future is None or not future.done():
            return
        self._poll_timer.stop()
        kind = self._future_kind
        self._future = None
        self._future_kind = ""
        self.deepCleanStateChanged.emit()
        if kind in {"release", "deep_clean"}:
            self._set_busy(False)
        try:
            result = future.result()
        except Exception as exc:
            self._set_status(f"操作失败：{exc}")
            if kind == "deep_preview":
                self._deep_clean_preview_busy = False
                self._deep_clean_preview_text = "检查失败，请稍后重试"
                self._deep_clean_candidate_names = str(exc)
                self.deepCleanStateChanged.emit()
            self._dispatch_pending_operation()
            self._schedule_refresh()
            return
        if kind == "refresh" and isinstance(result, MemorySnapshot):
            self._apply_memory(result)
            self._set_status("实时监测中")
        elif kind == "release" and isinstance(result, MemoryReleaseResult):
            self._apply_memory(result.after)
            self._set_status(f"已释放 {result.released_mb:,} MB")
        elif kind == "deep_preview" and isinstance(result, DeepCleanPlan):
            self._finish_deep_preview(result)
            if result.threshold_minutes != self._deep_clean_minutes:
                self._pending_deep_preview = True
        elif kind == "deep_clean" and isinstance(result, DeepCleanResult):
            self._finish_deep_clean(result)
        self._dispatch_pending_operation()
        self._schedule_refresh()

    def _finish_deep_preview(self, plan: DeepCleanPlan) -> None:
        self._deep_clean_preview_busy = False
        if plan.threshold_minutes != self._deep_clean_minutes:
            self._deep_clean_plan = None
            self.deepCleanStateChanged.emit()
            return
        self._deep_clean_plan = plan
        count = len(plan.candidates)
        if count:
            if plan.threshold_minutes == 0:
                self._deep_clean_preview_text = f"将请求关闭 {count} 个当前未使用的程序"
            else:
                self._deep_clean_preview_text = (
                    f"将请求关闭 {count} 个超过 {plan.threshold_minutes} 分钟未使用的程序"
                )
            names = list(plan.candidate_names[:4])
            self._deep_clean_candidate_names = "、".join(names)
            if count > len(names):
                self._deep_clean_candidate_names += f" 等 {count} 个"
        else:
            self._deep_clean_preview_text = "当前没有符合条件的普通桌面程序"
            self._deep_clean_candidate_names = "系统、后台服务和当前前台程序已自动跳过"
        self.deepCleanStateChanged.emit()

    def _finish_deep_clean(self, result: DeepCleanResult) -> None:
        self._deep_clean_plan = None
        self._deep_clean_preview_busy = False
        parts = [f"已向 {result.requested_count} 个程序发送关闭请求"]
        if result.skipped_count:
            parts.append(f"复核跳过 {result.skipped_count} 个")
        if result.failed_count:
            parts.append(f"失败 {result.failed_count} 个")
        summary = " · ".join(parts)
        self._deep_clean_preview_text = summary
        self._deep_clean_candidate_names = "目标程序仍可提示保存或取消关闭"
        self._set_status(f"深度清理：请求 {result.requested_count} 个")
        self.deepCleanStateChanged.emit()

    def _dispatch_pending_operation(self) -> None:
        if self._future is not None or self._closed:
            return
        if self._pending_release:
            self._pending_release = False
            QTimer.singleShot(0, self.releaseMemory)
        elif self._pending_deep_preview:
            self._pending_deep_preview = False
            QTimer.singleShot(0, self.prepareDeepClean)

    def _apply_memory(self, memory: MemorySnapshot) -> None:
        percent = clamp_percent(memory.used_percent)
        if self._usage_text != f"{percent:.0f}%":
            self._usage_text = f"{percent:.0f}%"
            self.usageTextChanged.emit()
        if self._usage_percent != percent:
            self._usage_percent = percent
            self.usagePercentChanged.emit()
        available = f"可用 {format_gb(memory.available_bytes)}"
        if self._available_text != available:
            self._available_text = available
            self.availableTextChanged.emit()

    def _set_status(self, text: str) -> None:
        if self._status_text != text:
            self._status_text = text
            self.statusTextChanged.emit()

    def _set_busy(self, busy: bool) -> None:
        if self._busy != busy:
            self._busy = busy
            self.busyChanged.emit()

    @Slot()
    def _observe_app_usage(self) -> None:
        if self._closed:
            return
        try:
            self.deep_clean_service.observe_usage(self.usage_tracker)
        except (OSError, RuntimeError):
            pass

    def _schedule_refresh(self) -> None:
        if not self._closed:
            self._refresh_timer.start()
