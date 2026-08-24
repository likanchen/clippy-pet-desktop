# -*- coding: utf-8 -*-
"""待机 1:1 验证：纯随机 idle + 官方帧时长自然播完 + 播完再随机。"""
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import clippy_pet as cp

cp.SETTINGS_FILE = os.path.join(tempfile.mkdtemp(), "idle.json")
pet = cp.ClippyPet()
pet.root.update()

# 1. 启动后：播放的是 idle 动画，官方帧时长（speed=1.0）
assert pet._anim_name.startswith("Idle"), pet._anim_name
assert pet._anim_speed == 1.0, pet._anim_speed
print("[1] 随机 idle:", pet._anim_name, "官方帧时长(1.0x) OK")

# 2. 播完自然换下一个 idle（推进中始终 idle，且见过多个）
seen = set()
for _ in range(1500):
    pet._step()
    if pet._anim_name != None:
        if not pet._is_idle():
            break
        seen.add(pet._anim_name)
    if len(seen) >= 3:
        break
assert len(seen) >= 2, "应能连续播放多个 idle: %d" % len(seen)
assert pet._is_idle(), "应始终处于 idle: %s" % pet._anim_name
print("[2] 连续播放 idle 数:", len(seen), "OK")
assert not hasattr(pet, "_idle_pool"), "去重池字段应已移除"
print("[3] 无去重池字段 OK")

# 3. 交互动画播完回待机（纯随机 idle）
pet.play_semantic("wave", on_done=pet._idle_next)
pet.root.update()
assert not pet._is_idle()
for _ in range(400):
    pet._step()
    if pet._is_idle():
        break
assert pet._is_idle(), pet._anim_name
print("[4] 交互后回随机待机 OK")

print("\nIDLE 1:1 OK")