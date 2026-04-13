"""
Windows 登录时自启动：写入当前用户「运行」注册表项。
非 Windows 平台不执行任何操作。
"""

import os
import sys
from dataclasses import dataclass
REG_RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
APP_VALUE_NAME = "MyTODOs"


@dataclass(frozen=True)
class StartupStatus:
    supported: bool
    enabled: bool
    expected_command: str
    actual_command: str = ""
    error: str = ""


def startup_supported() -> bool:
    return sys.platform == "win32"


def _pythonw_if_available(py: str) -> str:
    """无控制台启动 GUI：优先用同目录 pythonw.exe，避免登录自启弹出终端。"""
    base, name = os.path.split(py)
    if name.lower() != "python.exe":
        return py
    pyw = os.path.join(base, "pythonw.exe")
    return pyw if os.path.isfile(pyw) else py


def _launch_command() -> str:
    if getattr(sys, "frozen", False):
        exe = os.path.abspath(sys.executable)
        return f'"{exe}"'
    script = os.path.abspath(sys.argv[0])
    py = _pythonw_if_available(os.path.abspath(sys.executable))
    return f'"{py}" "{script}"'


def _normalize_command(command: str) -> str:
    return " ".join(str(command).strip().split()).casefold()


def get_startup_status() -> StartupStatus:
    expected = _launch_command()
    if not startup_supported():
        return StartupStatus(False, False, expected)

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


def is_startup_enabled() -> bool:
    return get_startup_status().enabled


def set_startup_enabled(enabled: bool) -> StartupStatus:
    if not startup_supported():
        return get_startup_status()
    import winreg

    cmd = _launch_command()
    try:
        key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, REG_RUN_KEY)
        if enabled:
            winreg.SetValueEx(key, APP_VALUE_NAME, 0, winreg.REG_SZ, cmd)
        else:
            try:
                winreg.DeleteValue(key, APP_VALUE_NAME)
            except FileNotFoundError:
                pass
    except OSError as exc:
        current = get_startup_status()
        return StartupStatus(
            current.supported,
            current.enabled,
            current.expected_command,
            actual_command=current.actual_command,
            error=str(exc),
        )
    finally:
        try:
            winreg.CloseKey(key)
        except UnboundLocalError:
            pass

    return get_startup_status()
