@echo off
rem clienthook - build every offline test driver into build\.
rem
rem   clienthook\tools\build_tests.cmd
rem
rem The harness runs build\<name>_test.exe; before this script existed that step was ad hoc and written down in
rem LADDER.md, so a fresh checkout could not run the suite. Nothing is installed and nothing is copied into the
rem game folder here.
rem
rem Every driver compiles the SHIPPED unit it tests - the same .c files the DLL is built from - so what is
rem proven is what runs, not a copy.

setlocal
cd /d "%~dp0"

rem The toolchain is discovered, not assumed (the same block as clienthook\build.cmd): cl already on PATH from a
rem developer prompt, else vswhere -latest, else VCINSTALLDIR.
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

if not exist "%~dp0..\build" mkdir "%~dp0..\build"
if not exist "%~dp0..\build\testsrc" mkdir "%~dp0..\build\testsrc"
del /q "%~dp0..\build\clienthook.log" 2>nul

set RC=0

call :build g11_test "%~dp0g11_test.c" "%~dp0..\src\g11.c"
rem build 25: master.c and nativepay.c ask the resolver where the client's addresses are, so both drivers carry
rem the SHIPPED src\resolve.c beside their own unit.
call :build master_test "%~dp0master_test.c" "%~dp0..\src\master.c" "%~dp0..\src\resolve.c"
call :build detour_test "%~dp0detour_test.c" "%~dp0..\src\master.c" "%~dp0..\src\resolve.c"
call :build pubxp_test "%~dp0pubxp_test.c" "%~dp0..\src\pubxp.c"
rem tokens.c carries the token channel's text and its file, so its driver links the shipped g11.c beside it
rem (the page checks and the name hash are g11's).
call :build tokens_test "%~dp0tokens_test.c" "%~dp0..\src\tokens.c" "%~dp0..\src\g11.c"
rem pick.c carries the armory pick channel's text, its file and the queue walk, so its driver links the
rem shipped g11.c beside it (the page checks and the name hash are g11's) and resolve.c (the record array's
rem two addresses), exactly as master_test and nativepay_test do.
call :build pick_test "%~dp0pick_test.c" "%~dp0..\src\pick.c" "%~dp0..\src\g11.c" "%~dp0..\src\resolve.c"
rem armory.c carries the xp feed's line, its state, its change log and the pay that rides the client's own award,
rem so its driver links the shipped g11.c beside it (the page checks and the name hash are g11's) and resolve.c
rem (the record array's two addresses), exactly as pick_test does.
call :build armory_test "%~dp0armory_test.c" "%~dp0..\src\armory.c" "%~dp0..\src\g11.c" "%~dp0..\src\resolve.c"
call :build publish_test "%~dp0publish_test.c" "%~dp0..\src\publish.c"
call :build nativepay_test "%~dp0nativepay_test.c" "%~dp0..\src\nativepay.c" "%~dp0..\src\resolve.c"
rem resolve_check.exe is the resolver's own checker: the shipped src\resolve.c over a PE file on disk.
call :build resolve_check "%~dp0resolve_check\resolve_check.c" "%~dp0..\src\resolve.c"
rem guard_test.exe carries the SHIPPED src\proxy_main.c, so the arm decision under test is the one the DLL is
rem built from; its three stubbed entry points are in the driver itself.
rem ch_passthru_host.exe is the host the pass-through test loads the DLL into (its name is the point).
call :build guard_test "%~dp0guard_test.c" "%~dp0..\src\proxy_main.c"
rem logline_test.exe includes the SHIPPED src\proxy_main.c outright (its own comment says why): this build's
rem bounded log_line is static, so the only way to call it with an over-long text is from its own translation unit.
call :build logline_test "%~dp0logline_test.c"
call :build ch_passthru_host "%~dp0passthru_host.c"

del /q "%~dp0..\build\testsrc\*.obj" 2>nul
del /q "%~dp0..\build\*.lib" "%~dp0..\build\*.exp" 2>nul

if not "%RC%"=="0" (
    echo TESTS BUILD FAILED rc=%RC%
    exit /b %RC%
)
echo BUILT: the drivers in %~dp0..\build
exit /b 0

:build
rem %1 = exe name, %2 = driver source, %3..%5 = the units under test (any may be empty)
cl /nologo /O2 /W3 /Brepro "%~2" %3 %4 %5 /Fo"%~dp0..\build\testsrc\\" /Fe:"%~dp0..\build\%~1.exe" ^
   /link user32.lib /MACHINE:X64
if errorlevel 1 (
    echo ERROR: %~1 failed
    set RC=1
)
exit /b 0
