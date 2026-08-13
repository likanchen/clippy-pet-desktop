# -*- coding: utf-8 -*-
"""真实时间帧率验证：3 秒内 _step 次数应≈预期（单 after 链，无加速）。"""
import os
import sys
import tempfile
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import clippy_pet as cp

cp.SETTINGS_FILE = os.path.join(tempfile.mkdtemp(), "rate.json")
pet = cp.ClippyPet()
pet.root.update()

# 主待机（loop, speed=2.5）
n0 = pet._steps
t0 = time.time()
while time.time() - t0 < 3.0:
    pet.root.update()
    time.sleep(0.01)
n1 = pet._steps
pet.root.update()

elapsed = n1 - n0
# 预期帧间隔 = 100ms × 2.5 = 250ms → 3 秒约 12 步
expected = 3.0 / (0.1 * pet._anim_speed)
print("3 秒内 _step 次数:", elapsed, "预期约:", round(expected, 1),
      "speed:", pet._anim_speed)
assert elapsed <= expected * 1.6, \
    "动画加速：多 after 链 (实际 %d > 预期 %.1f)" % (elapsed, expected)
print("RATE OK（单 after 链，无加速）")

# 修复前对照：loop 分支递归会导致翻倍以上的调用次数
# 现在应接近预期值

pet.quit()
print("FRAME-RATE OK")
