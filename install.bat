@echo off

SET SCRIPT_DIR=%~dp0

cd /d %SCRIPT_DIR%

python -m pip install -r requirements.txt
python -m pip install -e .

echo Installed Make Report Sign Easy.
echo Start the GUI with: python tools\fill_pdf_gui.py
echo Or run the CLI with: handfont-fill-pdf --help

pause
