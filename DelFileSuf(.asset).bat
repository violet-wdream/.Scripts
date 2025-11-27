@echo off
setlocal enabledelayedexpansion

echo ================================================
echo [INFO] Delete .asset suffixes
echo ================================================

REM find all .asset files
for /r %%F in (*.asset) do (
    set "FULLPATH=%%~fF"
    set "DIR=%%~dpF"
    set "NAME=%%~nF"

    echo [RENAME] %%~nxF → !NAME!
    ren "%%F" "!NAME!"
)

echo ================================================
echo [DONE] All .asset files were renamed！
pause