// Offline driver for src\pick.c: the line form, the file read, the tmp-and-rename write, the queue walk out of a
// staged record array, and the arm / tick / stop path over a fabricated dvar. Links the SHIPPED unit; the client is
// never touched.
//
//   pick_test.exe self                       the text, the parse, the build, the read, the write, the queue
//   pick_test.exe arm <dir> valid|queue|none|bad|nofolder   the arm, the ticks, the flush
//   pick_test.exe arm <dir> advance          the pay's post, the swap, the save and the empty queue
//
// Exit 0 when every check passes; the last line is "pick: OK - <n> checks", like the other drivers here.

#include <windows.h>
#include <stdarg.h>
#include <stdio.h>
#include <string.h>

#include "../src/master.h"
#include "../src/pick.h"

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

// --- the two things pick.c asks of the DLL -----------------------------------------------------------

static wchar_t SELF_DIR[MAX_PATH];
static char LOGS_ALL[12][PICK_MAX + 64];
static int LOGS = 0;

#define LAST_LOG (LOGS_ALL[LOGS > 0 ? LOGS - 1 : 0])

void ch_self_dir(wchar_t *out, DWORD cch)
{
    wcsncpy_s(out, cch, SELF_DIR, _TRUNCATE);
}

void ch_logf(const char *fmt, ...)
{
    char body[PICK_MAX + 64];
    va_list ap;
    va_start(ap, fmt);
    _vsnprintf_s(body, sizeof(body), _TRUNCATE, fmt, ap);
    va_end(ap);
    strcpy_s(LOGS_ALL[LOGS < 12 ? LOGS : 11], sizeof(LOGS_ALL[0]), body);
    if (LOGS < 12)
    {
        LOGS++;
    }
    printf("      | %s\n", body);
}

// the fabricated dvar_t: the value pointer sits `PK_SLOT` bytes into it
static struct
{
    char pad[16];
    char *value;
} PKD;

#define PK_SLOT 16L
static int REG_CALLS = 0;

static void *stub_reg(unsigned long long hash, const char *def, int flags, const char *desc)
{
    (void)hash;
    (void)flags;
    (void)desc;
    REG_CALLS++;
    PKD.value = (char *)def; // what the engine would have created it holding
    return &PKD;
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
    return _snwprintf_s(dir, cch, _TRUNCATE, L"%spick_unit_%lu", exe, (unsigned long)GetCurrentProcessId()) >= 0;
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

// "a=1;q=" then n comma separated six digit ids, the worst case of this ladder
static size_t make_queue(char *out, size_t cap, int n)
{
    size_t at = (size_t)_snprintf_s(out, cap, _TRUNCATE, "a=1;q=");
    for (int i = 0; i < n; i++)
    {
        at += (size_t)_snprintf_s(out + at, cap - at, _TRUNCATE, i ? ",%d" : "%d", 100000 + i);
    }
    return at;
}

// --- self: the text, the parse, the build, the read, the write, the queue -----------------------------

static unsigned char RECS[6 * MASTER_STRIDE];

static void put_rec(int i, unsigned long long id, int kind, int trigs, unsigned trig, int tiers, unsigned top,
                    long long xp, int status)
{
    unsigned char *r = RECS + (size_t)i * MASTER_STRIDE;
    memset(r, 0, MASTER_STRIDE);
    *(unsigned long long *)r = id;
    *(int *)(r + MASTER_REC_KIND) = kind;
    *(int *)(r + 0x490) = trigs;
    *(unsigned *)(r + 0x480) = trig;
    *(int *)(r + MASTER_REC_COUNT) = tiers;
    if (tiers > 0)
    {
        *(unsigned *)(r + MASTER_REC_THR) = top;
    }
    *(long long *)(r + MASTER_REC_XP) = xp;
    r[0x56D] = (unsigned char)status;
}

static int self(void)
{
    wchar_t dir[MAX_PATH];
    wchar_t file[MAX_PATH];
    wchar_t tmp[MAX_PATH];
    char src[PICK_MAX + 8];
    char back[PICK_MAX + 8];
    char out[PICK_MAX + 8];
    int q[PICK_Q_MAX];
    int a = -1;
    int qn = -7;
    const char *why = NULL;
    int rc = 0;

    if (!scratch_dir(dir, MAX_PATH))
    {
        printf("pick: no scratch folder beside the driver\n");
        return 2;
    }
    CreateDirectoryW(dir, NULL);
    {
        size_t n = wcslen(dir);
        dir[n] = L'\\';
        dir[n + 1] = L'\0';
    }
    wide_path(file, MAX_PATH, dir, L"pt_armory.txt");
    wide_path(tmp, MAX_PATH, dir, L"pt_armory.txt.tmp");
    DeleteFileW(file);

    // ---- 1. the line's own form ---------------------------------------------------------------------
    ok(pick_valid("a=0", 3) == 1, "form: the seed line passes");
    ok(pick_valid("a=75680", 7) == 1, "form: one row passes");
    ok(pick_valid("a=75680;q=69316,69318", strlen("a=75680;q=69316,69318")) == 1, "form: a row and its queue passes");
    ok(pick_valid("", 0) == 0, "form: an empty string fails");
    ok(pick_valid("a=75680;Q=1", 12) == 0, "form: an uppercase letter fails");
    ok(pick_valid("a=75680; q=1", 13) == 0, "form: a space fails");
    ok(pick_valid("a=-1", 4) == 0, "form: a minus sign fails");
    ok(pick_valid(NULL, 4) == 0, "form: a null string fails");
    fill(src, PICK_MAX, 'a');
    ok(pick_valid(src, PICK_MAX) == 1, "form: exactly 1024 chars passes");
    fill(src, PICK_MAX + 1, 'a');
    ok(pick_valid(src, PICK_MAX + 1) == 0, "form: 1025 chars fails");

    // ---- 2. the parse -------------------------------------------------------------------------------
    a = -1;
    qn = -7;
    ok(pick_parse("a=0", 3, &a, q, PICK_Q_MAX, &qn) == 1 && a == 0 && qn == -1,
       "parse: a=0 is no row and no queue");
    a = -1;
    qn = -7;
    ok(pick_parse("a=75680", 7, &a, q, PICK_Q_MAX, &qn) == 1 && a == 75680 && qn == -1,
       "parse: one row and no queue");
    a = -1;
    qn = -7;
    ok(pick_parse("a=75680;q=69316,69318", strlen("a=75680;q=69316,69318"), &a, q, PICK_Q_MAX, &qn) == 1 && a == 75680 && qn == 2
           && q[0] == 69316 && q[1] == 69318,
       "parse: the queue comes back in the line's own order");
    {
        size_t n = make_queue(src, sizeof(src), 76);
        a = -1;
        qn = -7;
        ok(pick_parse(src, n, &a, q, PICK_Q_MAX, &qn) == 1 && qn == 76,
           "parse: the 76 id worst case fits");
    }
    {
        size_t n = make_queue(src, sizeof(src), PICK_Q_MAX + 1);
        a = -1;
        qn = -7;
        ok(pick_parse(src, n, &a, q, PICK_Q_MAX, &qn) == 0, "parse: a queue longer than the buffer is refused whole");
    }
    {
        static const char *const bad[] = {"a=", "a", "b=1", "a=1;q=", "a=1;q=1,", "a=1;q=,1", "a=1;q=1;", "a=1;x=2",
                                          "a=1;q=1,,2", "a=2147483648"};
        int all = 0;
        for (int i = 0; i < (int)(sizeof(bad) / sizeof(bad[0])); i++)
        {
            a = -1;
            qn = -7;
            if (pick_parse(bad[i], strlen(bad[i]), &a, q, PICK_Q_MAX, &qn) == 0)
            {
                all++;
            }
        }
        ok(all == (int)(sizeof(bad) / sizeof(bad[0])), "parse: a malformed line is refused");
    }

    // ---- 3. the build -------------------------------------------------------------------------------
    ok(pick_build(out, sizeof(out), 0, NULL, 0) == 0 && strcmp(out, "a=0") == 0, "build: nothing is a=0");
    ok(pick_build(out, sizeof(out), 75680, NULL, 0) == 0 && strcmp(out, "a=75680") == 0,
       "build: one row with no queue");
    {
        static const int two[] = {69316, 69318};
        ok(pick_build(out, sizeof(out), 75680, two, 2) == 0 && strcmp(out, "a=75680;q=69316,69318") == 0,
           "build: the queue is comma separated after a semicolon");
    }
    {
        int many[76];
        for (int i = 0; i < 76; i++)
        {
            many[i] = 100000 + i;
        }
        ok(pick_build(out, sizeof(out), 75680, many, 76) == 0 && strlen(out) < PICK_MAX
               && pick_valid(out, strlen(out)) == 1,
           "build: the 76 id queue fits inside 1024");
        ok(pick_build(out, 40, 75680, many, 76) == -1, "build: a line that would not fit is refused");
    }
    ok(pick_build(out, sizeof(out), -1, NULL, 0) == -1, "build: a negative row is refused");

    // ---- 4. the read --------------------------------------------------------------------------------
    strcpy_s(src, sizeof(src), "no such file");
    why = "";
    ok(pick_read(file, src, sizeof(src), &why) == 0 && strcmp(src, "no such file") == 0,
       "read: a missing file is 0 and leaves the text alone");

    write_ascii(file, "a=75680;q=69316,69318");
    why = "";
    rc = pick_read(file, src, sizeof(src), &why);
    ok(rc == 1 && strcmp(src, "a=75680;q=69316,69318") == 0, "read: a valid file comes back whole");

    write_ascii(file, "a=75680\r\n");
    why = "";
    rc = pick_read(file, src, sizeof(src), &why);
    ok(rc == 1 && strcmp(src, "a=75680") == 0, "read: a trailing CRLF is not part of the line");

    write_ascii(file, "a=75680;Q=1\n");
    why = "";
    rc = pick_read(file, src, sizeof(src), &why);
    ok(rc == -1 && why[0] != '\0' && strcmp(src, "a=75680") == 0,
       "read: an uppercase letter is rejected and the text is left alone");

    write_ascii(file, "");
    why = "";
    ok(pick_read(file, src, sizeof(src), &why) == -1 && strstr(why, "empty") != NULL,
       "read: an empty file is rejected");

    fill(back, PICK_MAX + 1, 'a');
    write_ascii(file, back);
    why = "";
    ok(pick_read(file, src, sizeof(src), &why) == -1 && strstr(why, "1024") != NULL,
       "read: 1025 chars is rejected as too long");

    fill(back, PICK_MAX, 'a');
    write_ascii(file, back);
    why = "";
    ok(pick_read(file, src, sizeof(src), &why) == 1 && strlen(src) == PICK_MAX,
       "read: exactly 1024 chars is accepted");

    // ---- 5. the write -------------------------------------------------------------------------------
    DeleteFileW(file);
    ok(pick_write(file, "a=1;q=2,3") == 0, "write: a valid line is written");
    ok(read_ascii(file, back, sizeof(back)) == 9 && strcmp(back, "a=1;q=2,3") == 0,
       "write: the file holds exactly the line, with no newline");
    ok(GetFileAttributesW(tmp) == INVALID_FILE_ATTRIBUTES, "write: no .tmp is left beside it");

    ok(pick_write(file, "a=4") == 0, "write: a second line replaces the first");
    ok(pick_read(file, src, sizeof(src), &why) == 1 && strcmp(src, "a=4") == 0,
       "write: the replaced file reads back as the new line");

    ok(pick_write(file, "a=4;Q=5") == -1, "write: a line outside the alphabet is refused");
    ok(pick_read(file, src, sizeof(src), &why) == 1 && strcmp(src, "a=4") == 0,
       "write: a refused line leaves the file as it was");

    fill(back, PICK_MAX, 'a');
    ok(pick_write(file, back) == 0 && read_ascii(file, src, sizeof(src)) == PICK_MAX,
       "write: 1024 chars lands whole");

    // ---- 6. the queue out of a staged record array ---------------------------------------------------
    put_rec(0, 75680, 368, 1, 200001, 1, 150000, 0, 0);  // ours: queued
    put_rec(1, 69316, 368, 1, 200076, 1, 150000, 0, 0);  // ours, the last trigger: queued
    put_rec(2, 69318, 368, 1, 200077, 1, 150000, 0, 0);  // one past the ladder: not ours
    put_rec(3, 69320, 398, 1, 200010, 1, 150000, 0, 0);  // a weapon row: not ours
    put_rec(4, 69322, 368, 0, 200011, 1, 150000, 0, 0);  // no trigger: not ours
    {
        int got = pick_queue_native(RECS, 6, q, PICK_Q_MAX);
        ok(got == 2 && q[0] == 75680 && q[1] == 69316, "queue: only the 76 rows, in the array's own order");
        ok(pick_queue_native(RECS, 6, q, 1) == 1, "queue: a short buffer takes what fits");
        ok(pick_queue_native(NULL, 6, q, PICK_Q_MAX) == 0 && pick_queue_native(RECS, 0, q, PICK_Q_MAX) == 0,
           "queue: no array is no queue");
    }

    // ---- 7. the row's own answer ---------------------------------------------------------------------
    put_rec(0, 75680, 368, 1, 200001, 1, 150000, 150000, 1); // xp at the top, status 1
    put_rec(1, 69316, 368, 1, 200076, 1, 150000, 10, 3);     // status 3
    put_rec(2, 69318, 368, 1, 200077, 1, 150000, 10, 0);     // still owed
    put_rec(3, 69320, 368, 1, 200010, 0, 0, 10, 0);          // no threshold
    ok(pick_row_state(RECS, 4, 75680) == 1, "row: xp at the top threshold is complete");
    ok(pick_row_state(RECS, 4, 69316) == 1, "row: the client's own status 3 is complete");
    ok(pick_row_state(RECS, 4, 69318) == 0, "row: below the top is still owed");
    ok(pick_row_state(RECS, 4, 69320) == 0, "row: no threshold is never complete here");
    ok(pick_row_state(RECS, 4, 12345) == -1, "row: an id that is not in the array is -1");
    ok(pick_row_state(NULL, 4, 75680) == -1, "row: no array is -1");

    // ---- 8. the walk to the next id the advance takes -------------------------------------------------
    {
        // row 0 is complete by its xp, row 1 by the client's status, row 2 is still owed, 12345 is not held
        int qq[4];
        qq[0] = 75680;
        qq[1] = 69316;
        qq[2] = 69318;
        qq[3] = 12345;
        ok(pick_next(RECS, 4, 0, qq, 4) == 69318,
           "next: complete rows and ids the array does not hold are skipped");
        ok(pick_next(RECS, 4, 69318, qq, 4) == 0, "next: nothing else is owed so the walk ends");
        ok(pick_next(NULL, 0, 0, qq, 4) == 75680, "next: with no array the first id that is not the done one");
        ok(pick_next(NULL, 0, 75680, qq, 4) == 69316, "next: the done row is skipped without the array too");
        ok(pick_next(RECS, 4, 0, NULL, 0) == 0 && pick_next(RECS, 4, 0, qq, 0) == 0,
           "next: no queue is no next");
    }

    // ---- 9. the kill switch's own path ---------------------------------------------------------------
    {
        wchar_t off[MAX_PATH];
        wchar_t sub[MAX_PATH];
        wide_path(off, MAX_PATH, dir, L"progression-tuning\\armory_off.txt");
        wide_path(sub, MAX_PATH, dir, L"progression-tuning");
        ok(pick_off_present(dir) == 0, "switch: absent in a directory with no switch of its own");
        CreateDirectoryW(sub, NULL);
        write_ascii(off, "");
        ok(pick_off_present(dir) == 1, "switch: present when its file is there");
        DeleteFileW(off);
        RemoveDirectoryW(sub);
    }

    // leave nothing behind: the folder was this driver's own
    DeleteFileW(file);
    DeleteFileW(tmp);
    {
        wchar_t sub[MAX_PATH];
        wide_path(sub, MAX_PATH, dir, L"progression-tuning");
        RemoveDirectoryW(sub);
        size_t n = wcslen(dir);
        if (n > 0 && dir[n - 1] == L'\\')
        {
            dir[n - 1] = L'\0';
        }
    }
    RemoveDirectoryW(dir);

    printf("pick: %s - %d checks\n", FAILS == 0 ? "OK" : "FAILED", PASSES);
    return FAILS == 0 ? 0 : 1;
}

// --- arm: the arm, the ticks, the flush --------------------------------------------------------------

static int line_is(const char *want)
{
    return strcmp(LAST_LOG, want) == 0;
}

static int arm_mode(const wchar_t *dir, const char *mode)
{
    wchar_t file[MAX_PATH];
    wchar_t sub[MAX_PATH];
    char back[PICK_MAX + 8];
    char want[PICK_MAX + 64];
    int q[PICK_Q_MAX];
    const char *file_line = NULL;
    const char *merged = NULL;
    const int queued = (strcmp(mode, "queue") == 0);

    // ch_self_dir hands back a directory with its separator, which is what pick.c expects
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
    wide_path(file, MAX_PATH, SELF_DIR, L"players\\pt_armory.txt");
    wide_path(sub, MAX_PATH, SELF_DIR, L"players");

    // "nofolder" is the one mode that leaves the client's own folder out: the unit must skip, not make it
    if (strcmp(mode, "nofolder") != 0)
    {
        make_dir(SELF_DIR, L"players");
    }
    if (strcmp(mode, "valid") == 0)
    {
        write_ascii(file, "a=75680");
        file_line = "a=75680";
    }
    else if (queued)
    {
        write_ascii(file, "a=75680;q=69316,69318");
        file_line = "a=75680;q=69316,69318";
    }
    else if (strcmp(mode, "bad") == 0)
    {
        write_ascii(file, "a=75680;Q=1");
    }

    // ---- 9. the arm ---------------------------------------------------------------------------------
    ok(pick_armed() == 0, "arm: nothing is armed before the client's register is offered");
    ok(pick_active() == 0, "arm: no row is active before the arm");
    pick_arm(stub_reg, NULL, PK_SLOT);
    ok(REG_CALLS == 1, "arm: the register is asked exactly once");
    ok(pick_armed() == 1, "arm: the channel is armed once the call returned");
    if (strcmp(mode, "bad") == 0)
    {
        ok(LOGS == 2 && strncmp(LOGS_ALL[0], "pick: file rejected: ", 21) == 0,
           "arm: a rejected file is said, with its reason");
    }
    else if (strcmp(mode, "nofolder") == 0)
    {
        ok(LOGS == 2 && strcmp(LOGS_ALL[0], "pick: file rejected: no players folder") == 0,
           "arm: a missing players folder is said, and not made");
    }
    else if (file_line != NULL)
    {
        _snprintf_s(want, sizeof(want), _TRUNCATE, "pick: file %s", file_line);
        ok(LOGS == 2 && strcmp(LOGS_ALL[0], want) == 0, "arm: the file's own line is said first");
    }
    else
    {
        ok(LOGS == 2 && strcmp(LOGS_ALL[0], "pick: file none") == 0, "arm: no file is said as none");
    }
    ok(PKD.value != NULL && strcmp(PKD.value, file_line != NULL ? file_line : PICK_DEFAULT) == 0,
       "arm: the value slot holds the chosen line");
    _snprintf_s(want, sizeof(want), _TRUNCATE, "pick: registered %s = %s", PICK_NAME,
                file_line != NULL ? file_line : PICK_DEFAULT);
    ok(line_is(want), "arm: the registered line names the dvar and its value");
    if (queued)
    {
        ok(pick_active() == 75680 && pick_queue(q, PICK_Q_MAX) == 2 && q[0] == 69316 && q[1] == 69318,
           "arm: the file's row and queue are adopted");
    }
    else
    {
        ok(pick_active() == (file_line != NULL ? 75680 : 0) && pick_queue(q, PICK_Q_MAX) == 0,
           "arm: the file's row is adopted and there is no queue yet");
    }
    if (strcmp(mode, "nofolder") == 0)
    {
        ok(GetFileAttributesW(sub) == INVALID_FILE_ATTRIBUTES, "arm: the missing folder is still missing");
    }
    else
    {
        ok(GetFileAttributesW(sub) != INVALID_FILE_ATTRIBUTES, "arm: the client's players folder is untouched");
    }

    // ---- 10. one tick adopts a press, a second inside the second does not ---------------------------
    if (strcmp(mode, "nofolder") == 0)
    {
        // the folder is the client's own: a save into it is skipped, said once, and nothing is created
        static char first[] = "a=5";
        static char last[] = "a=9";
        PKD.value = first;
        pick_tick();
        ok(strcmp(LAST_LOG, "pick: save failed - a=5") == 0,
           "tick: a save with no players folder is skipped, and said");
        ok(GetFileAttributesW(file) == INVALID_FILE_ATTRIBUTES, "tick: and no file appears");
        ok(GetFileAttributesW(sub) == INVALID_FILE_ATTRIBUTES, "tick: and no folder appears");
        {
            int said = LOGS;
            PKD.value = last;
            pick_stop();
            ok(LOGS == said + 1 && strcmp(LAST_LOG, "pick: save failed - a=9") == 0,
               "stop: the detach save is said, and skipped the same way");
        }
        printf("pick: %s - %d checks\n", FAILS == 0 ? "OK" : "FAILED", PASSES);
        return FAILS == 0 ? 0 : 1;
    }

    {
        static char press[] = "a=69318";
        int said = LOGS;
        PKD.value = press;
        pick_tick();
        ok(pick_active() == 69318, "tick: the row the press named becomes the active one");
        ok(LOGS == said + 2 && strcmp(LOGS_ALL[said], "armory: pick a=69318") == 0,
           "tick: the press is one armory line and then the save");
        merged = queued ? "a=69318;q=69316,69318" : "a=69318";
        ok(read_ascii(file, back, sizeof(back)) > 0 && strcmp(back, merged) == 0,
           "tick: the file holds the press and keeps the queue it already had");
        {
            int lines = LOGS;
            static char second[] = "a=69320";
            PKD.value = second;
            pick_tick();
            ok(LOGS == lines && pick_active() == 69318 && read_ascii(file, back, sizeof(back)) > 0
                   && strcmp(back, merged) == 0,
               "tick: a second call inside the one-second window reads nothing");
            Sleep(1100);
            pick_tick();
            merged = queued ? "a=69320;q=69316,69318" : "a=69320";
            ok(pick_active() == 69320 && read_ascii(file, back, sizeof(back)) > 0 && strcmp(back, merged) == 0,
               "tick: one second later the new row is adopted and written");
        }
    }

    // ---- 11. a value a reader would reject is never written -----------------------------------------
    {
        static char junk[] = "a=4;Q=6";
        static char good[] = "a=7";
        char stop_line[PICK_MAX + 64];
        char stop_file[PICK_MAX + 8];
        int said = LOGS;
        PKD.value = junk;
        Sleep(1100);
        pick_tick();
        ok(LOGS == said + 1 && strcmp(LAST_LOG, "pick: refused a line a reader would not take") == 0,
           "tick: a value outside the alphabet is refused and said once");
        Sleep(1100);
        pick_tick();
        ok(LOGS == said + 1, "tick: and the refusal is not said again");
        ok(read_ascii(file, back, sizeof(back)) > 0 && strcmp(back, merged) == 0,
           "tick: the file is untouched by it");
        PKD.value = good;
        pick_stop();
        _snprintf_s(stop_line, sizeof(stop_line), _TRUNCATE, "pick: saved a=7%s",
                    queued ? ";q=69316,69318" : "");
        _snprintf_s(stop_file, sizeof(stop_file), _TRUNCATE, "a=7%s", queued ? ";q=69316,69318" : "");
        ok(line_is(stop_line), "stop: the detach save is said even inside the window");
        ok(read_ascii(file, back, sizeof(back)) == (int)strlen(stop_file) && strcmp(back, stop_file) == 0,
           "stop: and the file holds it, with the queue it already had");
    }

    printf("pick: %s - %d checks\n", FAILS == 0 ? "OK" : "FAILED", PASSES);
    return FAILS == 0 ? 0 : 1;
}

// --- advance: the pay's post, the tick's swap, and the queue that ends --------------------------------

static void set_self_dir(const wchar_t *dir)
{
    // ch_self_dir hands back a directory with its separator, which is what pick.c expects
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

static int advance_mode(const wchar_t *dir)
{
    wchar_t file[MAX_PATH];
    char back[PICK_MAX + 8];
    int q[PICK_Q_MAX];
    int said = 0;

    set_self_dir(dir);
    make_dir(SELF_DIR, L"players");
    wide_path(file, MAX_PATH, SELF_DIR, L"players\\pt_armory.txt");
    write_ascii(file, "a=75680;q=69316,69318");

    // ---- 13. the arm takes the file's row and its queue ----------------------------------------------
    pick_arm(stub_reg, NULL, PK_SLOT);
    ok(pick_armed() == 1 && pick_active() == 75680 && pick_queue(q, PICK_Q_MAX) == 2 && q[0] == 69316
           && q[1] == 69318,
       "advance: the file's row is active and its queue adopted");

    // ---- 14. one post, one swap, one line and one save -----------------------------------------------
    said = LOGS;
    pick_request_advance(75680);
    pick_tick();
    ok(pick_active() == 69316, "advance: the tick moves the pick to the next id in the queue");
    ok(line_is("armory: advance 75680 -> 69316"), "advance: one line names the row it left and the row it took");
    ok(PKD.value != NULL && strcmp(PKD.value, "a=69316;q=69316,69318") == 0,
       "advance: the merged line is pushed into the dvar");
    ok(read_ascii(file, back, sizeof(back)) > 0 && strcmp(back, "a=69316;q=69316,69318") == 0,
       "advance: and the file holds it");
    ok(LOGS == said + 2, "advance: one post is one line and one save");

    said = LOGS;
    pick_tick();
    ok(LOGS == said && pick_active() == 69316, "advance: a tick with no post advances nothing");

    pick_request_advance(69316);
    pick_tick();
    ok(pick_active() == 69318, "advance: the next completion moves the pick on again");
    ok(line_is("armory: advance 69316 -> 69318"), "advance: and says so with both ids");

    // ---- 15. the queue the lua writes is adopted, and its end leaves no row --------------------------
    {
        static char last[] = "a=69318;q=69318";
        PKD.value = last;
        Sleep(1100);
        pick_tick();
        ok(pick_active() == 69318 && pick_queue(q, PICK_Q_MAX) == 1 && q[0] == 69318,
           "advance: a queue written through the dvar is adopted whole");
    }
    said = LOGS;
    pick_request_advance(69318);
    pick_tick();
    ok(pick_active() == 0, "advance: an empty queue leaves no row active");
    ok(line_is("armory: queue done"), "advance: and says the queue is done");
    ok(read_ascii(file, back, sizeof(back)) > 0 && strcmp(back, "a=0;q=69318") == 0,
       "advance: the file holds the empty pick with the queue it had");
    ok(PKD.value != NULL && strcmp(PKD.value, "a=0;q=69318") == 0, "advance: and the dvar carries the same line");
    ok(LOGS == said + 2, "advance: the empty case is one line and one save too");

    said = LOGS;
    pick_request_advance(69318);
    pick_tick();
    ok(LOGS == said && pick_active() == 0, "advance: the queue-done line is said once, not once a post");

    said = LOGS;
    pick_request_advance(0);
    pick_tick();
    ok(LOGS == said && pick_active() == 0, "advance: a zero request posts nothing");

    // ---- 16. a press still wins after the queue ended -------------------------------------------------
    {
        static char press[] = "a=69318";
        PKD.value = press;
        Sleep(1100);
        pick_tick();
        ok(pick_active() == 69318 && read_ascii(file, back, sizeof(back)) > 0
               && strcmp(back, "a=69318;q=69318") == 0,
           "advance: a press after the empty queue wins on the next tick");
    }

    printf("pick: %s - %d checks\n", FAILS == 0 ? "OK" : "FAILED", PASSES);
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
        if (strcmp(argv[3], "advance") == 0)
        {
            return advance_mode(dir);
        }
        return arm_mode(dir, argv[3]);
    }
    printf("usage: pick_test.exe self | arm <dir> valid|queue|advance|none|bad|nofolder\n");
    return 2;
}
