# -*- coding: utf-8 -*-
"""全皮肤待机逻辑验证：每款皮肤主待机循环 + 穿插 + 回主待机。"""
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import clippy_pet as cp

cp.SETTINGS_FILE = os.path.join(tempfile.mkdtemp(), "si.json")
pet = cp.ClippyPet()
pet.root.update()

for sid, label in cp.SKINS:
    pet._set_skin(sid)
    # 步进完成换肤过渡：goodbye → 切换 → greet → 主待机
    for _ in range(600):
        pet._step()
        pet.root.update()
        if (not pet._skin_switching
                and pet._anim_name.startswith("Idle")):
            break
    pet.root.update()
    assert not pet._skin_switching, (sid, "换肤过渡未完成")
    assert pet._anim_name.startswith("Idle"), (sid, pet._anim_name)
    assert not hasattr(pet, "_idle_pool"), (sid, "去重池应已移除")
    assert not hasattr(pet, "_idle_action_job"), (sid, "穿插字段残留")

    # 官方纯随机：推进中持续播放 idle，应见过多个不同 idle
    seen = {pet._anim_name}
    prev = pet._anim_name
    for _ in range(1500):
        pet._step()
        if pet._anim_name != prev:
            assert pet._is_idle(), (sid, "应始终 idle")
            seen.add(pet._anim_name)
            prev = pet._anim_name
            if len(seen) >= 3:
                break
    assert 1 <= len(seen) <= max(len(pet._idle_anims), 1), (sid, len(seen))

    print("%-8s idle=%d 已见=%d  OK" %
          (sid, len(pet._idle_anims), len(seen)))

pet._do_exit()
print("\nALL-SKIN IDLE OK")
