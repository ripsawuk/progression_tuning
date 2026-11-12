// clienthook - the frame: what runs in the game process beside the proxy and the payment.
//
// Five things, and nothing else:
//
//   1. the install gate. One mutex, created here and handed to master.c's installer and to nativepay.c's, so
//      the two thread-freeze windows (five call sites, one call site) can never overlap. It lives as long as
//      the process and is never closed.
//   2. the game's own event stream. `players\ae_events.log` is written by the client through WriteFile /
//      WriteFileEx; the hooks on those two slots feed `aexp.c`'s line parser, and the match boundary
//      (`ev=109`) resets the published per-match figures. Read-only: no byte of the stream is changed.
//   3. the attachment-lock payload (g11). After each of the client's own publishes, the client's live lock
//      bitmap (`*(void**)(client+0x466CD8)`, 32,768 B) is copied into 33 hex dvars plus a header, through the
//      client's own register-or-find, so every lock it holds can reach the menu. No client byte is written.
//   4. the published weapon XP (`ptsplash_paid`). `nativepay.c` calls `pubxp_on_paid` around each payment on
//      the client's drain thread; this file reads the gun's record (`rec+0x560`) at both edges, keeps the
//      ledger in `pubxp.c` and stores the text into the dvar from its own thread.
//   5. the forced publish (`publish.c`). A thread of ours calls the client's own serialise-and-publish
//      (`client+0x962E0`) once a paid payment or a moved record asks for one, at most once per second, so the
//      state a menu reads is taken during a match instead of only at a boundary.
//
// Four threads: `probe_thread` (waits for the client image, installs master.c's hook, patches the four import
// slots), `g11_thread` (arms the payload and publishes it), `pxp_thread` (arms `ptsplash_paid`, writes it, and
// emits the log lines for both channels) and `publish_thread` (the forced publish's clock and its record scan).
// The client's own threads only ever reach memory here: `ae_on_rec` and `pubxp_on_paid` run on them, and neither
// opens a file except the once-per-match `ev=109` line.
//
// Import-table patching only - no inline hooks - so the client's own code is never rewritten: `patch_module`
// walks a module's import descriptors and replaces the four named slots, recording what the kernel32 address
// was first so every hook calls through.

#include <windows.h>
#include <stdio.h>
#include <wchar.h>

#include "aexp.h"
#include "g11.h"
#include "master.h"
#include "pubxp.h"
#include "nativepay.h"
#include "publish.h"
#include "resolve.h"

void ch_logf(const char *fmt, ...);

// --- where this file's client addresses come from --------------------------------------------------------
//
// Every one of them is asked of resolve.c, which finds it in the client's own executable sections. publish.h
// keeps PUB_RVA as the measured constant - that is the value the resolver compares its answer against and
// reports on - so under this name the file uses the resolver's answer instead, which is that same 0x962E0 on the
// build the release was measured on and follows the pattern on any other.
#undef PUB_RVA
#define PUB_RVA (pub_rva(client))

static unsigned pub_rva(HMODULE client)
{
    return rs_rva(rs_for(client), RS_PUB);
}

// One reason line for a feature whose symbols are not all resolved: "<symbol> is not resolved in this client".
static const char *frame_reason(char *buf, size_t cap, const RS_TABLE *rs, RS_FEATURE f)
{
    const char *miss = rs_feature_missing(rs, f);
    _snprintf_s(buf, cap, _TRUNCATE, "%s is not resolved in this client", miss != NULL ? miss : "an address");
    return buf;
}

// Both are called from threads that are not ours (the client's drain thread and the ae_events path), so they
// are forward-declared above the block that defines them.
void pubxp_on_paid(unsigned int loot, int amount, int phase);
void pubxp_match_reset(void);

// The publish gate's state (publish.h). Declared here, not beside its thread, because the payment's own hook
// raises its want and that hook is defined above the block that drives it.
static PUB_GATE PUB;

typedef HANDLE(WINAPI *fn_create_file_w)(LPCWSTR, DWORD, DWORD, LPSECURITY_ATTRIBUTES, DWORD, DWORD, HANDLE);
typedef HANDLE(WINAPI *fn_create_file_a)(LPCSTR, DWORD, DWORD, LPSECURITY_ATTRIBUTES, DWORD, DWORD, HANDLE);
typedef BOOL(WINAPI *fn_write_file)(HANDLE, LPCVOID, DWORD, LPDWORD, LPOVERLAPPED);
typedef BOOL(WINAPI *fn_write_file_ex)(HANDLE, LPCVOID, DWORD, LPOVERLAPPED, LPOVERLAPPED_COMPLETION_ROUTINE);

static fn_create_file_w real_create_file_w;
static fn_create_file_a real_create_file_a;
static fn_write_file real_write_file;
static fn_write_file_ex real_write_file_ex;

// --- the game's own event stream ---------------------------------------------------------------
//
// One line of `players\ae_events.log` is `<unix time>\tev=<n>\t<field>=<value>\t...` (aexp.h parses it). The
// handle is taken from the open when the hooks are armed in time, otherwise from the first write that looks
// like an event line (`<digits>\tev=`) and whose handle resolves to the file. A WriteFile may carry part of a
// line or several, so the accumulator only hands over whole lines.
//
// Only one event is acted on here: `ev=109`, the match start, which drops every gun's per-match base so
// `ptsplash_paid` renders 0 until the next payment. The rest of the stream is the payment's own business -
// `nativepay.c` reads field 45 off the event it intercepts.

#define AE_REJECT_MAX 64

static SRWLOCK AE_LOCK = SRWLOCK_INIT;
static HANDLE volatile AE_H = NULL;
static HANDLE AE_REJECT[AE_REJECT_MAX];
static int AE_REJECT_N = 0;
static AE_ACC AE_ACCUM;

static int ae_tail_is(const wchar_t *path)
{
    if (path == NULL)
        return 0;
    const wchar_t *tail = wcsrchr(path, L'\\');
    tail = (tail == NULL) ? path : tail + 1;
    return _wcsicmp(tail, L"ae_events.log") == 0;
}

static int ae_tail_is_a(const char *path)
{
    if (path == NULL)
        return 0;
    const char *tail = strrchr(path, '\\');
    tail = (tail == NULL) ? path : tail + 1;
    return _stricmp(tail, "ae_events.log") == 0;
}

static void ae_adopt(HANDLE h, DWORD access, const char *via)
{
    if (h == INVALID_HANDLE_VALUE || h == NULL)
        return;
    if ((access & (GENERIC_WRITE | GENERIC_ALL | FILE_WRITE_DATA | FILE_APPEND_DATA)) == 0)
        return;
    AcquireSRWLockExclusive(&AE_LOCK);
    HANDLE old = AE_H;
    AE_H = h;
    AE_ACCUM.n = 0;
    AE_ACCUM.overflow = 0;
    ReleaseSRWLockExclusive(&AE_LOCK);
    ch_logf("ae: ae_events.log handle taken via=%s access=0x%lX%s", via, (unsigned long)access,
            old != NULL ? " (replaces an earlier handle)" : "");
}

static void ae_on_rec(const AE_REC *r, void *ctx)
{
    (void)ctx;
    if (r->ev != 109)
        return;
    // ONE BOUNDARY, ONE RESET. The payment's own wrapper (nativepay_call, on the client's award call)
    // sees ev=109 unconditionally and owns the boundary whenever it is installed - which is the case with the
    // stock `log_events 0`, where no line ever reaches this reader. So when the wrapper is live this path stays
    // quiet: the same boundary cannot reset twice, and a payment that arrived between the two would keep its base.
    // This reader is the fallback for the one configuration where the wrapper is not installed (the nativepay kill
    // switch), and then only `log_events 1` gets it the event at all.
    if (nativepay_hook_live())
        return;
    ch_logf("ae: ev=109 match start - the published per-match figures reset");
    pubxp_match_reset();
}

static void ae_absorb(LPCVOID buf, DWORD n)
{
    if (buf == NULL || n == 0)
        return;
    AcquireSRWLockExclusive(&AE_LOCK);
    ae_feed(&AE_ACCUM, (const char *)buf, (size_t)n, ae_on_rec, NULL);
    ReleaseSRWLockExclusive(&AE_LOCK);
}

// a write that looks like an event line, on a handle nobody has named yet
static int ae_sniff(HANDLE h, LPCVOID buf, DWORD n)
{
    const char *b = (const char *)buf;
    if (b == NULL || n < 8 || b[0] < '1' || b[0] > '9')
        return 0;
    DWORD lim = n < 20 ? n : 20;
    int hit = 0;
    for (DWORD i = 1; i + 3 < lim; i++)
    {
        if (b[i] == '\t' && b[i + 1] == 'e' && b[i + 2] == 'v' && b[i + 3] == '=')
        {
            hit = 1;
            break;
        }
        if (b[i] < '0' || b[i] > '9')
            break;
    }
    if (!hit)
        return 0;
    AcquireSRWLockShared(&AE_LOCK);
    for (int i = 0; i < AE_REJECT_N; i++)
    {
        if (AE_REJECT[i] == h)
        {
            ReleaseSRWLockShared(&AE_LOCK);
            return 0;
        }
    }
    ReleaseSRWLockShared(&AE_LOCK);
    // name queries can block on a synchronous pipe with a pending read: only ever ask a disk file
    DWORD len = 0;
    wchar_t path[MAX_PATH];
    if (GetFileType(h) == FILE_TYPE_DISK)
    {
        len = GetFinalPathNameByHandleW(h, path, MAX_PATH, FILE_NAME_NORMALIZED);
    }
    if (len > 0 && len < MAX_PATH && ae_tail_is(path))
    {
        ae_adopt(h, FILE_APPEND_DATA, "write-sniff");
        return 1;
    }
    AcquireSRWLockExclusive(&AE_LOCK);
    if (AE_REJECT_N < AE_REJECT_MAX)
        AE_REJECT[AE_REJECT_N++] = h;
    ReleaseSRWLockExclusive(&AE_LOCK);
    ch_logf("ae: an event-shaped write went to another file (len=%lu) - ignored", (unsigned long)len);
    return 0;
}

static void ae_route_write(HANDLE h, LPCVOID buf, DWORD n)
{
    if (h == AE_H)
    {
        ae_absorb(buf, n);
    }
    else if (AE_H == NULL && ae_sniff(h, buf, n))
    {
        ae_absorb(buf, n);
    }
}

static BOOL WINAPI hook_write_file(HANDLE h, LPCVOID buf, DWORD want, LPDWORD wrote, LPOVERLAPPED ov)
{
    BOOL ok = real_write_file(h, buf, want, wrote, ov);
    if (ok)
    {
        ae_route_write(h, buf, (wrote != NULL && ov == NULL) ? *wrote : want);
    }
    return ok;
}

static BOOL WINAPI hook_write_file_ex(HANDLE h, LPCVOID buf, DWORD want, LPOVERLAPPED ov,
                                      LPOVERLAPPED_COMPLETION_ROUTINE cb)
{
    BOOL ok = real_write_file_ex(h, buf, want, ov, cb);
    if (ok)
    {
        ae_route_write(h, buf, want);
    }
    return ok;
}

// --- g11: the payload channel ------------------------------------------------------------------
//
// The client's own publish serialises a 273,448 B state into 96 chunks and Kronos's reader drops everything
// above 96 (`LUIFPSCounter.lua`), so only 14,702 of its locks ever reach the menu. This does not touch that
// channel: after each publish it copies the client's live lock bitmap (`*(void**)(client+0x466CD8)`, 32,768 B,
// ids 1..0x3FFFF) as 65,536 lowercase hex chars into 33 dvars of 2,000, then writes the serial into the header
// dvar LAST, the order the client itself uses for its chunks and its serial. The 35 dvars are created here
// where absent, with the client's own register-or-find, so the payload is published from the frontend with no
// match.
//
// Every address below is one the client's own code uses, and each is guarded before it is used:
//   the image      identified three ways - size 5,016,064 B, SHA-256 88a52103...fcfb, PE SizeOfImage 0x9A1000
//   the address    all nineteen come from resolve.c, out of this build's own executable sections: a pattern that
//                  matches exactly once, or an address derived from one that did (frame.c carries no number)
//   the register   `*(void**)(client+0x6C4280)` (resolved about 15 s into boot), whose
//   function       9-byte prologue the client itself compares; the bytes sit in the client at rva 0x16E490
//                  - 48 83 EC 58 48 89 54 24 30
//   the call       the client's own registration of `zm_ch_state`, `zm_ch_ver` and the 96 `zm_ch_s%d`:
//                  hash, default, flags, description - and it CREATES the dvar when it is missing
//   the hash       our port of the client's own name hash (client+0xB8420), proven against the client's own
//                  `zm_ch_ver` dvar_t pointer at `*(void**)(client+0x3E6840)`
//   the slot       `*(int*)(client+0x27764C)`, the string-value offset the client discovered for its own
//                  string dvars and then used for all 96 chunks
//   the bitmap     `*(void**)(client+0x466CD8)`, copied with a pointer re-read after the copy
//   the serial     `*(unsigned*)(client+0x3E6CBC)`, which the client increments itself
//
// A validation failure (slot not writable, a value that is not the sentinel) latches the feature off for the
// session with one `g11: refused - ...` line; a register-or-find that returns nothing is NOT a failure, it is
// "waiting" (retried every 5 s), because the function pointer only resolves after ~15 s; a bitmap that is not
// there yet, or a copy that straddles the client's buffer flip, skips that publish only.

// The six data addresses this channel reads are resolve.h's RS_SERIAL, RS_BITMAP, RS_CHVER, RS_SLOT, RS_RFN and
// RS_SALT; this file carries no number of its own. What follows is the identification triple, which is what
// decides whether RS_CHVER and RS_SLOT - the two with no pattern - may use their measured values.

#define G11_IMAGE_SIZE 5016064UL
#define G11_IMAGE_OFIMAGE 0x9A1000UL

static const char G11_IMAGE_SHA[65] =
    "88a52103c5555b2760f1e7ad13a594e8ef0440f007b45a10bddc61dda234fcfb";

static const unsigned char G11_RFN_SIG[9] = {0x48, 0x83, 0xEC, 0x58, 0x48, 0x89, 0x54, 0x24, 0x30};

// [0] the arm signal, [1] the header, [2..34] the 33 parts - the order the mod's GSC creates them in.
#define G11_DVARS (G11_PARTS + 2)

static const char *G11_NAMES[G11_DVARS] = {
    "zm_g11_arm", "zm_g11_ver",
    "zm_g11_0",  "zm_g11_1",  "zm_g11_2",  "zm_g11_3",  "zm_g11_4",  "zm_g11_5",
    "zm_g11_6",  "zm_g11_7",  "zm_g11_8",  "zm_g11_9",  "zm_g11_10", "zm_g11_11",
    "zm_g11_12", "zm_g11_13", "zm_g11_14", "zm_g11_15", "zm_g11_16", "zm_g11_17",
    "zm_g11_18", "zm_g11_19", "zm_g11_20", "zm_g11_21", "zm_g11_22", "zm_g11_23",
    "zm_g11_24", "zm_g11_25", "zm_g11_26", "zm_g11_27", "zm_g11_28", "zm_g11_29",
    "zm_g11_30", "zm_g11_31", "zm_g11_32"};

static unsigned char G11_BITMAP[G11_BITMAP_BYTES];
// two banks, so a Lua reader holding one string never sees it change under it
static char G11_BANK[2][G11_PARTS][G11_PART_CHARS + 1];
static char G11_VERBUF[2][G11_VER_CAP];
static void *G11_DVAR[G11_DVARS];
static long G11_SLOT = -1;
static G11GATE G11_GATE_STATE;
static volatile LONG G11_OFF = 0;
static int G11_ARMED = 0;
static unsigned G11_LAST = 0;
static int G11_SEEN = 0;
static int G11_BANK_NOW = 0;
static long G11_PUBLISHED = 0;
static int G11_SAID_NORFN = 0;
static int G11_SAID_ABSENT = 0;
static int G11_SAID_NOBITMAP = 0;
static int G11_SAID_UNSTABLE = 0;

static void g11_latch(const char *why)
{
    g11_gate(&G11_GATE_STATE, G11_REFUSE, why);
    InterlockedExchange(&G11_OFF, 1);
}

// --- the identification pass -----------------------------------------------------------------------------
//
// Size + PE header + SHA-256 of the client image, once for the session, and the verdict handed to the resolver.
// THE VERDICT IS NOT A REFUSAL. It decides one thing only: whether the two addresses with no pattern of their own
// (`zm_ch_ver`'s dvar_t slot and the string-value slot) may use their measured values. Every other address is
// resolved from whatever build is loaded, so a client we have never measured still gets the payment, the level
// hook and the forced publish; only the payload channel and the paid-XP text, which need those two, go quiet.
//
// 0 untried, 1 the pinned build, 2 not the pinned build, 3 the image could not be measured at all.
static volatile LONG FRAME_IMAGE = 0;
static SRWLOCK FRAME_IMAGE_LOCK = SRWLOCK_INIT;

static int frame_identify(HMODULE client)
{
    if (InterlockedCompareExchange(&FRAME_IMAGE, 0, 0) != 0)
    {
        return FRAME_IMAGE == 1 ? 1 : 0;
    }
    AcquireSRWLockExclusive(&FRAME_IMAGE_LOCK);
    if (FRAME_IMAGE == 0)
    {
        LONG verdict = 3;
        wchar_t path[MAX_PATH];
        DWORD n = (client != NULL) ? GetModuleFileNameW(client, path, MAX_PATH) : 0;
        HANDLE f = INVALID_HANDLE_VALUE;
        LARGE_INTEGER sz = {{0, 0}};
        if (n > 0 && n < MAX_PATH)
        {
            f = CreateFileW(path, GENERIC_READ, FILE_SHARE_READ | FILE_SHARE_WRITE | FILE_SHARE_DELETE, NULL,
                            OPEN_EXISTING, FILE_ATTRIBUTE_NORMAL, NULL);
        }
        if (f != INVALID_HANDLE_VALUE && GetFileSizeEx(f, &sz))
        {
            CloseHandle(f);
            f = INVALID_HANDLE_VALUE;
            IMAGE_DOS_HEADER *dos = (IMAGE_DOS_HEADER *)client;
            IMAGE_NT_HEADERS *nt = (dos->e_magic == IMAGE_DOS_SIGNATURE)
                                       ? (IMAGE_NT_HEADERS *)((BYTE *)client + dos->e_lfanew)
                                       : NULL;
            unsigned ofimage = 0;
            int header_ok = (nt != NULL && nt->Signature == IMAGE_NT_SIGNATURE &&
                             nt->FileHeader.Machine == IMAGE_FILE_MACHINE_AMD64);
            if (header_ok)
            {
                ofimage = nt->OptionalHeader.SizeOfImage;
            }
            if (!header_ok)
            {
                ch_logf("client: the image has no usable PE header - no address can be resolved");
            }
            else
            {
                unsigned char sha[32];
                char hex[65];
                if (g11_sha256_file(path, sha) == 0)
                {
                    g11_hex32(sha, hex);
                    int pinned = ((unsigned long long)sz.QuadPart == (unsigned long long)G11_IMAGE_SIZE) &&
                                 (ofimage == G11_IMAGE_OFIMAGE) && (_stricmp(hex, G11_IMAGE_SHA) == 0);
                    verdict = pinned ? 1 : 2;
                    if (pinned)
                    {
                        ch_logf("client: the pinned build - %lu B, sha256 %s, SizeOfImage 0x%lX",
                                (unsigned long)sz.QuadPart, hex, (unsigned long)ofimage);
                    }
                    else
                    {
                        ch_logf("client: not the pinned build (%lu B, sha256 %s, SizeOfImage 0x%lX) - every address "
                                "comes from this image's own code",
                                (unsigned long)sz.QuadPart, hex, (unsigned long)ofimage);
                    }
                }
                else
                {
                    ch_logf("client: the file's sha256 could not be computed - the two pattern-less addresses "
                            "stay unresolved");
                }
            }
        }
        else
        {
            if (f != INVALID_HANDLE_VALUE)
            {
                CloseHandle(f);
            }
            ch_logf("client: the image could not be sized or has no readable path - the two pattern-less "
                    "addresses stay unresolved");
        }
        InterlockedExchange(&FRAME_IMAGE, verdict);
        if (verdict == 1 || verdict == 2)
        {
            rs_set_known_build(verdict == 1);
            rs_report(rs_for(client));
        }
    }
    ReleaseSRWLockExclusive(&FRAME_IMAGE_LOCK);
    return FRAME_IMAGE == 1 ? 1 : 0;
}

static const RS_TABLE *G11_RS = NULL; // the resolver's answers, set by g11_arm

static int g11_arm(HMODULE client)
{
    // THE IDENTIFICATION PASS first: it logs once and hands the resolver its verdict. What then gates this
    // feature is the addresses it needs, not the image's hash - a build we have never measured gets the channel
    // whenever its own code carries all six.
    frame_identify(client);
    G11_RS = rs_for(client);
    if (!rs_feature_ok(G11_RS, RS_F_G11))
    {
        char why[96];
        ch_logf("g11: refused - %s; the payload channel is off for this session",
                frame_reason(why, sizeof(why), G11_RS, RS_F_G11));
        g11_latch("resolver");
        return 0;
    }

    void *rf = *(void **)((BYTE *)client + rs_rva(G11_RS, RS_RFN));
    if (rf == NULL)
    {
        if (!G11_SAID_NORFN)
        {
            G11_SAID_NORFN = 1;
            ch_logf("g11: the register function is not resolved yet (the client needs ~15 s) - waiting");
        }
        return 0;
    }
    if (!g11_page_ok(rf) || memcmp(rf, G11_RFN_SIG, sizeof(G11_RFN_SIG)) != 0)
    {
        ch_logf("g11: refused - the register function at 0x%08lX does not carry its 9-byte prologue",
                (unsigned long)((ULONG_PTR)rf & 0xFFFFFFFFu));
        g11_latch("register function");
        return 0;
    }

    unsigned salt_rva = rs_rva(G11_RS, RS_SALT);
    const unsigned char *salt = (const unsigned char *)((BYTE *)client + salt_rva);
    if (!g11_page_ok(salt))
    {
        ch_logf("g11: refused - the name-hash salt at rva 0x%lX is not readable", (unsigned long)salt_rva);
        g11_latch("hash salt");
        return 0;
    }

    G11_REG reg = (G11_REG)rf; // g11.h's own typedef: one signature, so the create pass and this call agree

    // The hash proof: a dvar the client already registered, found with OUR hash of its name, must be the same
    // dvar_t the client's own registration stored. A wrong hash cannot pass this.
    void *got = reg(g11_hash_name("zm_ch_ver", salt), G11_PROBE, 0, "g11 hash self-test");
    void *want = *(void **)((BYTE *)client + rs_rva(G11_RS, RS_CHVER));
    if (got == NULL || want == NULL || got != want)
    {
        ch_logf("g11: refused - the name hash does not match the client (zm_ch_ver -> 0x%08lX, want 0x%08lX)",
                (unsigned long)((ULONG_PTR)got & 0xFFFFFFFFu), (unsigned long)((ULONG_PTR)want & 0xFFFFFFFFu));
        g11_latch("name hash");
        return 0;
    }

    long off = (long)*(int *)((BYTE *)client + rs_rva(G11_RS, RS_SLOT));
    if (!g11_slot_ok(off))
    {
        ch_logf("g11: refused - the string slot offset is %ld, outside 0..0xFF or not 8-aligned", off);
        g11_latch("string slot");
        return 0;
    }

    // Find all 35 - and create any that are not there, through the client's own register-or-find. The default
    // is the SENTINEL, so a dvar this call creates is indistinguishable from one the mod's GSC made and the
    // canary below passes for both; asking with the probe default here would make the hook refuse itself.
    {
        int bad = -1;
        G11CREATE got35 = g11_dvar_pass(reg, salt, G11_NAMES, G11_DVARS, off, G11_DVAR);
        if (got35.usable != G11_DVARS)
        {
            bad = got35.bad;
            if (bad < 0 || bad >= G11_DVARS)
            {
                ch_logf("g11: refused - the payload dvar pass returned %d of %d", got35.usable, G11_DVARS);
                g11_latch("payload dvars");
                return 0;
            }
            if (got35.reason == G11_D_NULL)
            {
                // Not a verdict on the client's state: the engine has not resolved its register function yet
                // (or is still starting). Waiting is what a missing mod used to require, and it costs nothing.
                if (!G11_SAID_ABSENT)
                {
                    G11_SAID_ABSENT = 1;
                    ch_logf("g11: waiting - the engine did not hand back %s (the register function is not "
                            "usable yet); retrying every 5 s",
                            G11_NAMES[bad]);
                }
                return 0;
            }
            if (got35.reason == G11_D_SLOT)
            {
                ch_logf("g11: refused - the value slot of %s is not writable", G11_NAMES[bad]);
                g11_latch("value slot");
                return 0;
            }
            ch_logf("g11: refused - %s does not read \"%s\" back (the engine created it with another value)",
                    G11_NAMES[bad], G11_SENTINEL);
            g11_latch("payload value");
            return 0;
        }
    }

    G11_SLOT = off;
    G11_ARMED = 1;
    g11_gate(&G11_GATE_STATE, G11_OK, NULL);
    ch_logf("g11: armed - %d payload dvars validated at slot %ld, register 0x%08lX, 33 parts of %d hex chars "
            "(created here where absent - no match needed)",
            G11_DVARS, off, (unsigned long)((ULONG_PTR)rf & 0xFFFFFFFFu), G11_PART_CHARS);
    return 1;
}

static void g11_publish(HMODULE client)
{
    unsigned serial = *(volatile unsigned *)((BYTE *)client + rs_rva(G11_RS, RS_SERIAL));
    if (G11_SEEN && serial == G11_LAST)
    {
        return; // nothing published since the last time: no work, no bytes
    }

    unsigned char *bm = *(unsigned char **)((BYTE *)client + rs_rva(G11_RS, RS_BITMAP));
    if (bm == NULL || !g11_page_ok(bm))
    {
        if (!G11_SAID_NOBITMAP)
        {
            G11_SAID_NOBITMAP = 1;
            ch_logf("g11: the lock bitmap is not published yet - skipped");
        }
        return;
    }

    // The client clears and fills the OTHER buffer and then flips the pointer, so a
    // copy that straddles the flip can mix two bitmaps. Copy, then re-read the pointer and the first/last
    // dword; a change means "try again on the buffer we now see".
    int stable = 0;
    unsigned char *p0 = bm;
    for (int attempt = 0; attempt < 3 && !stable; attempt++)
    {
        if (!g11_page_ok(p0))
        {
            break;
        }
        unsigned long head = *(volatile unsigned long *)p0;
        unsigned long tail = *(volatile unsigned long *)(p0 + G11_BITMAP_BYTES - 4);
        memcpy(G11_BITMAP, p0, G11_BITMAP_BYTES);
        unsigned char *p1 = *(unsigned char **)((BYTE *)client + rs_rva(G11_RS, RS_BITMAP));
        unsigned long head2 = *(volatile unsigned long *)p0;
        unsigned long tail2 = *(volatile unsigned long *)(p0 + G11_BITMAP_BYTES - 4);
        if (p1 == p0 && head == head2 && tail == tail2)
        {
            stable = 1;
        }
        else
        {
            p0 = p1;
        }
    }
    if (!stable)
    {
        if (!G11_SAID_UNSTABLE)
        {
            G11_SAID_UNSTABLE = 1;
            ch_logf("g11: bitmap copy unstable (2 retries) - skipped");
        }
        return;
    }

    int bank = G11_BANK_NOW ^ 1;
    for (int i = 0; i < G11_PARTS; i++)
    {
        size_t off = g11_part_offset(i) / 2; // hex chars -> bitmap bytes: 1,000 a part
        size_t len = g11_part_chars(i) / 2;  // 1,000, or 768 for the last
        g11_hex(G11_BITMAP + off, len, G11_BANK[bank][i]);
    }
    for (int i = 0; i < G11_PARTS; i++)
    {
        *(char **)((BYTE *)G11_DVAR[2 + i] + G11_SLOT) = G11_BANK[bank][i];
    }
    // the header LAST, so a reader can never pair a new serial with old parts
    g11_ver(G11_VERBUF[bank], sizeof(G11_VERBUF[bank]), serial, G11_PARTS, G11_HEX);
    *(char **)((BYTE *)G11_DVAR[1] + G11_SLOT) = G11_VERBUF[bank];

    G11_BANK_NOW = bank;
    G11_LAST = serial;
    G11_SEEN = 1;
    long n = InterlockedIncrement(&G11_PUBLISHED);
    if (n <= 3 || (n % 60) == 0)
    {
        // counted part by part: the 33 strings are separate C strings, not one 65,536-char run
        int ids = 0;
        for (int i = 0; i < G11_PARTS; i++)
        {
            ids += g11_count_ids(G11_BANK[bank][i], g11_part_chars(i));
        }
        ch_logf("g11: published serial %u %d B in %d parts (32768 B bitmap, %d ids, #%ld)", serial, G11_HEX,
                G11_PARTS, ids, n);
    }
}

static DWORD WINAPI g11_thread(LPVOID unused)
{
    (void)unused;
    ULONGLONG last_try = 0;
    for (;;)
    {
        Sleep(250);
        if (G11_OFF)
        {
            continue;
        }
        HMODULE client = GetModuleHandleW(L"XINPUT9_1_0.dll");
        if (client == NULL)
        {
            continue;
        }
        if (!G11_ARMED)
        {
            ULONGLONG now = GetTickCount64();
            if (last_try != 0 && now - last_try < 5000)
            {
                continue;
            }
            last_try = now;
            if (!g11_arm(client))
            {
                continue;
            }
        }
        g11_publish(client);
    }
}

// --- the paid weapon XP, published into ONE dvar -------------------------------------------------
//
// A dvar the splash GSC also names, created and found by the client's own register-or-find
// (`client+0x6C4280`, the g11 pass above) and written through the string-value slot the client discovered for
// its own string dvars (`client+0x27764C`); what is different here is WHEN it is written - per payment,
// mid-match.
//
// WHAT IS PUBLISHED, and why this form cannot double count: one ABSOLUTE number per gun, the client's record
// XP (`rec+0x560`) read immediately after the wrapped award returned, plus the same record's value from before
// this match's first payment (`loot:total:thisMatch`, version-prefixed, bounded at 8 guns - pubxp.h holds
// the format, the ledger and the record lookup, all unit-tested offline).
//
// TIMING. Two callers, both on threads that are not ours:
//   * nativepay's wrapper, on the client's own event-drain thread, calls `pubxp_on_paid` twice
//     per payment - phase 0 before the award (that is when a missing base is read), phase 1 after it returned
//     (that is when the new total is read and the text is stored). No log, no file, no client lock taken.
//   * our own `pxp_thread` arms the dvar, publishes the constant `probe` once, writes the text, and emits the
//     log lines - the client's thread never opens a file.
//
// WRITE ONLY WHEN IT CHANGES. `pxp_render` compares the new text with what was last stored (`shown`); an
// unchanged payload is never written again, so a repeat payment of 0 XP or a re-read that moves nothing costs
// no store. The text is double-buffered (`PXP_BANK_TEXT`) so a Lua reader holding one string never sees it
// change underneath (the client's own rule); the mod's GSC may `setdvar` this name at
// level start, and our next store puts ours back.
//
// FAILURE BEHAVIOUR follows g11's: a null register function is WAITING (retried every 5 s, the pointer
// resolves ~15 s after boot), and a real validation failure latches this channel off with one
// `pubxp: refused - ...`, while the payment itself carries on untouched (the two are independent).

#define PXP_DVAR_NAME "ptsplash_paid"
#define PXP_REC_MAX 20000 // a store larger than this is not the client's record array (4,508 rows today)
#define PXP_LOG_EACH 20   // publish and self-check lines: the first 3, then every 20th
#define PXP_LOG_TEXT 220  // how much of the payload a log line carries (the log's own buffer is 512)

static SRWLOCK PXP_LOCK = SRWLOCK_INIT;
static PXP_LEDGER PXP_L;
static char PXP_BANK_TEXT[2][PXP_TEXT_MAX];
static int PXP_BANK = 0;
static void *PXP_DVAR = NULL;
static long PXP_SLOT = -1;
static volatile LONG PXP_OFF = 0; // latched off for the session
static int PXP_ARMED = 0;
static int PXP_SAID_WAIT = 0;
static volatile LONG PXP_KIND_SEEN = 0; // the kind of a record that matched owner+ev=95 but not the weapon kind
static unsigned PXP_KIND_LOOT = 0;
static int PXP_KIND_ROWS = 0;
static volatile LONG PXP_NOARM = 0; // payments seen before the dvar armed (one note, logged by our thread)
static volatile LONG PXP_MISMATCH = 0;
static volatile LONG PXP_PAYMENTS = 0;
static volatile LONG PXP_PUBLISHES = 0;
static volatile LONG PXP_NOREC = 0;  // a payment whose record could not be read (one note)
static volatile LONG PXP_CAPPED = 0; // a payment for a loot id past the 8-gun cap (one note)
static unsigned PXP_BAD_LOOT = 0;
static int PXP_BAD_PAID = 0;
static long long PXP_BAD_D = 0;
// the per-payment self-check: one line per payment, rate-limited, emitted by OUR thread because the values are
// read on the drain thread. A 64-slot ring, one producer (the drain), one consumer (ours).
#define PXP_RING 64
static struct
{
    unsigned loot;
    int paid;
    long long before;
    long long after;
} PXP_RING_BUF[PXP_RING];
static volatile LONG PXP_RING_W = 0;
static volatile LONG PXP_RING_R = 0;
static volatile LONG PXP_SELFCHK = 0;
// one payment at a time (nativepay's NP_BUSY guarantees it), so these need no lock of their own
static unsigned long PXP_PEND_LOOT = 0;
static long long PXP_PEND_BEFORE = 0;
static int PXP_PEND_REC = -1;
static int PXP_PEND_OK = 0;

// The record array: the two data addresses resolve.h calls RS_RECS and RS_COUNT, checked readable at both ends
// before a single field is read. The resolver is asked here rather than threaded through the call, because this
// is the one function both the publish thread's scan and the paid channel read the array through.
static int pxp_records(HMODULE client, unsigned char **out, int *count)
{
    const RS_TABLE *rs = rs_for(client);
    unsigned recs_rva = rs_rva(rs, RS_RECS);
    unsigned count_rva = rs_rva(rs, RS_COUNT);
    if (recs_rva == 0 || count_rva == 0)
    {
        return -1; // the boundary feature is off: no array address in this build
    }
    unsigned char *recs = *(unsigned char **)((BYTE *)client + recs_rva);
    int n = *(volatile int *)((BYTE *)client + count_rva);
    if (recs == NULL || n <= 0 || n > PXP_REC_MAX)
    {
        return -1;
    }
    if (!g11_page_ok(recs) || !g11_page_ok(recs + (size_t)(n - 1) * MASTER_STRIDE + MASTER_REC_XP))
    {
        return -1;
    }
    *out = recs;
    *count = n;
    return 0;
}

// The record for `loot`, re-validating the one cached from phase 0 first: the client can realloc the array,
// which moves the base but never reorders it, so an index that still validates is the record.
// Runs on the client's drain thread (through the paid hook), so a disagreement is COUNTED here and logged by our
// own thread - this function never opens the log.
static int pxp_record_for(HMODULE client, unsigned loot, int cached, long long *xp)
{
    unsigned char *recs = NULL;
    int n = 0;
    if (pxp_records(client, &recs, &n) != 0)
    {
        return -1;
    }
    int kind = 0;
    int idx = -1;
    if (cached >= 0 && cached < n)
    {
        const unsigned char *rec = recs + (size_t)cached * MASTER_STRIDE;
        if (*(const unsigned *)(rec + PXP_REC_OWNER) == loot && *(const int *)(rec + PXP_REC_KIND) == PXP_KIND_WEAPON)
        {
            idx = cached;
        }
    }
    if (idx < 0)
    {
        idx = pxp_find_record(recs, n, loot, &kind);
        if (idx < 0)
        {
            if (kind != 0 && InterlockedCompareExchange(&PXP_KIND_SEEN, kind, 0) == 0)
            {
                // not a latch, and not a write: a launch that disagrees with the record's own filter says so
                // once, from the thread that may open the log
                PXP_KIND_LOOT = loot;
                PXP_KIND_ROWS = n;
            }
            return -1;
        }
    }
    *xp = pxp_record_xp(recs + (size_t)idx * MASTER_STRIDE);
    return idx;
}

// caller holds PXP_LOCK
static void pxp_write_locked(const char *text)
{
    if (PXP_DVAR == NULL || PXP_SLOT < 0)
    {
        return;
    }
    int bank = PXP_BANK ^ 1;
    strncpy_s(PXP_BANK_TEXT[bank], PXP_TEXT_MAX, text, _TRUNCATE);
    *(char **)((BYTE *)PXP_DVAR + PXP_SLOT) = PXP_BANK_TEXT[bank];
    PXP_BANK = bank;
    InterlockedIncrement(&PXP_PUBLISHES);
}

// The nativepay seam: phase 0 = the award is about to run, phase 1 = it returned. Runs on the client's drain
// thread, so: no logging, no file, no allocation. A failure here must never affect the payment.
void pubxp_on_paid(unsigned int loot, int amount, int phase)
{
    if (phase == 0)
    {
        PXP_PEND_OK = 0;
        PXP_PEND_REC = -1;
        PXP_PEND_LOOT = loot;
        PXP_PEND_BEFORE = 0;
        if (loot == 0 || PXP_OFF)
        {
            return;
        }
        HMODULE client = GetModuleHandleW(L"XINPUT9_1_0.dll");
        if (client == NULL)
        {
            return;
        }
        long long xp = 0;
        int idx = pxp_record_for(client, loot, -1, &xp);
        if (idx < 0)
        {
            return;
        }
        PXP_PEND_OK = 1;
        PXP_PEND_REC = idx;
        PXP_PEND_BEFORE = xp;
        return;
    }

    if (loot == 0)
    {
        return;
    }
    // THE PUBLISH GATE'S TRIGGER. This is the tail of a paid `ev=95`, so the client's record has moved: one
    // interlocked store asks the publish thread for a snapshot. Before the two branches below that end this
    // call early, because the snapshot must not depend on this channel's own health. Still no log, no file and
    // no client lock on this thread.
    pub_want(&PUB);
    if (loot != PXP_PEND_LOOT || PXP_OFF)
    {
        return;
    }
    InterlockedIncrement(&PXP_PAYMENTS);
    if (!PXP_ARMED)
    {
        InterlockedExchange(&PXP_NOARM, 1);
        return;
    }
    if (!PXP_PEND_OK)
    {
        InterlockedExchange(&PXP_NOREC, 1); // the record was not found; our own thread logs it once
        return;
    }
    HMODULE client = GetModuleHandleW(L"XINPUT9_1_0.dll");
    long long after = PXP_PEND_BEFORE;
    if (client != NULL)
    {
        long long now = PXP_PEND_BEFORE;
        if (pxp_record_for(client, loot, PXP_PEND_REC, &now) < 0)
        {
            InterlockedExchange(&PXP_NOREC, 1);
            return;
        }
        after = now;
    }

    PXP_NOTE note;
    note.added = note.capped = note.mismatch = 0;
    AcquireSRWLockExclusive(&PXP_LOCK);
    int changed = pxp_note(&PXP_L, loot, PXP_PEND_BEFORE, after, amount, &note);
    if (changed)
    {
        pxp_write_locked(PXP_L.text);
        pxp_shown(&PXP_L);
    }
    ReleaseSRWLockExclusive(&PXP_LOCK);

    if (note.capped)
    {
        InterlockedExchange(&PXP_CAPPED, 1); // logged once by our own thread
    }
    if (note.mismatch)
    {
        PXP_BAD_LOOT = loot;
        PXP_BAD_PAID = amount;
        PXP_BAD_D = after - PXP_PEND_BEFORE;
        InterlockedIncrement(&PXP_MISMATCH);
    }
    // the self-check line's own record: `rec <before> -> <after> (d=…)` must equal the amount paid, and the line
    // announces itself if it ever does not. Printed by pxp_thread - never here.
    {
        LONG w = InterlockedIncrement(&PXP_RING_W) - 1;
        PXP_RING_BUF[w & (PXP_RING - 1)].loot = loot;
        PXP_RING_BUF[w & (PXP_RING - 1)].paid = amount;
        PXP_RING_BUF[w & (PXP_RING - 1)].before = PXP_PEND_BEFORE;
        PXP_RING_BUF[w & (PXP_RING - 1)].after = after;
    }
}

// `ev=109` (ae_on_rec): the match boundary. Called on the thread that saw the event line, so again: no logging.
// The reset is visible in the log as the publish it causes (`pubxp: published "v1;…:0;…"`), so nothing is flagged.
void pubxp_match_reset(void)
{
    // A match has started: from here the record scan may ask for a publish of its own (publish.c). Set first,
    // before the early return below, because the scan does not depend on this channel having armed. It is also
    // the only match-live signal this DLL gets with the stock `log_events 0`.
    pub_match_live(&PUB);
    if (PXP_OFF || !PXP_ARMED)
    {
        return;
    }
    AcquireSRWLockExclusive(&PXP_LOCK);
    int changed = pxp_reset_match(&PXP_L);
    if (changed)
    {
        pxp_write_locked(PXP_L.text);
        pxp_shown(&PXP_L);
    }
    ReleaseSRWLockExclusive(&PXP_LOCK);
}

static void pxp_latch(const char *why)
{
    ch_logf("pubxp: refused - %s; the %s channel is off for this session (payments continue)", why, PXP_DVAR_NAME);
    InterlockedExchange(&PXP_OFF, 1);
}

static int pxp_arm(HMODULE client)
{
    // ITS OWN GATE, and its own symbols. This channel reads the record array, the register-or-find pointer, the
    // hash salt and the two addresses with no pattern - so it is gated on exactly those and on nothing else. It
    // no longer inherits the payload channel's verdict: an image that fails one feature's checks cannot kill the
    // other (docs\RC1-VERSION-COUPLING.md 3, gap 2).
    frame_identify(client);
    const RS_TABLE *rs = rs_for(client);
    if (!rs_feature_ok(rs, RS_F_PUBXP))
    {
        char why[96];
        pxp_latch(frame_reason(why, sizeof(why), rs, RS_F_PUBXP));
        return 0;
    }

    void *rf = *(void **)((BYTE *)client + rs_rva(rs, RS_RFN));
    if (rf == NULL)
    {
        if (!PXP_SAID_WAIT)
        {
            PXP_SAID_WAIT = 1;
            ch_logf("pubxp: waiting - the engine has not resolved its register function yet (~15 s after boot); "
                    "retrying every 5 s");
        }
        return 0;
    }
    if (!g11_page_ok(rf) || memcmp(rf, G11_RFN_SIG, sizeof(G11_RFN_SIG)) != 0)
    {
        pxp_latch("the register function does not carry its 9-byte prologue");
        return 0;
    }
    const unsigned char *salt = (const unsigned char *)((BYTE *)client + rs_rva(rs, RS_SALT));
    if (!g11_page_ok(salt))
    {
        pxp_latch("the name-hash salt is not readable");
        return 0;
    }

    G11_REG reg = (G11_REG)rf;
    // the same name-hash self-test g11_arm makes: our hash of a dvar the client registered must find that dvar
    void *got = reg(g11_hash_name("zm_ch_ver", salt), G11_PROBE, 0, "pubxp hash self-test");
    void *want = *(void **)((BYTE *)client + rs_rva(rs, RS_CHVER));
    if (got == NULL || want == NULL || got != want)
    {
        pxp_latch("the name hash does not match the client's own zm_ch_ver");
        return 0;
    }
    long off = (long)*(int *)((BYTE *)client + rs_rva(rs, RS_SLOT));
    if (!g11_slot_ok(off))
    {
        pxp_latch("the string slot offset is outside 0..0xFF or not 8-aligned");
        return 0;
    }

    // Create-or-find through the client's own call, with g11's sentinel as the default (a dvar this call creates
    // is then indistinguishable from one the GSC made, which is exactly the state the canary expects). The value
    // is replaced by `probe` immediately after, so a create here still proves the channel.
    const char *names[1] = {PXP_DVAR_NAME};
    void *dvar[1] = {NULL};
    G11CREATE pass = g11_dvar_pass(reg, salt, names, 1, off, dvar);
    if (pass.usable != 1)
    {
        if (pass.reason == G11_D_NULL)
        {
            return 0; // waiting, as above: not a verdict on the client's state
        }
        pxp_latch(pass.reason == G11_D_SLOT ? "the dvar's value slot is not writable"
                                            : "the dvar did not read back as the one we would create");
        return 0;
    }

    PXP_DVAR = dvar[0];
    PXP_SLOT = off;
    PXP_ARMED = 1;
    ch_logf("pubxp: armed - %s at slot %ld, register 0x%08lX (created here where absent - no match needed)",
            PXP_DVAR_NAME, off, (unsigned long)((ULONG_PTR)rf & 0xFFFFFFFFu));

    // THE PROBE: the constant, before any payment, so the first launch proves the channel with no kills at all.
    // The ledger's text is set to it as well, so the publish log line and the change-only rule both start from
    // what is actually stored.
    AcquireSRWLockExclusive(&PXP_LOCK);
    strncpy_s(PXP_L.text, PXP_TEXT_MAX, PXP_PROBE, _TRUNCATE);
    pxp_write_locked(PXP_L.text);
    pxp_shown(&PXP_L);
    ReleaseSRWLockExclusive(&PXP_LOCK);
    ch_logf("pubxp: published \"%s\" - the channel's probe, before any payment", PXP_PROBE);
    return 1;
}

static DWORD WINAPI pxp_thread(LPVOID unused)
{
    (void)unused;
    ULONGLONG last_try = 0;
    int said_norec = 0;
    int said_noarm = 0;
    int said_capped = 0;
    for (;;)
    {
        Sleep(250);
        if (PXP_OFF)
        {
            continue;
        }
        HMODULE client = GetModuleHandleW(L"XINPUT9_1_0.dll");
        if (client == NULL)
        {
            continue;
        }
        if (!PXP_ARMED)
        {
            ULONGLONG now = GetTickCount64();
            if (last_try != 0 && now - last_try < 5000)
            {
                continue;
            }
            last_try = now;
            if (!pxp_arm(client))
            {
                continue;
            }
        }

        // the publish lines, rate-limited: this thread is the only one that opens the log for this channel
        LONG done = InterlockedCompareExchange(&PXP_PUBLISHES, 0, 0);
        if (done > 0)
        {
            static LONG logged = 0;
            while (logged < done)
            {
                logged++;
                if (logged <= 3 || (logged % PXP_LOG_EACH) == 0)
                {
                    char text[PXP_LOG_TEXT + 8];
                    AcquireSRWLockShared(&PXP_LOCK);
                    strncpy_s(text, sizeof(text), PXP_L.text, _TRUNCATE);
                    ReleaseSRWLockShared(&PXP_LOCK);
                    if (strlen(text) > PXP_LOG_TEXT)
                    {
                        text[PXP_LOG_TEXT] = '\0';
                        strcat_s(text, sizeof(text), "...");
                    }
                    ch_logf("pubxp: published \"%s\" (#%ld)", text, (long)logged);
                }
            }
        }
        // the per-payment self-check, from the ring the drain thread fills: `d` must equal the amount paid
        {
            LONG w = InterlockedCompareExchange(&PXP_RING_W, 0, 0);
            LONG r = InterlockedCompareExchange(&PXP_RING_R, 0, 0);
            if (w - r > PXP_RING)
            {
                r = w - PXP_RING; // this thread fell behind: drop the oldest rather than log a stale run
                InterlockedExchange(&PXP_RING_R, r);
            }
            while (r < w)
            {
                unsigned loot = PXP_RING_BUF[r & (PXP_RING - 1)].loot;
                int paid = PXP_RING_BUF[r & (PXP_RING - 1)].paid;
                long long before = PXP_RING_BUF[r & (PXP_RING - 1)].before;
                long long after = PXP_RING_BUF[r & (PXP_RING - 1)].after;
                r++;
                InterlockedExchange(&PXP_RING_R, r);
                LONG n = InterlockedIncrement(&PXP_SELFCHK);
                if (n <= 3 || (n % PXP_LOG_EACH) == 0)
                {
                    // 32-bit prints: a gun's stored XP is far below 2^31 (a full ladder is 4,539)
                    ch_logf("nativepay: paid loot=%u f45=%d rec %ld -> %ld (d=%d)%s", loot, paid, (long)before,
                            (long)after, (int)(after - before),
                            (after - before) == (long long)paid ? "" : "  <- the record did not move by the payment");
                }
            }
        }
        if (InterlockedExchange(&PXP_NOREC, 0) != 0 && !said_norec)
        {
            said_norec = 1;
            ch_logf("pubxp: note - a payment's record could not be read (not found, or the array moved); "
                    "that payment is paid but not published");
        }
        if (InterlockedExchange(&PXP_CAPPED, 0) != 0 && !said_capped)
        {
            said_capped = 1;
            ch_logf("pubxp: note - a loot id past the %d-gun cap is paid but not in the payload (dropped: %lu)",
                    PXP_MAX, PXP_L.dropped);
        }
        {
            LONG mis = InterlockedCompareExchange(&PXP_MISMATCH, 0, 0);
            if (mis > 0 && mis <= 3)
            {
                ch_logf("pubxp: note - the record moved by %d for loot %u, the payment was %d (mismatch %ld): the "
                        "client did not add the amount to that row (a completed tier, or another row)",
                        (int)PXP_BAD_D, PXP_BAD_LOOT, PXP_BAD_PAID, (long)mis);
            }
        }
        if (!said_noarm && PXP_NOARM)
        {
            said_noarm = 1;
            ch_logf("pubxp: note - a payment arrived before the channel armed; it is paid but not published");
        }
        {
            LONG kind = InterlockedCompareExchange(&PXP_KIND_SEEN, 0, 0);
            if (kind > 0)
            {
                InterlockedExchange(&PXP_KIND_SEEN, -1); // logged once
                ch_logf("pubxp: note - a record with owner %u lists ev=95 but its kind is %ld, not %d (%d rows): "
                        "not published",
                        PXP_KIND_LOOT, (long)kind, PXP_KIND_WEAPON, PXP_KIND_ROWS);
            }
        }
    }
}

// --- the forced publish: the client's own serialiser, called from here --------------------------------------
//
// `client + 0x962E0` is the client's own serialise-and-publish: it zeroes and fills the lock bitmap, writes every
// record as one `c` line, appends the gum lines, cuts the text into 96 chunks of at most 2,000 bytes and bumps the
// `%u:%d` serial last. The client calls it at a mode boundary, and the reader on the other side of the channel
// rebuilds only when the serial moves - so a row that advances mid-match stays a frozen number on screen. This
// block calls that same function on our own clock. Nothing else about it changes: the state, the chunking, the
// serial and the dvars are the client's, and no byte of the client's code is written.
//
// WHY THIS THREAD, AND WHY THAT IS SAFE. It is one of ours, never the client's award path or its file writer:
// entering the client's serialiser from inside its own write path would nest two of its locks in an order nobody
// has read. The serialiser takes the record lock itself, holds it across the record and bitmap build, releases it
// before the first dvar write, and raises on a recursive acquire - so a caller that holds nothing is exactly the
// caller it is written for. The shipped gate (publish.c) additionally verifies its 24-byte prologue before every
// single call and latches the feature off for the session on a mismatch.
//
// THE WANT HAS TWO SOURCES, and both are needed:
//   * a paid `ev=95` - `pubxp_on_paid`'s phase 1, on the client's drain thread, one interlocked store;
//   * the record scan below, because a camo tier, a daily or a weekly is credited by its own event (kills, medals,
//     counters), not by the weapon-XP payment, so those rows can move with no payment at all. The scan is a
//     fingerprint over every record's progress, status/level and prestige bytes, taken at most once per second and
//     only while a match is live; an unchanged record costs the scan and nothing else.
//
// THE COST. One publish stores ~191 KB of text into the client's 96 chunk dvars (its own budget is 192,000 B), so
// at the window's floor this is ~191 KB/s of dvar stores during a live match, and the reader re-parses that text
// once per new serial when a challenge screen is built. The frame cost of the call itself has not been measured.

static DWORD WINAPI publish_thread(LPVOID unused)
{
    (void)unused;
    if (pub_off_present(NULL))
    {
        InterlockedExchange(&PUB.off, 1);
        ch_logf("publish: disabled by file (%s)", "%TEMP%\\progression-tuning\\publish_off.txt");
        return 0;
    }
    ch_logf("publish: armed - the client's own serialiser at rva 0x962E0 on the pinned build (from the resolver on "
            "any other), its %d-byte prologue verified before every call, at most one call per %d ms (a paid ev=95 "
            "or a moved record asks for one), %s turns it off",
            PUB_SIG_LEN, PUB_MIN_MS, "%TEMP%\\progression-tuning\\publish_off.txt");

    const RS_TABLE *rs = NULL;
    int said_nopay = 0;

    for (;;)
    {
        Sleep(250);
        if (InterlockedCompareExchange(&PUB.off, 0, 0) != 0)
        {
            continue; // latched off: nothing is scanned and nothing is called
        }
        ULONGLONG now = GetTickCount64();
        HMODULE client = GetModuleHandleW(L"XINPUT9_1_0.dll");

        // THIS FEATURE'S OWN GATE. The serialiser is one pattern-found address now, so the gate is "does this
        // build carry it" - checked once, with one line - and not the image's hash. Everything else in this DLL
        // keeps running either way.
        if (client != NULL && rs == NULL)
        {
            frame_identify(client);
            rs = rs_for(client);
            if (!rs_feature_ok(rs, RS_F_PUBLISH))
            {
                char why[96];
                ch_logf("publish: refused - %s - off", frame_reason(why, sizeof(why), rs, RS_F_PUBLISH));
                InterlockedExchange(&PUB.off, 1);
                continue;
            }
        }
        // The bounds this frame owns: the module is loaded (above) and the 24 bytes are inside SizeOfImage. The
        // page itself is checked by publish.c's guard, which is the read that would fault.
        unsigned ofimage = (rs != NULL) ? rs->ofimage : 0;
        int inside = (client != NULL) && ofimage != 0 && (PUB_RVA + PUB_SIG_LEN) <= ofimage;
        const unsigned char *at = (client != NULL) ? (const unsigned char *)client + PUB_RVA : NULL;

        // the record scan: any row that moved, whoever moved it
        if (inside && pub_scan_due(&PUB, now))
        {
            unsigned char *recs = NULL;
            int n = 0;
            if (pxp_records(client, &recs, &n) == 0)
            {
                pub_note_fingerprint(&PUB, pub_fingerprint(recs, n));
            }
        }

        PUB_VERDICT v = pub_step(&PUB, now, inside ? at : NULL);
        if (v == PUB_COALESCED)
        {
            LONG s = InterlockedCompareExchange(&PUB.skip, 0, 0);
            if (s == 1 || (s % 60) == 0)
            {
                ch_logf("publish: coalesced (%ld so far, min %d ms)", (long)s, PUB_MIN_MS);
            }
        }
        else if (v == PUB_REFUSED)
        {
            if (client == NULL)
            {
                ch_logf("publish: the client module is not loaded - off");
            }
            else if (!inside)
            {
                ch_logf("publish: the client image is too small for rva 0x962e0 (SizeOfImage 0x%lX) - off",
                        (unsigned long)ofimage);
            }
            else
            {
                ch_logf("publish: the client build does not match rva 0x962e0 - refused, off");
            }
        }
        else if (v == PUB_CALL)
        {
            // the call itself: no lock of ours is held, and the client function takes its own
            ((void (*)(void))at)();
            LONG n = InterlockedCompareExchange(&PUB.done, 0, 0);
            if (n <= 3 || (n % PUB_LOG_EACH) == 0)
            {
                ch_logf("publish: challenge state re-published live (#%ld)", (long)n);
            }
            // One line so a reader of the log is not misled: with no payment hook there is no paid ev=95, so this
            // snapshot came from the record scan above and nothing is being paid (docs\RC1-VERSION-COUPLING.md 3,
            // gap 7).
            if (!nativepay_hook_live() && !said_nopay)
            {
                said_nopay = 1;
                ch_logf("publish: note - the payment hook is not installed this session, so no paid ev=95 exists; "
                        "this snapshot came from the record scan and no XP is being paid");
            }
        }
    }
}

// --- import-table patching (no inline hooks) -----------------------------------------------------
//
// The two CreateFile hooks exist only to catch the open of `players\ae_events.log` and keep its handle; every
// other open is passed through untouched.

static HANDLE WINAPI hook_create_file_w(LPCWSTR name, DWORD access, DWORD share, LPSECURITY_ATTRIBUTES sa,
                                        DWORD disp, DWORD flags, HANDLE tmpl)
{
    HANDLE h = real_create_file_w(name, access, share, sa, disp, flags, tmpl);
    if (ae_tail_is(name))
    {
        ae_adopt(h, access, "CreateFileW");
    }
    return h;
}

static HANDLE WINAPI hook_create_file_a(LPCSTR name, DWORD access, DWORD share, LPSECURITY_ATTRIBUTES sa,
                                        DWORD disp, DWORD flags, HANDLE tmpl)
{
    HANDLE h = real_create_file_a(name, access, share, sa, disp, flags, tmpl);
    if (ae_tail_is_a(name))
    {
        ae_adopt(h, access, "CreateFileA");
    }
    return h;
}

static int patch_one(FARPROC *slot, void *replacement, const char *what, const char *who)
{
    if (slot == NULL || *slot == (FARPROC)replacement)
    {
        return 0;
    }
    DWORD old = 0;
    if (!VirtualProtect(slot, sizeof(void *), PAGE_READWRITE, &old))
    {
        ch_logf("frame: refused - %s %s could not be made writable", who, what);
        return 0;
    }
    *slot = (FARPROC)replacement;
    VirtualProtect(slot, sizeof(void *), old, &old);
    return 1;
}

static int patch_module(HMODULE mod, const char *who)
{
    if (mod == NULL)
    {
        return 0;
    }
    BYTE *base = (BYTE *)mod;
    IMAGE_DOS_HEADER *dos = (IMAGE_DOS_HEADER *)base;
    if (dos->e_magic != IMAGE_DOS_SIGNATURE)
    {
        return 0;
    }
    IMAGE_NT_HEADERS *nt = (IMAGE_NT_HEADERS *)(base + dos->e_lfanew);
    if (nt->Signature != IMAGE_NT_SIGNATURE)
    {
        return 0;
    }
    IMAGE_DATA_DIRECTORY dir = nt->OptionalHeader.DataDirectory[IMAGE_DIRECTORY_ENTRY_IMPORT];
    if (dir.VirtualAddress == 0)
    {
        return 0;
    }

    int patched = 0;
    IMAGE_IMPORT_DESCRIPTOR *desc = (IMAGE_IMPORT_DESCRIPTOR *)(base + dir.VirtualAddress);
    for (; desc->Name != 0; desc++)
    {
        if (desc->OriginalFirstThunk == 0)
        {
            continue;
        }
        IMAGE_THUNK_DATA *int_thunk = (IMAGE_THUNK_DATA *)(base + desc->OriginalFirstThunk);
        IMAGE_THUNK_DATA *iat = (IMAGE_THUNK_DATA *)(base + desc->FirstThunk);
        for (; int_thunk->u1.AddressOfData != 0; int_thunk++, iat++)
        {
            if (IMAGE_SNAP_BY_ORDINAL(int_thunk->u1.Ordinal))
            {
                continue;
            }
            IMAGE_IMPORT_BY_NAME *by_name = (IMAGE_IMPORT_BY_NAME *)(base + int_thunk->u1.AddressOfData);
            const char *fn = (const char *)by_name->Name;
            void *repl = NULL;
            if (strcmp(fn, "CreateFileW") == 0)
                repl = (void *)hook_create_file_w;
            else if (strcmp(fn, "CreateFileA") == 0)
                repl = (void *)hook_create_file_a;
            else if (strcmp(fn, "WriteFile") == 0)
                repl = (void *)hook_write_file;
            else if (strcmp(fn, "WriteFileEx") == 0)
                repl = (void *)hook_write_file_ex;
            if (repl != NULL)
            {
                patched += patch_one((FARPROC *)&iat->u1.Function, repl, fn, who);
            }
        }
    }
    return patched;
}

// --- the ops check patch ---------------------------------------------------------------------------
//
// one byte at rva 0xe6c8e turns jne into jmp short
// so the client always takes its operators on path
// the 8 bytes before it are an identity check
// a different build is left untouched and says so

#define OPS_GUARD_RVA 0xe6c8cu
#define OPS_PATCH_RVA 0xe6c8eu

// the loader name record and load notification
typedef struct
{
    USHORT Length;
    USHORT MaximumLength;
    const wchar_t *Buffer;
} OPS_NAME;

typedef struct
{
    ULONG Flags;
    const OPS_NAME *FullDllName;
    const OPS_NAME *BaseDllName;
    PVOID DllBase;
    ULONG SizeOfImage;
} OPS_LOAD;

typedef LONG(NTAPI *ops_reg_fn)(ULONG, PVOID, PVOID, PVOID *);
typedef LONG(NTAPI *ops_unreg_fn)(PVOID);

static volatile LONG OPS_DONE = 0;
static PVOID OPS_COOKIE = NULL;
static ops_unreg_fn OPS_UNREG = NULL;

static int ops_is_client(const OPS_NAME *name)
{
    // the client module base name is 14 characters
    static const wchar_t want[] = L"XINPUT9_1_0.dll";
    if (name == NULL || name->Buffer == NULL)
    {
        return 0;
    }
    if (name->Length != (USHORT)(sizeof(want) - sizeof(wchar_t)))
    {
        return 0;
    }
    return _wcsnicmp(name->Buffer, want, 14) == 0;
}

// check the 8 bytes then write one byte
// how is notify or attach
static int ops_patch(HMODULE client, const char *how)
{
    static const BYTE want[8] = {0x85, 0xc0, 0x75, 0x30, 0x48, 0x8d, 0x54, 0x24};
    if (client == NULL)
    {
        return 0;
    }
    BYTE *base = (BYTE *)client;
    IMAGE_DOS_HEADER *dos = (IMAGE_DOS_HEADER *)base;
    if (dos->e_magic != IMAGE_DOS_SIGNATURE)
    {
        return 0;
    }
    IMAGE_NT_HEADERS *nt = (IMAGE_NT_HEADERS *)(base + dos->e_lfanew);
    if (nt->Signature != IMAGE_NT_SIGNATURE || nt->OptionalHeader.SizeOfImage <= OPS_PATCH_RVA)
    {
        return 0;
    }

    BYTE *b = base + OPS_GUARD_RVA;
    if (memcmp(b, want, sizeof(want)) != 0)
    {
        // nothing written and every other feature carries on
        ch_logf("opsfix: bytes differ - left alone (%02x %02x %02x %02x %02x %02x %02x %02x)", b[0], b[1],
                b[2], b[3], b[4], b[5], b[6], b[7]);
        return 0;
    }

    BYTE *at = base + OPS_PATCH_RVA;
    DWORD old = 0;
    if (!VirtualProtect(at, 1, PAGE_EXECUTE_READWRITE, &old))
    {
        ch_logf("opsfix: the page is not writable - left alone");
        return 0;
    }
    at[0] = 0xeb;
    {
        DWORD back = 0;
        VirtualProtect(at, 1, old, &back);
    }
    FlushInstructionCache(GetCurrentProcess(), at, 1);
    ch_logf("opsfix: patched jne->jmp at +0xe6c8e (%s)", how);
    return 1;
}

// runs under the loader lock before the init routine
// no loadlibrary no allocation at most one log line
// it fires for every load so filter first
// the done flag replaces build 27's unregister: LdrUnregisterDllNotification is not called from inside a
// notification callback any more, it is called from DllMain's DETACH (opsfix_stop below)
static VOID NTAPI ops_notify(ULONG reason, const OPS_LOAD *data, PVOID context)
{
    (void)context;
    if (reason != 1 || data == NULL)
    {
        return;
    }
    if (!ops_is_client(data->BaseDllName))
    {
        return;
    }
    if (InterlockedExchange(&OPS_DONE, 1) != 0)
    {
        // already patched, or being patched: every later notification is ignored
        return;
    }
    ops_patch((HMODULE)data->DllBase, "notify");
}

// called from dllmain attach before any of our threads
// register for the load or patch at once if present
void opsfix_start(void)
{
    HMODULE client = GetModuleHandleW(L"XINPUT9_1_0.dll");
    if (client != NULL)
    {
        InterlockedExchange(&OPS_DONE, 1);
        ops_patch(client, "attach");
        return;
    }
    {
        HMODULE ntdll = GetModuleHandleW(L"ntdll.dll");
        if (ntdll == NULL)
        {
            return;
        }
        ops_reg_fn reg = (ops_reg_fn)GetProcAddress(ntdll, "LdrRegisterDllNotification");
        OPS_UNREG = (ops_unreg_fn)GetProcAddress(ntdll, "LdrUnregisterDllNotification");
        if (reg == NULL || OPS_UNREG == NULL)
        {
            return;
        }
        {
            PVOID cookie = NULL;
            if (reg(0, (PVOID)ops_notify, NULL, &cookie) == 0)
            {
                OPS_COOKIE = cookie;
            }
        }
    }
}

// called from dllmain detach, after the frame has stopped
// the only place the loader notification is taken back off the list
void opsfix_stop(void)
{
    if (OPS_UNREG != NULL && OPS_COOKIE != NULL)
    {
        OPS_UNREG(OPS_COOKIE);
        OPS_COOKIE = NULL;
    }
}

// --- the frame's own thread, and the entry point -------------------------------------------------

static DWORD WINAPI probe_thread(LPVOID unused)
{
    (void)unused;
    HMODULE k32 = GetModuleHandleW(L"kernel32.dll");
    real_create_file_w = (fn_create_file_w)GetProcAddress(k32, "CreateFileW");
    real_create_file_a = (fn_create_file_a)GetProcAddress(k32, "CreateFileA");
    real_write_file = (fn_write_file)GetProcAddress(k32, "WriteFile");
    real_write_file_ex = (fn_write_file_ex)GetProcAddress(k32, "WriteFileEx");
    if (!real_create_file_w || !real_create_file_a || !real_write_file || !real_write_file_ex)
    {
        ch_logf("frame: refused - the kernel32 lookups failed, the reader is off");
        return 0;
    }

    for (int i = 0; i < 300; i++)
    {
        HMODULE client = GetModuleHandleW(L"XINPUT9_1_0.dll");
        if (client != NULL)
        {
            // The identification pass, first: one line about the image, and the resolver's verdict on the two
            // addresses that have no pattern. It is not a gate - every other address comes from this build.
            frame_identify(client);
            // The master-prestige hook is installed at the first moment the client module is visible (its own
            // threads have not started the 500 ms challenge worker, so the five call sites are almost certainly
            // idle). It refuses and logs on any signature mismatch, and nothing here depends on it.
            master_install(client);
            int n = patch_module(client, "client");
            int m = patch_module(GetModuleHandleW(NULL), "exe");
            ch_logf("frame: reader armed - %d client slot(s), %d exe slot(s) (CreateFileW/A, WriteFile, "
                    "WriteFileEx); ae_events.log ev=109 resets the published figures",
                    n, m);
            return 0;
        }
        Sleep(100);
    }
    ch_logf("frame: refused - the client module never appeared, the reader is off");
    return 0;
}

void ch_frame_start(void)
{
    // One mutex shared with nativepay.c's installer, so the two patch windows (master.c's five call sites and
    // nativepay's one) can never be inside their thread-freeze blocks at the same time. Created here, handed to
    // both, and never closed - it lives as long as the process.
    HANDLE gate = CreateMutexW(NULL, FALSE, NULL);
    if (gate != NULL)
    {
        master_set_install_gate(gate);
        nativepay_set_install_gate(gate);
    }
    // the publish seam: nativepay calls back into this file on the drain thread with phase 0 and 1 per payment.
    // Set BEFORE nativepay_start (DllMain's order), so no payment can ever arrive with no hook.
    nativepay_set_paid_hook(pubxp_on_paid);
    // and the match boundary: the same call site sees ev=109 before the client's `log_events` gate, which is the
    // only boundary signal that exists with the stock `log_events 0`.
    nativepay_set_match_reset_hook(pubxp_match_reset);
    // the publish gate's state, explicitly, before any thread can raise or honour a want
    pub_init(&PUB);

    HANDLE th = CreateThread(NULL, 0, probe_thread, NULL, 0, NULL);
    if (th != NULL)
    {
        CloseHandle(th);
    }
    HANDLE gh = CreateThread(NULL, 0, g11_thread, NULL, 0, NULL);
    if (gh != NULL)
    {
        CloseHandle(gh);
    }
    HANDLE xh = CreateThread(NULL, 0, pxp_thread, NULL, 0, NULL);
    if (xh != NULL)
    {
        CloseHandle(xh);
    }
    // the forced publish: started after the paid hook is set, so no payment can raise a want before the thread
    // that honours it exists (a want set early is kept, not lost).
    HANDLE bh = CreateThread(NULL, 0, publish_thread, NULL, 0, NULL);
    if (bh != NULL)
    {
        CloseHandle(bh);
    }
}
