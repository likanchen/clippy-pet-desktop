# -*- coding: utf-8 -*-
"""
Clippy 桌面宠物 v0.2 —— 官方 Clippy 素材逐帧动画 + 换肤/提醒/番茄钟/快捷键
素材: smore-inc/clippy.js 官方 Clippy agent (map.png 精灵表 + agent.js 动画定义)
功能: 喝水提醒 / 锻炼提醒 / 番茄钟 / 交互动作 / 拖动 / 右键菜单 / 中英文切换。
运行: python clippy_pet.py    （依赖 Pillow：pip install Pillow）
"""
import base64
import io
import json
import os
import random
import sys
import threading
import time
import tkinter as tk

from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageTk

# ---------------- 配置 ----------------
BASE = os.path.dirname(os.path.abspath(__file__))
if getattr(sys, "frozen", False):
    # PyInstaller 打包后：exe 目录用于设置持久化（可写），
    # 素材在 _MEIPASS（onefile）或 exe 旁 _internal（onedir），只读。
    APP_DIR = os.path.dirname(sys.executable)
    DATA_DIR = getattr(sys, "_MEIPASS",
                       os.path.join(APP_DIR, "_internal"))
else:
    APP_DIR = BASE
    DATA_DIR = BASE
CLIPPY_DIR = os.path.join(DATA_DIR, "assets", "clippy")
FRAMES_DIR = os.path.join(CLIPPY_DIR, "frames")
ANIM_JSON = os.path.join(CLIPPY_DIR, "animations.json")
ZOOM = 2                        # 精灵放大倍数
ZOOM_STEPS = [1, 1.5, 2, 2.5, 3, 4]   # 可调大小档位（倍率）
WATER_INTERVAL_MIN = 45
EXERCISE_INTERVAL_MIN = 60
SNOOZE_MIN = 10
FIRST_DELAY_S = 5
POMO_WORK_MIN = 25
POMO_BREAK_MIN = 5

# 皮肤（clippyjs/clippy.js 官方 agents）
SKINS = [
    ("clippy", "Clippy"),
    ("merlin", "Merlin"),
    ("genie", "Genie"),
    ("bonzi", "Bonzi"),
    ("peedy", "Peedy"),
    ("rover", "Rover"),
    ("links", "Links"),
    ("rocky", "Rocky"),
    ("f1", "F1"),
    ("genius", "Genius"),
]

# 语义 -> 候选动画（皮肤缺省动画时依次回退，见 _load_assets）
SEM_ALT = {
    "blink":      ["IdleAtom", "Blink", "IdleBlink"],
    "water":      ["Alert", "GetAttention"],
    "exercise":   ["GetAttention", "GetAttentionMinor", "Alert"],
    "greet":      ["Greeting", "Greet", "Wave"],
    "wave":       ["Wave", "Pleased", "GestureLeft"],
    "pointdown":  ["GestureDown", "LookDown"],
    "write":      ["Writing", "Write", "WriteContinued"],
    "think":      ["Thinking", "Think", "Searching"],
    "nod":        ["GestureDown", "GestureUp", "Acknowledge"],
    "surprise":   ["Alert", "Surprised", "DontRecognize"],
    "sleep":      ["IdleSnooze", "IdleFallsAsleep", "IdleYawn",
                   "Idle2_1", "RestPose"],
    "happy":      ["Congratulate", "Pleased", "CharacterSucceeds"],
    "artsy":      ["GetArtsy", "DoMagic1", "DoMagic2"],
    "search":     ["Searching", "Search", "ImageSearching"],
    "print":      ["Print", "Shopping"],
    "save":       ["Save", "Money"],
    "lookup":     ["LookUp"],
    "lookdown":   ["LookDown"],
    "lookleft":   ["LookLeft", "GestureLeft"],
    "lookright":  ["LookRight", "GestureRight"],
    "hearing":    ["Hearing_1", "StartListening", "Hearing_2"],
    "mail":       ["SendMail", "Announce"],
    "check":      ["CheckingSomething", "Process", "Pleased"],
    "processing": ["Processing", "Process", "Cooking"],
    "goodbye":    ["GoodBye", "Goodbye", "Hide"],
    "attention":  ["GetAttention", "GetAttentionMinor", "GetAttentionContinued"],
    "trash":      ["EmptyTrash", "Decline"],
    "greeting":   ["Greeting", "Greet", "Wave"],
    "gestureleft":  ["GestureLeft", "MoveLeft"],
    "gestureright": ["GestureRight", "MoveRight"],
    "gestureup":    ["GestureUp", "MoveUp"],
    "lookupright":  ["LookUpRight", "LookUp"],
    "lookupleft":   ["LookUpLeft", "LookUp"],
    "lookdownleft": ["LookDownLeft", "LookDown"],
    "lookdownright":["LookDownRight", "LookDown"],
}
SETTINGS_FILE = os.path.join(APP_DIR, "settings.json")

MAX_ANIM_MS = 5000            # 非循环动画最长播放时长（超时优雅退出）
MAX_EXIT_STEPS = 30           # 退出序列最大帧数（防二次循环）
IDLE_ACTION_MIN_MS = 8000     # 待机小动作穿插最小间隔
IDLE_ACTION_MAX_MS = 16000    # 待机小动作穿插最大间隔
IDLE_ANIM_SPEED = 2.5         # 待机动画帧时长系数（>1 放慢，呼吸更舒缓）

# 全局快捷键 -> 动画（默认映射，可在「快捷键动画设置」中编辑）
DEFAULT_HOTKEYS = {
    "save":       {"mods": ["Ctrl"], "key": "s"},
    "print":      {"mods": ["Ctrl"], "key": "p"},
    "search":     {"mods": ["Ctrl"], "key": "f"},
    "mail":       {"mods": ["Ctrl", "Shift"], "key": "m"},
    "trash":      {"mods": ["Ctrl"], "key": "Delete"},
    "processing": {"mods": ["Ctrl", "Shift"], "key": "p"},
}
HOTKEY_ACTIONS = list(DEFAULT_HOTKEYS)   # 顺序即设置列表顺序
HK_MOD_KEYS = ("Ctrl", "Shift", "Alt")


def _load_settings():
    """读取持久化设置；无文件/损坏时返回空 dict（用默认值）。"""
    try:
        with open(SETTINGS_FILE, encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, dict) else {}
    except Exception:
        return {}

# ---------------- 翻译表 ----------------
TR = {
    "zh": {
        "bubble_title": "回形针助手",
        "menu_water": "💧喝水提醒",
        "menu_ex": "🏃锻炼提醒",
        "menu_pomo_start": "🍅开始番茄钟",
        "menu_pomo_stop": "⏹停止番茄钟",
        "menu_pomo_settings": "⏱番茄钟设置…",
        "menu_perform": "表演动作",
        "menu_water_now": "立即提醒喝水",
        "menu_ex_now": "立即提醒锻炼",
        "menu_greet": "👋打个招呼",
        "menu_about": "ℹ关于",
        "menu_exit": "✖退出",
        "menu_pin": "📌显示在最前",
        "menu_dnd": "🌙全屏免打扰",
        "menu_auto": "⚡开机自启动",
        "menu_hotkey": "⌨全局快捷键动画",
        "hotkey_on_msg": "全局快捷键动画已开启",
        "hotkey_off_msg": "全局快捷键动画已关闭",
        "menu_lang": "🌐切换为 English",
        "menu_size": "调整大小",
        "menu_skin": "换肤",
        "skin_switched": "已切换皮肤：{skin}",
        "act_wave": "👋挥手", "act_pointdown": "⬇向下示意", "act_think": "🤔思考",
        "act_write": "✍写字", "act_happy": "🎉庆祝", "act_artsy": "🌈画彩虹",
        "act_search": "🔍搜索", "act_print": "🖨打印", "act_save": "💾保存",
        "act_sleep": "😴睡觉", "act_hearing": "👂歪头听",
        "act_lookup": "⬆看上面", "act_lookdown": "⬇看下面",
        "act_lookleft": "⬅看左边", "act_lookright": "➡看右边",
        "act_surprise": "😲惊讶",
        "act_mail": "📧发邮件",
        "act_check": "🔎检查中", "act_processing": "⚙处理中",
        "act_goodbye": "👋再见",
        "act_attention": "📢吸引注意", "act_trash": "🗑清空回收站",
        "act_greeting": "🙋打招呼",
        "act_gestureleft": "👈左示意", "act_gestureright": "👉右示意",
        "act_gestureup": "👆上示意",
        "act_lookupright": "↗看右上", "act_lookupleft": "↖看左上",
        "act_lookdownleft": "↙看左下", "act_lookdownright": "↘看右下",
        "water_tips": [
            "看起来你已经盯着屏幕好一会儿了。\n要去接杯水喝吗？",
            "温馨提示：身体缺水会让注意力下降哦，\n喝口水吧！",
            "咕噜咕噜…… 我虽然是回形针，\n也知道人需要喝水！",
            "喝水时间到！一天 8 杯水，\n你完成几杯啦？",
        ],
        "ex_tips": [
            "久坐伤身！站起来伸展一下，\n活动活动脖子和肩膀吧。",
            "该起来动一动啦！\n走两步、看看远处，眼睛也需要休息。",
            "我可以一辈子保持一个姿势，\n但你不行——起来拉伸一下！",
            "锻炼提醒：做 5 个深蹲，\n或者绕桌子走一圈？",
        ],
        "btn_done": "喝过了 ✓", "btn_snooze": "{n}分钟后",
        "btn_off": "今天别再提醒", "btn_ex_done": "已活动 ✓",
        "btn_pomo_next": "继续工作", "btn_pomo_stop": "结束", "btn_ok": "好",
        "pomo_running": "番茄钟已经在走啦！\n右键菜单可以停止。",
        "pomo_start": "🍅 番茄钟启动！专注工作 {n} 分钟。\n我会在这段时间里看着你哦～",
        "pomo_break": "工作辛苦啦！休息 {n} 分钟。\n喝口水、看看远处吧。",
        "pomo_done": "🍅 第 {n} 个番茄完成！\n要继续下一轮吗？",
        "pomo_stopped": "番茄钟已停止。\n本轮共完成 {n} 个 🍅",
        "pomo_stop_first": "请先停止当前的番茄钟，再修改设置。",
        "settings_title": "番茄钟设置",
        "settings_work": "工作时长（分钟）",
        "settings_break": "休息时长（分钟）",
        "menu_water_settings": "⚙喝水提醒设置…",
        "menu_ex_settings": "⚙锻炼提醒设置…",
        "water_settings_title": "喝水提醒设置",
        "water_settings_label": "提醒间隔（分钟）",
        "ex_settings_title": "锻炼提醒设置",
        "ex_settings_label": "提醒间隔（分钟）",
        "water_settings_saved": "喝水提醒间隔已设为 {n} 分钟",
        "ex_settings_saved": "锻炼提醒间隔已设为 {n} 分钟",
        "settings_saved": "番茄钟已设置：\n工作 {w} 分钟 / 休息 {b} 分钟。",
        "btn_cancel": "取消",
        "water_done_msg": "好样的！保持水分，头脑更清醒 💧",
        "snooze_msg": "好的，{n} 分钟后我再来叫你。",
        "water_off_msg": "明白，今天不再提醒喝水。\n（右键我可以重新开启）",
        "ex_done_msg": "动起来真棒！给你点赞 👍",
        "ex_snooze_msg": "好，{n} 分钟后再提醒你活动。",
        "ex_off_msg": "好的，今天不再提醒锻炼。\n（右键我可以重新开启）",
        "water_on_msg": "喝水提醒已开启 💧",
        "ex_on_msg": "锻炼提醒已开启 🏃",
        "greet_msgs": [
            "你好呀！我是你的回形针助手。\n我会定时提醒你喝水和活动哦～",
            "看起来你在努力工作呢！\n别忘了照顾好自己。",
            "需要帮忙吗？\n右键我可以设置提醒、开番茄钟。",
        ],
        "about": "Clippy 桌面宠物 v0.2\n"
                 "官方 Clippy 素材逐帧动画\n"
                 "素材来源: smore-inc/clippy.js（MIT）\n"
                 "Python/tkinter + Pillow 打造。",
        "lang_switched": "语言已切换为简体中文 ✓",
    },
    "en": {
        "bubble_title": "Clippy Assistant",
        "menu_water": "💧Water reminder",
        "menu_ex": "🏃Exercise reminder",
        "menu_pomo_start": "🍅Start Pomodoro",
        "menu_pomo_stop": "⏹Stop Pomodoro",
        "menu_pomo_settings": "⏱Pomodoro settings…",
        "menu_perform": "Perform actions",
        "menu_water_now": "Remind me to drink now",
        "menu_ex_now": "Remind me to move now",
        "menu_greet": "👋Say hello",
        "menu_about": "ℹAbout",
        "menu_exit": "✖Exit",
        "menu_pin": "📌Always on top",
        "menu_dnd": "🌙Fullscreen DND",
        "menu_auto": "⚡Launch at startup",
        "menu_hotkey": "⌨Global hotkey animations",
        "hotkey_on_msg": "Global hotkey animations enabled",
        "hotkey_off_msg": "Global hotkey animations disabled",
        "menu_lang": "🌐Switch to 中文",
        "menu_size": "Resize",
        "menu_skin": "Skin",
        "skin_switched": "Skin switched: {skin}",
        "act_wave": "👋Wave", "act_pointdown": "⬇Point down", "act_think": "🤔Think",
        "act_write": "✍Write", "act_happy": "🎉Celebrate",
        "act_artsy": "🌈Draw rainbow", "act_search": "🔍Search",
        "act_print": "🖨Print", "act_save": "💾Save", "act_sleep": "😴Sleep",
        "act_hearing": "👂Listen",
        "act_lookup": "⬆Look up", "act_lookdown": "⬇Look down",
        "act_lookleft": "⬅Look left", "act_lookright": "➡Look right",
        "act_surprise": "😲Surprise",
        "act_mail": "📧Mail",
        "act_check": "🔎Check", "act_processing": "⚙Process",
        "act_goodbye": "👋Goodbye",
        "act_attention": "📢Attention", "act_trash": "🗑Empty trash",
        "act_greeting": "🙋Greeting",
        "act_gestureleft": "👈Gest left", "act_gestureright": "👉Gest right",
        "act_gestureup": "👆Gest up",
        "act_lookupright": "↗Up-right", "act_lookupleft": "↖Up-left",
        "act_lookdownleft": "↙Down-left", "act_lookdownright": "↘Down-right",
        "water_tips": [
            "Looks like you've been staring at the screen.\nTime to grab some water?",
            "Heads up: dehydration hurts focus.\nTake a sip!",
            "Gulp gulp… I'm a paperclip,\nbut even I know humans need water!",
            "Water break! 8 glasses a day —\nhow many have you had?",
        ],
        "ex_tips": [
            "Sitting too long is bad! Stand up,\nstretch your neck and shoulders.",
            "Time to move around!\nWalk a few steps and look into the distance.",
            "I can hold one pose forever,\nbut you can't — get up and stretch!",
            "Exercise alert: do 5 squats,\nor walk around your desk?",
        ],
        "btn_done": "Done ✓", "btn_snooze": "{n} min later",
        "btn_off": "Not today", "btn_ex_done": "Moved ✓",
        "btn_pomo_next": "Next round", "btn_pomo_stop": "Stop", "btn_ok": "OK",
        "pomo_running": "A Pomodoro is already running!\nRight-click to stop it.",
        "pomo_start": "🍅 Pomodoro started! Focus for {n} minutes.\nI'll be watching you～",
        "pomo_break": "Great work! Take a {n}-minute break.\nDrink some water, look away.",
        "pomo_done": "🍅 Pomodoro #{n} complete!\nStart another round?",
        "pomo_stopped": "Pomodoro stopped.\n{n} 🍅 completed this session.",
        "pomo_stop_first": "Please stop the running Pomodoro\nbefore changing the settings.",
        "settings_title": "Pomodoro Settings",
        "settings_work": "Work minutes",
        "settings_break": "Break minutes",
        "menu_water_settings": "⚙Water reminder settings...",
        "menu_ex_settings": "⚙Exercise reminder settings...",
        "water_settings_title": "Water Reminder Settings",
        "water_settings_label": "Interval (minutes)",
        "ex_settings_title": "Exercise Reminder Settings",
        "ex_settings_label": "Interval (minutes)",
        "water_settings_saved": "Water reminder interval set to {n} min",
        "ex_settings_saved": "Exercise reminder interval set to {n} min",
        "settings_saved": "Pomodoro set:\n{w} min work / {b} min break.",
        "btn_cancel": "Cancel",
        "water_done_msg": "Nice! Stay hydrated, stay sharp 💧",
        "snooze_msg": "OK, I'll remind you in {n} minutes.",
        "water_off_msg": "Understood, no more water reminders today.\n(Right-click to re-enable)",
        "ex_done_msg": "Great job moving! Thumbs up 👍",
        "ex_snooze_msg": "OK, I'll remind you to move in {n} minutes.",
        "ex_off_msg": "OK, no more exercise reminders today.\n(Right-click to re-enable)",
        "water_on_msg": "Water reminders on 💧",
        "ex_on_msg": "Exercise reminders on 🏃",
        "greet_msgs": [
            "Hi! I'm your paperclip assistant.\nI'll remind you to drink water and move!",
            "Looks like you're working hard!\nDon't forget to take care of yourself.",
            "Need help? Right-click me for\nreminders, actions and Pomodoro.",
        ],
        "about": "Clippy Desktop Pet v0.2\n"
                 "Official Clippy sprite animations\n"
                 "Sprites: smore-inc/clippy.js (MIT)\n"
                 "Built with Python/tkinter + Pillow.",
        "lang_switched": "Language switched to English ✓",
    },
}

# 官方 Clippy 动画名（clippyjs/clippy.js）
ANIM_IDLE = "Idle1_1"

# 语义 -> 官方动画
ACT = {
    "blink":    "IdleAtom",
    "water":    "Alert",
    "exercise": "GetAttention",
    "greet":    "Greeting",
    "wave":     "Wave",
    "pointdown": "GestureDown",
    "write":    "Writing",
    "think":    "Thinking",
    "nod":      "GestureDown",
    "surprise": "Alert",
    "sleep":    "IdleSnooze",
    "happy":    "Congratulate",
    "artsy":    "GetArtsy",
    "search":   "Searching",
    "print":    "Print",
    "save":     "Save",
    "lookup":   "LookUp",
    "lookdown": "LookDown",
    "lookleft": "LookLeft",
    "lookright": "LookRight",
    "hearing":  "Hearing_1",
    "mail":     "SendMail",
    "check":    "CheckingSomething",
    "processing": "Processing",
    "goodbye":  "GoodBye",
    "attention": "GetAttention",
    "trash":    "EmptyTrash",
    "greeting": "Greeting",
    "gestureleft": "GestureLeft",
    "gestureright": "GestureRight",
    "gestureup": "GestureUp",
    "lookupright": "LookUpRight",
    "lookupleft": "LookUpLeft",
    "lookdownleft": "LookDownLeft",
    "lookdownright": "LookDownRight",
}

# 表演动作子菜单项：(翻译key, 语义名)
PERFORM_ITEMS = [
    ("act_wave", "wave"), ("act_pointdown", "pointdown"), ("act_think", "think"),
    ("act_write", "write"), ("act_happy", "happy"), ("act_artsy", "artsy"),
    ("act_search", "search"), ("act_print", "print"), ("act_save", "save"),
    ("act_sleep", "sleep"), ("act_hearing", "hearing"),
    ("act_lookup", "lookup"), ("act_lookdown", "lookdown"),
    ("act_lookleft", "lookleft"), ("act_lookright", "lookright"),
    ("act_surprise", "surprise"),
    ("act_mail", "mail"),
    ("act_check", "check"), ("act_processing", "processing"),
    ("act_goodbye", "goodbye"),
    ("act_attention", "attention"), ("act_trash", "trash"),
    ("act_greeting", "greeting"),
    ("act_gestureleft", "gestureleft"), ("act_gestureright", "gestureright"),
    ("act_gestureup", "gestureup"),
    ("act_lookupright", "lookupright"), ("act_lookupleft", "lookupleft"),
    ("act_lookdownleft", "lookdownleft"), ("act_lookdownright", "lookdownright"),
]


class SpeechBubble(tk.Toplevel):
    """Clippy 风格白色气泡（与设置对话框同一渲染技术）：
    白底圆角矩形 + 黑边 + 三角尾巴正对 Clippy，标题/文本/按钮整张
    Pillow 渲染成不透明 PNG，按钮/关闭用 Canvas 点击热区。
    所有通知/对话框统一此气泡样式。"""
    BG = "#FF00FF"           # 窗口底色 = 色键（图片圆角外也为此色 → 透明）

    def __init__(self, master, text, buttons, on_action, hide_cb,
                 auto_hide_ms=None, anchor=None, title="回形针助手"):
        super().__init__(master)
        self.on_action = on_action
        self.hide_cb = hide_cb
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        # Windows 色键透明：图片中 MAGENTA 像素显示为透明
        self.attributes("-transparentcolor", "magenta")
        self.configure(bg=self.BG)
        self._auto_job = None

        f_text = _load_font(11)
        f_title = _load_font(11)

        # ---- 测量排版 ----
        wrap_px = 220
        lines = _wrap_text(text, f_text, wrap_px)
        line_h = max(16, f_text.getbbox("中")[3] + 5)
        text_h = len(lines) * line_h + 4
        text_w = max((f_text.getlength(l) for l in lines), default=0)
        btns_total = (len(buttons) * 92 + (len(buttons) - 1) * 10) if buttons else 0
        body_w = max(200, min(int(text_w) + 36, wrap_px + 36),
                     btns_total + 24, int(f_title.getlength(title)) + 60)
        body_h = 40 + text_h + (40 if buttons else 10)

        # ---- 摆放（统一四方位 + 尾巴正对 Clippy）----
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        cw, ch = 248, 186
        if anchor:
            cx, cy = anchor
        else:
            cx, cy = sw - cw - 40, sh - ch - 40
        side, bx, by = _pick_side(cx, cy, cw, ch, sw, sh,
                                  body_w + TAIL_LEN, body_h + TAIL_LEN)
        if side == "top":
            edge, ox, oy, w2, h2 = "bottom", 0, 0, body_w, body_h + TAIL_LEN
        elif side == "bottom":
            edge, ox, oy, w2, h2 = "top", 0, TAIL_LEN, body_w, body_h + TAIL_LEN
        elif side == "left":
            edge, ox, oy, w2, h2 = "right", 0, 0, body_w + TAIL_LEN, body_h
        else:
            edge, ox, oy, w2, h2 = "left", TAIL_LEN, 0, body_w + TAIL_LEN, body_h
        bx = max(4, min(bx, sw - w2 - 4))
        by = max(4, min(by, sh - h2 - 4))
        if edge in ("bottom", "top"):
            tp = cx + cw // 2 - bx
            tp = max(30, min(tp, w2 - 30))
        else:
            tp = cy + ch // 2 - by
            tp = max(30, min(tp, h2 - 30))
        self._ox, self._oy = ox, oy
        self._body_w, self._body_h = body_w, body_h
        self._tail_edge, self._tail_pos = edge, tp

        # ---- 整张渲染气泡 PNG ----
        self._photo = tk.PhotoImage(
            master=self,
            data=render_speech_png(w2, h2, body_w, body_h, title, lines,
                                   buttons, edge, tp))
        cv = tk.Canvas(self, width=w2, height=h2, bg=self.BG,
                       highlightthickness=0, bd=0)
        cv.pack()
        self._cv = cv
        self._img = cv.create_image(w2 // 2, h2 // 2, image=self._photo)

        # ---- 点击热区 ----
        self._buttons = []
        if buttons:
            x0 = body_w // 2 - btns_total // 2 + ox
            by0 = body_h - 34 + oy
            for _label, key in buttons:
                self._buttons.append(((x0, by0, x0 + 92, by0 + 24), key))
                x0 += 102
        self._close_rect = (body_w - 36 + ox, 8 + oy, body_w - 8 + ox, 30 + oy)
        cv.bind("<Button-1>", self._on_click)
        cv.bind("<Motion>", self._on_motion)

        self.geometry(f"+{bx}+{by}")
        if auto_hide_ms:
            self._auto_job = self.after(auto_hide_ms, self.hide)

    def _in_rect(self, px, py, r):
        x1, y1, x2, y2 = r
        return x1 <= px <= x2 and y1 <= py <= y2

    def _on_click(self, e):
        for rect, key in self._buttons:
            if self._in_rect(e.x, e.y, rect):
                if callable(self.on_action):
                    self.on_action(key)
                self.hide()
                return
        if self._in_rect(e.x, e.y, self._close_rect):
            self.hide()

    def _on_motion(self, e):
        over = any(self._in_rect(e.x, e.y, r) for r, _ in self._buttons) \
            or self._in_rect(e.x, e.y, self._close_rect)
        self._cv.config(cursor="hand2" if over else "")

    def hide(self):
        if self._auto_job is not None:
            try:
                self.after_cancel(self._auto_job)
            except Exception:
                pass
            self._auto_job = None
        try:
            if callable(self.hide_cb):
                self.hide_cb()
            self.destroy()
        except Exception:
            pass


TAIL_LEN = 22              # 三角尾巴伸出长度（px）
BUBBLE_W, BUBBLE_H = 300, 196
BODY_X0, BODY_Y0, BODY_X1, BODY_Y1 = 4, 4, 296, 148
MAGENTA = (255, 0, 255)     # 窗口透明键控色（-transparentcolor）

# 开机自启动（注册表 HKCU Run 键，用户级免管理员）
AUTOSTART_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
AUTOSTART_NAME = "ClippyPet"


def _autostart_enabled():
    """读取注册表，判断开机自启动是否已启用。"""
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, AUTOSTART_KEY) as k:
            winreg.QueryValueEx(k, AUTOSTART_NAME)
            return True
    except OSError:
        return False


def _set_autostart(on):
    """写/删注册表 Run 项：启用写入 pythonw 启动命令，禁用删除。"""
    import sys
    import winreg
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, AUTOSTART_KEY,
                        0, winreg.KEY_SET_VALUE) as k:
        if on:
            pyw = os.path.join(os.path.dirname(sys.executable), "pythonw.exe")
            if not os.path.exists(pyw):
                pyw = sys.executable      # 回退：无 pythonw 时用当前解释器
            cmd = '"%s" "%s"' % (pyw, os.path.abspath(__file__))
            winreg.SetValueEx(k, AUTOSTART_NAME, 0, winreg.REG_SZ, cmd)
        else:
            try:
                winreg.DeleteValue(k, AUTOSTART_NAME)
            except FileNotFoundError:
                pass


def _punch_transparent(img, body_box, tri, radius=16):
    """把气泡形状（圆角矩形 + 三角尾巴）之外的所有像素强制填充为
    纯 MAGENTA 色键（抗锯齿边缘二值化）——窗口用
    `-transparentcolor magenta` 时形状外区域系统级透明。
    气泡形状直接画进图像内部：视觉对齐完全由图像决定，
    不再依赖 SetWindowRgn 裁剪，彻底消除"气泡与边框偏移"。"""
    mask = Image.new("L", img.size, 0)
    md = ImageDraw.Draw(mask)
    md.rounded_rectangle(body_box, radius=radius, fill=255)
    md.polygon(tri, fill=255)
    mask = mask.point(lambda v: 255 if v > 127 else 0)  # 二值化防混色
    bg = Image.new("RGB", img.size, MAGENTA)
    img.paste(bg, (0, 0), ImageOps.invert(mask))
    return img


def _wrap_text(text, font, max_px):
    """按词/字符贪心换行，返回行列表（Pillow 文本自动换行替代）。"""
    lines = []
    for para in str(text).split("\n"):
        words = para.split(" ")
        cur = ""
        for w in words:
            trial = (cur + " " + w).strip()
            if font.getlength(trial) <= max_px or not cur:
                cur = trial
            else:
                lines.append(cur)
                cur = w
        lines.append(cur)
    return lines


def _load_font(size):
    """加载系统中文/英文字体，失败回退默认字体。"""
    for path in ("C:/Windows/Fonts/msyh.ttc", "C:/Windows/Fonts/msyhbd.ttc",
                 "C:/Windows/Fonts/simhei.ttf", "C:/Windows/Fonts/simsun.ttc"):
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except OSError:
                continue
    return ImageFont.load_default()


def _draw_button(d, x1, y1, x2, y2, text, font):
    """Pillow 绘制 Windows 风格按钮（浅灰底 + 顶部高光 + 黑字）。"""
    d.rounded_rectangle([x1, y1, x2, y2], radius=5,
                        fill=(235, 235, 235), outline=(90, 90, 90), width=1)
    d.line([(x1 + 3, y1 + 1), (x2 - 3, y1 + 1)], fill=(255, 255, 255))
    bbox = d.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    d.text(((x1 + x2) / 2 - tw / 2 - bbox[0],
            (y1 + y2) / 2 - th / 2 - bbox[1]),
           text, font=font, fill=(16, 16, 16))


def render_bubble_png(w, h, title, work_label, break_label,
                      ok_text, cancel_text, tail_edge="bottom",
                      tail_pos=158, single=False):
    """整张渲染原版 Clippy 风格气泡：淡黄底圆角矩形 + 黑边 + 三角尾巴。
    尾巴可朝下/上/左/右（tail_edge），tail_pos 为尾巴在对边上正对
    Clippy 中心的坐标。圆角外填充 MAGENTA 色键（窗口透明），
    单图层不透明 PNG——无 alpha 混色、无图层错位、无控件溢出。"""
    CREAM = (247, 247, 200)   # 原版 Clippy 气泡经典淡黄底
    BLACK = (16, 16, 16)
    img = Image.new("RGB", (w, h), MAGENTA)
    d = ImageDraw.Draw(img)
    f_title = _load_font(13)
    f_body = _load_font(11)
    f_btn = _load_font(11)

    ox = TAIL_LEN if tail_edge == "left" else 0
    oy = TAIL_LEN if tail_edge == "top" else 0
    tp = tail_pos

    # 气泡主体：淡黄底圆角矩形 + 黑边框（随尾巴方向平移）
    d.rounded_rectangle([BODY_X0 + ox, BODY_Y0 + oy,
                         BODY_X1 + ox, BODY_Y1 + oy],
                        radius=16, fill=CREAM, outline=BLACK, width=2)
    # 三角尾巴（淡黄填充 + 两条斜边黑线，正对 Clippy 中心）
    if tail_edge == "bottom":
        tri = [(tp - 13, 148), (tp + 13, 148), (tp, 170)]
    elif tail_edge == "top":
        tri = [(tp - 13, 26), (tp + 13, 26), (tp, 4)]
    elif tail_edge == "left":
        tri = [(26, tp - 13), (26, tp + 13), (4, tp)]
    else:  # right
        tri = [(296, tp - 13), (296, tp + 13), (318, tp)]
    d.polygon(tri, fill=CREAM)
    # 盖掉圆角矩形底边黑线在三角根部的残留（原版无此横线）
    d.line([tri[0], tri[1]], fill=CREAM, width=3)
    d.line([tri[0], tri[2]], fill=BLACK, width=2)
    d.line([tri[1], tri[2]], fill=BLACK, width=2)

    # 标题 / 标签（随 body 平移）
    d.text((150 + ox, 26 + oy), title, font=f_title, fill=BLACK, anchor="mm")
    d.text((28 + ox, 59 + oy), work_label, font=f_body, fill=BLACK, anchor="lm")
    if not single:
        d.text((28 + ox, 93 + oy), break_label, font=f_body,
               fill=BLACK, anchor="lm")
    # 输入框白底（无边框 Entry 将叠放其上）
    d.rectangle([168 + ox, 46 + oy, 242 + ox, 72 + oy],
                fill=(255, 255, 255), outline=(128, 128, 128))
    if not single:
        d.rectangle([168 + ox, 80 + oy, 242 + ox, 106 + oy],
                    fill=(255, 255, 255), outline=(128, 128, 128))
    # 按钮
    _draw_button(d, 72 + ox, 112 + oy, 138 + ox, 140 + oy, ok_text, f_btn)
    _draw_button(d, 162 + ox, 112 + oy, 228 + ox, 140 + oy, cancel_text, f_btn)

    # 形状外强制填充色键（与绘制用同一圆角矩形/三角形几何）
    _punch_transparent(img, [BODY_X0 + ox, BODY_Y0 + oy,
                             BODY_X1 + ox, BODY_Y1 + oy], tri)

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode("ascii")


def render_speech_png(w, h, body_w, body_h, title, lines, buttons,
                      tail_edge, tail_pos):
    """整张渲染 Clippy 风格消息气泡：淡黄底圆角矩形 + 黑边 + 三角尾巴
    + 标题/关闭 ✕/多行正文/按钮。圆角外填充 MAGENTA 色键（窗口透明），
    单图层不透明 PNG。w/h 为窗口尺寸（含尾巴）。"""
    CREAM = (247, 247, 200)   # 原版 Clippy 气泡经典淡黄底
    BLACK = (16, 16, 16)
    img = Image.new("RGB", (w, h), MAGENTA)
    d = ImageDraw.Draw(img)
    f_title = _load_font(11)
    f_text = _load_font(11)
    f_btn = _load_font(11)

    ox = TAIL_LEN if tail_edge == "left" else 0
    oy = TAIL_LEN if tail_edge == "top" else 0
    tp = tail_pos

    # 气泡主体
    d.rounded_rectangle([4 + ox, 4 + oy, body_w - 4 + ox, body_h - 4 + oy],
                        radius=16, fill=CREAM, outline=BLACK, width=2)
    # 三角尾巴
    if tail_edge == "bottom":
        tri = [(tp - 13, body_h - 4 + oy), (tp + 13, body_h - 4 + oy),
               (tp, body_h - 4 + oy + TAIL_LEN)]
    elif tail_edge == "top":
        tri = [(tp - 13, 4 + oy), (tp + 13, 4 + oy), (tp, 4 + oy - TAIL_LEN)]
    elif tail_edge == "left":
        tri = [(4 + ox, tp - 13), (4 + ox, tp + 13), (4 + ox - TAIL_LEN, tp)]
    else:  # right
        tri = [(body_w - 4 + ox, tp - 13), (body_w - 4 + ox, tp + 13),
               (body_w - 4 + ox + TAIL_LEN, tp)]
    d.polygon(tri, fill=CREAM)
    # 盖掉圆角矩形底边黑线在三角根部的残留（原版无此横线）
    d.line([tri[0], tri[1]], fill=CREAM, width=3)
    d.line([tri[0], tri[2]], fill=BLACK, width=2)
    d.line([tri[1], tri[2]], fill=BLACK, width=2)

    # 标题 + 关闭 X（用线条绘制，避免字体缺字符显示方框）
    d.text((18 + ox, 14 + oy), title, font=f_title, fill=(64, 64, 64))
    cx0 = body_w - 22 + ox
    cy0 = 15 + oy
    d.line([(cx0, cy0), (cx0 + 10, cy0 + 10)], fill=(128, 128, 128), width=1)
    d.line([(cx0 + 10, cy0), (cx0, cy0 + 10)], fill=(128, 128, 128), width=1)
    # 正文（多行）
    y = 34 + oy
    line_h = max(16, f_text.getbbox("中")[3] + 5)
    for ln in lines:
        d.text((18 + ox, y), ln, font=f_text, fill=(26, 26, 26))
        y += line_h
    # 按钮（底部居中）
    if buttons:
        bw, bh, gap = 92, 24, 10
        total = len(buttons) * bw + (len(buttons) - 1) * gap
        x0 = body_w // 2 - total // 2 + ox
        by0 = body_h - 34 + oy
        for label, _k in buttons:
            _draw_button(d, x0, by0, x0 + bw, by0 + bh, label, f_btn)
            x0 += bw + gap

    # 形状外强制填充色键（与绘制用同一圆角矩形/三角形几何）
    _punch_transparent(img, [4 + ox, 4 + oy, body_w - 4 + ox,
                             body_h - 4 + oy], tri)

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode("ascii")




def _pick_side(cx, cy, cw, ch, sw, sh, w, h):
    """所有弹出对话框共用的四方位摆放策略：
    优先 Clippy 上方 → 下方 → 左侧 → 右侧，紧贴对应边（6px 间隙），
    贴屏边自动翻转方位，屏幕内夹紧。返回 (side, bx, by)。"""
    if cy - h - 6 >= 4:
        side, bx, by = "top", cx + cw // 2 - w // 2, cy - h - 6
    elif cy + ch + 6 + h <= sh - 4:
        side, bx, by = "bottom", cx + cw // 2 - w // 2, cy + ch + 6
    elif cx - w - 6 >= 4:
        side, bx, by = "left", cx - w - 6, cy + ch // 2 - h // 2
    elif cx + cw + 6 + w <= sw - 4:
        side, bx, by = "right", cx + cw + 6, cy + ch // 2 - h // 2
    else:
        side, bx, by = "top", cx + cw // 2 - w // 2, max(4, cy - h - 6)
    bx = max(4, min(bx, sw - w - 4))
    by = max(4, min(by, sh - h - 4))
    return side, bx, by


def plan_bubble_placement(cx, cy, cw, ch, sw, sh):
    """带尾巴设置气泡的摆放：方位由 _pick_side 统一决策，
    再细化尾巴几何——尾巴尖紧贴 Clippy 对应边，正对 Clippy 中心。
    返回 (x, y, w, h, tail_edge, tail_pos)。"""
    W, H = BUBBLE_W, BUBBLE_H
    TL = TAIL_LEN
    # 左右摆放时窗口更宽（含尾巴），判定用实际窗口宽
    side, _, _ = _pick_side(cx, cy, cw, ch, sw, sh, W + TL, H)
    if side == "top":
        edge, w2, h2 = "bottom", W, H
        bx, by = cx + cw // 2 - 160, cy - 172
    elif side == "bottom":
        edge, w2, h2 = "top", W, H
        bx, by = cx + cw // 2 - 160, cy + ch - 4
    elif side == "left":
        edge, w2, h2 = "right", W + TL, H
        bx, by = cx - W - TL, cy + ch // 2 - H // 2
    else:  # right
        edge, w2, h2 = "left", W + TL, H
        bx, by = cx + cw - 4, cy + ch // 2 - H // 2
    bx = max(4, min(bx, sw - w2 - 4))
    by = max(4, min(by, sh - h2 - 4))
    # 尾巴正对 Clippy 中心（窗口内坐标，夹紧在安全范围）
    if edge in ("bottom", "top"):
        tp = cx + cw // 2 - bx
        tp = max(40, min(tp, w2 - 40))
    else:
        tp = cy + ch // 2 - by
        tp = max(40, min(tp, h2 - 40))
    return bx, by, w2, h2, edge, tp


class SettingsDialog(tk.Toplevel):
    """原版 Clippy 风格气泡设置对话框：
    整张气泡（白底圆角矩形 + 黑边 + 三角尾巴 + 文字/按钮）由 Pillow
    渲染成单张不透明 PNG；输入框用无边框 Entry 叠放，按钮用点击热区。"""
    BG = "#FF00FF"           # 窗口底色 = 色键（图片圆角外也为此色 → 透明）

    def __init__(self, master, title, work_label, break_label, work, brk,
                 ok_text, cancel_text, on_ok, clippy_pos, single=False):
        super().__init__(master)
        self.on_ok = on_ok
        self._single = single
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        # Windows 色键透明：图片中 MAGENTA 像素显示为透明
        self.attributes("-transparentcolor", "magenta")
        self.configure(bg=self.BG)

        # 摆放规划：位置 + 窗口尺寸 + 尾巴方向/位置（正对 Clippy 中心）
        cx, cy = clippy_pos
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        bx, by, W, H, edge, tail_pos = plan_bubble_placement(
            cx, cy, 248, 186, sw, sh)
        self._tail_edge = edge
        self._tail_pos = tail_pos
        self._ox = TAIL_LEN if edge == "left" else 0
        self._oy = TAIL_LEN if edge == "top" else 0

        self.work_var = tk.StringVar(value=str(work))
        self.brk_var = tk.StringVar(value=str(brk))

        # 整张气泡渲染成一张不透明 PNG（无 alpha、无图层错位）
        self._photo = tk.PhotoImage(
            master=self,
            data=render_bubble_png(W, H, title, work_label, break_label,
                                   ok_text, cancel_text, edge, tail_pos,
                                   single=single),
        )
        cv = tk.Canvas(self, width=W, height=H, bg=self.BG,
                       highlightthickness=0, bd=0)
        cv.pack()
        self._cv = cv
        self._img = cv.create_image(W // 2, H // 2, image=self._photo)

        ox, oy = self._ox, self._oy
        # 输入框：无边框 Entry 叠放在渲染好的白底输入框上（Entry 保持白底）
        self._widgets = []
        entries = [(self.work_var, 59 + oy)]
        if not single:
            entries.append((self.brk_var, 93 + oy))
        for var, y in entries:
            e = tk.Entry(self, textvariable=var, width=4, justify="center",
                         bd=0, relief="flat", bg="#FFFFFF",
                         highlightthickness=0,
                         font=("Microsoft YaHei UI", 10))
            self._widgets.append(e)
            cv.create_window(205 + ox, y, window=e)

        # 按钮热区（与渲染坐标一致）
        self._btn_ok = (72 + ox, 112 + oy, 138 + ox, 140 + oy)
        self._btn_cancel = (162 + ox, 112 + oy, 228 + ox, 140 + oy)
        cv.bind("<Button-1>", self._on_click)
        cv.bind("<Motion>", self._on_motion)

        self.geometry(f"+{bx}+{by}")

        self.bind("<Return>", lambda e: self._ok())
        self.bind("<Escape>", lambda e: self.destroy())
        self.grab_set()
        self.focus_force()

    @staticmethod
    def _in_rect(px, py, r):
        x1, y1, x2, y2 = r
        return x1 <= px <= x2 and y1 <= py <= y2

    def _on_click(self, e):
        if self._in_rect(e.x, e.y, self._btn_ok):
            self._ok()
        elif self._in_rect(e.x, e.y, self._btn_cancel):
            self.destroy()

    def _on_motion(self, e):
        if (self._in_rect(e.x, e.y, self._btn_ok)
                or self._in_rect(e.x, e.y, self._btn_cancel)):
            self._cv.config(cursor="hand2")
        else:
            self._cv.config(cursor="")

    def _ok(self):
        try:
            work = int(self.work_var.get())
            if self._single:
                if not (1 <= work <= 180):
                    raise ValueError
            else:
                brk = int(self.brk_var.get())
                if not (1 <= work <= 180 and 1 <= brk <= 180):
                    raise ValueError
        except ValueError:
            self.bell()
            return
        cb = self.on_ok
        self.destroy()
        if cb:
            if self._single:
                cb(work)
            else:
                cb(work, brk)




class ClippyPet:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Clippy Pet")
        self.root.overrideredirect(True)

        # 加载持久化设置（在窗口属性、资源加载之前应用）
        self._s = _load_settings()
        self.lang = self._s.get("lang", "zh")
        self.zoom = self._s.get("zoom", ZOOM)
        self.pin_on = self._s.get("pin_on", True)   # 置顶（默认开）
        self.dnd_on = self._s.get("dnd_on", False)  # 全屏免打扰
        self.root.wm_attributes("-topmost", self.pin_on)
        self.skin = self._s.get("skin", "clippy")
        if self.skin not in [s[0] for s in SKINS]:
            self.skin = "clippy"
        self._skin_switching = False   # 换肤过渡动画进行中
        self._pending_skin = None

        self._load_assets()
        w, h = self.size

        try:
            self.root.wm_attributes("-transparentcolor", "magenta")
            self.root.configure(bg="magenta")
        except tk.TclError:
            self.root.configure(bg="magenta")

        self.canvas = tk.Canvas(self.root, width=w, height=h,
                                bg="magenta", highlightthickness=0, bd=0)
        self.canvas.pack()
        first = self.animations[self._idle_anim]["frames"][0]["f"]
        self._img_item = self.canvas.create_image(
            0, 0, anchor="nw", image=self._photo(first))

        # 状态
        self._drag = None
        self._quitting = False
        self.bubble = None
        self.water_enabled = self._s.get("water_enabled", True)
        self.exercise_enabled = self._s.get("exercise_enabled", True)
        self.water_interval = self._s.get(
            "water_interval_min", WATER_INTERVAL_MIN) * 60 * 1000
        self.exercise_interval = self._s.get(
            "exercise_interval_min", EXERCISE_INTERVAL_MIN) * 60 * 1000
        self.water_job = None
        self.exercise_job = None

        # 显示选项
        self._dnd_active = False    # 当前是否因全屏而隐藏
        self.autostart_on = _autostart_enabled()   # 开机自启动

        # 全局快捷键动画
        self.hotkey_on = self._s.get("hotkey_on", False)
        self.hotkey_map = {a: {"mods": list(v["mods"]), "key": v["key"]}
                           for a, v in DEFAULT_HOTKEYS.items()}
        saved_hk = self._s.get("hotkey_map")
        if isinstance(saved_hk, dict):
            for a, v in saved_hk.items():
                if a in self.hotkey_map and isinstance(v, dict) \
                        and v.get("key"):
                    self.hotkey_map[a] = {
                        "mods": list(v.get("mods", [])),
                        "key": str(v["key"]),
                    }
        self._hk_running = False
        self._hk_prev = {}

        # 动画状态机
        self._seq = None
        self._ai = 0
        self._cur = None          # 当前帧（含 branching/exitBranch）
        self._anim_name = None    # 当前动画名
        self._use_exit = False    # 当前动画 useExitBranching
        self._exiting = False
        self._loop = False
        self._on_done = None
        self._after_anim = None
        self._idle_action_job = None   # 待机小动作穿插定时器

        # 番茄钟
        self.pomo_work_min = self._s.get("pomo_work_min", POMO_WORK_MIN)
        self.pomo_break_min = self._s.get("pomo_break_min", POMO_BREAK_MIN)
        self.pomo_running = False
        self.pomo_phase = None
        self.pomo_end_ts = None
        self.pomo_job = None
        self.pomo_count = 0
        self._pomo_write_played = False

        self._place_bottom_right()
        self._bind_events()
        self._build_menu()
        self._start_loops()
        self._reschedule_all(first_run=True)
        self._start_hotkey_poll()
        if self.dnd_on:
            self._check_fullscreen()
        self.root.protocol("WM_DELETE_WINDOW", self.quit)

    def _save_settings(self):
        """将当前设置写入 settings.json（临时文件+原子替换，避免写坏）。"""
        data = {
            "water_enabled": self.water_enabled,
            "water_interval_min": int(self.water_interval // 60000),
            "exercise_enabled": self.exercise_enabled,
            "exercise_interval_min": int(self.exercise_interval // 60000),
            "pomo_work_min": self.pomo_work_min,
            "pomo_break_min": self.pomo_break_min,
            "pin_on": self.pin_on,
            "dnd_on": self.dnd_on,
            "lang": self.lang,
            "skin": self.skin,
            "zoom": self.zoom,
            "hotkey_on": self.hotkey_on,
            "hotkey_map": self.hotkey_map,
        }
        try:
            tmp = SETTINGS_FILE + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            os.replace(tmp, SETTINGS_FILE)
        except Exception:
            pass

    def _toggle_pin(self):
        """显示在最前开关：控制 clippy 主窗口置顶。"""
        self.pin_on = self.pin_var.get()
        try:
            self.root.wm_attributes("-topmost", self.pin_on)
        except tk.TclError:
            pass
        self._save_settings()

    def _toggle_autostart(self):
        """开机自启动开关：写/删 HKCU 注册表 Run 项（用户级，免管理员）。"""
        self.autostart_on = self.auto_var.get()
        try:
            _set_autostart(self.autostart_on)
        except Exception as e:
            self.say("%s: %s" % (self.tr("menu_auto"), e), auto_hide_ms=4000)

    # ---------- 全局快捷键动画 ----------
    def _start_hotkey_poll(self):
        """启动后台轮询线程：用 GetAsyncKeyState 观察全局按键，
        只「观察」不拦截——其他程序照常收到快捷键。"""
        self._hk_running = True
        t = threading.Thread(target=self._hk_loop, daemon=True)
        t.start()

    def _hk_loop(self):
        while self._hk_running:
            time.sleep(0.15)
            try:
                self._hk_tick()
            except Exception:
                pass

    def _hk_tick(self):
        if not self.hotkey_on or self._quitting:
            return
        import ctypes
        user32 = ctypes.windll.user32
        mods_now = {
            "Ctrl": bool(user32.GetAsyncKeyState(0x11) & 0x8000),
            "Shift": bool(user32.GetAsyncKeyState(0x10) & 0x8000),
            "Alt": bool(user32.GetAsyncKeyState(0x12) & 0x8000),
        }
        for a, combo in self.hotkey_map.items():
            vk = self._key_vk(combo.get("key", ""))
            if not vk:
                continue
            pressed = bool(user32.GetAsyncKeyState(vk) & 0x8000)
            # 修饰键精确匹配（只允许组合中声明的修饰键按下）
            if any((m in combo.get("mods", [])) != mods_now[m]
                   for m in HK_MOD_KEYS):
                continue
            prev = self._hk_prev.get(a, False)
            self._hk_prev[a] = pressed
            if pressed and not prev:        # 上升沿触发，避免按住连播
                self.root.after(0, lambda aa=a: self._hk_fire(aa))
                return

    @staticmethod
    def _key_vk(key):
        """Tk keysym -> Windows 虚拟键码。"""
        k = str(key).lower()
        if len(k) == 1 and k.isalnum():
            return ord(k.upper())
        special = {"delete": 0x2E, "space": 0x20, "return": 0x0D,
                   "tab": 0x09, "left": 0x25, "up": 0x26, "right": 0x27,
                   "down": 0x28, "home": 0x24, "end": 0x23, "prior": 0x21,
                   "next": 0x22, "insert": 0x2D, "backspace": 0x08,
                   "escape": 0x1B}
        if k in special:
            return special[k]
        if k.startswith("f") and k[1:].isdigit() and 1 <= int(k[1:]) <= 24:
            return 0x70 + int(k[1:]) - 1
        return 0

    def _hk_fire(self, action):
        """主线程内执行：非空闲/免打扰/已退出时不打断。"""
        if self._quitting or not self.hotkey_on:
            return
        if self._dnd_active:
            return
        if not self._is_idle():
            return
        self.play_semantic(action, on_done=self._idle_next)

    def _toggle_hotkey(self):
        self.hotkey_on = self.hotkey_var.get()
        self._save_settings()
        if self.hotkey_on:
            self.say(self.tr("hotkey_on_msg"), auto_hide_ms=3000)
        else:
            self.say(self.tr("hotkey_off_msg"), auto_hide_ms=3000)

    def _hotkey_settings(self):
        """快捷键映射不可编辑（已移除自定义 UI），保留默认映射。"""
        pass

    # ---------- 全屏免打扰 ----------
    def _toggle_dnd(self):
        """全屏免打扰开关：启用后轮询前台窗口，检测到全屏应用
        （视频/游戏/演示）时隐藏 clippy 并静默提醒，退出全屏自动恢复。"""
        self.dnd_on = self.dnd_var.get()
        if self.dnd_on:
            self._check_fullscreen()
        else:
            self._dnd_restore()
        self._save_settings()

    def _check_fullscreen(self):
        if self.dnd_on:
            if self._is_fullscreen():
                if not self._dnd_active:
                    self._dnd_active = True
                    try:
                        # 全屏免打扰优先于「显示在最前」：
                        # 检测到全屏时先取消置顶再隐藏，避免置顶
                        # 窗口残留覆盖在全屏应用之上。
                        self.root.wm_attributes("-topmost", False)
                    except tk.TclError:
                        pass
                    try:
                        self.root.withdraw()
                    except tk.TclError:
                        pass
            else:
                self._dnd_restore()
            self.root.after(2000, self._check_fullscreen)
        else:
            self._dnd_restore()

    def _dnd_restore(self):
        if self._dnd_active:
            self._dnd_active = False
            try:
                self.root.deiconify()
            except tk.TclError:
                return
            # deiconify 是异步重映射：立即设置 -topmost 可能被映射过程
            # 覆盖且此后不再重设（_dnd_active 已 False），导致置顶永久
            # 丢失。延迟到重映射完成后重设窗口属性。
            self.root.after(50, self._dnd_apply_attrs)

    def _dnd_apply_attrs(self):
        try:
            self.root.update_idletasks()
            self.root.wm_attributes("-topmost", self.pin_on)
            try:
                self.root.wm_attributes("-transparentcolor", "magenta")
            except tk.TclError:
                pass
        except tk.TclError:
            pass

    @staticmethod
    def _hwnd_is_fullscreen(hwnd):
        """判定指定窗口是否处于真全屏（覆盖整块显示器，非最大化窗口）。

        旧实现只比较窗口尺寸，导致三类误判：
        1) 最大化窗口（含 DWM 阴影外框时尺寸恰好等于屏幕）被当作全屏；
        2) 点击桌面（Progman/WorkerW 全屏）时 clippy 被隐藏；
        3) 隐藏/最小化的全屏窗口（如最小化的游戏）被当作当前全屏。
        修复：排除桌面壳层、不可见/最小化窗口、以及「带标准边框的
        最大化窗口」（任务栏自动隐藏时其可视矩形恰等于整屏，但只是
        最大化不是全屏）；用 DwmGetWindowAttribute 取真实可视矩形
        （剔除阴影/边框），以窗口所在显示器整屏区域作比较，并校验
        位置从显示器左上角开始，支持多显示器。
        """
        try:
            import ctypes
            from ctypes import wintypes
            user32 = ctypes.windll.user32

            if not hwnd:
                return False
            cls = ctypes.create_unicode_buffer(64)
            user32.GetClassNameW(hwnd, cls, 64)
            if cls.value in ("Progman", "WorkerW", "Shell_TrayWnd"):
                return False  # 桌面/任务栏不是全屏应用

            # 取根窗口：避免浮动子层（如 CEF-OSC-WIDGET）干扰判定
            root = user32.GetAncestor(hwnd, 2)  # GA_ROOT

            # 不可见/最小化窗口不参与判定：隐藏的全屏窗口、最小化的
            # 全屏游戏（其矩形位置为 -32000 且尺寸等于屏幕）都会导致
            # 非全屏状态下的误隐藏。
            if not user32.IsWindowVisible(root):
                return False
            if user32.IsIconic(root):
                return False

            # 排除「普通可调整窗口最大化」：带标题栏/可调边框的最大化
            # 窗口只是最大化而非全屏（任务栏自动隐藏时其可视矩形恰等于
            # 整屏）。无边框最大化（WS_POPUP 无标题，如游戏/播放器
            # 全屏）保留判定。
            user32.GetWindowLongPtrW.restype = ctypes.c_ssize_t
            style = user32.GetWindowLongPtrW(root, -16)  # GWL_STYLE
            WS_MAXIMIZE, WS_CAPTION, WS_THICKFRAME = (
                0x01000000, 0x00C00000, 0x00040000)
            if (style & WS_MAXIMIZE) and (style & (WS_CAPTION | WS_THICKFRAME)):
                return False

            # 真实可视矩形（DWM 扩展边框，剔除阴影外框）
            rect = wintypes.RECT()
            hr = ctypes.windll.dwmapi.DwmGetWindowAttribute(
                root, 9, ctypes.byref(rect), ctypes.sizeof(rect))
            if hr != 0:
                # 独占全屏/DWM 不可用等场景：回退 GetWindowRect
                # （阴影外框对判定无碍：全屏窗口仍覆盖整屏）
                if not user32.GetWindowRect(root, ctypes.byref(rect)):
                    return False

            # 窗口所在显示器的整屏区域（含任务栏）
            class MONITORINFO(ctypes.Structure):
                _fields_ = [
                    ("cbSize", wintypes.DWORD),
                    ("rcMonitor", wintypes.RECT),
                    ("rcWork", wintypes.RECT),
                    ("dwFlags", wintypes.DWORD),
                ]
            mon = user32.MonitorFromWindow(
                root, 2)  # MONITOR_DEFAULTTONEAREST
            mi = MONITORINFO()
            mi.cbSize = ctypes.sizeof(mi)
            if not user32.GetMonitorInfoW(mon, ctypes.byref(mi)):
                return False
            m = mi.rcMonitor
            mw = m.right - m.left
            mh = m.bottom - m.top
            w = rect.right - rect.left
            h = rect.bottom - rect.top
            return (w >= mw - 4 and h >= mh - 4
                    and rect.left <= m.left + 4
                    and rect.top <= m.top + 4)
        except Exception:
            return False

    def _is_fullscreen(self):
        """检测当前是否有真全屏窗口。

        不能只信 GetForegroundWindow：clippy 置顶后用户点击/拖拽过它，
        前台句柄会一直停在 clippy 自己（248×186）上，导致全屏应用漏判
        ——「显示在最前」+「全屏免打扰」同开时失效。因此前台是 clippy
        时改为遍历 Z 序顶层窗口。

        遍历规则（修复误判）：从 Z 序顶部往下找**第一个可见的、非
        驻留/壳层类的顶层窗口**——它就是用户当前实际看到的窗口，它的
        全屏状态即答案。旧实现遍历所有窗口、任一全屏即判 True，导致：
        1) 隐藏/最小化的全屏窗口误判（用户没在看它也隐藏 clippy）；
        2) 后台挂着的全屏窗口误判（用户切到普通窗口工作也被隐藏）。
        """
        import ctypes
        from ctypes import wintypes
        try:
            user32 = ctypes.windll.user32
            # 64 位系统 HWND 是 64 位指针，默认 c_int restype 会截断高位
            user32.GetForegroundWindow.restype = wintypes.HWND
            user32.GetWindow.restype = wintypes.HWND
            user32.GetTopWindow.restype = wintypes.HWND
            my = int(self.root.winfo_id())
            fg = user32.GetForegroundWindow()
            if fg and fg != my:
                return self._hwnd_is_fullscreen(fg)
            # 前台是 clippy（或不可用）：遍历 Z 序顶层窗口。
            # 注意不能 GetWindow(NULL, GW_HWNDFIRST)——hWnd 为 NULL 时
            # 该调用行为未定义（实测返回 0）；须用 GetTopWindow(NULL)
            # 取 Z 序最顶顶层窗口作起点。
            h = user32.GetTopWindow(None)
            while h:
                if h != my and not self._is_resident_class(h):
                    root = user32.GetAncestor(h, 2)
                    if (user32.IsWindowVisible(root)
                            and not user32.IsIconic(root)):
                        # 跳过系统常驻的极小辅助窗口（IME、GDI Hook、
                        # ThumbnailDeviceHelper 等 1x1 可见窗口）——
                        # 它们不是用户当前观看的窗口，否则会导致
                        # 全屏判定被这些辅助窗口截断。
                        rr = wintypes.RECT()
                        if user32.GetWindowRect(root, ctypes.byref(rr)):
                            w = rr.right - rr.left
                            hh = rr.bottom - rr.top
                            if w >= 100 and hh >= 60:
                                # 第一个有意义的可见非驻留顶层窗口：
                                # 它是否全屏即当前是否处于全屏
                                return self._hwnd_is_fullscreen(h)
                h = user32.GetWindow(h, 2)  # GW_HWNDNEXT
            return False
        except Exception:
            return False

    @staticmethod
    def _is_resident_class(hwnd):
        """判断窗口是否属于驻留/叠加类（遍历时需跳过）。"""
        try:
            import ctypes
            user32 = ctypes.windll.user32
            cls = ctypes.create_unicode_buffer(64)
            user32.GetClassNameW(hwnd, cls, 64)
            return cls.value in (
                "CEF-OSC-WIDGET",                 # Chromium 屏幕控件层
                "Windows.UI.Core.CoreWindow",     # UWP 容器（非全屏也常见）
                "Progman", "WorkerW", "Shell_TrayWnd",
            )
        except Exception:
            return False

    # ---------- 语言 ----------
    def tr(self, key, **kw):
        s = TR[self.lang].get(key, key)
        if kw:
            try:
                s = s.format(**kw)
            except (KeyError, IndexError):
                pass
        return s

    def _toggle_lang(self):
        self.lang = "en" if self.lang == "zh" else "zh"
        if self.bubble is not None:
            try:
                self.bubble.hide()
            except Exception:
                pass
            self.bubble = None
        self._build_menu()
        self.say(self.tr("lang_switched"), auto_hide_ms=3500)
        self._save_settings()

    # ---------- 资源加载 ----------
    def _fix_edges(self, im):
        """修复透明窗口紫边：
        1) 用 RGBa 中间模式缩放，避免半透明边缘颜色被稀释产生色偏；
        2) alpha 阈值化到 0/255，消除半透明像素与 magenta 背景的混合。
        """
        if self.zoom != 1:
            im = im.convert("RGBa").resize(self.size, Image.LANCZOS)
            im = im.convert("RGBA")
        alpha = im.getchannel("A").point(lambda v: 255 if v >= 110 else 0)
        im.putalpha(alpha)
        return im

    def _load_assets(self):
        """按当前皮肤加载动画定义并解析语义映射（皮肤自适应）。"""
        sdir = os.path.join(DATA_DIR, "assets", self.skin)
        with open(os.path.join(sdir, "animations.json"),
                  encoding="utf-8") as fp:
            data = json.load(fp)
        self.animations = data["animations"]
        fw, fh = data["framesize"]
        self.fw, self.fh = fw, fh
        self.size = (int(fw * self.zoom), int(fh * self.zoom))
        self.frames_dir = os.path.join(sdir, "frames")
        # 待机动画：优先官方 Idle1_1，其次任意 Idle*，最后任意动画
        self._idle_anims = [n for n in self.animations
                            if n.startswith("Idle")]
        if ANIM_IDLE in self.animations:
            self._idle_anim = ANIM_IDLE
        elif self._idle_anims:
            self._idle_anim = self._idle_anims[0]
        else:
            self._idle_anim = next(iter(self.animations))
        # 语义 -> 动画：按候选优先级解析，全缺失则回退待机
        self.act = {}
        for sem, base in ACT.items():
            for cand in SEM_ALT.get(sem, []) + [base]:
                if cand in self.animations:
                    self.act[sem] = cand
                    break
            else:
                self.act[sem] = None
        self._rebuild_cache()

    def _rebuild_cache(self):
        """惰性帧缓存：仅清空缓存并重建空帧占位。
        帧图按需加载（_photo 懒加载），不再启动时一次性加载
        全部数百帧 → 大幅降低内存占用与启动 IO。
        缩放/换肤后调用（self.size / self.frames_dir 已更新）。"""
        self._cache = {}
        # 空帧占位（官方 images=[] 时显示空白）
        blank = Image.new("RGBA", self.size, (0, 0, 0, 0))
        self._blank_img = ImageTk.PhotoImage(blank)

    def _photo(self, key):
        """惰性获取帧图：未缓存则从磁盘加载并缩放后缓存。
        只缓存实际播放过的帧，内存占用与动画使用量成正比。"""
        im = self._cache.get(key)
        if im is not None:
            return im
        try:
            p = os.path.join(self.frames_dir, key + ".png")
            img = Image.open(p).convert("RGBA")
            im = ImageTk.PhotoImage(self._fix_edges(img))
        except Exception:
            im = self._blank_img
        self._cache[key] = im
        return im

    # ---------- 动画引擎（官方 Animator branching 逻辑） ----------
    def play(self, action, loop=False, on_done=None, speed=1.0):
        """action 为官方动画名；loop=True 无回调时循环；on_done 播完后回调。
        完整支持官方 branching（随机分支跳转）与 exitBranch。
        speed>1 放慢帧时长（用于待机动画的舒缓节奏），
        交互/提醒/番茄钟等保持官方速度（speed=1.0）。"""
        if action not in self.animations:
            return
        if self._after_anim:
            try:
                self.root.after_cancel(self._after_anim)
            except Exception:
                pass
            self._after_anim = None
        self._anim_name = action
        self._seq = self.animations[action]["frames"]
        self._use_exit = self.animations[action]["useExitBranching"]
        self._ai = 0
        self._cur = None
        self._exiting = False
        self._steps = 0
        self._anim_ms = 0
        self._exit_steps = 0
        self._anim_speed = speed
        self._loop = loop
        self._on_done = on_done
        self._step()

    def play_semantic(self, name, loop=False, on_done=None):
        """按语义名播放（见 ACT/SEM_ALT 皮肤自适应映射）。"""
        if name in self.animations:
            self.play(name, loop=loop, on_done=on_done)
        else:
            self.play(self._a(name), loop=loop, on_done=on_done)

    def _a(self, sem):
        """语义 -> 皮肤解析后的动画名；缺失回退到待机动画。"""
        return self.act.get(sem, self._idle_anim)

    def _is_idle(self):
        """官方 _isIdleAnimation：当前动画名以 Idle 开头。"""
        return bool(self._anim_name) and self._anim_name.startswith("Idle")

    def _next_idx(self):
        """官方 Animator._getNextAnimationFrame：
        退出分支 → 随机分支（按权重） → 顺序推进。"""
        if self._cur is None:
            return 0
        if self._exiting and "exitBranch" in self._cur:
            return self._cur["exitBranch"]
        br = self._cur.get("branching")
        if br:
            rnd = random.random() * 100
            for b in br["branches"]:
                if rnd <= b["weight"]:
                    return b["frameIndex"]
                rnd -= b["weight"]
        return self._ai + 1

    def _finish_anim(self):
        """收尾当前动画：取消定时器，触发 on_done 或回待机。"""
        if self._after_anim:
            try:
                self.root.after_cancel(self._after_anim)
            except Exception:
                pass
            self._after_anim = None
        if self._on_done:
            cb = self._on_done
            self._on_done = None
            cb()
        else:
            self._idle_next()

    def _maybe_exit(self):
        """动画超时/超帧时触发优雅退出：置 _exiting 后继续正常播放，
        播到带 exitBranch 的帧时由 _next_idx 跳转退出序列自然收尾；
        仅当动画根本没有退出分支（或退出序列超长）时才强制收尾。
        返回 True 表示动画已在此处结束。"""
        if self._loop:
            return False
        if not self._exiting and (self._steps > len(self._seq) * 2 + 10
                                  or self._anim_ms > MAX_ANIM_MS):
            self._exiting = True
        if self._exiting:
            self._exit_steps += 1
            # 上限优先：退出序列超长（连环 exitBranch/循环）时强制收尾
            if self._exit_steps > MAX_EXIT_STEPS:
                self._finish_anim()
                return True
            # 有退出分支：_next_idx 会跳转退出序列，继续播放等待自然收尾
            if "exitBranch" in (self._cur or {}):
                return False
        return False

    def _step(self):
        # 真正取消上一个帧定时器（而非仅置 None）：
        # 真实 mainloop 运行时该 after 已执行，cancel 为无害 no-op；
        # 手动步进/测试时则能消除残留回调，避免陈旧 _step 累积快进动画。
        if self._after_anim:
            try:
                self.root.after_cancel(self._after_anim)
            except Exception:
                pass
            self._after_anim = None
        self._steps += 1
        if self._maybe_exit():
            return
        new_idx = min(self._next_idx(), len(self._seq) - 1)
        changed = self._cur is None or self._ai != new_idx
        self._ai = new_idx
        at_last = self._ai >= len(self._seq) - 1
        if not (at_last and self._use_exit):
            self._cur = self._seq[self._ai]
        f = self._cur
        delay = int(f["d"] * self._anim_speed)   # 待机放慢：帧时长 × 系数
        self._anim_ms += delay
        if f["f"]:
            self.canvas.itemconfig(self._img_item, image=self._photo(f["f"]))
        else:
            self.canvas.itemconfig(self._img_item, image=self._blank_img)
        self._after_anim = self.root.after(delay, self._step)
        if changed and at_last:
            if self._on_done:
                cb = self._on_done
                self._on_done = None
                cb()
            elif self._loop:
                # 循环重启：重置帧索引后由「已调度的 after」自然推进到第 0 帧。
                # 绝不能在此递归 _step()——会额外调度一个 after 定时器，
                # 多个定时器同时排队导致动画加速（帧间隔变短、越跑越快）。
                self._ai = 0
                self._cur = None
                return
            else:
                # 非循环动画自然结束且无回调 → 回待机
                self._idle_next()

    def _idle_next(self):
        """回到主待机：主待机动画循环播放作为稳定基底（连续呼吸），
        并调度低频小动作穿插。所有交互动作播完都回到这里，
        保证待机视觉连续、切换不再频繁。"""
        if self._quitting:
            return
        self.play(self._idle_anim, loop=True, speed=IDLE_ANIM_SPEED)
        self._schedule_idle_action()

    def _schedule_idle_action(self):
        """调度下一次待机小动作（8~16 秒随机）。"""
        if self._idle_action_job:
            try:
                self.root.after_cancel(self._idle_action_job)
            except Exception:
                pass
        self._idle_action_job = self.root.after(
            random.randint(IDLE_ACTION_MIN_MS, IDLE_ACTION_MAX_MS),
            self._idle_play_action)

    def _idle_play_action(self):
        """穿插一次待机小动作（眨眼/摇摆/挠头等），播完回主待机。"""
        self._idle_action_job = None
        if self._quitting:
            return
        if not self._is_idle():
            # 当前不在待机（交互/番茄钟/换肤中）→ 重新调度
            self._schedule_idle_action()
            return
        # 小动作池：排除主待机动画本身
        pool = [a for a in self._idle_anims if a != self._idle_anim]
        if not pool:
            pool = self._idle_anims
        self.play(random.choice(pool), on_done=self._idle_next,
                  speed=IDLE_ANIM_SPEED)

    def _start_loops(self):
        self._idle_next()

    # ---------- 窗口 ----------
    def _place_bottom_right(self):
        self.root.update_idletasks()
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        self.root.geometry(f"+{sw - self.root.winfo_width() - 40}"
                           f"+{sh - self.root.winfo_height() - 80}")

    def _bind_events(self):
        self.canvas.bind("<ButtonPress-1>", self._drag_start)
        self.canvas.bind("<B1-Motion>", self._drag_move)
        self.canvas.bind("<Double-Button-1>", self._double_click)
        self.canvas.bind("<Button-3>", self._popup_menu)
        self.canvas.bind("<Enter>", self._hover)

    def _hover(self, _e):
        if self._is_idle():
            self.play(self._a("wave"), on_done=self._idle_next)

    def _double_click(self, _e):
        self.play(self._a("surprise"),
                  on_done=self._idle_next)

    def _drag_start(self, event):
        self._drag = (event.x_root - self.root.winfo_x(),
                      event.y_root - self.root.winfo_y())

    def _drag_move(self, event):
        if self._drag:
            self.root.geometry(f"+{event.x_root - self._drag[0]}"
                               f"+{event.y_root - self._drag[1]}")

    # ---------- 提醒 ----------
    def _reschedule_all(self, first_run=False):
        delay = FIRST_DELAY_S * 1000 if first_run else 0
        self._schedule_water(self.water_interval + delay)
        self._schedule_exercise(self.exercise_interval + delay)

    def _schedule_water(self, ms):
        if self.water_job:
            self.root.after_cancel(self.water_job)
        self.water_job = self.root.after(int(ms), self._fire_water)

    def _schedule_exercise(self, ms):
        if self.exercise_job:
            self.root.after_cancel(self.exercise_job)
        self.exercise_job = self.root.after(int(ms), self._fire_exercise)

    def _alert(self, semantic):
        if self._dnd_active:      # 全屏免打扰：不响铃、不表演
            return
        self.root.bell()
        self.play_semantic(semantic,
                           on_done=self._idle_next)

    def _fire_water(self):
        if self._dnd_active:      # 全屏免打扰：跳过本轮，顺延到下一周期
            self._schedule_water(self.water_interval)
            return
        if self.water_enabled:
            self._alert("water")
            self.say(random.choice(self.tr("water_tips")),
                     buttons=[(self.tr("btn_done"), "water_done"),
                              (self.tr("btn_snooze", n=SNOOZE_MIN), "water_snooze"),
                              (self.tr("btn_off"), "water_off")])
        self._schedule_water(self.water_interval)

    def _fire_exercise(self):
        if self._dnd_active:      # 全屏免打扰：跳过本轮，顺延到下一周期
            self._schedule_exercise(self.exercise_interval)
            return
        if self.exercise_enabled:
            self._alert("exercise")
            self.say(random.choice(self.tr("ex_tips")),
                     buttons=[(self.tr("btn_ex_done"), "ex_done"),
                              (self.tr("btn_snooze", n=SNOOZE_MIN), "ex_snooze"),
                              (self.tr("btn_off"), "ex_off")])
        self._schedule_exercise(self.exercise_interval)

    # ---------- 番茄钟 ----------
    def start_pomodoro(self):
        if self.pomo_running:
            self.say(self.tr("pomo_running"), auto_hide_ms=4000)
            return
        self.pomo_running = True
        self._start_work_phase()

    def _start_work_phase(self):
        self.pomo_phase = "work"
        self.pomo_end_ts = time.time() + self.pomo_work_min * 60
        self._pomo_write_played = False
        # 播一次思考动画后自然回待机（不无限循环）
        self.play(self._a("think"), on_done=self._idle_next)
        if not self._dnd_active:
            self.say(self.tr("pomo_start", n=self.pomo_work_min),
                     auto_hide_ms=5000)
        self._tick_pomodoro()

    def _start_break_phase(self):
        self.pomo_phase = "break"
        self.pomo_end_ts = time.time() + self.pomo_break_min * 60
        # 播一次休息动画后自然回待机（不无限循环）
        self.play(self._a("sleep"), on_done=self._idle_next)
        if not self._dnd_active:
            self.say(self.tr("pomo_break", n=self.pomo_break_min),
                     auto_hide_ms=6000)
        self._tick_pomodoro()

    def _tick_pomodoro(self):
        if not self.pomo_running:
            return
        remain = self.pomo_end_ts - time.time()
        if remain <= 0:
            if self.pomo_phase == "work":
                self.pomo_count += 1
                self._alert("happy")
                self._start_break_phase()
            else:
                self._alert("artsy")
                if not self._dnd_active:
                    self.say(self.tr("pomo_done", n=self.pomo_count),
                             buttons=[(self.tr("btn_pomo_next"), "pomo_next"),
                                      (self.tr("btn_pomo_stop"), "pomo_stop")])
            return
        if remain <= 60 and self.pomo_phase == "work" and \
                not self._pomo_write_played:
            self._pomo_write_played = True
            # 最后 1 分钟播一次写字动画后回待机
            self.play(self._a("write"), on_done=self._idle_next)
        self.pomo_job = self.root.after(1000, self._tick_pomodoro)

    def stop_pomodoro(self):
        if not self.pomo_running:
            return
        self.pomo_running = False
        self.pomo_phase = None
        self._pomo_write_played = False
        if self.pomo_job:
            self.root.after_cancel(self.pomo_job)
            self.pomo_job = None
        self._idle_next()
        self.say(self.tr("pomo_stopped", n=self.pomo_count), auto_hide_ms=4000)

    def _pomo_settings(self):
        if self.pomo_running:
            self.say(self.tr("pomo_stop_first"), auto_hide_ms=4000)
            return
        SettingsDialog(
            self.root,
            title=self.tr("settings_title"),
            work_label=self.tr("settings_work"),
            break_label=self.tr("settings_break"),
            work=self.pomo_work_min,
            brk=self.pomo_break_min,
            ok_text=self.tr("btn_ok"),
            cancel_text=self.tr("btn_cancel"),
            on_ok=self._apply_pomo_settings,
            clippy_pos=(self.root.winfo_rootx(), self.root.winfo_rooty()),
        )

    def _apply_pomo_settings(self, work, brk):
        self.pomo_work_min = work
        self.pomo_break_min = brk
        self.say(self.tr("settings_saved", w=work, b=brk), auto_hide_ms=4000)
        self._save_settings()

    def _water_settings(self):
        """喝水提醒设置：单输入气泡对话框（提醒间隔分钟）。"""
        SettingsDialog(
            self.root,
            title=self.tr("water_settings_title"),
            work_label=self.tr("water_settings_label"),
            break_label="", work=self.water_interval // 60000, brk=0,
            ok_text=self.tr("btn_ok"), cancel_text=self.tr("btn_cancel"),
            on_ok=self._apply_water_settings,
            clippy_pos=(self.root.winfo_rootx(), self.root.winfo_rooty()),
            single=True,
        )

    def _apply_water_settings(self, minutes):
        self.water_interval = minutes * 60 * 1000
        if self.water_enabled:
            self._schedule_water(self.water_interval)
        self._save_settings()
        self.say(self.tr("water_settings_saved", n=minutes),
                 auto_hide_ms=4000)

    def _exercise_settings(self):
        """锻炼提醒设置：单输入气泡对话框（提醒间隔分钟）。"""
        SettingsDialog(
            self.root,
            title=self.tr("ex_settings_title"),
            work_label=self.tr("ex_settings_label"),
            break_label="", work=self.exercise_interval // 60000, brk=0,
            ok_text=self.tr("btn_ok"), cancel_text=self.tr("btn_cancel"),
            on_ok=self._apply_exercise_settings,
            clippy_pos=(self.root.winfo_rootx(), self.root.winfo_rooty()),
            single=True,
        )

    def _apply_exercise_settings(self, minutes):
        self.exercise_interval = minutes * 60 * 1000
        if self.exercise_enabled:
            self._schedule_exercise(self.exercise_interval)
        self._save_settings()
        self.say(self.tr("ex_settings_saved", n=minutes),
                 auto_hide_ms=4000)

    # ---------- 气泡 ----------
    def say(self, text, buttons=None, auto_hide_ms=15000):
        if self.bubble is not None:
            try:
                self.bubble.hide()
            except Exception:
                pass
            self.bubble = None
        # 用 winfo_rootx/y（屏幕绝对坐标）：winfo_x/y 在窗口未映射时返回 0，
        # 会导致气泡飘到屏幕左上角，远离 clippy
        anchor = (self.root.winfo_rootx(), self.root.winfo_rooty())
        self.bubble = SpeechBubble(
            self.root, text, buttons or [],
            on_action=self._on_action, hide_cb=self._clear_bubble,
            auto_hide_ms=auto_hide_ms, anchor=anchor,
            title=self.tr("bubble_title"))

    def _clear_bubble(self):
        self.bubble = None

    def _on_action(self, key):
        if key == "water_done":
            self.play(self._a("happy"),
                      on_done=self._idle_next)
            self.say(self.tr("water_done_msg"), auto_hide_ms=4000)
            self._schedule_water(self.water_interval)
        elif key == "water_snooze":
            self.say(self.tr("snooze_msg", n=SNOOZE_MIN), auto_hide_ms=4000)
            self._schedule_water(SNOOZE_MIN * 60 * 1000)
        elif key == "water_off":
            self.water_enabled = False
            self.play(self._a("sleep"),
                      on_done=self._idle_next)
            self.say(self.tr("water_off_msg"), auto_hide_ms=5000)
        elif key == "ex_done":
            self.play(self._a("wave"),
                      on_done=self._idle_next)
            self.say(self.tr("ex_done_msg"), auto_hide_ms=4000)
            self._schedule_exercise(self.exercise_interval)
        elif key == "ex_snooze":
            self.say(self.tr("ex_snooze_msg", n=SNOOZE_MIN), auto_hide_ms=4000)
            self._schedule_exercise(SNOOZE_MIN * 60 * 1000)
        elif key == "ex_off":
            self.exercise_enabled = False
            self.play(self._a("sleep"),
                      on_done=self._idle_next)
            self.say(self.tr("ex_off_msg"), auto_hide_ms=5000)
        elif key == "pomo_next":
            self._start_work_phase()
        elif key == "pomo_stop":
            self.stop_pomodoro()

    # ---------- 菜单 ----------

    def _perform_items_for_skin(self):
        """按当前皮肤过滤表演动作：只保留该皮肤有真实动画的语义项。
        皮肤动画集不同（如 Rover 缺大量动作），缺动画的动作不显示。"""
        return [(tkey, sem) for tkey, sem in PERFORM_ITEMS
                if self.act.get(sem)]

    def _build_menu(self):
        m = tk.Menu(self.root, tearoff=0)
        self.water_var = tk.BooleanVar(value=self.water_enabled)
        self.ex_var = tk.BooleanVar(value=self.exercise_enabled)
        m.add_checkbutton(label=self.tr("menu_water"), variable=self.water_var,
                          command=self._toggle_water)
        m.add_command(label=self.tr("menu_water_settings"),
                      command=self._water_settings)
        m.add_checkbutton(label=self.tr("menu_ex"), variable=self.ex_var,
                          command=self._toggle_exercise)
        m.add_command(label=self.tr("menu_ex_settings"),
                      command=self._exercise_settings)
        m.add_separator()
        m.add_command(label=self.tr("menu_pomo_start"),
                      command=self.start_pomodoro)
        m.add_command(label=self.tr("menu_pomo_stop"),
                      command=self.stop_pomodoro)
        m.add_command(label=self.tr("menu_pomo_settings"),
                      command=self._pomo_settings)
        m.add_separator()
        emo = tk.Menu(m, tearoff=0)
        for tkey, sem in self._perform_items_for_skin():
            emo.add_command(label=self.tr(tkey),
                            command=lambda s=sem: self._do_act(s))
        m.add_cascade(label=self.tr("menu_perform"), menu=emo)
        m.add_separator()
        zm = tk.Menu(m, tearoff=0)
        self.zoom_var = tk.DoubleVar(value=self.zoom)
        for z in ZOOM_STEPS:
            zm.add_radiobutton(
                label="%g%%" % (z * 100),
                value=z, variable=self.zoom_var,
                command=lambda zz=z: self._set_zoom(zz))
        m.add_cascade(label=self.tr("menu_size"), menu=zm)
        sk = tk.Menu(m, tearoff=0)
        self.skin_var = tk.StringVar(value=self.skin)
        self._skin_thumbs = {}
        for sid, label in SKINS:
            thumb = self._skin_thumb(sid)
            self._skin_thumbs[sid] = thumb
            sk.add_radiobutton(label=label, value=sid, image=thumb,
                               compound="left", variable=self.skin_var,
                               command=lambda s=sid: self._set_skin(s))
        m.add_cascade(label=self.tr("menu_skin"), menu=sk)
        m.add_separator()
        m.add_command(label=self.tr("menu_greet"), command=self._greet)
        m.add_command(label=self.tr("menu_about"), command=self._about)
        m.add_separator()
        self.pin_var = tk.BooleanVar(value=self.pin_on)
        self.dnd_var = tk.BooleanVar(value=self.dnd_on)
        self.auto_var = tk.BooleanVar(value=self.autostart_on)
        m.add_checkbutton(label=self.tr("menu_pin"), variable=self.pin_var,
                          command=self._toggle_pin)
        m.add_checkbutton(label=self.tr("menu_dnd"), variable=self.dnd_var,
                          command=self._toggle_dnd)
        m.add_checkbutton(label=self.tr("menu_auto"), variable=self.auto_var,
                          command=self._toggle_autostart)
        self.hotkey_var = tk.BooleanVar(value=self.hotkey_on)
        m.add_checkbutton(label=self.tr("menu_hotkey"),
                          variable=self.hotkey_var,
                          command=self._toggle_hotkey)
        m.add_separator()
        m.add_command(label=self.tr("menu_lang"), command=self._toggle_lang)
        m.add_separator()
        m.add_command(label=self.tr("menu_exit"), command=self.quit)
        self.menu = m

    def _do_act(self, sem):
        self.play_semantic(sem, on_done=self._idle_next)

    def _set_zoom(self, z):
        """调整 clippy 大小：重建帧缓存，窗口保持中心缩放。"""
        if abs(z - self.zoom) < 1e-9:
            return
        self.root.update_idletasks()
        cx = self.root.winfo_rootx() + self.root.winfo_width() // 2
        cy = self.root.winfo_rooty() + self.root.winfo_height() // 2
        self.zoom = z
        self.size = (int(self.fw * z), int(self.fh * z))
        self._rebuild_cache()
        w, h = self.size
        self.canvas.config(width=w, height=h)
        self.root.geometry(f"{w}x{h}+{cx - w // 2}+{cy - h // 2}")
        key = self._cur["f"] if self._cur and self._cur["f"] else None
        self.canvas.itemconfig(
            self._img_item,
            image=self._photo(key) if key else self._blank_img)
        self._save_settings()

    def _skin_thumb(self, sid, size=(44, 33)):
        """生成皮肤缩略图：取该皮肤待机动画第一帧，等比缩放居中。"""
        try:
            sdir = os.path.join(DATA_DIR, "assets", sid)
            with open(os.path.join(sdir, "animations.json"),
                      encoding="utf-8") as fp:
                data = json.load(fp)
            anims = data["animations"]
            if ANIM_IDLE in anims:
                idle = ANIM_IDLE
            else:
                idle = next((n for n in anims if n.startswith("Idle")),
                            next(iter(anims)))
            key = anims[idle]["frames"][0]["f"]
            im = Image.open(os.path.join(sdir, "frames", key + ".png"))
            im = im.convert("RGBA")
        except Exception:
            im = Image.new("RGBA", (1, 1), (0, 0, 0, 0))
        iw, ih = im.size
        scale = min(size[0] / iw, size[1] / ih)
        nw = max(1, int(iw * scale))
        nh = max(1, int(ih * scale))
        im = im.resize((nw, nh), Image.LANCZOS)
        canvas = Image.new("RGBA", size, (0, 0, 0, 0))
        canvas.paste(im, ((size[0] - nw) // 2, (size[1] - nh) // 2), im)
        return ImageTk.PhotoImage(canvas)

    def _set_skin(self, sid):
        """切换皮肤（带过渡动画）：旧皮肤播再见 → 新皮肤播打招呼。
        动画期间防重复触发。"""
        if sid == self.skin or self._skin_switching:
            return
        self._skin_switching = True
        self._pending_skin = sid
        # 旧皮肤播放「再见」动作，播完再切换
        self.play_semantic("goodbye", on_done=self._do_switch_skin)

    def _do_switch_skin(self):
        """再见动画播完：加载新皮肤、重建窗口与菜单，播放「打招呼」。"""
        sid = self._pending_skin
        self._pending_skin = None
        self.root.update_idletasks()
        cx = self.root.winfo_rootx() + self.root.winfo_width() // 2
        cy = self.root.winfo_rooty() + self.root.winfo_height() // 2
        self.skin = sid
        self._load_assets()
        self._build_menu()          # 重建菜单：表演动作按新皮肤过滤、换肤缩略图刷新
        w, h = self.size
        self.canvas.config(width=w, height=h)
        self.root.geometry(f"{w}x{h}+{cx - w // 2}+{cy - h // 2}")
        # 新皮肤播放「打招呼」动作后自然回待机
        self.play_semantic("greet", on_done=self._idle_next)
        self._save_settings()
        name = dict(SKINS).get(sid, sid)
        self.say(self.tr("skin_switched", skin=name), auto_hide_ms=3000)
        self._skin_switching = False

    def _popup_menu(self, event):
        self.water_var.set(self.water_enabled)
        self.ex_var.set(self.exercise_enabled)
        self.pin_var.set(self.pin_on)
        self.dnd_var.set(self.dnd_on)
        self.auto_var.set(self.autostart_on)
        self.skin_var.set(self.skin)
        self.menu.tk_popup(event.x_root, event.y_root)

    def _toggle_water(self):
        self.water_enabled = self.water_var.get()
        if self.water_enabled:
            self._schedule_water(self.water_interval)
            self.say(self.tr("water_on_msg"), auto_hide_ms=3000)
        self._save_settings()

    def _toggle_exercise(self):
        self.exercise_enabled = self.ex_var.get()
        if self.exercise_enabled:
            self._schedule_exercise(self.exercise_interval)
            self.say(self.tr("ex_on_msg"), auto_hide_ms=3000)
        self._save_settings()

    def _greet(self):
        self.play(self._a("greet"),
                  on_done=self._idle_next)
        self.say(random.choice(self.tr("greet_msgs")))

    def _about(self):
        self.say(self.tr("about"), auto_hide_ms=8000)

    # ---------- 运行 ----------
    def quit(self):
        """播放当前皮肤的「再见」动作后退出；播放期间防重复触发。"""
        if self._quitting:
            return
        self._quitting = True
        self._hk_running = False   # 停止全局按键轮询线程
        if self._idle_action_job:
            try:
                self.root.after_cancel(self._idle_action_job)
            except Exception:
                pass
            self._idle_action_job = None
        if self.bubble is not None:
            try:
                self.bubble.hide()
            except Exception:
                pass
            self.bubble = None
        # 取消全部定时器，避免退出动画期间触发提醒/番茄钟回调
        for job in (self.water_job, self.exercise_job, self.pomo_job):
            if job:
                try:
                    self.root.after_cancel(job)
                except Exception:
                    pass
        self.play_semantic("goodbye", on_done=self._do_exit)

    def _do_exit(self):
        try:
            self.root.destroy()
        except Exception:
            pass

    def run(self):
        # 等窗口映射、位置生效后再弹欢迎气泡（否则 anchor 是 (0,0)，
        # 气泡会出现在屏幕左上角，与 clippy 相距甚远）
        self.root.after(600, self._greet)
        try:
            _diag("MAINLOOP-START")
        except Exception:
            pass
        self.root.mainloop()


if __name__ == "__main__":
    import atexit
    import time
    import os

    def _diag(msg):
        try:
            with open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                   "pet_diag.log"), "a", encoding="utf-8") as f:
                f.write("[%s] %s pid=%s\n" % (time.strftime("%H:%M:%S"), msg, os.getpid()))
        except Exception:
            pass

    _diag("START")
    atexit.register(lambda: _diag("EXIT-atexit"))
    app = ClippyPet()
    _diag("WINDOW-CREATED")
    app.run()
    _diag("AFTER-MAINLOOP")
