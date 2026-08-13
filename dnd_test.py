# -*- coding: utf-8 -*-
"""全屏免打扰（DND）判定回归测试：
覆盖历史误判场景：最大化窗口、隐藏/最小化全屏窗口、后台全屏窗口。
"""
import os
import sys
import time
import tempfile
import ctypes
import tkinter as tk
from ctypes import wintypes

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import clippy_pet as cp

cp.SETTINGS_FILE = os.path.join(tempfile.mkdtemp(), "dnd_test.json")
pet = cp.ClippyPet()
pet.root.update()
u = ctypes.windll.user32
u.SetForegroundWindow.restype = wintypes.HWND
my = int(pet.root.winfo_id())


def root_hwnd(w):
    return u.GetAncestor(w.winfo_id(), 2)


def fg_clippy():
    """临时让 GetForegroundWindow 返回 clippy 自己，强制
    _is_fullscreen 走 Z 序遍历分支（Windows 前台锁定无法真实抢焦点）。"""
    u.GetForegroundWindow = lambda: my
    pet.root.update()


def restore_fg():
    u.GetForegroundWindow = orig_fg


orig_fg = u.GetForegroundWindow


def mk_fullscreen():
    w = tk.Toplevel(pet.root)
    w.overrideredirect(True)
    w.geometry("%dx%d+0+0" % (pet.root.winfo_screenwidth(),
                              pet.root.winfo_screenheight()))
    w.update()
    time.sleep(0.2)
    return w


sw, sh = pet.root.winfo_screenwidth(), pet.root.winfo_screenheight()

# --- 1) 无边框真全屏窗口 → 判定为全屏
fs = mk_fullscreen()
assert cp.ClippyPet._hwnd_is_fullscreen(root_hwnd(fs)) is True, "真全屏未识别"
print("[1] 无边框全屏窗口 → True  OK")

# --- 2) 最小化的全屏窗口 → 不算全屏（旧实现误判 → 误隐藏）
u.ShowWindow(root_hwnd(fs), 6)  # SW_MINIMIZE
pet.root.update()
time.sleep(0.2)
assert u.IsIconic(root_hwnd(fs)), "未进入最小化状态"
assert cp.ClippyPet._hwnd_is_fullscreen(root_hwnd(fs)) is False, "最小化全屏误判"
print("[2] 最小化全屏窗口 → False  OK")

# --- 3) 隐藏的全屏窗口 → 不算全屏（旧实现误判 → 误隐藏）
u.ShowWindow(root_hwnd(fs), 9)  # SW_RESTORE
pet.root.update()
time.sleep(0.2)
fs.withdraw()
fs.update()
assert cp.ClippyPet._hwnd_is_fullscreen(root_hwnd(fs)) is False, "隐藏全屏误判"
fs.destroy()
fs.update()
print("[3] 隐藏全屏窗口 → False  OK")

# --- 4) 普通可调整窗口最大化（带标题栏）→ 不算全屏
norm = tk.Toplevel(pet.root)
norm.geometry("600x400+100+100")
norm.state("zoomed")
norm.update()
time.sleep(0.3)
assert cp.ClippyPet._hwnd_is_fullscreen(root_hwnd(norm)) is False, "最大化窗口误判"
print("[4] 带边框最大化窗口 → False  OK")

# --- 5) 全屏窗口在底层 + 普通窗口在顶层 → 不算全屏（前台=clippy）
fs2 = mk_fullscreen()
fs2.lower()          # 全屏窗口沉底
norm.lift()          # 普通窗口在顶
fs2.update()
norm.update()
pet.root.update()
time.sleep(0.2)
fg_clippy()
assert pet._is_fullscreen() is False, "后台全屏窗口导致误隐藏"
print("[5] 后台全屏+前台普通窗口 → False  OK")

# --- 6) 全屏窗口在顶层 → 算全屏（置顶全屏窗口确保遍历最先遇到）
norm.withdraw()
fs2.update()
pet.root.update()
time.sleep(0.2)
fs2.attributes("-topmost", True)   # 置顶全屏窗口：Z 序高于一切普通窗口
fs2.update()
pet.root.update()
time.sleep(0.2)
fg_clippy()
assert pet._is_fullscreen() is True, "顶层全屏未识别"
print("[6] 顶层全屏窗口 → True  OK")

# --- 7) 端到端：普通窗口可见时 clippy 不隐藏
norm.state("normal")
norm.geometry("800x500+200+200")
norm.lift()
norm.update()
fs2.lower()
fs2.update()
time.sleep(0.2)
fg_clippy()
assert pet._is_fullscreen() is False
assert not pet._dnd_active
print("[7] 端到端：普通窗口下不隐藏  OK")

# --- 8) 端到端：全屏时进入免打扰（隐藏）
fs2.attributes("-topmost", True)
fs2.lift()
norm.withdraw()
fs2.update()
time.sleep(0.2)
fg_clippy()
pet.dnd_on = True
assert pet._is_fullscreen() is True
pet._check_fullscreen()
assert pet._dnd_active is True, "全屏未进入免打扰"
print("[8] 端到端：全屏时进入免打扰（隐藏）  OK")

# 清理
pet._dnd_restore()
fs2.destroy()
norm.destroy()
pet.root.update()
print("\nDND TEST ALL PASSED")
