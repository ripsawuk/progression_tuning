// clienthook - the resolver. See resolve.h for what it answers and why; this file is the machine.
//
// One scan of an image: the ten byte patterns below, each over the client's executable sections only, then the
// nine addresses derived from what those patterns found. Nothing is read outside SizeOfImage, every derived
// address is checked against it, and a pattern that matches twice resolves nothing at all.

#include <windows.h>
#include <stdio.h>
#include <string.h>

#include "resolve.h"

void ch_logf(const char *fmt, ...); // proxy_main.c in the DLL; the offline drivers' own stub

// --- the patterns, exactly as measured (docs\RC1-VERSION-COUPLING.md 2) ----------------------------------
//
// `??` is one wildcard byte: a displacement or a literal the shape does not pin. Every pattern carries a
// distinctive operand or immediate rather than a function prologue - the master function's 17-byte prologue
// alone has 21 matches in this .text, and a scanner keyed on it would be wrong 20 times out of 21.

#define RS_PAT_MAX 56
#define RS_PAT_COUNT 10

enum
{
    P_AWARD = 0,
    P_SITE,
    P_LOADS,
    P_PUB,
    P_MASTER,
    P_RECS,
    P_SERIAL,
    P_BITMAP,
    P_RFN,
    P_SALT
};

static const char *const RS_PAT_TEXT[RS_PAT_COUNT] = {
    // the award function: eight pushes, `sub rsp,0x38`, `mov eax,[rcx]`, `lea rbp,[rip+...]`
    "40 53 55 56 57 41 54 41 55 41 56 41 57 48 83 EC 38 8B 01 48 8D 2D ?? ?? ?? ??",
    // the one call site it writes: `E8 rel32`, then the kill-switch test into a dependent branch
    "E8 ?? ?? ?? ?? 83 3D ?? ?? ?? ?? 00 0F 84 ?? ?? ?? ??",
    // the two addend loads: `mov eax,[rip+kill]` then `cmovne ecx,[rip+crit]`
    "8B 05 ?? ?? ?? ?? 0F 45 0D ?? ?? ?? ??",
    // the serialise-and-publish: its 20-byte prologue and the `movsxd rax,[rip+...]` that follows
    "48 89 5C 24 18 55 56 57 41 54 41 55 41 56 41 57 48 83 EC 30 48 63 05 ?? ?? ?? ??",
    // the tier/level derivation: its prologue, then `mov r14,[rip+...]` and its own loop constants
    "40 53 55 56 57 41 54 41 55 41 56 41 57 48 83 EC 28 4C 8B 35 ?? ?? ?? ?? 45 33 E4 41 BD 03 00 00 00",
    // the record walk: the count load, the cap test, and the `add rdi,[rip+...]` onto the array base
    "B4 01 44 8B 1D ?? ?? ?? ?? 45 32 FF 45 8B F5 BD 01 00 00 00 45 85 DB 0F 8E ?? ?? ?? ?? "
    "41 BA D1 00 00 00 49 63 C6 48 69 F8 78 05 00 00 48 03 3D ?? ?? ?? ??",
    // the publish serial: the client's own compare, load, increment and store of it
    "83 3D ?? ?? ?? ?? 00 0F 8C ?? ?? ?? ?? 44 8B 0D ?? ?? ?? ?? 41 FF C1 44 89 0D ?? ?? ?? ??",
    // the lock-bitmap slot: `mov rax,[rip+slot]`, then the next two RIP-relative operands
    "48 8B 05 ?? ?? ?? ?? 4C 8D 3D ?? ?? ?? ?? 48 8D 0D",
    // the client's own getter for the register-or-find pointer: `mov rax,[rip+slot]; ret`, 15 padding bytes
    "48 8B 05 ?? ?? ?? ?? C3 CC CC CC CC CC CC CC CC 40 53 48 81 EC 40 01 00 00",
    // the name hash: its first-char load, the call after it, the salt `lea`, the multiplier, the constant
    "48 8B F9 0F BE 09 E8 ?? ?? ?? ?? 0F B6 D8 48 8D 15 ?? ?? ?? ?? 48 B8 ?? ?? ?? ?? ?? ?? ?? ?? "
    "48 8D 0D ?? ?? ?? ?? 48 33 D8 48 BE 33 02 00 00 00 01 00 00",
};

static const char *const RS_PAT_NAME[RS_PAT_COUNT] = {
    "award", "site", "loads", "pub", "master", "recs", "serial", "bitmap", "rfn", "salt"};

// The measured value of every symbol: the comparison baseline, never an address this DLL reads through.
static const unsigned RS_KNOWN[RS_SYM_COUNT] = {
    0x93820u,                                                   // award
    0x930D3u,                                                   // site
    0x93E5Du,                                                   // load_a
    0x93E63u,                                                   // load_b
    0x2775F4u,                                                  // kill
    0x2775F8u,                                                  // crit
    0x962E0u,                                                   // pub
    0x96680u,                                                   // master
    0x93DFFu, 0x96212u, 0x9723Du, 0x97626u, 0x976ACu,           // the five call sites
    0x3DD288u,                                                  // recs
    0x3DD290u,                                                  // count
    0x3E6CBCu,                                                  // serial
    0x466CD8u,                                                  // bitmap
    0x6C4280u,                                                  // rfn
    0x16ED38u,                                                  // salt
    0x3E6840u,                                                  // chver
    0x27764Cu,                                                  // slot
};

static const char *const RS_NAME[RS_SYM_COUNT] = {
    "award", "site", "load_a", "load_b", "kill", "crit", "pub", "master",
    "site0", "site1", "site2", "site3", "site4",
    "recs", "count", "serial", "bitmap", "rfn", "salt", "chver", "slot",
};

typedef struct
{
    int len;
    unsigned char b[RS_PAT_MAX];
    unsigned char m[RS_PAT_MAX]; // 1 = this byte must match, 0 = wildcard
} RS_PAT;

static RS_PAT RS_PAT_TAB[RS_PAT_COUNT];
static volatile LONG RS_PAT_READY = 0;
static SRWLOCK RS_PAT_LOCK = SRWLOCK_INIT;

// The identification verdict, kept apart from any table because a scan zeroes the table it fills: the DLL asks
// for the verdict first (frame_identify) and only then for the addresses, and a scan must not lose it.
static volatile LONG RS_KNOWN_BUILD = 0;

// "40 53 ?? EC" -> b[]/m[]. Returns 0 on a malformed token.
static int rs_pat_parse(const char *text, RS_PAT *p)
{
    p->len = 0;
    const char *c = text;
    for (;;)
    {
        while (*c == ' ')
        {
            c++;
        }
        if (*c == '\0')
        {
            return 1;
        }
        if (p->len >= RS_PAT_MAX)
        {
            return 0;
        }
        if (c[0] == '?' && c[1] == '?')
        {
            p->m[p->len] = 0;
            p->b[p->len] = 0;
            c += 2;
        }
        else
        {
            int hi = -1;
            int lo = -1;
            for (int k = 0; k < 2; k++)
            {
                char ch = c[k];
                int v = -1;
                if (ch >= '0' && ch <= '9')
                {
                    v = ch - '0';
                }
                else if (ch >= 'A' && ch <= 'F')
                {
                    v = ch - 'A' + 10;
                }
                else if (ch >= 'a' && ch <= 'f')
                {
                    v = ch - 'a' + 10;
                }
                if (v < 0)
                {
                    return 0;
                }
                if (k == 0)
                {
                    hi = v;
                }
                else
                {
                    lo = v;
                }
            }
            p->m[p->len] = 1;
            p->b[p->len] = (unsigned char)((hi << 4) | lo);
            c += 2;
        }
        p->len++;
    }
}

static int rs_pat_init(void)
{
    if (InterlockedCompareExchange(&RS_PAT_READY, 0, 0) != 0)
    {
        return RS_PAT_READY == 1 ? 1 : 0;
    }
    AcquireSRWLockExclusive(&RS_PAT_LOCK);
    if (RS_PAT_READY == 0)
    {
        LONG ok = 1;
        for (int i = 0; i < RS_PAT_COUNT; i++)
        {
            if (!rs_pat_parse(RS_PAT_TEXT[i], &RS_PAT_TAB[i]))
            {
                ok = 0;
            }
        }
        InterlockedExchange(&RS_PAT_READY, ok);
    }
    ReleaseSRWLockExclusive(&RS_PAT_LOCK);
    return RS_PAT_READY == 1 ? 1 : 0;
}

// --- the scan ----------------------------------------------------------------------------------------------

// How many times `p` occurs in `s`, stopping at 2 (two is a refusal, and the third costs nothing to skip).
// `first` receives the offset of the first match.
static int rs_count(const RS_PAT *p, const unsigned char *s, unsigned size, unsigned *first)
{
    if (size < (unsigned)p->len || s == NULL)
    {
        return 0;
    }
    unsigned last = size - (unsigned)p->len;
    int n = 0;
    for (unsigned i = 0; i <= last; i++)
    {
        if (p->m[0] != 0 && s[i] != p->b[0])
        {
            continue;
        }
        int hit = 1;
        for (int k = 1; k < p->len; k++)
        {
            if (p->m[k] != 0 && s[i + (unsigned)k] != p->b[k])
            {
                hit = 0;
                break;
            }
        }
        if (hit)
        {
            if (n == 0 && first != NULL)
            {
                *first = i;
            }
            n++;
            if (n > 1)
            {
                return n;
            }
        }
    }
    return n;
}

// The image's sections, validated once: every executable section with a usable size, inside SizeOfImage.
#define RS_SEC_MAX 32
typedef struct
{
    const unsigned char *at;
    unsigned va;
    unsigned size;
} RS_SEC;

typedef struct
{
    const unsigned char *base;
    unsigned ofimage;
    RS_SEC exec[RS_SEC_MAX];
    int n_exec;
} RS_IMAGE;

static int rs_read_image(const unsigned char *image, RS_IMAGE *im)
{
    if (image == NULL)
    {
        return 0;
    }
    im->base = image;
    im->n_exec = 0;
    const IMAGE_DOS_HEADER *dos = (const IMAGE_DOS_HEADER *)image;
    if (dos->e_magic != IMAGE_DOS_SIGNATURE)
    {
        return 0;
    }
    unsigned lfanew = (unsigned)dos->e_lfanew;
    if (lfanew < 0x40 || lfanew > 0x1000)
    {
        return 0;
    }
    const IMAGE_NT_HEADERS64 *nt = (const IMAGE_NT_HEADERS64 *)(image + lfanew);
    if (nt->Signature != IMAGE_NT_SIGNATURE || nt->OptionalHeader.Magic != IMAGE_NT_OPTIONAL_HDR64_MAGIC)
    {
        return 0;
    }
    im->ofimage = nt->OptionalHeader.SizeOfImage;
    if (im->ofimage < 0x1000 || im->ofimage > 0x10000000u)
    {
        return 0;
    }
    const IMAGE_SECTION_HEADER *sec = IMAGE_FIRST_SECTION(nt);
    for (int i = 0; i < nt->FileHeader.NumberOfSections && i < RS_SEC_MAX; i++)
    {
        if ((sec[i].Characteristics & IMAGE_SCN_MEM_EXECUTE) == 0)
        {
            continue;
        }
        unsigned va = sec[i].VirtualAddress;
        unsigned size = sec[i].Misc.VirtualSize;
        if (size == 0)
        {
            continue;
        }
        if (va >= im->ofimage || size > im->ofimage - va)
        {
            continue; // a section that does not fit the image is not scanned: a pattern half outside is no match
        }
        im->exec[im->n_exec].at = image + va;
        im->exec[im->n_exec].va = va;
        im->exec[im->n_exec].size = size;
        im->n_exec++;
    }
    return im->n_exec > 0 ? 1 : 0;
}

// The RVA a pattern must land on, or 0 when it matched anything other than exactly once.
static unsigned rs_locate(const RS_IMAGE *im, const RS_PAT *p)
{
    unsigned hit = 0;
    unsigned rva = 0;
    int n = 0;
    for (int i = 0; i < im->n_exec; i++)
    {
        int c = rs_count(p, im->exec[i].at, im->exec[i].size, &hit);
        if (c == 0)
        {
            continue;
        }
        if (c > 1)
        {
            return 0;
        }
        n++;
        rva = im->exec[i].va + hit;
    }
    return n == 1 ? rva : 0;
}

// A RIP-relative operand: disp32 at `disp_off` in the pattern, the instruction ending at `end_off` (both counted
// from the pattern's first byte). The target must land inside the image.
static unsigned rs_rip(const RS_IMAGE *im, unsigned pat_rva, int disp_off, int end_off)
{
    int d = 0;
    for (int i = 0; i < im->n_exec; i++)
    {
        unsigned va = im->exec[i].va;
        if (pat_rva >= va && pat_rva + (unsigned)end_off <= va + im->exec[i].size)
        {
            memcpy(&d, im->exec[i].at + (pat_rva - va) + (unsigned)disp_off, 4);
            long long dst = (long long)pat_rva + (long long)end_off + (long long)d;
            if (dst <= 0 || dst >= (long long)im->ofimage)
            {
                return 0;
            }
            return (unsigned)dst;
        }
    }
    return 0;
}

// The `E8 rel32` callers of `target_rva`, in section order (which is ascending rva order). Returns the count and
// fills up to `cap`; a count above `cap` leaves out[] incomplete - the caller decides.
static int rs_callers(const RS_IMAGE *im, unsigned target_rva, unsigned *out, int cap)
{
    int n = 0;
    for (int i = 0; i < im->n_exec; i++)
    {
        const unsigned char *s = im->exec[i].at;
        unsigned size = im->exec[i].size;
        if (size < 5)
        {
            continue;
        }
        for (unsigned k = 0; k + 5 <= size; k++)
        {
            if (s[k] != 0xE8)
            {
                continue;
            }
            int rel = 0;
            memcpy(&rel, s + k + 1, 4);
            long long dst = (long long)im->exec[i].va + (long long)k + 5 + (long long)rel;
            if (dst == (long long)target_rva)
            {
                if (out != NULL && n < cap)
                {
                    out[n] = im->exec[i].va + k;
                }
                n++;
            }
        }
    }
    return n;
}

static void rs_derive(const RS_IMAGE *im, RS_TABLE *t)
{
    unsigned site[5];
    int n;

    // nativepay: the award, its call site, the two addends and the two ints they read.
    t->rva[RS_LOAD_B] = t->rva[RS_LOAD_A] ? t->rva[RS_LOAD_A] + 6u : 0;
    if (t->rva[RS_LOAD_A] != 0)
    {
        t->rva[RS_KILL] = rs_rip(im, t->rva[RS_LOAD_A], 2, 6);
        t->rva[RS_CRIT] = rs_rip(im, t->rva[RS_LOAD_A], 9, 13);
    }

    // master: the five call sites of the pattern-found level function. Exactly five, or none is used.
    if (t->rva[RS_MASTER_FN] != 0)
    {
        memset(site, 0, sizeof(site));
        n = rs_callers(im, t->rva[RS_MASTER_FN], site, 5);
        if (n == 5)
        {
            for (int i = 0; i < 5; i++)
            {
                t->rva[RS_MASTER_SITE0 + i] = site[i];
            }
        }
    }

    // the record array: the count its own walk loads, then the base its own walk adds.
    if (t->rva[RS_RECS] != 0)
    {
        unsigned pat = t->rva[RS_RECS];
        t->rva[RS_COUNT] = rs_rip(im, pat, 5, 9);
        t->rva[RS_RECS] = rs_rip(im, pat, 48, 52);
    }

    // the publish serial: the store at the end of the client's own compare/inc/store triple.
    if (t->rva[RS_SERIAL] != 0)
    {
        t->rva[RS_SERIAL] = rs_rip(im, t->rva[RS_SERIAL], 26, 30);
    }

    // the lock-bitmap slot, the register-or-find slot, the hash salt.
    if (t->rva[RS_BITMAP] != 0)
    {
        t->rva[RS_BITMAP] = rs_rip(im, t->rva[RS_BITMAP], 3, 7);
    }
    if (t->rva[RS_RFN] != 0)
    {
        t->rva[RS_RFN] = rs_rip(im, t->rva[RS_RFN], 3, 7);
    }
    if (t->rva[RS_SALT] != 0)
    {
        t->rva[RS_SALT] = rs_rip(im, t->rva[RS_SALT], 17, 21);
    }
}

// A pattern's own address, before derivation: kept apart so rs_derive can read the anchor twice.
static void rs_anchors(const RS_IMAGE *im, RS_TABLE *t)
{
    static const struct
    {
        int pat;
        RS_SYM sym;
    } MAP[] = {
        {P_AWARD, RS_AWARD}, {P_SITE, RS_SITE}, {P_LOADS, RS_LOAD_A}, {P_PUB, RS_PUB},
        {P_MASTER, RS_MASTER_FN}, {P_RECS, RS_RECS}, {P_SERIAL, RS_SERIAL}, {P_BITMAP, RS_BITMAP},
        {P_RFN, RS_RFN}, {P_SALT, RS_SALT},
    };
    for (int i = 0; i < (int)(sizeof(MAP) / sizeof(MAP[0])); i++)
    {
        t->rva[MAP[i].sym] = rs_locate(im, &RS_PAT_TAB[MAP[i].pat]);
    }
}

// --- the public scan --------------------------------------------------------------------------------------

int rs_scan(const unsigned char *image, RS_TABLE *t)
{
    if (t == NULL)
    {
        return 0;
    }
    memset(t, 0, sizeof(*t));
    if (!rs_pat_init())
    {
        return 0;
    }
    RS_IMAGE im;
    memset(&im, 0, sizeof(im));
    if (!rs_read_image(image, &im))
    {
        return 0;
    }
    t->ofimage = im.ofimage;
    rs_anchors(&im, t);
    rs_derive(&im, t);
    // the caller's verdict, if it has already been given: a scan fills the table, it never resets the verdict
    t->known_build = rs_known_build();
    return 1;
}

// The patterns' own match counts, for the offline checker: 0, 1, or 2 for "two or more".
int rs_pattern_hits(const unsigned char *image, int pattern, unsigned *rva)
{
    if (rva != NULL)
    {
        *rva = 0;
    }
    if (!rs_pat_init() || pattern < 0 || pattern >= RS_PAT_COUNT)
    {
        return -1;
    }
    RS_IMAGE im;
    memset(&im, 0, sizeof(im));
    if (!rs_read_image(image, &im))
    {
        return -1;
    }
    unsigned hit = 0;
    unsigned found = 0;
    int n = 0;
    for (int i = 0; i < im.n_exec; i++)
    {
        int c = rs_count(&RS_PAT_TAB[pattern], im.exec[i].at, im.exec[i].size, &hit);
        if (c == 0)
        {
            continue;
        }
        if (c > 1)
        {
            return 2;
        }
        n++;
        found = im.exec[i].va + hit;
    }
    if (n == 1 && rva != NULL)
    {
        *rva = found;
    }
    return n;
}

int rs_pattern_count(void)
{
    return RS_PAT_COUNT;
}

const char *rs_pattern_name(int pattern)
{
    return (pattern >= 0 && pattern < RS_PAT_COUNT) ? RS_PAT_NAME[pattern] : "?";
}

// --- the cached scan of one image --------------------------------------------------------------------------

static SRWLOCK RS_CACHE_LOCK = SRWLOCK_INIT;
static const void *RS_CACHE_BASE = NULL;
static RS_TABLE RS_CACHE;
static int RS_CACHE_STATE = 0; // 0 untried, 1 the scan succeeded, 2 it did not

const RS_TABLE *rs_for(const void *image)
{
    if (image == NULL)
    {
        return NULL;
    }
    if (RS_CACHE_STATE == 1 && RS_CACHE_BASE == image)
    {
        return &RS_CACHE;
    }
    AcquireSRWLockExclusive(&RS_CACHE_LOCK);
    if (RS_CACHE_STATE == 0 || RS_CACHE_BASE != image)
    {
        RS_CACHE_BASE = image;
        RS_CACHE_STATE = rs_scan((const unsigned char *)image, &RS_CACHE) ? 1 : 2;
    }
    RS_TABLE *out = (RS_CACHE_STATE == 1) ? &RS_CACHE : NULL;
    ReleaseSRWLockExclusive(&RS_CACHE_LOCK);
    return out;
}

void rs_set_known_build(int is_known)
{
    InterlockedExchange(&RS_KNOWN_BUILD, (is_known != 0) ? 1 : 0);
    AcquireSRWLockExclusive(&RS_CACHE_LOCK);
    RS_CACHE.known_build = (is_known != 0) ? 1 : 0;
    ReleaseSRWLockExclusive(&RS_CACHE_LOCK);
}

int rs_known_build(void)
{
    return InterlockedCompareExchange(&RS_KNOWN_BUILD, 0, 0) != 0 ? 1 : 0;
}

// --- the answers --------------------------------------------------------------------------------------------

unsigned rs_known_rva(RS_SYM s)
{
    return (s >= 0 && s < RS_SYM_COUNT) ? RS_KNOWN[s] : 0;
}

const char *rs_sym_name(RS_SYM s)
{
    return (s >= 0 && s < RS_SYM_COUNT) ? RS_NAME[s] : "?";
}

unsigned rs_rva(const RS_TABLE *t, RS_SYM s)
{
    if (t == NULL || s < 0 || s >= RS_SYM_COUNT)
    {
        return 0;
    }
    if (s == RS_CHVER || s == RS_SLOT)
    {
        // The two with no pattern: the measured constant, and only on the known build.
        return t->known_build ? RS_KNOWN[s] : 0;
    }
    return t->rva[s];
}

int rs_ok(const RS_TABLE *t, RS_SYM s)
{
    return rs_rva(t, s) != 0 ? 1 : 0;
}

int rs_resolved(const RS_TABLE *t)
{
    int n = 0;
    for (int i = 0; i < RS_SYM_COUNT; i++)
    {
        if (rs_ok(t, (RS_SYM)i))
        {
            n++;
        }
    }
    return n;
}

// --- the features ------------------------------------------------------------------------------------------

// Each feature, and exactly the symbols it reads. A feature whose list is not fully resolved turns itself off;
// another feature's missing symbol is not its business.
static const struct
{
    const char *name;
    RS_SYM syms[7];
    int n;
} RS_FEAT[RS_F_COUNT] = {
    {"nativepay", {RS_AWARD, RS_SITE, RS_LOAD_A, RS_LOAD_B, RS_KILL, RS_CRIT, RS_SYM_COUNT}, 6},
    {"publish", {RS_PUB, RS_SYM_COUNT, RS_SYM_COUNT, RS_SYM_COUNT, RS_SYM_COUNT, RS_SYM_COUNT, RS_SYM_COUNT}, 1},
    {"master", {RS_MASTER_FN, RS_MASTER_SITE0, RS_MASTER_SITE1, RS_MASTER_SITE2, RS_MASTER_SITE3, RS_RECS, RS_COUNT},
     7},
    {"g11", {RS_SERIAL, RS_BITMAP, RS_RFN, RS_SALT, RS_CHVER, RS_SLOT, RS_SYM_COUNT}, 6},
    {"pubxp", {RS_RECS, RS_COUNT, RS_RFN, RS_SALT, RS_CHVER, RS_SLOT, RS_SYM_COUNT}, 6},
    {"boundary", {RS_RECS, RS_COUNT, RS_SYM_COUNT, RS_SYM_COUNT, RS_SYM_COUNT, RS_SYM_COUNT, RS_SYM_COUNT}, 2},
};

const char *rs_feature_name(RS_FEATURE f)
{
    return (f >= 0 && f < RS_F_COUNT) ? RS_FEAT[f].name : "?";
}

const char *rs_feature_missing(const RS_TABLE *t, RS_FEATURE f)
{
    if (f < 0 || f >= RS_F_COUNT)
    {
        return "?";
    }
    for (int i = 0; i < RS_FEAT[f].n; i++)
    {
        if (!rs_ok(t, RS_FEAT[f].syms[i]))
        {
            return rs_sym_name(RS_FEAT[f].syms[i]);
        }
    }
    return NULL;
}

int rs_feature_ok(const RS_TABLE *t, RS_FEATURE f)
{
    return rs_feature_missing(t, f) == NULL ? 1 : 0;
}

// --- the report ----------------------------------------------------------------------------------------------

static int rs_debug_on(void)
{
    wchar_t dir[MAX_PATH];
    wchar_t path[MAX_PATH];
    DWORD n = GetTempPathW(MAX_PATH, dir);
    if (n == 0 || n >= MAX_PATH)
    {
        return 0;
    }
    if (_snwprintf_s(path, MAX_PATH, _TRUNCATE, L"%sprogression-tuning\\resolve_debug.txt", dir) < 0)
    {
        return 0;
    }
    DWORD a = GetFileAttributesW(path);
    return (a != INVALID_FILE_ATTRIBUTES && a != 0xFFFFFFFFu) ? 1 : 0;
}

void rs_report(const RS_TABLE *t)
{
    if (t == NULL)
    {
        ch_logf("resolve: no table - the client image could not be read, every feature is off");
        return;
    }
    RS_TABLE *w = (RS_TABLE *)t;
    if (InterlockedCompareExchange(&w->reported, 1, 0) != 0)
    {
        return;
    }

    int n = rs_resolved(t);
    char list[192];
    list[0] = '\0';
    int missing = 0;
    for (int i = 0; i < RS_SYM_COUNT; i++)
    {
        if (rs_ok(t, (RS_SYM)i))
        {
            continue;
        }
        int used = (int)strlen(list);
        _snprintf_s(list + used, sizeof(list) - (size_t)used, _TRUNCATE, "%s%s", missing != 0 ? ", " : "",
                    rs_sym_name((RS_SYM)i));
        missing++;
    }
    ch_logf("resolve: %d/%d symbols (%s)", n, (int)RS_SYM_COUNT, missing == 0 ? "all" : list);

    int debug = rs_debug_on();
    for (int i = 0; i < RS_SYM_COUNT; i++)
    {
        unsigned got = rs_rva(t, (RS_SYM)i);
        unsigned known = RS_KNOWN[i];
        if (got != 0 && got != known)
        {
            ch_logf("resolve: %s differs from the known build (rva 0x%lX, known 0x%lX)", rs_sym_name((RS_SYM)i),
                    (unsigned long)got, (unsigned long)known);
        }
        else if (debug)
        {
            ch_logf("resolve: %s rva 0x%lX, known 0x%lX", rs_sym_name((RS_SYM)i), (unsigned long)got,
                    (unsigned long)known);
        }
    }
    if (t->known_build == 0)
    {
        ch_logf("resolve: the image is not the known build, so chver and slot (the two with no pattern) stay "
                "unresolved and g11 and pubxp turn off");
    }
}
