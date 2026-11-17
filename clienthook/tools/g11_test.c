// g11_test - the offline driver for clienthook build 15's G11 payload channel (tools\test_g11.py runs it).
//
// It links src\g11.c and nothing else: no game address, no game, no install. Five commands:
//
//   g11_test.exe self                            the unit checks, then `g11: OK - <n> checks`
//   g11_test.exe encode <bitmap.bin>            32,768 B in, 33 lines out on stdout (2,000 x 32 + 1,536)
//   g11_test.exe collect <array.bin>            n records of 0x578 B in, RECORDS/REWARD/HEADER + 33 lines out
//   g11_test.exe hash <salt16hex> <name>          the client's FUN_1800b8420 port, one 16-hex line
//   g11_test.exe sha256 <file>                    the image gate's hash path, one 64-hex line
//
// Exit 0 only when nothing failed.

#include <windows.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <wchar.h>

#include "../src/g11.h"
#include "../src/master.h"

static int CHECKS = 0;
static int FAILS = 0;

static void ok(int cond, const char *what)
{
    CHECKS++;
    if (!cond)
    {
        FAILS++;
        printf("FAIL  %s\n", what);
    }
    else
    {
        printf("pass  %s\n", what);
    }
}

static int hexval(char c)
{
    if (c >= '0' && c <= '9')
        return c - '0';
    if (c >= 'a' && c <= 'f')
        return c - 'a' + 10;
    if (c >= 'A' && c <= 'F')
        return c - 'A' + 10;
    return -1;
}

// --- the bitmap model: bit (id & 31) of dword (id >> 5), ids 1..0x3FFFF (180094030:11-15) ----------------
static void bitmap_set(unsigned char *bm, unsigned long id)
{
    if (id < 1 || id > (unsigned long)G11_MAX_ID)
    {
        return;
    }
    bm[id >> 3] |= (unsigned char)(1u << (id & 7));
}

static int bitmap_get(const unsigned char *bm, unsigned long id)
{
    if (id < 1 || id > (unsigned long)G11_MAX_ID)
    {
        return 0;
    }
    return (bm[id >> 3] >> (id & 7)) & 1;
}

// the mod's own query, in the mod's arithmetic (no bit library, no shifts in Lua) - G11-DESIGN-B15 4.6
static int nibble_locked(const char *hex, unsigned long id)
{
    if (id < 1 || id > (unsigned long)G11_MAX_ID)
    {
        return 0;
    }
    unsigned long b = id / 8;
    unsigned long r = id % 8;
    unsigned long p = b * 2 + ((r >= 4) ? 1 : 2); // 1-based hex digit: digit 1 holds bits 7..4
    int nib = hexval(hex[p - 1]);
    if (nib < 0)
    {
        return -1;
    }
    int v = (int)(nib / (1 << (r % 4)));
    return v % 2;
}

// --- the fake engine: the client's register-or-find, modelled ------------------------------------------
//
// `reg(hash, default, flags, desc)` finds a dvar by the client's name hash and CREATES it with `default` when it
// is not there (`1800968f0:69-72,88-90,107-114`). A dvar_t is modelled as a 0x100-byte block whose string-value
// pointer sits at SLOT - the same shape the client discovered for its own string dvars (`1800968f0:76-87`).
//
// The 35 names are the DLL's own list, repeated here because this driver links g11.c only; tools\test_g11.py
// checks this list against `G11_NAMES` in io_probe.c, so the two cannot drift.

#define SLOT 0x50

static const char *TEST_NAMES[] = {
    "zm_g11_arm", "zm_g11_ver",
    "zm_g11_0",  "zm_g11_1",  "zm_g11_2",  "zm_g11_3",  "zm_g11_4",  "zm_g11_5",
    "zm_g11_6",  "zm_g11_7",  "zm_g11_8",  "zm_g11_9",  "zm_g11_10", "zm_g11_11",
    "zm_g11_12", "zm_g11_13", "zm_g11_14", "zm_g11_15", "zm_g11_16", "zm_g11_17",
    "zm_g11_18", "zm_g11_19", "zm_g11_20", "zm_g11_21", "zm_g11_22", "zm_g11_23",
    "zm_g11_24", "zm_g11_25", "zm_g11_26", "zm_g11_27", "zm_g11_28", "zm_g11_29",
    "zm_g11_30", "zm_g11_31", "zm_g11_32"};
#define TEST_N ((int)(sizeof(TEST_NAMES) / sizeof(TEST_NAMES[0])))

static const unsigned char SALT16[16] = {0x71, 0x36, 0x6e, 0x2d, 0x2b, 0x37, 0x3d, 0x74,
                                         0x79, 0x79, 0x74, 0x67, 0x39, 0x34, 0x5f, 0x2a};

typedef struct
{
    unsigned long long hash;
    void *dvar;
    int created; // 1 = the engine made this one on a call, 0 = it was already there
} FAKE_ENTRY;

typedef struct
{
    FAKE_ENTRY e[TEST_N + 8];
    int n;
    int created;    // calls that returned a new dvar
    int found;      // calls that returned an existing one
    int refuse_at;  // index (in call order) that returns NULL, or -1
    int calls;
    unsigned char *mem[TEST_N + 8];
} FAKE_ENGINE;

static FAKE_ENGINE *FAKE;

static void *fake_reg(unsigned long long hash, const char *def, int flags, const char *desc)
{
    (void)flags;
    (void)desc;
    if (FAKE == NULL || def == NULL)
    {
        return NULL;
    }
    if (FAKE->refuse_at >= 0 && FAKE->calls == FAKE->refuse_at)
    {
        FAKE->calls++;
        return NULL;
    }
    FAKE->calls++;
    for (int i = 0; i < FAKE->n; i++)
    {
        if (FAKE->e[i].hash == hash)
        {
            FAKE->found++;
            return FAKE->e[i].dvar;
        }
    }
    unsigned char *d = (unsigned char *)malloc(0x100);
    char *v = (char *)malloc(strlen(def) + 1);
    if (d == NULL || v == NULL)
    {
        return NULL;
    }
    memset(d, 0, 0x100);
    memcpy(v, def, strlen(def) + 1);
    *(char **)(d + SLOT) = v;
    FAKE->e[FAKE->n].hash = hash;
    FAKE->e[FAKE->n].dvar = d;
    FAKE->e[FAKE->n].created = 1;
    FAKE->mem[FAKE->n] = d;
    FAKE->n++;
    FAKE->created++;
    return d;
}

static void fake_reset(FAKE_ENGINE *f)
{
    memset(f, 0, sizeof(*f));
    f->refuse_at = -1;
    FAKE = f;
}

// Seed one dvar the way the mod's GSC would, without going through the fake's create path.
static void fake_seed(FAKE_ENGINE *f, int idx, const char *value)
{
    unsigned char *d = (unsigned char *)malloc(0x100);
    char *v = (char *)malloc(strlen(value) + 1);
    memset(d, 0, 0x100);
    memcpy(v, value, strlen(value) + 1);
    *(char **)(d + SLOT) = v;
    f->e[f->n].hash = g11_hash_name(TEST_NAMES[idx], SALT16);
    f->e[f->n].dvar = d;
    f->e[f->n].created = 0;
    f->mem[f->n] = d;
    f->n++;
}

static void fake_free(FAKE_ENGINE *f)
{
    for (int i = 0; i < f->n; i++)
    {
        free(*(char **)(f->mem[i] + SLOT));
        free(f->mem[i]);
    }
    f->n = 0;
    if (FAKE == f)
    {
        FAKE = NULL;
    }
}

static int self_checks(const char *saltfile)
{
    (void)saltfile;

    // 1. the encoder: 4 bytes -> 8 chars, lowercase, NUL-terminated
    {
        const unsigned char in[4] = {0x00, 0x0F, 0x10, 0xFF};
        char out[9];
        memset(out, 'x', sizeof(out));
        g11_hex(in, 4, out);
        ok(strcmp(out, "000f10ff") == 0, "encoder: 00 0f 10 ff -> 000f10ff");
        ok(out[8] == '\0', "encoder: NUL-terminated");
    }

    // 2. the splitter: 33 parts, 2,000 chars each except the last, and 32,768 B of bitmap in total
    {
        ok(g11_part_chars(0) == 2000, "split: part 0 holds 2,000 chars");
        ok(g11_part_chars(31) == 2000, "split: part 31 holds 2,000 chars");
        ok(g11_part_chars(32) == 1536, "split: part 32 holds 1,536 chars");
        ok(g11_part_chars(33) == 0 && g11_part_chars(-1) == 0, "split: only 33 parts exist");
        size_t sum = 0, bytes = 0;
        for (int i = 0; i < G11_PARTS; i++)
        {
            sum += g11_part_chars(i);
            bytes += g11_part_chars(i) / 2;
            if (g11_part_chars(i) > 2047)
            {
                ok(0, "split: a part exceeds the 2,047-char Lua read cap");
            }
        }
        ok(sum == G11_HEX, "split: the 33 parts add up to 65,536 chars");
        ok(bytes == G11_BITMAP_BYTES, "split: and to 32,768 bitmap bytes");
        ok(g11_part_offset(1) == 2000 && g11_part_offset(32) == 64000, "split: offsets are 2,000 apart");
    }

    // 3. round trip: a known bitmap through the encoder and the 33 parts, back through the mod's query
    {
        static unsigned char bm[G11_BITMAP_BYTES];
        static char parts[G11_PARTS][G11_PART_CHARS + 1];
        static char full[G11_HEX + 1];
        memset(bm, 0, sizeof(bm));
        const unsigned long ids[] = {1, 2, 31, 32, 33, 1425, 89575, 96171, 96192, 96202, 101417, 102671,
                                     111457, 126597, 126619, 154735, 262143};
        for (size_t i = 0; i < sizeof(ids) / sizeof(ids[0]); i++)
        {
            bitmap_set(bm, ids[i]);
        }
        size_t pos = 0;
        for (int i = 0; i < G11_PARTS; i++)
        {
            size_t off = g11_part_offset(i) / 2;
            size_t len = g11_part_chars(i) / 2;
            g11_hex(bm + off, len, parts[i]);
            memcpy(full + pos, parts[i], g11_part_chars(i));
            pos += g11_part_chars(i);
        }
        full[G11_HEX] = '\0';
        ok(pos == G11_HEX, "split: the parts concatenate to 65,536 chars");
        ok(strlen(parts[0]) == 2000 && strlen(parts[32]) == 1536, "split: every part is a complete string");
        int bad = 0;
        for (size_t i = 0; i < sizeof(ids) / sizeof(ids[0]); i++)
        {
            if (nibble_locked(full, ids[i]) != 1)
            {
                bad++;
            }
        }
        for (unsigned long id = 0; id < 300000UL; id++)
        {
            if (nibble_locked(full, id) != bitmap_get(bm, id))
            {
                bad++;
                if (bad > 5)
                {
                    break;
                }
            }
        }
        ok(bad == 0, "query: the mod's nibble expression reads every id 0..299,999 as the bitmap does");
        ok(g11_count_ids(full, G11_HEX) == (int)(sizeof(ids) / sizeof(ids[0])),
           "count: the popcount equals the number of ids set");
    }

    // 4. the header the mod parses
    {
        char ver[G11_VER_CAP];
        int n = g11_ver(ver, sizeof(ver), 17u, G11_PARTS, G11_HEX);
        ok(n > 0 && strcmp(ver, "17:33:65536") == 0, "header: serial:parts:chars -> 17:33:65536");
        ok(g11_ver(ver, sizeof(ver), 4294967295u, G11_PARTS, G11_HEX) > 0 &&
               strcmp(ver, "4294967295:33:65536") == 0,
           "header: the serial is unsigned 32-bit");
    }

    // 5. the canary validator the arm step uses, on the same shapes the client checks (1800968f0:76-83)
    {
        static const char good[] = "g11";
        static const char wrong[] = "g11n";
        ok(g11_page_ok(good) == 1, "canary: a committed string's page is readable");
        ok(g11_sentinel_ok(good, G11_SENTINEL) == 1, "canary: \"g11\" passes");
        ok(g11_sentinel_ok(wrong, G11_SENTINEL) == 0, "canary: \"g11n\" does not pass (the probe default)");
        ok(g11_sentinel_ok(NULL, G11_SENTINEL) == 0, "canary: a null pointer does not pass");
        ok(g11_sentinel_ok((const void *)1, G11_SENTINEL) == 0, "canary: an unmapped address does not pass");
        ok(g11_page_writable(good) == 0, "canary: a read-only page is not writable");
        char heap[8];
        memcpy(heap, "g11", 4);
        ok(g11_page_writable(heap) == 1, "canary: a writable page is writable");
    }

    // 6. the slot offset rule: 0..0xFF and 8-aligned (1800968f0:87's discovery loop)
    {
        ok(g11_slot_ok(-1) == 0, "slot: -1 (the client's own not-found value) is rejected");
        ok(g11_slot_ok(0x100) == 0, "slot: 0x100 is rejected");
        ok(g11_slot_ok(4) == 0, "slot: 4 is rejected (not 8-aligned)");
        ok(g11_slot_ok(0) == 1 && g11_slot_ok(0xF8) == 1, "slot: 0 and 0xF8 are accepted");
    }

    // 7. the latch: the only way this build can write twice into a session it refused
    {
        G11GATE g;
        memset(&g, 0, sizeof(g));
        ok(g11_gate(&g, G11_WAIT, NULL) == 0 && g.state == G11_WAIT, "latch: waiting does not arm");
        ok(g11_gate(&g, G11_WAIT, NULL) == 0 && g.state == G11_WAIT, "latch: waiting still does not latch");
        ok(g11_gate(&g, G11_OK, NULL) == 1 && g.state == G11_OK, "latch: ok arms");
        ok(g11_gate(&g, G11_REFUSE, "why-1") == 0 && g.state == G11_REFUSE, "latch: refuse latches");
        ok(g.why != NULL && strcmp(g.why, "why-1") == 0, "latch: the first reason is kept");
        ok(g11_gate(&g, G11_OK, NULL) == 0 && g.state == G11_REFUSE, "latch: no later ok re-opens it");
        ok(g11_gate(&g, G11_REFUSE, "why-2") == 0 && strcmp(g.why, "why-1") == 0,
           "latch: a later refusal does not overwrite the reason");
        ok(g.refusals == 1, "latch: later refusals are counted");
    }

    // 8. the client's name hash. The salt is the client's own 16 bytes at rva 0x16ED38 (1800b8420:18,24) and
    //    the expected values are the client's own constants: `zm_ch_ver` is `DV_CH_VER` in the installed
    //    LUIFPSCounter.lua:2525, and `zm_ch_s0..s95` are its 96 DV_CH_PARTS names (:2526-2551).
    {
        static const unsigned char salt[16] = {0x71, 0x36, 0x6e, 0x2d, 0x2b, 0x37, 0x3d, 0x74,
                                               0x79, 0x79, 0x74, 0x67, 0x39, 0x34, 0x5f, 0x2a};
        struct
        {
            const char *name;
            const char *hash;
        } KNOWN[] = {
            {"zm_ch_ver", "e621c4c8cb4b6a1d"},
            {"zm_ch_state", "de9c5cd1259caedd"},
            {"zm_ch_s0", "1a2f59e42a21e7f3"},
            {"zm_ch_s1", "1a2f58e42a21e5c0"},
            {"zm_ch_s2", "1a2f5be42a21ec59"},
            {"zm_ch_s95", "b82982c8a8b324b7"},
            {"zm_ch_s96", "b82983c8a8b326ea"},
            {"zm_g11_arm", "f9b17c8eaed9d8a6"},
            {"zm_g11_ver", "e904748de8105869"},
            {"zm_g11_0", "dc82c22041372fc4"},
            {"zm_g11_32", "2acdf4ef6c6cb61d"},
            {"kronos_g11_scope", "8ac08c598be484ef"},
        };
        int bad = 0;
        for (size_t i = 0; i < sizeof(KNOWN) / sizeof(KNOWN[0]); i++)
        {
            unsigned long long h = g11_hash_name(KNOWN[i].name, salt);
            char got[17];
            _snprintf_s(got, sizeof(got), _TRUNCATE, "%016llx", h);
            if (strcmp(got, KNOWN[i].hash) != 0)
            {
                printf("FAIL  hash %s -> %s, want %s\n", KNOWN[i].name, got, KNOWN[i].hash);
                bad++;
            }
        }
        ok(bad == 0, "hash: the client's own constants reproduce (zm_ch_ver, zm_ch_s0/s1/s2/s95/s96, g11 names)");
        // the hash is case-insensitive on the name, like the client's tolower() loop (:17-31)
        ok(g11_hash_name("ZM_G11_ARM", salt) == g11_hash_name("zm_g11_arm", salt),
           "hash: names are case-insensitive");
    }

    // 9. the create-and-validate pass (build 16, D16.4): the hook makes the dvars itself, through the client's
    //    own register-or-find, so the payload no longer waits for a match. These checks run the real g11_dvar_pass
    //    against a model of that call, so "either order works" and "a second pass creates nothing" are measured.
    {
        static void *dv[TEST_N];
        static FAKE_ENGINE f;
        G11CREATE r;
        int bad, i;

        // (a) the hook is first: 35 created, 35 usable, every value the sentinel
        fake_reset(&f);
        r = g11_dvar_pass(fake_reg, SALT16, TEST_NAMES, TEST_N, SLOT, dv);
        ok(r.usable == TEST_N && r.bad == -1 && r.reason == G11_D_OK,
           "create: an empty engine -> all 35 usable");
        ok(f.created == TEST_N && f.found == 0, "create: it created exactly the 35 names, nothing else");
        bad = 0;
        for (i = 0; i < TEST_N; i++)
        {
            if (strcmp(*(char **)((char *)f.e[i].dvar + SLOT), G11_SENTINEL) != 0)
            {
                bad++;
            }
            if (f.e[i].hash != g11_hash_name(TEST_NAMES[i], SALT16) || dv[i] != f.e[i].dvar)
            {
                bad++;
            }
        }
        ok(bad == 0, "create: the sentinel is the value and the names are the list, in order");

        // (b) idempotent: the second pass finds all 35 and creates none, and changes no value
        {
            int created = f.created;
            f.found = 0;
            r = g11_dvar_pass(fake_reg, SALT16, TEST_NAMES, TEST_N, SLOT, dv);
            ok(r.usable == TEST_N && r.bad == -1, "create: a second pass still validates all 35");
            ok(f.created == created && f.found == TEST_N, "create: a second pass creates nothing (idempotent)");
            ok(strcmp(*(char **)((char *)f.e[0].dvar + SLOT), G11_SENTINEL) == 0,
               "create: and the value is still the sentinel");
        }
        fake_free(&f);

        // (c) the mod's GSC was first (the shipped order until now): found, never created - build 15's path
        fake_reset(&f);
        for (i = 0; i < TEST_N; i++)
        {
            fake_seed(&f, i, G11_SENTINEL);
        }
        r = g11_dvar_pass(fake_reg, SALT16, TEST_NAMES, TEST_N, SLOT, dv);
        ok(r.usable == TEST_N && f.created == 0 && f.found == TEST_N,
           "create: the GSC first -> all 35 found, none created");
        fake_free(&f);

        // (d) build 15's probe default sitting in a slot is not ours to write: refused, and the index names it
        fake_reset(&f);
        fake_seed(&f, 0, G11_PROBE);
        for (i = 1; i < TEST_N; i++)
        {
            fake_seed(&f, i, G11_SENTINEL);
        }
        r = g11_dvar_pass(fake_reg, SALT16, TEST_NAMES, TEST_N, SLOT, dv);
        ok(r.usable == 0 && r.bad == 0 && r.reason == G11_D_VALUE,
           "create: a slot holding \"g11n\" refuses the pass at index 0");
        fake_free(&f);

        // (e) one foreign value mid-list refuses the whole pass - nothing is written on a partial set
        fake_free(&f);
        fake_reset(&f);
        for (i = 0; i < TEST_N; i++)
        {
            fake_seed(&f, i, (i == 7) ? "someone else" : G11_SENTINEL);
        }
        r = g11_dvar_pass(fake_reg, SALT16, TEST_NAMES, TEST_N, SLOT, dv);
        {
            char msg[160];
            int nulls = 0;
            for (i = 0; i < TEST_N; i++)
            {
                if (dv[i] == NULL)
                {
                    nulls++;
                }
            }
            _snprintf_s(msg, sizeof(msg), _TRUNCATE,
                        "create: one foreign value (index 7) refuses the whole pass (usable %d, bad %d, reason %d, "
                        "%d of 35 slots left null)",
                        r.usable, r.bad, r.reason, nulls);
            ok(r.usable != TEST_N && r.bad == 7 && r.reason == G11_D_VALUE && nulls == TEST_N, msg);
        }
        fake_free(&f);

        // (f) the engine hands back nothing (the register pointer has not resolved): a name and no latch
        fake_reset(&f);
        f.refuse_at = 3;
        r = g11_dvar_pass(fake_reg, SALT16, TEST_NAMES, TEST_N, SLOT, dv);
        {
            char msg[160];
            _snprintf_s(msg, sizeof(msg), _TRUNCATE,
                        "create: a null return names the dvar and waits (usable %d, bad %d, reason %d)",
                        r.usable, r.bad, r.reason);
            ok(r.usable != TEST_N && r.bad == 3 && r.reason == G11_D_NULL && dv[0] == NULL, msg);
        }
        fake_free(&f);

        // (g) the arguments
        fake_reset(&f);
        r = g11_dvar_pass(NULL, SALT16, TEST_NAMES, TEST_N, SLOT, dv);
        ok(r.usable == 0 && r.reason == G11_D_NULL, "create: no register function -> nothing usable");
        r = g11_dvar_pass(fake_reg, SALT16, NULL, TEST_N, SLOT, dv);
        ok(r.usable == 0 && r.reason == G11_D_NULL, "create: no name list -> nothing usable");
        fake_free(&f);
    }

    // 10. the reward set's walk (build 30): the row's own tier count is the bound, three ids a tier, and the
    //     game's own id guard (id - 1 < 0x3FFFF) drops 0 and 0x40000
    {
        static unsigned char recs[2 * MASTER_STRIDE];
        static unsigned char set[G11_BITMAP_BYTES];
        memset(recs, 0, sizeof(recs));
        // record 0, two tiers: {0, 1, 0x3FFFF} then {0x40000, 0, 0} - two ids survive the guard
        *(int *)(recs + MASTER_REC_COUNT) = 2;
        {
            unsigned *a = (unsigned *)(recs + MASTER_REC_TIER_LOOT);
            a[0] = 0;
            a[1] = 1;
            a[2] = (unsigned)G11_MAX_ID;
            a[3] = 0x40000;
        }
        // record 1, no tiers - and a first block full of ids the walk must never reach
        *(int *)(recs + MASTER_STRIDE + MASTER_REC_COUNT) = 0;
        {
            unsigned *b = (unsigned *)(recs + MASTER_STRIDE + MASTER_REC_TIER_LOOT);
            b[0] = 2;
            b[1] = 3;
            b[2] = 4;
        }
        int n = g12_collect(recs, 2, set);
        ok(n == 2 && bitmap_get(set, 1) == 1 && bitmap_get(set, (unsigned long)G11_MAX_ID) == 1 &&
               bitmap_get(set, 0) == 0 && bitmap_get(set, 2) == 0 && bitmap_get(set, 0x40000) == 0,
           "g12: the walk keeps 1..0x3FFFF, drops 0 and 0x40000, and stops at the row's own tier count");

        // and a row with no tiers at all contributes nothing
        *(int *)(recs + MASTER_REC_COUNT) = 0;
        ok(g12_collect(recs, 2, set) == 0, "g12: a row with no tiers contributes nothing");

        // the kill switch: absent in a clean directory, present once its own file is there. The scratch lives
        // beside the driver (its own directory is writable), not in %TEMP% - the function takes the directory.
        {
            wchar_t dir[MAX_PATH];
            wchar_t sub[MAX_PATH];
            wchar_t probe[MAX_PATH];
            wchar_t f[MAX_PATH];
            int sw = 0;
            if (GetModuleFileNameW(NULL, dir, MAX_PATH) > 0)
            {
                wchar_t *slash = wcsrchr(dir, L'\\');
                if (slash != NULL)
                {
                    slash[1] = L'\0';
                    _snwprintf_s(sub, MAX_PATH, _TRUNCATE, L"%sg11test-%lu", dir,
                                 (unsigned long)GetCurrentProcessId());
                    CreateDirectoryW(sub, NULL);
                    // the switch takes a directory that ends in a separator, the shape GetTempPathW hands back
                    _snwprintf_s(probe, MAX_PATH, _TRUNCATE, L"%s\\", sub);
                    sw = (g12_off_present(probe) == 0);
                    _snwprintf_s(f, MAX_PATH, _TRUNCATE, L"%s\\progression-tuning", sub);
                    CreateDirectoryW(f, NULL);
                    _snwprintf_s(f, MAX_PATH, _TRUNCATE, L"%s\\progression-tuning\\rewards_off.txt", sub);
                    HANDLE h = CreateFileW(f, GENERIC_WRITE, 0, NULL, CREATE_ALWAYS, FILE_ATTRIBUTE_NORMAL, NULL);
                    if (h != INVALID_HANDLE_VALUE)
                    {
                        CloseHandle(h);
                    }
                    sw = sw && (g12_off_present(probe) == 1);
                    DeleteFileW(f);
                    _snwprintf_s(f, MAX_PATH, _TRUNCATE, L"%s\\progression-tuning", sub);
                    RemoveDirectoryW(f);
                    RemoveDirectoryW(sub);
                }
            }
            ok(sw == 1, "g12: the kill switch reads absent in a clean directory and present with its own file");
        }
    }

    printf("\n%d checks, %d failed\n", CHECKS, FAILS);
    if (FAILS == 0)
    {
        printf("g11: OK - %d checks\n", CHECKS);
        return 0;
    }
    printf("g11: FAIL - %d of %d checks\n", FAILS, CHECKS);
    return 1;
}

static int cmd_encode(const char *inpath)
{
    FILE *f = fopen(inpath, "rb");
    if (f == NULL)
    {
        printf("g11: cannot open %s\n", inpath);
        return 2;
    }
    static unsigned char bm[G11_BITMAP_BYTES + 1];
    size_t got = fread(bm, 1, sizeof(bm), f);
    fclose(f);
    if (got != G11_BITMAP_BYTES)
    {
        printf("g11: %s holds %lu B, expected %d\n", inpath, (unsigned long)got, G11_BITMAP_BYTES);
        return 2;
    }
    // The 33 parts go to stdout: a freshly built exe is not allowed to write into this machine's
    // %TEMP%\progression-tuning scratch, and the caller only ever wants to compare the bytes anyway.
    for (int i = 0; i < G11_PARTS; i++)
    {
        static char line[G11_PART_CHARS + 1];
        size_t off = g11_part_offset(i) / 2;
        size_t len = g11_part_chars(i) / 2;
        g11_hex(bm + off, len, line);
        printf("%s\n", line);
    }
    fflush(stdout);
    return 0;
}

// The reward set's walk over a staged record array: n = filesize / MASTER_STRIDE records, straight out of
// g12_collect. RECORDS/REWARD/HEADER first (the header through the shipped g11_ver, so the count, the 33 parts
// and the 65,536 hex chars are the shipped numbers), then the 33 parts.
static int cmd_collect(const char *inpath)
{
    FILE *f = fopen(inpath, "rb");
    if (f == NULL)
    {
        printf("g11: cannot open %s\n", inpath);
        return 2;
    }
    if (fseek(f, 0, SEEK_END) != 0)
    {
        fclose(f);
        printf("g11: cannot size %s\n", inpath);
        return 2;
    }
    long sz = ftell(f);
    if (sz <= 0 || (sz % MASTER_STRIDE) != 0)
    {
        fclose(f);
        printf("g11: %s holds %ld B, not a multiple of %d\n", inpath, sz, MASTER_STRIDE);
        return 2;
    }
    rewind(f);
    int n = (int)(sz / MASTER_STRIDE);
    unsigned char *recs = (unsigned char *)malloc((size_t)sz);
    if (recs == NULL)
    {
        fclose(f);
        printf("g11: no memory for %ld B\n", sz);
        return 2;
    }
    size_t got = fread(recs, 1, (size_t)sz, f);
    fclose(f);
    if (got != (size_t)sz)
    {
        free(recs);
        printf("g11: %s gave %lu B of %ld\n", inpath, (unsigned long)got, sz);
        return 2;
    }
    static unsigned char set[G11_BITMAP_BYTES];
    int count = g12_collect(recs, n, set);
    free(recs);
    printf("RECORDS %d\n", n);
    printf("REWARD %d\n", count);
    char ver[G11_VER_CAP];
    if (g11_ver(ver, sizeof(ver), (unsigned)count, G11_PARTS, G11_HEX) > 0)
    {
        printf("HEADER %s\n", ver);
    }
    for (int i = 0; i < G11_PARTS; i++)
    {
        static char line[G11_PART_CHARS + 1];
        size_t off = g11_part_offset(i) / 2;
        size_t len = g11_part_chars(i) / 2;
        g11_hex(set + off, len, line);
        printf("%s\n", line);
    }
    fflush(stdout);
    return 0;
}

static int cmd_hash(const char *salt_hex, const char *name)
{
    unsigned char salt[16];
    if (strlen(salt_hex) != 32)
    {
        printf("g11: the salt must be 32 hex chars\n");
        return 2;
    }
    for (int i = 0; i < 16; i++)
    {
        int hi = hexval(salt_hex[i * 2]);
        int lo = hexval(salt_hex[i * 2 + 1]);
        if (hi < 0 || lo < 0)
        {
            printf("g11: the salt is not hex\n");
            return 2;
        }
        salt[i] = (unsigned char)(hi * 16 + lo);
    }
    printf("%016llx\n", g11_hash_name(name, salt));
    return 0;
}

static int cmd_sha256(const char *path)
{
    wchar_t wide[MAX_PATH];
    if (MultiByteToWideChar(CP_ACP, 0, path, -1, wide, MAX_PATH) <= 0)
    {
        printf("g11: bad path\n");
        return 2;
    }
    unsigned char sha[32];
    if (g11_sha256_file(wide, sha) != 0)
    {
        printf("g11: the hash could not be computed\n");
        return 2;
    }
    char hex[65];
    g11_hex32(sha, hex);
    printf("%s\n", hex);
    return 0;
}

int main(int argc, char **argv)
{
    if (argc >= 2 && strcmp(argv[1], "self") == 0)
    {
        return self_checks(argc >= 3 ? argv[2] : NULL);
    }
    if (argc >= 3 && strcmp(argv[1], "encode") == 0)
    {
        return cmd_encode(argv[2]);
    }
    if (argc >= 3 && strcmp(argv[1], "collect") == 0)
    {
        return cmd_collect(argv[2]);
    }
    if (argc >= 4 && strcmp(argv[1], "hash") == 0)
    {
        return cmd_hash(argv[2], argv[3]);
    }
    if (argc >= 3 && strcmp(argv[1], "sha256") == 0)
    {
        return cmd_sha256(argv[2]);
    }
    printf("usage: g11_test.exe self | encode <in.bin> | collect <array.bin> | hash <salt32hex> <name> | "
           "sha256 <file>\n");
    return 2;
}
