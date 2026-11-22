// the augment research channel the file and the pay
//
// the game menu writes one dvar
// the hook mirrors it to one file
// boot makes the file line the dvar default
// the pay takes the same match operator xp
// and keeps its own paid and pending
// the row is the active id own private trigger
// the credit is the row own rise
// every line the pay earns is posted here
// and written by the frame thread

#include <windows.h>
#include <stdio.h>
#include <string.h>
#include <wchar.h>

#include "g11.h"
#include "master.h"
#include "resolve.h"
#include "armory.h"
#include "nativepay.h"
#include "research.h"

void ch_logf(const char *fmt, ...);          // proxy_main.c
void ch_self_dir(wchar_t *out, DWORD cch);   // proxy_main.c

#define RES_SUBDIR L"players"
#define RES_FILE L"research.txt"
#define RES_TICK_MS 1000   // read the dvar at most this often

static void *RES_DVAR;
static long RES_SLOT;
static int RES_ARMED;
static int RES_OFF;
static char RES_DISK[RESEARCH_MAX + 1];  // what the file holds as far as this process knows
static volatile LONG RES_A;              // the active row
static int RES_SAID_BAD;
static ULONGLONG RES_TICK_AT;

// the feed is the armory dvar read again
// the state is ours so the accounting stays apart
static void *RES_FEED;
static arm_state RES_ST;

// the two unlock dvars the game registered
static void *RES_UA;
static void *RES_ALL;
static volatile LONG RES_UNLOCK;  // 1 = unlock augments or unlock all on

static res_pay_state RES_PS;
static volatile LONG RES_PAY_BUSY;    // one thread inside the pay at a time
static volatile LONG RES_SAID_NOTE;   // the second thread note is one line
static int RES_SAID_DONE;             // the row the complete line last named
static int RES_PAY_OFF;               // the pay kill switch

int res_valid(const char *s, size_t n)
{
    if (s == NULL || n == 0 || n > RESEARCH_MAX)
    {
        return 0;
    }
    for (size_t i = 0; i < n; i++)
    {
        char c = s[i];
        int ok = (c >= 'a' && c <= 'z') || (c >= '0' && c <= '9') || c == '=';
        if (!ok)
        {
            return 0;
        }
    }
    return 1;
}

int res_parse(const char *s, size_t n, int *a)
{
    if (s == NULL || a == NULL || n < 3 || !res_valid(s, n))
    {
        return 0;
    }
    if (s[0] != 'a' || s[1] != '=')
    {
        return 0;
    }
    long long v = 0;
    size_t d = 0;
    for (size_t i = 2; i < n; i++)
    {
        if (s[i] < '0' || s[i] > '9')
        {
            return 0;
        }
        v = v * 10 + (s[i] - '0');
        if (v > 2147483647LL)
        {
            return 0;
        }
        d++;
    }
    if (d == 0)
    {
        return 0;
    }
    *a = (int)v;
    return 1;
}

// the digits of v in order 0 is one zero
static int res_dec(char *out, int v)
{
    char rev[12];
    int n = 0;
    if (v < 0)
    {
        return 0;
    }
    do
    {
        rev[n++] = (char)('0' + (v % 10));
        v /= 10;
    } while (v != 0);
    for (int i = 0; i < n; i++)
    {
        out[i] = rev[n - 1 - i];
    }
    return n;
}

int res_build(char *out, size_t cap, int a)
{
    if (out == NULL || cap == 0 || a < 0)
    {
        return -1;
    }
    char digits[12];
    int n = res_dec(digits, a);
    if (n <= 0 || (size_t)n + 3 > cap)
    {
        return -1;
    }
    out[0] = 'a';
    out[1] = '=';
    memcpy(out + 2, digits, (size_t)n);
    out[2 + n] = '\0';
    return 0;
}

// <dll dir>players\<file> the folder is never made here
static int res_path(wchar_t *out, DWORD cch)
{
    wchar_t base[MAX_PATH];
    ch_self_dir(base, MAX_PATH);
    if (base[0] == L'\0')
    {
        return 0;
    }
    return _snwprintf_s(out, cch, _TRUNCATE, L"%s" RES_SUBDIR L"\\" RES_FILE, base) >= 0;
}

// 1 when the game players folder is there
static int res_folder(void)
{
    wchar_t base[MAX_PATH];
    wchar_t dir[MAX_PATH];
    ch_self_dir(base, MAX_PATH);
    if (base[0] == L'\0')
    {
        return 0;
    }
    if (_snwprintf_s(dir, MAX_PATH, _TRUNCATE, L"%s" RES_SUBDIR, base) < 0)
    {
        return 0;
    }
    DWORD a = GetFileAttributesW(dir);
    return (a != INVALID_FILE_ATTRIBUTES && (a & FILE_ATTRIBUTE_DIRECTORY) != 0) ? 1 : 0;
}

int res_read(const wchar_t *path, char *out, size_t cap, const char **why)
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
    // one byte past a full line and its ending
    char buf[RESEARCH_MAX + 3];
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
    if (n > RESEARCH_MAX)
    {
        if (why != NULL)
        {
            *why = "the line is longer than 32 chars";
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
    if (!res_valid(buf, n))
    {
        if (why != NULL)
        {
            *why = "the line carries a character outside [a-z0-9=]";
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

int res_write(const wchar_t *path, const char *line)
{
    if (path == NULL || line == NULL)
    {
        return -1;
    }
    size_t n = strlen(line);
    if (!res_valid(line, n))
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
    // rename over the old file never edit in place
    if (!MoveFileExW(tmp, path, MOVEFILE_REPLACE_EXISTING | MOVEFILE_WRITE_THROUGH))
    {
        DeleteFileW(tmp);
        return -1;
    }
    return 0;
}

// the file value moves only when the write landed
static void res_save(const char *line, int a)
{
    wchar_t path[MAX_PATH];
    // a missing folder is a skip never made here
    int rc = -1;
    if (res_folder() && res_path(path, MAX_PATH))
    {
        rc = res_write(path, line);
    }
    if (rc == 0)
    {
        memcpy(RES_DISK, line, strlen(line) + 1);
        ch_logf("research: saved a=%d", a);
    }
    else
    {
        ch_logf("research: save failed a=%d", a);
    }
}

// the dvar text or NULL when unreadable
static const char *res_value(void)
{
    if (RES_DVAR == NULL)
    {
        return NULL;
    }
    const char *v = *(char **)((char *)RES_DVAR + RES_SLOT);
    if (v == NULL || !g11_page_ok(v))
    {
        return NULL;
    }
    return v;
}

// 1 when the dvar reads the string 1
static int res_one(void *dvar)
{
    if (dvar == NULL)
    {
        return 0;
    }
    const char *v = *(char **)((char *)dvar + RES_SLOT);
    if (v == NULL || !g11_page_ok(v))
    {
        return 0;
    }
    return strcmp(v, "1") == 0 ? 1 : 0;
}

// the armory feed line stepped into our own state
static void res_feed(ULONGLONG now)
{
    if (RES_FEED == NULL)
    {
        return;
    }
    const char *v = *(char **)((char *)RES_FEED + RES_SLOT);
    if (v == NULL || !g11_page_ok(v))
    {
        return;
    }
    size_t n = strnlen(v, ARMORY_MAX + 1);
    arm_line ln;
    if (!arm_valid(v, n) || arm_parse(v, n, &ln) == 0)
    {
        return;
    }
    arm_events ev;
    arm_feed_step(&RES_ST, &ln, now, &ev);
}

// 1 when the row is one of our 32
int res_row_ours(const unsigned char *row)
{
    if (row == NULL)
    {
        return 0;
    }
    if (*(const int *)(row + MASTER_REC_KIND) != RES_KIND)
    {
        return 0;
    }
    if (*(const int *)(row + RES_REC_TRIGS) < 1)
    {
        return 0;
    }
    unsigned t = *(const unsigned *)(row + RES_REC_TRIG);
    return (t >= RES_TRIG_FIRST && t <= RES_TRIG_LAST) ? 1 : 0;
}

// one look under the game store lock
int res_pay_look(res_pay_state *ps, const res_pay_in *in, arm_state *st, unsigned long long now,
                 np_fn orig, int *kill, int *crit, res_pay_result *out)
{
    if (out == NULL)
    {
        return 0;
    }
    memset(out, 0, sizeof(*out));
    if (ps == NULL || in == NULL || st == NULL || orig == NULL || kill == NULL || crit == NULL)
    {
        return 0;
    }
    // unlock augments on first and cheapest nothing pays
    if (in->unlocked != 0)
    {
        if (!ps->paused)
        {
            ps->paused = 1;
            out->why = RES_PAY_PAUSE;
            return 1;
        }
        return 0;
    }
    if (ps->paused)
    {
        ps->paused = 0;
        out->why = RES_PAY_RESUME;
        return 1;
    }
    if (in->off || ps->latched)
    {
        return 0;
    }
    // the look clock before anything else
    if (ps->last_look != 0 && now - ps->last_look < RES_PAY_MIN_MS)
    {
        return 0;
    }
    ps->last_look = now;
    if (!arm_feed_live(st, now))
    {
        return 0;
    }
    int id = in->active;
    if (id <= 0)
    {
        return 0;
    }
    out->id = id;
    int idx = arm_row_find(in->recs, in->n, id);
    if (idx < 0)
    {
        return 0;
    }
    const unsigned char *row = in->recs + (size_t)idx * MASTER_STRIDE;
    if (!res_row_ours(row))
    {
        return 0;
    }
    out->top = arm_row_top(row);
    if (out->top < 0)
    {
        return 0;
    }
    // research stays selected so a complete row is only said
    if (arm_row_complete(row))
    {
        out->why = RES_PAY_COMPLETE;
        return 1;
    }
    long pending = st->pending;
    if (pending <= 0)
    {
        return 0;
    }
    long long before = arm_row_xp(row);
    // the game own synthetic record precedent zeroes the block
    // and writes the trigger then hands it on
    unsigned int ev[NP_RECORD_LEN / 4];
    memset(ev, 0, sizeof(ev));
    ev[0] = *(const unsigned *)(row + RES_REC_TRIG);
    ev[1] = 0;
    int k0 = *kill;
    int c0 = *crit;
    volatile int faulted = 0;
    __try
    {
        __try
        {
            *kill = (int)pending;
            *crit = 0;
            orig(ev);
        }
        __finally
        {
            *kill = k0;
            *crit = c0;
        }
    }
    __except (EXCEPTION_EXECUTE_HANDLER)
    {
        faulted = 1;
    }
    out->held = pending;
    if (faulted)
    {
        ps->latched = 1;
        out->why = RES_PAY_FAULT;
        return 1;
    }
    // the credit is the row rise not the hold
    long got = 0;
    int at = arm_row_find(in->recs, in->n, id);
    if (at >= 0)
    {
        long long after = arm_row_xp(in->recs + (size_t)at * MASTER_STRIDE);
        out->progress = after;
        got = (long)(after - before);
    }
    if (got < 0)
    {
        got = 0;
    }
    out->got = got;
    if (got > 0)
    {
        st->paid += got;
        st->pending = (st->pending > got) ? st->pending - got : 0;
    }
    out->why = (got == pending) ? RES_PAY_DONE : RES_PAY_SHORT;
    return 1;
}

// the post the frame thread writes
#define RES_POST_MAX 4

typedef struct
{
    volatile LONG kind;   // 0 empty otherwise a RES_PAY_*
    int id;
    long held;
    long got;
    long long progress;
    long long top;
} res_post_rec;

static res_post_rec RES_POST[RES_POST_MAX];
static volatile LONG RES_POST_N;

void res_pay_post(const res_pay_result *r)
{
    if (r == NULL || r->why == RES_PAY_NONE)
    {
        return;
    }
    if (r->why == RES_PAY_COMPLETE)
    {
        if (RES_SAID_DONE == r->id)
        {
            return;
        }
        RES_SAID_DONE = r->id;
    }
    LONG n = InterlockedIncrement(&RES_POST_N) - 1;
    res_post_rec *p = &RES_POST[n % RES_POST_MAX];
    p->id = r->id;
    p->held = r->held;
    p->got = r->got;
    p->progress = r->progress;
    p->top = r->top;
    MemoryBarrier();
    InterlockedExchange(&p->kind, (LONG)r->why);
}

void research_pay_log(void)
{
    for (int i = 0; i < RES_POST_MAX; i++)
    {
        res_post_rec *p = &RES_POST[i];
        if (p->kind == 0)
        {
            continue;
        }
        int kind = (int)p->kind;
        int id = p->id;
        long held = p->held;
        long got = p->got;
        long long progress = p->progress;
        long long top = p->top;
        InterlockedExchange(&p->kind, 0);
        if (kind == RES_PAY_DONE)
        {
            ch_logf("research: paid row=%d +%ld -> %lld/%lld", id, held, progress, top);
        }
        else if (kind == RES_PAY_SHORT)
        {
            ch_logf("research: pay short row=%d moved %ld of %ld -> %lld/%lld", id, got, held, progress, top);
        }
        else if (kind == RES_PAY_COMPLETE)
        {
            ch_logf("research: row %d complete", id);
        }
        else if (kind == RES_PAY_FAULT)
        {
            ch_logf("research: pay latched off after a fault in the award");
        }
        else if (kind == RES_PAY_NOTE)
        {
            ch_logf("research: pay note - a second thread entered the window");
        }
        else if (kind == RES_PAY_PAUSE)
        {
            ch_logf("research: pay paused (unlock augments)");
        }
        else if (kind == RES_PAY_RESUME)
        {
            ch_logf("research: pay resumed");
        }
    }
}

// the game record array resolved as the pick does
static int res_records(unsigned char **out, int *count)
{
    HMODULE client = GetModuleHandleW(L"XINPUT9_1_0.dll");
    if (client == NULL)
    {
        return -1;
    }
    const RS_TABLE *rs = rs_for(client);
    unsigned recs_rva = rs_rva(rs, RS_RECS);
    unsigned count_rva = rs_rva(rs, RS_COUNT);
    if (recs_rva == 0 || count_rva == 0)
    {
        return -1;
    }
    unsigned char *recs = *(unsigned char **)((BYTE *)client + recs_rva);
    int n = *(volatile int *)((BYTE *)client + count_rva);
    if (recs == NULL || n <= 0 || n > RES_REC_MAX)
    {
        return -1;
    }
    if (!g11_page_ok(recs) || !g11_page_ok(recs + (size_t)(n - 1) * MASTER_STRIDE + MASTER_REC_XP))
    {
        return -1;
    }
    *out = recs;
    *count = n;
    return 0;
}

// the drain thread shell reads then looks once
static void res_pay_once(np_fn orig, int *kill, int *crit)
{
    // the two cheapest gates before the array walk
    ULONGLONG now = GetTickCount64();
    if (RES_PS.latched || (RES_PS.last_look != 0 && now - RES_PS.last_look < RES_PAY_MIN_MS))
    {
        return;
    }
    unsigned char *recs = NULL;
    int n = 0;
    if (res_records(&recs, &n) != 0)
    {
        return;
    }
    res_pay_in in;
    in.active = research_active();
    in.unlocked = research_paused();
    in.off = RES_PAY_OFF;
    in.recs = recs;
    in.n = n;
    res_pay_result r;
    if (res_pay_look(&RES_PS, &in, &RES_ST, now, orig, kill, crit, &r))
    {
        res_pay_post(&r);
    }
}

void research_pay_latch(void)
{
    if (RES_PS.latched)
    {
        return;
    }
    RES_PS.latched = 1;
    res_pay_result r;
    memset(&r, 0, sizeof(r));
    r.why = RES_PAY_FAULT;
    res_pay_post(&r);
}

void research_pay(np_fn orig, int *kill, int *crit)
{
    if (!RES_ARMED || RES_PAY_OFF || orig == NULL || kill == NULL || crit == NULL)
    {
        return;
    }
    if (InterlockedCompareExchange(&RES_PAY_BUSY, 1, 0) != 0)
    {
        if (InterlockedCompareExchange(&RES_SAID_NOTE, 1, 0) == 0)
        {
            res_pay_result r;
            memset(&r, 0, sizeof(r));
            r.why = RES_PAY_NOTE;
            res_pay_post(&r);
        }
        return;
    }
    __try
    {
        res_pay_once(orig, kill, crit);
    }
    __except (EXCEPTION_EXECUTE_HANDLER)
    {
        research_pay_latch();
    }
    InterlockedExchange(&RES_PAY_BUSY, 0);
}

void research_arm(G11_REG reg, const unsigned char salt[16], long slot)
{
    if (RES_ARMED || RES_OFF || reg == NULL)
    {
        return;
    }
    wchar_t path[MAX_PATH];
    // static not stack the engine may keep this pointer
    static char line[RESEARCH_MAX + 1];
    const char *why = "";
    int got = 0;
    if (!res_folder())
    {
        got = -1;
        why = "no players folder";
    }
    else if (res_path(path, MAX_PATH))
    {
        got = res_read(path, line, sizeof(line), &why);
    }
    else
    {
        got = -1;
        why = "the dll own directory could not be named";
    }
    if (got == -1)
    {
        ch_logf("research: file rejected: %s", why);
    }
    if (got != 1)
    {
        strcpy_s(line, sizeof(line), RESEARCH_DEFAULT);
    }
    // our value is the default this call creates it with
    void *d = reg(g11_hash_name(RESEARCH_NAME, salt), line, 0, "progression tuning research");
    if (d == NULL)
    {
        return; // the engine register is not usable yet the caller retries
    }
    char **value = (char **)((char *)d + slot);
    if (!g11_page_writable(value))
    {
        RES_OFF = 1;
        ch_logf("research: refused - the value slot is not writable");
        return;
    }
    int a = 0;
    if (res_parse(line, strlen(line), &a) == 0)
    {
        a = 0;
    }
    RES_A = a;
    strcpy_s(RES_DISK, sizeof(RES_DISK), line);
    *value = RES_DISK;
    RES_DVAR = d;
    RES_SLOT = slot;
    arm_state_init(&RES_ST);
    RES_ARMED = 1;
    ch_logf("research: armed a=%d (%s)", a, got == 1 ? "file" : "default");
    // the feed is the armory dvar found not made
    RES_FEED = reg(g11_hash_name(ARMORY_NAME, salt), ARMORY_DEFAULT, 0, "progression tuning armory xp");
    if (RES_FEED == NULL)
    {
        ch_logf("research: feed dvar not found - the pay cannot run");
    }
    // the two unlock dvars the game registers
    RES_UA = reg(g11_hash_name("zm_unlock_augments", salt), "0", 0, "progression tuning research gate");
    RES_ALL = reg(g11_hash_name("zm_unlock_all", salt), "0", 0, "progression tuning research gate");
    if (RES_UA == NULL || RES_ALL == NULL)
    {
        ch_logf("research: unlock dvars not found - that gate is off");
    }
    // the pay own kill switch read once here
    if (res_pay_off_present(NULL))
    {
        RES_PAY_OFF = 1;
        ch_logf("research: pay disabled by file (%s)", "%TEMP%\\progression-tuning\\research_pay_off.txt");
    }
}

void research_tick(void)
{
    // the lines the pay posted first whatever the feed state
    research_pay_log();
    if (!RES_ARMED || RES_OFF)
    {
        return;
    }
    ULONGLONG now = GetTickCount64();
    // the gate the pay reads from any thread
    InterlockedExchange(&RES_UNLOCK, (res_one(RES_UA) || res_one(RES_ALL)) ? 1 : 0);
    // the feed every tick so a beat stays fresh
    res_feed(now);
    if (RES_TICK_AT != 0 && now - RES_TICK_AT < RES_TICK_MS)
    {
        return;
    }
    RES_TICK_AT = now;
    const char *v = res_value();
    if (v == NULL)
    {
        return;
    }
    size_t n = strnlen(v, RESEARCH_MAX + 1);
    int a = 0;
    if (!res_valid(v, n) || res_parse(v, n, &a) == 0)
    {
        if (!RES_SAID_BAD)
        {
            RES_SAID_BAD = 1;
            ch_logf("research: refused a line a reader would not take");
        }
        return; // nothing to write or nothing a reader would accept
    }
    RES_A = a;
    char line[RESEARCH_MAX + 1];
    if (res_build(line, sizeof(line), a) == 0 && strcmp(line, RES_DISK) != 0)
    {
        res_save(line, a);
    }
}

void research_stop(void)
{
    if (!RES_ARMED)
    {
        return;
    }
    const char *v = res_value();
    if (v == NULL)
    {
        return;
    }
    size_t n = strnlen(v, RESEARCH_MAX + 1);
    int a = 0;
    if (!res_valid(v, n) || res_parse(v, n, &a) == 0)
    {
        return;
    }
    char line[RESEARCH_MAX + 1];
    if (res_build(line, sizeof(line), a) != 0 || strcmp(line, RES_DISK) == 0)
    {
        return;
    }
    res_save(line, a);
}

int research_armed(void)
{
    return RES_ARMED;
}

int research_active(void)
{
    return (int)RES_A;
}

int research_paused(void)
{
    return (int)RES_UNLOCK;
}

int res_pay_off_present(const wchar_t *tempdir)
{
    wchar_t dir[MAX_PATH];
    wchar_t path[MAX_PATH];
    if (tempdir == NULL)
    {
        DWORD n = GetTempPathW(MAX_PATH, dir);
        if (n == 0 || n >= MAX_PATH)
        {
            return 0;
        }
        tempdir = dir;
    }
    if (_snwprintf_s(path, MAX_PATH, _TRUNCATE, L"%sprogression-tuning\\research_pay_off.txt", tempdir) < 0)
    {
        return 0;
    }
    DWORD a = GetFileAttributesW(path);
    return (a != INVALID_FILE_ATTRIBUTES && a != 0xFFFFFFFFu) ? 1 : 0;
}
