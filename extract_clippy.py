# -*- coding: utf-8 -*-
"""
从 smore-inc/clippy.js 官方素材提取 Clippy 精灵帧。
输入: assets/dl/agent.js + assets/dl/clippyjs-map.png
输出: assets/clippy/frames/*.png + assets/clippy/animations.json
"""
import json
import os
import re

from PIL import Image

BASE = os.path.dirname(os.path.abspath(__file__))
DL = os.path.join(BASE, "assets", "dl")
OUT = os.path.join(BASE, "assets", "clippy")
FRAME_DIR = os.path.join(OUT, "frames")
os.makedirs(FRAME_DIR, exist_ok=True)

FW, FH = 124, 93  # 官方帧尺寸


def parse_agent_js(path):
    src = open(path, encoding="utf-8").read()
    i = src.index("{")
    data, _ = json.JSONDecoder().raw_decode(src[i:])
    return data


def main():
    data = parse_agent_js(os.path.join(DL, "clippyjs-agent.js"))
    map_im = Image.open(os.path.join(DL, "map.png")).convert("RGBA")
    W, H = map_im.size

    animations = {}
    used = {}
    total_frames = 0

    for aname, ainfo in data["animations"].items():
        seq = []
        for f in ainfo["frames"]:
            if "images" in f:
                x, y = f["images"][0]
                key = f"f_{x}_{y}"
                used[key] = (x, y)
            else:
                key = None  # 空帧：只延时不换图
            item = {"f": key, "d": f.get("duration", 100),
                    "s": f.get("sound")}
            # 保留官方分支/退出分支机制（Animator._getNextAnimationFrame）
            if f.get("branching"):
                item["branching"] = f["branching"]
            if "exitBranch" in f:
                item["exitBranch"] = f["exitBranch"]
            seq.append(item)
            total_frames += 1
        animations[aname] = {
            "useExitBranching": bool(ainfo.get("useExitBranching")),
            "frames": seq,
        }

    # 裁剪精灵表
    for key, (x, y) in used.items():
        box = (x, y, min(x + FW, W), min(y + FH, H))
        im = map_im.crop(box)
        # 统一尺寸，保证透明画布一致
        canvas = Image.new("RGBA", (FW, FH), (0, 0, 0, 0))
        canvas.paste(im, (0, 0))
        canvas.save(os.path.join(FRAME_DIR, key + ".png"))

    with open(os.path.join(OUT, "animations.json"), "w", encoding="utf-8") as fp:
        json.dump({"framesize": [FW, FH],
                   "animations": animations}, fp, ensure_ascii=False)

    print(f"动画: {len(animations)} 个, 帧引用: {total_frames}, 去重精灵: {len(used)}")
    print(f"精灵表: {W}x{H}, 输出: {OUT}")


if __name__ == "__main__":
    main()
