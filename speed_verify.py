# -*- coding: utf-8 -*-
"""验证修复后待机帧间隔（官方速度 100ms/帧）。"""
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import clippy_pet as cp

cp.SETTINGS_FILE = os.path.join(tempfile.mkdtemp(), "spd.json")
pet = cp.ClippyPet()
pet.root.update()

print("动画:", pet._anim_name, "speed:", pet._anim_speed)
ms0 = pet._anim_ms
pet._step()
step_ms = pet._anim_ms - ms0
print("step 帧间隔:", step_ms, "ms")
assert step_ms == 100, "帧间隔应为 100ms（官方速度）: %d" % step_ms
print("SPEED-FIX OK")
