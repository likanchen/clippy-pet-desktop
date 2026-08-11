# -*- coding: utf-8 -*-
"""喝水/锻炼提醒设置验证：single 模式气泡对话框 + 间隔应用。"""
import base64
import io
import os
import tempfile

from PIL import Image

import clippy_pet as cp

cp.SETTINGS_FILE = os.path.join(tempfile.mkdtemp(), "r.json")
pet = cp.ClippyPet()
pet.root.update()

# 1) single 模式 PNG 渲染正常
png = cp.render_bubble_png(320, 172, "Water Reminder Settings",
                           "Interval (minutes)", "", "OK", "Cancel",
                           "bottom", 158, single=True)
im = Image.open(io.BytesIO(base64.b64decode(png)))
assert im.size == (320, 172), im.size
print("SINGLE RENDER OK", im.size)

# 2) 对话框 single 模式：_ok 单值回调
got = []
dlg = cp.SettingsDialog(
    pet.root, title="t", work_label="l", break_label="", work=30, brk=0,
    ok_text="OK", cancel_text="Cancel", on_ok=lambda v: got.append(v),
    clippy_pos=(600, 400), single=True)
pet.root.update()
dlg.work_var.set("45")
dlg._ok()
assert got == [45], got
print("SINGLE DIALOG OK, callback got", got)

# 3) 间隔应用：30 分钟 + 自动重排 + 保存
before = pet.water_interval
pet._apply_water_settings(30)
assert pet.water_interval == 30 * 60000, pet.water_interval
assert pet.water_job is not None  # 开启状态下已重排
pet._apply_exercise_settings(40)
assert pet.exercise_interval == 40 * 60000, pet.exercise_interval
data = cp._load_settings()
assert data["water_interval_min"] == 30, data
assert data["exercise_interval_min"] == 40, data
print("APPLY OK, water=%dmin ex=%dmin saved" %
      (data["water_interval_min"], data["exercise_interval_min"]))

pet._do_exit()
print("REMINDER_SETTINGS OK")
