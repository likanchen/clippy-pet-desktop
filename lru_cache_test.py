# -*- coding: utf-8 -*-
"""LRU 帧缓存验证：播放超过上限后缓存不再增长。"""
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import clippy_pet as cp

cp.SETTINGS_FILE = os.path.join(tempfile.mkdtemp(), "lru.json")
pet = cp.ClippyPet()
pet.root.update()

# 播放多个不同动画（触发大量不同帧加载），缓存不应超过 MAX_FRAME_CACHE
for sem in ("wave", "surprise", "write", "think", "happy", "artsy",
            "search", "print", "save", "mail", "check", "processing",
            "goodbye", "attention", "trash"):
    pet.play_semantic(sem)
    pet.root.update()
    for _ in range(60):
        pet._step()
        if pet._is_idle():
            break

print("缓存帧数:", len(pet._cache), "上限:", cp.MAX_FRAME_CACHE)
assert len(pet._cache) <= cp.MAX_FRAME_CACHE, \
    "缓存超过上限: %d > %d" % (len(pet._cache), cp.MAX_FRAME_CACHE)
# 播放了多种动画，应确实触发过缓存（> 若干帧）
assert len(pet._cache) > 20, "缓存过小，测试无效"
print("LRU OK")
