// clienthook - the PAID weapon XP, published into one dvar. This is the PURE half: the text format, the per-gun
// ledger, the match ledger and the record lookup. Nothing in this file reads a client address, so the offline
// driver proves all of it with a fabricated record array.
//
// WHAT IS PUBLISHED. The client's own record XP after each payment - never a delta added to a base:
//
//     ptsplash_paid = "v1;102705:4539:4539;98753:473:473;..."          loot:total:thisMatch
//
//   total      = `rec+0x560` read immediately AFTER the wrapped award returned. That record is the profile
//                mid-match - the level byte is derived from it and the store writer copies it - so a reader
//                needs no base, no delta and no boundary.
//   thisMatch  = total minus the same record's value captured BEFORE the first payment of the level, i.e. since
//                the last `ev=109` (the boundary is the event frame.c's ae_on_rec acts on).
//                It is recomputed from the two absolutes, never accumulated, so it cannot double count.
//
// THE RECORD, and how each offset is used by the client:
//
//   array base   `*(void**)(client+0x3DD288)`   the `add rdi,[rip+...]` at rva 0x93BFD resolves to it
//   array count  `*(int*)(client+0x3DD290)`     the `mov r11d,[rip+...]` that follows
//   stride       0x578                          the `imul rdi, rax, 0x578` at rva 0x93BF6
//   +0x08  int   kind, 398 = a weapon ladder     what the client checks before it derives a level
//   +0x54  uint  owner id, the weapon's loot id  the client's own `W` filter: a cmp against the event's
//                                                field 0x2c
//   +0x480 uint[] trigger AE event ids           up to four, the ids that move this row
//   +0x490 int   trigger count                   how many of those four are set
//   +0x560 i64   progress / XP                   `add qword ptr [rdi+0x560], rax` when the award pays
//
// The lookup is the client's own selection for this event (owner == the event's field 44, and the event id 95 in
// the trigger list), plus the kind filter. A record that matches owner and event but not the kind is reported
// through `kind_seen` instead of being used, so a client build that disagrees with this description says so in
// one line rather than publishing a camo row's XP.
//
// BOUNDS. `PXP_MAX` guns (the mod's own `ptsplash_c` cap). A ninth loot id is NOT added - it keeps
// being paid by the client, it is simply not in the text - so the payload has a hard ceiling:
// 4 + 8 * (10 + 1 + 20 + 1 + 20 + 1) = 428 characters inside `PXP_TEXT_MAX`.

#ifndef PXP_H
#define PXP_H

#include "master.h"   // MASTER_STRIDE / MASTER_RECS_RVA / ... - one source for the record's numbers

#define PXP_MAX 8
#define PXP_TEXT_MAX 512
#define PXP_VERSION "v1"        // the payload's prefix: a reader that does not know "v1" must not guess
#define PXP_PROBE "probe"       // what is published at attach, before any payment, so the channel proves itself

// The event the payment is about, and the record's own selection fields.
#define PXP_EVENT_XP 0x5Fu          // ev=95, the weapon-XP event (mp_addxp), the same id nativepay.h uses
// The trigger list is FOUR uints wide, not more: `+0x480` to `+0x490` is 16 bytes, and the count sits in the
// last 4 of them (the client appends an AE event id to it, up to four).
// So a count above 4 is a corrupt record and only the first four ids are ids at all - reading an eighth would
// read the requirement count.
#define PXP_EVENTS_MAX 4
#define PXP_REC_KIND MASTER_REC_KIND       // +0x08
#define PXP_REC_OWNER 0x54                 // +0x54, the client's `W` filter target
#define PXP_REC_EVENTS 0x480               // +0x480, uint[4]
#define PXP_REC_EVENT_N 0x490              // +0x490, int
#define PXP_REC_XP MASTER_REC_XP           // +0x560
#define PXP_KIND_WEAPON MASTER_KIND_WEAPON // 398

// One gun, keyed by the loot id the event carried (never by a row id: the mod maps loot -> row itself).
typedef struct
{
    unsigned loot;
    long long total;      // rec+0x560 as last read (the absolute profile total)
    long long base;       // rec+0x560 before the first payment of this match (has_base)
    int has_base;
    int rec;              // the record index last found, -1 = unknown
    unsigned long payments;
} PXP_GUN;

typedef struct
{
    PXP_GUN g[PXP_MAX];
    int n;
    unsigned long dropped;      // payments for a loot id past the cap (counted, never published)
    char text[PXP_TEXT_MAX];    // what pxp_render last built
    char shown[PXP_TEXT_MAX];   // what was actually stored into the dvar
} PXP_LEDGER;

// One payment's own verdicts, so the caller can log the two things that would invalidate the channel:
// `capped`  - the gun is past the 8-gun cap (paid anyway, not shown);
// `mismatch`- the record moved by something other than the amount paid (`after - before != paid`), which is the
//             one future change that would make `total` a lie, so it is checked on every payment.
typedef struct
{
    int added;
    int capped;
    int mismatch;
} PXP_NOTE;

void pxp_init(PXP_LEDGER *L);
int pxp_index(const PXP_LEDGER *L, unsigned loot);

// One payment: `before` was read before the award ran, `after` immediately after it, `paid` is what the wrapper
// told the client to pay. Returns 1 when the ledger's text now differs from what the dvar holds (so the caller
// writes, and only then). `out` may be NULL.
int pxp_note(PXP_LEDGER *L, unsigned loot, long long before, long long after, int paid, PXP_NOTE *out);

// `ev=109`: this match is over. Every gun keeps its absolute total and loses its base, so `thisMatch` renders 0
// until the next payment sets a new base. Returns 1 when the text changed (i.e. something is worth publishing) -
// and 0 without touching anything when no gun has a base, which is what makes a second notification for the same
// boundary a no-op (see the implementation's comment).
int pxp_reset_match(PXP_LEDGER *L);

// Builds L->text; 1 = it differs from L->shown (write), 0 = identical (do not touch the dvar).
int pxp_render(PXP_LEDGER *L);
// Records that L->text is now what the dvar holds. Only the caller of the store may call this.
void pxp_shown(PXP_LEDGER *L);

// The record for `loot`: kind 398, owner == loot, and PXP_EVENT_XP in its trigger list. -1 when there is none.
// `kind_seen`, when non-NULL, receives the kind of the first record that matched owner and event but was not
// 398 (0 when there was no such record) - the diagnostic for a build that disagrees with this description.
int pxp_find_record(const unsigned char *records, int count, unsigned loot, int *kind_seen);
long long pxp_record_xp(const unsigned char *record);

#endif // PXP_H
