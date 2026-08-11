# -*- coding: utf-8 -*-
"""退出动画验证：quit() 应播放当前皮肤 goodbye 动作后销毁窗口。"""
import os
import tempfile
import time

import clippy_pet as cp

cp.SETTINGS_FILE = os.path.join(tempfile.mkdtemp(), "q.json")
pet = cp.ClippyPet()
pet.root.update()
goodbye = pet.act.get("goodbye", pet._idle_anim)
print("goodbye anim for clippy:", goodbye)

pet.quit()
assert pet._quitting is True
pet.root.update()
print("playing:", pet._anim_name)
assert pet._anim_name == goodbye, (pet._anim_name, goodbye)

# 推进几帧确认动画正常步进，再手动完成退出
for _ in range(3):
    pet.root.update()
    time.sleep(0.05)
pet._do_exit()
print("QUIT OK")
