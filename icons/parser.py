import os
import sys

import numpy

_raw_icon_svgs = None
_raw_icon_path = None
_colored_icons = {}


def _icons_dat_path():
    """源码运行时在 icons/ 旁；打包后优先 _MEIPASS/icons，其次 exe 旁的 icons/。"""
    here = os.path.dirname(os.path.abspath(__file__))
    candidates = [os.path.join(here, "icons.dat")]
    if getattr(sys, "frozen", False):
        meipass = getattr(sys, "_MEIPASS", None)
        if meipass:
            candidates.append(os.path.join(meipass, "icons", "icons.dat"))
        exe_dir = os.path.dirname(os.path.abspath(sys.executable))
        candidates.append(os.path.join(exe_dir, "icons", "icons.dat"))
        candidates.append(os.path.join(exe_dir, "icons.dat"))
    for path in candidates:
        if os.path.isfile(path):
            return path
    return candidates[0]


data_file_path = _icons_dat_path()


def _load_raw_icons(library_path):
    """解密一次 icons.dat，缓存未着色的 SVG 文本。"""
    global _raw_icon_svgs, _raw_icon_path
    if _raw_icon_svgs is not None and _raw_icon_path == library_path:
        return _raw_icon_svgs

    # ！注意！  你不应使用这些文件，他们已经过加密处理
    # 如果你需要这些图标文件，你可以直接在 flaticon.com 免费获取他们
    with open(library_path, "rb") as f:
        library_raw = f.read()
    library_list = list(library_raw)
    library = bytes(
        list((numpy.array(library_list) + numpy.array(range(len(library_list))) * 17) % 255)
    ).decode()

    raw = {}
    for item in library.split("!!!")[1:]:
        name, data = item.split("###")
        raw[name] = data
    _raw_icon_svgs = raw
    _raw_icon_path = library_path
    return raw


class IconDictionary:
    def __init__(self, library_path=data_file_path, color=None):
        cache_key = (library_path, color)
        cached = _colored_icons.get(cache_key)
        if cached is not None:
            self.icons = cached
            return

        colored = {}
        for name, data in _load_raw_icons(library_path).items():
            colored[name] = data.replace("/>", ' fill="{}" />'.format(color)).encode()
        _colored_icons[cache_key] = colored
        self.icons = colored

    def get(self, name):
        svg_data = self.icons[name]
        return svg_data.encode()
