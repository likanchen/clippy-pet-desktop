"""启动 Clippy Pet（可靠版）：
通过 Windows 计划任务（Task Scheduler）启动，进程父进程为 svchost，
彻底脱离终端进程树，避免被会话清理机制误杀。
用法: python launch.py
"""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PYW = os.path.join(os.path.dirname(sys.executable), "pythonw.exe")
if not os.path.exists(PYW):
    PYW = sys.executable
SCRIPT = os.path.join(HERE, "clippy_pet.py")

tr = '"%s" "%s"' % (PYW, SCRIPT)
r = subprocess.run(
    ["schtasks", "/Create", "/F", "/TN", "ClippyPet",
     "/TR", tr, "/SC", "ONCE", "/ST", "00:00"],
    capture_output=True, text=True)
print("CREATE:", r.returncode, (r.stdout or r.stderr).strip())

r = subprocess.run(["schtasks", "/Run", "/TN", "ClippyPet"],
                   capture_output=True, text=True)
print("RUN:", r.returncode, (r.stdout or r.stderr).strip())
