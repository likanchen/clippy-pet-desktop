# -*- coding: utf-8 -*-
"""番茄钟动画自然性验证：work/break 动画播一次后回待机，不无限循环。"""
import os
import time
import tempfile

import clippy_pet as cp

cp.SETTINGS_FILE = os.path.join(tempfile.mkdtemp(), "pomo.json")
pet = cp.ClippyPet()
pet.root.update()


def fstep(n):
    """手动推进动画帧：先取消已调度 after，避免陈旧回调累积
    （手动 _step 与 after 链混合会导致残留回调把动画快进）。"""
    for _ in range(n):
        if pet._after_anim:
            try:
                pet.root.after_cancel(pet._after_anim)
            except Exception:
                pass
            pet._after_anim = None
        pet._step()

# 1. 工作阶段：think 播一次（非循环），步进后回待机
pet.start_pomodoro()
pet.root.update()
assert pet.pomo_phase == "work"
assert pet._anim_name == pet.act.get("think", pet._idle_anim), pet._anim_name
assert pet._loop is False, "think 不应循环"
for _ in range(80):
    fstep(1)
    if pet._is_idle():
        break
assert pet._is_idle(), "工作动画未回待机 %s" % pet._anim_name
print("WORK-ONCE OK")

# 2. 最后 1 分钟：write 播一次，不重复触发
pet._anim_ms = 99999
fstep(1)                           # 超时保险收尾，回到 idle
pet.root.update()
pet.pomo_end_ts = time.time() + 30   # 模拟剩余 30 秒（< 60s）
pet._tick_pomodoro()
pet.root.update()
assert pet._pomo_write_played is True
assert pet._loop is False, "write 不应循环"
for _ in range(80):
    fstep(1)
    if pet._is_idle():
        break
assert pet._is_idle(), "write 未回待机 %s" % pet._anim_name
print("WRITE-ONCE OK")

# 3. 休息阶段：sleep 播一次后回待机
pet._start_break_phase()
pet.root.update()
assert pet.pomo_phase == "break"
assert pet._anim_name == pet.act.get("sleep", pet._idle_anim), pet._anim_name
assert pet._loop is False, "sleep 不应循环"
for _ in range(120):
    fstep(1)
    if pet._is_idle():
        break
assert pet._is_idle(), "休息动画未回待机 %s" % pet._anim_name
print("BREAK-ONCE OK")

# 4. stop 清理
pet.stop_pomodoro()
pet.root.update()
assert pet.pomo_running is False
assert pet._pomo_write_played is False
print("STOP OK")

pet._hk_running = False
pet._do_exit()
print("POMO_ANIM OK")
