# Memory Pilot Implementation Plan

## Architecture

```text
Tkinter UI
  -> ProcessMonitor (sampling, grouping, filtering)
  -> MemoryReleaseService (safe orchestration)
      -> WindowsApi (ctypes-only platform boundary)
```

The UI owns presentation state only. Core services use immutable models and depend on an injected Windows API adapter so unit tests never trim real processes.

## Implementation Order

1. Scaffold the package, immutable models, and test harness.
2. Build the Windows API adapter for memory status, process enumeration, process memory/CPU sampling, and documented working-set trimming.
3. Build process aggregation, protection rules, filtering, sorting, and cleanup orchestration.
4. Build the accessible Tkinter interface with a compact Windows-style visual system.
5. Add packaging metadata, application manifest, documentation, attribution, and license.
6. Run unit tests, syntax checks, live read-only sampling, controlled cleanup verification, EXE build, and EXE launch smoke test.

## Dependencies

- Steps 2 and 3 depend on the models from step 1.
- Step 4 depends on stable service interfaces from steps 2 and 3.
- Packaging depends on the working application and passing tests.
- Only PyInstaller is downloaded. Its package files and pip cache must be stored under `E:\软件工作盘\MemoryPilot`.

## UI Direction

- Compact utility layout optimized for scanning, not a card-heavy dashboard.
- Neutral Windows palette with blue as the single action color.
- Header: product name, live memory summary, refresh state.
- Toolbar: search, grouped/PID view switch, manual refresh.
- Main area: sortable Treeview with name, PID/count, status, CPU, memory, path.
- Footer: one primary “安全释放内存” button and an accessible result/status region.
- Text labels accompany every color-coded status.

## Risks and Mitigations

1. **Permission failures:** protected processes reject access. Treat as expected skips, never fatal errors.
2. **Misleading reclaimed-memory values:** sample before and after with a short bounded wait, report zero honestly, and explain that Windows can reload pages.
3. **UI freezes:** process sampling and cleanup run on worker threads; Tkinter updates stay on the UI thread.
4. **CPU percentage noise:** calculate deltas between snapshots and clamp invalid values.
5. **Over-cleaning:** protect critical processes and the application itself; no automatic cleanup loop.
6. **Packaging size:** use standard library only at runtime and a clean PyInstaller one-directory/one-file evaluation before choosing the smaller reliable artifact.
7. **License contamination:** implement from scratch, include links and acknowledgements, copy no GPL source.

## Verification Checkpoints

- Checkpoint A: models and pure rules pass unit tests.
- Checkpoint B: live process sampling returns rows without administrator rights.
- Checkpoint C: mocked cleanup proves protected processes are always skipped.
- Checkpoint D: GUI opens, refreshes, filters, sorts, and remains keyboard operable.
- Checkpoint E: controlled cleanup reports before/after values without terminating processes.
- Checkpoint F: packaged EXE starts on this computer and keeps idle usage below the specified target where practical.

## Download and Build Locations

- Project: `E:\软件工作盘\MemoryPilot`
- Downloaded Python packages: `E:\软件工作盘\MemoryPilot\.tools`
- pip cache: `E:\软件工作盘\MemoryPilot\.cache\pip`
- PyInstaller work/cache: `E:\软件工作盘\MemoryPilot\build`
- Final artifact: `E:\软件工作盘\MemoryPilot\dist`

## Deep Clean Extension

1. Extend the ctypes boundary with read-only foreground/top-level-window discovery and non-forcing `WM_CLOSE` posting.
2. Add a monotonic foreground-usage tracker, protected candidate planner, execution-time revalidation, and truthful close-request results.
3. Persist only the 0–60 minute setting in local app data; never persist or infer stale usage history across app downtime.
4. Add an accessible compact QML confirmation panel and a “深度清理” button in the requested mini-widget gap without increasing the window size.
5. Unit-test all eligibility and revalidation boundaries; use only a controlled disposable test window for any live close verification.
6. Bump the patch version, rebuild both installed EXEs in place, preserve both desktop shortcuts, and leave GitHub unchanged unless separately requested.

### Deep Clean Risks

- **Unsaved work:** use `WM_CLOSE` only so the target application can prompt to save or cancel; never force termination.
- **Unknown pre-launch history:** initialize every visible app at launch time and make it wait for the selected threshold.
- **Race after preview:** re-read foreground state and last-use timestamps immediately before posting each close request.
- **Closing background services:** require a normal visible top-level app window and existing `USER_APP` classification.
- **Zero-minute scope:** show candidate count/names and require a second explicit confirmation.
- **Stale PID reuse:** retain only currently visible PIDs and rebuild candidates from a fresh process/window snapshot.

## Unified Mini Mode Extension

1. Make `MemoryPilot.exe` dispatch `--mini` to the existing QML mini runtime while keeping the default dashboard path unchanged.
2. Add named-event IPC beside the existing singleton mutex so the dashboard can request a graceful mini shutdown and read actual running state.
3. Add a small mini-mode manager and dashboard state machine for start, stop, transition timeout, and external-exit reconciliation.
4. Place an accessible “迷你悬浮窗” switch in the dashboard header using the existing neutral-blue design language.
5. Keep the legacy mini shortcut but retarget it to `MemoryPilot.exe --mini`; retain `MemoryPilotMini.exe` for one compatibility release only.
6. Bump to 0.2.6, rebuild in place, verify one-EXE start/stop, shortcuts, QML, and existing mini window behavior; do not publish GitHub automatically.

### Unified Mini Mode Risks

- **Start/stop race:** maintain a desired state with a bounded transition window and reconcile against the named mutex.
- **Force termination:** use a named event consumed by the mini Qt process; never call `TerminateProcess` or `Stop-Process` from product code.
- **Stale switch state:** poll the mutex and update the switch when the mini exits from its own menu.
- **Broken legacy entry:** preserve the desktop shortcut name while changing only target arguments to the unified executable.

## Mini Widget Extension

1. Add testable work-area positioning helpers and Windows tool-window style handling.
2. Build a focused Tkinter mini widget that reuses the existing Windows API, monitor, release service, theme, and logo.
3. Add a dedicated frozen entry point and `MemoryPilotMini.spec` without changing the full application entry point.
4. Rebuild both executables in place, keep the original shortcut target unchanged, and add one new mini-widget shortcut.
5. Verify syntax, unit tests, EXE resources, single-instance behavior, shortcut targets, and hidden-window/taskbar styles.

### Mini Widget Risks

- **Taskbar or Alt-Tab leakage:** apply `WS_EX_TOOLWINDOW`, clear `WS_EX_APPWINDOW`, and verify the native extended style.
- **Widget off-screen:** calculate position from the Windows work area rather than raw screen resolution.
- **Duplicate widgets:** hold a named Windows mutex for the process lifetime.
- **UI stalls during cleanup:** keep process enumeration and working-set trimming on the existing worker-thread pattern.
- **Accidental loss of the full app:** package to a second EXE and preserve `MemoryPilot.exe` plus its existing shortcut.
