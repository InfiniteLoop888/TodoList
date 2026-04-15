"""
开机自启动支持：
Windows：写入当前用户「运行」注册表项。
Linux：在用户的 ~/.config/autostart/ 目录下生成 .desktop 文件。
macOS：在用户的 ~/Library/LaunchAgents/ 目录下生成 .plist 文件。
"""

import os
import sys
from dataclasses import dataclass
from typing import List

APP_NAME = "MyTODOs"

@dataclass(frozen=True)
class StartupStatus:
    supported: bool
    enabled: bool
    expected_command: str
    actual_command: str = ""
    error: str = ""

def startup_supported() -> bool:
    return sys.platform in ("win32", "linux", "darwin")

def _pythonw_if_available(py: str) -> str:
    """无控制台启动 GUI：优先用同目录 pythonw.exe，避免登录自启弹出终端。"""
    base, name = os.path.split(py)
    if name.lower() != "python.exe":
        return py
    pyw = os.path.join(base, "pythonw.exe")
    return pyw if os.path.isfile(pyw) else py

def _launch_command_list() -> List[str]:
    """返回启动命令作为字符串列表（用于 macOS plist）"""
    if getattr(sys, "frozen", False):
        exe = os.path.abspath(sys.executable)
        return [exe]
    script = os.path.abspath(sys.argv[0])
    if sys.platform == "win32":
        py = _pythonw_if_available(os.path.abspath(sys.executable))
    else:
        py = os.path.abspath(sys.executable)
    return [py, script]

def _launch_command() -> str:
    """返回作为字符串的完整启动命令（用于 Windows 和 Linux）"""
    cmd_list = _launch_command_list()
    # 简单转义处理，如果有空格加上双引号
    return " ".join([f'"{arg}"' if " " in arg else arg for arg in cmd_list])

def _normalize_command(command: str) -> str:
    return " ".join(str(command).strip().split()).casefold()

# ========== Windows ==========

REG_RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
APP_VALUE_NAME = APP_NAME

def _get_startup_status_windows(expected: str) -> StartupStatus:
    import winreg
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_RUN_KEY, 0, winreg.KEY_READ)
        try:
            value, _ = winreg.QueryValueEx(key, APP_VALUE_NAME)
        except FileNotFoundError:
            return StartupStatus(True, False, expected)
        finally:
            winreg.CloseKey(key)
    except OSError as exc:
        return StartupStatus(True, False, expected, error=str(exc))

    actual = str(value).strip()
    enabled = bool(actual) and _normalize_command(actual) == _normalize_command(expected)
    return StartupStatus(True, enabled, expected, actual_command=actual)

def _set_startup_enabled_windows(enabled: bool, expected: str) -> StartupStatus:
    import winreg
    try:
        key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, REG_RUN_KEY)
        if enabled:
            winreg.SetValueEx(key, APP_VALUE_NAME, 0, winreg.REG_SZ, expected)
        else:
            try:
                winreg.DeleteValue(key, APP_VALUE_NAME)
            except FileNotFoundError:
                pass
    except OSError as exc:
        current = _get_startup_status_windows(expected)
        return StartupStatus(True, current.enabled, expected, actual_command=current.actual_command, error=str(exc))
    finally:
        try:
            winreg.CloseKey(key)
        except UnboundLocalError:
            pass
    return _get_startup_status_windows(expected)

# ========== Linux ==========

def _get_linux_desktop_file_path() -> str:
    return os.path.expanduser(f"~/.config/autostart/{APP_NAME}.desktop")

def _get_startup_status_linux(expected: str) -> StartupStatus:
    desktop_file = _get_linux_desktop_file_path()
    if not os.path.isfile(desktop_file):
        return StartupStatus(True, False, expected)
    
    try:
        with open(desktop_file, "r", encoding="utf-8") as f:
            content = f.read()
            # 简单判断是否包含 Exec 且指向预期的命令
            for line in content.splitlines():
                if line.startswith("Exec="):
                    actual = line.split("=", 1)[1].strip()
                    enabled = _normalize_command(actual) == _normalize_command(expected)
                    return StartupStatus(True, enabled, expected, actual_command=actual)
        return StartupStatus(True, False, expected)
    except Exception as exc:
        return StartupStatus(True, False, expected, error=str(exc))

def _set_startup_enabled_linux(enabled: bool, expected: str) -> StartupStatus:
    desktop_file = _get_linux_desktop_file_path()
    if not enabled:
        if os.path.exists(desktop_file):
            try:
                os.remove(desktop_file)
            except OSError as exc:
                return StartupStatus(True, True, expected, error=str(exc))
        return _get_startup_status_linux(expected)
    
    # 开启自启动
    os.makedirs(os.path.dirname(desktop_file), exist_ok=True)
    desktop_content = f"""[Desktop Entry]
Type=Application
Exec={expected}
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
Name={APP_NAME}
Comment={APP_NAME} Autostart
"""
    try:
        with open(desktop_file, "w", encoding="utf-8") as f:
            f.write(desktop_content)
    except Exception as exc:
        return StartupStatus(True, False, expected, error=str(exc))
    
    return _get_startup_status_linux(expected)

# ========== macOS ==========

def _get_macos_plist_file_path() -> str:
    return os.path.expanduser(f"~/Library/LaunchAgents/com.{APP_NAME.lower()}.app.plist")

def _get_startup_status_macos(expected: str) -> StartupStatus:
    plist_file = _get_macos_plist_file_path()
    if not os.path.isfile(plist_file):
        return StartupStatus(True, False, expected)
    
    try:
        with open(plist_file, "r", encoding="utf-8") as f:
            content = f.read()
            enabled = "<key>ProgramArguments</key>" in content
            return StartupStatus(True, enabled, expected)
    except Exception as exc:
        return StartupStatus(True, False, expected, error=str(exc))

def _set_startup_enabled_macos(enabled: bool, expected: str) -> StartupStatus:
    plist_file = _get_macos_plist_file_path()
    if not enabled:
        if os.path.exists(plist_file):
            try:
                os.remove(plist_file)
            except OSError as exc:
                return StartupStatus(True, True, expected, error=str(exc))
        return _get_startup_status_macos(expected)
    
    os.makedirs(os.path.dirname(plist_file), exist_ok=True)
    cmd_list = _launch_command_list()
    import html
    args_xml = "\\n        ".join(f"<string>{html.escape(arg)}</string>" for arg in cmd_list)
    
    plist_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.{APP_NAME.lower()}.app</string>
    <key>ProgramArguments</key>
    <array>
        {args_xml}
    </array>
    <key>RunAtLoad</key>
    <true/>
</dict>
</plist>
"""
    try:
        with open(plist_file, "w", encoding="utf-8") as f:
            f.write(plist_content)
    except Exception as exc:
        return StartupStatus(True, False, expected, error=str(exc))
    
    return _get_startup_status_macos(expected)


# ========== 暴露的接口 ==========

def get_startup_status() -> StartupStatus:
    expected = _launch_command()
    if not startup_supported():
        return StartupStatus(False, False, expected)
    
    if sys.platform == "win32":
        return _get_startup_status_windows(expected)
    elif sys.platform == "linux":
        return _get_startup_status_linux(expected)
    elif sys.platform == "darwin":
        return _get_startup_status_macos(expected)
    
    return StartupStatus(False, False, expected)

def is_startup_enabled() -> bool:
    return get_startup_status().enabled

def set_startup_enabled(enabled: bool) -> StartupStatus:
    expected = _launch_command()
    if not startup_supported():
        return StartupStatus(False, False, expected)
    
    if sys.platform == "win32":
        return _set_startup_enabled_windows(enabled, expected)
    elif sys.platform == "linux":
        return _set_startup_enabled_linux(enabled, expected)
    elif sys.platform == "darwin":
        return _set_startup_enabled_macos(enabled, expected)

    return get_startup_status()
