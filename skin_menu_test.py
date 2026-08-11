# -*- coding: utf-8 -*-
"""皮肤专属表演动作菜单验证：按皮肤过滤动作项，切换皮肤菜单更新。"""
import os
import tempfile

import clippy_pet as cp

cp.SETTINGS_FILE = os.path.join(tempfile.mkdtemp(), "sm.json")
pet = cp.ClippyPet()
pet.root.update()

counts = {}
for sid, label in cp.SKINS:
    pet._set_skin(sid)
    for _ in range(200):
        pet._step()
        if not pet._skin_switching:
            break
    pet.root.update()
    assert pet.skin == sid, (sid, pet.skin)
    items = pet._perform_items_for_skin()
    for tkey, sem in items:
        assert pet.act.get(sem), (sid, sem, "动作无真实动画")
    counts[sid] = len(items)
    print("%-8s %-10s 动作数=%d" % (sid, label, len(items)))

# 关键断言：Rover 动画集小，动作应显著少于 Clippy 全量
assert counts["clippy"] == len(cp.PERFORM_ITEMS), counts["clippy"]
assert counts["rover"] < counts["clippy"], counts
assert counts["merlin"] < counts["clippy"], counts  # 老式助手缺部分动作

# 切回 clippy：菜单恢复全量
pet._set_skin("clippy")
pet._build_menu()
assert len(pet._perform_items_for_skin()) == len(cp.PERFORM_ITEMS)
print("SKIN-MENU OK: clippy=%d rover=%d merlin=%d" %
      (counts["clippy"], counts["rover"], counts["merlin"]))
