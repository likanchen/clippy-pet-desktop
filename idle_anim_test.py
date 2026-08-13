# -*- coding: utf-8 -*-
"""待机动画逻辑验证：主待机稳定循环 + 低频小动作穿插（全皮肤）。"""
import os
import random
import sys
import tempfile
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import clippy_pet as cp

cp.SETTINGS_FILE = os.path.join(tempfile.mkdtemp(), "idle.json")
pet = cp.ClippyPet()
pet.root.update()

# 1. 启动后：主待机动画循环播放 + 穿插定时器已调度 + 放慢系数生效
assert pet._anim_name == pet._idle_anim, (pet._anim_name, pet._idle_anim)
assert pet._loop is True, "主待机应循环播放"
assert pet._idle_action_job is not None, "穿插定时器未调度"
assert pet._anim_speed == cp.IDLE_ANIM_SPEED, \
    "主待机应放慢: %s" % pet._anim_speed
print("[1] 主待机循环 + 定时器 + 放慢%.1fx  OK: %s" %
      (pet._anim_speed, pet._idle_anim))

# 2. 间隔范围 8~16 秒
lo, hi = 1 << 30, 0
for _ in range(60):
    d = random.randint(cp.IDLE_ACTION_MIN_MS, cp.IDLE_ACTION_MAX_MS)
    lo, hi = min(lo, d), max(hi, d)
assert lo >= 8000 and hi <= 16000, (lo, hi)
print("[2] 间隔范围 [%d, %d] ms  OK" % (lo, hi))

# 3. 手动触发穿插：播放小动作（非主待机），播完回主待机
pet._idle_play_action()
pet.root.update()
assert pet._is_idle() and pet._anim_name != pet._idle_anim, \
    "穿插应播放非主待机的小动作: %s" % pet._anim_name
print("[3] 穿插动作:", pet._anim_name, " OK")

# 4. 穿插播完 → 回到主待机循环 + 重新调度
for _ in range(150):
    pet._step()
    if pet._anim_name == pet._idle_anim and pet._loop:
        break
assert pet._anim_name == pet._idle_anim and pet._loop, \
    "穿插后未回到主待机: %s" % pet._anim_name
assert pet._idle_action_job is not None, "穿插后未重新调度"
print("[4] 穿插后回主待机 + 重新调度  OK")

# 5. 非待机状态（交互中）触发穿插 → 不打断，重新调度；交互动画保持官方速度
pet.play_semantic("wave", on_done=pet._idle_next)
pet.root.update()
assert not pet._is_idle(), "wave 应在播放"
assert pet._anim_speed == 1.0, "交互动画应保持官方速度: %s" % pet._anim_speed
pet._idle_action_job = None   # 模拟定时器已触发
pet._idle_play_action()
pet.root.update()
assert pet._anim_name == pet.act.get("wave", pet._idle_anim), \
    "交互中不应被穿插打断: %s" % pet._anim_name
assert pet._idle_action_job is not None, "交互中应重新调度穿插"
print("[5] 交互中穿插不打断 + 交互官方速度  OK")

# 6. quit 清理定时器
pet.quit()
assert pet._idle_action_job is None
print("[6] quit 清理  OK")

print("\nIDLE OK")
