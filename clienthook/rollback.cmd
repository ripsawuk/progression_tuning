@echo off
rem clienthook rollback: remove the proxy. The game goes back to the system version.dll unchanged.
rem
rem   clienthook\rollback.cmd --game "<the Call of Duty folder>"
rem   clienthook\rollback.cmd                      (with KRONOS_GAME_DIR set)
rem
rem The game must be closed: both files are locked while cod25-cod.exe runs.

setlocal
rem The game folder: --game "<dir>" as the first argument, else KRONOS_GAME_DIR. Either form works - the folder
rem that holds cod25\, or cod25 itself.
set "GAME=%KRONOS_GAME_DIR%"
if /i "%~1"=="--game" set "GAME=%~2"

if not defined GAME (
    echo ERROR: no game folder given. Pass --game "C:\path\to\Call of Duty" or set KRONOS_GAME_DIR.
    exit /b 1
)
if exist "%GAME%\cod25" set "GAME=%GAME%\cod25"

tasklist /fi "imagename eq cod25-cod.exe" 2>nul | find /i "cod25-cod.exe" >nul
if not errorlevel 1 (
    echo ERROR: cod25-cod.exe is running. Close the game first.
    exit /b 1
)

for %%f in ("%GAME%\version.dll" "%GAME%\version_orig.dll") do (
    if exist "%%~ff" ( del /f /q "%%~ff" & echo removed %%~ff )
)

echo.
echo rollback done. clienthook.log, if present, is kept as evidence.
exit /b 0
