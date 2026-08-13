# -*- coding: utf-8 -*-
"""压缩 dist/ClippyPet-v0.2 为发布 zip（含 _internal 运行时与素材）。"""
import os
import zipfile

SRC = os.path.abspath("dist/ClippyPet-v0.2")
OUT = os.path.join(os.environ.get("TEMP", "/tmp"),
                   "clippy-release", "ClippyPet-v0.2-windows.zip")
os.makedirs(os.path.dirname(OUT), exist_ok=True)

total = 0
with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as z:
    for root, _dirs, files in os.walk(SRC):
        for f in files:
            p = os.path.join(root, f)
            arc = os.path.join("ClippyPet-v0.2", os.path.relpath(p, SRC))
            z.write(p, arc)
            total += 1
print("ZIP OK:", OUT)
print("文件数:", total, "大小:", round(os.path.getsize(OUT) / 1048576, 1), "MB")
