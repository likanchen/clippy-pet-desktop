# -*- coding: utf-8 -*-
"""frozen 模式模拟（onefile）：APP_DIR=exe 目录、DATA_DIR=_MEIPASS、
设置持久化到 exe 旁。"""
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
sys.frozen = True
sys.executable = os.path.join(BASE, "dist", "ClippyPet-v0.2.3.exe")
# 模拟 onefile 解压目录（素材在其中）
sys._MEIPASS = BASE

import clippy_pet as cp  # noqa: E402

assert cp.APP_DIR == os.path.dirname(sys.executable), cp.APP_DIR
assert cp.DATA_DIR == BASE, cp.DATA_DIR
assert os.path.isdir(os.path.join(cp.DATA_DIR, "assets", "clippy", "frames"))
print("PATH OK: APP_DIR =", cp.APP_DIR)
print("DATA OK: DATA_DIR =", cp.DATA_DIR)

pet = cp.ClippyPet()
pet._save_settings()
sf = os.path.join(cp.APP_DIR, "settings.json")
assert os.path.exists(sf)
data = json.load(open(sf, encoding="utf-8"))
assert "water_enabled" in data and "lang" in data
print("SAVE OK: 设置持久化到 exe 目录 ->", sf)
os.remove(sf)
print("测试设置已清理")