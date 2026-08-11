# -*- coding: utf-8 -*-
"""换肤菜单缩略图验证。"""
import os
import tempfile

import clippy_pet as cp

cp.SETTINGS_FILE = os.path.join(tempfile.mkdtemp(), "t.json")
pet = cp.ClippyPet()
pet._build_menu()
thumbs = pet._skin_thumbs
assert len(thumbs) == len(cp.SKINS), len(thumbs)
for sid, t in thumbs.items():
    assert t.width() == 44 and t.height() == 33, (sid, t.width(), t.height())
    print(sid, "thumb", t.width(), "x", t.height())
print("THUMB OK: %d 张缩略图" % len(thumbs))
