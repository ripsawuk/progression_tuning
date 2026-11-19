// clienthook - the token channel's dvar, and the file that carries it across a session
//
// `pt_tokens_ch` is one ascii line: p/w the remaining seconds of the operator and the weapon token, n the
// serial, and an optional c= with eight counts. the mod reads and writes that text, but nothing of the mod
// runs before a level start, so the dvar has to exist from boot and its value has to outlive the process
//
// the file sits at players\tokens.txt under the dll's own directory and is written the way the client writes
// its own store: a .tmp beside it, then a replace-rename. one line, 512 chars at most, and only [a-z0-9=;,] -
// anything else in the file is left alone and said once. the folder is the client's own: never made here

#include <windows.h>
#include <stdio.h>
#include <string.h>
#include <wchar.h>

#include "g11.h"
#include "tokens.h"

void ch_logf(const char *fmt, ...);          // proxy_main.c
void ch_self_dir(wchar_t *out, DWORD cch);   // proxy_main.c

#define TK_SUBDIR L"players"
#define TK_FILE L"tokens.txt"
#define TK_TICK_MS 1000   // read the dvar at most this often
#define TK_LOG_MS 30000   // one saved line per this window, after the first

static void *TK_DVAR;
static long TK_SLOT;
static int TK_ARMED;
static int TK_OFF;
static char TK_DISK[TOKENS_MAX + 1];   // what the file holds, as far as this process knows
static int TK_SAID;
static ULONGLONG TK_LOG_AT;
static ULONGLONG TK_TICK_AT;

int tokens_valid(const char *s, size_t n)
{
    if (s == NULL || n == 0 || n > TOKENS_MAX)
    {
        return 0;
    }
    for (size_t i = 0; i < n; i++)
    {
        char c = s[i];
        int ok = (c >= 'a' && c <= 'z') || (c >= '0' && c <= '9') || c == '=' || c == ';' || c == ',';
        if (!ok)
        {
            return 0;
        }
    }
    return 1;
}

// <dll dir>players\tokens.txt; the folder is the client's own and is never made here
static int tk_path(wchar_t *out, DWORD cch)
{
    wchar_t base[MAX_PATH];
    ch_self_dir(base, MAX_PATH);
    if (base[0] == L'\0')
    {
        return 0;
    }
    return _snwprintf_s(out, cch, _TRUNCATE, L"%s" TK_SUBDIR L"\\" TK_FILE, base) >= 0;
}

// 1 when the client's players folder is there: a save into a folder that is not is a skip, not a create
static int tk_folder(void)
{
    wchar_t base[MAX_PATH];
    wchar_t dir[MAX_PATH];
    ch_self_dir(base, MAX_PATH);
    if (base[0] == L'\0')
    {
        return 0;
    }
    if (_snwprintf_s(dir, MAX_PATH, _TRUNCATE, L"%s" TK_SUBDIR, base) < 0)
    {
        return 0;
    }
    DWORD a = GetFileAttributesW(dir);
    return (a != INVALID_FILE_ATTRIBUTES && (a & FILE_ATTRIBUTE_DIRECTORY) != 0) ? 1 : 0;
}

int tokens_read(const wchar_t *path, char *out, size_t cap, const char **why)
{
    if (why != NULL)
    {
        *why = "";
    }
    if (path == NULL || out == NULL || cap == 0)
    {
        return 0;
    }
    HANDLE f = CreateFileW(path, GENERIC_READ, FILE_SHARE_READ | FILE_SHARE_WRITE | FILE_SHARE_DELETE, NULL,
                           OPEN_EXISTING, FILE_ATTRIBUTE_NORMAL, NULL);
    if (f == INVALID_HANDLE_VALUE)
    {
        DWORD e = GetLastError();
        if (e == ERROR_FILE_NOT_FOUND || e == ERROR_PATH_NOT_FOUND)
        {
            return 0;
        }
        if (why != NULL)
        {
            *why = "the file could not be opened";
        }
        return -1;
    }
    // one byte past a full line and its line ending, so a longer file is seen as longer
    char buf[TOKENS_MAX + 3];
    DWORD got = 0;
    BOOL ok = ReadFile(f, buf, (DWORD)sizeof(buf), &got, NULL);
    CloseHandle(f);
    if (!ok)
    {
        if (why != NULL)
        {
            *why = "the file could not be read";
        }
        return -1;
    }
    size_t n = (size_t)got;
    while (n > 0 && (buf[n - 1] == '\n' || buf[n - 1] == '\r'))
    {
        n--;
    }
    if (n > TOKENS_MAX)
    {
        if (why != NULL)
        {
            *why = "the line is longer than 512 chars";
        }
        return -1;
    }
    if (n == 0)
    {
        if (why != NULL)
        {
            *why = "the file is empty";
        }
        return -1;
    }
    if (!tokens_valid(buf, n))
    {
        if (why != NULL)
        {
            *why = "the line carries a character outside [a-z0-9=;,]";
        }
        return -1;
    }
    if (n + 1 > cap)
    {
        if (why != NULL)
        {
            *why = "the buffer is too small";
        }
        return -1;
    }
    memcpy(out, buf, n);
    out[n] = '\0';
    return 1;
}

int tokens_write(const wchar_t *path, const char *line)
{
    if (path == NULL || line == NULL)
    {
        return -1;
    }
    size_t n = strlen(line);
    if (!tokens_valid(line, n))
    {
        return -1;
    }
    wchar_t tmp[MAX_PATH];
    if (_snwprintf_s(tmp, MAX_PATH, _TRUNCATE, L"%s.tmp", path) < 0)
    {
        return -1;
    }
    HANDLE f = CreateFileW(tmp, GENERIC_WRITE, 0, NULL, CREATE_ALWAYS, FILE_ATTRIBUTE_NORMAL, NULL);
    if (f == INVALID_HANDLE_VALUE)
    {
        return -1;
    }
    DWORD wrote = 0;
    BOOL ok = WriteFile(f, line, (DWORD)n, &wrote, NULL);
    if (ok && wrote == (DWORD)n)
    {
        ok = FlushFileBuffers(f);
    }
    CloseHandle(f);
    if (!ok || wrote != (DWORD)n)
    {
        DeleteFileW(tmp);
        return -1;
    }
    // the client's own store does it this way: rename over the old file, never edit it in place
    if (!MoveFileExW(tmp, path, MOVEFILE_REPLACE_EXISTING | MOVEFILE_WRITE_THROUGH))
    {
        DeleteFileW(tmp);
        return -1;
    }
    return 0;
}

// the first save is always said, then one per window
static int tk_may_say(ULONGLONG now)
{
    if (!TK_SAID)
    {
        TK_SAID = 1;
        TK_LOG_AT = now;
        return 1;
    }
    if (now - TK_LOG_AT >= TK_LOG_MS)
    {
        TK_LOG_AT = now;
        return 1;
    }
    return 0;
}

// one write; the file's value only becomes the known one when the write landed
static void tk_save(const char *line, ULONGLONG now, int force)
{
    wchar_t path[MAX_PATH];
    // the folder is the client's own: missing means skip, said once, never made here
    int rc = -1;
    if (tk_folder() && tk_path(path, MAX_PATH))
    {
        rc = tokens_write(path, line);
    }
    if (tk_may_say(now) || force)
    {
        if (rc == 0)
        {
            ch_logf("tokens: saved %s", line);
        }
        else
        {
            ch_logf("tokens: save failed - %s", line);
        }
    }
    if (rc == 0)
    {
        memcpy(TK_DISK, line, strlen(line) + 1);
    }
}

void tokens_arm(G11_REG reg, const unsigned char salt[16], long slot)
{
    if (TK_ARMED || TK_OFF || reg == NULL)
    {
        return;
    }
    wchar_t path[MAX_PATH];
    // static, not stack: this text is the dvar's default, and the engine may keep the pointer it was handed
    static char line[TOKENS_MAX + 1];
    const char *why = "";
    int got = 0;
    if (!tk_folder())
    {
        got = -1;
        why = "no players folder";
    }
    else if (tk_path(path, MAX_PATH))
    {
        got = tokens_read(path, line, sizeof(line), &why);
    }
    else
    {
        got = -1;
        why = "the dll's own directory could not be named";
    }
    if (got != 1)
    {
        strcpy_s(line, sizeof(line), TOKENS_DEFAULT);
    }
    // our own value is the default, so a dvar this call creates already holds what the file said
    void *d = reg(g11_hash_name(TOKENS_NAME, salt), line, 0, "progression tuning tokens");
    if (d == NULL)
    {
        return; // the engine's register is not usable yet: the caller retries
    }
    char **value = (char **)((char *)d + slot);
    if (!g11_page_writable(value))
    {
        TK_OFF = 1;
        ch_logf("tokens: refused - the value slot is not writable");
        return;
    }
    if (got == 1)
    {
        ch_logf("tokens: file %s", line);
    }
    else if (got == 0)
    {
        ch_logf("tokens: file none");
    }
    else
    {
        ch_logf("tokens: file rejected: %s", why);
    }
    strcpy_s(TK_DISK, sizeof(TK_DISK), line);
    *value = TK_DISK;
    TK_DVAR = d;
    TK_SLOT = slot;
    TK_ARMED = 1;
    ch_logf("tokens: registered %s = %s", TOKENS_NAME, TK_DISK);
}

// the dvar's text, or NULL when what it points at is not readable
static const char *tokens_value(void)
{
    const char *v = *(char **)((char *)TK_DVAR + TK_SLOT);
    if (v == NULL || !g11_page_ok(v))
    {
        return NULL;
    }
    return v;
}

void tokens_tick(void)
{
    if (!TK_ARMED)
    {
        return;
    }
    ULONGLONG now = GetTickCount64();
    if (TK_TICK_AT != 0 && now - TK_TICK_AT < TK_TICK_MS)
    {
        return;
    }
    TK_TICK_AT = now;
    const char *v = tokens_value();
    if (v == NULL)
    {
        return;
    }
    size_t n = strnlen(v, TOKENS_MAX + 1);
    if (!tokens_valid(v, n) || strcmp(v, TK_DISK) == 0)
    {
        return; // nothing to write, or nothing a reader would accept
    }
    char copy[TOKENS_MAX + 1];
    memcpy(copy, v, n + 1);
    tk_save(copy, now, 0);
}

void tokens_stop(void)
{
    if (!TK_ARMED)
    {
        return;
    }
    const char *v = tokens_value();
    if (v == NULL)
    {
        return;
    }
    size_t n = strnlen(v, TOKENS_MAX + 1);
    if (!tokens_valid(v, n) || strcmp(v, TK_DISK) == 0)
    {
        return;
    }
    char copy[TOKENS_MAX + 1];
    memcpy(copy, v, n + 1);
    tk_save(copy, GetTickCount64(), 1);
}

int tokens_armed(void)
{
    return TK_ARMED;
}
