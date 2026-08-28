# Memory Pilot Task List

- [x] Task 1: Scaffold package and domain models
  - Acceptance: Application imports cleanly; immutable models represent memory, processes, grouped rows, and cleanup results.
  - Verify: `python -m compileall -q src tests` and model unit tests pass.
  - Files: `pyproject.toml`, `src/memory_pilot/__init__.py`, `src/memory_pilot/models.py`, `tests/test_models.py`

- [x] Task 2: Implement Windows API adapter
  - Acceptance: Adapter reads system memory, enumerates processes, samples per-process memory/times, resolves executable paths when allowed, and trims accessible working sets.
  - Verify: Wrapper tests pass; a read-only smoke command returns current process data.
  - Files: `src/memory_pilot/platform/__init__.py`, `src/memory_pilot/platform/windows_api.py`, `tests/test_windows_api.py`

- [x] Task 3: Implement monitoring, grouping, and protection rules
  - Acceptance: Consecutive snapshots produce CPU percentages; rows group by name; search/sort work; critical and current processes receive explicit protection status.
  - Verify: Unit tests cover grouping, filtering, CPU deltas, and protection cases.
  - Files: `src/memory_pilot/core/__init__.py`, `src/memory_pilot/core/process_monitor.py`, `src/memory_pilot/core/protection.py`, `tests/test_process_monitor.py`, `tests/test_protection_rules.py`

- [x] Task 4: Implement safe memory release service
  - Acceptance: Service never terminates processes, skips protected/inaccessible targets, and reports before/after/processed/skipped/failure details.
  - Verify: Mock-based unit tests prove only eligible PIDs reach the trim API.
  - Files: `src/memory_pilot/core/memory_release.py`, `tests/test_memory_release.py`

- [x] Task 5: Build accessible desktop UI
  - Acceptance: Dashboard, search, grouping toggle, sortable table, manual refresh, cleanup action, loading/error/empty states, and keyboard navigation work.
  - Verify: GUI smoke test plus keyboard-only manual walkthrough.
  - Files: `src/memory_pilot/ui/__init__.py`, `src/memory_pilot/ui/theme.py`, `src/memory_pilot/ui/app.py`, `src/memory_pilot/__main__.py`

- [x] Task 6: Package and document
  - Acceptance: README explains use and limitations; MIT license and upstream acknowledgements are present; manifest and PyInstaller configuration produce an EXE under `dist`.
  - Verify: Build command succeeds and artifact metadata is recorded.
  - Files: `README.md`, `LICENSE`, `packaging/app.manifest`, `packaging/MemoryPilot.spec`

- [x] Task 7: End-to-end verification
  - Acceptance: All tests and syntax checks pass; live sampling works; controlled cleanup does not terminate processes; packaged EXE launches; final size and idle resource usage are reported.
  - Verify: Execute the complete verification checklist and save results in `VERIFICATION.md`.
  - Files: `VERIFICATION.md`, `tasks/todo.md`

- [x] Task 8: Add mini-widget windowing helpers
  - Acceptance: Work-area positioning is deterministic; Windows tool-window styles hide taskbar/Alt-Tab presence; duplicate instances are rejected.
  - Verify: Unit tests cover positioning and an EXE smoke probe reads the expected native extended styles.
  - Files: `src/memory_pilot/ui/windowing.py`, `tests/test_windowing.py`

- [x] Task 9: Build the frameless mini widget
  - Acceptance: A compact 240×132 top-right card shows live memory without DPI clipping, safely releases memory, can be dragged, and exposes full-app/exit controls through a context menu and keyboard shortcuts.
  - Verify: Syntax/tests pass and the packaged widget remains responsive while refresh and cleanup run off the UI thread.
  - Files: `src/memory_pilot/ui/mini_app.py`, `src/memory_pilot/mini.py`, `src/memory_pilot/ui/theme.py`

- [x] Task 10: Package, install shortcuts, and verify both modes
  - Acceptance: `MemoryPilot.exe` is updated in place, `MemoryPilotMini.exe` is added, the original shortcut still targets the full app, and a new mini shortcut targets the mini EXE.
  - Verify: Build both specs, inspect hashes/icons/shortcuts, launch the mini EXE, confirm single-instance behavior, and record results in `VERIFICATION.md`.
  - Files: `packaging/MemoryPilot.spec`, `packaging/MemoryPilotMini.spec`, `README.md`, `VERIFICATION.md`, `tasks/todo.md`

- [x] Task 11: Redesign the mini widget as a 2026 liquid-glass card
  - Acceptance: The widget has no visible logo; it uses a restrained ice-blue-to-mist-purple semi-transparent gradient, rounded transparent corners, crisp typography, a liquid progress accent, and a glass pill release button.
  - Verify: Pure rendering helpers pass tests; a packaged screenshot confirms the full 268×140 layout, legible text, transparency, correct top-right placement, and unchanged interactions.
  - Files: `src/memory_pilot/ui/mini_app.py`, `tests/test_mini_visuals.py`, `SPEC.md`, `README.md`, `VERIFICATION.md`

- [x] Task 12: Repackage 0.2.1 and preserve desktop entry points
  - Acceptance: Both EXEs are rebuilt in place as 0.2.1; existing full and mini shortcuts keep their targets; the mini widget remains single-instance and frameless.
  - Verify: Full test suite, EXE build, native style probe, shortcut target check, screenshot review, and SHA-256 recording pass.
  - Files: `pyproject.toml`, `src/memory_pilot/__init__.py`, `packaging/app.manifest`, `README.md`, `VERIFICATION.md`, `tasks/todo.md`

- [x] Task 13: Replace jagged custom corners with native DWM corners
  - Acceptance: The glass card uses Windows-native anti-aliased rounded corners with no transparent-key stair-stepping or colored fringe; transparency, layout, interactions, and shortcuts remain unchanged.
  - Verify: Rendering tests pass; native DWM corner preference succeeds; a packaged screenshot at current DPI shows smooth edges on all four corners.
  - Files: `src/memory_pilot/ui/windowing.py`, `src/memory_pilot/ui/mini_app.py`, `tests/test_mini_visuals.py`, `SPEC.md`, `VERIFICATION.md`

- [x] Task 14: Migrate both interfaces to PySide6 and Qt Quick/QML
  - Acceptance: The dashboard and mini widget use QML vector rendering with a purpose-built design system; monitoring, grouping, search, sorting, safe release, keyboard shortcuts, drag/menu behavior, and single-instance protection remain functional; no Tkinter runtime path remains.
  - Verify: QML source smoke tests load both roots with live data; 25 automated tests run with one opt-in skip; both packaged EXEs launch through the preserved desktop shortcuts; native style probes and final screenshots pass.
  - Files: `src/memory_pilot/ui/qt_bridge.py`, `src/memory_pilot/ui/qt_runtime.py`, `src/memory_pilot/ui/qml/`, `packaging/MemoryPilot.spec`, `packaging/MemoryPilotMini.spec`, `README.md`, `VERIFICATION.md`

- [x] Task 15: Make automatic monitoring refresh visually silent
  - Acceptance: The two-second background sample never enters the cleanup busy state; changed rows update in place while reorder, insertion, and removal use incremental model signals without resetting the entire process model.
  - Verify: Model signal tests prove value, reorder, insertion, and removal refreshes emit no model reset; live controller probes show zero busy-state transitions across repeated automatic refreshes.
  - Files: `src/memory_pilot/ui/qt_bridge.py`, `src/memory_pilot/ui/qml/Main.qml`, `tests/test_qt_bridge.py`, `SPEC.md`, `VERIFICATION.md`

- [x] Task 16: Add safe inactive-application tracking and deep-clean planning
  - Acceptance: Visible app PIDs start from a safe current-time baseline; foreground use refreshes their timestamp; candidates honor the 0–60 minute threshold and all process/window protections.
  - Verify: Unit tests cover timing boundaries, foreground updates, protected classifications, and unknown-history behavior.
  - Files: `src/memory_pilot/models.py`, `src/memory_pilot/core/deep_clean.py`, `src/memory_pilot/platform/windows_api.py`, `tests/test_deep_clean.py`, `tests/test_windows_api.py`

- [x] Task 17: Add revalidated graceful-close execution and local settings
  - Acceptance: Execution rechecks current foreground/use state and only posts `WM_CLOSE`; the selected minute value persists as a clamped local JSON setting.
  - Verify: Fake-API tests prove no force-termination path exists, reactivated apps are skipped, failed posts are reported, and invalid setting files fall back safely.
  - Files: `src/memory_pilot/core/deep_clean.py`, `src/memory_pilot/core/settings.py`, `tests/test_deep_clean.py`, `tests/test_settings.py`

- [x] Task 18: Add the mini-widget deep-clean button and confirmation panel
  - Acceptance: The requested gap contains a compact “深度清理” button; an accessible panel previews candidate count/names, edits 0–60 minutes, and requires explicit confirmation without resizing the widget.
  - Verify: QML loads without errors; keyboard controls and `Ctrl+D` work; screenshots confirm no clipping, overlap, or refresh flicker.
  - Files: `src/memory_pilot/ui/qt_bridge.py`, `src/memory_pilot/ui/qml/Mini.qml`, `tests/test_qt_bridge.py`, `VERIFICATION.md`

- [x] Task 19: Package and verify Memory Pilot 0.2.5 in place
  - Acceptance: Both EXEs are rebuilt as 0.2.5, both desktop shortcuts remain unchanged, the mini stays single-instance/topmost/tool-window, and no GitHub upload occurs without a new explicit request.
  - Verify: Full automated suite, source and packaged QML smoke, controlled close probe, screenshot review, hashes, native style probe, and shortcut target checks pass.
  - Files: `pyproject.toml`, `src/memory_pilot/__init__.py`, `packaging/app.manifest`, `README.md`, `VERIFICATION.md`, `tasks/todo.md`
