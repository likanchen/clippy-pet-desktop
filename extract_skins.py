# -*- coding: utf-8 -*-
"""
从 clippyjs/clippy.js 官方 agents 素材提取任意皮肤精灵帧。
输入: assets/dl/skins/<skin>/agent.js + map.png
输出: assets/skins/<skin>/frames/*.png + animations.json
用法: python extract_skins.py [skin...]   （缺省提取全部）
"""
import json
import os
import sys

from PIL import Image

BASE = os.path.dirname(os.path.abspath(__file__))
DL = os.path.join(BASE, "assets", "dl", "skins")
OUT_ROOT = os.path.join(BASE, "assets", "skins")

SKIN_IDS = ["clippy", "bonzi", "f1", "genie", "genius",
            "links", "merlin", "peedy", "rocky", "rover"]


def parse_agent_js(path):
    src = open(path, encoding="utf-8").read()
    data, _ = json.JSONDecoder().raw_decode(src[src.index("{"):])
    return data


def extract(skin):
    d = os.path.join(DL, skin)
    data = parse_agent_js(os.path.join(d, "agent.js"))
    fw, fh = data.get("framesize", [124, 93])
    map_im = Image.open(os.path.join(d, "map.png")).convert("RGBA")
    W, H = map_im.size

    out = os.path.join(OUT_ROOT, skin)
    fdir = os.path.join(out, "frames")
    os.makedirs(fdir, exist_ok=True)

    animations = {}
    used = {}
    total = 0
    for aname, ainfo in data["animations"].items():
        seq = []
        for f in ainfo["frames"]:
            if f.get("images"):
                x, y = f["images"][0]
                key = "f_%d_%d" % (x, y)
                used[key] = (x, y)
            else:
                key = None  # 空帧：只延时
            item = {"f": key, "d": f.get("duration", 100)}
            if f.get("branching"):
                item["branching"] = f["branching"]
            if "exitBranch" in f:
                item["exitBranch"] = f["exitBranch"]
            seq.append(item)
            total += 1
        animations[aname] = {
            "useExitBranching": bool(ainfo.get("useExitBranching")),
            "frames": seq,
        }

    for key, (x, y) in used.items():
        box = (x, y, min(x + fw, W), min(y + fh, H))
        im = map_im.crop(box)
        canvas = Image.new("RGBA", (fw, fh), (0, 0, 0, 0))
        canvas.paste(im, (0, 0))
        canvas.save(os.path.join(fdir, key + ".png"))

    with open(os.path.join(out, "animations.json"), "w",
              encoding="utf-8") as fp:
        json.dump({"framesize": [fw, fh], "animations": animations},
                  fp, ensure_ascii=False)

    print(f"{skin}: 动画 {len(animations)} 个, 帧引用 {total}, "
          f"精灵 {len(used)}, framesize {fw}x{fh}")


if __name__ == "__main__":
    ids = sys.argv[1:] or SKIN_IDS
    for s in ids:
        if s not in SKIN_IDS:
            print("跳过未知皮肤:", s)
            continue
        extract(s)
    print("完成")
