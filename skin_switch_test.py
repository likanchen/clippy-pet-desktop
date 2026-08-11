# -*- coding: utf-8 -*-
"""换肤过渡动画验证：旧皮肤再见 → 切换 → 新皮肤打招呼 → 回待机。"""
import os
import tempfile

import clippy_pet as cp

cp.SETTINGS_FILE = os.path.join(tempfile.mkdtemp(), "sw.json")
pet = cp.ClippyPet()
pet.root.update()

# 1. 所有皮肤都有再见/打招呼动画（数据层）
for sid, _label in cp.SKINS:
    pet._set_skin(sid)
    for _ in range(200):
        pet._step()
        if not pet._skin_switching:
            break
    pet.root.update()
    assert pet.skin == sid, (sid, pet.skin)
    gb = pet.act.get("goodbye")
    gr = pet.act.get("greet")
    assert gb and gr, (sid, gb, gr)
    print("%-8s 再见=%s 打招呼=%s 切换OK" % (sid, gb, gr))
    # 新皮肤 greet 播完回待机
    for _ in range(150):
        pet._step()
        if pet._is_idle():
            break
    assert pet._is_idle(), pet._anim_name
    pet.root.update()

# 2. 切回 clippy 恢复
pet._set_skin("clippy")
for _ in range(200):
    pet._step()
    if not pet._skin_switching:
        break
assert pet.skin == "clippy"
print("BACK OK")

# 3. 防重复触发：切换中再次 _set_skin 被忽略
pet._set_skin("merlin")
assert pet._skin_switching is True
pet._set_skin("rover")          # 切换中 → 忽略
assert pet._pending_skin == "merlin"
for _ in range(200):
    pet._step()
    if not pet._skin_switching:
        break
assert pet.skin == "merlin"
print("NO-RACE OK")

pet._hk_running = False
pet._do_exit()
print("SKIN-SWITCH OK")
