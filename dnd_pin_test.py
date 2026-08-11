# -*- coding: utf-8 -*-
"""置顶 + 全屏免打扰联合验证（hwnd 判定，不依赖前台焦点）。"""
import ctypes
import os
import tempfile
import time
import tkinter as tk

import clippy_pet as cp

cp.SETTINGS_FILE = os.path.join(tempfile.mkdtemp(), "dp.json")
pet = cp.ClippyPet()
pet.root.update()
pet.dnd_on = True            # 开启免打扰
pet.pin_on = True            # 开启置顶
pet.root.wm_attributes("-topmost", True)
pet.root.update()

u = ctypes.windll.user32


def root_hwnd(w):
    return u.GetAncestor(w.winfo_id(), 2)  # GA_ROOT


# 1. 置顶已生效
assert pet.root.wm_attributes("-topmost") == 1
print("PIN OK")

# 2. 最大化窗口 → 非全屏（WS_MAXIMIZE 排除）
top = tk.Toplevel(pet.root)
top.title("max")
top.geometry("800x600+50+50")
top.update()
top.state("zoomed")
pet.root.update()
time.sleep(0.3)
pet.root.update()
assert cp.ClippyPet._hwnd_is_fullscreen(root_hwnd(top)) is False, \
    "最大化窗口被误判为全屏"
print("MAX OK")

# 3. 真全屏窗口 → 全屏
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
assert cp.ClippyPet._hwnd_is_fullscreen(root_hwnd(full)) is True, \
    "真全屏未被识别"
print("FULL OK")

# 4. 模拟 DND 激活（withdraw）→ 隐藏
pet._dnd_active = True
pet.root.withdraw()
pet.root.update()
assert str(pet.root.state()) == "withdrawn", pet.root.state()
print("HIDE OK")

# 5. 恢复 → 显示且置顶保持（冲突核心）
pet._dnd_restore()
pet.root.update()
time.sleep(0.3)
pet.root.update()
assert pet._dnd_active is False, "未恢复"
assert str(pet.root.state()) != "withdrawn", pet.root.state()
topmost = pet.root.wm_attributes("-topmost")
print("恢复后 topmost =", topmost)
assert topmost == 1, "DND 恢复后置顶丢失"
print("RESTORE+PIN OK")

# 6. _dnd_apply_attrs 按 pin_on 重设置顶
pet.root.wm_attributes("-topmost", False)
pet.pin_on = True
pet._dnd_apply_attrs()
pet.root.update()
assert pet.root.wm_attributes("-topmost") == 1
pet.pin_on = False
pet._dnd_apply_attrs()
pet.root.update()
assert pet.root.wm_attributes("-topmost") == 0
pet.pin_on = True
pet._dnd_apply_attrs()
pet.root.update()
print("ATTRS OK")

pet._do_exit()
print("DND+PIN OK")
