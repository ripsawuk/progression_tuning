// Offline driver for src\armory.c: the line's three fields, the state the serial move and the window leave behind,
// the liveness the beat carries, and the arm / tick path over a fabricated dvar. Then the pay: the row walk over a
// fabricated record array, the one call of a fabricated award, the amount held and the credit read back. Links the
// SHIPPED unit; the client is never touched.
//
//   armory_test.exe self         the parse, the state, the serial move, the beat restart, the window, the liveness
//   armory_test.exe arm          the register, the ticks, the deferred line, the refused line
//   armory_test.exe pay          the row walk, the gates, the hold, the award call, the read back, the log lines
//   armory_test.exe off <dir>    1 when <dir>\progression-tuning\armory_feed_off.txt is there, else 0
//   armory_test.exe payoff <dir> 1 when <dir>\progression-tuning\armory_pay_off.txt is there, else 0
//   armory_test.exe advoff <dir> 1 when <dir>\progression-tuning\armory_advance_off.txt is there, else 0
//
// Exit 0 when every check passes; the last line is "armory: OK - <n> checks", like the other drivers here.

#include <windows.h>
#include <stdarg.h>
#include <stdio.h>
#include <string.h>

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

// --- the one thing armory.c asks of the DLL ----------------------------------------------------------

static char LOGS_ALL[32][256];
static int LOGS = 0;

#define LAST_LOG (LOGS_ALL[LOGS > 0 ? LOGS - 1 : 0])

void ch_logf(const char *fmt, ...)
{
    char body[256];
    va_list ap;
    va_start(ap, fmt);
    _vsnprintf_s(body, sizeof(body), _TRUNCATE, fmt, ap);
    va_end(ap);
    strcpy_s(LOGS_ALL[LOGS < 32 ? LOGS : 31], sizeof(LOGS_ALL[0]), body);
    if (LOGS < 32)
    {
        LOGS++;
    }
    printf("      | %s\n", body);
}

// the fabricated dvar_t: the value pointer sits ARM_SLOT bytes into it
static struct
{
    char pad[16];
    char *value;
} ARD;

#define ARM_SLOT 16L
static int REG_CALLS = 0;
static char REG_DEF[ARMORY_MAX + 1];

static void *stub_reg(unsigned long long hash, const char *def, int flags, const char *desc)
{
    (void)hash;
    (void)flags;
    (void)desc;
    REG_CALLS++;
    strcpy_s(REG_DEF, sizeof(REG_DEF), def);
    ARD.value = (char *)def; // what the engine would have created it holding
    return &ARD;
}

// --- the line ----------------------------------------------------------------------------------------

static int parses(const char *text, long s, long x, long h)
{
    arm_line ln;
    if (arm_parse(text, strlen(text), &ln) == 0)
    {
        return 0;
    }
    return ln.s == s && ln.x == x && ln.h == h;
}

static int refuses(const char *text)
{
    arm_line ln;
    return arm_parse(text, strlen(text), &ln) == 0;
}

// --- the state ---------------------------------------------------------------------------------------

// one accepted line through the state; 1 = the feed line is due now, *delta gets its rise
static int step2(arm_state *st, long s, long x, long h, unsigned long long now, long *delta)
{
    arm_line ln;
    ln.s = s;
    ln.x = x;
    ln.h = h;
    arm_events ev;
    arm_feed_step(st, &ln, now, &ev);
    if (delta != NULL)
    {
        *delta = ev.delta;
    }
    return ev.feed;
}

static int step(arm_state *st, long s, long x, long h, unsigned long long now)
{
    return step2(st, s, x, h, now, NULL);
}

// one accepted line with the whole event out, for the boundary the line crossed
static void step_ev(arm_state *st, long s, long x, long h, unsigned long long now, arm_events *ev)
{
    arm_line ln;
    ln.s = s;
    ln.x = x;
    ln.h = h;
    arm_feed_step(st, &ln, now, ev);
}

static int self(void)
{
    // ---- 1. the line ---------------------------------------------------------------------------------
    ok(parses("s=12;x=1840;h=97", 12, 1840, 97), "parse: a full line reads its three fields");
    ok(parses("x=5;s=1;h=2", 1, 5, 2), "parse: the keys may come in any order");
    ok(parses("s=2147483647;x=2147483647;h=2147483647", 2147483647L, 2147483647L, 2147483647L),
       "parse: the largest int the gsc can hold is taken");
    ok(refuses("s=1;x=2"), "parse: a line with no h is refused");
    ok(refuses("s=1;x=2;h=3;z=4"), "parse: an unknown key is refused");
    ok(refuses("s=1;s=2;x=0;h=0"), "parse: a key twice is refused");
    ok(refuses("s=1;x=2;h="), "parse: a field with no digits is refused");
    ok(refuses("s=1;x=2147483648;h=0"), "parse: a value past the int is refused");
    ok(refuses(""), "parse: an empty line is refused");
    ok(refuses("s=1;x=2;h=3;"), "parse: a trailing separator is refused");
    ok(refuses("S=1;x=2;h=3"), "parse: an upper case key is refused");
    ok(refuses("s=1;x=2;h=3 "), "parse: a character outside the alphabet is refused");
    {
        char big[ARMORY_MAX + 2];
        memset(big, '1', sizeof(big) - 1);
        big[sizeof(big) - 1] = '\0';
        ok(refuses(big), "parse: a line longer than the cap is refused");
    }
    ok(!arm_valid(NULL, 4), "valid: a null pointer is never a line");

    // ---- 2. the state --------------------------------------------------------------------------------
    arm_state st;
    arm_state_init(&st);
    ok(st.serial == 0 && st.pending == 0 && st.beat == 0 && st.seen_x == -1 && st.have == 0 && !st.dirty,
       "state: a fresh state has no line, no serial and nothing seen");
    ok(step(&st, 0, 0, 0, 1000) == 0 && st.serial == 0 && st.have == 0,
       "state: the dvar's own default is not a feed and moves nothing");
    ok(arm_feed_live(&st, 1000) == 0, "live: the default never makes the feed live");

    ok(step(&st, 1, 0, 1, 2000) == 1, "state: the first real line is due at once");
    ok(st.serial == 1 && st.pending == 0 && st.beat == 1 && st.seen_x == 0 && st.have == 1,
       "state: and it carries the serial the total and the beat");
    ok(step(&st, 1, 0, 2, 2100) == 0, "state: the same total with a new beat writes no second line");
    ok(step(&st, 1, 40, 3, 2500) == 0 && st.dirty == 1,
       "state: a rise inside the window waits, it is not dropped");
    long delta = 0;
    ok(step2(&st, 1, 40, 4, 3000, &delta) == 1 && st.seen_x == 40 && st.dirty == 0 && delta == 40,
       "state: once the second is up the waiting total is written with its rise");
    ok(step(&st, 1, 90, 5, 3100) == 0 && st.pending == 90,
       "state: a rise inside the window is still pending");

    // ---- 3. the serial move --------------------------------------------------------------------------
    long old_serial = st.serial;
    arm_line ln;
    ln.s = 2;
    ln.x = 0;
    ln.h = 1;
    arm_events ev;
    arm_feed_step(&st, &ln, 4000, &ev);
    ok(ev.dropped == 1 && st.drop_x == 90 && st.drop_s == old_serial,
       "serial: the move names the total the last match left behind");
    ok(ev.restart == 1 && strcmp(ev.why, "serial") == 0,
       "serial: a serial that moved is a new match of its own");
    ok(st.serial == 2 && st.pending == 0 && st.seen_x == 0 && st.dirty == 0,
       "serial: and the new match starts from nothing");
    ok(ev.feed == 1, "serial: the new match's first line is due at once, whatever the window said");
    arm_feed_step(&st, &ln, 4500, &ev);
    ok(ev.dropped == 0, "serial: the drop is said once, not on every line");
    ok(step(&st, 3, 0, 1, 5000) == 1 && st.drop_x == 0, "serial: a move with nothing pending says no drop");
    st.paid = 200;
    arm_feed_step(&st, &ln, 6000, &ev);
    ok(st.paid == 0 && st.pending == 0, "serial: a move resets what was paid this match");

    // ---- 4. a total that goes backwards --------------------------------------------------------------
    arm_state back;
    arm_state_init(&back);
    step(&back, 1, 100, 40, 1000);
    back.paid = 100;
    ln.s = 1;
    ln.x = 40;
    ln.h = 70;
    arm_feed_step(&back, &ln, 2000, &ev);
    ok(back.paid == 40 && back.pending == 0,
       "backwards: a total under what was paid lowers the paid mark, never a negative");

    // ---- 4b. a new match the serial cannot see --------------------------------------------------------
    // the mod's dvar does not survive a level load, so s reads 1 at every thread start: the beat that goes
    // back, and the total back at nothing on an early beat, are what a second match shows the hook
    arm_state bt;
    arm_state_init(&bt);
    step(&bt, 1, 0, 1, 20000);
    step(&bt, 1, 360, 123, 21000);
    arm_events ev2;
    step_ev(&bt, 1, 0, 1, 22000, &ev2);
    ok(ev2.restart == 1 && strcmp(ev2.why, "beat restart") == 0,
       "beat: a beat under the last with the same serial is a new match");
    ok(ev2.dropped == 1 && bt.drop_x == 360 && bt.drop_s == 1,
       "beat: and the match it closed leaves its total behind, not silence");
    ok(ev2.feed == 1 && ev2.delta == 0 && bt.seen_x == 0 && bt.pending == 0,
       "beat: the new match is written from nothing, never as a loss");
    ok(step(&bt, 1, 40, 4, 24000) == 1, "beat: the new match then counts from its own first rise");
    step_ev(&bt, 1, 40, 5, 25000, &ev2);
    ok(ev2.restart == 0 && ev2.feed == 0, "beat: the same total with the next beat is the same match");
    step_ev(&bt, 1, 40, 90, 26000, &ev2);
    ok(ev2.restart == 0 && ev2.feed == 0, "beat: a beat far ahead of the last is still the same match");
    // the beat still ahead of the last, the total back at nothing and the beat early
    arm_state xb;
    arm_state_init(&xb);
    step(&xb, 1, 320, 4, 30000);
    step_ev(&xb, 1, 0, 6, 31000, &ev2);
    ok(ev2.restart == 1 && ev2.dropped == 1 && xb.drop_x == 320,
       "beat: a total under the last on an early beat is a new match");
    ok(ev2.feed == 1 && ev2.delta == 0, "beat: and that line carries no loss either");
    // the same total going back late in a match is not a match, and is still never a loss
    arm_state lb;
    arm_state_init(&lb);
    step(&lb, 1, 200, 40, 40000);
    long late = -1;
    ok(step2(&lb, 1, 120, 70, 41000, &late) == 1 && late == 0,
       "backwards: a total under the last late in a match is written as no loss");
    ok(lb.seen_x == 120 && lb.pending == 120, "backwards: and the baseline follows the total down");

    // ---- 5. the liveness -----------------------------------------------------------------------------
    arm_state lv;
    arm_state_init(&lv);
    ok(arm_feed_live(&lv, 9000) == 0, "live: no line is not live");
    step(&lv, 1, 0, 1, 10000);
    ok(arm_feed_live(&lv, 10000) == 1, "live: a beat makes it live");
    ok(arm_feed_live(&lv, 11999) == 1, "live: and it stays live inside the two seconds");
    ok(arm_feed_live(&lv, 12000) == 0, "live: four missed ticks make it dead");
    step(&lv, 1, 0, 1, 12100);
    ok(arm_feed_live(&lv, 12100) == 0, "live: a frozen beat does not revive it");
    step(&lv, 1, 0, 2, 13100);
    ok(arm_feed_live(&lv, 13100) == 1, "live: the next beat does");

    printf("armory: %s - %d checks\n", FAILS == 0 ? "OK" : "FAILED", PASSES);
    return FAILS == 0 ? 0 : 1;
}

// --- the arm and the ticks ---------------------------------------------------------------------------

static char STAGED[ARMORY_MAX + 1];

static void stage(const char *line)
{
    strcpy_s(STAGED, sizeof(STAGED), line);
    ARD.value = STAGED;
}

static int arm_mode(void)
{
    // ---- 6. the arm ----------------------------------------------------------------------------------
    ok(armory_armed() == 0, "arm: nothing is armed before the client's register is offered");
    armory_arm(stub_reg, NULL, ARM_SLOT);
    ok(REG_CALLS == 1, "arm: the register is asked exactly once");
    ok(armory_armed() == 1, "arm: the feed is armed once the call returned");
    ok(strcmp(REG_DEF, ARMORY_DEFAULT) == 0, "arm: the dvar is created with s=0;x=0;h=0");
    ok(ARD.value != NULL && strcmp(ARD.value, ARMORY_DEFAULT) == 0, "arm: the value slot holds that line");
    ok(LOGS == 1 && strcmp(LAST_LOG, "armory: registered pt_armory_xp = s=0;x=0;h=0") == 0,
       "arm: the registered line names the dvar and its default");

    // ---- 7. the ticks --------------------------------------------------------------------------------
    stage(ARMORY_DEFAULT);
    armory_tick();
    ok(LOGS == 1, "tick: the dvar's own default writes nothing");

    stage("s=1;x=0;h=1");
    armory_tick();
    ok(LOGS == 3 && strcmp(LOGS_ALL[1], "armory: feed s=1 x=0 h=1 (+0)") == 0
           && strcmp(LOGS_ALL[2], "armory: live=1 s=1 x=0 h=1") == 0,
       "tick: the first line of a match is logged, then its liveness");

    armory_tick();
    ok(LOGS == 3, "tick: the same line again writes nothing");

    stage("s=1;x=250;h=3");
    armory_tick();
    ok(LOGS == 3, "tick: a rise inside the one second window waits");

    Sleep(1100);
    armory_tick();
    ok(LOGS == 4 && strcmp(LAST_LOG, "armory: feed s=1 x=250 h=3 (+250)") == 0,
       "tick: the waiting total is written once the window is up, with its rise");

    stage("s=2;x=0;h=1");
    armory_tick();
    ok(LOGS == 6 && strcmp(LOGS_ALL[4], "armory: dropped 250 at s=1 (serial)") == 0
           && strcmp(LOGS_ALL[5], "armory: feed s=2 x=0 h=1 (+0)") == 0,
       "tick: the next match drops what the last one left and starts again");

    stage("s=");
    armory_tick();
    ok(LOGS == 7 && strcmp(LAST_LOG, "armory: refused a line a reader would not take") == 0,
       "tick: a line that is not the feed is said once");
    armory_tick();
    ok(LOGS == 7, "tick: and not again on the next tick");
    ok(armory_armed() == 1, "tick: a refused line leaves the feed armed");

    printf("armory: %s - %d checks\n", FAILS == 0 ? "OK" : "FAILED", PASSES);
    return FAILS == 0 ? 0 : 1;
}

// --- the pay: a fabricated record array and a fabricated award ---------------------------------------

#define PAY_ROWS 8

static unsigned char RECS[PAY_ROWS * MASTER_STRIDE];
static arm_pay_state PS;
static arm_state ST;
static arm_pay_result RES;
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
static int ACTIVE = 0;      // what the pick channel would answer
static int ADV_POSTS = 0;   // how many advance requests the pay posted
static int ADV_ID = 0;      // the last row it posted
static int IN_ADV_OFF = 0;  // the advance kill switch as the shell would pass it

// the pick channel's one read, so the shell links without the real unit
int pick_active(void)
{
    return ACTIVE;
}

// and its one write: the request the tick would serve
void pick_request_advance(int done_id)
{
    if (done_id > 0)
    {
        ADV_POSTS++;
        ADV_ID = done_id;
    }
}

// one row of the fabricated array
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
    *(int *)(r + ARM_REC_TRIGS) = 1;
    *(unsigned *)(r + ARM_REC_TRIG) = trig;
}

// 0 the active row 1 another armory row 2 a weapon row 3 a complete armory row 4 no threshold 5 not ours 6 7 spares
static void rows_init(void)
{
    row_init(0, 75680, 368, 1, 150000, 0, 0, 200067);
    row_init(1, 75669, 368, 1, 250000, 0, 1000, 200068);
    row_init(2, 90001, 398, 1, 5000, 0, 0, 0);
    row_init(3, 75681, 368, 1, 150000, 3, 150000, 200069);
    row_init(4, 75682, 368, 0, 0, 0, 0, 200070);
    row_init(5, 75683, 368, 1, 150000, 0, 0, 900001);
    row_init(6, 75684, 368, 1, 150000, 0, 0, 200071);
    row_init(7, 75685, 368, 1, 150000, 0, 0, 200072);
}

static unsigned char *row_at(int i)
{
    return RECS + (size_t)i * MASTER_STRIDE;
}

// the client's own add, faked: the row whose trigger the record names gains what was held
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
        if (*(unsigned *)(r + ARM_REC_TRIG) != (unsigned)AW_TRIG)
        {
            continue;
        }
        long take = (AW_TAKE < 0) ? *W_KILL : AW_TAKE;
        *(long long *)(r + MASTER_REC_XP) += take;
        break;
    }
    return 0;
}

// one case from a clean process state, the beat this fresh
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
    ACTIVE = 0;
    ADV_POSTS = 0;
    ADV_ID = 0;
    IN_ADV_OFF = 0;
    // anything the last case posted is written and the count starts again
    armory_pay_log();
    LOGS = 0;
}

// one look the way the shell makes it: the look then its post
static int look(unsigned long long now, int active, long pending)
{
    arm_pay_in in;
    in.active = active;
    in.off = 0;
    in.advance_off = IN_ADV_OFF;
    in.recs = RECS;
    in.n = PAY_ROWS;
    ST.pending = pending;
    int r = arm_pay_look(&PS, &in, &ST, now, fake_award, &KILL, &CRIT, &RES);
    if (r)
    {
        arm_pay_post(&RES);
    }
    return r;
}

static int look_off(unsigned long long now, int active, long pending)
{
    arm_pay_in in;
    in.active = active;
    in.off = 1;
    in.advance_off = IN_ADV_OFF;
    in.recs = RECS;
    in.n = PAY_ROWS;
    ST.pending = pending;
    int r = arm_pay_look(&PS, &in, &ST, now, fake_award, &KILL, &CRIT, &RES);
    if (r)
    {
        arm_pay_post(&RES);
    }
    return r;
}

static int pay_mode(void)
{
    rows_init();
    LOGS = 0;

    // ---- 8. the row walk -----------------------------------------------------------------------------
    ok(arm_row_find(RECS, PAY_ROWS, 75680) == 0 && arm_row_find(RECS, PAY_ROWS, 75685) == 7,
       "row: the walk finds a row by the id at its own first eight bytes");
    ok(arm_row_find(RECS, PAY_ROWS, 0) == -1 && arm_row_find(RECS, PAY_ROWS, 42) == -1
           && arm_row_find(NULL, PAY_ROWS, 75680) == -1,
       "row: a zero id, an absent id and no array are all no row");
    ok(arm_row_ours(row_at(0)) == 1 && arm_row_ours(row_at(2)) == 0 && arm_row_ours(row_at(5)) == 0,
       "row: ours is a kind 368 row with a private trigger and nothing else");
    ok(arm_row_top(row_at(0)) == 150000 && arm_row_top(row_at(4)) == -1,
       "row: the last threshold is the row own and a zero count is not one");
    ok(arm_row_complete(row_at(3)) == 1 && arm_row_complete(row_at(0)) == 0,
       "row: complete is the client own status or the xp past the last threshold");

    // ---- 9. the happy path ---------------------------------------------------------------------------
    pay_setup(10000);
    int did = look(10000, 75680, 1200);
    ok(did == 1 && RES.why == ARM_PAY_DONE, "pay: one look with something owed pays");
    ok(AW_CALLS == 1, "pay: the client award is called exactly once");
    ok(AW_TRIG == 200067 && AW_N == 0, "pay: the record is the row own private trigger with no entries");
    ok(AW_TAIL_ZERO == 1, "pay: the rest of the 0x200 block is zero");
    ok(AW_KILL == 1200 && AW_CRIT == 0, "pay: the amount held is the pending total and the crit is zero");
    ok(arm_row_xp(row_at(0)) == 1200, "pay: the active row gains exactly that amount");
    ok(arm_row_xp(row_at(1)) == 1000 && arm_row_xp(row_at(2)) == 0 && arm_row_xp(row_at(3)) == 150000,
       "pay: every other row is untouched");
    ok(KILL == 7 && CRIT == 5, "pay: both globals read back what they held before the call");
    ok(ST.paid == 1200 && ST.pending == 0, "pay: the paid mark and the pending follow the read back");
    ok(RES.id == 75680 && RES.held == 1200 && RES.got == 1200 && RES.progress == 1200 && RES.top == 150000,
       "pay: the result carries the row the amount the rise and the bar");
    armory_pay_log();
    ok(LOGS == 1 && strcmp(LAST_LOG, "armory: paid row=75680 +1200 -> 1200/150000") == 0,
       "pay: the paid line names the row the rise and the bar");

    // ---- 10. the rate limit --------------------------------------------------------------------------
    pay_setup(10000);
    look(10000, 75680, 500);
    look(10500, 75680, 500);
    ok(AW_CALLS == 1, "pay: a second look inside the second does not pay");
    look(11000, 75680, 500);
    ok(AW_CALLS == 2, "pay: a look a second after the last one pays again");

    // ---- 11. the gates -------------------------------------------------------------------------------
    pay_setup(10000);
    ok(look(10000, 0, 900) == 0 && AW_CALLS == 0, "pay: no pick pays nothing");
    ok(look(11000, 75680, 0) == 0 && AW_CALLS == 0, "pay: nothing owed pays nothing");
    ok(look(12000, 90001, 900) == 0 && AW_CALLS == 0, "pay: a weapon row the pick names pays nothing");
    ok(look(13000, 75683, 900) == 0 && AW_CALLS == 0, "pay: a row outside the private triggers pays nothing");
    ok(look(14000, 75682, 900) == 0 && AW_CALLS == 0, "pay: a row with no threshold pays nothing");
    ok(look(15000, 99999, 900) == 0 && AW_CALLS == 0, "pay: an id the array does not hold pays nothing");
    pay_setup(10000);
    ok(look(13000, 75680, 900) == 0 && AW_CALLS == 0, "pay: a beat older than the window pays nothing");
    ok(look_off(10000, 75680, 900) == 0 && AW_CALLS == 0, "pay: the kill switch pays nothing");

    // ---- 12. the complete row ------------------------------------------------------------------------
    pay_setup(10000);
    ok(look(10000, 75681, 900) == 1 && RES.why == ARM_PAY_COMPLETE && AW_CALLS == 0,
       "pay: a complete row is named and never paid");
    ok(ADV_POSTS == 1 && ADV_ID == 75681, "advance: a complete row posts exactly one advance");
    armory_pay_log();
    ok(LOGS == 1 && strcmp(LAST_LOG, "armory: row 75681 complete") == 0,
       "pay: the complete line names the row");
    look(11000, 75681, 900);
    armory_pay_log();
    ok(LOGS == 1, "pay: the complete line is said once for the same row");
    ok(ADV_POSTS == 1, "advance: and the row is posted once, not once a look");

    // ---- 13. the read back is the credit -------------------------------------------------------------
    pay_setup(10000);
    AW_TAKE = 800;
    look(10000, 75684, 1200);
    ok(RES.why == ARM_PAY_SHORT && RES.got == 800, "pay: a rise under the held amount is not the amount held");
    ok(arm_row_xp(row_at(6)) == 800 && ST.paid == 800 && ST.pending == 400,
       "pay: the credit follows the read back and the pending keeps the rest");
    armory_pay_log();
    ok(LOGS == 1 && strcmp(LAST_LOG, "armory: pay short row=75684 moved 800 of 1200 -> 800/150000") == 0,
       "pay: the short line names what moved and what was wanted");
    pay_setup(10000);
    AW_TAKE = 0;
    look(10000, 75685, 1000);
    ok(RES.why == ARM_PAY_SHORT && RES.got == 0 && ST.paid == 0 && ST.pending == 1000,
       "pay: a row that does not move is never credited");

    // ---- 14. the fault -------------------------------------------------------------------------------
    pay_setup(10000);
    AW_FAULT = 1;
    int caught = 0;
    __try
    {
        look(10000, 75684, 700);
    }
    __except (EXCEPTION_EXECUTE_HANDLER)
    {
        caught = 1;
    }
    ok(caught == 0, "pay: a fault in the award does not escape the look");
    ok(RES.why == ARM_PAY_FAULT && PS.latched == 1, "pay: a fault latches the pay off");
    ok(KILL == 7 && CRIT == 5, "pay: both globals read back what they held after the fault");
    ok(ST.paid == 0 && ST.pending == 700 && arm_row_xp(row_at(6)) == 0, "pay: a fault pays nothing");
    armory_pay_log();
    ok(LOGS == 1 && strcmp(LAST_LOG, "armory: pay latched off after a fault in the award") == 0,
       "pay: the fault is one line");
    AW_FAULT = 0;
    ok(look(12000, 75685, 500) == 0 && AW_CALLS == 1, "pay: a latched pay never looks again");

    // ---- 15. the advance that follows a payment which finished the row ------------------------------
    pay_setup(10000);
    ok(look(10000, 75680, 150000) == 1 && RES.why == ARM_PAY_DONE && ADV_POSTS == 0,
       "advance: the payment that finishes a row posts nothing itself");
    ok(arm_row_complete(row_at(0)) == 1, "advance: the row it just paid reads complete");
    AW_CALLS = 0;
    ok(look(11000, 75680, 500) == 1 && RES.why == ARM_PAY_COMPLETE && AW_CALLS == 0,
       "advance: the completed row is never paid a second time");
    ok(ADV_POSTS == 1 && ADV_ID == 75680, "advance: the look that sees it complete posts it once");
    look(12000, 75680, 500);
    ok(ADV_POSTS == 1, "advance: and a later look posts it no more");
    pay_setup(10000);
    *(unsigned char *)(row_at(6) + ARM_REC_STATUS) = 3;
    IN_ADV_OFF = 1;
    ok(look(10000, 75684, 900) == 1 && RES.why == ARM_PAY_COMPLETE && ADV_POSTS == 0,
       "advance: the advance kill switch leaves the completion unposted");
    IN_ADV_OFF = 0;
    ok(look(11000, 75684, 900) == 1 && ADV_POSTS == 1 && ADV_ID == 75684,
       "advance: with the switch clear that row posts its advance");

    printf("armory: %s - %d checks\n", FAILS == 0 ? "OK" : "FAILED", PASSES);
    return FAILS == 0 ? 0 : 1;
}

int main(int argc, char **argv)
{
    if (argc >= 2 && strcmp(argv[1], "self") == 0)
    {
        return self();
    }
    if (argc >= 2 && strcmp(argv[1], "arm") == 0)
    {
        return arm_mode();
    }
    if (argc >= 2 && strcmp(argv[1], "pay") == 0)
    {
        return pay_mode();
    }
    if (argc >= 3 && strcmp(argv[1], "off") == 0)
    {
        wchar_t dir[MAX_PATH];
        MultiByteToWideChar(CP_ACP, 0, argv[2], -1, dir, MAX_PATH);
        printf("%d\n", arm_feed_off_present(dir));
        return 0;
    }
    if (argc >= 3 && strcmp(argv[1], "payoff") == 0)
    {
        wchar_t dir[MAX_PATH];
        MultiByteToWideChar(CP_ACP, 0, argv[2], -1, dir, MAX_PATH);
        printf("%d\n", arm_pay_off_present(dir));
        return 0;
    }
    if (argc >= 3 && strcmp(argv[1], "advoff") == 0)
    {
        wchar_t dir[MAX_PATH];
        MultiByteToWideChar(CP_ACP, 0, argv[2], -1, dir, MAX_PATH);
        printf("%d\n", arm_advance_off_present(dir));
        return 0;
    }
    printf("usage: armory_test self | arm | pay | off <dir> | payoff <dir> | advoff <dir>\n");
    return 2;
}
