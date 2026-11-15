// master_test - the offline driver for clienthook build 16's master-prestige formula (tools\test_master.py).
//
// Links src\master.c and nothing else. No client address is read, the game is never launched, and nothing is
// installed; `master_install` is never called (its `ch_logf` is stubbed below so the link has a definition).
//
//   master_test.exe self                          the unit checks, then `master: OK - <n> checks`
//   master_test.exe level <count> <step> <xp>     one line: "<prestige> <level>" for prestige 0..2, or "-1"
//   master_test.exe step <text>                   the setting's parser, one line: "<n>"
//
// Exit 0 only when nothing failed.

#include <windows.h>
#include <stdarg.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "../src/master.h"

static int CHECKS = 0;
static int FAILS = 0;

// master.c logs through proxy_main.c's ch_logf; the test never installs, so this only has to exist and be loud
// if it is ever called.
void ch_logf(const char *fmt, ...)
{
    va_list ap;
    va_start(ap, fmt);
    printf("LOG   ");
    vprintf(fmt, ap);
    printf("\n");
    va_end(ap);
}

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

// A 47-threshold ladder shaped like a sat_ row: 1,000 then +1,200 each, last = 56,200.
#define N47 47
static unsigned THR47[N47];

static void fill_thr(unsigned *thr, int n, unsigned first, unsigned step)
{
    unsigned v = first;
    for (int i = 0; i < n; i++)
    {
        thr[i] = v;
        v += step;
    }
}

static int self_checks(void)
{
    fill_thr(THR47, N47, 1000u, 1200u);
    const unsigned last = 56200u;   // THR47[N47-1] = 1000 + 46 x 1200, checked below
    const int count = N47;
    ok(THR47[N47 - 1] == last, "ladder: the model's last threshold is 56,200");

    // 1. the client's own walk, which is the answer this build must never change below the band
    {
        ok(master_client_level(0, N47, THR47) == 0, "client: 0 XP -> level 0");
        ok(master_client_level(999, N47, THR47) == 0, "client: 999 XP is below the first threshold -> 0");
        ok(master_client_level(1000, N47, THR47) == 1, "client: exactly the first threshold -> 1");
        ok(master_client_level(last - 1, N47, THR47) == 46, "client: one XP short of the last -> 46");
        ok((int)master_client_level(last, N47, THR47) == count, "client: exactly the last -> count (47)");
        ok((int)master_client_level(last + 1, N47, THR47) == count, "client: past the last -> count (no track)");
        ok(master_client_level(0, 0, THR47) == 0, "client: no thresholds and 0 XP -> 0");
        ok(master_client_level(1, 0, THR47) == 1, "client: no thresholds and XP -> 1 (180096680:88-91)");
    }

    // 2. prestige 0 and 1: this build writes nothing at all (-1), at every XP
    {
        const unsigned long long xps[] = {0, last - 1, last, last + 1799, last + 1800, 1000000};
        int bad = 0;
        for (size_t i = 0; i < sizeof(xps) / sizeof(xps[0]); i++)
        {
            if (master_level(xps[i], N47, THR47, 0, MASTER_STEP_DEFAULT) != -1)
                bad++;
            if (master_level(xps[i], N47, THR47, 1, MASTER_STEP_DEFAULT) != -1)
                bad++;
        }
        ok(bad == 0, "prestige 0 and 1: untouched at every XP (the client's own behaviour)");
        ok(master_level(last + 1800, N47, THR47, 2, 0) == -1, "prestige 2 with step 0: refused, not divided");
    }

    // 3. the master band, at the boundaries the client's own step gives
    {
        ok(master_level(0, N47, THR47, 2, MASTER_STEP_DEFAULT) == 0, "band: 0 XP at prestige 2 -> 0");
        ok((int)master_level(last - 1, N47, THR47, 2, MASTER_STEP_DEFAULT) == 46,
           "band: one XP short of the last -> 46 (still the client's own)");
        ok((int)master_level(last, N47, THR47, 2, MASTER_STEP_DEFAULT) == count,
           "band: at the last threshold -> count (47)");
        ok((int)master_level(last + 1799, N47, THR47, 2, MASTER_STEP_DEFAULT) == count,
           "band: +1,799 -> the same level (47)");
        ok((int)master_level(last + 1800, N47, THR47, 2, MASTER_STEP_DEFAULT) == count + 1,
           "band: +1,800 -> one more (48)");
        ok((int)master_level(last + 5000, N47, THR47, 2, MASTER_STEP_DEFAULT) == count + 2,
           "band: +5,000 -> two more (49)");
        ok((int)master_level(1000000ULL, N47, THR47, 2, MASTER_STEP_DEFAULT) == MASTER_LEVEL_CAP,
           "band: far past the end -> capped at 250");
        ok((int)master_level(last + 203ULL * 1800ULL, N47, THR47, 2, MASTER_STEP_DEFAULT) == MASTER_LEVEL_CAP,
           "band: the first XP that reaches 250 (47 + 203)");
        ok((int)master_level(last + 202ULL * 1800ULL + 1799ULL, N47, THR47, 2, MASTER_STEP_DEFAULT) ==
               MASTER_LEVEL_CAP - 1,
           "band: one step short of it is 249");
        ok((int)master_level(last + 1800, N47, THR47, 3, MASTER_STEP_DEFAULT) == count + 1,
           "band: prestige 3 behaves as 2 (the band is prestige >= 2)");
        ok((int)master_level(0xFFFFFFFFFFFFULL, N47, THR47, 2, MASTER_STEP_DEFAULT) == MASTER_LEVEL_CAP,
           "band: no overflow at 2^48 XP");
    }

    // 4. the step is the setting, and it is honoured (D16.2 keeps it a switch)
    {
        ok((int)master_level(last + 2500, N47, THR47, 2, 1000) == count + 2, "step 1,000: +2,500 -> two levels");
        ok((int)master_level(last + 2500, N47, THR47, 2, 5000) == count, "step 5,000: +2,500 -> no level yet");
        ok((int)master_level(last + 5000, N47, THR47, 2, 5000) == count + 1, "step 5,000: +5,000 -> one level");
        ok((int)master_level(last + 7500, N47, THR47, 2, 10000) == count, "step 10,000: +7,500 -> none");
        ok((int)master_level(last + 10000, N47, THR47, 2, 10000) == count + 1, "step 10,000: +10,000 -> one");
        ok((int)master_level(last + 100000ULL * 2500ULL, N47, THR47, 2, 2500) == MASTER_LEVEL_CAP,
           "a small step still cannot pass the cap");
    }

    // 5. shapes that are not a weapon ladder: no thresholds, a count past the record's ceiling
    {
        ok(master_level(0, 0, THR47, 2, MASTER_STEP_DEFAULT) == 0, "count 0: 0 XP -> 0 (no band)");
        ok(master_level(500, 0, THR47, 2, MASTER_STEP_DEFAULT) == 1, "count 0: XP -> 1 (the client's answer)");
        ok(master_level(1ULL, 65, THR47, 2, MASTER_STEP_DEFAULT) == -1,
           "count 65 is past the record's 64 (1800950d0:42): refused");
        ok(master_level(1ULL, -1, THR47, 2, MASTER_STEP_DEFAULT) == -1, "a negative count: refused");
        ok(master_level(1ULL, N47, NULL, 2, MASTER_STEP_DEFAULT) == -1, "no threshold array: refused");
    }

    // 6. the setting's parser
    {
        ok(master_step_parse(NULL, 0) == MASTER_STEP_DEFAULT, "step: absent -> 1,800");
        ok(master_step_parse("", 0) == MASTER_STEP_DEFAULT, "step: empty -> 1,800");
        ok(master_step_parse("2500", 4) == 2500, "step: \"2500\" -> 2500");
        ok(master_step_parse("2500\r\n", 6) == 2500, "step: a CRLF file -> 2500");
        ok(master_step_parse("  5000  ", 8) == 5000, "step: surrounding spaces -> 5000");
        ok(master_step_parse("1", 1) == 1, "step: the minimum 1 is accepted");
        ok(master_step_parse("1000000", 7) == 1000000, "step: the maximum 1,000,000 is accepted");
        ok(master_step_parse("0", 1) == MASTER_STEP_DEFAULT, "step: 0 -> the default (no division by zero)");
        ok(master_step_parse("1000001", 7) == MASTER_STEP_DEFAULT, "step: above the maximum -> the default");
        ok(master_step_parse("abc", 3) == MASTER_STEP_DEFAULT, "step: not a number -> the default");
        ok(master_step_parse("-2500", 5) == MASTER_STEP_DEFAULT, "step: negative -> the default");
        ok(master_step_parse("2500abc", 7) == 2500, "step: trailing junk after the digits is ignored");
    }

    // 7. the signature, against the client's own bytes and one wrong one
    {
        static unsigned char good[MASTER_PROLOGUE_LEN + 8];
        memcpy(good, MASTER_PROLOGUE, MASTER_PROLOGUE_LEN);
        ok(MASTER_PROLOGUE_LEN == 17, "signature: the prologue is 17 bytes (disasm: 0x96680..0x96690)");
        ok(MASTER_PROLOGUE[0] == 0x40 && MASTER_PROLOGUE[1] == 0x53, "signature: it starts `push rbx`");
        ok(MASTER_PROLOGUE[13] == 0x48 && MASTER_PROLOGUE[14] == 0x83 && MASTER_PROLOGUE[15] == 0xEC &&
               MASTER_PROLOGUE[16] == 0x28,
           "signature: it ends with `sub rsp,0x28`, not on its first three bytes");
        ok(master_prologue_ok(good) == 1, "signature: the recorded bytes pass");
        good[16] ^= 0x01;
        ok(master_prologue_ok(good) == 0, "signature: one changed byte refuses");
        good[16] ^= 0x01;
        good[0] = 0x41;
        ok(master_prologue_ok(good) == 0, "signature: a different first byte refuses");
        ok(master_prologue_ok(NULL) == 0, "signature: a null target refuses");
        ok(master_prologue_ok((const void *)1) == 0, "signature: an unmapped target refuses");
    }

    printf("\n%d checks, %d failed\n", CHECKS, FAILS);
    if (FAILS == 0)
    {
        printf("master: OK - %d checks\n", CHECKS);
        return 0;
    }
    printf("master: FAIL - %d of %d checks\n", FAILS, CHECKS);
    return 1;
}

int main(int argc, char **argv)
{
    if (argc >= 2 && strcmp(argv[1], "self") == 0)
    {
        return self_checks();
    }
    if (argc >= 5 && strcmp(argv[1], "level") == 0)
    {
        // level <count> <step> <xp>: the same formula, one record, one line per prestige
        int count = atoi(argv[2]);
        int step = atoi(argv[3]);
        unsigned long long xp = _strtoui64(argv[4], NULL, 10);
        static unsigned thr[64];
        fill_thr(thr, count < 64 ? count : 64, 1000u, 1200u);
        printf("%d %d %d\n", master_level(xp, count, thr, 0, step), master_level(xp, count, thr, 1, step),
               master_level(xp, count, thr, 2, step));
        return 0;
    }
    if (argc >= 3 && strcmp(argv[1], "step") == 0)
    {
        printf("%d\n", master_step_parse(argv[2], (int)strlen(argv[2])));
        return 0;
    }
    if (argc >= 2 && strcmp(argv[1], "sites") == 0)
    {
        // The five call-site RVAs and the prologue length the install carries. The patched bytes are built at run
        // time from the site and the thunk (`master_site_patch`), so there is no fixed patch image to print any
        // more - the build-16 prologue patch is gone (docs\B16-CRASH.md).
        printf("prologue %d\n", MASTER_PROLOGUE_LEN);
        for (int i = 0; i < MASTER_SITE_COUNT; i++)
        {
            printf("site %d 0x%X\n", i, MASTER_SITE_RVA[i]);
        }
        printf("len %d\n", MASTER_SITE_LEN);
        return 0;
    }
    if (argc >= 7 && strcmp(argv[1], "sweep") == 0)
    {
        // sweep <count> <step> <xp-start> <xp-end> <xp-stride>: one line per XP, all three prestige answers
        // ("<xp> <p0> <p1> <p2>"), so tools\test_master.py can compare a whole curve at once instead of
        // launching a process per point.
        int count = atoi(argv[2]);
        int step = atoi(argv[3]);
        unsigned long long a = _strtoui64(argv[4], NULL, 10);
        unsigned long long b = _strtoui64(argv[5], NULL, 10);
        unsigned long long stride = _strtoui64(argv[6], NULL, 10);
        static unsigned thr[64];
        fill_thr(thr, count < 64 ? count : 64, 1000u, 1200u);
        if (stride < 1)
        {
            stride = 1;
        }
        for (unsigned long long xp = a; xp <= b; xp += stride)
        {
            printf("%llu %d %d %d\n", xp, master_level(xp, count, thr, 0, step),
                   master_level(xp, count, thr, 1, step), master_level(xp, count, thr, 2, step));
        }
        return 0;
    }
    printf("usage: master_test.exe self | level <count> <step> <xp> | step <text> | sites | "
           "sweep <count> <step> <xp-start> <xp-end> <xp-stride>\n");
    return 2;
}
