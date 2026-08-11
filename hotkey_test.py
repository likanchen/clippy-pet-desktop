# -*- coding: utf-8 -*-
"""全局快捷键动画验证：默认映射/VK码/开关/触发。"""
import os
import tempfile

import clippy_pet as cp

cp.SETTINGS_FILE = os.path.join(tempfile.mkdtemp(), "hk.json")
pet = cp.ClippyPet()
pet.root.update()

# 1. 默认映射
assert pet.hotkey_on is False
assert set(pet.hotkey_map) == set(cp.DEFAULT_HOTKEYS)
assert pet.hotkey_map["save"] == {"mods": ["Ctrl"], "key": "s"}
print("DEFAULT OK")

# 2. VK 码映射
assert pet._key_vk("s") == 0x53
assert pet._key_vk("Delete") == 0x2E
assert pet._key_vk("F5") == 0x74
assert pet._key_vk("f5") == 0x74
assert pet._key_vk("Space") == 0x20
print("VK OK")

# 3. 开关 + 持久化
pet.hotkey_var.set(True)
pet._toggle_hotkey()
assert pet.hotkey_on is True
data = cp._load_settings()
assert data["hotkey_on"] is True
assert data["hotkey_map"]["save"]["key"] == "s"
print("TOGGLE OK")

# 4. 编辑功能已移除：无 HotkeySettingsDialog、无 _apply_hotkeys
assert not hasattr(cp, "HotkeySettingsDialog")
assert not hasattr(pet, "_apply_hotkeys")
print("EDIT-REMOVED OK")

# 5. 触发：空闲时触发 save 动画
for _ in range(3):
    pet.root.update()
assert pet._is_idle(), pet._anim_name
pet._hk_fire("save")
pet.root.update()
assert pet._anim_name == pet.act.get("save", pet._idle_anim), pet._anim_name
print("FIRE OK")

# 6. 保险：超时触发退出，等待 exitBranch 优雅退出（Searching）
pet.play_semantic("search")
pet.root.update()
assert not pet._is_idle(), pet._anim_name
pet._anim_ms = 99999                      # 模拟超时
ret = pet._maybe_exit()
assert ret is False and pet._exiting is True, (ret, pet._exiting)
# 继续步进：播到 exitBranch 帧跳转退出序列(55-60)后自然回待机
for _ in range(80):
    pet._step()
    if pet._is_idle():
        break
assert pet._is_idle(), "优雅退出未完成 %s" % pet._anim_name
print("GUARD OK")

# 6b. exitBranch 跳转退出序列
pet.play_semantic("search")
pet.root.update()
exit_i = next(i for i, f in enumerate(pet._seq) if "exitBranch" in f)
pet._ai = exit_i
pet._cur = pet._seq[exit_i]
pet._anim_ms = 99999
ret = pet._maybe_exit()
assert ret is False and pet._exiting is True
pet._step()                                # _next_idx 跳转退出序列
assert pet._ai == 55, pet._ai
print("EXIT-BRANCH OK")

# 6c. 退出序列超长强制收尾（上限优先）
pet._exit_steps = 999
pet._step()
pet.root.update()
assert pet._is_idle(), pet._anim_name
print("EXIT-CAP OK")

# 7. 保险不影响 loop=True 动画（番茄钟工作/休息）
pet.play(pet._a("think"), loop=True)
pet.root.update()
pet._steps = 999
pet._anim_ms = 99999
pet._step()
pet.root.update()
assert pet._anim_name == pet.act.get("think", pet._idle_anim), pet._anim_name
print("LOOP-OK")

# 8. 保险触发 on_done 回调（等待退出序列或上限兜底）
done = []
pet.play_semantic("save", on_done=lambda: done.append(1))
pet.root.update()
pet._anim_ms = 99999
pet._maybe_exit()
for _ in range(60):
    pet._step()
    if done:
        break
assert done == [1], done
print("DONE-OK")

pet._hk_running = False
pet._do_exit()
print("HOTKEY OK")
