// Offline driver for src\publish.c: the gate that decides when the client's own serialiser is called. It links
// the SHIPPED unit, so what is proved is what runs.
//
//   publish_test.exe self            the gate, the guard, the window, the kill switch and the fingerprint
//   publish_test.exe off <tempdir>   the kill switch's answer for a directory ("0" or "1")
//
// Nothing here reads a client address: the 24 bytes are a literal, and the record array is a fabricated block of
// MASTER_STRIDE records.

#include <stdio.h>
#include <string.h>

#include "..\src\publish.h"

static int PASSES = 0;
static int FAILS = 0;

static void ok(int cond, const char *what, const char *detail)
{
    int has = (detail != NULL && detail[0] != '\0');
    if (cond)
    {
        PASSES++;
    }
    else
    {
        FAILS++;
    }
    printf("%s  %s%s%s%s\n", cond ? "ok  " : "FAIL", what, has ? "  (" : "", has ? detail : "", has ? ")" : "");
}

// The client's own 24 bytes, repeated here so the shipped table is compared with the click, not with itself.
static const unsigned char WANT_SIG[PUB_SIG_LEN] = {
    0x48, 0x89, 0x5C, 0x24, 0x18, 0x55, 0x56, 0x57, 0x41, 0x54, 0x41, 0x55,
    0x41, 0x56, 0x41, 0x57, 0x48, 0x83, 0xEC, 0x30, 0x48, 0x63, 0x05, 0xBD};

// The shape of frame.c's trigger: the paid hook runs twice per payment, and only the phase after the award
// returned (1) is the one that means "the record has moved".
static void paid_hook_like(PUB_GATE *g, unsigned loot, int phase)
{
    if (phase == 1 && loot != 0)
    {
        pub_want(g);
    }
}

#define RECS 3
static unsigned char RECORD_BLOCK[(size_t)RECS * MASTER_STRIDE];

static unsigned char *rec_at(int i)
{
    return RECORD_BLOCK + (size_t)i * MASTER_STRIDE;
}

static void rec_set_xp(int i, long long xp)
{
    memcpy(rec_at(i) + MASTER_REC_XP, &xp, 8);
}

static int mode_self(void)
{
    unsigned char sig[PUB_SIG_LEN];
    memcpy(sig, WANT_SIG, PUB_SIG_LEN);

    printf("publish gate: the guard\n");
    ok(memcmp(PUB_SIG, WANT_SIG, PUB_SIG_LEN) == 0, "the shipped table is the client's own 24 bytes", "");
    ok(pub_sig_ok(sig) == 1, "the guard passes on those bytes", "");
    sig[23] ^= 0x01;
    ok(pub_sig_ok(sig) == 0, "one byte off is a mismatch", "");
    memcpy(sig, WANT_SIG, PUB_SIG_LEN);
    ok(pub_sig_ok(NULL) == 0, "a null target is not a match", "");
    {
        unsigned char buf[PUB_SIG_LEN + 4];
        memcpy(buf + 1, WANT_SIG, PUB_SIG_LEN);
        ok(pub_sig_ok(buf + 1) == 1, "an unaligned copy is still a match (24 bytes, not a word-aligned read)", "");
    }

    printf("\npublish gate: the constants\n");
    ok(PUB_MIN_MS == 1000, "the window is 1,000 ms", "");
    ok(PUB_LOG_EACH == 20, "the publish line is the first 3 then every 20th", "");
    ok(PUB_RVA == 0x962E0u, "the target is rva 0x962E0", "");

    printf("\npublish gate: nothing wanted, nothing called\n");
    PUB_GATE g;
    pub_init(&g);
    ok(g.want == 0 && g.off == 0 && g.done == 0 && g.skip == 0 && g.live == 0 && g.last_ms == 0 &&
           g.scan_ms == 0 && g.have_fp == 0,
       "a fresh gate is zero", "");
    ok(pub_step(&g, 5000, sig) == PUB_IDLE, "no want = no call, even with a loaded guard", "");
    ok(g.done == 0 && g.last_ms == 0, "and nothing was recorded", "");

    printf("\npublish gate: the paid hook's trigger\n");
    paid_hook_like(&g, 125186, 0);
    ok(g.want == 0, "phase 0 (before the award) raises no want", "");
    ok(pub_step(&g, 5000, sig) == PUB_IDLE, "and the tick before the payment calls nothing", "");
    paid_hook_like(&g, 125186, 1);
    ok(g.want == 1, "phase 1 (after the award returned) raises the want", "");
    paid_hook_like(&g, 0, 1);
    ok(g.want == 1, "a payment with no loot id is not a trigger of its own", "");

    printf("\npublish gate: the window\n");
    ok(pub_step(&g, 5000, sig) == PUB_CALL, "the first wanted tick calls", "");
    ok(g.done == 1 && g.want == 0 && g.last_ms == 5000, "the call is recorded and the want is cleared", "");
    paid_hook_like(&g, 125186, 1);
    ok(pub_step(&g, 5500, sig) == PUB_COALESCED, "500 ms later the want is coalesced", "");
    ok(g.want == 1 && g.done == 1, "the want survives the coalesce and nothing was called", "");
    ok(g.skip == 1, "the coalesce is counted", "");
    paid_hook_like(&g, 125186, 1);
    ok(pub_step(&g, 5999, sig) == PUB_COALESCED, "999 ms after the last call is still inside the window", "");
    ok(pub_step(&g, 6000, sig) == PUB_CALL, "1,000 ms after it, the deferred want is honoured", "");
    ok(g.done == 2 && g.skip == 2, "two calls, two coalesces - nothing was dropped", "");
    ok(pub_step(&g, 6500, sig) == PUB_IDLE, "and with no further want the gate goes quiet", "");

    printf("\npublish gate: no call when the guard fails\n");
    PUB_GATE bad;
    pub_init(&bad);
    pub_want(&bad);
    unsigned char wrong[PUB_SIG_LEN];
    memcpy(wrong, WANT_SIG, PUB_SIG_LEN);
    wrong[0] = 0x00;
    ok(pub_step(&bad, 7000, wrong) == PUB_REFUSED, "a mismatched target is refused", "");
    ok(bad.off == 1 && bad.done == 0 && bad.want == 0, "the feature latches off and makes no call", "");
    pub_want(&bad);
    ok(pub_step(&bad, 9000, sig) == PUB_IDLE, "a latched-off feature never calls again, even with a good guard",
       "");
    ok(bad.want == 0, "and it leaves no want behind", "");

    printf("\npublish gate: no call when the client is not loaded\n");
    PUB_GATE gone;
    pub_init(&gone);
    pub_want(&gone);
    ok(pub_step(&gone, 7000, NULL) == PUB_REFUSED, "a null serialiser is refused", "");
    ok(gone.off == 1 && gone.done == 0, "and it latches off without a call", "");

    printf("\npublish gate: the match flag\n");
    PUB_GATE live;
    pub_init(&live);
    pub_match_live(&live);
    ok(live.live == 1, "the match-start seam sets the flag", "");

    printf("\npublish gate: the record fingerprint\n");
    memset(RECORD_BLOCK, 0, sizeof(RECORD_BLOCK));
    for (int i = 0; i < RECS; i++)
    {
        rec_set_xp(i, 1000 + i);
        rec_at(i)[MASTER_REC_LEVEL] = (unsigned char)(1 + i);
        rec_at(i)[MASTER_REC_PRESTIGE] = 0;
    }
    unsigned long long base = pub_fingerprint(RECORD_BLOCK, RECS);
    ok(base == pub_fingerprint(RECORD_BLOCK, RECS), "the same records give the same number", "");
    ok(base != 0, "and it is not zero", "");
    rec_set_xp(1, 2000);
    unsigned long long moved_xp = pub_fingerprint(RECORD_BLOCK, RECS);
    ok(moved_xp != base, "one row's progress moving changes it", "");
    rec_set_xp(1, 1001);
    ok(pub_fingerprint(RECORD_BLOCK, RECS) == base, "putting it back gives the first number again", "");
    rec_at(2)[MASTER_REC_LEVEL] = 9;
    unsigned long long moved_level = pub_fingerprint(RECORD_BLOCK, RECS);
    ok(moved_level != base, "a level byte moving changes it", "");
    rec_at(2)[MASTER_REC_LEVEL] = 3;
    rec_at(0)[MASTER_REC_PRESTIGE] = 1;
    ok(pub_fingerprint(RECORD_BLOCK, RECS) != base, "a prestige byte moving changes it", "");
    rec_at(0)[MASTER_REC_PRESTIGE] = 0;
    rec_at(0)[MASTER_REC_LEVEL - 1] = 3;
    ok(pub_fingerprint(RECORD_BLOCK, RECS) != base, "a status byte moving changes it", "");
    rec_at(0)[MASTER_REC_LEVEL - 1] = 0;
    ok(pub_fingerprint(RECORD_BLOCK, RECS) == base, "back to the first state, back to the first number", "");
    ok(pub_fingerprint(NULL, RECS) == 0, "a null array has no fingerprint", "");
    ok(pub_fingerprint(RECORD_BLOCK, 0) == 0, "no records has no fingerprint", "");

    printf("\npublish gate: the scan's own decision\n");
    PUB_GATE s;
    pub_init(&s);
    ok(pub_note_fingerprint(&s, base) == 0, "the first scan only takes the baseline", "");
    ok(s.want == 0 && s.have_fp == 1, "so nothing is wanted and the baseline is kept", "");
    ok(pub_note_fingerprint(&s, base) == 0, "an unchanged record raises nothing", "");
    ok(pub_note_fingerprint(&s, moved_xp) == 0, "a change outside a match only re-baselines", "");
    ok(s.want == 0, "and asks for no publish", "");
    pub_match_live(&s);
    ok(pub_note_fingerprint(&s, moved_level) == 1, "the same change in a live match raises the want", "");
    ok(s.want == 1, "and the gate holds it", "");
    ok(pub_step(&s, 12000, sig) == PUB_CALL, "which the next tick turns into one call", "");

    printf("\npublish gate: the scan's clock\n");
    PUB_GATE t;
    pub_init(&t);
    ok(pub_scan_due(&t, 20000) == 1, "the first scan is due", "");
    ok(pub_scan_due(&t, 20500) == 0, "half a window later it is not", "");
    ok(pub_scan_due(&t, 20999) == 0, "still not at 999 ms", "");
    ok(pub_scan_due(&t, 21000) == 1, "due again at the window", "");

    printf("\n%d passed, %d failed\n", PASSES, FAILS);
    return FAILS == 0 ? 0 : 1;
}

static int mode_off(const wchar_t *dir)
{
    // the shipped unit joins "<tempdir>progression-tuning\..." exactly as `GetTempPathW` returns it, i.e. with a
    // trailing separator; a caller that passes a bare directory gets one appended here, not in the unit
    wchar_t full[MAX_PATH];
    size_t n = wcslen(dir);
    if (n > 0 && (dir[n - 1] == L'\\' || dir[n - 1] == L'/'))
    {
        _snwprintf_s(full, MAX_PATH, _TRUNCATE, L"%s", dir);
    }
    else
    {
        _snwprintf_s(full, MAX_PATH, _TRUNCATE, L"%s\\", dir);
    }
    printf("%d\n", pub_off_present(full));
    return 0;
}

int main(int argc, char **argv)
{
    if (argc >= 2 && strcmp(argv[1], "off") == 0)
    {
        if (argc < 3)
        {
            fprintf(stderr, "usage: publish_test off <tempdir>\n");
            return 2;
        }
        wchar_t dir[MAX_PATH];
        if (MultiByteToWideChar(CP_ACP, 0, argv[2], -1, dir, MAX_PATH) == 0)
        {
            fprintf(stderr, "cannot convert %s\n", argv[2]);
            return 2;
        }
        return mode_off(dir);
    }
    return mode_self();
}
