// Offline driver for src\pubxp.c (clienthook build 20): the publish format, the cap, the change-only rule, the
// match reset, and the record lookup over a fabricated record array. Nothing here touches the game.
//
//   pubxp_test.exe self
//
// Exit 0 when every check passes; prints "pubxp: OK - <n> checks" on the last line, like the other drivers here.

#include <stdio.h>
#include <string.h>

#include "../src/pubxp.h"

static int PASS = 0;
static int FAIL = 0;

static void ok(int cond, const char *name)
{
    if (cond)
    {
        PASS++;
        printf("pass  %s\n", name);
    }
    else
    {
        FAIL++;
        printf("FAIL  %s\n", name);
    }
}

// one record in a fabricated array, at `rec` (0x578 bytes of it)
static void rec_init(unsigned char *rec, int kind, unsigned owner, const unsigned *ev, int n, long long xp)
{
    memset(rec, 0, MASTER_STRIDE);
    memcpy(rec + PXP_REC_KIND, &kind, sizeof(int));
    memcpy(rec + PXP_REC_OWNER, &owner, sizeof(unsigned));
    memcpy(rec + PXP_REC_EVENT_N, &n, sizeof(int));
    for (int i = 0; i < n && i < 16; i++)
    {
        memcpy(rec + PXP_REC_EVENTS + (size_t)i * 4, &ev[i], sizeof(unsigned));
    }
    memcpy(rec + PXP_REC_XP, &xp, sizeof(long long));
}

static int self(void)
{
    PXP_LEDGER L;
    PXP_NOTE note;

    // ---- 1. the format -------------------------------------------------------------------------------
    pxp_init(&L);
    ok(L.n == 0 && L.dropped == 0, "ledger: init leaves it empty");
    ok(pxp_render(&L) == 1 && strcmp(L.text, "v1;") == 0, "format: an empty ledger renders \"v1;\"");
    pxp_shown(&L);
    ok(pxp_render(&L) == 0, "change-only: rendering the same thing again needs no write");

    // the design's own example (DESIGN 2.2): two guns, absolute totals
    {
        pxp_init(&L);
        ok(pxp_note(&L, 102705, 4526, 4539, 13, &note) == 1 && note.added && !note.capped && !note.mismatch,
           "ledger: the first payment adds the gun and asks for a write");
        ok(strcmp(L.text, "v1;102705:4539:13") == 0, "format: loot:total:thisMatch, version-prefixed");
        pxp_shown(&L);
        ok(pxp_note(&L, 102705, 4539, 4539 + 190, 190, &note) == 1, "ledger: the second payment changes the text");
        ok(strcmp(L.text, "v1;102705:4729:203") == 0, "format: total is absolute, thisMatch is total - base");
        pxp_shown(&L);
        ok(pxp_note(&L, 102705, 4729, 4729, 0, &note) == 0, "change-only: a payment that moves nothing writes nothing");
        pxp_note(&L, 98753, 0, 473, 473, &note);
        ok(strcmp(L.text, "v1;102705:4729:203;98753:473:473") == 0,
           "format: two guns, insertion order, ';' between entries");
    }

    // ---- 2. the cap ---------------------------------------------------------------------------------
    {
        pxp_init(&L);
        for (int i = 0; i < PXP_MAX; i++)
        {
            pxp_note(&L, 400000 + (unsigned)i, 0, 100, 100, &note);
        }
        ok(L.n == PXP_MAX && L.dropped == 0, "cap: eight guns are all published");
        int len8 = (int)strlen(L.text);
        ok(pxp_note(&L, 999999, 0, 50, 50, &note) == 0 && note.capped && L.dropped == 1 && L.n == PXP_MAX,
           "cap: the ninth loot id is counted, not added, and asks for no write");
        ok(strstr(L.text, "999999") == NULL, "cap: the ninth gun is not in the payload");
        ok(pxp_note(&L, 400000, 100, 200, 100, &note) == 1 && !note.capped,
           "cap: a gun already published keeps updating");
        ok(len8 < PXP_TEXT_MAX && (int)strlen(L.text) < PXP_TEXT_MAX, "cap: the payload stays inside PXP_TEXT_MAX");
        pxp_init(&L);
        for (int i = 0; i < PXP_MAX; i++)
        {
            pxp_note(&L, 4000000000u - (unsigned)i, 0, 999999999999LL, 1, &note);
        }
        ok((int)strlen(L.text) < PXP_TEXT_MAX,
           "cap: the worst-case text (10-digit loot, 12-digit totals) still fits");
        printf("      worst case: %d chars (cap %d)\n", (int)strlen(L.text), PXP_TEXT_MAX);
    }

    // ---- 3. the match reset (ev=109) -----------------------------------------------------------------
    {
        pxp_init(&L);
        pxp_note(&L, 700, 1000, 1200, 200, &note);
        pxp_shown(&L);
        ok(strcmp(L.text, "v1;700:1200:200") == 0, "reset: before it, thisMatch is the payment since the base");
        ok(pxp_reset_match(&L) == 1, "reset: the match boundary changes the text");
        ok(strcmp(L.text, "v1;700:1200:0") == 0, "reset: the absolute total is kept and thisMatch goes to 0");
        pxp_shown(&L);
        ok(pxp_reset_match(&L) == 0, "reset: a second boundary with nothing paid writes nothing");
        pxp_note(&L, 700, 1200, 1310, 110, &note);
        ok(strcmp(L.text, "v1;700:1310:110") == 0, "reset: the next payment's base is the total at the boundary");
    }

    // ---- 3b. idempotence: the same boundary delivered twice is one boundary ---------------------------
    //
    // Two paths can see ev=109 - the payment's wrapper (before the client's log gate) and the ae_events reader
    // (only when log_events 1) - and the DLL gives the boundary exactly one owner. The ledger itself is built to
    // make a duplicate harmless anyway: with no per-match base set there is nothing to drop.
    {
        PXP_LEDGER A, B;
        pxp_init(&A);
        pxp_note(&A, 700, 1000, 1200, 200, &note);
        pxp_note(&A, 701, 1000, 1050, 50, &note);
        pxp_shown(&A);
        B = A;
        ok(pxp_reset_match(&A) == 1, "reset-once: the first notification writes (thisMatch -> 0)");
        ok(pxp_reset_match(&B) == 1 && pxp_reset_match(&B) == 0,
           "reset-twice: two notifications for one boundary equal one (the second is a no-op)");
        ok(strcmp(A.text, B.text) == 0 && memcmp(&A.g[0], &B.g[0], sizeof(A.g[0])) == 0,
           "reset-twice: both end in the same state - the same text and the same guns");
        ok(A.g[0].total == 1200 && B.g[0].total == 1200, "reset-twice: the absolute totals are never lost");
        ok(strcmp(A.text, "v1;700:1200:0;701:1050:0") == 0, "reset-twice: every gun's thisMatch is 0");
        ok(pxp_reset_match(&A) == 0, "reset-twice: a third call is still a no-op");
    }

    // ---- 4. the self-check --------------------------------------------------------------------------
    {
        pxp_init(&L);
        ok(pxp_note(&L, 5, 500, 500, 20, &note) == 1 && note.mismatch,
           "self-check: a record that did not move is a mismatch");
        ok(L.g[0].total == 500, "self-check: the total is what the record says, never base + paid");
        ok(pxp_note(&L, 5, 500, 520, 20, &note) == 0 && !note.mismatch || L.g[0].total == 520,
           "self-check: an exact move is not a mismatch");
        ok(pxp_note(&L, 6, 900, 880, 0, &note) == 1 && note.mismatch, "self-check: a negative move is a mismatch");
        ok(strstr(L.text, "6:880:-20") != NULL, "self-check: a negative thisMatch is printed, not clamped away");
    }

    // ---- 5. the record lookup, over a fabricated array ----------------------------------------------
    {
        static unsigned char recs[256 * MASTER_STRIDE];
        int kind_seen = 0;
        const unsigned kill_only[] = {123};
        const unsigned kill_and_xp[] = {123, 95};
        const unsigned spread[] = {1, 2, 3, 4, 95};     // ev=95 at index 4 - outside the four-id list
        const unsigned last_slot[] = {1, 2, 3, 95};     // ev=95 at index 3 - the last id that exists

        // index 5 is the weapon row for loot 4242; 200 is the one at the far end of the array
        rec_init(recs + 5 * MASTER_STRIDE, PXP_KIND_WEAPON, 4242, kill_and_xp, 2, 4500);
        rec_init(recs + 200 * MASTER_STRIDE, PXP_KIND_WEAPON, 777, kill_and_xp, 2, 12);
        // a camo row on the same weapon, whose trigger list has no ev=95
        rec_init(recs + 6 * MASTER_STRIDE, 400, 4242, kill_only, 1, 831);
        // a row whose owner and event match but whose kind is not the weapon kind
        rec_init(recs + 7 * MASTER_STRIDE, 400, 4243, kill_and_xp, 2, 99);
        // a weapon row whose trigger list does not contain ev=95
        rec_init(recs + 8 * MASTER_STRIDE, PXP_KIND_WEAPON, 4244, kill_only, 1, 7);
        // ev=95 beyond the four ids the trigger list can hold
        rec_init(recs + 9 * MASTER_STRIDE, PXP_KIND_WEAPON, 4245, spread, 5, 3);
        // ev=95 at the last id that exists (index 3 of 4)
        rec_init(recs + 10 * MASTER_STRIDE, PXP_KIND_WEAPON, 4246, last_slot, PXP_EVENTS_MAX, 4);

        ok(pxp_find_record(recs, 256, 4242, &kind_seen) == 5,
           "record: the weapon row for the loot id is found by owner + kind + ev=95");
        ok(kind_seen == 0, "record: a camo row on the same weapon (no ev=95) is not even considered");
        ok(pxp_find_record(recs, 256, 4243, &kind_seen) == -1 && kind_seen == 400,
           "record: owner + ev=95 with another kind is reported, not used");
        ok(pxp_find_record(recs, 256, 4244, &kind_seen) == -1, "record: a weapon row without ev=95 is not matched");
        ok(pxp_find_record(recs, 256, 4245, &kind_seen) == -1,
           "record: ev=95 past the fourth trigger id (the count field) is not read blind");
        ok(pxp_find_record(recs, 256, 4246, &kind_seen) == 10,
           "record: ev=95 at the last trigger id that exists is matched");
        {
            // diagnostic: what the walk actually sees at that index (kept: it is the cheapest answer if this
            // check ever fails on a new reader)
            const unsigned char *r = recs + 10 * MASTER_STRIDE;
            printf("      index 10: kind=%d owner=%u events=%d xp=%lld\n", *(const int *)(r + PXP_REC_KIND),
                   *(const unsigned *)(r + PXP_REC_OWNER), *(const int *)(r + PXP_REC_EVENT_N),
                   pxp_record_xp(r));
        }
        ok(pxp_find_record(recs, 256, 777, &kind_seen) == 200,
           "record: the stride (0x578) puts record 200 where the walk expects it");
        ok(pxp_find_record(recs, 0, 4242, &kind_seen) == -1, "record: a count of 0 finds nothing");
        ok(pxp_find_record(NULL, 256, 4242, &kind_seen) == -1, "record: a NULL array finds nothing");
        ok(pxp_find_record(recs, 256, 99999, &kind_seen) == -1, "record: an absent loot id finds nothing");
        ok(pxp_record_xp(recs + 5 * MASTER_STRIDE) == 4500, "record: +0x560 is the XP");
        ok(pxp_record_xp(recs + 200 * MASTER_STRIDE) == 12, "record: +0x560 again, at the far end of the array");
        {
            long long big = 3000000000LL; // beyond 2^31: the field is an int64, not an int
            memcpy(recs + 11 * MASTER_STRIDE + PXP_REC_XP, &big, sizeof(big));
            ok(pxp_record_xp(recs + 11 * MASTER_STRIDE) == big, "record: +0x560 is read as 64-bit");
        }
        {
            int n = *(int *)(recs + 5 * MASTER_STRIDE + PXP_REC_EVENT_N);
            ok(n == 2, "record: the fabricated record really has a two-id trigger list");
        }
    }

    printf("pubxp: %s - %d checks\n", FAIL == 0 ? "OK" : "FAILED", PASS);
    return FAIL == 0 ? 0 : 1;
}

int main(int argc, char **argv)
{
    if (argc >= 2 && strcmp(argv[1], "self") == 0)
    {
        return self();
    }
    printf("usage: pubxp_test.exe self\n");
    return 2;
}
