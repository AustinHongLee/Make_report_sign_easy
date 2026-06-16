@echo off
setlocal EnableExtensions

set "ROOT=%~dp0"
cd /d "%ROOT%"
set "PYTHONPATH=%ROOT%src;%PYTHONPATH%"
set "VALUES=%ROOT%samples\values_sample.json"

for %%F in ("%ROOT%samples"\*.pdf) do (
    if /I not "%%~nxF"=="Fount.pdf" (
        set "TEMPLATE=%%~fF"
        goto :found_template
    )
)

:found_template
if not defined TEMPLATE (
    echo No sample PDF template was found under "%ROOT%samples".
    exit /b 1
)

if not exist "%VALUES%" (
    echo Missing sample values JSON: "%VALUES%"
    exit /b 1
)

set "INTERACTIVE=0"
if "%~1"=="" (
    set "INTERACTIVE=1"
    goto :menu
)

if /I "%~1"=="gui" goto :gui
if /I "%~1"=="smoke" goto :smoke
if /I "%~1"=="tests" goto :tests
if /I "%~1"=="test" goto :tests
if /I "%~1"=="install" goto :install
if /I "%~1"=="help" goto :help
goto :help

:menu
echo.
echo HandFont Studio test launcher
echo Project: %ROOT%
echo.
echo   1. Open GUI with sample template and values
echo   2. Run G5 smoke test
echo   3. Run ruff + pytest
echo   4. Install/update editable environment
echo.
set /p "CHOICE=Choose [1-4, default 1]: "
if "%CHOICE%"=="" set "CHOICE=1"
if "%CHOICE%"=="1" goto :gui
if "%CHOICE%"=="2" goto :smoke
if "%CHOICE%"=="3" goto :tests
if "%CHOICE%"=="4" goto :install
echo Unknown choice: %CHOICE%
goto :done_error

:gui
echo.
echo Opening HandFont Studio with sample data...
echo Template: %TEMPLATE%
echo Values:   %VALUES%
set "QT_QPA_PLATFORM=windows"
python -m Make_report_sign_easy.gui.app --template "%TEMPLATE%" --values "%VALUES%"
if errorlevel 1 goto :done_error
goto :done_ok

:smoke
echo.
echo Running G5 smoke test...
set "OUTDIR=%TEMP%\mrse-g5-manual-%RANDOM%%RANDOM%"
set "BATCHDIR=%OUTDIR%\batch"
set "SINGLE=%OUTDIR%\single.pdf"
set "SHOT=%OUTDIR%\workbench.png"
set "PDF1=%BATCHDIR%\batch-1.pdf"
set "PDF2=%BATCHDIR%\batch-2.pdf"
mkdir "%OUTDIR%" >nul 2>nul

set "QT_QPA_PLATFORM=offscreen"
python -m Make_report_sign_easy.gui.app --smoke --template "%TEMPLATE%" --values "%VALUES%" --smoke-preview --smoke-profile --smoke-batch-dir "%BATCHDIR%" --smoke-output "%SINGLE%" --smoke-screenshot "%SHOT%"
if errorlevel 1 goto :done_error

echo.
echo Smoke output folder:
echo %OUTDIR%
echo.
echo Main files:
echo   %SINGLE%
echo   %SHOT%
echo   %PDF1%
echo   %PDF2%
goto :done_ok

:tests
echo.
echo Running ruff + pytest...
python -m ruff check .
if errorlevel 1 goto :done_error
python -m pytest
if errorlevel 1 goto :done_error
goto :done_ok

:install
echo.
echo Installing/updating editable environment...
python -m pip install -r requirements.txt
if errorlevel 1 goto :done_error
if exist requirements-dev.txt (
    python -m pip install -r requirements-dev.txt
    if errorlevel 1 goto :done_error
)
python -m pip install -e .
if errorlevel 1 goto :done_error
goto :done_ok

:help
echo Usage:
echo   test_workbench.bat gui      Open the GUI with sample data
echo   test_workbench.bat smoke    Run GUI smoke, batch smoke, and hash check
echo   test_workbench.bat tests    Run ruff + pytest
echo   test_workbench.bat install  Install dependencies and editable package
exit /b 1

:done_ok
echo.
echo Done.
if "%INTERACTIVE%"=="1" pause
exit /b 0

:done_error
echo.
echo Failed.
if "%INTERACTIVE%"=="1" pause
exit /b 1
