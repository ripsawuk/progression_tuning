// clienthook - the armory xp feed the dvar the parse and the change log
//
// the level thread of the mod gsc publishes the operator pre cap rank xp as
// a total for the match this unit registers pt_armory_xp at boot reads it on
// the frame 250 ms thread and writes one line when the total moves
// a serial that moved begins a new match so does a beat that went back
// and a total that went back on an early beat the mod dvar does not
// survive a level load so the serial reads one at every thread start
// it opens no file and starts no thread
//
// the pay turns what the match earned into row progress and it runs on the
// client own drain thread inside the store lock through the client own award
// the amount is held in the two globals for exactly one call and the row is
// the one active pick named by its own private trigger the credit is never
// taken from that hold it is the row own rise read back after the call
// every line the pay earns is posted here and written by the frame thread

#include <windows.h>
#include <string.h>
#include <wchar.h>

#include "g11.h"
#include "master.h"
#include "resolve.h"
#include "pick.h"
#include "armory.h"

void ch_logf(const char *fmt, ...);   // proxy_main.c

#define ARM_BIT_NONE 0
#define ARM_BIT_S 1
#define ARM_BIT_X 2
#define ARM_BIT_H 4
#define ARM_BITS_ALL (ARM_BIT_S | ARM_BIT_X | ARM_BIT_H)

static void *ARM_DVAR;
static long ARM_SLOT;
static int ARM_ARMED;
static int ARM_OFF;
static int ARM_SAID_BAD;
static int ARM_PAY_OFF;
static char ARM_DEF[ARMORY_MAX + 1];   // the dvar default text static on purpose
static arm_state ARM_ST;
static arm_pay_state ARM_PS;
static volatile LONG ARM_PAY_BUSY;     // one thread inside the pay at a time
static volatile LONG ARM_SAID_NOTE;     // the second thread note is one line
static int ARM_SAID_DONE;              // the row the complete line last named
static int ARM_ADV_ID;                 // the row whose completion was posted
static int ARM_ADV_OFF;                // the advance kill switch

int arm_valid(const char *s, size_t n)
{
    if (s == NULL || n == 0 || n > ARMORY_MAX)
    {
        return 0;
    }
    for (size_t i = 0; i < n; i++)
    {
        char c = s[i];
        int ok = (c >= 'a' && c <= 'z') || (c >= '0' && c <= '9') || c == '=' || c == ';';
        if (!ok)
        {
            return 0;
        }
    }
    return 1;
}

int arm_parse(const char *s, size_t n, arm_line *out)
{
    if (s == NULL || out == NULL || n < 5 || !arm_valid(s, n))
    {
        return 0;
    }
    out->s = 0;
    out->x = 0;
    out->h = 0;
    int seen = ARM_BIT_NONE;
    size_t i = 0;
    while (i < n)
    {
        char key = s[i];
        int bit = ARM_BIT_NONE;
        long *dst = NULL;
        if (key == 's')
        {
            bit = ARM_BIT_S;
            dst = &out->s;
        }
        else if (key == 'x')
        {
            bit = ARM_BIT_X;
            dst = &out->x;
        }
        else if (key == 'h')
        {
            bit = ARM_BIT_H;
            dst = &out->h;
        }
        else
        {
            return 0; // an unknown key is not this line
        }
        if ((seen & bit) != 0 || i + 2 > n || s[i + 1] != '=')
        {
            return 0;
        }
        seen |= bit;
        i += 2;
        long long v = 0;
        size_t d = 0;
        while (i < n && s[i] >= '0' && s[i] <= '9')
        {
            v = v * 10 + (s[i] - '0');
            if (v > 2147483647LL)
            {
                return 0;
            }
            i++;
            d++;
        }
        if (d == 0)
        {
            return 0;
        }
        *dst = (long)v;
        if (i == n)
        {
            break;
        }
        if (s[i] != ';')
        {
            return 0;
        }
        i++;
        if (i == n)
        {
            return 0; // a trailing separator is not a field
        }
    }
    return seen == ARM_BITS_ALL ? 1 : 0;
}

void arm_state_init(arm_state *st)
{
    if (st == NULL)
    {
        return;
    }
    memset(st, 0, sizeof(*st));
    st->serial = 0;
    st->paid = 0;
    st->pending = 0;
    st->beat = 0;
    st->seen_x = -1;
    st->drop_x = 0;
    st->drop_s = 0;
    st->dirty = 0;
    st->live = 0;
    st->have = 0;
    st->beat_ms = 0;
    st->log_ms = 0;
}

void arm_feed_step(arm_state *st, const arm_line *ln, unsigned long long now, arm_events *ev)
{
    ev->dropped = 0;
    ev->feed = 0;
    ev->delta = 0;
    ev->restart = 0;
    ev->why = "";
    if (st == NULL || ln == NULL)
    {
        return;
    }
    st->drop_x = 0;
    st->drop_s = 0;
    if (ln->s == 0)
    {
        return; // the dvar own default no level has published yet
    }
    // three things begin a new match
    // a serial that moved a beat that went back
    // and a total under the last on an early beat
    int moved = ln->s != st->serial;
    int beat = ln->h < st->beat;
    int xp = ln->x < st->seen_x && ln->h <= ARMORY_SMALL_H;
    int bound = st->have && (moved || beat || xp);
    if (bound || !st->have)
    {
        if (bound)
        {
            ev->restart = 1;
            ev->why = moved ? "serial" : "beat restart";
            if (st->pending > 0)
            {
                st->drop_x = st->pending;
                st->drop_s = st->serial;
                ev->dropped = 1;
            }
        }
        st->serial = ln->s;
        st->paid = 0;
        st->pending = 0;
        st->seen_x = 0;
        st->dirty = 1;
        st->log_ms = 0; // the first line of a match is said at once
    }
    if (ln->x < st->paid)
    {
        st->paid = ln->x; // the feed restarted under us never negative
    }
    st->pending = ln->x - st->paid;
    if (!st->have || ln->h != st->beat)
    {
        st->beat_ms = now;
    }
    st->beat = ln->h;
    st->have = 1;
    if (ln->x != st->seen_x)
    {
        st->dirty = 1;
    }
    if (st->dirty && (st->log_ms == 0 || now - st->log_ms >= ARMORY_LOG_MS))
    {
        long rise = ln->x - st->seen_x;
        ev->delta = rise > 0 ? rise : 0;
        st->dirty = 0;
        st->seen_x = ln->x;
        st->log_ms = now;
        ev->feed = 1;
    }
}

// 1 while the last beat is inside the window the pay shares this answer
static int arm_live_at(const arm_state *st, unsigned long long now)
{
    if (st == NULL || !st->have)
    {
        return 0;
    }
    return (now - st->beat_ms < ARMORY_LIVE_MS) ? 1 : 0;
}

int arm_feed_live(arm_state *st, unsigned long long now)
{
    if (st == NULL)
    {
        return 0;
    }
    st->live = arm_live_at(st, now);
    return st->live;
}

// the row whose id is this one -1 when the array does not hold it
int arm_row_find(const unsigned char *recs, int n, int id)
{
    if (recs == NULL || n <= 0 || id <= 0)
    {
        return -1;
    }
    for (int i = 0; i < n; i++)
    {
        const unsigned char *r = recs + (size_t)i * MASTER_STRIDE;
        if (*(const unsigned long long *)r == (unsigned long long)id)
        {
            return i;
        }
    }
    return -1;
}

// 1 when the row is one of our 76 an armory kind with a private trigger
int arm_row_ours(const unsigned char *row)
{
    if (row == NULL)
    {
        return 0;
    }
    if (*(const int *)(row + MASTER_REC_KIND) != ARM_KIND_ARMORY)
    {
        return 0;
    }
    if (*(const int *)(row + ARM_REC_TRIGS) < 1)
    {
        return 0;
    }
    unsigned t = *(const unsigned *)(row + ARM_REC_TRIG);
    return (t >= ARM_TRIG_FIRST && t <= ARM_TRIG_LAST) ? 1 : 0;
}

// the row last threshold -1 when its count is not 1..64
long long arm_row_top(const unsigned char *row)
{
    if (row == NULL)
    {
        return -1;
    }
    int tiers = *(const int *)(row + MASTER_REC_COUNT);
    if (tiers <= 0 || tiers > MASTER_THRESHOLDS_MAX)
    {
        return -1;
    }
    return (long long)*(const unsigned *)(row + MASTER_REC_THR + (size_t)(tiers - 1) * 4);
}

long long arm_row_xp(const unsigned char *row)
{
    return (row == NULL) ? 0 : *(const long long *)(row + MASTER_REC_XP);
}

// the client own answer and the number our payment wrote either one is enough
int arm_row_complete(const unsigned char *row)
{
    long long top = arm_row_top(row);
    if (top < 0)
    {
        return 0;
    }
    if (*(const unsigned char *)(row + ARM_REC_STATUS) == 3)
    {
        return 1;
    }
    return (arm_row_xp(row) >= top) ? 1 : 0;
}

// one look the client drain thread runs this with the store lock held
int arm_pay_look(arm_pay_state *ps, const arm_pay_in *in, arm_state *st, unsigned long long now,
                 np_fn orig, int *kill, int *crit, arm_pay_result *out)
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
    // unlock armory on first and cheapest nothing pays
    if (in->unlocked != 0)
    {
        if (!ps->paused)
        {
            ps->paused = 1;
            out->why = ARM_PAY_PAUSE;
            return 1;
        }
        return 0;
    }
    if (ps->paused)
    {
        ps->paused = 0;
        out->why = ARM_PAY_RESUME;
        return 1;
    }
    if (in->off || ps->latched)
    {
        return 0;
    }
    // the look clock before anything else so a refused look costs its second
    if (ps->last_look != 0 && now - ps->last_look < ARM_PAY_MIN_MS)
    {
        return 0;
    }
    ps->last_look = now;
    if (!arm_live_at(st, now))
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
    if (!arm_row_ours(row))
    {
        return 0;
    }
    out->top = arm_row_top(row);
    if (out->top < 0)
    {
        return 0;
    }
    if (arm_row_complete(row))
    {
        // the pick thread does the swap this one posts
        if (!in->advance_off && ARM_ADV_ID != id)
        {
            ARM_ADV_ID = id;
            pick_request_advance(id);
        }
        out->why = ARM_PAY_COMPLETE;
        return 1;
    }
    long pending = st->pending;
    if (pending <= 0)
    {
        return 0;
    }
    long long before = arm_row_xp(row);
    // the client own synthetic record precedent 180094ec0 zeroes the block
    // and writes the id then hands it to the same dispatcher
    unsigned int ev[NP_RECORD_LEN / 4];
    memset(ev, 0, sizeof(ev));
    ev[0] = *(const unsigned *)(row + ARM_REC_TRIG);
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
        out->why = ARM_PAY_FAULT;
        return 1;
    }
    // the credit is the row own rise never the amount held
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
    out->why = (got == pending) ? ARM_PAY_DONE : ARM_PAY_SHORT;
    return 1;
}

// the post the drain thread leaves the frame thread to write
#define ARM_POST_MAX 4

typedef struct
{
    volatile LONG kind;   // 0 empty otherwise an ARM_PAY_*
    int id;
    long held;
    long got;
    long long progress;
    long long top;
} arm_post_rec;

static arm_post_rec ARM_POST[ARM_POST_MAX];
static volatile LONG ARM_POST_N;

void arm_pay_post(const arm_pay_result *r)
{
    if (r == NULL || r->why == ARM_PAY_NONE)
    {
        return;
    }
    if (r->why == ARM_PAY_COMPLETE)
    {
        if (ARM_SAID_DONE == r->id)
        {
            return;
        }
        ARM_SAID_DONE = r->id;
    }
    LONG n = InterlockedIncrement(&ARM_POST_N) - 1;
    arm_post_rec *p = &ARM_POST[n % ARM_POST_MAX];
    p->id = r->id;
    p->held = r->held;
    p->got = r->got;
    p->progress = r->progress;
    p->top = r->top;
    MemoryBarrier();
    InterlockedExchange(&p->kind, (LONG)r->why);
}

void armory_pay_log(void)
{
    for (int i = 0; i < ARM_POST_MAX; i++)
    {
        arm_post_rec *p = &ARM_POST[i];
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
        if (kind == ARM_PAY_DONE)
        {
            ch_logf("armory: paid row=%d +%ld -> %lld/%lld", id, held, progress, top);
        }
        else if (kind == ARM_PAY_SHORT)
        {
            ch_logf("armory: pay short row=%d moved %ld of %ld -> %lld/%lld", id, got, held, progress, top);
        }
        else if (kind == ARM_PAY_COMPLETE)
        {
            ch_logf("armory: row %d complete", id);
        }
        else if (kind == ARM_PAY_FAULT)
        {
            ch_logf("armory: pay latched off after a fault in the award");
        }
        else if (kind == ARM_PAY_NOTE)
        {
            ch_logf("armory: pay note - a second thread entered the window");
        }
        else if (kind == ARM_PAY_PAUSE)
        {
            ch_logf("armory: pay paused (unlock armory on)");
        }
        else if (kind == ARM_PAY_RESUME)
        {
            ch_logf("armory: pay resumed");
        }
    }
}

// the dvar text or NULL when it is unreadable
static const char *arm_value(void)
{
    if (ARM_DVAR == NULL)
    {
        return NULL;
    }
    const char *v = *(char **)((char *)ARM_DVAR + ARM_SLOT);
    if (v == NULL || !g11_page_ok(v))
    {
        return NULL;
    }
    return v;
}

int arm_feed_off_present(const wchar_t *tempdir)
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
    if (_snwprintf_s(path, MAX_PATH, _TRUNCATE, L"%sprogression-tuning\\armory_feed_off.txt", tempdir) < 0)
    {
        return 0;
    }
    DWORD a = GetFileAttributesW(path);
    return (a != INVALID_FILE_ATTRIBUTES && a != 0xFFFFFFFFu) ? 1 : 0;
}

int arm_pay_off_present(const wchar_t *tempdir)
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
    if (_snwprintf_s(path, MAX_PATH, _TRUNCATE, L"%sprogression-tuning\\armory_pay_off.txt", tempdir) < 0)
    {
        return 0;
    }
    DWORD a = GetFileAttributesW(path);
    return (a != INVALID_FILE_ATTRIBUTES && a != 0xFFFFFFFFu) ? 1 : 0;
}

int arm_advance_off_present(const wchar_t *tempdir)
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
    if (_snwprintf_s(path, MAX_PATH, _TRUNCATE, L"%sprogression-tuning\\armory_advance_off.txt", tempdir) < 0)
    {
        return 0;
    }
    DWORD a = GetFileAttributesW(path);
    return (a != INVALID_FILE_ATTRIBUTES && a != 0xFFFFFFFFu) ? 1 : 0;
}

// the client record array the pay walks resolved the same way the pick does
static int arm_records(unsigned char **out, int *count)
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
    if (recs == NULL || n <= 0 || n > ARM_REC_MAX)
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

// the shell on the drain thread reads the pick the feed and the array then looks once
static void arm_pay_once(np_fn orig, int *kill, int *crit)
{
    // the two cheapest gates again before the client array is resolved: this runs for every event the client
    // dispatches, and the look itself re-checks all of them, so a pass here only saves the walk
    ULONGLONG now = GetTickCount64();
    if (ARM_PS.latched || (ARM_PS.last_look != 0 && now - ARM_PS.last_look < ARM_PAY_MIN_MS))
    {
        return;
    }
    unsigned char *recs = NULL;
    int n = 0;
    if (arm_records(&recs, &n) != 0)
    {
        return;
    }
    arm_pay_in in;
    in.active = pick_active();
    in.unlocked = pick_unlocked();
    in.off = ARM_PAY_OFF;
    in.advance_off = ARM_ADV_OFF;
    in.recs = recs;
    in.n = n;
    arm_pay_result r;
    if (arm_pay_look(&ARM_PS, &in, &ARM_ST, now, orig, kill, crit, &r))
    {
        arm_pay_post(&r);
    }
}

void armory_pay(np_fn orig, int *kill, int *crit)
{
    if (!ARM_ARMED || ARM_PAY_OFF || orig == NULL || kill == NULL || crit == NULL)
    {
        return;
    }
    if (InterlockedCompareExchange(&ARM_PAY_BUSY, 1, 0) != 0)
    {
        if (InterlockedCompareExchange(&ARM_SAID_NOTE, 1, 0) == 0)
        {
            arm_pay_result r;
            memset(&r, 0, sizeof(r));
            r.why = ARM_PAY_NOTE;
            arm_pay_post(&r);
        }
        return;
    }
    __try
    {
        arm_pay_once(orig, kill, crit);
    }
    __except (EXCEPTION_EXECUTE_HANDLER)
    {
        ARM_PS.latched = 1;
        arm_pay_result r;
        memset(&r, 0, sizeof(r));
        r.why = ARM_PAY_FAULT;
        arm_pay_post(&r);
    }
    InterlockedExchange(&ARM_PAY_BUSY, 0);
}

void armory_arm(G11_REG reg, const unsigned char salt[16], long slot)
{
    if (ARM_ARMED || ARM_OFF || reg == NULL)
    {
        return;
    }
    if (arm_feed_off_present(NULL))
    {
        ARM_OFF = 1;
        ch_logf("armory: feed disabled by file (%s)", "%TEMP%\\progression-tuning\\armory_feed_off.txt");
        return;
    }
    strcpy_s(ARM_DEF, sizeof(ARM_DEF), ARMORY_DEFAULT);
    void *d = reg(g11_hash_name(ARMORY_NAME, salt), ARM_DEF, 0, "progression tuning armory xp");
    if (d == NULL)
    {
        return; // the engine register is not ready the caller retries
    }
    char **value = (char **)((char *)d + slot);
    if (!g11_page_writable(value))
    {
        ARM_OFF = 1;
        ch_logf("armory: refused - the value slot is not writable");
        return;
    }
    // the default this call creates the dvar with
    *value = ARM_DEF;
    ARM_DVAR = d;
    ARM_SLOT = slot;
    arm_state_init(&ARM_ST);
    ARM_ARMED = 1;
    ch_logf("armory: registered %s = %s", ARMORY_NAME, ARM_DEF);
    // the pay own kill switch read once here and latched like the feed one
    if (arm_pay_off_present(NULL))
    {
        ARM_PAY_OFF = 1;
        ch_logf("armory: pay disabled by file (%s)", "%TEMP%\\progression-tuning\\armory_pay_off.txt");
    }
    // the advance switch moves nothing the pay still runs
    if (arm_advance_off_present(NULL))
    {
        ARM_ADV_OFF = 1;
        ch_logf("armory: advance disabled by file (%s)", "%TEMP%\\progression-tuning\\armory_advance_off.txt");
    }
}

void armory_tick(void)
{
    // the lines the pay posted first whatever the feed state
    armory_pay_log();
    if (!ARM_ARMED || ARM_OFF)
    {
        return;
    }
    ULONGLONG now = GetTickCount64();
    const char *v = arm_value();
    if (v != NULL)
    {
        size_t n = strnlen(v, ARMORY_MAX + 1);
        arm_line ln;
        if (!arm_valid(v, n) || arm_parse(v, n, &ln) == 0)
        {
            if (!ARM_SAID_BAD)
            {
                ARM_SAID_BAD = 1;
                ch_logf("armory: refused a line a reader would not take");
            }
        }
        else
        {
            arm_events ev;
            arm_feed_step(&ARM_ST, &ln, now, &ev);
            if (ev.dropped)
            {
                ch_logf("armory: dropped %ld at s=%ld (%s)", ARM_ST.drop_x, ARM_ST.drop_s, ev.why);
            }
            if (ev.feed)
            {
                ch_logf("armory: feed s=%ld x=%ld h=%ld (+%ld)", ln.s, ln.x, ln.h, ev.delta);
            }
        }
    }
    // the liveness after the line so this beat counts
    int was = ARM_ST.live;
    int live = arm_feed_live(&ARM_ST, now);
    if (live != was)
    {
        ch_logf("armory: live=%d s=%ld x=%ld h=%ld", live, ARM_ST.serial, ARM_ST.seen_x, ARM_ST.beat);
    }
}

int armory_armed(void)
{
    return ARM_ARMED;
}
