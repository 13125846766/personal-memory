@echo off
setlocal
where py >nul 2>nul
if errorlevel 1 goto use_python
py -3 "%~dp0skills\personal-memory\scripts\memory.py" serve --open
goto finish
:use_python
python "%~dp0skills\personal-memory\scripts\memory.py" serve --open
:finish
if errorlevel 1 pause
