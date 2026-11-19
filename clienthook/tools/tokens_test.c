// Offline driver for src\tokens.c: the one-line form, the file read, the tmp-and-rename write, and the arm /
// tick / stop path over a fabricated dvar. Links the SHIPPED unit; the client is never touched.
//
//   tokens_test.exe self                       the text, the read, the write
//   tokens_test.exe arm <dir> valid|none|bad|nofolder   the arm, one tick, the window, the flush
//
// Exit 0 when every check passes; the last line is "tokens: OK - <n> checks", like the other drivers here.

#include <windows.h>
#include <stdarg.h>
#include <stdio.h>
#include <string.h>

#include "../src/tokens.h"

static int PASSES = 0;
static int FAILS = 0;

static void ok(int cond, const char *what)
{
    if (cond)
    {
        PASSES++;
        printf("pass  %s\n", what);
    }
    else
    {
        FAILS++;
        printf("FAIL  %s\n", what);
    }
}

// --- the two things tokens.c asks of the DLL ---------------------------------------------------------

static wchar_t SELF_DIR[MAX_PATH];
static char LOGS_ALL[8][TOKENS_MAX + 64];
static int LOGS = 0;

#define LAST_LOG (LOGS_ALL[LOGS > 0 ? LOGS - 1 : 0])

void ch_self_dir(wchar_t *out, DWORD cch)
{
    wcsncpy_s(out, cch, SELF_DIR, _TRUNCATE);
}

void ch_logf(const char *fmt, ...)
{
    char body[TOKENS_MAX + 64];
    va_list ap;
    va_start(ap, fmt);
    _vsnprintf_s(body, sizeof(body), _TRUNCATE, fmt, ap);
    va_end(ap);
    strcpy_s(LOGS_ALL[LOGS < 8 ? LOGS : 7], sizeof(LOGS_ALL[0]), body);
    if (LOGS < 8)
    {
        LOGS++;
    }
    printf("      | %s\n", body);
}

// the fabricated dvar_t: the value pointer sits `TK_SLOT` bytes into it
static struct
{
    char pad[16];
    char *value;
} TK;

#define TK_SLOT 16L
static int REG_CALLS = 0;

static void *stub_reg(unsigned long long hash, const char *def, int flags, const char *desc)
{
    (void)hash;
    (void)flags;
    (void)desc;
    REG_CALLS++;
    TK.value = (char *)def; // what the engine would have created it holding
    return &TK;
}

// --- helpers ----------------------------------------------------------------------------------------

static void wide_path(wchar_t *out, DWORD cch, const wchar_t *dir, const wchar_t *rel)
{
    size_t n = wcslen(dir);
    if (n > 0 && (dir[n - 1] == L'\\' || dir[n - 1] == L'/'))
    {
        _snwprintf_s(out, cch, _TRUNCATE, L"%s%s", dir, rel);
    }
    else
    {
        _snwprintf_s(out, cch, _TRUNCATE, L"%s\\%s", dir, rel);
    }
}

static void make_dir(const wchar_t *dir, const wchar_t *rel)
{
    wchar_t path[MAX_PATH];
    wide_path(path, MAX_PATH, dir, rel);
    CreateDirectoryW(path, NULL); // already there is not an error
}

// a scratch folder beside the driver's own exe: the workspace is writable, a system temp folder may not be
static int scratch_dir(wchar_t *dir, DWORD cch)
{
    wchar_t exe[MAX_PATH];
    DWORD n = GetModuleFileNameW(NULL, exe, MAX_PATH);
    if (n == 0 || n >= MAX_PATH)
    {
        return 0;
    }
    wchar_t *slash = wcsrchr(exe, L'\\');
    if (slash == NULL)
    {
        return 0;
    }
    *(slash + 1) = L'\0';
    return _snwprintf_s(dir, cch, _TRUNCATE, L"%stokens_unit_%lu", exe, (unsigned long)GetCurrentProcessId()) >= 0;
}

static void write_ascii(const wchar_t *path, const char *text)
{
    HANDLE f = CreateFileW(path, GENERIC_WRITE, 0, NULL, CREATE_ALWAYS, FILE_ATTRIBUTE_NORMAL, NULL);
    DWORD wrote = 0;
    if (f != INVALID_HANDLE_VALUE)
    {
        WriteFile(f, text, (DWORD)strlen(text), &wrote, NULL);
        CloseHandle(f);
    }
}

static int read_ascii(const wchar_t *path, char *out, size_t cap)
{
    HANDLE f = CreateFileW(path, GENERIC_READ, FILE_SHARE_READ, NULL, OPEN_EXISTING, FILE_ATTRIBUTE_NORMAL, NULL);
    DWORD got = 0;
    if (f == INVALID_HANDLE_VALUE)
    {
        return -1;
    }
    BOOL ok = ReadFile(f, out, (DWORD)(cap - 1), &got, NULL);
    CloseHandle(f);
    if (!ok)
    {
        return -1;
    }
    out[got] = '\0';
    return (int)got;
}

static void fill(char *out, size_t n, char c)
{
    for (size_t i = 0; i < n; i++)
    {
        out[i] = c;
    }
    out[n] = '\0';
}

// --- self: the text, the read, the write -------------------------------------------------------------

static int self(void)
{
    wchar_t dir[MAX_PATH];
    wchar_t file[MAX_PATH];
    wchar_t tmp[MAX_PATH];
    char src[TOKENS_MAX + 8];
    char back[TOKENS_MAX + 8];
    const char *why = NULL;
    int rc = 0;

    if (!scratch_dir(dir, MAX_PATH))
    {
        printf("tokens: no scratch folder beside the driver\n");
        return 2;
    }
    CreateDirectoryW(dir, NULL);
    {
        size_t n = wcslen(dir);
        dir[n] = L'\\';
        dir[n + 1] = L'\0';
    }
    wide_path(file, MAX_PATH, dir, L"tokens.txt");
    wide_path(tmp, MAX_PATH, dir, L"tokens.txt.tmp");
    DeleteFileW(file);

    // ---- 1. the line's own form ---------------------------------------------------------------------
    ok(tokens_valid("p=0;w=0;n=0", strlen("p=0;w=0;n=0")) == 1, "form: the seed line passes");
    ok(tokens_valid("p=900;w=0;n=46", strlen("p=900;w=0;n=46")) == 1, "form: p/w/n passes");
    ok(tokens_valid("p=900;w=0;n=46;c=1,2,3,4,5,6,7,8", strlen("p=900;w=0;n=46;c=1,2,3,4,5,6,7,8")) == 1,
       "form: the c= counts pass");
    ok(tokens_valid("", 0) == 0, "form: an empty string fails");
    ok(tokens_valid("P=900;w=0;n=1", strlen("P=900;w=0;n=1")) == 0, "form: an uppercase letter fails");
    ok(tokens_valid("p=1; w=2;n=0", strlen("p=1; w=2;n=0")) == 0, "form: a space fails");
    ok(tokens_valid("p=-1;w=0;n=0", strlen("p=-1;w=0;n=0")) == 0, "form: a minus sign fails");
    ok(tokens_valid(NULL, 4) == 0, "form: a null string fails");
    fill(src, TOKENS_MAX, 'p');
    ok(tokens_valid(src, TOKENS_MAX) == 1, "form: exactly 512 chars passes");
    fill(src, TOKENS_MAX + 1, 'p');
    ok(tokens_valid(src, TOKENS_MAX + 1) == 0, "form: 513 chars fails");

    // ---- 2. the read --------------------------------------------------------------------------------
    strcpy_s(src, sizeof(src), "no such file");
    why = "";
    ok(tokens_read(file, src, sizeof(src), &why) == 0 && strcmp(src, "no such file") == 0,
       "read: a missing file is 0 and leaves the text alone");

    write_ascii(file, "p=900;w=0;n=46;c=1,2,3,4,5,6,7,8");
    why = "";
    rc = tokens_read(file, src, sizeof(src), &why);
    ok(rc == 1 && strcmp(src, "p=900;w=0;n=46;c=1,2,3,4,5,6,7,8") == 0, "read: a valid file comes back whole");

    write_ascii(file, "p=900;w=0;n=46\r\n");
    why = "";
    rc = tokens_read(file, src, sizeof(src), &why);
    ok(rc == 1 && strcmp(src, "p=900;w=0;n=46") == 0, "read: a trailing CRLF is not part of the line");

    write_ascii(file, "p=900;W=0\n");
    why = "";
    rc = tokens_read(file, src, sizeof(src), &why);
    ok(rc == -1 && why[0] != '\0' && strcmp(src, "p=900;w=0;n=46") == 0,
       "read: an uppercase letter is rejected and the text is left alone");

    write_ascii(file, "");
    why = "";
    ok(tokens_read(file, src, sizeof(src), &why) == -1 && strstr(why, "empty") != NULL,
       "read: an empty file is rejected");

    fill(back, TOKENS_MAX + 1, 'p');
    write_ascii(file, back);
    why = "";
    ok(tokens_read(file, src, sizeof(src), &why) == -1 && strstr(why, "512") != NULL,
       "read: 513 chars is rejected as too long");

    fill(back, TOKENS_MAX, 'p');
    write_ascii(file, back);
    why = "";
    ok(tokens_read(file, src, sizeof(src), &why) == 1 && strlen(src) == TOKENS_MAX,
       "read: exactly 512 chars is accepted");

    // ---- 3. the write -------------------------------------------------------------------------------
    DeleteFileW(file);
    ok(tokens_write(file, "p=1;w=2;n=3") == 0, "write: a valid line is written");
    ok(read_ascii(file, back, sizeof(back)) == 11 && strcmp(back, "p=1;w=2;n=3") == 0,
       "write: the file holds exactly the line, with no newline");
    ok(GetFileAttributesW(tmp) == INVALID_FILE_ATTRIBUTES, "write: no .tmp is left beside it");

    ok(tokens_write(file, "p=4;w=5;n=6") == 0, "write: a second line replaces the first");
    ok(tokens_read(file, src, sizeof(src), &why) == 1 && strcmp(src, "p=4;w=5;n=6") == 0,
       "write: the replaced file reads back as the new line");

    ok(tokens_write(file, "p=4;W=5") == -1, "write: a line outside the alphabet is refused");
    ok(tokens_read(file, src, sizeof(src), &why) == 1 && strcmp(src, "p=4;w=5;n=6") == 0,
       "write: a refused line leaves the file as it was");

    fill(back, TOKENS_MAX, 'p');
    ok(tokens_write(file, back) == 0 && read_ascii(file, src, sizeof(src)) == TOKENS_MAX,
       "write: 512 chars lands whole");

    // leave nothing behind: the folder was this driver's own
    DeleteFileW(file);
    DeleteFileW(tmp);
    {
        size_t n = wcslen(dir);
        if (n > 0 && dir[n - 1] == L'\\')
        {
            dir[n - 1] = L'\0';
        }
    }
    RemoveDirectoryW(dir);

    printf("tokens: %s - %d checks\n", FAILS == 0 ? "OK" : "FAILED", PASSES);
    return FAILS == 0 ? 0 : 1;
}

// --- arm: the arm, one tick, the window, the detach flush --------------------------------------------

static int arm_mode(const wchar_t *dir, const char *mode)
{
    wchar_t file[MAX_PATH];
    wchar_t sub[MAX_PATH];
    char back[TOKENS_MAX + 8];
    const char *expect = TOKENS_DEFAULT;

    // ch_self_dir hands back a directory with its separator, which is what tokens.c expects
    {
        size_t n = wcslen(dir);
        if (n > 0 && (dir[n - 1] == L'\\' || dir[n - 1] == L'/'))
        {
            wcsncpy_s(SELF_DIR, MAX_PATH, dir, _TRUNCATE);
        }
        else
        {
            _snwprintf_s(SELF_DIR, MAX_PATH, _TRUNCATE, L"%s\\", dir);
        }
    }
    wide_path(file, MAX_PATH, SELF_DIR, L"players\\tokens.txt");
    wide_path(sub, MAX_PATH, SELF_DIR, L"players");

    // "nofolder" is the one mode that leaves the client's own folder out: the unit must skip, not make it
    if (strcmp(mode, "nofolder") != 0)
    {
        make_dir(SELF_DIR, L"players");
    }
    if (strcmp(mode, "valid") == 0)
    {
        write_ascii(file, "p=900;w=0;n=46;c=1,2,3,4,5,6,7,8");
        expect = "p=900;w=0;n=46;c=1,2,3,4,5,6,7,8";
    }
    else if (strcmp(mode, "bad") == 0)
    {
        write_ascii(file, "p=900;W=0;n=46");
    }

    // ---- 4. the arm ---------------------------------------------------------------------------------
    ok(tokens_armed() == 0, "arm: nothing is armed before the client's register is offered");
    tokens_arm(stub_reg, NULL, TK_SLOT);
    ok(REG_CALLS == 1, "arm: the register is asked exactly once");
    ok(tokens_armed() == 1, "arm: the channel is armed once the call returned");
    if (strcmp(mode, "bad") == 0)
    {
        ok(LOGS == 2 && strncmp(LOGS_ALL[0], "tokens: file rejected: ", 23) == 0,
           "arm: a rejected file is said, with its reason");
    }
    else if (strcmp(mode, "nofolder") == 0)
    {
        ok(LOGS == 2 && strcmp(LOGS_ALL[0], "tokens: file rejected: no players folder") == 0,
           "arm: a missing players folder is said, and not made");
    }
    else if (strcmp(mode, "valid") == 0)
    {
        ok(LOGS == 2 && strcmp(LOGS_ALL[0], "tokens: file p=900;w=0;n=46;c=1,2,3,4,5,6,7,8") == 0,
           "arm: the file's own line is said first");
    }
    else
    {
        ok(LOGS == 2 && strcmp(LOGS_ALL[0], "tokens: file none") == 0, "arm: no file is said as none");
    }
    ok(TK.value != NULL && strcmp(TK.value, expect) == 0, "arm: the value slot holds the chosen line");
    if (strcmp(mode, "valid") == 0)
    {
        ok(strcmp(LAST_LOG, "tokens: registered pt_tokens_ch = p=900;w=0;n=46;c=1,2,3,4,5,6,7,8") == 0,
           "arm: a valid file's line reaches the dvar, unchanged");
    }
    else
    {
        ok(strcmp(LAST_LOG, "tokens: registered pt_tokens_ch = p=0;w=0;n=0") == 0,
           "arm: with no usable file the dvar holds the seed line");
    }
    if (strcmp(mode, "nofolder") == 0)
    {
        ok(GetFileAttributesW(sub) == INVALID_FILE_ATTRIBUTES, "arm: the missing folder is still missing");
    }
    else
    {
        ok(GetFileAttributesW(sub) != INVALID_FILE_ATTRIBUTES, "arm: the client's players folder is untouched");
    }

    // ---- 5. one tick writes, a second inside the second does not ------------------------------------
    if (strcmp(mode, "nofolder") == 0)
    {
        // the folder is the client's own: a save into it is skipped, said once, and nothing is created
        static char first[] = "p=5;w=6;n=7";
        static char last[] = "p=9;w=9;n=9";
        TK.value = first;
        tokens_tick();
        ok(strcmp(LAST_LOG, "tokens: save failed - p=5;w=6;n=7") == 0,
           "tick: a save with no players folder is skipped, and said");
        ok(GetFileAttributesW(file) == INVALID_FILE_ATTRIBUTES, "tick: and no file appears");
        ok(GetFileAttributesW(sub) == INVALID_FILE_ATTRIBUTES, "tick: and no folder appears");
        {
            int said = LOGS;
            TK.value = last;
            tokens_stop();
            ok(LOGS == said + 1 && strcmp(LAST_LOG, "tokens: save failed - p=9;w=9;n=9") == 0,
               "stop: the detach save is said, and skipped the same way");
        }
        printf("tokens: %s - %d checks\n", FAILS == 0 ? "OK" : "FAILED", PASSES);
        return FAILS == 0 ? 0 : 1;
    }

    {
        static char first[] = "p=5;w=6;n=7";
        static char moved[] = "p=4;w=6;n=8";
        TK.value = first;
        tokens_tick();
        ok(strcmp(LAST_LOG, "tokens: saved p=5;w=6;n=7") == 0, "tick: a moved value is written and said");
        ok(read_ascii(file, back, sizeof(back)) == 11 && strcmp(back, first) == 0, "tick: the file holds it");
        {
            int said = LOGS;
            TK.value = moved;
            tokens_tick();
            ok(LOGS == said && read_ascii(file, back, sizeof(back)) == 11 && strcmp(back, first) == 0,
               "tick: a second call inside the one-second window reads nothing");
            Sleep(1100);
            tokens_tick();
            ok(read_ascii(file, back, sizeof(back)) == 11 && strcmp(back, moved) == 0,
               "tick: one second later the new value is written");
            ok(LOGS == said, "tick: and the saved line stays inside the 30 s window");
        }
    }

    // ---- 6. a value a reader would reject is never written ------------------------------------------
    {
        static char junk[] = "P=4;w=6;n=8";
        int said = LOGS;
        TK.value = junk;
        tokens_stop();
        ok(LOGS == said, "stop: a value outside the alphabet is not written");
        ok(read_ascii(file, back, sizeof(back)) == 11 && strcmp(back, "p=4;w=6;n=8") == 0,
           "stop: the file is untouched by it");
    }

    // ---- 7. the detach flush, inside the log window -------------------------------------------------
    {
        static char last[] = "p=9;w=9;n=9";
        int said = LOGS;
        TK.value = last;
        tokens_stop();
        ok(LOGS == said + 1 && strcmp(LAST_LOG, "tokens: saved p=9;w=9;n=9") == 0,
           "stop: the detach save is said even inside the 30 s window");
        ok(read_ascii(file, back, sizeof(back)) == 11 && strcmp(back, last) == 0, "stop: and the file holds it");
    }

    printf("tokens: %s - %d checks\n", FAILS == 0 ? "OK" : "FAILED", PASSES);
    return FAILS == 0 ? 0 : 1;
}

int main(int argc, char **argv)
{
    if (argc >= 2 && strcmp(argv[1], "self") == 0)
    {
        return self();
    }
    if (argc >= 4 && strcmp(argv[1], "arm") == 0)
    {
        wchar_t dir[MAX_PATH];
        if (MultiByteToWideChar(CP_ACP, 0, argv[2], -1, dir, MAX_PATH) <= 0)
        {
            return 2;
        }
        return arm_mode(dir, argv[3]);
    }
    printf("usage: tokens_test.exe self | arm <dir> valid|none|bad|nofolder\n");
    return 2;
}
