@echo off
rem clienthook - roll the proxy out as soon as the game is closed.
rem
rem   clienthook\rollback_watch.cmd --game "<the Call of Duty folder>"
rem   clienthook\rollback_watch.cmd                      (with KRONOS_GAME_DIR set)
rem
rem The DLL is locked while cod25-cod.exe runs, so the removal has to wait for it. Run this once, then close the
rem game: the folder goes back to the shipped state, no version.dll and no version_orig.dll.
rem
rem NOTE: run this in a real console. `timeout` and `2>nul` need a console; in a redirected shell they fail with
rem "Input redirection is not supported" and the loop spins.

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

echo waiting for cod25-cod.exe to exit ...

:wait
tasklist /fi "imagename eq cod25-cod.exe" | find /i "cod25-cod.exe" >nul
if not errorlevel 1 (
    ping -n 4 127.0.0.1 >nul
    goto wait
)

for %%f in ("%GAME%\version.dll" "%GAME%\version_orig.dll") do (
    if exist "%%~ff" ( del /f /q "%%~ff" & echo removed %%~ff )
)

if exist "%GAME%\version.dll" (
    echo ERROR: version.dll is still there - delete it by hand.
) else (
    echo rollback done - the game is back to the shipped client.
)
exit /b 0
