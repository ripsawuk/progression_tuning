// clienthook - master prestige: the formula (pure) and the CALL-SITE hook (this file's one code
// patch). See master.h for the addresses, and for why the hook sits on the call sites rather than the callee.
// The formula half reads no client address, so the offline driver proves it directly; the hook half is only ever
// reached from the client's own five `call 180096680` sites.

#include <windows.h>
#include <tlhelp32.h>
#include <intrin.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "master.h"
#include "resolve.h"

void ch_logf(const char *fmt, ...); // proxy_main.c: bounded _vsnprintf_s into 512 bytes, truncated never overflowed

// The level function's address in the image being hooked. It starts at the measured rva, which is what the
// offline drivers' staged pages carry; master_install replaces it with the resolver's answer for the client it is
// handed, and every other address below is derived from it.
static unsigned MASTER_FN_RVA = MASTER_RVA;

// The 17 bytes at client+0x96680:
//   4053 push rbx / 55 push rbp / 56 push rsi / 57 push rdi / 4154 push r12 / 4155 push r13 /
//   4156 push r14 / 4157 push r15 / 4883ec28 sub rsp,0x28        -> the next instruction starts at 0x96691.
// This is the install's signature guard: the function must be the one described above, and the guard's length
// must equal the length the client's own RUNTIME_FUNCTION declares (prolog_size 0x11).
// None of these bytes is ever written: the hook is on the five call sites, not on the function.
const unsigned char MASTER_PROLOGUE[MASTER_PROLOGUE_LEN] = {
    0x40, 0x53, 0x55, 0x56, 0x57, 0x41, 0x54, 0x41, 0x55, 0x41, 0x56, 0x41, 0x57, 0x48, 0x83, 0xEC, 0x28};

// The five `E8 rel32` call sites, in .text order, from a scan of the client's own .text:
//   0x93DFF e87c280000 / 0x96212 e869040000 / 0x9723D e83ef4ffff / 0x97626 e855f0ffff / 0x976AC e8cfefffff
// `master_scan_sites` re-derives them from the client's own .text at run time and refuses unless the result is
// exactly this list - a client update that adds or drops a call site fails closed instead of half-hooking.
const unsigned MASTER_SITE_RVA[MASTER_SITE_COUNT] = {0x93DFF, 0x96212, 0x9723D, 0x97626, 0x976AC};

// --- the formula ------------------------------------------------------------------------------------
//
// The client's own order, reproduced: walk the thresholds while the XP is not below them, so the answer is the
// number of thresholds passed; a record with no thresholds answers 1 iff its XP is non-zero.

unsigned master_client_level(unsigned long long xp, int count, const unsigned *thr)
{
    if (count < 0)
    {
        count = 0;
    }
    if (count > MASTER_THRESHOLDS_MAX)
    {
        count = MASTER_THRESHOLDS_MAX;
    }
    if (count == 0)
    {
        return (xp != 0) ? 1u : 0u;
    }
    int i = 0;
    while (i < count)
    {
        if (xp < (unsigned long long)thr[i])
        {
            break;
        }
        i++;
    }
    return (unsigned)i;
}

int master_level(unsigned long long xp, int count, const unsigned *thr, int prestige, int step)
{
    if (prestige < MASTER_PRESTIGE_MIN)
    {
        return -1; // prestige 0/1 is the client's own behaviour, byte for byte: no write at all
    }
    if (step < MASTER_STEP_MIN || count < 0 || count > MASTER_THRESHOLDS_MAX || thr == NULL)
    {
        return -1;
    }
    if (count == 0)
    {
        // no thresholds means no band to extend: the client's own answer stands
        return (int)master_client_level(xp, 0, thr);
    }
    {
        unsigned long long last = (unsigned long long)thr[count - 1];
        if (xp <= last)
        {
            return (int)master_client_level(xp, count, thr); // at the last threshold this IS count
        }
        unsigned long long lvl = (unsigned long long)count + (xp - last) / (unsigned long long)step;
        if (lvl > (unsigned long long)MASTER_LEVEL_CAP)
        {
            lvl = (unsigned long long)MASTER_LEVEL_CAP;
        }
        return (int)lvl;
    }
}

// %TEMP%\progression-tuning\master_step.txt: "1800", "1800\n", " 5000 ". Out of range or not a number = default.
int master_step_parse(const char *text, int len)
{
    if (text == NULL || len <= 0)
    {
        return MASTER_STEP_DEFAULT;
    }
    int i = 0;
    while (i < len && (text[i] == ' ' || text[i] == '\t' || text[i] == '\r' || text[i] == '\n'))
    {
        i++;
    }
    if (i >= len || text[i] < '0' || text[i] > '9')
    {
        return MASTER_STEP_DEFAULT;
    }
    long long v = 0;
    while (i < len && text[i] >= '0' && text[i] <= '9')
    {
        v = v * 10 + (text[i] - '0');
        if (v > (long long)MASTER_STEP_MAX)
        {
            return MASTER_STEP_DEFAULT;
        }
        i++;
    }
    if (v < MASTER_STEP_MIN)
    {
        return MASTER_STEP_DEFAULT;
    }
    return (int)v;
}

// --- the settings -----------------------------------------------------------------------------------

static int master_step_read(void)
{
    wchar_t dir[MAX_PATH];
    wchar_t path[MAX_PATH];
    DWORD n = GetTempPathW(MAX_PATH, dir);
    if (n == 0 || n >= MAX_PATH)
    {
        return MASTER_STEP_DEFAULT;
    }
    if (_snwprintf_s(path, MAX_PATH, _TRUNCATE, L"%sprogression-tuning\\master_step.txt", dir) < 0)
    {
        return MASTER_STEP_DEFAULT;
    }
    HANDLE f = CreateFileW(path, GENERIC_READ, FILE_SHARE_READ | FILE_SHARE_WRITE | FILE_SHARE_DELETE, NULL,
                           OPEN_EXISTING, FILE_ATTRIBUTE_NORMAL, NULL);
    if (f == INVALID_HANDLE_VALUE)
    {
        return MASTER_STEP_DEFAULT;
    }
    char buf[64];
    DWORD got = 0;
    BOOL ok = ReadFile(f, buf, (DWORD)(sizeof(buf) - 1), &got, NULL);
    CloseHandle(f);
    if (!ok || got == 0)
    {
        return MASTER_STEP_DEFAULT;
    }
    return master_step_parse(buf, (int)got);
}

// The kill switch: a file, not a setting. Present = the hook does not install this session and says so; absent =
// normal. Leaving the hook off costs a relaunch, never a rebuild.
int master_off_present(const wchar_t *tempdir)
{
    wchar_t path[MAX_PATH];
    wchar_t dir[MAX_PATH];
    if (tempdir == NULL)
    {
        DWORD n = GetTempPathW(MAX_PATH, dir);
        if (n == 0 || n >= MAX_PATH)
        {
            return 0;
        }
        tempdir = dir;
    }
    if (_snwprintf_s(path, MAX_PATH, _TRUNCATE, L"%sprogression-tuning\\master_off.txt", tempdir) < 0)
    {
        return 0;
    }
    DWORD a = GetFileAttributesW(path);
    if (a == INVALID_FILE_ATTRIBUTES || a == 0xFFFFFFFFu)
    {
        return 0;
    }
    return 1;
}

// --- the hook ---------------------------------------------------------------------------------------
//
// Shape: the client's function is never modified, so its RUNTIME_FUNCTION
// (`prolog_size 0x11`, ALLOC_SMALL 0x28, 8 PUSH_NONVOL) stays TRUE. Each of its five `call` sites is repointed
// at `master_thunk`, a normal compiled function with its own .pdata, which calls the untouched original and then
// runs the fixup below. Every frame on the stack therefore matches a record the OS can read.

typedef unsigned long long (*master_fn)(void);

static int MASTER_PAGE_OK(const void *p)
{
    if (p == NULL)
    {
        return 0;
    }
    MEMORY_BASIC_INFORMATION mbi;
    if (VirtualQuery(p, &mbi, sizeof(mbi)) == 0)
    {
        return 0;
    }
    if (mbi.State != MEM_COMMIT || (mbi.Protect & (PAGE_GUARD | PAGE_NOACCESS)) != 0)
    {
        return 0;
    }
    return 1;
}

int master_prologue_ok(const void *p)
{
    if (!MASTER_PAGE_OK(p))
    {
        return 0;
    }
    return memcmp(p, MASTER_PROLOGUE, MASTER_PROLOGUE_LEN) == 0;
}

// rel32 reach, with margin: an `E8 rel32` reaches -2 GB..+2 GB from the *end* of the instruction. Keep 1 MB of
// headroom so an off-by-a-page in the trampoline search can never produce a wrap-around jump.
#define MASTER_REACH_MAX 0x7FF00000LL

static int master_reach(const void *site, const void *target)
{
    long long d = (long long)((const unsigned char *)target - ((const unsigned char *)site + MASTER_SITE_LEN));
    return (d >= -MASTER_REACH_MAX && d <= MASTER_REACH_MAX) ? 1 : 0;
}

int master_site_ok(const unsigned char *site, const unsigned char *client)
{
    if (site == NULL || client == NULL || !MASTER_PAGE_OK(site))
    {
        return 0;
    }
    if (site[0] != 0xE8)
    {
        return 0;
    }
    int rel = 0;
    memcpy(&rel, site + 1, 4);
    return ((const unsigned char *)site + MASTER_SITE_LEN + rel == client + MASTER_FN_RVA) ? 1 : 0;
}

int master_site_patch(unsigned char out[MASTER_SITE_LEN], const unsigned char *site, const void *target)
{
    if (out == NULL || site == NULL || target == NULL || !master_reach(site, target))
    {
        return 0;
    }
    long long d = (long long)((const unsigned char *)target - ((const unsigned char *)site + MASTER_SITE_LEN));
    int rel = (int)d;
    out[0] = 0xE8;
    memcpy(out + 1, &rel, 4);
    return 1;
}

int master_site_is_patch(const unsigned char *site, const void *target)
{
    unsigned char want[MASTER_SITE_LEN];
    if (site == NULL || !MASTER_PAGE_OK(site) || !master_site_patch(want, site, target))
    {
        return 0;
    }
    return memcmp(site, want, MASTER_SITE_LEN) == 0 ? 1 : 0;
}

// The trampoline for the case our DLL is more than 2 GB from the client image: `mov rax, <thunk>; jmp rax`.
// A pure leaf jump - it pushes nothing, keeps no frame, and touches only rax (volatile at every call) - so it
// needs no unwind info: a walk never sees a PC inside it. 12 bytes, one per site.
#define MASTER_TRAMP_LEN 12
static int master_tramp_bytes(unsigned char out[MASTER_TRAMP_LEN], ULONG_PTR target)
{
    out[0] = 0x48;
    out[1] = 0xB8;
    memcpy(out + 2, &target, 8);
    out[10] = 0xFF;
    out[11] = 0xE0;
    return MASTER_TRAMP_LEN;
}

static volatile LONG MASTER_STATE = 0;   // 0 untried, 1 on, 2 refused, 3 off by the kill switch
static master_fn MASTER_LEVEL_FN = NULL; // client+0x96680 - read, never written
static unsigned char *MASTER_CLIENT = NULL;
static int MASTER_STEP = MASTER_STEP_DEFAULT;
static int MASTER_FROZEN_LOG = 0;        // how many threads the patch window froze (for the install line)
static void *MASTER_GATE = NULL;         // the mutex shared with nativepay.c's installer

void master_set_install_gate(void *mutex)
{
    MASTER_GATE = mutex;
}

// One entry per record index (modulo 256), so a master record whose level the client rewrites to its own answer
// on every pass is restored silently instead of logging at the client's call rate.
#define MASTER_LOG_SLOTS 256
static struct
{
    int idx;
    int lvl;
} MASTER_SAID[MASTER_LOG_SLOTS];

// After the client's own pass: recompute the master band and put the level byte back, per record.
static void master_fixup(void)
{
    unsigned char *client = MASTER_CLIENT;
    if (client == NULL)
    {
        return;
    }
    unsigned char *recs = *(unsigned char **)(client + MASTER_RECS_RVA);
    int n = *(int *)(client + MASTER_COUNT_RVA);
    if (recs == NULL || n < 1 || n > 0x10000 || !MASTER_PAGE_OK(recs) ||
        !MASTER_PAGE_OK(recs + (size_t)(n - 1) * MASTER_STRIDE + MASTER_REC_LEVEL))
    {
        return; // the array is not there (or is being reallocated): nothing to do, next pass will be fine
    }
    int step = MASTER_STEP;
    for (int i = 0; i < n; i++)
    {
        // The array can be reallocated while we walk it, which is why the client's own pass re-reads the base
        // pointer mid-loop. Re-read both globals every record and stop on any change: a stale base would be
        // freed memory, and the next pass (within 500 ms) picks the new one up.
        if (*(unsigned char **)(client + MASTER_RECS_RVA) != recs ||
            *(int *)(client + MASTER_COUNT_RVA) != n)
        {
            return;
        }
        unsigned char *r = recs + (size_t)i * MASTER_STRIDE;
        if (*(int *)(r + MASTER_REC_KIND) != MASTER_KIND_WEAPON)
        {
            continue;
        }
        int prestige = (int)r[MASTER_REC_PRESTIGE];
        int count = *(int *)(r + MASTER_REC_COUNT);
        int want = master_level(*(unsigned long long *)(r + MASTER_REC_XP), count,
                                (const unsigned *)(r + MASTER_REC_THR), prestige, step);
        if (want < 0 || want > 255)
        {
            continue;
        }
        int have = (int)r[MASTER_REC_LEVEL];
        if (have != want)
        {
            r[MASTER_REC_LEVEL] = (unsigned char)want;
            int slot = (unsigned)i & (MASTER_LOG_SLOTS - 1);
            if (MASTER_SAID[slot].idx != i || MASTER_SAID[slot].lvl != want)
            {
                MASTER_SAID[slot].idx = i;
                MASTER_SAID[slot].lvl = want;
                // %s is the client's own row name (rec+0xc); the XP is printed in 32 bits because the band
                // peaks under 700,000 and every log reader here expects the 32-bit field.
                ch_logf("master: %s prestige %d level %d -> %d (xp %u, step %d)", r + MASTER_REC_NAME,
                        prestige, have, want, (unsigned)*(unsigned long long *)(r + MASTER_REC_XP), step);
            }
        }
    }
}

// The thunk: a normal compiled function with its own RUNTIME_FUNCTION, so a stack walk through it is correct.
// It calls the client's untouched function and keeps its answer in rax across the fixup: a detour that let
// master_fixup's own scratch land in rax would change what the function returns, and none of the five callers
// reads rax after the call, but a hook should not change it anyway.
static unsigned long long master_thunk(void)
{
    master_fn fn = MASTER_LEVEL_FN;
    if (fn == NULL)
    {
        return 0;
    }
    unsigned long long rv = fn(); // the client's own prologue and frame, exactly as shipped
    master_fixup();
    return rv;
}

// The offline test's seam: the thunk's own address, and a way to point it at a staged page
// instead of the client. Neither is called by the install path.
void *master_thunk_address(void)
{
    return (void *)master_thunk;
}

void master_bind_level_fn(void *fn)
{
    MASTER_LEVEL_FN = (master_fn)fn;
}

// --- finding the call sites -------------------------------------------------------------------------

// The five callers are the resolver's RS_MASTER_SITE0..4: it walks the client's executable sections for
// `E8 rel32` landing on the level function its own pattern found, and requires exactly five, or it resolves none
// of them (resolve.h). This file used to re-derive them here; the scan now lives in one place, so no two
// features can disagree about where the hook goes.
//
// MASTER_SITE_RVA above stays as the measured five: the resolver compares its answer against exactly those and
// logs `resolve: site0 differs from the known build` when one moves, and the offline driver prints them.

// --- writing the patch, with the other threads frozen -------------------------------------------------

#define MASTER_FREEZE_MAX 256
static HANDLE MASTER_THREADS[MASTER_FREEZE_MAX];
static int MASTER_THREADS_N = 0;

// Collect the process's other threads. Allocates (the snapshot does), so it runs before anything is suspended.
static int master_threads_collect(void)
{
    MASTER_THREADS_N = 0;
    HANDLE snap = CreateToolhelp32Snapshot(TH32CS_SNAPTHREAD, 0);
    if (snap == INVALID_HANDLE_VALUE)
    {
        return -1;
    }
    THREADENTRY32 te;
    te.dwSize = sizeof(te);
    DWORD self = GetCurrentThreadId();
    DWORD pid = GetCurrentProcessId();
    if (Thread32First(snap, &te))
    {
        do
        {
            if (te.th32OwnerProcessID != pid || te.th32ThreadID == self)
            {
                continue;
            }
            if (MASTER_THREADS_N >= MASTER_FREEZE_MAX)
            {
                break;
            }
            HANDLE h = OpenThread(THREAD_SUSPEND_RESUME, FALSE, te.th32ThreadID);
            if (h != NULL)
            {
                MASTER_THREADS[MASTER_THREADS_N++] = h;
            }
        } while (Thread32Next(snap, &te));
    }
    CloseHandle(snap);
    return MASTER_THREADS_N;
}

// A 5-byte store is not atomic, so a thread executing one of these sites could read a torn displacement. Freeze
// every other thread for the handful of stores - no allocation and no kernel call inside the window (the pages
// are already writable, and the instruction cache is flushed after the thaw) - then thaw. `frozen[i]` records
// which suspends took, so the thaw matches the freeze exactly.
static int master_freeze(int *frozen, int cap)
{
    int n = 0;
    for (int i = 0; i < MASTER_THREADS_N; i++)
    {
        frozen[i] = 0;
        if (i < cap && SuspendThread(MASTER_THREADS[i]) != (DWORD)-1)
        {
            frozen[i] = 1;
            n++;
        }
    }
    return n;
}

static void master_thaw(const int *frozen)
{
    for (int i = 0; i < MASTER_THREADS_N; i++)
    {
        if (frozen[i])
        {
            ResumeThread(MASTER_THREADS[i]);
        }
        CloseHandle(MASTER_THREADS[i]);
    }
    MASTER_THREADS_N = 0;
}

// All-or-nothing: every site's patch is built and its bytes verified before the first write; a failure after
// that restores the sites already written from `orig`. Returns 1 on success, and logs the refusal otherwise.
//
// The whole window runs under MASTER_GATE, the mutex nativepay.c's installer takes too, so the two
// installers' thread-freeze windows can never overlap (see that file's header).
static int master_write_sites(unsigned char **sites, const void *const *targets,
                              const unsigned char orig[MASTER_SITE_COUNT][MASTER_SITE_LEN])
{
    unsigned char patch[MASTER_SITE_COUNT][MASTER_SITE_LEN];
    DWORD old[MASTER_SITE_COUNT];
    int frozen[MASTER_FREEZE_MAX];
    int protected_n = 0;
    int wrote_n = 0;

    for (int i = 0; i < MASTER_SITE_COUNT; i++)
    {
        if (!master_site_patch(patch[i], sites[i], targets[i]))
        {
            ch_logf("master: refused - the hook target is not within rel32 range of the call site at 0x%08lX",
                    (unsigned long)((ULONG_PTR)sites[i] & 0xFFFFFFFFu));
            return 0;
        }
    }

    void *gate = MASTER_GATE;
    if (gate != NULL)
    {
        WaitForSingleObject((HANDLE)gate, 5000);
    }

    // The pages first, so the frozen window below does no kernel work: a suspended thread holding the address
    // space lock would otherwise deadlock every VirtualProtect that came after it.
    for (int i = 0; i < MASTER_SITE_COUNT; i++)
    {
        if (!VirtualProtect(sites[i], MASTER_SITE_LEN, PAGE_EXECUTE_READWRITE, &old[i]))
        {
            ch_logf("master: refused - the call site at 0x%08lX is not writable (0x%lX)",
                    (unsigned long)((ULONG_PTR)sites[i] & 0xFFFFFFFFu), (unsigned long)GetLastError());
            for (int j = 0; j < protected_n; j++)
            {
                DWORD back = 0;
                VirtualProtect(sites[j], MASTER_SITE_LEN, old[j], &back);
            }
            if (gate != NULL)
            {
                ReleaseMutex((HANDLE)gate);
            }
            return 0;
        }
        protected_n++;
    }

    int threads = master_threads_collect();
    int frozen_n = 0;
    if (threads > 0)
    {
        frozen_n = master_freeze(frozen, MASTER_FREEZE_MAX);
    }

    for (int i = 0; i < MASTER_SITE_COUNT; i++)
    {
        memcpy(sites[i], patch[i], MASTER_SITE_LEN);
        wrote_n++;
    }

    if (threads > 0)
    {
        master_thaw(frozen);
    }
    for (int i = 0; i < MASTER_SITE_COUNT; i++)
    {
        FlushInstructionCache(GetCurrentProcess(), sites[i], MASTER_SITE_LEN);
    }

    // Read back: every site must now be exactly the patch, or the whole thing is undone.
    int bad = -1;
    for (int i = 0; i < MASTER_SITE_COUNT; i++)
    {
        if (!master_site_is_patch(sites[i], targets[i]))
        {
            bad = i;
            break;
        }
    }
    if (bad >= 0)
    {
        for (int i = 0; i < wrote_n; i++)
        {
            memcpy(sites[i], orig[i], MASTER_SITE_LEN);
            FlushInstructionCache(GetCurrentProcess(), sites[i], MASTER_SITE_LEN);
        }
        for (int j = 0; j < protected_n; j++)
        {
            DWORD back = 0;
            VirtualProtect(sites[j], MASTER_SITE_LEN, old[j], &back);
        }
        ch_logf("master: refused - the call site at 0x%08lX did not read back - all five restored",
                (unsigned long)((ULONG_PTR)sites[bad] & 0xFFFFFFFFu));
        if (gate != NULL)
        {
            ReleaseMutex((HANDLE)gate);
        }
        return 0;
    }

    for (int j = 0; j < protected_n; j++)
    {
        DWORD back = 0;
        VirtualProtect(sites[j], MASTER_SITE_LEN, old[j], &back);
    }
    if (gate != NULL)
    {
        ReleaseMutex((HANDLE)gate);
    }
    MASTER_FROZEN_LOG = frozen_n; // read by the caller's success line
    return 1;
}

// A trampoline within rel32 reach of all five sites, or NULL. Allocated near the client image: the sites are
// inside it, so a page within a few hundred MB of its base reaches all five.
static unsigned char *master_tramp_alloc(unsigned char *client, unsigned char **sites, const void *thunk)
{
    ULONG_PTR base = (ULONG_PTR)client;
    const ULONG_PTR step = 0x10000;
    for (ULONG_PTR k = 1; k < 0x4000; k++)
    {
        for (int side = 0; side < 2; side++)
        {
            ULONG_PTR want = side == 0 ? base + k * step : base - k * step;
            unsigned char *p = (unsigned char *)VirtualAlloc((void *)want, 0x1000, MEM_COMMIT | MEM_RESERVE,
                                                             PAGE_EXECUTE_READWRITE);
            if (p == NULL)
            {
                continue;
            }
            int ok = 1;
            for (int i = 0; i < MASTER_SITE_COUNT; i++)
            {
                if (!master_reach(sites[i], p + i * 16))
                {
                    ok = 0;
                    break;
                }
            }
            if (ok)
            {
                return p;
            }
            VirtualFree(p, 0, MEM_RELEASE);
        }
    }
    (void)thunk;
    return NULL;
}

int master_install(HMODULE client)
{
    LONG state = InterlockedCompareExchange(&MASTER_STATE, 0, 0);
    if (state == 1)
    {
        return 1;
    }
    if (state == 2)
    {
        return -1;
    }
    if (state == 3)
    {
        return 0;
    }
    if (client == NULL)
    {
        ch_logf("master: refused - the client module is not loaded");
        InterlockedExchange(&MASTER_STATE, 2);
        return -1;
    }

    // The kill switch, first: with this file present the session runs without the master track and the dvars
    // and the payment are untouched, which makes an A/B a relaunch rather than a rebuild.
    if (master_off_present(NULL))
    {
        ch_logf("master: disabled by file");
        InterlockedExchange(&MASTER_STATE, 3);
        return 0;
    }

    MASTER_CLIENT = (unsigned char *)client;
    MASTER_STEP = master_step_read();

    // EVERY ADDRESS THIS HOOK NEEDS, from the resolver: the level function from its own pattern, the five call
    // sites from the `E8 rel32` scan for that function. A symbol this build does not carry turns this feature
    // off alone, with one line naming it - the payment, the payload and the publish are not touched.
    const RS_TABLE *rs = rs_for(client);
    if (!rs_feature_ok(rs, RS_F_MASTER))
    {
        if (!rs_ok(rs, RS_MASTER_FN))
        {
            ch_logf("master: refused - master (the level function) is not resolved in this client - off");
        }
        else
        {
            int found = 0;
            for (int i = 0; i < MASTER_SITE_COUNT; i++)
            {
                if (rs_ok(rs, (RS_SYM)(RS_MASTER_SITE0 + i)))
                {
                    found++;
                }
            }
            ch_logf("master: refused - %d call sites to 0x%08lX, expected %d - off", found,
                    (unsigned long)rs_rva(rs, RS_MASTER_FN), MASTER_SITE_COUNT);
        }
        InterlockedExchange(&MASTER_STATE, 2);
        return -1;
    }

    MASTER_FN_RVA = rs_rva(rs, RS_MASTER_FN);
    unsigned char *fn = (unsigned char *)client + MASTER_FN_RVA;
    if (!master_prologue_ok(fn))
    {
        // The refusal line names the address and the first bytes, so a client update says exactly what moved.
        ch_logf("master: the level function at 0x%08lX does not match the pattern - off",
                (unsigned long)((ULONG_PTR)fn & 0xFFFFFFFFu));
        InterlockedExchange(&MASTER_STATE, 2);
        return -1;
    }

    // The five call sites the resolver found, each checked as the call it must be: `E8 rel32` landing on the
    // level function, in a committed readable page. A site that is not, is a refusal - never a half-hook.
    unsigned char *sites[MASTER_SITE_COUNT];
    for (int i = 0; i < MASTER_SITE_COUNT; i++)
    {
        unsigned rva = rs_rva(rs, (RS_SYM)(RS_MASTER_SITE0 + i));
        sites[i] = (unsigned char *)client + rva;
        if (!master_site_ok(sites[i], (unsigned char *)client))
        {
            ch_logf("master: refused - the call site at 0x%08lX is not E8+rel32 to 0x%08lX - off",
                    (unsigned long)rva, (unsigned long)MASTER_FN_RVA);
            InterlockedExchange(&MASTER_STATE, 2);
            return -1;
        }
    }

    MASTER_LEVEL_FN = (master_fn)(void *)fn;

    // Straight to the thunk when it is in reach; otherwise through a per-site trampoline near the client image.
    void *target = (void *)master_thunk;
    unsigned char *tramp = NULL;
    int need_tramp = 0;
    for (int i = 0; i < MASTER_SITE_COUNT; i++)
    {
        if (!master_reach(sites[i], target))
        {
            need_tramp = 1;
        }
    }
    if (need_tramp)
    {
        tramp = master_tramp_alloc((unsigned char *)client, sites, target);
        if (tramp == NULL)
        {
            ch_logf("master: refused - the thunk at 0x%08lX is out of range and no trampoline could be allocated",
                    (unsigned long)((ULONG_PTR)target & 0xFFFFFFFFu));
            InterlockedExchange(&MASTER_STATE, 2);
            return -1;
        }
        for (int i = 0; i < MASTER_SITE_COUNT; i++)
        {
            unsigned char stub[MASTER_TRAMP_LEN];
            master_tramp_bytes(stub, (ULONG_PTR)target);
            memcpy(tramp + i * 16, stub, MASTER_TRAMP_LEN);
        }
        FlushInstructionCache(GetCurrentProcess(), tramp, MASTER_SITE_COUNT * 16);
    }

    void *site_target[MASTER_SITE_COUNT];
    for (int i = 0; i < MASTER_SITE_COUNT; i++)
    {
        site_target[i] = need_tramp ? (void *)(tramp + i * 16) : target;
    }

    unsigned char orig[MASTER_SITE_COUNT][MASTER_SITE_LEN];
    for (int i = 0; i < MASTER_SITE_COUNT; i++)
    {
        memcpy(orig[i], sites[i], MASTER_SITE_LEN);
    }

    // The client's function must still be byte-identical after the write - the test suite's invariant: a hook
    // may not change a function's prologue without repairing its unwind data, so this one does not change it at
    // all.
    unsigned char before[MASTER_PROLOGUE_LEN];
    memcpy(before, fn, MASTER_PROLOGUE_LEN);

    if (!master_write_sites(sites, (const void *const *)site_target, (const unsigned char(*)[MASTER_SITE_LEN])orig))
    {
        if (tramp != NULL)
        {
            VirtualFree(tramp, 0, MEM_RELEASE);
        }
        InterlockedExchange(&MASTER_STATE, 2);
        return -1;
    }
    if (memcmp(before, fn, MASTER_PROLOGUE_LEN) != 0)
    {
        // Only reachable if something outside this install wrote the function: undo our five patches, then refuse.
        DWORD old = 0;
        for (int i = 0; i < MASTER_SITE_COUNT; i++)
        {
            if (VirtualProtect(sites[i], MASTER_SITE_LEN, PAGE_EXECUTE_READWRITE, &old))
            {
                memcpy(sites[i], orig[i], MASTER_SITE_LEN);
                DWORD back = 0;
                VirtualProtect(sites[i], MASTER_SITE_LEN, old, &back);
            }
            FlushInstructionCache(GetCurrentProcess(), sites[i], MASTER_SITE_LEN);
        }
        if (tramp != NULL)
        {
            VirtualFree(tramp, 0, MEM_RELEASE);
        }
        ch_logf("master: refused - the level function's own bytes changed - off, all five sites restored");
        InterlockedExchange(&MASTER_STATE, 2);
        return -1;
    }

    InterlockedExchange(&MASTER_STATE, 1);
    ch_logf("master: %d call sites hooked (0x%08lX 0x%08lX 0x%08lX 0x%08lX 0x%08lX), the function at "
            "0x%08lX is untouched, thunk 0x%08lX, %d threads frozen - master prestige on at prestige >= %d "
            "(level = count + (xp - last)/%d, cap %d)",
            MASTER_SITE_COUNT, (unsigned long)rs_rva(rs, RS_MASTER_SITE0),
            (unsigned long)rs_rva(rs, RS_MASTER_SITE1), (unsigned long)rs_rva(rs, RS_MASTER_SITE2),
            (unsigned long)rs_rva(rs, RS_MASTER_SITE3), (unsigned long)rs_rva(rs, RS_MASTER_SITE4),
            (unsigned long)MASTER_FN_RVA, (unsigned long)((ULONG_PTR)target & 0xFFFFFFFFu), MASTER_FROZEN_LOG,
            MASTER_PRESTIGE_MIN, MASTER_STEP, MASTER_LEVEL_CAP);
    return 1;
}
