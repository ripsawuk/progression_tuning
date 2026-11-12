// passthru_host - the offline host for clienthook build 21's host guard (tools\test_build21.py runs it).
//
// WHY IT EXISTS. Build 21 arms only when the process image is `cod25-cod.exe`. Two things have to be
// proven and neither can be proven from a python process (python.exe is a foreign image, which is one
// half of the answer, but it can never exercise the other half):
//
//   pass    (this exe under its own name)  - a process that is NOT the game loads build\version.dll,
//           calls one forwarded export, compares it with the system DLL's own answer, then FreeLibrary's
//           the DLL and keeps running. Nothing may crash, and the DLL must leave NO clienthook.log: build
//           20 started seven threads here, one of which was still inside the image when it was unmapped
//           (`version.dll_unloaded`, 0xc0000005 at image offset 0x61A2).
//
//   armed   (this exe copied to `cod25-cod.exe`) - the same load and the same forwarded call, but the
//           process exits with ExitProcess instead of FreeLibrary, so the loader terminates the threads
//           it started. That is what lets the harness read the armed path's log lines
//           (`proxy attached ...`, `init: version.dll resolved from ...`) without ever risking the
//           unload fault this build exists to remove.
//
// Usage:
//   passthru_host.exe pass  <full path to version.dll> [file to version-check]
//   passthru_host.exe armed <full path to version.dll> [file to version-check]
//
// Nothing is installed, nothing under the game folder is touched, and no file is written by this exe:
// the log lines it produces are the DLL's own, written next to the DLL.

#include <windows.h>
#include <stdio.h>
#include <string.h>

typedef DWORD(WINAPI *fn_size_w)(LPCWSTR, LPDWORD);
typedef BOOL(WINAPI *fn_info_w)(LPCWSTR, DWORD, DWORD, LPVOID);
typedef BOOL(WINAPI *fn_query_w)(LPCVOID, LPCWSTR, LPVOID *, PUINT);

static const wchar_t *g_target = NULL;

static void say(const char *fmt, ...)
{
    va_list ap;
    va_start(ap, fmt);
    vprintf(fmt, ap);
    va_end(ap);
    printf("\n");
    fflush(stdout);
}

// Ask a module for the fixed-file version of the target file, through the three exports the game itself
// imports (GetFileVersionInfoSizeW, GetFileVersionInfoW, VerQueryValueW). Returns 0 when the module
// cannot answer, else the size it reported; the version is left in *ver (0 when there is none).
static DWORD ask_version(HMODULE mod, unsigned *ver, int *queried)
{
    fn_size_w size_w = (fn_size_w)(void *)GetProcAddress(mod, "GetFileVersionInfoSizeW");
    fn_info_w info_w = (fn_info_w)(void *)GetProcAddress(mod, "GetFileVersionInfoW");
    fn_query_w query_w = (fn_query_w)(void *)GetProcAddress(mod, "VerQueryValueW");
    if (size_w == NULL || info_w == NULL || query_w == NULL)
    {
        return 0;
    }
    DWORD size = size_w(g_target, NULL);
    if (size == 0)
    {
        return 0;
    }
    void *block = malloc(size);
    if (block == NULL)
    {
        return 0;
    }
    *ver = 0;
    *queried = 0;
    if (info_w(g_target, 0, size, block))
    {
        void *out = NULL;
        UINT len = 0;
        if (query_w(block, L"\\", &out, &len) && out != NULL)
        {
            *queried = 1;
            const unsigned *ms = (const unsigned *)out;
            *ver = ((ms[2] >> 16) << 24) | ((ms[2] & 0xFFFF) << 16) | ((ms[3] >> 16) << 8) | (ms[3] & 0xFFFF);
        }
    }
    free(block);
    return size;
}

static int default_target(wchar_t *out, DWORD cch)
{
    UINT n = GetSystemDirectoryW(out, cch);
    if (n == 0 || n >= cch)
    {
        return 0;
    }
    if ((size_t)n + 13 > cch)
    {
        return 0;
    }
    wcscat_s(out, cch, L"\\notepad.exe");
    return 1;
}

int main(int argc, char **argv)
{
    if (argc < 3)
    {
        say("usage: passthru_host.exe pass|armed <full path to version.dll> [file to version-check]");
        return 2;
    }
    const int armed_mode = _stricmp(argv[1], "armed") == 0;
    const int pass_mode = _stricmp(argv[1], "pass") == 0;
    if (!armed_mode && !pass_mode)
    {
        say("passthru_host: unknown mode '%s' (pass or armed)", argv[1]);
        return 2;
    }

    wchar_t dll_path[MAX_PATH];
    if (MultiByteToWideChar(CP_ACP, 0, argv[2], -1, dll_path, MAX_PATH) <= 0)
    {
        say("passthru_host: cannot widen the DLL path");
        return 2;
    }

    wchar_t target[MAX_PATH];
    if (argc > 3)
    {
        MultiByteToWideChar(CP_ACP, 0, argv[3], -1, target, MAX_PATH);
    }
    else if (!default_target(target, MAX_PATH))
    {
        say("passthru_host: no target file to read a version from");
        return 2;
    }
    g_target = target;

    // 1. who is this process? The whole test is this line.
    wchar_t self[MAX_PATH];
    DWORD self_n = GetModuleFileNameW(NULL, self, MAX_PATH);
    char self_a[MAX_PATH * 2];
    self_a[0] = '\0';
    if (self_n > 0)
    {
        WideCharToMultiByte(CP_ACP, 0, self, -1, self_a, (int)sizeof(self_a), NULL, NULL);
    }
    say("host: image %s", self_a[0] != '\0' ? self_a : "(unreadable)");
    say("host: mode %s", armed_mode ? "armed" : "pass");
    say("host: dll  %s", argv[2]);

    // 2. load the DLL under test BY FULL PATH, so the app directory cannot answer instead.
    HMODULE ours = LoadLibraryW(dll_path);
    if (ours == NULL)
    {
        say("host: FAIL LoadLibraryW rc=%lu", (unsigned long)GetLastError());
        return 1;
    }
    wchar_t got[MAX_PATH];
    DWORD got_n = GetModuleFileNameW(ours, got, MAX_PATH);
    char got_a[MAX_PATH * 2];
    got_a[0] = '\0';
    if (got_n > 0)
    {
        WideCharToMultiByte(CP_ACP, 0, got, -1, got_a, (int)sizeof(got_a), NULL, NULL);
    }
    say("host: loaded %s", got_a);

    // 3. one forwarded export, ours, then the system DLL's own answer for the same file.
    unsigned ver_ours = 0;
    int queried_ours = 0;
    DWORD size_ours = ask_version(ours, &ver_ours, &queried_ours);
    say("ours: GetFileVersionInfoSizeW=%lu version=0x%08X queried=%d", (unsigned long)size_ours, ver_ours,
        queried_ours);

    wchar_t sys_path[MAX_PATH];
    UINT sd = GetSystemDirectoryW(sys_path, MAX_PATH);
    if (sd == 0 || sd >= MAX_PATH)
    {
        say("host: FAIL cannot name the Windows system directory");
        return 1;
    }
    wcscat_s(sys_path, MAX_PATH, L"\\version.dll");
    HMODULE sysdll = LoadLibraryExW(sys_path, NULL, LOAD_LIBRARY_SEARCH_SYSTEM32);
    if (sysdll == NULL)
    {
        say("host: FAIL the system version.dll did not load rc=%lu", (unsigned long)GetLastError());
        return 1;
    }
    unsigned ver_sys = 0;
    int queried_sys = 0;
    DWORD size_sys = ask_version(sysdll, &ver_sys, &queried_sys);
    say("system: GetFileVersionInfoSizeW=%lu version=0x%08X queried=%d", (unsigned long)size_sys, ver_sys,
        queried_sys);
    say("host: answers equal = %s", (size_ours == size_sys && ver_ours == ver_sys) ? "YES" : "NO");

    int rc = (size_ours == size_sys && size_sys != 0 && ver_ours == ver_sys) ? 0 : 1;

    if (armed_mode)
    {
        // The armed path started our threads in this process. ExitProcess is the way out that cannot test
        // the unload fault: the loader terminates the other threads and only then unmaps the images, so
        // the armed host proves the LOG and the FORWARDING without asking the crash question here.
        say("host: exiting with ExitProcess (armed image - the loader terminates the threads)");
        ExitProcess((UINT)rc);
    }

    // 4. the pass-through proof: FreeLibrary the DLL under test, then keep using the process. Build 20's
    // failure was a thread of ours still executing inside this image a moment after this point.
    if (!FreeLibrary(ours))
    {
        say("host: FAIL FreeLibrary rc=%lu", (unsigned long)GetLastError());
        return 1;
    }
    say("host: FreeLibrary done");
    Sleep(400);
    if (GetModuleHandleW(dll_path) != NULL)
    {
        say("host: NOTE the module is still loaded (another reference?)");
    }
    unsigned ver_after = 0;
    int queried_after = 0;
    DWORD size_after = ask_version(sysdll, &ver_after, &queried_after);
    say("after: the system DLL still answers (%lu), so this process is alive", (unsigned long)size_after);
    if (size_after != size_sys)
    {
        rc = 1;
    }
    FreeLibrary(sysdll);
    say("passthru: %s", rc == 0 ? "OK - forwarded, unloaded, no crash" : "FAIL");
    return rc;
}
