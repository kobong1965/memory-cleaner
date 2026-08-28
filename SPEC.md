# Spec: Memory Pilot（进程监控与一键内存释放）

## Assumptions

1. 目标平台是 Windows 10/11 x64，不支持 macOS、Linux 或 32 位 Windows。
2. 这是一个轻量原生桌面体验，不使用 Electron；采用 Python 3.11、PySide6、Qt Quick/QML 与 Windows API，最终打包成独立 EXE。
3. “合成”指在一个新软件中统一实现 System Informer 的核心进程查看能力和 Mem Reduct 的手动内存释放能力，而不是直接复制两个项目的全部源代码。
4. 首版不提供一键结束进程、禁用服务、清理注册表或删除文件，避免误伤当前工作和用户数据。
5. 内存释放默认只使用 Windows 可公开调用的进程工作集修剪能力；不调用未公开的系统内存列表接口，不清空待机列表。
6. 软件不联网、不上传进程信息、不收集遥测，也不在未经用户选择时开机自启。
7. “没有窗口”指迷你模式没有标题栏、边框和任务栏按钮，但仍保留可交互的桌面悬浮卡片。
8. 迷你模式作为独立 EXE 和独立桌面快捷方式提供；完整版、原安装位置和原快捷方式继续保留。
9. “程序多久未使用”以其普通顶层窗口最近一次成为前台窗口的时间计算；只记录 Memory Pilot 本次运行期间可观察到的活动，启动前历史一律视为未知并从当前时刻开始计时。
10. 深度清理只发送标准 `WM_CLOSE` 正常关闭请求，不调用强制终止进程 API；有未保存内容的程序可以自行显示保存确认并保持打开。

## Objective

构建一个中文 Windows 桌面工具，让普通用户能在同一个窗口中：

- 查看系统总内存、已用内存、可用内存和使用率。
- 查看各进程的名称、PID、内存、CPU、进程数量和风险分类。
- 搜索进程并按内存、CPU、名称排序。
- 点击一次按钮，安全修剪可访问进程的闲置工作集。
- 清楚看到释放前后内存、成功处理数量、跳过数量和错误原因。
- 识别系统关键进程并明确标记为“受保护”，不误导用户结束它们。

目标用户是经常同时运行 Codex、浏览器、办公软件、Ollama 和虚拟机，遇到内存压力与卡顿的 Windows 用户。

## Functional Requirements

### Dashboard

- 顶部显示总内存、已用内存、可用内存、使用率和最近更新时间。
- 主表格每 2 秒刷新一次，刷新期间保持搜索、排序和选中状态。
- 默认按总内存占用降序展示同名进程分组。
- 支持切换“按应用分组”和“显示单个 PID”。
- 支持搜索进程名称或 PID。
- 表格状态不能只依赖颜色，同时显示“用户应用”“系统进程”“受保护”等文字标签。

### One-click memory release

- 主按钮文案为“安全释放内存”。
- 点击后先采集基线，再修剪允许访问且不在保护名单中的进程工作集。
- 永不结束进程，永不停止服务，永不删除文件。
- 跳过当前软件自身、Windows 关键进程、受保护进程和访问被拒绝的进程。
- 完成后显示：释放前可用内存、释放后可用内存、差值、处理数量、跳过数量和耗时。
- 结果可能为零或短期回升；界面必须解释“Windows 可能重新载入被修剪的页面，这不是永久降低软件内存占用”。
- 普通权限可运行；权限不足时给出明确提示，并允许用户主动选择以管理员身份重新启动。不得默认请求管理员权限。

### Desktop mini widget

- 提供 `MemoryPilotMini.exe`，默认尺寸 286×158 像素，吸附到主屏幕工作区右上角并保留 16 像素边距；该高度需在当前 Windows 显示缩放下完整容纳按钮与状态文字。
- 使用无标题栏、无系统边框、无任务栏按钮的桌面悬浮卡片，并保持在普通窗口上方。
- 悬浮卡片不显示产品 Logo；视觉采用 2026 液态玻璃方向：霜白、冰蓝和浅青的克制渐变、轻微高光和约 96% 底色不透明度；圆角由 Qt Quick 矢量渲染并启用 Windows DWM 圆角，不使用逐像素透明色硬裁切。
- 数据使用 `Segoe UI Variable Display` 风格的大号数字，中文说明使用 `Microsoft YaHei UI`；文字对比度在浅色渐变上保持清晰。
- 内存进度使用横向液态渐变条作为唯一视觉重点；不添加多余图标、重阴影或装饰性卡片。
- 每 2 秒刷新内存使用率和当前可用内存；刷新失败时显示可理解的错误状态。
- 显示一个明确的“安全释放”按钮；清理时禁用重复点击，完成后显示真实释放量。
- 可按住卡片空白处拖动；右键菜单提供“打开完整版”和“退出迷你版”。
- 支持 `F5` 刷新、`Ctrl+L` 释放、`Ctrl+O` 打开完整版、`Shift+F10` 打开菜单、`Ctrl+Q` 退出。
- 同一时间只允许运行一个迷你版实例；重复打开时不创建第二个悬浮卡片。
- 不默认加入开机启动，不自动周期性清理内存。

### Deep clean inactive applications

- 迷你悬浮卡片在状态文字和“释放内存”之间增加“深度清理”按钮，不改变 286×158 外部尺寸。
- 点击按钮先打开确认面板，提供 0–60 分钟整数阈值，默认 60 分钟；设置保存在 `%LOCALAPPDATA%\MemoryPilot\settings.json`。
- 0 分钟表示预览所有当前未在前台、且满足其他保护条件的普通桌面程序；仍必须经过二次确认。
- 预览显示符合条件的程序数量和最多若干个程序名；阈值变化后重新计算预览，不能使用过期候选列表。
- 使用时间定义为普通顶层窗口最近一次成为前台窗口的时刻；Memory Pilot 启动时为所有已发现窗口建立安全基线，不能猜测启动前的使用历史。
- 仅考虑拥有可见、无所有者、非工具窗口且标题非空的普通顶层窗口；无窗口后台进程、Windows 服务和托盘后台进程不进入深度清理。
- 跳过当前前台程序、Memory Pilot 自身、Windows 核心/桌面进程、系统会话进程、访问受限进程及 Windows 系统目录程序。
- 执行前重新读取前台窗口和最近使用时间；若程序在预览后被用户再次使用，必须安全跳过。
- 关闭使用 `PostMessageW(hwnd, WM_CLOSE, 0, 0)`，不调用 `TerminateProcess`、`taskkill /F` 或等效强制终止接口。
- 完成后明确显示已发送关闭请求、因重新使用而跳过及请求失败的数量；不得把“已发送请求”误报为“已确认退出”。
- 深度清理只由用户手动触发，不按阈值自动定时关闭程序。
- 键盘支持 `Ctrl+D` 打开深度清理确认面板；滑块、取消和确认按钮具有可见焦点与可读辅助名称。

### Safety and accessibility

- 所有操作都可用键盘完成，并有可见焦点。
- 主要按钮、搜索框、表格和状态信息具有屏幕阅读器可理解的名称。
- 清理期间禁用重复点击，并显示进行中状态。
- Windows API 调用失败不能导致应用崩溃；错误应转换为用户可理解的信息。
- 不提供“自动每隔几分钟清理”；避免反复修剪造成应用重载和卡顿。
- 深度清理必须预览并二次确认，且仅做可被目标程序拒绝或拦截的正常关闭；不能绕过目标程序的未保存内容提示。

## Tech Stack

- Python 3.11 x64。
- PySide6 Essentials 6.11.2：Qt Quick/QML 桌面界面与矢量渲染。
- ctypes：调用 `GlobalMemoryStatusEx`、Tool Help、进程时间和 `EmptyWorkingSet` 等 Windows API。
- unittest：单元测试。
- PyInstaller 6.x：生成独立 Windows EXE，仅作为构建依赖。
- 许可证：MIT；代码从零实现，不复制 Mem Reduct GPL-3.0 源码。README 中注明功能参考了 System Informer 与 Mem Reduct，并链接原项目。

## Commands

在项目根目录运行：

```powershell
# 开发运行
$env:PYTHONPATH = ".tools;src"
python -m memory_pilot

# 语法检查
python -m compileall -q src tests

# 测试
python -m unittest discover -s tests -p "test_*.py" -v

# 安装界面与打包工具到项目盘
python -m pip install --target .tools PySide6_Essentials==6.11.2 "pyinstaller>=6.10,<7"

# 构建独立 EXE
python -m PyInstaller packaging/MemoryPilot.spec --noconfirm --clean
python -m PyInstaller packaging/MemoryPilotMini.spec --noconfirm --clean
```

## Project Structure

```text
memory-pilot/
  SPEC.md                         # 产品与技术规格
  README.md                       # 使用方法、安全说明、开源致谢
  LICENSE                         # MIT 许可证
  pyproject.toml                  # 包元数据与工具配置
  src/memory_pilot/
    __init__.py
    __main__.py                   # 应用入口
    mini.py                       # 迷你悬浮模式入口
    models.py                     # 进程、内存快照和清理结果模型
    core/
      deep_clean.py               # 前台使用跟踪、候选预览与正常关闭编排
      process_monitor.py          # 采样、聚合、过滤与排序
      memory_release.py           # 安全释放编排和保护规则
      settings.py                 # 深度清理分钟数的本地 JSON 设置
    platform/
      windows_api.py              # ctypes Windows API 封装
    ui/
      qt_bridge.py                # QML 数据模型、状态与异步操作桥
      qt_runtime.py               # Qt 应用启动、资源与窗口编排
      qml/Main.qml                # 完整版系统仪表台
      qml/Mini.qml                # 无边框桌面悬浮卡片
      qml/components/             # 玻璃面板、仪表和状态组件
      windowing.py                # 工作区定位与 Windows 窗口样式
  tests/
    test_deep_clean.py
    test_process_monitor.py
    test_memory_release.py
    test_protection_rules.py
  packaging/
    MemoryPilot.spec              # PyInstaller 配置
    MemoryPilotMini.spec          # 迷你版 PyInstaller 配置
    app.manifest                  # Windows 权限与兼容性声明
  tasks/
    plan.md
    todo.md
```

## Code Style

- 使用类型标注、`dataclass` 和小型纯函数；Windows API 封装与 UI 分离。
- 类名用 `PascalCase`，函数与变量用 `snake_case`，常量用 `UPPER_SNAKE_CASE`。
- UI 不直接调用 ctypes；UI 只消费领域模型和服务结果。

```python
@dataclass(frozen=True, slots=True)
class MemoryReleaseResult:
    available_before_mb: int
    available_after_mb: int
    processed_count: int
    skipped_count: int

    @property
    def released_mb(self) -> int:
        return max(0, self.available_after_mb - self.available_before_mb)
```

## Testing Strategy

- 单元测试覆盖进程分组、排序、CPU 差值计算、保护规则和释放结果计算。
- 深度清理测试覆盖前台使用计时、0/60 分钟边界、系统/当前/前台/无窗口保护、预览后重新使用保护，以及只发送 `WM_CLOSE` 的执行结果。
- Windows API 通过接口封装，在测试中使用假的快照和错误返回值，不对测试机真实进程执行清理。
- 集成测试验证普通权限下可启动、列表可刷新、访问拒绝被安全跳过。
- 纯函数测试覆盖右上角定位与边距计算；迷你版手工验收覆盖无边框、无任务栏按钮、置顶、拖动与快捷键。
- 手工验收测试覆盖键盘操作、125%/150% 缩放、浅色/深色模式、清理按钮防重复点击和高进程数量场景。
- 构建后对 EXE 进行启动测试，并记录空闲状态内存与 CPU。

## Boundaries

- Always：保护系统关键进程；清理前后测量；显示真实结果；运行测试；构建前检查许可证和致谢。
- Ask first：加入强制结束进程、开机自启、后台自动清理、系统托盘、服务控制或未公开 Windows API。
- Never：静默或强制结束进程；绕过未保存内容提示；关闭 Defender；禁用系统服务；删除用户文件；上传进程数据；复制 GPL 源码后仍以 MIT 发布。

## Success Criteria

- Windows 10/11 x64 上可以从单个 EXE 启动。
- 3 秒内显示首个进程与内存快照。
- 进程表可搜索、排序、分组，并每 2 秒静默刷新；后台采样不改变按钮、状态或色彩，也不整表重建造成闪动。
- “安全释放内存”不会结束任何进程，并能报告处理/跳过/失败明细。
- “深度清理”可按 0–60 分钟前台闲置阈值预览普通桌面程序，经二次确认后只发送正常关闭请求，并在执行瞬间重新保护刚被使用的程序。
- 系统进程或访问拒绝不会导致崩溃。
- Qt Quick 完整版空闲工作集目标小于 160MB，迷你版小于 130MB，平均 CPU 小于 1%。
- 无网络请求、无遥测、无默认自启。
- 所有自动化测试通过，最终 EXE 完成基本启动验收。
- 迷你版从独立快捷方式启动后位于工作区右上角，没有 Logo、标题栏或任务栏按钮，呈现半透明冰蓝—雾紫玻璃渐变，内容在当前显示缩放下不被裁切，且不会重复启动第二个实例。

## Open Questions

1. 软件名称是否使用“Memory Pilot / 内存领航员”？
2. 是否接受首版只做安全工作集修剪，不使用 Mem Reduct 的未公开 API 清空待机列表？
3. 是否接受从零实现并使用 MIT 许可证；还是必须直接复用 Mem Reduct 源码并将整个软件改为 GPL-3.0？
4. 首版是否确实不需要“结束选中进程”和“开机自动优化”？
