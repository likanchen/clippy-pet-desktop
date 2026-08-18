# -*- coding: utf-8 -*-
"""ULW 原型（干净版）：Tk 分层窗口 + UpdateLayeredWindow 显示带 alpha 帧。
验证：显示、拖拽、性能。运行: python proto_ulw.py"""
import ctypes
import os
import sys
import time
import tkinter as tk
from ctypes import wintypes
from PIL import Image

user32 = ctypes.windll.user32
gdi32 = ctypes.windll.gdi32
kernel32 = ctypes.windll.kernel32

WS_EX_LAYERED = 0x00080000
ULW_ALPHA = 0x00000002
AC_SRC_OVER = 0x00
AC_SRC_ALPHA = 0x01


class BITMAPINFOHEADER(ctypes.Structure):
    _fields_ = [
        ("biSize", wintypes.DWORD), ("biWidth", ctypes.c_long),
        ("biHeight", ctypes.c_long), ("biPlanes", wintypes.WORD),
        ("biBitCount", wintypes.WORD), ("biCompression", wintypes.DWORD),
        ("biSizeImage", wintypes.DWORD), ("biXPelsPerMeter", ctypes.c_long),
        ("biYPelsPerMeter", ctypes.c_long), ("biClrUsed", wintypes.DWORD),
        ("biClrImportant", wintypes.DWORD),
    ]


class BLENDFUNCTION(ctypes.Structure):
    _fields_ = [
        ("BlendOp", ctypes.c_ubyte), ("BlendFlags", ctypes.c_ubyte),
        ("SrcConstantAlpha", ctypes.c_ubyte), ("AlphaFormat", ctypes.c_ubyte),
    ]


root = tk.Tk()
root.overrideredirect(True)
root.geometry("248x186+400+300")
root.configure(bg="magenta")

user32.GetAncestor.restype = wintypes.HWND
hwnd = user32.GetAncestor(root.winfo_id(), 2)
style = user32.GetWindowLongW(hwnd, -20)
user32.SetWindowLongW(hwnd, -20, style | WS_EX_LAYERED)

BASE = os.path.dirname(os.path.abspath(__file__))
fr = Image.open(os.path.join(BASE, "assets", "skins", "clippy", "frames",
                             "f_0_0.png")).convert("RGBA").resize(
    (248, 186), Image.LANCZOS)

W, H = fr.size
screen_dc = user32.GetDC(0)
mem_dc = gdi32.CreateCompatibleDC(screen_dc)
bmi = BITMAPINFOHEADER()
bmi.biSize = ctypes.sizeof(BITMAPINFOHEADER)
bmi.biWidth = W
bmi.biHeight = H
bmi.biPlanes = 1
bmi.biBitCount = 32
bmi.biCompression = 0
dib = gdi32.CreateDIBSection(mem_dc, ctypes.byref(bmi), 0, None, None, 0)
gdi32.SelectObject(mem_dc, dib)
buf = ctypes.create_string_buffer(W * H * 4)


def to_bgrab(im):
    rgba = im.tobytes()
    out = bytearray(W * H * 4)
    for y in range(H):
        sy = H - 1 - y
        for x in range(W):
            i = (sy * W + x) * 4
            o = (y * W + x) * 4
            out[o] = rgba[i + 2]
            out[o + 1] = rgba[i + 1]
            out[o + 2] = rgba[i]
            out[o + 3] = rgba[i + 3]
    return bytes(out)


def push(im):
    data = to_bgrab(im)
    ctypes.memmove(buf, data, len(data))
    gdi32.SetDIBits(mem_dc, dib, 0, H, buf, ctypes.byref(bmi), 0)
    blf = BLENDFUNCTION(AC_SRC_OVER, 0, 255, AC_SRC_ALPHA)
    pt = wintypes.POINT(0, 0)
    size = wintypes.SIZE(W, H)
    user32.UpdateLayeredWindow(hwnd, screen_dc, None, ctypes.byref(size),
                               mem_dc, ctypes.byref(pt), 0,
                               ctypes.byref(blf), ULW_ALPHA)


# 事件
drag = None
root.bind("<ButtonPress-1>", lambda e: setattr(
    sys.modules[__name__], "drag", (e.x_root - root.winfo_x(),
                                    e.y_root - root.winfo_y())))
root.bind("<B1-Motion>", lambda e: (drag and root.geometry(
    "+%d+%d" % (e.x_root - drag[0], e.y_root - drag[1]))))
root.bind("<ButtonRelease-1>", lambda e: setattr(sys.modules[__name__],
                                                 "drag", None))
root.bind("<Button-3>", lambda e: print("右键@", e.x_root, e.y_root))

print("拖动测试: 按住左键移动窗口，右键打印坐标")

t0 = time.time()
N = 60
for _ in range(N):
    push(fr)
el = time.time() - t0
print("60 帧 ULW 更新耗时 %.2fs (%.2f ms/帧)" % (el, el / N * 1000))

root.after(3000, root.destroy)
root.mainloop()
print("PROTO ULW OK")
