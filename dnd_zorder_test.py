# -*- coding: utf-8 -*-
"""「显示在最前 + 全屏免打扰」双开回归：前台被 clippy 占据时，
仍能经 Z 序遍历发现真全屏窗口（GetForegroundWindow 漏判修复）。"""
import ctypes
import os
import tempfile
import time
import tkinter as tk

import clippy_pet as cp

cp.SETTINGS_FILE = os.path.join(tempfile.mkdtemp(), "z.json")
pet = cp.ClippyPet()
pet.root.update()
pet.dnd_on = True            # 双开：免打扰 + 置顶
pet.pin_on = True
pet.root.wm_attributes("-topmost", True)
pet.root.update()

u = ctypes.windll.user32
orig_fg = u.GetForegroundWindow

# 1. 无全屏窗口，前台=clippy → 非全屏
u.GetForegroundWindow = lambda: int(pet.root.winfo_id())
pet.root.update()
assert pet._is_fullscreen() is False
print("NO-FULL OK")

# 2. 创建真全屏窗口；前台仍=clippy → 经 Z 序遍历应发现全屏
sw = pet.root.winfo_screenwidth()
sh = pet.root.winfo_screenheight()
full = tk.Toplevel(pet.root)
full.overrideredirect(True)
full.geometry("%dx%d+0+0" % (sw, sh))
full.configure(bg="black")
full.attributes("-topmost", True)   # 置顶全屏：Z 序高于其他应用窗口
full.update()
pet.root.update()
time.sleep(0.3)
pet.root.update()
assert pet._is_fullscreen() is True, "双开时全屏被漏判"
print("ZORDER-FULL OK")

# 3. 关闭全屏窗口 → 恢复非全屏
full.destroy()
pet.root.update()
time.sleep(0.3)
pet.root.update()
assert pet._is_fullscreen() is False
print("ZORDER-CLEAR OK")

u.GetForegroundWindow = orig_fg
pet._do_exit()
print("ZORDER OK")
