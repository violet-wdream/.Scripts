@echo off
setlocal enabledelayedexpansion

echo ================================================
echo [INFO] Delete .prefab suffixes
echo ================================================

REM find all .prefab files
for /r %%F in (*.prefab) do (
    set "FULLPATH=%%~fF"
    set "DIR=%%~dpF"
    set "NAME=%%~nF"

    echo [RENAME] %%~nxF → !NAME!
    ren "%%F" "!NAME!"
)

echo ================================================
echo [DONE] All .prefab files were renamed！
pause