# -*- coding: utf-8 -*-
"""frozen 模式模拟：验证打包后 APP_DIR/DATA_DIR 解析与设置持久化。"""
import json
import os
import sys

sys.frozen = True
sys.executable = os.path.abspath(
    "dist/ClippyPet-v0.2.1/ClippyPet-v0.2.1.exe")

import clippy_pet as cp  # noqa: E402

assert cp.APP_DIR.endswith("dist" + os.sep + "ClippyPet-v0.2.1"), cp.APP_DIR
assert cp.DATA_DIR == os.path.join(cp.APP_DIR, "_internal"), cp.DATA_DIR
assert os.path.isdir(os.path.join(cp.DATA_DIR, "assets", "clippy", "frames"))
print("PATH OK:", cp.APP_DIR)
print("DATA OK: 素材目录可读")

pet = cp.ClippyPet()
pet._save_settings()
sf = os.path.join(cp.APP_DIR, "settings.json")
assert os.path.exists(sf)
data = json.load(open(sf, encoding="utf-8"))
assert "water_enabled" in data and "lang" in data
print("SAVE OK: 设置持久化到 exe 目录 ->", sf)
os.remove(sf)
print("测试设置已清理")
