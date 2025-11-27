@echo off
setlocal enabledelayedexpansion

REM 当前目录
set ROOT=%cd%

for /d %%A in (*_res_export) do (
    echo [INFO] Process Dir: %%A

    REM 获取不带后缀的新目录名
    set NAME=%%A
    set NEWNAME=!NAME:_res_export=!

    REM 如果新目录不存在则重命名
    if not exist "!NEWNAME!" (
        ren "%%A" "!NEWNAME!"
    )

    REM 进入目录查找 CAB-* 子目录
    pushd "!NEWNAME!"
    for /d %%B in (CAB-*) do (
        echo [INFO] Move CAB Files: %%B
        move "%%B\*" ".\" >nul 2>&1
        rd "%%B"
    )
    popd
)

echo OK!
pause
