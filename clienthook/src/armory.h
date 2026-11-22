// clienthook - the armory xp feed read from the mod dvar and the pay it feeds
//
// the mod gsc publishes s x and h every half second the match serial the xp
// this match has earned and a beat count this unit parses that line and logs
// the feed when x moves the pay holds the unpaid total in the award two
// globals for one call of the client own award and pays it into the one
// active row the pick channel names by that row own private trigger
// the pay runs on the client drain thread under its store lock and opens no
// file what it paid is posted to the frame thread and written there

#ifndef ARMORY_H
#define ARMORY_H

#include <stddef.h>

#include "g11.h"
#include "nativepay.h"

// one ascii line of s=<serial>;x=<xp this match>;h=<beat>
#define ARMORY_NAME "pt_armory_xp"
#define ARMORY_MAX 64
#define ARMORY_DEFAULT "s=0;x=0;h=0"
// the beat is stale after four missed half second ticks
#define ARMORY_LIVE_MS 2000
// one feed line per this window after the first
#define ARMORY_LOG_MS 1000
// a beat this early with a total below the last is a new match
#define ARMORY_SMALL_H 8

// the row numbers the pay reads out of the client own array
#define ARM_REC_TRIG 0x480     // the first u32 trigger
#define ARM_REC_TRIGS 0x490    // how many triggers the row carries
#define ARM_REC_STATUS 0x56D   // the client own status byte 3 = complete
#define ARM_KIND_ARMORY 368    // the armory row kind
#define ARM_TRIG_FIRST 200001  // the ladder own first private trigger
#define ARM_TRIG_LAST 200076   // and the last of the 76 rows
#define ARM_REC_MAX 20000      // a larger array is not the game challenge table
// one look a second at most so the walk and the payments stay bounded
#define ARM_PAY_MIN_MS 1000

// what one look decided
#define ARM_PAY_NONE 0      // nothing owed
#define ARM_PAY_DONE 1      // paid and the read back matched
#define ARM_PAY_SHORT 2     // the row moved less than the amount held
#define ARM_PAY_COMPLETE 3  // the row reads complete
#define ARM_PAY_FAULT 4     // a fault latched the pay off for the process
#define ARM_PAY_NOTE 5      // a second thread was inside the window
#define ARM_PAY_PAUSE 6     // unlock armory came on so the pay stopped
#define ARM_PAY_RESUME 7    // unlock armory went off so the pay runs again

// the three fields of one line
typedef struct
{
    long s;
    long x;
    long h;
} arm_line;

// the feed as this process knows it
typedef struct
{
    long serial;                  // s of the last accepted line 0 = none yet
    long paid;                    // xp already paid this match 0 until a pay exists
    long pending;                 // x - paid
    long beat;                    // h of the last accepted line
    long seen_x;                  // the x of the last feed line -1 none yet
    long drop_x;                  // the pending a serial move left behind
    long drop_s;                  // and the serial it belonged to
    int dirty;                    // the feed moved and waits for its window
    int live;                     // 1 while the beats are fresh 0 when stale
    int have;                     // a line has been accepted at least once
    unsigned long long beat_ms;   // when h last moved
    unsigned long long log_ms;    // when the last feed line was written
} arm_state;

// what one accepted line asks the caller to log
typedef struct
{
    int dropped;   // 1 = the drop line first st holds its numbers
    int feed;      // 1 = the feed line
    long delta;    // the feed line rise over the last line written
    int restart;   // 1 when the line began a new match
    const char *why; // the boundary the line crossed
} arm_events;

// what one pay look is handed
typedef struct
{
    int active;                 // pick_active() 0 = nothing picked
    int unlocked;               // pick_unlocked() 1 = unlock armory on
    int off;                    // the pay kill switch
    int advance_off;            // the advance kill switch
    const unsigned char *recs;  // the client record array
    int n;                      // how many records it holds
} arm_pay_in;

// what one pay look decided and what the read back answered
typedef struct
{
    int why;              // ARM_PAY_*
    int id;               // the row looked at 0 = none
    long held;            // the amount put in the award global
    long got;             // the row own rise read back
    long long progress;   // the row xp after the call
    long long top;        // the row last threshold
} arm_pay_result;

// the pay as this process knows it
typedef struct
{
    unsigned long long last_look; // the look clock
    int latched;                  // a fault latched the pay off
    int paused;                   // 1 while unlock armory is on
} arm_pay_state;

// 1 when s is a line this unit can read
int arm_valid(const char *s, size_t n);
// the three fields out of one line 1 = read
int arm_parse(const char *s, size_t n, arm_line *out);

// the state before any line
void arm_state_init(arm_state *st);
// one line the serial the pending the beat and the due
void arm_feed_step(arm_state *st, const arm_line *ln, unsigned long long now, arm_events *ev);
// 1 while h moved within ARMORY_LIVE_MS
int arm_feed_live(arm_state *st, unsigned long long now);

// the row walk over the client own array
int arm_row_find(const unsigned char *recs, int n, int id);
int arm_row_ours(const unsigned char *row);
long long arm_row_top(const unsigned char *row);
long long arm_row_xp(const unsigned char *row);
int arm_row_complete(const unsigned char *row);

// one look the gates then the hold the call and the read back
int arm_pay_look(arm_pay_state *ps, const arm_pay_in *in, arm_state *st, unsigned long long now,
                 np_fn orig, int *kill, int *crit, arm_pay_result *out);
// one result posted to the frame thread own log pass
void arm_pay_post(const arm_pay_result *r);
// the frame tick writes what the pay posted
void armory_pay_log(void);
// the nativepay seam on the client drain thread after its own award returned
void armory_pay(np_fn orig, int *kill, int *crit);

// register the dvar with the default or find it
void armory_arm(G11_REG reg, const unsigned char salt[16], long slot);
// the frame tick read the dvar and log what moved
void armory_tick(void);
int armory_armed(void);
// 1 when the feed kill switch file is there
int arm_feed_off_present(const wchar_t *tempdir);
// 1 when the pay kill switch file is there
int arm_pay_off_present(const wchar_t *tempdir);
// 1 when the advance kill switch file is there
int arm_advance_off_present(const wchar_t *tempdir);

#endif
