// clienthook - the forced publish, the pure half: the guard, the window, the two triggers and the record
// fingerprint. Nothing here reads a client address; publish.h carries the why.

#include <stdio.h>
#include <string.h>
#include <wchar.h>

#include "publish.h"

// The prologue of the client's serialise-and-publish in the pinned build. Read from its own bytes; a mismatch
// refuses the feature instead of calling into an unknown address.
const unsigned char PUB_SIG[PUB_SIG_LEN] = {
    0x48, 0x89, 0x5C, 0x24, 0x18, 0x55, 0x56, 0x57, 0x41, 0x54, 0x41, 0x55,
    0x41, 0x56, 0x41, 0x57, 0x48, 0x83, 0xEC, 0x30, 0x48, 0x63, 0x05, 0xBD};

void pub_init(PUB_GATE *g)
{
    if (g == NULL)
    {
        return;
    }
    memset(g, 0, sizeof(*g));
}

void pub_want(PUB_GATE *g)
{
    if (g == NULL)
    {
        return;
    }
    InterlockedExchange(&g->want, 1);
}

void pub_match_live(PUB_GATE *g)
{
    if (g == NULL)
    {
        return;
    }
    InterlockedExchange(&g->live, 1);
}

int pub_off_present(const wchar_t *tempdir)
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
    if (_snwprintf_s(path, MAX_PATH, _TRUNCATE, L"%sprogression-tuning\\publish_off.txt", tempdir) < 0)
    {
        return 0;
    }
    DWORD a = GetFileAttributesW(path);
    return (a != INVALID_FILE_ATTRIBUTES && a != 0xFFFFFFFFu) ? 1 : 0;
}

// 1 when the 24 bytes at `at` are in memory this process may read. THE READ THAT WOULD FAULT is the memcmp
// below, and it is the only one in this DLL that is not already behind a VirtualQuery or an image-size check:
// on a client build smaller than the address this feature was measured at, reading it is an access violation in
// our own thread - the one failure that would take the game with it. This is master.c's MASTER_PAGE_OK
// discipline, applied to the target, and it is the first thing the guard does.
static int pub_readable(const unsigned char *at)
{
    if (at == NULL)
    {
        return 0;
    }
    const DWORD readable = PAGE_READONLY | PAGE_READWRITE | PAGE_WRITECOPY | PAGE_EXECUTE_READ |
                           PAGE_EXECUTE_READWRITE | PAGE_EXECUTE_WRITECOPY;
    // both ends, because 24 bytes can straddle a page boundary
    const unsigned char *ends[2] = {at, at + PUB_SIG_LEN - 1};
    for (int i = 0; i < 2; i++)
    {
        MEMORY_BASIC_INFORMATION mbi;
        if (VirtualQuery(ends[i], &mbi, sizeof(mbi)) == 0)
        {
            return 0;
        }
        if (mbi.State != MEM_COMMIT || (mbi.Protect & (PAGE_GUARD | PAGE_NOACCESS)) != 0 ||
            (mbi.Protect & readable) == 0)
        {
            return 0;
        }
    }
    return 1;
}

int pub_sig_ok(const unsigned char *at)
{
    if (!pub_readable(at))
    {
        return 0;
    }
    return memcmp(at, PUB_SIG, PUB_SIG_LEN) == 0 ? 1 : 0;
}

PUB_VERDICT pub_step(PUB_GATE *g, unsigned long long now_ms, const unsigned char *at)
{
    if (g == NULL)
    {
        return PUB_IDLE;
    }
    if (g->off)
    {
        // a latched-off feature never calls again and never leaves a want behind
        InterlockedExchange(&g->want, 0);
        return PUB_IDLE;
    }
    if (InterlockedCompareExchange(&g->want, 0, 0) == 0)
    {
        return PUB_IDLE;
    }
    // the window: measured from the START of the last call, so two calls can never be closer than PUB_MIN_MS
    if (g->last_ms != 0 && (now_ms < g->last_ms || now_ms - g->last_ms < (unsigned long long)PUB_MIN_MS))
    {
        InterlockedIncrement(&g->skip);
        return PUB_COALESCED; // the want stays SET: deferred, never dropped
    }
    InterlockedExchange(&g->want, 0);
    if (!pub_sig_ok(at))
    {
        InterlockedExchange(&g->off, 1);
        return PUB_REFUSED;
    }
    g->last_ms = now_ms;
    InterlockedIncrement(&g->done);
    return PUB_CALL;
}

int pub_scan_due(PUB_GATE *g, unsigned long long now_ms)
{
    if (g == NULL)
    {
        return 0;
    }
    if (g->scan_ms != 0 && (now_ms < g->scan_ms || now_ms - g->scan_ms < (unsigned long long)PUB_MIN_MS))
    {
        return 0;
    }
    g->scan_ms = now_ms;
    return 1;
}

static unsigned long long pub_fnv(unsigned long long h, const unsigned char *p, size_t n)
{
    for (size_t i = 0; i < n; i++)
    {
        h ^= (unsigned long long)p[i];
        h *= 1099511628211ULL;
    }
    return h;
}

unsigned long long pub_fingerprint(const unsigned char *records, int count)
{
    if (records == NULL || count <= 0)
    {
        return 0;
    }
    unsigned long long h = 14695981039346656037ULL;
    for (int i = 0; i < count; i++)
    {
        const unsigned char *r = records + (size_t)i * MASTER_STRIDE;
        h = pub_fnv(h, r + MASTER_REC_XP, 8);                  // progress / XP
        h = pub_fnv(h, r + MASTER_REC_LEVEL - 1, 2);           // the status byte, then the level byte
        h = pub_fnv(h, r + MASTER_REC_PRESTIGE, 1);            // the prestige byte
    }
    return h;
}

int pub_note_fingerprint(PUB_GATE *g, unsigned long long fp)
{
    if (g == NULL)
    {
        return 0;
    }
    if (!g->have_fp)
    {
        // the baseline is not a change: a snapshot taken at boot is not a row that moved
        g->fp = fp;
        g->have_fp = 1;
        return 0;
    }
    if (fp == g->fp)
    {
        return 0;
    }
    g->fp = fp;
    if (!g->live)
    {
        // nothing on screen is reading a live record outside a match, so a move is re-baselined, not published
        return 0;
    }
    pub_want(g);
    return 1;
}
