@echo off
setlocal EnableExtensions

set "OUT_DIR=..\dll"
set "DLL_NAME=graph_core.dll"
set "OBJ_FILES=graph_core.obj graph_math.obj graph_manager.obj graph_plot.obj graph_view.obj"
set "GCC="

if not exist "%OUT_DIR%" mkdir "%OUT_DIR%"

where nasm >nul 2>nul
if errorlevel 1 (
    echo Loi: Khong tim thay NASM trong PATH.
    exit /b 1
)

where x86_64-w64-mingw32-gcc >nul 2>nul
if not errorlevel 1 set "GCC=x86_64-w64-mingw32-gcc"

if not defined GCC (
    where gcc >nul 2>nul
    if not errorlevel 1 set "GCC=gcc"
)

if not defined GCC (
    echo Loi: Khong tim thay MinGW-w64 gcc trong PATH.
    exit /b 1
)

echo Building graph_core.dll...

nasm -f win64 graph_core.asm -o graph_core.obj
if errorlevel 1 exit /b 1

nasm -f win64 graph_math.asm -o graph_math.obj
if errorlevel 1 exit /b 1

nasm -f win64 graph_manager.asm -o graph_manager.obj
if errorlevel 1 exit /b 1

nasm -f win64 graph_plot.asm -o graph_plot.obj
if errorlevel 1 exit /b 1

nasm -f win64 graph_view.asm -o graph_view.obj
if errorlevel 1 exit /b 1

%GCC% -shared -o "%OUT_DIR%\%DLL_NAME%" %OBJ_FILES% graph_core.def
if errorlevel 1 exit /b 1

del /q %OBJ_FILES% >nul 2>nul
echo Done: %OUT_DIR%\%DLL_NAME%
exit /b 0
