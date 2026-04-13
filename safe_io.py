import os
import shutil
import uuid
from pathlib import Path


def backup_path_for(path: str) -> Path:
    p = Path(path)
    return p.with_name(p.name + ".bak")


def read_text_if_exists(path: str, encoding: str = "utf-8") -> str:
    p = Path(path)
    if not p.exists():
        return ""
    return p.read_text(encoding=encoding)


def restore_backup(path: str) -> bool:
    src = backup_path_for(path)
    dst = Path(path)
    if not src.exists():
        return False
    shutil.copy2(src, dst)
    return True


def atomic_write_text(path: str, text: str, encoding: str = "utf-8", keep_backup: bool = True) -> None:
    dst = Path(path)
    dst.parent.mkdir(parents=True, exist_ok=True)
    tmp = dst.with_name(f".{dst.name}.{uuid.uuid4().hex}.tmp")

    with open(tmp, "w", encoding=encoding) as file:
        file.write(text)
        file.flush()
        os.fsync(file.fileno())

    if keep_backup and dst.exists():
        shutil.copy2(dst, backup_path_for(str(dst)))

    os.replace(tmp, dst)
