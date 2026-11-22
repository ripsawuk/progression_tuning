// offline driver for src research c
//
//   research_test.exe self   the line the build the file the arm and the tick
//   research_test.exe pay    the row walk the gates the hold the credit and the log
//   research_test.exe off <dir>  1 when <dir>\progression-tuning\research_pay_off.txt is there
//
// links the shipped units the game is never touched
// exit 0 when every check passes the last line is research ok n checks

#include <windows.h>
#include <stdarg.h>
#include <stdio.h>
#include <string.h>
#include <wchar.h>

#include "../src/research.h"
#include "../src/armory.h"
#include "../src/master.h"

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

// the one thing research c asks of the dll
static char LOGS_ALL[64][256];
static int LOGS = 0;

#define LAST_LOG (LOGS_ALL[LOGS > 0 ? LOGS - 1 : 0])

void ch_logf(const char *fmt, ...)
{
    char body[256];
    va_list ap;
    va_start(ap, fmt);
    _vsnprintf_s(body, sizeof(body), _TRUNCATE, fmt, ap);
    va_end(ap);
    strcpy_s(LOGS_ALL[LOGS < 64 ? LOGS : 63], sizeof(LOGS_ALL[0]), body);
    if (LOGS < 64)
    {
        LOGS++;
    }
    printf("      | %s\n", body);
}

// the staged dll directory
static wchar_t DIR[MAX_PATH];

void ch_self_dir(wchar_t *out, DWORD cch)
{
    wcscpy_s(out, cch, DIR);
}

// the pick channel armory c links against
int pick_active(void)
{
    return 0;
}

int pick_unlocked(void)
{
    return 0;
}

void pick_request_advance(int done_id)
{
    (void)done_id;
}

// --- the staged directory and its file ---------------------------------------------------------------

static int stage_dir(void)
{
    wchar_t exe[MAX_PATH];
    wchar_t root[MAX_PATH];
    wchar_t players[MAX_PATH];
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
    // beside the driver so the run needs no writable temp
    if (_snwprintf_s(root, MAX_PATH, _TRUNCATE, L"%sstage", exe) < 0)
    {
        return 0;
    }
    CreateDirectoryW(root, NULL);
    if (_snwprintf_s(players, MAX_PATH, _TRUNCATE, L"%s\\players", root) < 0)
    {
        return 0;
    }
    CreateDirectoryW(players, NULL);
    DWORD a = GetFileAttributesW(players);
    if (a == INVALID_FILE_ATTRIBUTES || (a & FILE_ATTRIBUTE_DIRECTORY) == 0)
    {
        return 0;
    }
    // the dll directory as the hook sees it ends with a backslash
    return _snwprintf_s(DIR, MAX_PATH, _TRUNCATE, L"%s\\", root) >= 0;
}

static int file_path(wchar_t *out)
{
    return _snwprintf_s(out, MAX_PATH, _TRUNCATE, L"%splayers\\research.txt", DIR) >= 0;
}

// the raw text into the file no line ending added
static int put_raw(const wchar_t *path, const char *text)
{
    HANDLE f = CreateFileW(path, GENERIC_WRITE, 0, NULL, CREATE_ALWAYS, FILE_ATTRIBUTE_NORMAL, NULL);
    if (f == INVALID_HANDLE_VALUE)
    {
        return -1;
    }
    DWORD wrote = 0;
    size_t n = strlen(text);
    BOOL ok = WriteFile(f, text, (DWORD)n, &wrote, NULL);
    CloseHandle(f);
    return (ok && wrote == (DWORD)n) ? 0 : -1;
}

// --- the dvar the game would have made ---------------------------------------------------------------

static struct
{
    char pad[16];
    char *value;
} DV[4];

#define RES_SLOT 16L

static int REG_CALLS = 0;

static const unsigned char SALT[16] = { 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16 };

static void *stub_reg(unsigned long long hash, const char *def, int flags, const char *desc)
{
    (void)hash;
    (void)flags;
    (void)desc;
    int i = REG_CALLS < 4 ? REG_CALLS : 3;
    REG_CALLS++;
    DV[i].value = (char *)def;
    return &DV[i];
}

// --- the grammar -------------------------------------------------------------------------------------

static int parses(const char *text, int want)
{
    int a = -1;
    if (res_parse(text, strlen(text), &a) == 0)
    {
        return 0;
    }
    return a == want;
}

static int refuses(const char *text)
{
    int a = -1;
    return res_parse(text, strlen(text), &a) == 0;
}

static int builds(int id, const char *want)
{
    char out[RESEARCH_MAX + 1];
    if (res_build(out, sizeof(out), id) != 0)
    {
        return 0;
    }
    return strcmp(out, want) == 0;
}

static int self_mode(void)
{
    LOGS = 0;
    if (!stage_dir())
    {
        printf("research: FAILED - no temp directory\n");
        return 1;
    }
    // a switch left by an earlier run would arm the pay off
    {
        wchar_t tmp[MAX_PATH];
        wchar_t path[MAX_PATH];
        DWORD n = GetTempPathW(MAX_PATH, tmp);
        if (n > 0 && n < MAX_PATH && _snwprintf_s(path, MAX_PATH, _TRUNCATE,
                                                  L"%sprogression-tuning\\research_pay_off.txt", tmp) >= 0)
        {
            DeleteFileW(path);
        }
    }

    // ---- 1. the line ------------------------------------------------------------------------------
    ok(res_valid("a=55571", 7) == 1 && res_valid("a=0", 3) == 1,
       "line: a= and a decimal id is the whole text");
    ok(res_valid("A=55571", 7) == 0 && res_valid("a=1;", 4) == 0 && res_valid("a=1 ", 4) == 0
           && res_valid("a=1,u=2", 7) == 0,
       "line: an upper case a semicolon a space and a comma are all refused");
    ok(res_valid("", 0) == 0 && res_valid("aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa", 33) == 0,
       "line: nothing and a line past 32 chars are refused");
    ok(parses("a=55571", 55571) && parses("a=0", 0) && parses("a=2147483647", 2147483647),
       "line: the id reads out of a= and a=0 is none");
    ok(refuses("a=") && refuses("a") && refuses("b=1") && refuses("a=1=2") && refuses("a=-1"),
       "line: no digits a wrong key a second = and a sign are all refused");
    ok(refuses("a=2147483648") && refuses("a=55571x"),
       "line: an id past 32 bits and a letter after the digits are refused");
    ok(builds(55571, "a=55571") && builds(0, "a=0"),
       "line: the built text is a= then the id");
    {
        char tiny[4];
        ok(res_build(tiny, sizeof(tiny), 55571) != 0, "line: a buffer that cannot hold it is refused");
    }

    // ---- 2. the file ------------------------------------------------------------------------------
    {
        wchar_t path[MAX_PATH];
        char out[RESEARCH_MAX + 1];
        const char *why = "";
        ok(file_path(path) && put_raw(path, "a=55571\n") == 0 && res_read(path, out, sizeof(out), &why) == 1
               && strcmp(out, "a=55571") == 0,
           "file: a line and its ending read back as the line");
        ok(put_raw(path, "a=55571\r\n") == 0 && res_read(path, out, sizeof(out), &why) == 1
               && strcmp(out, "a=55571") == 0,
           "file: a crlf is stripped the same way");
        ok(put_raw(path, "") == 0 && res_read(path, out, sizeof(out), &why) == -1,
           "file: an empty file is a refusal not a missing one");
        ok(put_raw(path, "A=1\n") == 0 && res_read(path, out, sizeof(out), &why) == -1,
           "file: a line outside the charset is refused");
        ok(put_raw(path, "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa\n") == 0
               && res_read(path, out, sizeof(out), &why) == -1,
           "file: a line past 32 chars is refused");
        DeleteFileW(path);
        ok(res_read(path, out, sizeof(out), &why) == 0, "file: no file is a miss not a refusal");
        ok(res_write(path, "a=1;") != 0, "file: a line this unit would refuse is never written");
        ok(res_write(path, "a=55572") == 0 && res_read(path, out, sizeof(out), &why) == 1
               && strcmp(out, "a=55572") == 0,
           "file: a write lands and reads back");
        {
            wchar_t tmp[MAX_PATH];
            _snwprintf_s(tmp, MAX_PATH, _TRUNCATE, L"%s.tmp", path);
            ok(GetFileAttributesW(tmp) == INVALID_FILE_ATTRIBUTES, "file: the tmp is renamed away");
        }
    }

    // ---- 3. the arm from the file -----------------------------------------------------------------
    {
        wchar_t path[MAX_PATH];
        file_path(path);
        put_raw(path, "a=55571\n");
        REG_CALLS = 0;
        research_arm(stub_reg, SALT, RES_SLOT);
        ok(research_armed() == 1 && research_active() == 55571,
           "arm: the file line is the dvar default and the active row");
        ok(LOGS == 1 && strcmp(LAST_LOG, "research: armed a=55571 (file)") == 0,
           "arm: one line names the id and the file");
        ok(REG_CALLS == 4, "arm: the channel the feed and the two unlock dvars are asked for");
        ok(strcmp(DV[1].value, ARMORY_DEFAULT) == 0, "arm: the feed dvar is the armory one untouched");
        ok(strcmp(DV[2].value, "0") == 0 && strcmp(DV[3].value, "0") == 0,
           "arm: both unlock dvars are asked for with the game own default");

        // ---- 4. the tick --------------------------------------------------------------------------
        Sleep(1050);
        research_tick();
        ok(LOGS == 1, "tick: the same line writes nothing");
        DV[0].value = (char *)"a=55572";
        Sleep(1050);
        research_tick();
        ok(LOGS == 2 && strcmp(LAST_LOG, "research: saved a=55572") == 0,
           "tick: a moved dvar is saved and said");
        {
            char out[RESEARCH_MAX + 1];
            const char *why = "";
            ok(res_read(path, out, sizeof(out), &why) == 1 && strcmp(out, "a=55572") == 0,
               "tick: the file holds the new id");
        }
        DV[0].value = (char *)"a=";
        Sleep(1050);
        research_tick();
        ok(LOGS == 3 && strcmp(LAST_LOG, "research: refused a line a reader would not take") == 0,
           "tick: a line a reader would not take is said once");
        Sleep(1050);
        research_tick();
        ok(LOGS == 3 && research_active() == 55572, "tick: and the last good id stays active");
        DV[0].value = (char *)"a=55579";
        Sleep(1050);
        research_stop();
        ok(LOGS == 4 && strcmp(LAST_LOG, "research: saved a=55579") == 0,
           "stop: the detach flush writes the line the last tick had not");

        // ---- 5. the unlock gate -------------------------------------------------------------------
        DV[2].value = (char *)"1";
        Sleep(1050);
        research_tick();
        ok(research_paused() == 1, "gate: unlock augments on reads as paused");
        DV[2].value = (char *)"0";
        DV[3].value = (char *)"1";
        Sleep(1050);
        research_tick();
        ok(research_paused() == 1, "gate: unlock all on reads as paused too");
        DV[3].value = (char *)"0";
        Sleep(1050);
        research_tick();
        ok(research_paused() == 0, "gate: both off reads as not paused");
    }

    printf("research: %s - %d checks\n", FAILS == 0 ? "OK" : "FAILED", PASSES);
    return FAILS == 0 ? 0 : 1;
}

// --- the pay: a fabricated record array and a fabricated award ---------------------------------------

#define PAY_ROWS 10

static unsigned char RECS[PAY_ROWS * MASTER_STRIDE];
static res_pay_state PS;
static arm_state ST;
static res_pay_result RES;
static int KILL = 7;
static int CRIT = 5;
static int *W_KILL = &KILL;
static int *W_CRIT = &CRIT;

static int AW_CALLS = 0;
static int AW_TRIG = -1;
static int AW_N = -1;
static int AW_KILL = -1;
static int AW_CRIT = -1;
static int AW_TAIL_ZERO = 0;
static long AW_TAKE = -1;   // -1 = the whole held amount
static int AW_FAULT = 0;

// the armory side of the same feed
static arm_state ARM_ST;
static arm_pay_state APS;
static arm_pay_result ARES;

static void row_init(int i, unsigned long long id, int kind, int tiers, unsigned thr0, int status, long long xp,
                     unsigned trig)
{
    unsigned char *r = RECS + (size_t)i * MASTER_STRIDE;
    memset(r, 0, MASTER_STRIDE);
    *(unsigned long long *)r = id;
    *(int *)(r + MASTER_REC_KIND) = kind;
    *(int *)(r + MASTER_REC_COUNT) = tiers;
    *(unsigned *)(r + MASTER_REC_THR) = thr0;
    *(unsigned char *)(r + ARM_REC_STATUS) = (unsigned char)status;
    *(long long *)(r + MASTER_REC_XP) = xp;
    *(int *)(r + RES_REC_TRIGS) = 1;
    *(unsigned *)(r + RES_REC_TRIG) = trig;
}

static unsigned char *row_at(int i)
{
    return RECS + (size_t)i * MASTER_STRIDE;
}

// the three thresholds the real augment rows carry
static void set_thr(int i, unsigned t0, unsigned t1, unsigned t2)
{
    unsigned char *r = row_at(i);
    *(unsigned *)(r + MASTER_REC_THR) = t0;
    *(unsigned *)(r + MASTER_REC_THR + 4) = t1;
    *(unsigned *)(r + MASTER_REC_THR + 8) = t2;
}

// 0 an armory row 1 the research row 2 another research row 3 a weapon row
// 4 a research row outside the range 5 a research row with no trigger
// 6 a complete research row 7 the last of the range 8 one past it 9 the armory last
static void rows_init(void)
{
    row_init(0, 75671, 368, 1, 250000, 0, 0, 200001);
    row_init(1, 55571, 437, 3, 70000, 0, 0, 200085);
    set_thr(1, 70000, 140000, 275000);
    row_init(2, 55572, 437, 3, 70000, 0, 0, 200086);
    set_thr(2, 70000, 140000, 275000);
    row_init(3, 90001, 398, 1, 5000, 0, 0, 0);
    row_init(4, 55573, 437, 1, 150000, 0, 0, 900001);
    row_init(5, 55574, 437, 1, 150000, 0, 0, 200090);
    *(int *)(row_at(5) + RES_REC_TRIGS) = 0;
    row_init(6, 55575, 437, 1, 150000, 3, 150000, 200077);
    row_init(7, 55576, 437, 1, 150000, 0, 0, 200108);
    row_init(8, 55577, 437, 1, 150000, 0, 0, 200109);
    row_init(9, 55578, 437, 1, 150000, 0, 0, 200076);
}

// the game own add faked the row whose trigger the record names gains what was held
static unsigned long long fake_award(const unsigned int *ev)
{
    AW_CALLS++;
    AW_TRIG = (int)ev[0];
    AW_N = (int)ev[1];
    AW_KILL = *W_KILL;
    AW_CRIT = *W_CRIT;
    AW_TAIL_ZERO = 1;
    for (int i = 2; i < 8; i++)
    {
        if (ev[i] != 0)
        {
            AW_TAIL_ZERO = 0;
        }
    }
    if (AW_FAULT)
    {
        RaiseException(0xC0000005, 0, 0, NULL);
    }
    for (int i = 0; i < PAY_ROWS; i++)
    {
        unsigned char *r = row_at(i);
        if (*(unsigned *)(r + RES_REC_TRIG) != (unsigned)AW_TRIG)
        {
            continue;
        }
        long take = (AW_TAKE < 0) ? *W_KILL : AW_TAKE;
        *(long long *)(r + MASTER_REC_XP) += take;
        break;
    }
    return 0;
}

// one case from a clean process state the beat this fresh
static void pay_setup(unsigned long long beat_ms)
{
    arm_state_init(&ST);
    ST.have = 1;
    ST.serial = 1;
    ST.beat = 5;
    ST.beat_ms = beat_ms;
    memset(&PS, 0, sizeof(PS));
    memset(&RES, 0, sizeof(RES));
    rows_init();
    AW_CALLS = 0;
    AW_TRIG = -1;
    AW_N = -1;
    AW_KILL = -1;
    AW_CRIT = -1;
    AW_TAIL_ZERO = 0;
    AW_TAKE = -1;
    AW_FAULT = 0;
    KILL = 7;
    CRIT = 5;
    // anything the last case posted is written and the count starts again
    research_pay_log();
    LOGS = 0;
}

// one look the way the shell makes it
static int look(unsigned long long now, int active, long pending, int unlocked, int off)
{
    res_pay_in in;
    in.active = active;
    in.unlocked = unlocked;
    in.off = off;
    in.recs = RECS;
    in.n = PAY_ROWS;
    ST.pending = pending;
    int r = res_pay_look(&PS, &in, &ST, now, fake_award, &KILL, &CRIT, &RES);
    if (r)
    {
        res_pay_post(&RES);
    }
    return r;
}

static int look2(unsigned long long now, int active, long pending)
{
    return look(now, active, pending, 0, 0);
}

// the armory pay over the same array and its own state
static void arm_setup(unsigned long long beat_ms)
{
    arm_state_init(&ARM_ST);
    ARM_ST.have = 1;
    ARM_ST.serial = 1;
    ARM_ST.beat = 5;
    ARM_ST.beat_ms = beat_ms;
    memset(&APS, 0, sizeof(APS));
    memset(&ARES, 0, sizeof(ARES));
}

static int arm_look(unsigned long long now, int active, long pending)
{
    arm_pay_in in;
    in.active = active;
    in.unlocked = 0;
    in.off = 0;
    in.advance_off = 1;
    in.recs = RECS;
    in.n = PAY_ROWS;
    ARM_ST.pending = pending;
    int r = arm_pay_look(&APS, &in, &ARM_ST, now, fake_award, &KILL, &CRIT, &ARES);
    if (r)
    {
        arm_pay_post(&ARES);
    }
    return r;
}

static int pay_mode(void)
{
    rows_init();
    LOGS = 0;

    // ---- 6. the row walk --------------------------------------------------------------------------
    ok(arm_row_find(RECS, PAY_ROWS, 55571) == 1 && arm_row_find(RECS, PAY_ROWS, 55578) == 9,
       "row: the walk finds a row by the id at its own first eight bytes");
    ok(arm_row_find(RECS, PAY_ROWS, 0) == -1 && arm_row_find(RECS, PAY_ROWS, 42) == -1
           && arm_row_find(NULL, PAY_ROWS, 55571) == -1,
       "row: a zero id an absent id and no array are all no row");
    ok(res_row_ours(row_at(1)) == 1 && res_row_ours(row_at(2)) == 1 && res_row_ours(row_at(7)) == 1,
       "row: ours is a kind 437 row with a trigger in 200077..200108");
    ok(res_row_ours(row_at(0)) == 0 && res_row_ours(row_at(3)) == 0,
       "row: the armory row and the weapon row are not ours");
    ok(res_row_ours(row_at(4)) == 0 && res_row_ours(row_at(8)) == 0 && res_row_ours(row_at(9)) == 0,
       "row: a trigger outside the range one past it and the armory last are not ours");
    ok(res_row_ours(row_at(5)) == 0 && res_row_ours(NULL) == 0,
       "row: a row with no trigger and no row at all are not ours");
    ok(arm_row_top(row_at(1)) == 275000 && arm_row_top(row_at(6)) == 150000,
       "row: the last threshold is the row own of its three");
    ok(arm_row_complete(row_at(6)) == 1 && arm_row_complete(row_at(1)) == 0,
       "row: complete is the game own status or the xp past the last threshold");

    // ---- 7. the happy path ------------------------------------------------------------------------
    pay_setup(10000);
    int did = look2(10000, 55571, 1200);
    ok(did == 1 && RES.why == RES_PAY_DONE, "pay: one look with something owed pays");
    ok(AW_CALLS == 1 && AW_TRIG == 200085 && AW_N == 0,
       "pay: the record is the row own private trigger with no entries");
    ok(AW_TAIL_ZERO == 1, "pay: the rest of the 0x200 block is zero");
    ok(AW_KILL == 1200 && AW_CRIT == 0, "pay: the amount held is the pending total and the crit is zero");
    ok(arm_row_xp(row_at(1)) == 1200, "pay: the active row gains exactly that amount");
    ok(arm_row_xp(row_at(0)) == 0 && arm_row_xp(row_at(2)) == 0,
       "pay: the armory row and every other research row are untouched");
    ok(KILL == 7 && CRIT == 5, "pay: both globals read back what they held before the call");
    ok(ST.paid == 1200 && ST.pending == 0, "pay: the paid mark and the pending follow the read back");
    ok(RES.id == 55571 && RES.held == 1200 && RES.got == 1200 && RES.progress == 1200 && RES.top == 275000,
       "pay: the result carries the row the amount the rise and the bar");
    research_pay_log();
    ok(LOGS == 1 && strcmp(LAST_LOG, "research: paid row=55571 +1200 -> 1200/275000") == 0,
       "pay: the paid line names the row the rise and the bar");

    // ---- 8. the rate limit ------------------------------------------------------------------------
    pay_setup(10000);
    look2(10000, 55571, 500);
    look2(10500, 55571, 500);
    ok(AW_CALLS == 1, "pay: a second look inside the second does not pay");
    look2(11000, 55571, 500);
    ok(AW_CALLS == 2, "pay: a look a second after the last one pays again");

    // ---- 9. the gates -----------------------------------------------------------------------------
    pay_setup(10000);
    ok(look2(10000, 0, 900) == 0 && AW_CALLS == 0, "pay: no research picked pays nothing");
    ok(look2(11000, 55571, 0) == 0 && AW_CALLS == 0, "pay: nothing owed pays nothing");
    ok(look2(12000, 90001, 900) == 0 && AW_CALLS == 0, "pay: a weapon row the channel names pays nothing");
    ok(look2(13000, 55573, 900) == 0 && AW_CALLS == 0, "pay: a row outside the private triggers pays nothing");
    ok(look2(14000, 55574, 900) == 0 && AW_CALLS == 0, "pay: a row with no trigger count pays nothing");
    ok(look2(15000, 75671, 900) == 0 && AW_CALLS == 0, "pay: an armory row the channel names pays nothing");
    ok(look2(16000, 99999, 900) == 0 && AW_CALLS == 0, "pay: an id the array does not hold pays nothing");
    pay_setup(10000);
    ok(look2(13000, 55571, 900) == 0 && AW_CALLS == 0, "pay: a beat older than the window pays nothing");
    pay_setup(10000);
    ok(look(10000, 55571, 900, 0, 1) == 0 && AW_CALLS == 0, "pay: the kill switch pays nothing");

    // ---- 10. the unlock gate ----------------------------------------------------------------------
    pay_setup(10000);
    ok(look(10000, 55571, 1200, 1, 0) == 1 && RES.why == RES_PAY_PAUSE && AW_CALLS == 0,
       "pay: unlock augments on pays nothing");
    ok(arm_row_xp(row_at(1)) == 0 && ST.paid == 0 && ST.pending == 1200,
       "pay: the row does not move and nothing is credited");
    research_pay_log();
    ok(LOGS == 1 && strcmp(LAST_LOG, "research: pay paused (unlock augments)") == 0,
       "pay: the pause is one line");
    ok(look(11000, 55571, 1200, 1, 0) == 0 && AW_CALLS == 0, "pay: a later look while paused still pays nothing");
    research_pay_log();
    ok(LOGS == 1, "pay: the pause is said once not once a look");
    ST.beat_ms = 12000;
    ok(look(12000, 55571, 1200, 0, 0) == 1 && RES.why == RES_PAY_RESUME && AW_CALLS == 0,
       "pay: the first look after it goes off says the pay resumed");
    research_pay_log();
    ok(LOGS == 2 && strcmp(LAST_LOG, "research: pay resumed") == 0, "pay: the resume is one line");
    ST.beat_ms = 13000;
    ok(look(13000, 55571, 1200, 0, 0) == 1 && RES.why == RES_PAY_DONE && AW_CALLS == 1,
       "pay: and the next look pays again");

    // ---- 11. the short credit ---------------------------------------------------------------------
    pay_setup(10000);
    AW_TAKE = 400;
    ok(look2(10000, 55571, 1200) == 1 && RES.why == RES_PAY_SHORT && RES.got == 400,
       "pay: a row that moves less than the hold is a short credit");
    ok(ST.paid == 400 && ST.pending == 800, "pay: the short rise is kept and the rest is still owed");
    research_pay_log();
    ok(LOGS == 1 && strcmp(LAST_LOG, "research: pay short row=55571 moved 400 of 1200 -> 400/275000") == 0,
       "pay: the short line carries the rise the hold and the bar");
    AW_TAKE = -1;
    ok(look2(11000, 55571, 800) == 1 && RES.why == RES_PAY_DONE && arm_row_xp(row_at(1)) == 1200,
       "pay: the next look pays the rest of the same total");

    // ---- 12. the complete row ---------------------------------------------------------------------
    pay_setup(10000);
    ok(look2(10000, 55575, 1200) == 1 && RES.why == RES_PAY_COMPLETE && AW_CALLS == 0,
       "pay: a complete row pays nothing");
    research_pay_log();
    ok(LOGS == 1 && strcmp(LAST_LOG, "research: row 55575 complete") == 0,
       "pay: the completion is one line");
    ok(arm_row_xp(row_at(6)) == 150000, "pay: the complete row does not move");
    ok(look2(11000, 55575, 1200) == 1 && RES.why == RES_PAY_COMPLETE && AW_CALLS == 0,
       "pay: a later look says complete again and still pays nothing");
    research_pay_log();
    ok(LOGS == 1, "pay: the completion is said once not once a look");

    // ---- 13. the fault ----------------------------------------------------------------------------
    pay_setup(10000);
    AW_FAULT = 1;
    ok(look2(10000, 55571, 900) == 1 && RES.why == RES_PAY_FAULT, "pay: a fault in the award is caught");
    ok(PS.latched == 1 && KILL == 7 && CRIT == 5, "pay: the pay latches off and the pair is put back");
    research_pay_log();
    ok(LOGS == 1 && strcmp(LAST_LOG, "research: pay latched off after a fault in the award") == 0,
       "pay: the fault is one line");
    AW_FAULT = 0;
    ok(look2(11000, 55571, 900) == 0 && AW_CALLS == 1, "pay: a latched pay never pays again");

    // ---- 14. our own accounting beside the armory's -----------------------------------------------
    pay_setup(10000);
    arm_setup(10000);
    {
        arm_line ln;
        arm_events ev;
        ln.s = 1;
        ln.x = 1200;
        ln.h = 5;
        arm_feed_step(&ST, &ln, 10000, &ev);
        arm_feed_step(&ARM_ST, &ln, 10000, &ev);
    }
    ok(ST.pending == 1200 && ARM_ST.pending == 1200, "apart: one feed line gives both pays the same total");
    ok(arm_look(10000, 75671, ARM_ST.pending) == 1 && ARES.why == ARM_PAY_DONE,
       "apart: the armory pays its own row the whole total");
    ok(arm_row_xp(row_at(0)) == 1200 && ARM_ST.paid == 1200 && ARM_ST.pending == 0,
       "apart: the armory row holds it and the armory state is spent");
    ok(ST.paid == 0 && ST.pending == 1200,
       "apart: the research state still holds the whole total");
    ok(look2(10000, 55571, ST.pending) == 1 && RES.why == RES_PAY_DONE,
       "apart: the research pay credits its own row the same total");
    ok(arm_row_xp(row_at(1)) == 1200 && ST.paid == 1200 && ST.pending == 0,
       "apart: both rows were paid the same match xp independently");
    ok(AW_CALLS == 2 && AW_TRIG == 200085, "apart: each pay called the award once for its own trigger");
    research_pay_log();
    ok(LOGS == 1 && strcmp(LAST_LOG, "research: paid row=55571 +1200 -> 1200/275000") == 0,
       "apart: the research line is its own not the armory one");
    armory_pay_log();
    ok(LOGS == 2 && strcmp(LAST_LOG, "armory: paid row=75671 +1200 -> 1200/250000") == 0,
       "apart: the armory line still names the armory row");

    // ---- 15. the kill switch file -----------------------------------------------------------------
    {
        wchar_t sub[MAX_PATH];
        wchar_t path[MAX_PATH];
        _snwprintf_s(sub, MAX_PATH, _TRUNCATE, L"%sprogression-tuning", DIR);
        CreateDirectoryW(sub, NULL);
        _snwprintf_s(path, MAX_PATH, _TRUNCATE, L"%sprogression-tuning\\research_pay_off.txt", DIR);
        ok(put_raw(path, "") == 0, "off: the switch file is staged");
        ok(res_pay_off_present(DIR) == 1, "off: the research pay switch is found");
        DeleteFileW(path);
        ok(res_pay_off_present(DIR) == 0, "off: and it is gone when the file is");
    }

    printf("research: %s - %d checks\n", FAILS == 0 ? "OK" : "FAILED", PASSES);
    return FAILS == 0 ? 0 : 1;
}

int main(int argc, char **argv)
{
    if (argc >= 2 && strcmp(argv[1], "self") == 0)
    {
        return self_mode();
    }
    if (argc >= 2 && strcmp(argv[1], "pay") == 0)
    {
        return pay_mode();
    }
    if (argc >= 3 && strcmp(argv[1], "off") == 0)
    {
        wchar_t dir[MAX_PATH];
        int n = MultiByteToWideChar(CP_ACP, 0, argv[2], -1, dir, MAX_PATH);
        if (n <= 0)
        {
            return 2;
        }
        printf("%d\n", res_pay_off_present(dir));
        return 0;
    }
    printf("usage: research_test.exe self | pay | off <dir>\n");
    return 2;
}
