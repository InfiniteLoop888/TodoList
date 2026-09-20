import os
import sys

import numpy


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

class IconDictionary:
    def __init__(self, library_path=data_file_path, color=None):

        # ！注意！  你不应使用这些文件，他们已经过加密处理
        # 如果你需要这些图标文件，你可以直接在 flaticon.com 免费获取他们

        # 读取数据并解密
        f = open(library_path, 'rb')
        library_raw = f.read()
        library_list = list(library_raw)
        library = bytes(list((numpy.array(library_list) + numpy.array(range(len(library_list))) * 17) % 255)).decode()  # 解密

        # 整理成字典
        items = library.split('!!!')
        names = []
        datas = []
        for item in items[1:]:
            name, data = item.split('###')
            data = data.replace('/>', ' fill="{}" />'.format(color))
            names.append(name)
            datas.append(data.encode())
        self.icons = dict(zip(names, datas))

    def get(self, name):
        svg_data = self.icons[name]
        return svg_data.encode()
