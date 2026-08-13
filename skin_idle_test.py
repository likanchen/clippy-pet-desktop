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
                and pet._anim_name == pet._idle_anim
                and pet._loop):
            break
    pet.root.update()
    assert not pet._skin_switching, (sid, "换肤过渡未完成")
    assert pet._anim_name == pet._idle_anim, (sid, pet._anim_name)
    assert pet._loop is True, (sid, "主待机未循环")
    assert pet._idle_action_job is not None, (sid, "穿插定时器未调度")

    # 穿插小动作（若该皮肤除主待机外还有其它 idle 动作）
    pool = [a for a in pet._idle_anims if a != pet._idle_anim]
    if pool:
        pet._idle_play_action()
        pet.root.update()
        # 穿插后仍在待机态（极短动作可能已瞬间播完回到主待机）
        assert pet._is_idle(), (sid, pet._anim_name)
        # 最终回到主待机循环
        for _ in range(250):
            pet._step()
            if pet._anim_name == pet._idle_anim and pet._loop:
                break
        assert pet._anim_name == pet._idle_anim, (sid, "未回主待机")
    else:
        print("  %s 无额外 idle 动作（仅主待机）" % sid)

    print("%-8s 主待机=%-14s idle池=%d  OK" %
          (sid, pet._idle_anim, len(pet._idle_anims)))

pet._do_exit()
print("\nALL-SKIN IDLE OK")
