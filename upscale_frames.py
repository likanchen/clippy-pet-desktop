# -*- coding: utf-8 -*-
"""批量 AI 超分皮肤帧（并行 + 断点续跑）。
输入: assets/skins/<skin>/frames/*.png
输出: assets/skins/<skin>/hd/*.png（124x93 -> 248x186）
用法: python upscale_frames.py [--skins clippy,rover] [--workers 6]
"""
import argparse
import os
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor

BASE = os.path.dirname(os.path.abspath(__file__))
EXE = os.path.join(BASE, "tools", "realesrgan-ncnn-vulkan.exe")
SKINS = ["clippy", "merlin", "genie", "bonzi", "peedy", "rover",
         "links", "rocky", "f1", "genius"]

_counter_lock = None  # 简单打印节流


def upscale_one(skin, src, dst):
    if os.path.exists(dst):
        return "skip"
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    r = subprocess.run(
        [EXE, "-i", src, "-o", dst, "-s", "2", "-n", "realesrgan-x4plus"],
        capture_output=True, creationflags=0x08000000)  # CREATE_NO_WINDOW
    return "ok" if r.returncode == 0 and os.path.exists(dst) else "fail"


def process_skin(skin, workers, progress):
    frames_dir = os.path.join(BASE, "assets", "skins", skin, "frames")
    hd_dir = os.path.join(BASE, "assets", "skins", skin, "hd")
    if not os.path.isdir(frames_dir):
        print("跳过（无 frames）:", skin)
        return
    files = sorted(f for f in os.listdir(frames_dir) if f.endswith(".png"))
    todo = [(skin, os.path.join(frames_dir, f), os.path.join(hd_dir, f))
            for f in files]
    done_skip = sum(1 for _, _, d in todo if os.path.exists(d))
    print("[%s] 共 %d 帧, 已完成 %d, 待处理 %d"
          % (skin, len(todo), done_skip, len(todo) - done_skip), flush=True)
    ok = fail = 0
    t0 = time.time()
    with ThreadPoolExecutor(max_workers=workers) as ex:
        for i, res in enumerate(ex.map(lambda x: upscale_one(*x), todo)):
            if res == "ok":
                ok += 1
            elif res == "fail":
                fail += 1
            if (i + 1) % 50 == 0 or i + 1 == len(todo):
                el = time.time() - t0
                print("[%s] %d/%d ok=%d fail=%d  %.0fs (%.2f fps)"
                      % (skin, i + 1, len(todo), ok, fail, el,
                         (i + 1) / max(el, 0.01)), flush=True)
    print("[%s] 完成 ok=%d fail=%d" % (skin, ok, fail), flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--skins", default=",".join(SKINS))
    ap.add_argument("--workers", type=int, default=6)
    a = ap.parse_args()
    skins = [s for s in a.skins.split(",") if s]
    for skin in skins:
        process_skin(skin, a.workers, None)


if __name__ == "__main__":
    main()
