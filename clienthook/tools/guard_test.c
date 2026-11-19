// guard_test - the offline unit proof of clienthook build 21's host guard (tools\test_build21.py runs it).
//
// It compiles the SHIPPED decision - src\proxy_main.c's `ch_arm_for_image()` and `ch_arm_here()` - not a
// copy of the rule, and asks it about image names. The three entry points DllMain names are stubbed here
// so the proxy can be linked into an exe; nothing in this driver calls DllMain, and nothing it does
// touches the loader, the disk or the game.
//
//   build\guard_test.exe self     -> one line per case, then "guard: OK - N checks" (exit 0) or the failures

#include <windows.h>
#include <stdio.h>
#include <wchar.h>

// The symbols DllMain's body references. Never called here.
void ch_frame_start(void)
{
}
void nativepay_start(void)
{
}
void nativepay_stop(void)
{
}
void opsfix_start(void)
{
}
void opsfix_stop(void)
{
}
void tokens_stop(void)
{
}

// The shipped functions.
BOOL ch_arm_for_image(const wchar_t *image_path);

static int passes = 0;
static int failures = 0;

static void ok(int cond, const wchar_t *what, const wchar_t *path, int want)
{
    if (cond)
    {
        passes++;
        wprintf(L"pass  %s (%s -> %s)\n", what, path != NULL ? path : L"(null)", want ? L"arm" : L"pass-through");
    }
    else
    {
        failures++;
        wprintf(L"FAIL  %s (%s -> wanted %s)\n", what, path != NULL ? path : L"(null)", want ? L"arm" : L"pass-through");
    }
}

static void case_(const wchar_t *path, int want, const wchar_t *what)
{
    ok(ch_arm_for_image(path) == (want ? TRUE : FALSE), what, path, want);
}

int main(int argc, char **argv)
{
    (void)argc;
    (void)argv;

    // --- the game, in the shapes a real install takes ------------------------------------------------
    case_(L"D:\\Games\\Call of Duty\\cod25\\cod25-cod.exe", 1, L"the game, by full path");
    case_(L"cod25-cod.exe", 1, L"the game, as a bare image name");
    case_(L"C:/Games/cod25/cod25-cod.exe", 1, L"the game, with forward slashes");
    case_(L"C:\\Games\\cod25\\COD25-COD.EXE", 1, L"the game, upper case (the test is case-insensitive)");
    case_(L"C:\\Games\\cod25\\CoD25-CoD.Exe", 1, L"the game, mixed case");
    case_(L"\\\\?\\C:\\Games\\cod25\\cod25-cod.exe", 1, L"the game behind a \\\\?\\ prefix");

    // --- the process that actually faulted -----------------------------------------------------------
    case_(L"D:\\Games\\Call of Duty\\cod25\\codCrashHandler.exe", 0, L"codCrashHandler.exe - the crash");
    case_(L"D:\\Games\\Call of Duty\\cod25\\KronosLauncher.exe", 0, L"the Kronos launcher");
    case_(L"C:\\Windows\\System32\\notepad.exe", 0, L"an unrelated exe");
    case_(L"C:\\Python\\python.exe", 0, L"the harness's own interpreter");

    // --- near misses that must NOT arm ---------------------------------------------------------------
    case_(L"C:\\Games\\cod25-cod.exe\\game.exe", 0, L"a directory named cod25-cod.exe");
    case_(L"C:\\Games\\cod25\\cod25-cod.exe.bak", 0, L"a dotfile-ish neighbour");
    case_(L"C:\\Games\\cod25\\cod25-cod.exe ", 0, L"a trailing space is a different name");
    case_(L"C:\\Games\\cod25\\cod25-cod.exe\\", 0, L"a trailing separator means no file name");
    case_(L"C:\\Games\\cod25\\xcod25-cod.exe", 0, L"a longer name ending in the game's");
    case_(L"C:\\Games\\cod25\\cod25-cod.exe.old\\cod25-cod.exe", 1, L"the game inside a directory named like it");
    case_(L"", 0, L"the empty string");
    case_(NULL, 0, L"a null pointer");

    // --- the loader's answer in THIS process ---------------------------------------------------------
    {
        wchar_t self[MAX_PATH];
        DWORD n = GetModuleFileNameW(NULL, self, MAX_PATH);
        if (n > 0 && n < MAX_PATH)
        {
            wprintf(L"info  this process's image is %s\n", self);
            // guard_test.exe is never cod25-cod.exe, so this driver's own answer must be pass-through:
            // the same question DllMain asks, through the same function.
            ok(ch_arm_for_image(self) == FALSE, L"this driver's own image does not arm", self, 0);
        }
        else
        {
            failures++;
            wprintf(L"FAIL  the driver could not read its own image name\n");
        }
    }

    wprintf(L"\n");
    if (failures == 0)
    {
        wprintf(L"guard: OK - %d checks\n", passes);
        return 0;
    }
    wprintf(L"guard: %d passed, %d FAILED\n", passes, failures);
    return 1;
}
