"""
用户配置目录：系统「文档」文件夹下的 TodoList（Windows 即「文档」/ 资源管理器中的「我的文档」）。
首次运行时若该目录或 ini 不存在，则从程序所在目录复制同名文件，便于升级版本后保留设置。

每次将 ini 写入用户目录后，会同步复制一份到程序目录（见 mirror_user_ini_to_application_dir），
便于开发时直接看到项目根目录下的 options.ini / todos.ini 与运行态一致。
"""

import shutil
import sys
from pathlib import Path
from typing import Optional, Tuple

_OPTIONS_NAME = "options.ini"
_TODOS_NAME = "todos.ini"


def application_dir() -> Path:
    """可执行文件或脚本所在目录（打包后与 exe 同目录）。"""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


def documents_dir() -> Path:
    try:
        from PyQt5.QtCore import QStandardPaths

        p = QStandardPaths.writableLocation(QStandardPaths.DocumentsLocation)
        if p:
            return Path(p)
    except Exception:
        pass
    return Path.home() / "Documents"


def user_config_dir() -> Path:
    return documents_dir() / "TodoList"


def _default_options_ini_text() -> str:
    """程序目录与打包目录均无 options.ini 时的兜底内容（与仓库默认一致）。"""
    return (
        "FIXED_POSITION = False\n"
        "USE_DARK_MODE = False\n"
        "FIXED_POSITION_X = 928\n"
        "FIXED_POSITION_Y = -18\n"
        "HAS_CUSTOM_POSITION = True\n"
        "TRANSLUCENT_MODE = True\n"
        "TRANSLUCENT_OPACITY = 95\n"
        "CALENDAR_MAXIMIZED = False\n"
        "CALENDAR_X = 66\n"
        "CALENDAR_Y = 90\n"
        "CALENDAR_WIDTH = 1011\n"
        "CALENDAR_HEIGHT = 733\n"
        "SETTINGS_MAXIMIZED = False\n"
        "SETTINGS_X = 180\n"
        "SETTINGS_Y = 120\n"
        "SETTINGS_WIDTH = 584\n"
        "SETTINGS_HEIGHT = 514\n"
        "TODO_ITEM_FONT_PX = 16\n"
    )


def ensure_user_ini_files() -> Tuple[str, str]:
    """
    确保「文档/TodoList」存在；若其中 options.ini / todos.ini 不存在，
    则优先从程序目录复制，否则写入合理默认值。
    返回 (options.ini 绝对路径, todos.ini 绝对路径)。
    """
    cfg = user_config_dir()
    cfg.mkdir(parents=True, exist_ok=True)
    app = application_dir()

    def ensure_one(filename: str, default_text: Optional[str]) -> str:
        dst = cfg / filename
        if dst.exists():
            return str(dst)
        src = app / filename
        if src.exists():
            shutil.copy2(src, dst)
            return str(dst)
        if default_text is not None:
            dst.write_text(default_text, encoding="utf-8")
        else:
            dst.write_text("", encoding="utf-8")
        return str(dst)

    opt = ensure_one(_OPTIONS_NAME, _default_options_ini_text())
    todo = ensure_one(_TODOS_NAME, None)
    return opt, todo


def mirror_user_ini_to_application_dir(user_file_path: str) -> None:
    """
    将已写入「文档/TodoList」下的 ini 复制到程序所在目录（同名文件）。
    源与目标为同一路径时跳过；复制失败时静默忽略（例如目录只读）。
    """
    try:
        src = Path(user_file_path).resolve()
        if not src.is_file():
            return
        dst = (application_dir() / src.name).resolve()
        if src == dst:
            return
        shutil.copy2(src, dst)
    except OSError:
        pass
