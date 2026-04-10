"""
Windows 登录时自启动：写入当前用户「运行」注册表项。
非 Windows 平台不执行任何操作。
"""

import os
import sys
REG_RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
APP_VALUE_NAME = "MyTODOs"


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


def is_startup_enabled() -> bool:
    if not startup_supported():
        return False
    import winreg

    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_RUN_KEY, 0, winreg.KEY_READ)
        try:
            value, _ = winreg.QueryValueEx(key, APP_VALUE_NAME)
            return bool(value and str(value).strip())
        except FileNotFoundError:
            return False
        finally:
            winreg.CloseKey(key)
    except OSError:
        return False


def set_startup_enabled(enabled: bool) -> None:
    if not startup_supported():
        return
    import winreg

    cmd = _launch_command()
    key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_RUN_KEY, 0, winreg.KEY_SET_VALUE)
    try:
        if enabled:
            winreg.SetValueEx(key, APP_VALUE_NAME, 0, winreg.REG_SZ, cmd)
        else:
            try:
                winreg.DeleteValue(key, APP_VALUE_NAME)
            except FileNotFoundError:
                pass
    finally:
        winreg.CloseKey(key)
