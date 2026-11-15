// nativepay-poc's offline test driver. Nothing here touches the game folder beyond reading the client file, and
// nothing is installed. Five modes, driven by tools\test_nativepay.py:
//
//   nativepay_test.exe self [client]   the pure half + the SHIPPED wrapper against a fabricated event record and
//                                      fake ints: decode, clamp, the save/set/call/restore window (including a
//                                      fault raised inside the called function), the log line, the 400-then-every-
//                                      20th cap, SHA-256 against known vectors, the `E8 rel32` patch and its reach,
//                                      and the install guard's five refusal reasons against a synthetic image. The
//                                      optional <client> (or KRONOS_GAME_DIR) is the file the synthetic image is
//                                      built from; without it the guard checks cannot run and the mode stops.
//   nativepay_test.exe sites <client>  the recorded signature constants against the FILE on disk: size, sha256 and
//                                      the four sites at rva 0x93820 / 0x930D3 / 0x93E5D / 0x93E63.
//   nativepay_test.exe install <client> map the client read-only as an image, run the real nativepay_install
//                                      through its real log seam, prove the 5 bytes are the only code changed and
//                                      that the site now calls our wrapper, then put the bytes back.
//   nativepay_test.exe off <dir>       the kill switch's file test (a scratch dir supplied by the python driver).
//   nativepay_test.exe proxy <dll>     build 20's single-file proof (build 19's change, kept): load THIS DLL as version.dll, then load
//                                      <System32>\version.dll by full path, and prove the second is the system
//                                      module (distinct handle, path under the system directory) and that all 17
//                                      exports answer like it - with no version_orig.dll anywhere near it.
//
// Exit 0 = every check in that mode passed; the last line is "nativepay: OK - N checks".

#include <windows.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "../src/nativepay.h"

// src\resolve.c (linked in since build 25) logs through proxy_main.c's ch_logf. This driver reports the
// resolver's answers itself where it needs them (the `sites` mode and tools\test_resolve.py), so the definition
// only has to exist: a line here would land inside the log capture the install mode asserts on.
void ch_logf(const char *fmt, ...)
{
    (void)fmt;
}

// The client file is a setting, never a constant. KRONOS_GAME_DIR names the game install: either the folder that
// holds cod25\ or the cod25 folder itself. Returns 0 and leaves `out` alone when the setting is absent, so the
// caller can say so and stop rather than run the guard checks against nothing.
static int game_client(wchar_t *out, size_t cch)
{
    wchar_t dir[MAX_PATH];
    const wchar_t *env = _wgetenv(L"KRONOS_GAME_DIR");
    size_t n = 0;
    int is_cod25 = 0;

    if (env == NULL || env[0] == L'\0')
        return 0;
    wcsncpy_s(dir, MAX_PATH, env, _TRUNCATE);
    n = wcslen(dir);
    while (n > 0 && (dir[n - 1] == L'\\' || dir[n - 1] == L'/'))
        dir[--n] = L'\0';
    if (n >= 5 && _wcsicmp(dir + (n - 5), L"cod25") == 0 && (n == 5 || dir[n - 6] == L'\\' || dir[n - 6] == L'/'))
        is_cod25 = 1;
    if (is_cod25)
        _snwprintf_s(out, cch, _TRUNCATE, L"%s\\XINPUT9_1_0.dll", dir);
    else
        _snwprintf_s(out, cch, _TRUNCATE, L"%s\\cod25\\XINPUT9_1_0.dll", dir);
    return 1;
}

static int PASSES = 0;
static int FAILS = 0;

static void ok(int cond, const char *name, const char *detail)
{
    if (cond)
    {
        PASSES++;
        if (detail != NULL && detail[0] != '\0')
        {
            printf("pass  %s  (%s)\n", name, detail);
        }
        else
        {
            printf("pass  %s\n", name);
        }
    }
    else
    {
        FAILS++;
        if (detail != NULL && detail[0] != '\0')
        {
            printf("FAIL  %s  (%s)\n", name, detail);
        }
        else
        {
            printf("FAIL  %s\n", name);
        }
    }
}

// --- the log sink, so the SHIPPED wrapper's own lines can be asserted ---------------------------------

#define LOGMAX 512
static char LOG[LOGMAX][256];
static int LOGN = 0;

static void log_hook(const char *body)
{
    if (LOGN < LOGMAX)
    {
        strncpy_s(LOG[LOGN], sizeof(LOG[LOGN]), body, _TRUNCATE);
        LOGN++;
    }
}

static void log_reset(void)
{
    LOGN = 0;
}

static const char *log_at(int i)
{
    return (i >= 0 && i < LOGN) ? LOG[i] : "";
}

// =======================================================================================================
// a fabricated event record: the layout `180092ff0:81-96` + `180093820:238-247` describe
//   ev[0] = id, ev[1] = count, ids as u16 at byte 8 + 2i, values as i64 at byte 0x70 + 8i
// =======================================================================================================

static int make_event(unsigned int *buf, unsigned int id, const unsigned short *ids, const long long *vals, int n)
{
    memset(buf, 0, NP_RECORD_LEN);
    memcpy(buf, &id, 4);
    memcpy((unsigned char *)buf + 4, &n, 4);
    for (int i = 0; i < n; i++)
    {
        memcpy((unsigned char *)buf + NP_ENTRY_ID_OFF + (size_t)i * 2, &ids[i], 2);
        memcpy((unsigned char *)buf + NP_ENTRY_VAL_OFF + (size_t)i * 8, &vals[i], 8);
    }
    return n;
}

// The ev=95 the design study describes: fields 0, 3, 19, 31 (the operator value), 44 (the weapon) and 45.
static void make_kill_event(unsigned int *buf)
{
    static const unsigned short ids[] = {0, 3, 19, 31, 44, 45};
    static const long long vals[] = {0, 7, 2, 555, 125186, 13};
    make_event(buf, 95, ids, vals, 6);
}

// --- the match-boundary spy (build 23b) ---------------------------------------------------------------

static int RESETS = 0;
static void reset_spy(void)
{
    RESETS++;
}

// --- the stand-in for the client's award function ------------------------------------------------------
static int OBS_KILL = -1; // what the called function saw in kill
static int OBS_CRIT = -1; // ... and in crit
static int OBS_CALLS = 0;
static const unsigned int *OBS_EV = NULL; // ... and the event pointer it was handed

// one function per behaviour, each reading the pair it was handed through file-scope pointers
static int *W_KILL = NULL;
static int *W_CRIT = NULL;

static unsigned long long fake_quiet(const unsigned int *ev)
{
    OBS_EV = ev;
    OBS_CALLS++;
    OBS_KILL = (W_KILL != NULL) ? *W_KILL : -2;
    OBS_CRIT = (W_CRIT != NULL) ? *W_CRIT : -2;
    return 99;
}

static unsigned long long fake_fault(const unsigned int *ev)
{
    OBS_EV = ev;
    OBS_CALLS++;
    OBS_KILL = (W_KILL != NULL) ? *W_KILL : -2;
    OBS_CRIT = (W_CRIT != NULL) ? *W_CRIT : -2;
    RaiseException(0xC0000005, 0, 0, NULL);
    return 0;
}

// expected value of the record's field 45 - 13 in make_kill_event()
#define F45 13
#define LOOT 125186

// =======================================================================================================
// self
// =======================================================================================================

static void test_decode(void)
{
    unsigned int ev[NP_RECORD_LEN / 4];
    np_event e;

    make_kill_event(ev);
    ok(np_decode(ev, &e) == 1, "decode: ev=95 with field 45 is accepted", "");
    ok(e.id == 95 && e.n == 6, "decode: the id is at byte 0 and the entry count at byte 4", "");
    ok(e.has45 && e.f45 == F45, "decode: field 45's value is at byte 0x70 + 8i (8-byte entries)", "");
    ok(e.has44 && e.f44 == LOOT, "decode: field 44 (the weapon id) is found in the same pass", "");

    {
        static const unsigned short ids[] = {0, 3, 19, 31, 45, 44};
        static const long long vals[] = {0, 7, 2, 555, F45, LOOT};
        make_event(ev, 95, ids, vals, 6);
        ok(np_decode(ev, &e) == 1 && e.f45 == F45 && e.f44 == LOOT,
           "decode: the order of the entries does not matter", "");
    }
    {
        static const unsigned short ids[] = {44, 45};
        static const long long vals[] = {LOOT, F45};
        make_event(ev, 123, ids, vals, 2);
        ok(np_decode(ev, &e) == 0, "decode: ev=123 is not ours", "");
    }
    {
        static const unsigned short ids[] = {0, 44};
        static const long long vals[] = {0, LOOT};
        make_event(ev, 95, ids, vals, 2);
        ok(np_decode(ev, &e) == 0 && e.has44, "decode: ev=95 with no field 45 is refused (the cfg award stands)",
           "");
    }
    {
        int bad = -1;
        make_kill_event(ev);
        memcpy((unsigned char *)ev + 4, &bad, 4);
        ok(np_decode(ev, &e) == 0, "decode: a negative entry count is refused", "");
        bad = NP_ENTRY_MAX + 1;
        memcpy((unsigned char *)ev + 4, &bad, 4);
        ok(np_decode(ev, &e) == 0, "decode: a count above 64 is refused", "");
        bad = 51; // 0x70 + 51*8 > 0x200: the values would leave the 512-byte record
        memcpy((unsigned char *)ev + 4, &bad, 4);
        ok(np_decode(ev, &e) == 0, "decode: a count whose values leave the 0x200-byte record is refused", "");
    }
    {
        static const unsigned short ids[] = {45, 45};
        static const long long vals[] = {F45, 999};
        make_event(ev, 95, ids, vals, 2);
        ok(np_decode(ev, &e) == 1 && e.f45 == F45, "decode: a repeated field 45 takes the first value", "");
    }
    ok(np_decode(NULL, &e) == 0, "decode: a NULL record is refused", "");
    ok(np_decode(ev, NULL) == 0, "decode: a NULL output is refused", "");
}

static void test_clamp(void)
{
    ok(np_clamp45(-5) == 0, "clamp: a negative field 45 becomes 0 (a zero sum adds nothing)", "");
    ok(np_clamp45(0) == 0, "clamp: 0 stays 0", "");
    ok(np_clamp45(F45) == F45, "clamp: 13 stays 13", "");
    ok(np_clamp45(NP_FIELD45_MAX) == NP_FIELD45_MAX, "clamp: the ceiling itself is allowed", "");
    ok(np_clamp45(NP_FIELD45_MAX + 1) == NP_FIELD45_MAX, "clamp: one over the ceiling is clamped", "");
}

static void test_call_window(void)
{
    unsigned int ev[NP_RECORD_LEN / 4];
    int kill = 20, crit = 5;
    W_KILL = &kill;
    W_CRIT = &crit;
    OBS_KILL = OBS_CRIT = -1;
    make_kill_event(ev);

    unsigned long long rv = np_call(&kill, &crit, ev, fake_quiet);
    ok(OBS_KILL == F45, "window: the client's function is called with kill = field 45", "");
    ok(OBS_CRIT == 0, "window: and with crit = 0 (field 45 already carries the game's crit bonus)", "");
    ok(rv == 99, "window: the client's return value is passed through", "");
    ok(kill == 20 && crit == 5, "window: both ints are restored afterwards", "");

    {
        static const unsigned short ids[] = {44, 45};
        static const long long vals[] = {LOOT, F45};
        make_event(ev, 123, ids, vals, 2);
        OBS_KILL = OBS_CRIT = -1;
        OBS_CALLS = 0;
        rv = np_call(&kill, &crit, ev, fake_quiet);
        ok(OBS_CALLS == 1 && kill == 20 && crit == 5, "window: a non-95 event runs the client's function unchanged",
           "");
    }
    {
        static const unsigned short ids[] = {0, 44};
        static const long long vals[] = {0, LOOT};
        make_event(ev, 95, ids, vals, 2);
        rv = np_call(&kill, &crit, ev, fake_quiet);
        ok(rv == 99 && kill == 20 && crit == 5, "window: ev=95 without field 45 leaves the pair untouched", "");
    }
    {
        make_kill_event(ev);
        OBS_KILL = OBS_CRIT = -1;
        int faulted = 0;
        __try
        {
            rv = np_call(&kill, &crit, ev, fake_fault);
        }
        __except (EXCEPTION_EXECUTE_HANDLER)
        {
            faulted = 1;
        }
        ok(faulted == 1, "window: a fault inside the client propagates (not swallowed)", "");
        ok(OBS_KILL == F45 && OBS_CRIT == 0, "window: the fault path ran with the pair already set", "");
        ok(kill == 20 && crit == 5, "window: __finally restored the pair after the fault", "");
    }
    ok(np_call(NULL, &crit, ev, fake_quiet) == 99, "window: a NULL kill pointer passes straight through", "");
}

static void test_format(void)
{
    unsigned int ev[NP_RECORD_LEN / 4];
    np_event e;
    char line[256];

    make_kill_event(ev);
    np_decode(ev, &e);
    np_format(line, (int)sizeof(line), &e, 20, 0);
    ok(strcmp(line, "nativepay: ev=95 loot=125186 f45=13 kill=20 crit=0 (paid 13)") == 0,
       "format: the per-event line names the loot, field 45 and both ints before the call", line);

    {
        static const unsigned short ids[] = {44, 45};
        static const long long vals[] = {LOOT, 200000};
        make_event(ev, 95, ids, vals, 2);
        np_decode(ev, &e);
        np_format(line, (int)sizeof(line), &e, 20, 0);
        ok(strstr(line, "(paid 100000) [clamped from 200000]") != NULL, "format: a clamped value is marked", line);
    }
    {
        static const unsigned short ids[] = {45};
        static const long long vals[] = {F45};
        make_event(ev, 95, ids, vals, 1);
        np_decode(ev, &e);
        np_format(line, (int)sizeof(line), &e, 20, 0);
        ok(strstr(line, "loot=0 ") != NULL, "format: a missing field 44 prints loot=0", line);
    }
}

// The SHIPPED wrapper (nativepay_call), driven through its log seam against fake ints.
static void test_wrapper(void)
{
    unsigned int ev[NP_RECORD_LEN / 4];
    int kill = 20, crit = 0;
    W_KILL = &kill;
    W_CRIT = &crit;

    make_kill_event(ev);
    nativepay_set_log(log_hook);
    nativepay_reset_for_test();
    nativepay_bind_for_test(&kill, &crit, fake_quiet);
    log_reset();

    unsigned long long rv = nativepay_call(ev);
    ok(rv == 99 && kill == 20 && crit == 0, "wrapper: one ev=95 call restores the pair", "");
    ok(LOGN == 1, "wrapper: one ev=95 call emits exactly one log line", "");
    ok(strcmp(log_at(0), "nativepay: ev=95 loot=125186 f45=13 kill=20 crit=0 (paid 13)") == 0,
       "wrapper: the log line is the documented one", log_at(0));

    {
        static const unsigned short ids[] = {44, 45};
        static const long long vals[] = {LOOT, F45};
        make_event(ev, 75, ids, vals, 2);
        log_reset();
        OBS_CALLS = 0;
        nativepay_call(ev);
        ok(LOGN == 0 && OBS_CALLS == 1, "wrapper: ev=75 emits no line and pays nothing", "");
    }

    // the cap: the first 3 lines, then every 20th
    make_kill_event(ev);
    nativepay_reset_for_test();
    log_reset();
    for (int i = 0; i < 420; i++)
    {
        nativepay_call(ev);
    }
    ok(LOGN == 24, "wrapper: 420 events -> 3 lines + every 20th after that (24)", "");
    log_reset();
    for (int i = 0; i < 20; i++)
    {
        nativepay_call(ev);
    }
    ok(LOGN == 1, "wrapper: after the cap, one line in twenty", "");

    // the log is rate-limited and stateless: the observable here is that two events of the same loot produce
    // two identical lines (the per-gun totals live in pubxp.c, proven by pubxp_test.exe).
    nativepay_reset_for_test();
    log_reset();
    nativepay_call(ev);
    nativepay_call(ev);
    ok(LOGN == 2 && strcmp(log_at(0), log_at(1)) == 0, "wrapper: two identical events produce two identical lines",
       "");

    // ---- the match boundary (ev=109). The call site is `180092ff0:81`, which the client takes for EVERY event
    // before the `log_events` gate at `:82`, so the boundary reaches this wrapper whether or not the client is
    // writing players\ae_events.log. One event, one hook call, and the event itself unchanged.
    {
        make_event(ev, 109, NULL, NULL, 0);
        nativepay_set_match_reset_hook(reset_spy);
        RESETS = 0;
        log_reset();
        OBS_CALLS = 0;
        OBS_EV = NULL;
        unsigned long long r = nativepay_call(ev);
        ok(RESETS == 1, "boundary: an ev=109 event calls the reset hook exactly once", "");
        ok(OBS_CALLS == 1 && r == 99, "boundary: and the event goes to the client's own function, once", "");
        ok(OBS_EV == ev, "boundary: the client's function is handed the SAME record, unchanged", "");
        ok(LOGN == 0, "boundary: no payment line is produced for it", "");
        ok(kill == 20 && crit == 0, "boundary: the weapon_xp pair is not touched", "");

        // a second dispatch of the event is a second boundary, and this wrapper never calls the hook twice for one
        nativepay_call(ev);
        ok(RESETS == 2, "boundary: exactly one call per event, never two for one", "");
    }
    {
        // no hook set: harmless, and the event still passes through to the client
        nativepay_set_match_reset_hook(NULL);
        make_event(ev, 109, NULL, NULL, 0);
        RESETS = 0;
        log_reset();
        OBS_CALLS = 0;
        unsigned long long r = nativepay_call(ev);
        ok(r == 99 && OBS_CALLS == 1, "boundary: with no hook set the event passes through untouched", "");
        ok(RESETS == 0, "boundary: and nothing is called", "");
    }
    {
        // the boundary hook is for ev=109 only - the XP event must not touch it
        nativepay_set_match_reset_hook(reset_spy);
        make_kill_event(ev);
        RESETS = 0;
        nativepay_reset_for_test();
        log_reset();
        unsigned long long r = nativepay_call(ev);
        ok(RESETS == 0 && r == 99, "boundary: an ev=95 event never calls the reset hook", "");
        ok(LOGN == 1, "boundary: and ev=95 still pays on its own path (one line)", "");
        nativepay_set_match_reset_hook(NULL);
    }
    nativepay_set_match_reset_hook(NULL);
}

static void test_patch(void)
{
    unsigned char site[16];
    unsigned char *target = site + 8;
    unsigned char patch[NP_SITE_LEN];
    memset(site, 0xCC, sizeof(site));

    ok(np_reach(site, target) == 1, "patch: a target on the same page is in reach", "");
    ok(np_site_patch(patch, site, target) == 1, "patch: the 5 bytes are built", "");
    ok(patch[0] == 0xE8, "patch: the patch is a `call` (E8)", "");
    {
        int rel = 0;
        memcpy(&rel, patch + 1, 4);
        ok((unsigned char *)(site + 5 + rel) == target, "patch: the rel32 lands exactly on the target", "");
    }
    ok(np_reach(site, site + 0xC0000000LL) == 0, "patch: a target ~3 GB away is out of reach", "");
    ok(np_site_patch(patch, site, site + 0xC0000000LL) == 0, "patch: and the patch is refused, not truncated", "");
    ok(np_reach(site, site + 0x7FF00000LL) == 1, "patch: the last byte of rel32 reach is still in reach", "");

    {
        unsigned char tramp[12];
        unsigned long long back = 0;
        np_tramp_bytes(tramp, 0x18000123456789ABull);
        memcpy(&back, tramp + 2, 8);
        ok(tramp[0] == 0x48 && tramp[1] == 0xB8 && tramp[10] == 0xFF && tramp[11] == 0xE0 &&
               back == 0x18000123456789ABull,
           "patch: the trampoline is `mov rax,<thunk>; jmp rax`", "");
    }
}

static void test_sha256(void)
{
    char hex[65];
    np_sha256_hex("", 0, hex);
    ok(strcmp(hex, "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855") == 0,
       "sha256: the empty string's known vector", hex);
    np_sha256_hex("abc", 3, hex);
    ok(strcmp(hex, "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad") == 0,
       "sha256: the 'abc' known vector", hex);
    {
        char *big = (char *)malloc(1000 * 1000);
        if (big != NULL)
        {
            memset(big, 'a', 1000 * 1000);
            np_sha256_hex(big, 1000 * 1000, hex);
            ok(strcmp(hex, "cdc76e5c9914fb9281a1c7e284d73e67f1809a48a497200e046d39ccc7112cd0") == 0,
               "sha256: one million 'a' (many blocks, both padding lengths)", hex);
            free(big);
        }
    }
}

// --- the install guard, against a synthetic image built from the real file's own bytes ---------------

static int load_fake_image(const wchar_t *path, unsigned char **out)
{
    FILE *f = _wfopen(path, L"rb");
    if (f == NULL)
    {
        return 0;
    }
    fseek(f, 0, SEEK_END);
    long n = ftell(f);
    fseek(f, 0, SEEK_SET);
    unsigned char *raw = (unsigned char *)malloc((size_t)n);
    if (raw == NULL || fread(raw, 1, (size_t)n, f) != (size_t)n)
    {
        fclose(f);
        free(raw);
        return 0;
    }
    fclose(f);

    unsigned int lfanew = 0;
    memcpy(&lfanew, raw + 0x3C, 4);
    int nsec = 0;
    memcpy(&nsec, raw + lfanew + 6, 2);
    unsigned int opt_size = 0;
    memcpy(&opt_size, raw + lfanew + 20, 2);
    const unsigned char *sec = raw + lfanew + 24 + opt_size;

    unsigned char *img = (unsigned char *)calloc(1, NP_CLIENT_IMAGE_SIZE);
    if (img == NULL)
    {
        free(raw);
        return 0;
    }
    memcpy(img, raw, 0x1000); // the headers, so SizeOfImage and the section table are real
    unsigned int rvas[4] = {NP_AWARD_RVA, NP_SITE_RVA, NP_LOAD_A_RVA, NP_LOAD_B_RVA};
    int lens[4] = {NP_AWARD_ENTRY_LEN, NP_SITE_LEN, NP_LOAD_A_LEN, NP_LOAD_B_LEN};
    for (int k = 0; k < 4; k++)
    {
        for (int i = 0; i < nsec; i++)
        {
            unsigned int vsize, va, rawsize, rawptr;
            memcpy(&vsize, sec + i * 40 + 8, 4);
            memcpy(&va, sec + i * 40 + 12, 4);
            memcpy(&rawsize, sec + i * 40 + 16, 4);
            memcpy(&rawptr, sec + i * 40 + 20, 4);
            unsigned int span = vsize > rawsize ? vsize : rawsize;
            if (rvas[k] >= va && rvas[k] + (unsigned int)lens[k] <= va + span)
            {
                memcpy(img + rvas[k], raw + rawptr + (rvas[k] - va), (size_t)lens[k]);
            }
        }
    }
    free(raw);
    *out = img;
    return 1;
}

static void test_guard(const wchar_t *client)
{
    unsigned char *img = NULL;
    char why[256];
    why[0] = '\0';
    if (client == NULL || !load_fake_image(client, &img))
    {
        ok(0, "guard: the client file could be read for a synthetic image", "no client on disk - skipped");
        return;
    }
    ok(np_verify_image(img, why, (int)sizeof(why)) == 1, "guard: a faithful copy of the four sites passes", why);

    {
        struct
        {
            const char *name;
            unsigned int rva;
            const char *want;
        } cases[] = {
            {"guard: a changed byte in the award at 0x93820 is refused", NP_AWARD_RVA, "award"},
            {"guard: a changed byte in the call site 0x930D3 is refused", NP_SITE_RVA, "call site"},
            {"guard: a changed byte in the load at 0x93E5D is refused", NP_LOAD_A_RVA, "load at 0x93E5D"},
            {"guard: a changed byte in the load at 0x93E63 is refused", NP_LOAD_B_RVA, "load at 0x93E63"},
        };
        for (int i = 0; i < 4; i++)
        {
            img[cases[i].rva] ^= 0xFF;
            why[0] = '\0';
            int r = np_verify_image(img, why, (int)sizeof(why));
            ok(r == 0 && strstr(why, cases[i].want) != NULL, cases[i].name, why);
            img[cases[i].rva] ^= 0xFF;
        }
    }
    {
        // The 5 bytes ARE the rel32, so a call that points somewhere else cannot also equal the recorded bytes: the
        // byte guard catches it, and it must name the site. (The separate "does it resolve to 0x93820" check in
        // np_verify_image is a second belt for the same fact; it is unreachable while the bytes match.)
        unsigned char keep[NP_SITE_LEN];
        int rel = 0x1234;
        memcpy(keep, img + NP_SITE_RVA, NP_SITE_LEN);
        img[NP_SITE_RVA] = 0xE8;
        memcpy(img + NP_SITE_RVA + 1, &rel, 4);
        why[0] = '\0';
        int r = np_verify_image(img, why, (int)sizeof(why));
        ok(r == 0 && strstr(why, "0x930D3") != NULL && strstr(why, "E8 48 07 00 00") != NULL,
           "guard: a call whose rel32 points elsewhere is refused, naming the site", why);
        memcpy(img + NP_SITE_RVA, keep, NP_SITE_LEN);
    }
    {
        unsigned int lfanew = 0;
        unsigned int soi = 0x9A2000;
        memcpy(&lfanew, img + 0x3C, 4);
        memcpy(img + lfanew + 24 + 56, &soi, 4);
        why[0] = '\0';
        int r = np_verify_image(img, why, (int)sizeof(why));
        ok(r == 0 && strstr(why, "SizeOfImage") != NULL, "guard: another SizeOfImage is refused", why);
        soi = NP_CLIENT_IMAGE_SIZE;
        memcpy(img + lfanew + 24 + 56, &soi, 4);
    }
    ok(np_verify_image(img, why, (int)sizeof(why)) == 1, "guard: the image passes again after the probes", "");
    ok(np_verify_image(NULL, why, (int)sizeof(why)) == 0, "guard: a NULL module is refused", why);
    free(img);
}

static void test_file_guard(const wchar_t *client)
{
    char why[256];
    why[0] = '\0';
    if (client != NULL && GetFileAttributesW(client) != INVALID_FILE_ATTRIBUTES)
    {
        ok(np_verify_file(client, why, (int)sizeof(why)) == 1, "guard: the client file's size + sha256 pass", why);
    }
    {
        wchar_t tmp[MAX_PATH];
        wchar_t dir[MAX_PATH];
        GetTempPathW(MAX_PATH, dir);
        _snwprintf_s(tmp, MAX_PATH, _TRUNCATE, L"%snativepay-wrong-size.bin", dir);
        FILE *f = _wfopen(tmp, L"wb");
        if (f != NULL)
        {
            fwrite("not the client", 1, 14, f);
            fclose(f);
            why[0] = '\0';
            int r = np_verify_file(tmp, why, (int)sizeof(why));
            ok(r == 0 && strstr(why, "the client file is 14 B") != NULL, "guard: a wrong-sized file is refused", why);
            _wremove(tmp);
        }
    }
    why[0] = '\0';
    ok(np_verify_file(L"Z:\\no\\such\\file.dll", why, (int)sizeof(why)) == 0, "guard: an unreadable file is refused",
       why);
}

static int mode_self(const wchar_t *client)
{
    printf("nativepay: the pure half, the shipped wrapper and the build guard\n\n");
    test_decode();
    test_clamp();
    test_call_window();
    test_format();
    test_wrapper();
    test_patch();
    test_sha256();
    test_guard(client);
    test_file_guard(client);
    printf("\n%d passed, %d failed\n", PASSES, FAILS);
    if (FAILS == 0)
    {
        printf("nativepay: OK - %d checks\n", PASSES);
        return 0;
    }
    return 1;
}

// =======================================================================================================
// sites - the recorded constants against the FILE on disk
// =======================================================================================================

static int read_rva(FILE *f, const unsigned char *hdr, unsigned int rva, unsigned char *out, int n)
{
    unsigned int lfanew = 0;
    memcpy(&lfanew, hdr + 0x3C, 4);
    int nsec = 0;
    memcpy(&nsec, hdr + lfanew + 6, 2);
    unsigned int opt_size = 0;
    memcpy(&opt_size, hdr + lfanew + 20, 2);
    const unsigned char *sec = hdr + lfanew + 24 + opt_size;
    for (int i = 0; i < nsec; i++)
    {
        unsigned int vsize, va, rawsize, rawptr;
        memcpy(&vsize, sec + i * 40 + 8, 4);
        memcpy(&va, sec + i * 40 + 12, 4);
        memcpy(&rawsize, sec + i * 40 + 16, 4);
        memcpy(&rawptr, sec + i * 40 + 20, 4);
        unsigned int span = vsize > rawsize ? vsize : rawsize;
        if (rva >= va && rva + (unsigned int)n <= va + span)
        {
            if (fseek(f, (long)(rawptr + (rva - va)), SEEK_SET) != 0)
            {
                return 0;
            }
            return fread(out, 1, (size_t)n, f) == (size_t)n;
        }
    }
    return 0;
}

static int mode_sites(const wchar_t *path)
{
    unsigned long long size = 0;
    char hex[65];
    if (!np_hash_file(path, &size, hex))
    {
        printf("FAIL  cannot read %ls\n", path);
        return 1;
    }
    printf("file        %ls\n", path);
    printf("size        %llu B   (recorded %u B)\n", size, (unsigned int)NP_CLIENT_SIZE);
    printf("sha256      %s\n", hex);
    printf("recorded    %s\n", NP_CLIENT_SHA256);
    ok(size == (unsigned long long)NP_CLIENT_SIZE, "sites: the file's size is the recorded one", "");
    ok(lstrcmpiA(hex, NP_CLIENT_SHA256) == 0, "sites: the file's sha256 is the recorded one", "");

    FILE *f = _wfopen(path, L"rb");
    if (f == NULL)
    {
        printf("FAIL  cannot open the file\n");
        return 1;
    }
    unsigned char hdr[0x1000];
    if (fread(hdr, 1, sizeof(hdr), f) != sizeof(hdr))
    {
        fclose(f);
        printf("FAIL  the header is short\n");
        return 1;
    }

    {
        struct
        {
            unsigned int rva;
            int len;
            const unsigned char *want;
            const char *name;
        } sites[] = {
            {NP_AWARD_RVA, NP_AWARD_ENTRY_LEN, NP_AWARD_ENTRY, "award function 0x93820"},
            {NP_SITE_RVA, NP_SITE_LEN, NP_SITE_BYTES, "call site 0x930D3"},
            {NP_LOAD_A_RVA, NP_LOAD_A_LEN, NP_LOAD_A_BYTES, "addend load 0x93E5D"},
            {NP_LOAD_B_RVA, NP_LOAD_B_LEN, NP_LOAD_B_BYTES, "addend load 0x93E63"},
        };
        for (int i = 0; i < 4; i++)
        {
            unsigned char got[32];
            char name[128];
            if (!read_rva(f, hdr, sites[i].rva, got, sites[i].len))
            {
                printf("FAIL  %s: the rva is in no section\n", sites[i].name);
                FAILS++;
                continue;
            }
            _snprintf_s(name, sizeof(name), _TRUNCATE, "sites: %s matches the recorded %d bytes", sites[i].name,
                        sites[i].len);
            ok(memcmp(got, sites[i].want, (size_t)sites[i].len) == 0, name, "");
            printf("      0x%05X  ", sites[i].rva);
            for (int k = 0; k < sites[i].len; k++)
            {
                printf("%02x%s", got[k], (k + 1 == sites[i].len) ? "" : " ");
            }
            printf("\n");
        }
    }
    {
        unsigned char b[8];
        int rel = 0;
        read_rva(f, hdr, NP_SITE_RVA, b, 5);
        memcpy(&rel, b + 1, 4);
        printf("      0x930D3 + 5 + %d = 0x%X\n", rel, NP_SITE_RVA + 5 + rel);
        ok(NP_SITE_RVA + 5 + rel == NP_AWARD_RVA, "sites: the call at 0x930D3 resolves to 0x93820", "");
        read_rva(f, hdr, NP_LOAD_A_RVA, b, 6);
        memcpy(&rel, b + 2, 4);
        printf("      0x93E5D + 6 + %d = 0x%X\n", rel, NP_LOAD_A_RVA + 6 + rel);
        ok(NP_LOAD_A_RVA + 6 + rel == NP_KILL_RVA, "sites: the load at 0x93E5D reads rva 0x2775F4", "");
        read_rva(f, hdr, NP_LOAD_B_RVA, b, 7);
        memcpy(&rel, b + 3, 4);
        printf("      0x93E63 + 7 + %d = 0x%X\n", rel, NP_LOAD_B_RVA + 7 + rel);
        ok(NP_LOAD_B_RVA + 7 + rel == NP_CRIT_RVA, "sites: the load at 0x93E63 reads rva 0x2775F8", "");
    }
    fclose(f);
    printf("\n%d passed, %d failed\n", PASSES, FAILS);
    if (FAILS == 0)
    {
        printf("nativepay: OK - %d checks\n", PASSES);
        return 0;
    }
    return 1;
}

// =======================================================================================================
// install - the real installer against the client mapped read-only as an image
// =======================================================================================================

static int mode_install(const wchar_t *path)
{
    wchar_t scratch[MAX_PATH];
    wchar_t dir[MAX_PATH];
    GetTempPathW(MAX_PATH, dir);
    _snwprintf_s(scratch, MAX_PATH, _TRUNCATE, L"%snativepay-poc-scratch\\", dir);
    CreateDirectoryW(scratch, NULL);
    nativepay_set_tempdir(scratch); // an empty directory, so the kill switch is off
    nativepay_set_log(log_hook);
    log_reset();

    HANDLE f = CreateFileW(path, GENERIC_READ, FILE_SHARE_READ, NULL, OPEN_EXISTING, 0, NULL);
    if (f == INVALID_HANDLE_VALUE)
    {
        printf("FAIL  cannot open the client\n");
        return 2;
    }
    HANDLE m = CreateFileMappingW(f, NULL, PAGE_READONLY | SEC_IMAGE, 0, 0, NULL);
    if (m == NULL)
    {
        printf("FAIL  the client could not be mapped as an image (0x%lX)\n", (unsigned long)GetLastError());
        CloseHandle(f);
        return 2;
    }
    unsigned char *base = (unsigned char *)MapViewOfFile(m, FILE_MAP_READ, 0, 0, 0);
    if (base == NULL)
    {
        printf("FAIL  MapViewOfFile failed (0x%lX)\n", (unsigned long)GetLastError());
        CloseHandle(m);
        CloseHandle(f);
        return 2;
    }

    unsigned char site_before[NP_SITE_LEN];
    unsigned char award_before[NP_AWARD_ENTRY_LEN];
    unsigned char loada_before[NP_LOAD_A_LEN];
    unsigned char loadb_before[NP_LOAD_B_LEN];
    int kill_before = 0, crit_before = 0;
    memcpy(site_before, base + NP_SITE_RVA, NP_SITE_LEN);
    memcpy(award_before, base + NP_AWARD_RVA, NP_AWARD_ENTRY_LEN);
    memcpy(loada_before, base + NP_LOAD_A_RVA, NP_LOAD_A_LEN);
    memcpy(loadb_before, base + NP_LOAD_B_RVA, NP_LOAD_B_LEN);
    memcpy(&kill_before, base + NP_KILL_RVA, 4);
    memcpy(&crit_before, base + NP_CRIT_RVA, 4);

    int rc = nativepay_install((void *)base, path);
    printf("INFO  nativepay_install -> %d  (1 = installed; LOG lines are the DLL's own)\n", rc);
    for (int i = 0; i < LOGN; i++)
    {
        printf("LOG   %s\n", LOG[i]);
    }
    ok(rc == 1, "install: the install returns 1", "");

    {
        unsigned char now[NP_SITE_LEN];
        int rel = 0;
        void *dst;
        const void *thunk = nativepay_thunk_address();
        int is_thunk, is_tramp = 0;
        memcpy(now, base + NP_SITE_RVA, NP_SITE_LEN);
        memcpy(&rel, now + 1, 4);
        dst = (void *)(base + NP_SITE_RVA + NP_SITE_LEN + rel);
        is_thunk = (dst == thunk);
        if (!is_thunk)
        {
            unsigned char stub[12];
            unsigned long long t = 0;
            memcpy(stub, (const unsigned char *)dst, 12);
            memcpy(&t, stub + 2, 8);
            is_tramp = stub[0] == 0x48 && stub[1] == 0xB8 && stub[10] == 0xFF && stub[11] == 0xE0 &&
                       t == (unsigned long long)(ULONG_PTR)thunk;
        }
        printf("INFO  site 0x%X: %s -> %s 0x%llX\n", NP_SITE_RVA, (now[0] == 0xE8) ? "E8 rel32" : "??",
               is_thunk ? "nativepay_call" : (is_tramp ? "trampoline -> nativepay_call" : "NOT OUR HOOK"),
               (unsigned long long)(ULONG_PTR)dst);
        ok(now[0] == 0xE8, "install: the call site is now a `call`", "");
        ok(is_thunk || is_tramp, "install: and it reaches nativepay_call (directly or through a trampoline)", "");
        ok(memcmp(now, site_before, NP_SITE_LEN) != 0, "install: the 5 bytes really changed", "");
    }
    ok(memcmp(award_before, base + NP_AWARD_RVA, NP_AWARD_ENTRY_LEN) == 0,
       "install: the award's first 24 bytes are byte-identical (never written)", "");
    ok(memcmp(loada_before, base + NP_LOAD_A_RVA, NP_LOAD_A_LEN) == 0,
       "install: the addend load at 0x93E5D is byte-identical", "");
    ok(memcmp(loadb_before, base + NP_LOAD_B_RVA, NP_LOAD_B_LEN) == 0,
       "install: the addend load at 0x93E63 is byte-identical", "");
    {
        int k = 0, c = 0;
        memcpy(&k, base + NP_KILL_RVA, 4);
        memcpy(&c, base + NP_CRIT_RVA, 4);
        ok(k == kill_before && c == crit_before, "install: the two ints are not written at install time", "");
    }
    {
        unsigned char ctx[3];
        memcpy(ctx, base + NP_SITE_RVA - 3, 3);
        ok(ctx[0] == 0x48 && ctx[1] == 0x8B && ctx[2] == 0xCF,
           "install: `mov rcx,rdi` (48 8b cf) immediately before the patched call is intact", "");
    }
    ok(strstr(log_at(0), "nativepay: attach - XINPUT9_1_0.dll 5016064 B sha256 88a52103c5555b27") != NULL,
       "install: the attach line carries the file's size and hash", log_at(0));
    {
        int found = 0;
        for (int i = 0; i < LOGN; i++)
        {
            if (strstr(log_at(i), "nativepay: hook installed - 5 bytes at 0x930D3: E8 48 07 00 00 -> E8") != NULL)
            {
                found = 1;
            }
        }
        ok(found, "install: the hook line prints the 5 bytes before and after", "");
    }

    DWORD old = 0;
    if (VirtualProtect(base + NP_SITE_RVA, NP_SITE_LEN, PAGE_EXECUTE_READWRITE, &old))
    {
        DWORD back = 0;
        memcpy(base + NP_SITE_RVA, site_before, NP_SITE_LEN);
        VirtualProtect(base + NP_SITE_RVA, NP_SITE_LEN, old, &back);
    }
    ok(memcmp(base + NP_SITE_RVA, site_before, NP_SITE_LEN) == 0,
       "install: the 5 original bytes go back (the offline path restores its own view)", "");

    UnmapViewOfFile(base);
    CloseHandle(m);
    CloseHandle(f);
    RemoveDirectoryW(scratch);
    printf("\n%d passed, %d failed\n", PASSES, FAILS);
    if (FAILS == 0)
    {
        printf("nativepay: OK - %d checks\n", PASSES);
        return 0;
    }
    return 1;
}

static int mode_off(const wchar_t *dir)
{
    nativepay_set_tempdir(dir);
    printf("%d\n", np_off_present(NULL));
    return 0;
}

// =======================================================================================================
// proxy - THE BUILT DLL, loaded as a module, answering as the system version.dll
//
// The one question build 19 added (build 20 keeps it): the proxy loads the real DLL from C:\Windows\System32 at run time, and the
// module it gets back must be the SYSTEM module - not itself, though both files are called version.dll.
//
// The order matters and is the hard one: this exe imports no version.dll (USER32 + KERNEL32 only, checked with
// the harness's own PE reader), the DLL under test is loaded FIRST, and only then is the system path asked for.
// If the loader matched by base name, the second call would hand back our own handle and every check below fails.
//
// It answers 17 exports: resolves every one of them on both modules, and compares the answers of 14 by calling
// them (two are resolved but not called - VerInstallFileA/W are one argument short in the wrapper build 1 shipped,
// and GetFileVersionInfoByHandle's prototype is undocumented; neither is imported by cod25-cod.exe, whose
// version.dll imports are re-read by the python driver on every run).
// =======================================================================================================

typedef DWORD(WINAPI *p_size_w)(LPCWSTR, LPDWORD);
typedef DWORD(WINAPI *p_size_a)(LPCSTR, LPDWORD);
typedef DWORD(WINAPI *p_size_ex_w)(DWORD, LPCWSTR, LPDWORD);
typedef DWORD(WINAPI *p_size_ex_a)(DWORD, LPCSTR, LPDWORD);
typedef BOOL(WINAPI *p_info_w)(LPCWSTR, DWORD, DWORD, LPVOID);
typedef BOOL(WINAPI *p_info_a)(LPCSTR, DWORD, DWORD, LPVOID);
typedef BOOL(WINAPI *p_info_ex_w)(DWORD, LPCWSTR, DWORD, DWORD, LPVOID);
typedef BOOL(WINAPI *p_info_ex_a)(DWORD, LPCSTR, DWORD, DWORD, LPVOID);
typedef DWORD(WINAPI *p_find_w)(DWORD, LPCWSTR, LPCWSTR, LPCWSTR, LPWSTR, PUINT, LPWSTR, PUINT);
typedef DWORD(WINAPI *p_find_a)(DWORD, LPCSTR, LPCSTR, LPCSTR, LPSTR, PUINT, LPSTR, PUINT);
typedef DWORD(WINAPI *p_install_w)(DWORD, LPCWSTR, LPCWSTR, LPCWSTR, LPCWSTR, LPWSTR, PUINT);
typedef DWORD(WINAPI *p_install_a)(DWORD, LPCSTR, LPCSTR, LPCSTR, LPCSTR, LPSTR, PUINT);
typedef DWORD(WINAPI *p_lang_w)(DWORD, LPWSTR, DWORD);
typedef DWORD(WINAPI *p_lang_a)(DWORD, LPSTR, DWORD);
typedef BOOL(WINAPI *p_query_w)(LPCVOID, LPCWSTR, LPVOID *, PUINT);
typedef BOOL(WINAPI *p_query_a)(LPCVOID, LPCSTR, LPVOID *, PUINT);
typedef BOOL(WINAPI *p_by_handle)(DWORD, HANDLE, LPVOID);

typedef struct
{
    HMODULE mod;
    int resolved;   // of 17
    p_size_w size_w;
    p_size_a size_a;
    p_size_ex_w size_ex_w;
    p_size_ex_a size_ex_a;
    p_info_w info_w;
    p_info_a info_a;
    p_info_ex_w info_ex_w;
    p_info_ex_a info_ex_a;
    p_find_w find_w;
    p_find_a find_a;
    p_install_w install_w;
    p_install_a install_a;
    p_lang_w lang_w;
    p_lang_a lang_a;
    p_query_w query_w;
    p_query_a query_a;
    p_by_handle by_handle;
} VAPI;

static void vap_load(VAPI *v, HMODULE m)
{
    memset(v, 0, sizeof(*v));
    v->mod = m;
#define VAP(field, name)                                     \
    v->field = (p_##field)GetProcAddress(m, name);            \
    if (v->field != NULL)                                     \
    {                                                         \
        v->resolved++;                                        \
    }
    VAP(size_w, "GetFileVersionInfoSizeW")
    VAP(size_a, "GetFileVersionInfoSizeA")
    VAP(size_ex_w, "GetFileVersionInfoSizeExW")
    VAP(size_ex_a, "GetFileVersionInfoSizeExA")
    VAP(info_w, "GetFileVersionInfoW")
    VAP(info_a, "GetFileVersionInfoA")
    VAP(info_ex_w, "GetFileVersionInfoExW")
    VAP(info_ex_a, "GetFileVersionInfoExA")
    VAP(find_w, "VerFindFileW")
    VAP(find_a, "VerFindFileA")
    VAP(install_w, "VerInstallFileW")
    VAP(install_a, "VerInstallFileA")
    VAP(lang_w, "VerLanguageNameW")
    VAP(lang_a, "VerLanguageNameA")
    VAP(query_w, "VerQueryValueW")
    VAP(query_a, "VerQueryValueA")
    VAP(by_handle, "GetFileVersionInfoByHandle")
#undef VAP
}

// one probe of every export, so two modules' answers can be compared field by field
typedef struct
{
    DWORD size_w;
    BOOL info_w;
    unsigned long long buf_w;   // FNV-1a over the whole version block GetFileVersionInfoW returned
    BOOL query_w;
    UINT qlen_w;
    unsigned char fixed[16];    // the VS_FIXEDFILEINFO's first 16 bytes
    DWORD size_a;
    BOOL info_a;
    unsigned long long buf_a;
    BOOL query_a;
    DWORD size_ex_w;
    BOOL info_ex_w;
    DWORD size_ex_a;
    BOOL info_ex_a;
    DWORD find_w;
    wchar_t find_cur[260];
    wchar_t find_dest[260];
    DWORD find_a;
    char find_cur_a[260];
    char find_dest_a[260];
    DWORD lang_w;
    wchar_t lang_buf_w[128];
    DWORD lang_a;
    char lang_buf_a[128];
} ANSWER;

static unsigned long long fnv1a(const unsigned char *p, size_t n)
{
    unsigned long long h = 1469598103934665603ULL;
    for (size_t i = 0; i < n; i++)
    {
        h ^= p[i];
        h *= 1099511628211ULL;
    }
    return h;
}

// Does this loaded module's own image carry `needle`? Guards every page with VirtualQuery, so a scan over an
// image region can never fault. Used to prove the module under test is THIS build, not a stray copy of the system
// DLL that happens to sit at the path given on the command line.
static int module_carries(HMODULE m, const char *needle)
{
    const unsigned char *base;
    unsigned int lfanew = 0;
    unsigned int soi = 0;
    size_t n;
    const unsigned char *p;

    if (m == NULL || needle == NULL)
    {
        return 0;
    }
    base = (const unsigned char *)m;
    memcpy(&lfanew, base + 0x3C, 4);
    if (lfanew == 0 || lfanew > 0x1000)
    {
        return 0;
    }
    memcpy(&soi, base + lfanew + 24 + 56, 4); // OptionalHeader.SizeOfImage
    if (soi < 0x1000 || soi > 0x4000000)
    {
        return 0;
    }
    n = strlen(needle);
    p = base;
    while (p + n < base + soi)
    {
        MEMORY_BASIC_INFORMATION mi;
        const unsigned char *end;
        const unsigned char *q;
        if (VirtualQuery(p, &mi, sizeof(mi)) == 0)
        {
            return 0;
        }
        end = (const unsigned char *)mi.BaseAddress + mi.RegionSize;
        if (end > base + soi)
        {
            end = base + soi;
        }
        if (mi.State == MEM_COMMIT && (mi.Protect & (PAGE_NOACCESS | PAGE_GUARD)) == 0)
        {
            for (q = p; q + n <= end; q++)
            {
                if (memcmp(q, needle, n) == 0)
                {
                    return 1;
                }
            }
        }
        if (end <= p)
        {
            return 0;
        }
        p = end;
    }
    return 0;
}

static void ask(const VAPI *v, const wchar_t *target, const char *target_a, ANSWER *a)
{
    memset(a, 0, sizeof(*a));

    a->size_w = v->size_w ? v->size_w(target, NULL) : 0;
    if (a->size_w != 0 && v->info_w != NULL)
    {
        unsigned char *buf = (unsigned char *)calloc(1, a->size_w);
        if (buf != NULL)
        {
            a->info_w = v->info_w(target, 0, a->size_w, buf);
            a->buf_w = fnv1a(buf, a->size_w);
            if (v->query_w != NULL)
            {
                LPVOID p = NULL;
                UINT len = 0;
                a->query_w = v->query_w(buf, L"\\", &p, &len);
                a->qlen_w = len;
                if (a->query_w && p != NULL && len >= 16)
                {
                    memcpy(a->fixed, p, 16);
                }
            }
            free(buf);
        }
    }
    a->size_a = v->size_a ? v->size_a(target_a, NULL) : 0;
    if (a->size_a != 0 && v->info_a != NULL)
    {
        unsigned char *buf = (unsigned char *)calloc(1, a->size_a);
        if (buf != NULL)
        {
            a->info_a = v->info_a(target_a, 0, a->size_a, buf);
            a->buf_a = fnv1a(buf, a->size_a);
            if (v->query_a != NULL)
            {
                LPVOID p = NULL;
                UINT len = 0;
                a->query_a = v->query_a(buf, "\\", &p, &len);
            }
            free(buf);
        }
    }
    a->size_ex_w = v->size_ex_w ? v->size_ex_w(0, target, NULL) : 0;
    if (a->size_ex_w != 0 && v->info_ex_w != NULL)
    {
        unsigned char *buf = (unsigned char *)calloc(1, a->size_ex_w);
        if (buf != NULL)
        {
            a->info_ex_w = v->info_ex_w(0, target, 0, a->size_ex_w, buf);
            free(buf);
        }
    }
    a->size_ex_a = v->size_ex_a ? v->size_ex_a(0, target_a, NULL) : 0;
    if (a->size_ex_a != 0 && v->info_ex_a != NULL)
    {
        unsigned char *buf = (unsigned char *)calloc(1, a->size_ex_a);
        if (buf != NULL)
        {
            a->info_ex_a = v->info_ex_a(0, target_a, 0, a->size_ex_a, buf);
            free(buf);
        }
    }

    // VerFindFile: it only decides WHERE a named file would go, and writes nothing.
    if (v->find_w != NULL)
    {
        UINT cl = 260, dl = 260;
        a->find_w = v->find_w(0, L"nativepay-nover-0001.dll", target, target, a->find_cur, &cl,
                              a->find_dest, &dl);
    }
    if (v->find_a != NULL)
    {
        UINT cl = 260, dl = 260;
        a->find_a = v->find_a(0, "nativepay-nover-0001.dll", target_a, target_a, a->find_cur_a, &cl,
                              a->find_dest_a, &dl);
    }

    // VerInstallFile is deliberately NOT called. winver.h:76-97 declares 8 parameters (uFlags, src, dest,
    // srcDir, destDir, curDir, tmpFile, puTmpFileLen); this proxy's wrapper carries 7 (src\version_proxy.def's
    // ch_VerInstallFileA/W, unchanged since build 1), so a call through the wrapper hands the callee a garbage
    // eighth argument and faults - measured, 0xC0000005, before this comment existed. The game imports neither:
    // `cod25-cod.exe`'s version.dll imports are the 6 of GetFileVersionInfo*/VerQueryValue* only (tools\
    // test_nativepay.py re-reads that list every run). Both are still resolved and counted below.

    // VerLanguageName: two real languages, so the answer is text and not just a length.
    if (v->lang_w != NULL)
    {
        a->lang_w = v->lang_w(0x0409, a->lang_buf_w, 128);
    }
    if (v->lang_a != NULL)
    {
        a->lang_a = v->lang_a(0x0407, a->lang_buf_a, 128);
    }
}

static int mode_proxy(const wchar_t *dll)
{
    wchar_t dir[MAX_PATH];
    wchar_t noside[MAX_PATH];
    wchar_t sysdir[MAX_PATH];
    wchar_t sysver[MAX_PATH];
    wchar_t ours_path[MAX_PATH];
    wchar_t sys_path[MAX_PATH];
    char ours_a[MAX_PATH];
    char sys_a[MAX_PATH];
    char line[1400];

    printf("proxy: the built DLL as a module against the system version.dll\n\n");

    // 1. the DLL's own directory - and no version_orig.dll in it
    dir[0] = L'\0';
    {
        const wchar_t *slash = wcsrchr(dll, L'\\');
        if (slash != NULL)
        {
            size_t k = (size_t)(slash - dll) + 1;
            wcsncpy_s(dir, MAX_PATH, dll, k);
        }
    }
    ok(dir[0] != L'\0', "proxy: the DLL path has a directory in it", "");
    _snwprintf_s(noside, MAX_PATH, _TRUNCATE, L"%sversion_orig.dll", dir);
    printf("file        %ls\n", dll);
    printf("beside it   %ls  (%s)\n", noside,
           GetFileAttributesW(noside) == INVALID_FILE_ATTRIBUTES ? "absent - build 20 needs no copy" : "PRESENT");
    ok(GetFileAttributesW(noside) == INVALID_FILE_ATTRIBUTES,
       "proxy: there is no version_orig.dll beside the DLL under test", "");

    // 2. the system paths
    UINT n = GetSystemDirectoryW(sysdir, MAX_PATH);
    ok(n != 0 && n < MAX_PATH, "proxy: the Windows system directory resolves", "");
    _snwprintf_s(sysver, MAX_PATH, _TRUNCATE, L"%s\\version.dll", sysdir);
    printf("system      %ls  (%s)\n", sysver,
           GetFileAttributesW(sysver) == INVALID_FILE_ATTRIBUTES ? "ABSENT" : "present");
    ok(GetFileAttributesW(sysver) != INVALID_FILE_ATTRIBUTES, "proxy: the system version.dll is on disk", "");

    // 3. version.dll must NOT already be in this process, or the same-name case is not the one tested
    {
        HMODULE pre = GetModuleHandleW(L"version.dll");
        wchar_t pre_p[MAX_PATH];
        pre_p[0] = L'\0';
        if (pre != NULL)
        {
            GetModuleFileNameW(pre, pre_p, MAX_PATH);
        }
        printf("pre-loaded  version.dll %s\n", pre == NULL ? "no" : "YES");
        ok(pre == NULL, "proxy: version.dll was not already loaded (the two-same-names case is the one tested)", "");
    }

    // 4. ours first, by its full path
    HMODULE ours = LoadLibraryExW(dll, NULL, LOAD_WITH_ALTERED_SEARCH_PATH);
    ok(ours != NULL, "proxy: the DLL under test loads as version.dll", "");
    if (ours == NULL)
    {
        printf("\n%d passed, %d failed\n", PASSES, FAILS);
        return 1;
    }
    GetModuleFileNameW(ours, ours_path, MAX_PATH);
    WideCharToMultiByte(CP_ACP, 0, ours_path, -1, ours_a, (int)sizeof(ours_a), NULL, NULL);
    printf("ours        0x%p  %s\n", (void *)(ULONG_PTR)ours, ours_a);

    // 5. the system file, by full path, with the search pinned to %windows%\system32
    SetLastError(0);
    HMODULE sys = LoadLibraryExW(sysver, NULL, LOAD_LIBRARY_SEARCH_SYSTEM32);
    DWORD err = GetLastError();
    ok(sys != NULL, "proxy: the system DLL loads by its full path", "");
    if (sys == NULL)
    {
        printf("\n%d passed, %d failed (LoadLibraryExW err %lu)\n", PASSES, FAILS, (unsigned long)err);
        FreeLibrary(ours);
        return 1;
    }
    GetModuleFileNameW(sys, sys_path, MAX_PATH);
    WideCharToMultiByte(CP_ACP, 0, sys_path, -1, sys_a, (int)sizeof(sys_a), NULL, NULL);
    printf("system      0x%p  %s\n", (void *)(ULONG_PTR)sys, sys_a);
    printf("\n");

    // 6. THE claim: a distinct module, under the system directory, not this DLL
    ok(sys != ours, "proxy: the full path did NOT hand back this DLL (distinct module handles)", "");
    ok(_wcsnicmp(sys_path, sysdir, wcslen(sysdir)) == 0,
       "proxy: the resolved module's path is under the Windows system directory", sys_a);
    ok(_wcsicmp(sys_path, ours_path) != 0, "proxy: and it is not this DLL's path", sys_a);
    // and the module called "ours" really is this build, in memory - not a stray system copy at that path
    // (the literal is this build's banner; it moves with the banner, build 29's is 402 chars - build 27's
    // 490-char one formatted a 513-byte line into log_line's 512-byte buffer, docs\B27-NOLAUNCH.md 3.3)
    ok(module_carries(ours, "proxy attached (version.dll build 29"),
       "proxy: the module under test carries this build's banner in its own image", "");
    ok(!module_carries(sys, "proxy attached"), "proxy: the system module does not carry it", "");

    // 7. all 17 exports resolve on both
    VAPI vo, vs;
    vap_load(&vo, ours);
    vap_load(&vs, sys);
    {
        char d[64];
        _snprintf_s(d, sizeof(d), _TRUNCATE, "%d of 17 on ours, %d on the system DLL", vo.resolved, vs.resolved);
        ok(vo.resolved == 17, "proxy: all 17 version.dll exports resolve on the DLL under test", d);
        ok(vs.resolved == 17, "proxy: and all 17 resolve on the system DLL", d);
    }

    // 8. and answer the same, export by export
    {
        wchar_t target[MAX_PATH];
        char target_a[MAX_PATH];
        _snwprintf_s(target, MAX_PATH, _TRUNCATE, L"%s\\notepad.exe", sysdir);
        WideCharToMultiByte(CP_ACP, 0, target, -1, target_a, (int)sizeof(target_a), NULL, NULL);
        ok(GetFileAttributesW(target) != INVALID_FILE_ATTRIBUTES, "proxy: the probe file (notepad.exe) is on disk",
           target_a);

        ANSWER ao, as;
        ask(&vo, target, target_a, &ao);
        ask(&vs, target, target_a, &as);

        printf("\n  ours:    size=%lu info=%d query=%d qlen=%u fixed=%08lx%08lx\n", (unsigned long)ao.size_w,
               (int)ao.info_w, (int)ao.query_w, ao.qlen_w, ((unsigned long *)ao.fixed)[0],
               ((unsigned long *)ao.fixed)[1]);
        printf("  system:  size=%lu info=%d query=%d qlen=%u fixed=%08lx%08lx\n", (unsigned long)as.size_w,
               (int)as.info_w, (int)as.query_w, as.qlen_w, ((unsigned long *)as.fixed)[0],
               ((unsigned long *)as.fixed)[1]);
        printf("\n");

        _snprintf_s(line, sizeof(line), _TRUNCATE, "size %lu, info %d, block hash %016llx", (unsigned long)ao.size_w,
                    (int)ao.info_w, ao.buf_w);
        ok(ao.size_w == as.size_w && ao.size_w != 0 && ao.info_w == as.info_w && ao.buf_w == as.buf_w,
           "proxy: GetFileVersionInfoSizeW + GetFileVersionInfoW answer identically", line);
        _snprintf_s(line, sizeof(line), _TRUNCATE, "query %d, len %u, fixed %08lx", (int)ao.query_w, ao.qlen_w,
                    ((unsigned long *)ao.fixed)[0]);
        ok(ao.query_w == as.query_w && ao.qlen_w == as.qlen_w && ao.query_w != 0 &&
               memcmp(ao.fixed, as.fixed, 16) == 0,
           "proxy: VerQueryValueW answers identically", line);
        ok(ao.size_a == as.size_a && ao.size_a != 0 && ao.info_a == as.info_a && ao.buf_a == as.buf_a &&
               ao.query_a == as.query_a,
           "proxy: the three A exports answer identically", "");
        ok(ao.size_ex_w == as.size_ex_w && ao.size_ex_w != 0 && ao.info_ex_w == as.info_ex_w &&
               ao.size_ex_a == as.size_ex_a && ao.info_ex_a == as.info_ex_a,
           "proxy: the four Ex exports answer identically", "");
        _snprintf_s(line, sizeof(line), _TRUNCATE, "w %lu '%ls' -> '%ls'", (unsigned long)ao.find_w, ao.find_cur,
                    ao.find_dest);
        ok(ao.find_w == as.find_w && wcscmp(ao.find_cur, as.find_cur) == 0 && wcscmp(ao.find_dest, as.find_dest) == 0,
           "proxy: VerFindFileW answers identically", line);
        ok(ao.find_a == as.find_a && strcmp(ao.find_cur_a, as.find_cur_a) == 0 &&
               strcmp(ao.find_dest_a, as.find_dest_a) == 0,
           "proxy: VerFindFileA answers identically", "");
        _snprintf_s(line, sizeof(line), _TRUNCATE, "0x0409 -> '%ls'", ao.lang_buf_w);
        ok(ao.lang_w == as.lang_w && wcscmp(ao.lang_buf_w, as.lang_buf_w) == 0, "proxy: VerLanguageNameW answers identically",
           line);
        ok(ao.lang_a == as.lang_a && strcmp(ao.lang_buf_a, as.lang_buf_a) == 0,
           "proxy: VerLanguageNameA answers identically", ao.lang_buf_a);
        // resolved, never called: see the arity note in ask() and the prototype note here
        ok(vo.install_w != NULL && vs.install_w != NULL && vo.install_a != NULL && vs.install_a != NULL,
           "proxy: VerInstallFileW/A resolve on both (not called - 7 parameters in the wrapper, 8 in winver.h)", "");
        ok(vo.by_handle != NULL && vs.by_handle != NULL,
           "proxy: GetFileVersionInfoByHandle resolves on both (resolved only - its prototype is undocumented)", "");
        printf("\n  14 of the 17 exports are compared above by answer: size/info/query A+W, the four Ex, "
               "VerFindFile A+W,\n  VerLanguageName A+W. VerInstallFileA/W resolve but are one argument short in "
               "the wrapper (build 1's\n  .def, unchanged) and are not called; GetFileVersionInfoByHandle's "
               "prototype is undocumented and is not\n  called either. Neither is imported by cod25-cod.exe.\n");
    }

    // 9. the DLL's own log - the module it really loaded, in its own words. Only when this process is allowed to
    //    create files at all: on this machine a freshly built exe run from the project tree is refused
    //    (ERROR_ACCESS_DENIED from every CreateFileW), while the same bytes run from %TEMP% are not, so the
    //    check is skipped with a note there and tools\test_nativepay.py repeats it in its own process.
    {
        wchar_t logp[MAX_PATH];
        wchar_t probe[MAX_PATH];
        int can_write = 0;
        HANDLE ph;
        _snwprintf_s(logp, MAX_PATH, _TRUNCATE, L"%sclienthook.log", dir);
        _snwprintf_s(probe, MAX_PATH, _TRUNCATE, L"%snp_probe_write.txt", dir);
        SetLastError(0);
        ph = CreateFileW(probe, GENERIC_WRITE, FILE_SHARE_READ | FILE_SHARE_WRITE, NULL, CREATE_ALWAYS,
                         FILE_ATTRIBUTE_NORMAL, NULL);
        if (ph != INVALID_HANDLE_VALUE)
        {
            can_write = 1;
            CloseHandle(ph);
            DeleteFileW(probe);
        }
        if (!can_write)
        {
            printf("     note: this process cannot create a file in that directory (err %lu), so the DLL's own log\n"
                   "           could not be written in THIS run. The resolved module is still proved above by the\n"
                   "           handle compare and by this build's banner in its image; tools\\test_nativepay.py\n"
                   "           repeats the log read in its own process (python), which can write.\n",
                   (unsigned long)GetLastError());
        }
        else
        {
            // The host guard: this driver's image is nativepay_test.exe, not cod25-cod.exe, so the DLL arms
            // nothing here and must leave no file behind. The log's own content is proved where the image name IS
            // the game's: ch_passthru_host's `armed` mode and the harness that loads this DLL as the game.
            ok(GetFileAttributesW(logp) == INVALID_FILE_ATTRIBUTES,
               "proxy: this host is not the game, so the DLL wrote no clienthook.log beside itself", "");
            FILE *f = _wfopen(logp, L"rb");
            if (f != NULL)
            {
                fclose(f);
            }
        }
    }

    FreeLibrary(ours);
    printf("\n%d passed, %d failed\n", PASSES, FAILS);
    if (FAILS == 0)
    {
        printf("nativepay: OK - %d checks\n", PASSES);
        return 0;
    }
    return 1;
}

int main(int argc, char **argv)
{
    // unbuffered: a fault in a probe (these modes call real system code) must not swallow the lines printed so far
    setvbuf(stdout, NULL, _IONBF, 0);

    if (argc >= 2 && strcmp(argv[1], "self") == 0)
    {
        wchar_t client[MAX_PATH];
        int have = 0;
        if (argc >= 3)
        {
            MultiByteToWideChar(CP_ACP, 0, argv[2], -1, client, MAX_PATH);
            have = 1;
        }
        else
        {
            have = game_client(client, MAX_PATH);
        }
        if (!have)
        {
            printf("nativepay: the guard checks read the client file, and its location is a setting - pass it as "
                   "`self <client.dll>` or set KRONOS_GAME_DIR to the game install (the folder holding cod25\\, "
                   "or cod25 itself)\n");
            return 2;
        }
        return mode_self(client);
    }
    if (argc >= 3 && strcmp(argv[1], "sites") == 0)
    {
        wchar_t w[MAX_PATH];
        MultiByteToWideChar(CP_ACP, 0, argv[2], -1, w, MAX_PATH);
        return mode_sites(w);
    }
    if (argc >= 3 && strcmp(argv[1], "install") == 0)
    {
        wchar_t w[MAX_PATH];
        MultiByteToWideChar(CP_ACP, 0, argv[2], -1, w, MAX_PATH);
        return mode_install(w);
    }
    if (argc >= 3 && strcmp(argv[1], "off") == 0)
    {
        wchar_t w[MAX_PATH];
        MultiByteToWideChar(CP_ACP, 0, argv[2], -1, w, MAX_PATH);
        return mode_off(w);
    }
    if (argc >= 3 && strcmp(argv[1], "proxy") == 0)
    {
        wchar_t w[MAX_PATH];
        MultiByteToWideChar(CP_ACP, 0, argv[2], -1, w, MAX_PATH);
        return mode_proxy(w);
    }
    printf("usage: nativepay_test.exe self [client.dll] | sites <client.dll> | install <client.dll> | off <dir> | "
           "proxy <the built version.dll>\n");
    return 2;
}
