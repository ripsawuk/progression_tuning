@echo off
rem clienthook build: our version.dll - the pass-through proxy plus the progression frame and the payment.
rem
rem   clienthook\build.cmd            -> build\version.dll
rem
rem Needs the x64 MSVC toolchain. It is discovered, not assumed: a developer prompt that already has cl, else
rem vswhere (the VS installer's own query tool) -latest, else VCINSTALLDIR. Nothing is copied into the game
rem here; install.cmd is a separate, explicit step.

setlocal
cd /d "%~dp0"

set "VSWHERE=%ProgramFiles(x86)%\Microsoft Visual Studio\Installer\vswhere.exe"

set VCVARS=
where /q cl.exe 2>nul
if not errorlevel 1 set VCVARS=cl.exe
if not defined VCVARS if exist "%VSWHERE%" (
    for /f "usebackq delims=" %%I in (`"%VSWHERE%" -latest -products * -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -find VC\Auxiliary\Build\vcvars64.bat 2^>nul`) do set "VCVARS=%%I"
)
if not defined VCVARS if defined VCINSTALLDIR if exist "%VCINSTALLDIR%Auxiliary\Build\vcvars64.bat" set "VCVARS=%VCINSTALLDIR%Auxiliary\Build\vcvars64.bat"

if not defined VCVARS (
    echo ERROR: no x64 MSVC toolchain found - install the Visual Studio C++ x64 tools, or run this
    echo        from a "x64 Native Tools Command Prompt for VS", and it uses cl from there.
    exit /b 1
)

if /i not "%VCVARS%"=="cl.exe" (
    call "%VCVARS%" >nul 2>&1
    if errorlevel 1 (
        echo ERROR: %VCVARS% failed
        exit /b 1
    )
)

if not exist "%~dp0build" mkdir "%~dp0build"
rem a leftover clienthook.log in build\ would otherwise accumulate one line per run
del /q "%~dp0build\clienthook.log" 2>nul
pushd "%~dp0build"

rem /Brepro: deterministic output. Without it every build stamps a new timestamp into the PE header, so
rem the rebuilt bytes never equal the installed ones and "hash read back equal" silently stops meaning
rem anything. With it a rebuild from the same source reproduces the same DLL.
rem
rem The eight sources, and what each carries:
rem   proxy_main.c  the 17 exports, the one-file System32 resolve, the host guard, DllMain
rem   frame.c       the identification pass, the g11 lock payload, the ptsplash_paid publish, the forced
rem                 publish's thread and its two triggers, the client's ops check
rem   resolve.c     every client address, found at run time: ten wildcarded patterns, the addresses derived from
rem                 them, the per-feature gate, and the one summary line
rem   publish.c     the forced publish's pure half: the page check, the 24-byte guard, the window, the kill
rem                 switch, the record fingerprint
rem   g11.c         the payload's pure half (hex, split, header, name hash, canary)
rem   master.c      the master-prestige level byte, hooked at the level function's five call sites
rem   nativepay.c   the 5 bytes at the award's call site: ev=95 pays the game's own field 45
rem   pubxp.c       the paid-XP text, the per-gun ledger and the record lookup
rem
rem `src\version_floor.c` is deliberately NOT compiled in: the user's 2026-11-12 decision is that the hook has
rem no game-version restriction. The files stay on disk, untouched, as the record of build 26.
rem /W3 and zero warnings is a build requirement, not an aspiration.
cl /nologo /LD /O2 /W3 /Brepro /DUNICODE /D_UNICODE "%~dp0src\proxy_main.c" "%~dp0src\frame.c" "%~dp0src\resolve.c" "%~dp0src\publish.c" "%~dp0src\g11.c" "%~dp0src\master.c" "%~dp0src\nativepay.c" "%~dp0src\pubxp.c" ^
   /link /DEF:"%~dp0src\version_proxy.def" /OUT:version.dll user32.lib /MACHINE:X64
set RC=%ERRORLEVEL%

rem the intermediates are byproducts, not deliverables: build\ keeps version.dll.
del /q "%~dp0build\*.obj" "%~dp0build\*.lib" "%~dp0build\*.exp" 2>nul

popd

if not "%RC%"=="0" (
    echo BUILD FAILED rc=%RC%
    exit /b %RC%
)

rem the hash file, in sha256sum form, so the artefact the installer takes is the one the tests read
call :hash "%~dp0build\version.dll" "%~dp0build\version.dll.sha256"

echo BUILT: %~dp0build\version.dll
type "%~dp0build\version.dll.sha256"
exit /b 0

rem %1 = file, %2 = hash file to write. certutil, so no PowerShell policy is involved.
:hash
set CH_SHA=
for /f "skip=1 usebackq delims=" %%H in (`certutil -hashfile %1 SHA256`) do (
    if not defined CH_SHA set CH_SHA=%%H
)
if not defined CH_SHA (
    echo ERROR: could not hash %1
    exit /b 1
)
> %2 echo %CH_SHA%  %~nx1
exit /b 0
