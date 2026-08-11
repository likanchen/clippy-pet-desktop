@echo off
rem 通过计划任务启动（脱离 bash/控制台进程树，避免被误杀）
start "" pythonw "%~dp0launch.py"
