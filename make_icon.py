# -*- coding: utf-8 -*-
"""从 Clippy 第一帧生成 exe 图标 clippy.ico。"""
from PIL import Image

im = Image.open("assets/clippy/frames/f_0_0.png").convert("RGBA")
img = Image.new("RGBA", (256, 256), (0, 0, 0, 0))
iw, ih = im.size
scale = 200 / max(iw, ih)
nw, nh = int(iw * scale), int(ih * scale)
im = im.resize((nw, nh), Image.LANCZOS)
img.paste(im, ((256 - nw) // 2, (256 - nh) // 2), im)
img.save("clippy.ico", sizes=[(16, 16), (32, 32), (48, 48),
                              (64, 64), (128, 128), (256, 256)])
print("ICON OK")
