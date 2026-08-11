# -*- coding: utf-8 -*-
"""冒烟测试 v5：验证官方素材加载、动画状态机、提醒、番茄钟。"""
import os
import tempfile
import clippy_pet as cp

# 重定向设置文件到临时路径，避免测试污染真实用户设置
cp.SETTINGS_FILE = os.path.join(tempfile.mkdtemp(), "smoke_settings.json")

pet = cp.ClippyPet()
pet.root.update()

# 1. 素材完整性
assert cp.ANIM_IDLE in pet.animations, "缺少主待机动画"
for sem, official in cp.ACT.items():
    assert official in pet.animations, f"{sem} -> {official} 缺失"
print(f"ASSETS OK: {len(pet.animations)} 个官方动画, "
      f"缓存 {len(pet._cache)} 张精灵, 尺寸 {pet.size}")

# 2. 动画状态机
pet.play(cp.ANIM_IDLE, loop=True)
pet.root.update()
assert pet._loop is True
pet.play_semantic("wave")
pet.root.update()
pet.play_semantic("blink")
for _ in range(5):
    pet.root.update()
print("ANIM OK")

# 3. 提醒动作
pet._on_action("water_done")
pet._on_action("ex_snooze")
pet._on_action("water_off")
pet.root.update()
assert pet.water_enabled is False
print("REMIND OK")

# 4. 番茄钟
pet.start_pomodoro()
pet.root.update()
assert pet.pomo_running and pet.pomo_phase == "work"
assert pet._anim_name == cp.ACT["think"]
assert pet._seq is pet.animations[cp.ACT["think"]]["frames"]
pet._start_break_phase()
pet.root.update()
assert pet.pomo_phase == "break"
pet.stop_pomodoro()
pet.root.update()
assert not pet.pomo_running
print("POMODORO OK")

# 5. 气泡
pet.say("冒烟测试", buttons=[("好", "water_done")])
pet.root.update()
assert pet.bubble is not None
pet.bubble.hide()
pet.root.update()
print("BUBBLE OK")

# 6. 语言切换
assert pet.lang == "zh"
pet._toggle_lang()
pet.root.update()
assert pet.lang == "en"
assert pet.tr("menu_water") == "\U0001F4A7Water reminder"
assert pet.tr("btn_snooze", n=5) == "5 min later"
pet._toggle_lang()
pet.root.update()
assert pet.lang == "zh"
assert pet.tr("menu_water") == "\U0001F4A7喝水提醒"
print("LANG OK")

# 7. 动作映射（描述与官方动画匹配）
assert cp.ACT["surprise"] == "Alert", "惊讶应映射官方 Alert（GetAttention 是吸引注意）"
assert cp.ACT["pointdown"] == "GestureDown"
assert cp.ACT["print"] == "Print"
assert ("act_pointdown", "pointdown") in cp.PERFORM_ITEMS
assert ("act_print", "print") in cp.PERFORM_ITEMS
assert ("act_nod", "nod") not in cp.PERFORM_ITEMS
print("MAPPING OK")

# 8. 番茄钟设置
assert pet.pomo_work_min == 25 and pet.pomo_break_min == 5
pet._apply_pomo_settings(50, 10)
pet.root.update()
assert pet.pomo_work_min == 50 and pet.pomo_break_min == 10
pet._apply_pomo_settings(25, 5)
pet.root.update()
assert pet.pomo_work_min == 25 and pet.pomo_break_min == 5
print("POMO_SETTINGS OK")

# 9. 思考气泡设置对话框
d = cp.SettingsDialog(pet.root, title="番茄钟设置", work_label="工作时长（分钟）",
                      break_label="休息时长（分钟）", work=25, brk=5,
                      ok_text="好", cancel_text="取消", on_ok=None,
                      clippy_pos=(200, 200))
pet.root.update()
assert d.winfo_exists()
assert d.work_var.get() == "25" and d.brk_var.get() == "5"
d._ok()  # 无 on_ok，仅验证销毁流程
pet.root.update()
assert not d.winfo_exists()
print("THOUGHT_BUBBLE OK")

print("SMOKE OK: window =", pet.root.winfo_width(), "x", pet.root.winfo_height())
pet.quit()
