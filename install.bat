@echo off

SET SCRIPT_DIR=%~dp0

cd /d %SCRIPT_DIR%

python -m pip install -r requirements.txt
python -m pip install -e .

if not exist previews mkdir previews

if not exist confirm mkdir confirm

python demo.py %*

pause
