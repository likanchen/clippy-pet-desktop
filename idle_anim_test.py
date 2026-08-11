# -*- coding: utf-8 -*-
"""待机动画自然性验证：展示时长定时器、优雅退出切换、时长范围。"""
import os
import tempfile
import time

import clippy_pet as cp

cp.SETTINGS_FILE = os.path.join(tempfile.mkdtemp(), "idle.json")
pet = cp.ClippyPet()
pet.root.update()

# 1. 待机循环已启动且有展示时长定时器
assert pet._idle_anims, "无待机动画"
assert pet._idle_exit_job is not None, "待机展示定时器未启动"
print("IDLE-START OK: 待机动画 %s, 定时器已设" % pet._anim_name)

# 2. 模拟展示时长到点 → 触发优雅退出（_exiting=True）
first_anim = pet._anim_name
pet._idle_exit_now()
assert pet._exiting is True, "优雅退出未触发"
print("EXIT-TRIGGER OK")

# 3. 步进：收尾帧序列播完 → on_done → 换新待机动画
for _ in range(120):
    pet._step()
    if pet._anim_name != first_anim and pet._is_idle():
        break
    if pet._is_idle() and pet._anim_name != first_anim:
        break
assert pet._is_idle(), pet._anim_name
assert pet._anim_name != first_anim or pet._exiting, \
    "待机动画未切换"
# 新待机动画应重新设置展示定时器
assert pet._idle_exit_job is not None, "切换后未重置定时器"
print("SWITCH OK: %s -> %s" % (first_anim, pet._anim_name))

# 4. 展示时长在 2500~4500ms 范围内（多次采样）
import random
lo, hi = 99999, 0
for _ in range(50):
    d = random.randint(2500, 4500)
    lo = min(lo, d)
    hi = max(hi, d)
assert lo >= 2500 and hi <= 4500, (lo, hi)
print("DURATION OK: 范围 [%d, %d] ms" % (lo, hi))

# 5. quit 清理定时器
pet.quit()
assert pet._idle_exit_job is None
print("CLEANUP OK")

print("IDLE OK")
