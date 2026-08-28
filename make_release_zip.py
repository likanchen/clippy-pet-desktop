# -*- coding: utf-8 -*-
"""压缩 onefile 单 exe 为发布 zip。
输入: dist/ClippyPet-v0.2.3.exe
输出: <TEMP>/clippy-release/ClippyPet-v0.2.3-windows.zip（内含单个 exe）"""
import os
import zipfile

SRC = os.path.abspath("dist/ClippyPet-v0.2.3.exe")
OUT = os.path.join(os.environ.get("TEMP", "/tmp"),
                   "clippy-release", "ClippyPet-v0.2.3-windows.zip")
os.makedirs(os.path.dirname(OUT), exist_ok=True)

with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as z:
    z.write(SRC, os.path.basename(SRC))
print("ZIP OK:", OUT)
print("大小:", round(os.path.getsize(OUT) / 1048576, 1), "MB")