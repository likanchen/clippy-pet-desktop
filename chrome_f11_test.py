# -*- coding: utf-8 -*-
"""Chrome F11 全屏判定验证：带 WS_MAXIMIZE 样式的全屏窗口应判全屏；
普通最大化窗口（未覆盖任务栏区域）应判非全屏。"""
import ctypes
import os
import tempfile
import time
import tkinter as tk
from ctypes import wintypes

import clippy_pet as cp

cp.SETTINGS_FILE = os.path.join(tempfile.mkdtemp(), "c.json")
pet = cp.ClippyPet()
pet.root.update()

u = ctypes.windll.user32
u.GetWindowLongW.restype = wintypes.LONG


def root_hwnd(w):
    return u.GetAncestor(w.winfo_id(), 2)


# 1. 普通最大化窗口（800x600 zoomed）→ 非全屏（未覆盖任务栏区域）
top = tk.Toplevel(pet.root)
top.title("max")
top.geometry("800x600+50+50")
top.update()
top.state("zoomed")
pet.root.update()
time.sleep(0.3)
pet.root.update()
mh = cp.ClippyPet._hwnd_is_fullscreen(root_hwnd(top))
print("最大化窗口判全屏 =", mh)
assert mh is False, "普通最大化窗口被误判为全屏"
print("MAX OK")

# 2. Chrome F11 全屏模拟：无边框全屏窗口 + 强制加 WS_MAXIMIZE 样式
sw = pet.root.winfo_screenwidth()
sh = pet.root.winfo_screenheight()
full = tk.Toplevel(pet.root)
full.overrideredirect(True)
full.geometry("%dx%d+0+0" % (sw, sh))
full.configure(bg="black")
full.update()
pet.root.update()
time.sleep(0.3)
pet.root.update()
fh = root_hwnd(full)
style = u.GetWindowLongW(fh, -16)
u.SetWindowLongW(fh, -16, style | 0x01000000)   # 模拟 Chrome F11 的 WS_MAXIMIZE
pet.root.update()
time.sleep(0.3)
pet.root.update()
ok = cp.ClippyPet._hwnd_is_fullscreen(fh)
print("Chrome F11 模拟（带 WS_MAXIMIZE 的全屏）判全屏 =", ok)
assert ok is True, "Chrome F11 全屏未被识别（WS_MAXIMIZE 误排除）"
print("CHROME-F11 OK")

pet._do_exit()
print("F11 OK")
