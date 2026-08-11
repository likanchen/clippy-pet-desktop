# Clippy Desktop Pet

A desktop pet based on the **official Office 2003 Clippy assets**: water/exercise reminders, Pomodoro timer, global hotkey animations, and 10 official character skins. All animations are frame-by-frame reproductions of the originals with natural transitions.

> [简体中文](README.md) | English

## 🤖 Development Note

This project was generated and iteratively maintained with the **DeepSeek V4 Flash (0731) video coding** model.

## ✨ Features

### 🐱 Skins (10 official characters)
- Assets from the official `agents/` directory of [clippyjs/clippy.js](https://github.com/clippyjs/clippy.js), 10 characters: **Clippy** (classic paperclip), Merlin (wizard), Genie (genie), Bonzi (gorilla), Peedy (parrot), Rover (dog), Links (cat), Rocky (rock star), F1 (race driver), Genius (prodigy)
- Right-click menu → "Skin": each skin shows a **thumbnail preview**, current skin checked
- **Skin-switch transition animation**: old skin plays "Goodbye" → new skin plays "Hello" → back to idle
- **Per-skin perform-action menus**: only actions that have real animations for that skin are shown (e.g. Rover has the smallest set, its menu shrinks automatically)
- Semantic mapping falls back automatically (e.g. Rover uses `Money` when `Save` is missing), so every skin can perform actions

### 💧 Reminders
- **Water reminder**: every 45 minutes by default (interval editable in settings), `Alert` animation + classic yellow bubble + chime
- **Exercise reminder**: every 60 minutes by default, `GetAttention` animation + bubble
- Right-click menu to **toggle**, **set the interval** (Clippy-style bubble dialog), or snooze 10 minutes
- Silently skipped during fullscreen DND and deferred to the next cycle

### 🍅 Pomodoro
- 25 min work + 5 min break by default (configurable 1–180 min)
- Work plays `Thinking`, the last minute plays `Writing`, completion plays `Congratulate`, break plays `IdleSnooze` — each animation **plays once and returns to idle naturally** (no more infinite looping)

### ⌨ Global Hotkey Animations
- Press a hotkey and the pet plays the matching animation (**observe-only, never intercepts** — other apps still receive the key):
  | Hotkey | Action |
  |---|---|
  | Ctrl+S | Save |
  | Ctrl+P | Print |
  | Ctrl+F | Search |
  | Ctrl+Shift+M | Send mail |
  | Ctrl+Delete | Delete |
  | Ctrl+Shift+P | Processing |
- Toggle via right-click "⌨Global hotkey animations" (off by default); animations have a timeout guard so they never loop forever

### 🖥 Display Controls
- **Always on top** (default on)
- **Fullscreen DND**: auto-hides the pet and silences reminders when a true fullscreen app is detected (video/game/presentation), auto-restores on exit; **takes priority over always-on-top** — hides even when pinned, including Chrome F11 fullscreen
- **Launch at startup** (HKCU registry, user-level, no admin needed)
- **Resize**: 100% – 400%

### 🌐 Misc
- **Chinese/English menu toggle**
- Left-drag / double-click surprise / hover wave
- **Exit animation**: plays the current skin's "Goodbye" before quitting
- **Settings persistence**: all settings auto-saved to `settings.json`, restored on restart
- Natural idle animation: each idle pose shows for 2.5–4.5 s, then transitions gracefully through the closing frames

## 🚀 Run

### Option 1: Run the exe (recommended)
Build output is in `dist/ClippyPet-v0.1/` — double-click `ClippyPet-v0.1.exe`. **No Python needed**; copy the folder to another PC and it works.

### Option 2: Run from source
```bash
pip install pillow pyinstaller
python clippy_pet.py
```
Or double-click `run_clippy-pet.bat` (no console window; launches via Task Scheduler to avoid being killed by the terminal's cleanup).

## 📖 Usage

Right-click the pet to open the menu: water/exercise reminders (toggle + settings), Pomodoro (start/stop/settings), perform actions (filtered per skin), skin switcher, greet, about, always on top, fullscreen DND, launch at startup, global hotkey animations, language toggle, exit.

## 🛠 Build the exe

```bash
python -m PyInstaller --noconfirm --clean ClippyPet-v0.1.spec
```
- Output: `dist/ClippyPet-v0.1/ClippyPet-v0.1.exe` (onedir, bundles all skin assets)
- Generate icon: `python make_icon.py` (creates `clippy.ico` from Clippy's first frame)
- After packaging, `settings.json` is persisted next to the exe

## 📁 Project Layout

```
clippy-pet/
├── clippy_pet.py            # Main program (animation engine + reminders + Pomodoro + hotkeys + menus)
├── assets/
│   ├── skins/<skin>/        # 10 skins: frames/*.png sprite frames + animations.json
│   └── dl/skins/<skin>/     # Original official assets (agent.js + map.png)
├── extract_skins.py         # Skin extraction script (rebuilds skins/ from raw assets)
├── ClippyPet-v0.1.spec   # PyInstaller build config
├── make_icon.py             # exe icon generator
├── launch.py                # Background launcher (Task Scheduler based, survives terminal cleanup)
├── run_clippy-pet.bat       # No-console startup script (via Task Scheduler)
├── settings.json            # User settings (auto-generated)
└── Test scripts: smoke_test.py, hotkey_test.py, pomo_anim_test.py,
    skin_switch_test.py, skin_menu_test.py, dnd_pin_test.py, dnd_zorder_test.py,
    chrome_f11_test.py, idle_anim_test.py, reminder_settings_test.py,
    quit_test.py, frozen_test.py (packaged-path verification)
```

## ⚙️ Configuration

All settings are saved to `settings.json` automatically when changed via menus (language, skin, zoom, pin, DND, autostart, hotkey toggle, reminder intervals, Pomodoro durations, etc.). You may also edit the file directly (quit the app first).

## 📦 Asset Source

- Repository: [clippyjs/clippy.js](https://github.com/clippyjs/clippy.js) (MIT License)
- Assets: `agents/<name>/agent.js` (animation definitions) + `map.png` (sprite sheet)
