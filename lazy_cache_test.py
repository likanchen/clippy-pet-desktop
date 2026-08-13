# -*- coding: utf-8 -*-
"""惰性帧缓存验证：启动只缓存少量帧，随播放增长但远小于全量。"""
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import clippy_pet as cp

cp.SETTINGS_FILE = os.path.join(tempfile.mkdtemp(), "m.json")
pet = cp.ClippyPet()
pet.root.update()
print("启动后缓存帧数:", len(pet._cache), "(惰性加载应极少)")
assert len(pet._cache) < 10, "启动缓存应极少: %d" % len(pet._cache)

for _ in range(30):
    pet._step()
print("播放30步后缓存帧数:", len(pet._cache), "/ 全量902")
assert 0 < len(pet._cache) < 902, "缓存应远小于全量: %d" % len(pet._cache)

# 切缩放：缓存清空后当前帧仍能显示（_photo 立即加载）
pet._set_zoom(3)
pet.root.update()
assert len(pet._cache) >= 1, "缩放后当前帧应立即加载"
print("缩放后缓存:", len(pet._cache))
print("LAZY OK")
