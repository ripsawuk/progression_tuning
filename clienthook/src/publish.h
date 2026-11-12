// clienthook - the forced publish: the client's own challenge-state serialiser, called by this DLL.
//
// WHY THIS EXISTS. The client serialises its challenge record on its own schedule - at a mode boundary - and the
// reader on the other side of the channel rebuilds its copy only when the published serial moves. So a row that
// advances while a match runs is a frozen number on screen until the next boundary. Calling the client's own
// serialiser from a thread of ours changes only WHEN the snapshot is taken: the state, the chunking, the serial
// and the dvars are the client's, and no byte of the client's code is written.
//
// The guard. The target is one address (the resolver's `pub` symbol, which is `client + 0x962e0` on the build
// this was measured on), so it is checked before EVERY call: the bytes must be readable memory (VirtualQuery,
// because a client build smaller than that address would otherwise fault here) and their first 24 must equal
// PUB_SIG, taken from the pinned client build. A mismatch turns this feature off for the session with one log
// line and touches nothing else - the payment, the paid-XP payload, the lock payload and the level hook keep
// running exactly as they did.
//
// THE DISCIPLINE. One caller (a thread of this DLL), one call at a time, and the caller holds no lock of the
// client's while it calls: the serialiser acquires the record lock itself and releases it before it writes the
// first dvar, and it raises on a recursive acquire - so a thread that holds nothing is the caller it is written
// for. The window is PUB_MIN_MS between call starts. A want raised inside the window is KEPT, not dropped, and
// is honoured on the first tick after the window closes: nothing is lost, only deferred.
//
// WHAT RAISES A WANT.
//   1. A paid `ev=95`. The payment's own hook runs after the client's award returned, so the record has moved.
//   2. A record scan. A fingerprint over every record's progress, status/level and prestige bytes, compared at
//      most once per PUB_MIN_MS and only while a match is live. This exists because rows other than the weapon
//      ladder - camo tiers, dailies, weeklies - are credited by their own events and can move with no `ev=95`
//      at all, so a payment-only trigger would leave them frozen.
//
// THE KILL SWITCH is a file, not a setting: `%TEMP%\progression-tuning\publish_off.txt`, the same mechanism as
// the payment's and the master hook's. Present at start = this feature never runs and says so in one line.
//
// Everything here is pure: no client address is read in this file, so the whole gate is proved offline. The one
// system call it makes is VirtualQuery, which is what makes the guard's own read safe on an unknown build.

#ifndef PUBLISH_H
#define PUBLISH_H

#include <windows.h>

#include "master.h" // MASTER_STRIDE / MASTER_REC_* - one source for the record's numbers

#define PUB_RVA 0x962E0u    // the client's serialise-and-publish, in the pinned client build
#define PUB_SIG_LEN 24      // the prologue compared before every call
#define PUB_MIN_MS 1000     // the floor between two call starts
#define PUB_LOG_EACH 20     // the publish line: the first 3, then every 20th

// The 24 bytes at PUB_RVA in the pinned client build. A different client cannot pass this.
extern const unsigned char PUB_SIG[PUB_SIG_LEN];

// What one tick's decision was. Only PUB_CALL licenses a call: everything else is a reason not to make one.
typedef enum
{
    PUB_IDLE = 0,     // nothing wanted, or the feature is latched off
    PUB_COALESCED = 1,// wanted, but inside the window - the want stays set
    PUB_REFUSED = 2,  // wanted, window closed, and the guard failed: latched off for the session
    PUB_CALL = 3      // wanted, window closed, guard passed: the caller calls, once
} PUB_VERDICT;

typedef struct
{
    volatile LONG want;   // raised by the paid hook and by the record scan
    volatile LONG off;    // latched off: the guard failed, the module was gone, or the kill switch was present
    volatile LONG done;   // calls made
    volatile LONG skip;   // ticks that found a want inside the window
    volatile LONG live;   // a match has started (the match-start event reached the payment's own call site)
    unsigned long long last_ms;   // start of the last call, 0 = none yet
    unsigned long long scan_ms;   // the last record scan, 0 = none yet
    unsigned long long fp;        // the last record fingerprint
    int have_fp;                  // 0 = fp is not yet a baseline
} PUB_GATE;

void pub_init(PUB_GATE *g);

// The two triggers. Both are one interlocked store: safe on a thread that may not open a file or take a lock.
void pub_want(PUB_GATE *g);
void pub_match_live(PUB_GATE *g);

// 1 when <tempdir>\progression-tuning\publish_off.txt exists. tempdir NULL = the process's %TEMP%.
int pub_off_present(const wchar_t *tempdir);

// 1 when the 24 bytes at `at` are PUB_SIG. NULL, and memory this process may not read, are not a match.
int pub_sig_ok(const unsigned char *at);

// The decision. `at` is the client's serialiser (client + PUB_RVA) or NULL when the client is not loaded.
// Side effects, all of them the caller's business afterwards: a want inside the window increments `skip`; a
// failure latches `off`; a call clears `want`, records `last_ms` and increments `done`.
PUB_VERDICT pub_step(PUB_GATE *g, unsigned long long now_ms, const unsigned char *at);

// 1 at most once per PUB_MIN_MS: the record scan's own clock.
int pub_scan_due(PUB_GATE *g, unsigned long long now_ms);

// One number over every record's progress (8 B), status+level (2 B) and prestige (1 B) bytes. Any row that moves
// changes it; a record array that cannot be read is the caller's to detect (0 is also "no records").
unsigned long long pub_fingerprint(const unsigned char *records, int count);

// Compares `fp` with the last one. The first call only takes the baseline (0). A change while a match is live
// raises the want and returns 1; a change outside a match only re-baselines (0).
int pub_note_fingerprint(PUB_GATE *g, unsigned long long fp);

#endif // PUBLISH_H
