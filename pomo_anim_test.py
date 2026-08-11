# -*- coding: utf-8 -*-
"""番茄钟动画自然性验证：work/break 动画播一次后回待机，不无限循环。"""
import os
import time
import tempfile

import clippy_pet as cp

cp.SETTINGS_FILE = os.path.join(tempfile.mkdtemp(), "pomo.json")
pet = cp.ClippyPet()
pet.root.update()

# 1. 工作阶段：think 播一次（非循环），步进后回待机
pet.start_pomodoro()
pet.root.update()
assert pet.pomo_phase == "work"
assert pet._anim_name == pet.act.get("think", pet._idle_anim), pet._anim_name
assert pet._loop is False, "think 不应循环"
for _ in range(80):
    pet._step()
    if pet._is_idle():
        break
assert pet._is_idle(), "工作动画未回待机 %s" % pet._anim_name
print("WORK-ONCE OK")

# 2. 最后 1 分钟：write 播一次，不重复触发
pet._anim_ms = 99999
pet._step()                       # 超时保险收尾，回到 idle
pet.root.update()
pet.pomo_end_ts = time.time() + 30   # 模拟剩余 30 秒（< 60s）
pet._tick_pomodoro()
pet.root.update()
assert pet._pomo_write_played is True
assert pet._loop is False, "write 不应循环"
for _ in range(80):
    pet._step()
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
    pet._step()
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
