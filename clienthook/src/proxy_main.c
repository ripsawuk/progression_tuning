// clienthook - a pass-through proxy for version.dll, and the carrier for this workstream's in-process code.
//
// WHAT THIS FILE IS. `cod25-cod.exe` imports version.dll statically, version.dll is not a KnownDLL (so the
// loader takes the app-directory copy first), it has 17 named exports and no ordinals, and it appears in
// neither launcher_manifest.txt nor launcher_hashes.txt. Every one of the 17 exports here forwards to the
// function it took from the real DLL, so the game's own behaviour is unchanged.
//
//   * the real DLL is resolved from the Windows system directory at run time: `GetSystemDirectoryW` then
//     `LoadLibraryExW(<that>\version.dll, NULL, LOAD_LIBRARY_SEARCH_SYSTEM32)`. There is no `version_orig.dll`
//     beside it - the build is ONE file in the game folder.
//   * `DllMain` starts the frame (ch_frame_start: the install gate, the lock payload, the published weapon XP)
//     and THEN nativepay_start - in that order, because the frame is what hands nativepay its paid hook and the
//     shared install gate.
//
// THE HOST GUARD. The game is not the only process that loads this file. `codCrashHandler.exe` reaches
// version.dll through the api-ms-win-core-version API set that shell32 imports, and in that process there is no
// XINPUT9_1_0.dll, no client and no reason for threads of ours to exist - started there, one of them was still
// executing inside our image when the image had been unmapped: `version.dll_unloaded`, 0xc0000005, execute
// fault, image offset 0x61A2. So `DllMain` asks the loader for
// the host image name and arms only for `cod25-cod.exe`. In every other process this DLL is the 17 exports and
// nothing else: no hooks, no threads, no log write, no file I/O, so nothing of ours can outlive the unload. The
// forwarding still happens there - the export wrapper resolves the system DLL on its first call.

#include <windows.h>
#include <stdarg.h>
#include <stdio.h>
#include <string.h>

// --- the original DLL, resolved from C:\Windows\System32 at run time --------------------------------

typedef DWORD(WINAPI *fn_size_a)(LPCSTR, LPDWORD);
typedef DWORD(WINAPI *fn_size_w)(LPCWSTR, LPDWORD);
typedef DWORD(WINAPI *fn_size_ex_a)(DWORD, LPCSTR, LPDWORD);
typedef DWORD(WINAPI *fn_size_ex_w)(DWORD, LPCWSTR, LPDWORD);
typedef BOOL(WINAPI *fn_info_a)(LPCSTR, DWORD, DWORD, LPVOID);
typedef BOOL(WINAPI *fn_info_w)(LPCWSTR, DWORD, DWORD, LPVOID);
typedef BOOL(WINAPI *fn_info_ex_a)(DWORD, LPCSTR, DWORD, DWORD, LPVOID);
typedef BOOL(WINAPI *fn_info_ex_w)(DWORD, LPCWSTR, DWORD, DWORD, LPVOID);
typedef DWORD(WINAPI *fn_find_a)(DWORD, LPCSTR, LPCSTR, LPCSTR, LPSTR, PUINT, LPSTR, PUINT);
typedef DWORD(WINAPI *fn_find_w)(DWORD, LPCWSTR, LPCWSTR, LPCWSTR, LPWSTR, PUINT, LPWSTR, PUINT);
typedef DWORD(WINAPI *fn_install_a)(DWORD, LPCSTR, LPCSTR, LPCSTR, LPCSTR, LPSTR, PUINT);
typedef DWORD(WINAPI *fn_install_w)(DWORD, LPCWSTR, LPCWSTR, LPCWSTR, LPCWSTR, LPWSTR, PUINT);
typedef DWORD(WINAPI *fn_lang_a)(DWORD, LPSTR, DWORD);
typedef DWORD(WINAPI *fn_lang_w)(DWORD, LPWSTR, DWORD);
typedef BOOL(WINAPI *fn_query_a)(LPCVOID, LPCSTR, LPVOID *, PUINT);
typedef BOOL(WINAPI *fn_query_w)(LPCVOID, LPCWSTR, LPVOID *, PUINT);
typedef BOOL(WINAPI *fn_by_handle)(DWORD, HANDLE, LPVOID);

static struct
{
    HMODULE mod;
    fn_size_a size_a;
    fn_size_w size_w;
    fn_size_ex_a size_ex_a;
    fn_size_ex_w size_ex_w;
    fn_info_a info_a;
    fn_info_w info_w;
    fn_info_ex_a info_ex_a;
    fn_info_ex_w info_ex_w;
    fn_find_a find_a;
    fn_find_w find_w;
    fn_install_a install_a;
    fn_install_w install_w;
    fn_lang_a lang_a;
    fn_lang_w lang_w;
    fn_query_a query_a;
    fn_query_w query_w;
    fn_by_handle by_handle;
} ORIG;

static INIT_ONCE ONCE = INIT_ONCE_STATIC_INIT;

// This DLL's own directory: where the log goes, and the path load_orig compares the resolved module against.
static void self_dir(wchar_t *out, DWORD cch)
{
    HMODULE self = NULL;
    if (!GetModuleHandleExW(GET_MODULE_HANDLE_EX_FLAG_FROM_ADDRESS | GET_MODULE_HANDLE_EX_FLAG_UNCHANGED_REFCOUNT,
                            (LPCWSTR)&self_dir, &self))
    {
        out[0] = L'\0';
        return;
    }
    DWORD n = GetModuleFileNameW(self, out, cch);
    if (n == 0 || n >= cch)
    {
        out[0] = L'\0';
        return;
    }
    wchar_t *slash = wcsrchr(out, L'\\');
    if (slash == NULL)
    {
        out[0] = L'\0';
        return;
    }
    *(slash + 1) = L'\0';
}

// tokens.c names the same directory for its file: one copy of the rule, in this file
void ch_self_dir(wchar_t *out, DWORD cch)
{
    self_dir(out, cch);
}

// --- the host guard --------------------------------------------------------------------------------
//
// The proxy is a static-import target of more than the game. `codCrashHandler.exe` - a 1,516,024 B exe in
// the same folder - reaches version.dll through the api-ms-win-core-version API set that shell32.dll
// imports, so the app-directory copy wins the search there too. Started in that process, the frame's threads
// can never find a client and all of them are still alive when the image goes, which is the crash this guard
// removes (see the file header).
#define CH_GAME_IMAGE L"cod25-cod.exe"

// The arm decision, and the only place the rule lives. Pure: no I/O, no globals, so the offline driver can ask
// the shipped function directly. TRUE only when the image's FILE NAME is
// cod25-cod.exe: the path is not part of the test, so a moved install still arms; a directory that
// happens to be called cod25-cod.exe does not, and neither does cod25-cod.exe.bak.
BOOL ch_arm_for_image(const wchar_t *image_path)
{
    if (image_path == NULL || image_path[0] == L'\0')
    {
        return FALSE;
    }
    const wchar_t *name = image_path;
    for (const wchar_t *p = image_path; *p != L'\0'; p++)
    {
        if (*p == L'\\' || *p == L'/')
        {
            name = p + 1;
        }
    }
    return _wcsicmp(name, CH_GAME_IMAGE) == 0;
}

// The host, asked of the loader: GetModuleFileNameW(NULL) is this process's own exe. Anything we cannot
// read is a "no": an unnamed host never arms.
static BOOL ch_arm_here(void)
{
    wchar_t path[MAX_PATH];
    DWORD n = GetModuleFileNameW(NULL, path, MAX_PATH);
    if (n == 0 || n >= MAX_PATH)
    {
        return FALSE;
    }
    return ch_arm_for_image(path);
}

// Set once, at the top of DllMain's ATTACH, before a thread of ours can exist; read by log_line,
// DllMain's DETACH and nothing else. FALSE is the safe default: a call that somehow arrives before the
// guard has an answer writes nothing.
static BOOL g_armed = FALSE;

static void log_line(const char *text)
{
    // A process that is not the game gets no file I/O at all, this line included. `g_armed` is set once, at the
    // top of DllMain's ATTACH, before any thread of ours can exist, so this is the same answer every call in a
    // process: write the log, or never touch the disk.
    if (!g_armed)
    {
        return;
    }
    wchar_t path[MAX_PATH];
    self_dir(path, MAX_PATH);
    if (path[0] == L'\0')
    {
        return;
    }
    if (wcslen(path) + 16 >= MAX_PATH)
    {
        return;
    }
    wcscat_s(path, MAX_PATH, L"clienthook.log");

    HANDLE fh = CreateFileW(path, FILE_APPEND_DATA, FILE_SHARE_READ | FILE_SHARE_WRITE,
                            NULL, OPEN_ALWAYS, FILE_ATTRIBUTE_NORMAL, NULL);
    if (fh == INVALID_HANDLE_VALUE)
    {
        return;
    }
    SYSTEMTIME st;
    GetLocalTime(&st);
    // Bounded, always. `_snprintf_s` with `_TRUNCATE` never writes past `line`, always NUL-terminates, and
    // returns -1 when the text was cut (MSVC CRT, already linked here: resolve.c, nativepay.c, pubxp.c and
    // g11.c call it; no new import). wsprintfA has no bound at all - build 27's 490-char banner formatted a
    // 513-byte line into this 512-byte buffer and wrote two bytes over the /GS stack cookie, which killed the
    // process inside DllMain (docs\B27-NOLAUNCH.md 3.3). An over-long line is now truncated, never overflowed.
    char line[512];
    int len = _snprintf_s(line, sizeof(line), _TRUNCATE, "%04d-%02d-%02d %02d:%02d:%02d  %s\r\n",
                          st.wYear, st.wMonth, st.wDay, st.wHour, st.wMinute, st.wSecond, text);
    if (len < 0)
    {
        // Truncated: the CRLF at the end of the format was cut with the text. Put it back on the last two
        // bytes that fit, so a shortened line still ends where the next one starts. len is the stored length,
        // which is <= sizeof(line) - 1, so both writes are inside the buffer.
        len = (int)strlen(line);
        if (len >= 2)
        {
            line[len - 2] = '\r';
            line[len - 1] = '\n';
        }
    }
    if (len > 0)
    {
        DWORD wrote = 0;
        WriteFile(fh, line, (DWORD)len, &wrote, NULL);
    }
    CloseHandle(fh);
}

static BOOL CALLBACK load_orig(PINIT_ONCE once, PVOID param, PVOID *ctx)
{
    (void)once;
    (void)param;
    (void)ctx;

    // The real DLL is the SYSTEM one, named by its full path and resolved again on every process:
    //   <GetSystemDirectoryW()>\version.dll      (C:\Windows\System32\version.dll on this machine)
    // No side-by-side copy: that is what makes this build one file in the game folder. A Windows update may move
    // that file's bytes; a full path is re-resolved every launch, a copied version_orig.dll was pinned to one
    // Windows build. LOAD_LIBRARY_SEARCH_SYSTEM32 also keeps the dependency
    // search out of the game folder. A fully qualified path "searches only that path for the module" - the
    // same-base-name ambiguity is documented only for a name *without* a path - and the handle compare below is
    // the exact test that the module we got is not this one.
    wchar_t path[MAX_PATH];
    UINT n = GetSystemDirectoryW(path, MAX_PATH);
    if (n == 0 || n >= MAX_PATH)
    {
        log_line("init: cannot resolve the Windows system directory");
        return TRUE;
    }
    // "\\version.dll" is 12 chars + the terminator
    if ((size_t)n + 13 > MAX_PATH)
    {
        log_line("init: the Windows system directory path is too long");
        return TRUE;
    }
    wcscat_s(path, MAX_PATH, L"\\version.dll");

    ORIG.mod = LoadLibraryExW(path, NULL, LOAD_LIBRARY_SEARCH_SYSTEM32);
    if (ORIG.mod == NULL)
    {
        log_line("init: the system version.dll did not load");
        return TRUE;
    }

    // Two modules are now called version.dll. Prove the handle is the system file and not this one: the handle
    // compare is the exact test, and the resolved path is logged so the game's own log can be read against it.
    {
        HMODULE self = NULL;
        GetModuleHandleExW(GET_MODULE_HANDLE_EX_FLAG_FROM_ADDRESS |
                               GET_MODULE_HANDLE_EX_FLAG_UNCHANGED_REFCOUNT,
                           (LPCWSTR)&self_dir, &self);
        if (self != NULL && ORIG.mod == self)
        {
            // Never forward to ourselves: every export must then fail safely, not recurse.
            ORIG.mod = NULL;
            log_line("init: refused - the system version.dll resolved to THIS module; exports are dead");
            return TRUE;
        }
        {
            wchar_t got[MAX_PATH];
            DWORD got_n = GetModuleFileNameW(ORIG.mod, got, MAX_PATH);
            if (got_n == 0 || got_n >= MAX_PATH)
            {
                log_line("init: the system version.dll loaded but its path could not be read");
            }
            else
            {
                char said[MAX_PATH * 2];
                said[0] = '\0';
                if (WideCharToMultiByte(CP_ACP, 0, got, -1, said, (int)sizeof(said), NULL, NULL) <= 0)
                {
                    said[0] = '\0';
                }
                {
                    char line[512];
                    _snprintf_s(line, sizeof(line), _TRUNCATE, "init: version.dll resolved from %s", said);
                    log_line(line);
                }
            }
        }
    }

    ORIG.size_a = (fn_size_a)GetProcAddress(ORIG.mod, "GetFileVersionInfoSizeA");
    ORIG.size_w = (fn_size_w)GetProcAddress(ORIG.mod, "GetFileVersionInfoSizeW");
    ORIG.size_ex_a = (fn_size_ex_a)GetProcAddress(ORIG.mod, "GetFileVersionInfoSizeExA");
    ORIG.size_ex_w = (fn_size_ex_w)GetProcAddress(ORIG.mod, "GetFileVersionInfoSizeExW");
    ORIG.info_a = (fn_info_a)GetProcAddress(ORIG.mod, "GetFileVersionInfoA");
    ORIG.info_w = (fn_info_w)GetProcAddress(ORIG.mod, "GetFileVersionInfoW");
    ORIG.info_ex_a = (fn_info_ex_a)GetProcAddress(ORIG.mod, "GetFileVersionInfoExA");
    ORIG.info_ex_w = (fn_info_ex_w)GetProcAddress(ORIG.mod, "GetFileVersionInfoExW");
    ORIG.find_a = (fn_find_a)GetProcAddress(ORIG.mod, "VerFindFileA");
    ORIG.find_w = (fn_find_w)GetProcAddress(ORIG.mod, "VerFindFileW");
    ORIG.install_a = (fn_install_a)GetProcAddress(ORIG.mod, "VerInstallFileA");
    ORIG.install_w = (fn_install_w)GetProcAddress(ORIG.mod, "VerInstallFileW");
    ORIG.lang_a = (fn_lang_a)GetProcAddress(ORIG.mod, "VerLanguageNameA");
    ORIG.lang_w = (fn_lang_w)GetProcAddress(ORIG.mod, "VerLanguageNameW");
    ORIG.query_a = (fn_query_a)GetProcAddress(ORIG.mod, "VerQueryValueA");
    ORIG.query_w = (fn_query_w)GetProcAddress(ORIG.mod, "VerQueryValueW");
    ORIG.by_handle = (fn_by_handle)GetProcAddress(ORIG.mod, "GetFileVersionInfoByHandle");

    log_line("init: the system version.dll's 17 exports are resolved");
    return TRUE;
}

static void ensure(void)
{
    InitOnceExecuteOnce(&ONCE, load_orig, NULL, NULL);
}

// --- the 17 exports, each a straight pass-through to the system DLL ---------------------------------

DWORD WINAPI ch_GetFileVersionInfoSizeA(LPCSTR f, LPDWORD h)
{
    ensure();
    return ORIG.size_a ? ORIG.size_a(f, h) : 0;
}

DWORD WINAPI ch_GetFileVersionInfoSizeW(LPCWSTR f, LPDWORD h)
{
    ensure();
    return ORIG.size_w ? ORIG.size_w(f, h) : 0;
}

DWORD WINAPI ch_GetFileVersionInfoSizeExA(DWORD flags, LPCSTR f, LPDWORD h)
{
    ensure();
    return ORIG.size_ex_a ? ORIG.size_ex_a(flags, f, h) : 0;
}

DWORD WINAPI ch_GetFileVersionInfoSizeExW(DWORD flags, LPCWSTR f, LPDWORD h)
{
    ensure();
    return ORIG.size_ex_w ? ORIG.size_ex_w(flags, f, h) : 0;
}

BOOL WINAPI ch_GetFileVersionInfoA(LPCSTR f, DWORD h, DWORD len, LPVOID data)
{
    ensure();
    return ORIG.info_a ? ORIG.info_a(f, h, len, data) : FALSE;
}

BOOL WINAPI ch_GetFileVersionInfoW(LPCWSTR f, DWORD h, DWORD len, LPVOID data)
{
    ensure();
    return ORIG.info_w ? ORIG.info_w(f, h, len, data) : FALSE;
}

BOOL WINAPI ch_GetFileVersionInfoExA(DWORD flags, LPCSTR f, DWORD h, DWORD len, LPVOID data)
{
    ensure();
    return ORIG.info_ex_a ? ORIG.info_ex_a(flags, f, h, len, data) : FALSE;
}

BOOL WINAPI ch_GetFileVersionInfoExW(DWORD flags, LPCWSTR f, DWORD h, DWORD len, LPVOID data)
{
    ensure();
    return ORIG.info_ex_w ? ORIG.info_ex_w(flags, f, h, len, data) : FALSE;
}

DWORD WINAPI ch_VerFindFileA(DWORD flags, LPCSTR file, LPCSTR win, LPCSTR app,
                                               LPSTR cur, PUINT curlen, LPSTR dest, PUINT destlen)
{
    ensure();
    return ORIG.find_a ? ORIG.find_a(flags, file, win, app, cur, curlen, dest, destlen) : 0;
}

DWORD WINAPI ch_VerFindFileW(DWORD flags, LPCWSTR file, LPCWSTR win, LPCWSTR app,
                                               LPWSTR cur, PUINT curlen, LPWSTR dest, PUINT destlen)
{
    ensure();
    return ORIG.find_w ? ORIG.find_w(flags, file, win, app, cur, curlen, dest, destlen) : 0;
}

DWORD WINAPI ch_VerInstallFileA(DWORD flags, LPCSTR src, LPCSTR dest, LPCSTR srcname,
                                                  LPCSTR destname, LPSTR tmp, PUINT tmplen)
{
    ensure();
    return ORIG.install_a ? ORIG.install_a(flags, src, dest, srcname, destname, tmp, tmplen) : 0;
}

DWORD WINAPI ch_VerInstallFileW(DWORD flags, LPCWSTR src, LPCWSTR dest, LPCWSTR srcname,
                                                  LPCWSTR destname, LPWSTR tmp, PUINT tmplen)
{
    ensure();
    return ORIG.install_w ? ORIG.install_w(flags, src, dest, srcname, destname, tmp, tmplen) : 0;
}

DWORD WINAPI ch_VerLanguageNameA(DWORD lang, LPSTR buf, DWORD len)
{
    ensure();
    return ORIG.lang_a ? ORIG.lang_a(lang, buf, len) : 0;
}

DWORD WINAPI ch_VerLanguageNameW(DWORD lang, LPWSTR buf, DWORD len)
{
    ensure();
    return ORIG.lang_w ? ORIG.lang_w(lang, buf, len) : 0;
}

BOOL WINAPI ch_VerQueryValueA(LPCVOID block, LPCSTR sub, LPVOID *out, PUINT outlen)
{
    ensure();
    return ORIG.query_a ? ORIG.query_a(block, sub, out, outlen) : FALSE;
}

BOOL WINAPI ch_VerQueryValueW(LPCVOID block, LPCWSTR sub, LPVOID *out, PUINT outlen)
{
    ensure();
    return ORIG.query_w ? ORIG.query_w(block, sub, out, outlen) : FALSE;
}

BOOL WINAPI ch_GetFileVersionInfoByHandle(DWORD flags, HANDLE file, LPVOID data)
{
    ensure();
    return ORIG.by_handle ? ORIG.by_handle(flags, file, data) : FALSE;
}

void ch_logf(const char *fmt, ...)
{
    // Bounded like log_line: `_vsnprintf_s` + `_TRUNCATE` cannot write past `body`, always NUL-terminates and
    // returns -1 when it cut. It is the CRT's formatter, so a 64-bit or floating conversion in a future format
    // string will now work here; every caller today uses %d/%u/%x/%s/%02x only, so the text is unchanged.
    char body[512];
    va_list ap;
    va_start(ap, fmt);
    _vsnprintf_s(body, sizeof(body), _TRUNCATE, fmt, ap);
    va_end(ap);
    log_line(body);
}

BOOL APIENTRY DllMain(HMODULE self, DWORD reason, LPVOID reserved)
{
    (void)reserved;

    void ch_frame_start(void);
    void nativepay_start(void);
    void nativepay_stop(void);
    void opsfix_start(void);
    void opsfix_stop(void);
    void tokens_stop(void);
    void pick_stop(void);

    switch (reason)
    {
    case DLL_PROCESS_ATTACH:
        DisableThreadLibraryCalls(self);
        // The host decides. Only `cod25-cod.exe` gets the frame and the payment. Anywhere else -
        // codCrashHandler.exe above all - this DLL is its 17 exports and nothing else: no hook, no thread,
        // no log line, no file, nothing that could still be running when the image is unloaded. The
        // forwarding is untouched: the first export call resolves the system DLL.
        g_armed = ch_arm_here();
        if (!g_armed)
        {
            break;
        }
        // Two writers to one append-only file, both opening with share-all and writing whole lines: the proxy's
        // one-line writer (this file) and nativepay's buffered writer. Interleaving per line is expected.
        // the banner is measured, not estimated: 484 chars, so the formatted line is 19 + 2 + 484 + 2 = 507
        // bytes, 5 short of the 512-byte buffer in log_line and its /GS cookie (docs\B28-BOUNDED-LOG.md 1).
        log_line("proxy attached (version.dll build 37: one file - the system copy loads at run time, every "
                 "address from the game own code, the award call site pays field 45 on ev=95, "
                 "ptsplash_paid per payment, zm_g11_* the lock bitmap, zm_g12_* the challenge reward set, "
                 "master.c extends the level byte, an ops check branch forced on, state republished in match, "
                 "pt_tokens_ch, pt_armory_ch, pt_armory_xp at boot (the last the match xp feed), and the "
                 "armory pay rides the award wrapper in a live match)");
        // the client ops check armed before the client is mapped
        opsfix_start();
        // the frame first: it owns the paid hook and the install gate nativepay needs, and it starts the threads
        // both channels publish from
        ch_frame_start();
        nativepay_start();
        break;
    case DLL_PROCESS_DETACH:
        // Nothing was created in a pass-through process, so detach touches nothing there - not nativepay's
        // state, not the log. A process that never armed writes nothing at all here.
        if (!g_armed)
        {
            break;
        }
        // the token channel's last write, first of all: it is the only thing here whose loss would be data
        tokens_stop();
        pick_stop();
        nativepay_stop();
        // The loader notification is unregistered here, never from inside the callback that receives it.
        opsfix_stop();
        log_line("proxy detached");
        break;
    default:
        break;
    }
    return TRUE;
}
