@echo off
rem clienthook install: put the proxy in the game folder.
rem
rem   clienthook\install.cmd --game "<the Call of Duty folder>"
rem   clienthook\install.cmd                      (with KRONOS_GAME_DIR set)
rem
rem The game folder is the install that holds cod25\, or cod25 itself. The game must be closed.
rem
rem This installs build\version.dll - the DLL build.cmd produced, or the one from the release package. It writes
rem exactly two files:
rem
rem   cod25\version.dll        our proxy
rem   cod25\clienthook.log     written by the proxy itself at load, one line per attach
rem
rem and it deletes a cod25\version_orig.dll left behind by an older build: the proxy loads the system DLL from
rem C:\Windows\System32 at run time, so there is no side-by-side copy any more.
rem
rem Rollback: clienthook\rollback.cmd (deletes both; the log is kept as evidence).

setlocal
rem The game folder: --game "<dir>" as the first argument, else KRONOS_GAME_DIR. Either form works - the folder
rem that holds cod25\, or cod25 itself.
set "GAME=%KRONOS_GAME_DIR%"
if /i "%~1"=="--game" set "GAME=%~2"

if not defined GAME (
    echo ERROR: no game folder given. Pass --game "C:\path\to\Call of Duty" or set KRONOS_GAME_DIR.
    echo        The folder is the install that holds cod25\, or cod25 itself.
    exit /b 1
)
if exist "%GAME%\cod25" set "GAME=%GAME%\cod25"
if not exist "%GAME%\cod25-cod.exe" (
    echo ERROR: %GAME% does not look like the cod25 folder - there is no cod25-cod.exe in it.
    exit /b 1
)

tasklist /fi "imagename eq cod25-cod.exe" 2>nul | find /i "cod25-cod.exe" >nul
if not errorlevel 1 (
    echo ERROR: cod25-cod.exe is running. Close the game first.
    exit /b 1
)

if not exist "%~dp0build\version.dll" (
    echo ERROR: build\version.dll missing - run clienthook\build.cmd first, or unzip the release package's file here
    exit /b 1
)

if exist "%GAME%\version_orig.dll" (
    del /f /q "%GAME%\version_orig.dll"
    echo removed %GAME%\version_orig.dll  ^(not needed - the system DLL is loaded by full path^)
)

copy /y "%~dp0build\version.dll" "%GAME%\version.dll" >nul || exit /b 1

echo.
echo installed:
for %%f in ("%GAME%\version.dll") do (
    echo   %%~ff
    certutil -hashfile "%%~ff" SHA256 | find /v ":" | find /v "CertUtil"
)
echo.
echo launch the game, then check %GAME%\clienthook.log
exit /b 0
