# -*- coding: utf-8 -*-
"""生成 README 预览图：皮肤样式网格图 + 右键菜单示意图。
输出到 docs/images/（GitHub 相对路径引用）。
"""
import os

from PIL import Image, ImageDraw, ImageFont

BASE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(BASE, "docs", "images")
os.makedirs(OUT, exist_ok=True)

SKINS = ["clippy", "merlin", "genie", "bonzi", "peedy",
         "rover", "links", "rocky", "f1", "genius"]
NAMES = ["Clippy", "Merlin", "Genie", "Bonzi", "Peedy",
         "Rover", "Links", "Rocky", "F1", "Genius"]


def font(size, bold=False):
    for p in ("C:/Windows/Fonts/msyhbd.ttc" if bold else "C:/Windows/Fonts/msyh.ttc",
              "C:/Windows/Fonts/msyh.ttc", "C:/Windows/Fonts/simhei.ttf"):
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except OSError:
                continue
    return ImageFont.load_default()


def skins_preview():
    """10 皮肤网格图：每格角色形象 + 名称。"""
    cols, rows = 5, 2
    cw, ch = 230, 180
    pad = 12
    W, H = cols * cw + pad * 2, rows * ch + pad * 2
    img = Image.new("RGB", (W, H), (245, 245, 245))
    d = ImageDraw.Draw(img)
    f_name = font(20, bold=True)
    f_sub = font(13)

    for i, (skin, name) in enumerate(zip(SKINS, NAMES)):
        cx = pad + (i % cols) * cw
        cy = pad + (i // cols) * ch
        # 格背景
        d.rounded_rectangle([cx, cy, cx + cw - 8, cy + ch - 8],
                            radius=10, fill=(255, 255, 255),
                            outline=(210, 210, 210), width=1)
        # 皮肤第一帧
        fp = os.path.join(BASE, "assets", "skins", skin, "frames", "f_0_0.png")
        try:
            im = Image.open(fp).convert("RGBA")
        except Exception:
            im = None
        if im:
            # 缩放居中
            box_w, box_h = cw - 40, 110
            iw, ih = im.size
            scale = min(box_w / iw, box_h / ih)
            nw, nh = int(iw * scale), int(ih * scale)
            im = im.resize((nw, nh), Image.LANCZOS)
            ix = cx + (cw - 8) // 2 - nw // 2
            iy = cy + 14
            img.paste(im, (ix, iy), im)
        # 名称
        d.text((cx + (cw - 8) // 2, cy + ch - 42), name,
               font=f_name, fill=(30, 30, 30), anchor="mm")
        d.text((cx + (cw - 8) // 2, cy + ch - 18),
               "%dx%d" % (im.size[0], im.size[1]) if im else "",
               font=f_sub, fill=(140, 140, 140), anchor="mm")
    img.save(os.path.join(OUT, "skins_preview.png"))
    print("skins_preview.png:", img.size)


MENU_ZH = [
    ("icon", "\u2714 喝水提醒", True),
    ("", "\u2699 喝水提醒设置\u2026", None),
    ("icon", "\u2714 锻炼提醒", True),
    ("", "\u2699 锻炼提醒设置\u2026", None),
    ("sep", None, None),
    ("", "开始番茄钟", None),
    ("", "停止番茄钟", None),
    ("", "番茄钟设置\u2026", None),
    ("sep", None, None),
    ("", "表演动作  \u25B6", None),       # ▶ 子菜单
    ("", "调整大小  \u25B6", None),
    ("", "换肤  \u25B6", None),
    ("sep", None, None),
    ("icon", "\u2714 显示在最前", True),
    ("", "全屏免打扰", None),
    ("", "开机自启动", None),
    ("", "全局快捷键动画", None),
    ("sep", None, None),
    ("", "切换为 English", None),
    ("sep", None, None),
    ("", "退出", None),
]


def menu_preview():
    """模拟右键菜单图：白底 + 菜单项 + ✓/▶ + 分隔线。"""
    line_h = 32
    pad_x, pad_y = 16, 10
    width = 240
    height = pad_y * 2 + len(MENU_ZH) * line_h + 6
    img = Image.new("RGB", (width, height), (255, 255, 255))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([0, 0, width - 1, height - 1], radius=8,
                        outline=(190, 190, 190), width=1)
    f = font(16)

    y = pad_y
    for kind, text, checked in MENU_ZH:
        if kind == "sep":
            y += line_h // 2
            d.line([pad_x, y, width - pad_x, y], fill=(230, 230, 230), width=1)
            y += line_h // 2
            continue
        if kind == "icon":
            # 图标槽
            d.rounded_rectangle([8, y + 6, 26, y + 26], radius=4,
                                fill=(240, 240, 240), outline=(200, 200, 200))
            d.text((17, y + 16), "\u2714", font=font(13), fill=(60, 130, 60),
                   anchor="mm")
            tx = 34
        else:
            tx = 18
        d.text((tx, y + 16), text or "", font=f, fill=(28, 28, 28),
               anchor="lm")
        y += line_h
    img.save(os.path.join(OUT, "context_menu.png"))
    print("context_menu.png:", img.size)


if __name__ == "__main__":
    skins_preview()
    menu_preview()
