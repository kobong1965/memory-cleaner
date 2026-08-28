# 内存清理器（Memory Pilot / 内存领航员）

Memory Pilot 是一个使用 PySide6 + Qt Quick/QML 构建的 Windows 进程监控与安全内存释放工具。它把进程占用查看和手动工作集修剪放在同一个现代中文界面中。

## 下载

普通用户请从 GitHub Releases 下载 `MemoryPilot.exe`（完整版）或 `MemoryPilotMini.exe`（右上角悬浮版）。两个 EXE 均已包含 Python 与 Qt Quick 运行组件，无需另外安装开发环境。

## 功能

- 查看总内存、已用内存、可用内存和使用率。
- 每两秒刷新进程名称、PID、CPU、内存、状态和程序位置。
- 按应用分组或显示单个 PID。
- 搜索并点击表头排序。
- 一键安全修剪可访问用户进程的闲置工作集。
- 提供无标题栏、无任务栏按钮的右上角半透明液态玻璃悬浮版。
- 自动保护 Windows 关键进程、本程序、访问受限进程和低占用进程。
- 完全离线，无遥测，无默认开机自启。

## 安全说明

“安全释放内存”不会结束进程、停止服务、修改注册表或删除文件。它调用 Windows 提供的 `EmptyWorkingSet`，让符合条件的用户进程归还当前不活跃的物理内存页面。

释放效果是临时且真实测量的。Windows 和应用可能随后按需重新载入页面，因此不建议频繁重复清理。长期卡顿应优先关闭不用的软件、取消不必要的开机启动或增加物理内存。

普通权限即可查看进程和处理部分用户进程。受保护或权限不足的进程会被安全跳过。

当前本地构建未使用商业代码签名证书。Windows 首次运行时可能显示“未知发布者”；请仅运行项目 `dist` 目录中由你自己构建并可用 SHA-256 校验的文件。

## 快捷键

- `Ctrl+F`：定位到搜索框。
- `F5`：立即刷新。
- `Ctrl+L`：安全释放内存。

## 迷你悬浮版

- 桌面快捷方式：`Memory Pilot 迷你悬浮版`。
- 默认位于主屏幕工作区右上角，尺寸 286×158，并保持置顶。
- 悬浮卡片不显示 Logo，使用霜白到冰蓝的半透明渐变、Qt Quick 矢量圆角、Windows DWM 圆角和液态内存进度条。
- 显示实时内存使用率、可用内存和“安全释放”按钮。
- 按住空白处可拖动；右键可打开完整版、刷新或退出。
- 快捷键：`F5` 刷新、`Ctrl+L` 释放、`Ctrl+O` 打开完整版、`Shift+F10` 菜单、`Ctrl+Q` 退出。
- 不加入开机启动；重复打开不会生成第二个组件。

## 从源码运行

```powershell
$env:PYTHONPATH = ".tools;src"
python -m memory_pilot
```

## 测试

```powershell
python -m compileall -q src tests
python -m unittest discover -s tests -t . -p "test_*.py" -v
```

## 构建

PySide6 Essentials 与 PyInstaller 是构建依赖；独立 EXE 已包含运行所需的 Qt Quick 组件。

```powershell
$env:PYTHONPATH = ".tools;src"
$env:PYINSTALLER_CONFIG_DIR = ".cache\pyinstaller"
$env:TEMP = ".cache\temp"
$env:TMP = ".cache\temp"
python -m PyInstaller packaging\MemoryPilot.spec --noconfirm --clean --distpath dist --workpath build
python -m PyInstaller packaging\MemoryPilotMini.spec --noconfirm --clean --distpath dist --workpath build
```

## 开源致谢

本项目从零实现，没有复制下列项目的源代码。产品方向参考了：

- [System Informer](https://github.com/winsiderss/systeminformer) — MIT，进程和系统资源分析工具。
- [Mem Reduct](https://github.com/henrypp/memreduct) — GPL-3.0，Windows 内存管理工具。

Memory Pilot 自身采用 MIT 许可证。

## 当前构建

- 版本：`0.2.3`
- 完整版：`dist\MemoryPilot.exe`
- 完整版 SHA-256：`A8425D6A2BF4E66CAB8A5B9B69AA252034F78BBDD860A8B69864F785260E8EEB`
- 迷你版：`dist\MemoryPilotMini.exe`
- 迷你版 SHA-256：`8F2A9D5DC48F9CA97855E7E47E32E9624634DC8BBAC81A71AC1D27799BDF85B0`
- 图标：`assets\memory-pilot-logo.png`
