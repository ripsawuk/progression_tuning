// clienthook - the native payment. One 5-byte call-site repoint, two ints held changed for the duration of one
// call. No prologue patch, no detour inside the award, no cfg access, no record walk. The award function itself
// is never written.
//
// WHAT THIS FILE DOES, in one sentence: it repoints ONE 5-byte call at client rva 0x930D3 at the C function
// `nativepay_call`, which for the weapon-XP event (ev=95) holds the two ints the award's X branch reads
// (0x2775F4 = the event's field 45, 0x2775F8 = 0) for the duration of that one call and restores them afterwards,
// and which for every other event calls the client's own function untouched.
//
// Two seams, both outside the payment:
//   * `NP_PAID` - a function pointer the caller sets with nativepay_set_paid_hook(). Called with phase 0 just
//     before the award runs for an ev=95 (so the record's XP can be read as the match's base) and phase 1 just
//     after it returns (so the XP can be read back and published). frame.c's `pubxp` block installs it. NULL -
//     the offline test driver - means the payment behaves exactly as it did without a reader.
//   * `NP_RESET` - the match boundary: called once for each ev=109 (NP_EVENT_MATCH_START) and then the event is
//     passed through untouched. This is what makes the boundary reachable with the stock `log_events 0`, where the
//     client writes no `players\ae_events.log` at all: the award call is taken for every event, before the log
//     gate, and this wrapper is that call.
//   * `NP_GATE` - an optional mutex (nativepay_set_install_gate) held across the 5-byte store, so this installer
//     and master.c's five call sites can never be inside their thread-freeze windows at the same time. NULL means
//     no gate, which is what the offline test driver passes.
//
// The call site is inside the client's own event dispatch loop (one call per event, before the `log_events`
// gate), so this wrapper sees every event the client dispatches, logged or not.
//
// Every address below was read off the supported client and is re-checked at attach, byte for byte. Build 25 asks
// resolve.c where they are in the image it is handed, so a client update that keeps these four instructions keeps
// the payment; the measured values stay as the baseline the resolver reports against, and as the check that the
// build we know still resolves to exactly them.

#include <windows.h>
#include <tlhelp32.h>
#include <stdarg.h>
#include <stdio.h>
#include <string.h>

#include "nativepay.h"
#include "resolve.h"

// --- the one supported client build ---------------------------------------------------------------------
//
//   XINPUT9_1_0.dll   5,016,064 B
//   sha256            88a52103c5555b2760f1e7ad13a594e8ef0440f007b45a10bddc61dda234fcfb
//
// The four sites, read back from that file (file offset -> bytes):
//   0x93820  40 53 55 56 57 41 54 41 55 41 56 41 57 48 83 ec 38 8b 01 48 8d 2d c6 c7
//   0x930D3  e8 48 07 00 00        rel32 = 0x748 -> 0x93820
//   0x93E5D  8b 05 91 37 1e 00     rip-relative -> rva 0x2775F4
//   0x93E63  0f 45 0d 8e 37 1e 00  rip-relative -> rva 0x2775F8
const char NP_CLIENT_SHA256[65] = "88a52103c5555b2760f1e7ad13a594e8ef0440f007b45a10bddc61dda234fcfb";

const unsigned char NP_AWARD_ENTRY[NP_AWARD_ENTRY_LEN] = {
    0x40, 0x53, 0x55, 0x56, 0x57, 0x41, 0x54, 0x41, 0x55, 0x41, 0x56, 0x41, 0x57,
    0x48, 0x83, 0xEC, 0x38,                                     // sub rsp,0x38
    0x8B, 0x01,                                                 // mov eax,[rcx]   (the event id)
    0x48, 0x8D, 0x2D, 0xC6, 0xC7};                              // lea rbp,[rip-0x3839]

const unsigned char NP_SITE_BYTES[NP_SITE_LEN] = {0xE8, 0x48, 0x07, 0x00, 0x00};

const unsigned char NP_LOAD_A_BYTES[NP_LOAD_A_LEN] = {0x8B, 0x05, 0x91, 0x37, 0x1E, 0x00};

const unsigned char NP_LOAD_B_BYTES[NP_LOAD_B_LEN] = {0x0F, 0x45, 0x0D, 0x8E, 0x37, 0x1E, 0x00};

// =======================================================================================================
// 1. the log. Buffered: the game thread only ever memcpy()s into a static buffer, and a background thread
//    writes it to <dll dir>\clienthook.log every 500 ms. Nothing on the client's worker thread touches a file.
// =======================================================================================================

#define NP_BUFMAX 32768
#define NP_CAP_FIRST 3
#define NP_CAP_EVERY 20

static void (*NP_HOOK)(const char *) = NULL; // the offline test's seam: printf instead of the buffer
static char NP_DIR[MAX_PATH] = {0};          // the DLL's own directory, ASCII, with a trailing backslash
static wchar_t NP_TEMPDIR[MAX_PATH] = {0};   // override for np_off_present() (the test passes a scratch dir)
static np_paid_fn NP_PAID = NULL;            // the publish hook (NULL = no reader attached)
static np_reset_fn NP_RESET = NULL;          // the match-boundary hook (NULL = the boundary is not observed here)
static np_pay_fn NP_PAY = NULL;              // the armory pay seam (NULL = nothing pays from this wrapper)
static void *NP_GATE = NULL;                 // the mutex shared with master.c's installer

void nativepay_set_paid_hook(np_paid_fn fn)
{
    NP_PAID = fn;
}

void nativepay_set_match_reset_hook(np_reset_fn fn)
{
    NP_RESET = fn;
}

void nativepay_set_pay_hook(np_pay_fn fn)
{
    NP_PAY = fn;
}

void nativepay_set_install_gate(void *mutex)
{
    NP_GATE = mutex;
}

static char NP_BUF[NP_BUFMAX];
static int NP_BUFLEN = 0;
static volatile LONG NP_LOCK = 0;
static HANDLE NP_FILE = INVALID_HANDLE_VALUE;

static HANDLE NP_STOP = NULL;
static HANDLE NP_THREAD = NULL;
static volatile LONG NP_LINES = 0;        // every ev=95 that carried field 45 (emitted or capped)
static volatile LONG NP_SUPPRESSED = 0;   // those the cap dropped
static volatile LONG NP_BUSY = 0;         // one thread inside the altered window at a time
static volatile LONG NP_CONCURRENT_NOTE = 0;
static volatile LONG NP_CLOSING = 0;      // DllMain(DETACH) has taken over the final flush

static void np_lock(void)
{
    while (InterlockedCompareExchange(&NP_LOCK, 1, 0) != 0)
    {
        Sleep(0);
    }
}

static void np_unlock(void)
{
    InterlockedExchange(&NP_LOCK, 0);
}

static void np_open_file(void)
{
    if (NP_FILE != INVALID_HANDLE_VALUE || NP_DIR[0] == '\0')
    {
        return;
    }
    char path[MAX_PATH * 2];
    if (_snprintf_s(path, sizeof(path), _TRUNCATE, "%sclienthook.log", NP_DIR) < 0)
    {
        return;
    }
    // FILE_APPEND_DATA + share-all: proxy_main.c's own one-line writer and this buffer can both use the file.
    NP_FILE = CreateFileA(path, FILE_APPEND_DATA, FILE_SHARE_READ | FILE_SHARE_WRITE | FILE_SHARE_DELETE, NULL,
                          OPEN_ALWAYS, FILE_ATTRIBUTE_NORMAL, NULL);
}

// caller holds the lock
static void np_flush_locked(void)
{
    if (NP_BUFLEN <= 0)
    {
        return;
    }
    np_open_file();
    if (NP_FILE != INVALID_HANDLE_VALUE)
    {
        DWORD wrote = 0;
        WriteFile(NP_FILE, NP_BUF, (DWORD)NP_BUFLEN, &wrote, NULL);
    }
    NP_BUFLEN = 0;
}

static void np_flush(void)
{
    np_lock();
    np_flush_locked();
    np_unlock();
}

// caller holds the lock
static void np_push_locked(const char *text, int len)
{
    if (len <= 0)
    {
        return;
    }
    if (NP_BUFLEN + len > NP_BUFMAX)
    {
        np_flush_locked(); // the only path that can grow the buffer past one line: flush, then append
    }
    if (NP_BUFLEN + len <= NP_BUFMAX)
    {
        memcpy(NP_BUF + NP_BUFLEN, text, (size_t)len);
        NP_BUFLEN += len;
    }
}

static int np_stamp(char *line, int cap, const char *body)
{
    SYSTEMTIME st;
    if (line == NULL || cap <= 0)
    {
        return 0;
    }
    GetLocalTime(&st);
    // bounded (_snprintf_s + _TRUNCATE): this used to be wsprintfA, which has no bound at all
    int n = _snprintf_s(line, (size_t)cap, _TRUNCATE, "%02d:%02d:%02d  %s\r\n", (int)st.wHour, (int)st.wMinute,
                        (int)st.wSecond, body);
    if (n < 0)
    {
        // truncated: keep the CRLF inside the buffer and report the length that was stored
        n = (int)strlen(line);
        if (n >= 2)
        {
            line[n - 2] = '\r';
            line[n - 1] = '\n';
        }
    }
    return n;
}

// The one formatting entry point. The line prefix is the wall clock (the deliverable asks for "time" per event).
static void np_emit(const char *body)
{
    if (NP_HOOK != NULL)
    {
        NP_HOOK(body);
        return;
    }
    char line[704];
    int n = np_stamp(line, (int)sizeof(line), body);
    np_lock();
    np_push_locked(line, n);
    np_unlock();
}

static void np_logf(const char *fmt, ...)
{
    // bounded like proxy_main.c's ch_logf: _vsnprintf_s + _TRUNCATE cannot write past `body` and always
    // NUL-terminates, where wvsprintfA had no bound at all
    char body[512];
    va_list ap;
    va_start(ap, fmt);
    _vsnprintf_s(body, sizeof(body), _TRUNCATE, fmt, ap);
    va_end(ap);
    np_emit(body);
}

void nativepay_set_log(void (*fn)(const char *line))
{
    NP_HOOK = fn;
}

void nativepay_set_tempdir(const wchar_t *dir)
{
    if (dir == NULL)
    {
        NP_TEMPDIR[0] = L'\0';
        return;
    }
    lstrcpynW(NP_TEMPDIR, dir, MAX_PATH);
}

// =======================================================================================================
// 2. the pure half - no client address is read here, so the offline driver proves it directly
// =======================================================================================================

int np_u64(char *out, int cap, unsigned long long v)
{
    if (out == NULL || cap < 2)
    {
        return 0;
    }
    char tmp[24];
    int n = 0;
    do
    {
        tmp[n++] = (char)('0' + (int)(v % 10));
        v /= 10;
    } while (v != 0 && n < (int)sizeof(tmp));
    if (n + 1 > cap)
    {
        out[0] = '\0';
        return 0;
    }
    for (int i = 0; i < n; i++)
    {
        out[i] = tmp[n - 1 - i];
    }
    out[n] = '\0';
    return n;
}

// The event record, as the client's dispatch and award functions read it:
//   ev[0] = the event id, ev[1] = the entry count (dwords); entry i's id is a u16 at byte 8 + 2i and its value an
//   i64 at byte 0x70 + 8i. `np_decode` says "this is ev=95 and it carries field 45" or it says no, and the wrapper
//   then does what the client would have done.

int np_decode(const unsigned int *ev, np_event *out)
{
    if (ev == NULL || out == NULL)
    {
        return 0;
    }
    memset(out, 0, sizeof(*out));
    memcpy(&out->id, ev, 4);
    memcpy(&out->n, (const unsigned char *)ev + 4, 4);
    if (out->id != NP_EVENT_XP_ID)
    {
        return 0;
    }
    if (out->n < 0 || out->n > NP_ENTRY_MAX)
    {
        return 0;
    }
    // The record is 0x200 bytes; a count whose values would run past it is not a record this wrapper will read.
    // The client's own parser holds 4 ids, so this never fires in practice.
    if (NP_ENTRY_VAL_OFF + (long long)out->n * 8 > NP_RECORD_LEN)
    {
        return 0;
    }
    for (int i = 0; i < out->n; i++)
    {
        unsigned short id = 0;
        long long v = 0;
        memcpy(&id, (const unsigned char *)ev + NP_ENTRY_ID_OFF + (size_t)i * 2, 2);
        memcpy(&v, (const unsigned char *)ev + NP_ENTRY_VAL_OFF + (size_t)i * 8, 8);
        if (id == NP_FIELD_45 && !out->has45)
        {
            out->has45 = 1;
            out->f45 = v;
        }
        else if (id == NP_FIELD_44 && !out->has44)
        {
            out->has44 = 1;
            out->f44 = v;
        }
    }
    return out->has45 ? 1 : 0;
}

// The amount is the event's own field 45, clamped. The client adds `kill + (crit bit ? crit : 0)` and skips the
// add when the sum is 0, so a clamp to 0 pays nothing rather than a negative amount.
int np_clamp45(long long v)
{
    if (v <= 0)
    {
        return 0;
    }
    if (v > NP_FIELD45_MAX)
    {
        return NP_FIELD45_MAX;
    }
    return (int)v;
}

// Save both globals, set them for one call, restore them whatever happens inside the client. __finally, not a
// trailing statement: a fault inside the award must not leave weapon_xp_kill altered for the rest of the session.
unsigned long long np_call(int *kill, int *crit, const unsigned int *ev, np_fn orig)
{
    np_event e;
    if (kill == NULL || crit == NULL || orig == NULL || !np_decode(ev, &e))
    {
        return orig != NULL ? orig(ev) : 0;
    }
    int k0 = *kill;
    int c0 = *crit;
    int amount = np_clamp45(e.f45);
    unsigned long long rv = 0;
    __try
    {
        *kill = amount;
        *crit = 0;
        rv = orig(ev);
    }
    __finally
    {
        *kill = k0;
        *crit = c0;
    }
    return rv;
}

// `nativepay: ev=95 loot=125186 f45=13 kill=20 crit=0 (paid 13)`, plus a note when the value had to be clamped.
int np_format(char *out, int cap, const np_event *e, int kill_before, int crit_before)
{
    if (out == NULL || cap <= 0 || e == NULL)
    {
        return 0;
    }
    int amount = np_clamp45(e->f45);
    // `cap` was declared and never used while this was wsprintfA (no bound); it is the real bound now
    int n = _snprintf_s(out, (size_t)cap, _TRUNCATE, "nativepay: ev=95 loot=%u f45=%d kill=%d crit=%d (paid %d)",
                        e->has44 ? (unsigned int)e->f44 : 0u, (int)(e->f45 & 0xFFFFFFFF), kill_before,
                        crit_before, amount);
    if (n < 0)
    {
        return (int)strlen(out);
    }
    if (amount != (int)e->f45)
    {
        int add = _snprintf_s(out + n, (size_t)cap - (size_t)n, _TRUNCATE, " [clamped from %d]",
                             (int)(e->f45 & 0xFFFFFFFF));
        n = add > 0 ? n + add : (int)strlen(out);
    }
    return n;
}

// `E8 rel32` reach, with 1 MB of headroom, the same rule master.c's installer uses.
#define NP_REACH_MAX 0x7FF00000LL

int np_reach(const void *site, const void *target)
{
    long long d = (long long)((const unsigned char *)target - ((const unsigned char *)site + NP_SITE_LEN));
    return (d >= -NP_REACH_MAX && d <= NP_REACH_MAX) ? 1 : 0;
}

int np_site_patch(unsigned char out[NP_SITE_LEN], const void *site, const void *target)
{
    if (out == NULL || site == NULL || target == NULL || !np_reach(site, target))
    {
        return 0;
    }
    long long d = (long long)((const unsigned char *)target - ((const unsigned char *)site + NP_SITE_LEN));
    int rel = (int)d;
    out[0] = 0xE8;
    memcpy(out + 1, &rel, 4);
    return 1;
}

// The trampoline, for when our DLL is more than 2 GB from the client image: `mov rax,<thunk>; jmp rax`. A pure
// leaf jump - it pushes nothing, keeps no frame and touches only rax, so it needs no unwind data.
void np_tramp_bytes(unsigned char out[12], unsigned long long target)
{
    if (out == NULL)
    {
        return;
    }
    out[0] = 0x48;
    out[1] = 0xB8;
    memcpy(out + 2, &target, 8);
    out[10] = 0xFF;
    out[11] = 0xE0;
}

// =======================================================================================================
// 3. SHA-256, so the build guard needs no third-party library and the test can hash the same file
// =======================================================================================================

typedef struct
{
    unsigned int h[8];
    unsigned long long len;
    unsigned char buf[64];
    int used;
} np_sha256;

static const unsigned int NP_K[64] = {
    0x428a2f98u, 0x71374491u, 0xb5c0fbcfu, 0xe9b5dba5u, 0x3956c25bu, 0x59f111f1u, 0x923f82a4u, 0xab1c5ed5u,
    0xd807aa98u, 0x12835b01u, 0x243185beu, 0x550c7dc3u, 0x72be5d74u, 0x80deb1feu, 0x9bdc06a7u, 0xc19bf174u,
    0xe49b69c1u, 0xefbe4786u, 0x0fc19dc6u, 0x240ca1ccu, 0x2de92c6fu, 0x4a7484aau, 0x5cb0a9dcu, 0x76f988dau,
    0x983e5152u, 0xa831c66du, 0xb00327c8u, 0xbf597fc7u, 0xc6e00bf3u, 0xd5a79147u, 0x06ca6351u, 0x14292967u,
    0x27b70a85u, 0x2e1b2138u, 0x4d2c6dfcu, 0x53380d13u, 0x650a7354u, 0x766a0abbu, 0x81c2c92eu, 0x92722c85u,
    0xa2bfe8a1u, 0xa81a664bu, 0xc24b8b70u, 0xc76c51a3u, 0xd192e819u, 0xd6990624u, 0xf40e3585u, 0x106aa070u,
    0x19a4c116u, 0x1e376c08u, 0x2748774cu, 0x34b0bcb5u, 0x391c0cb3u, 0x4ed8aa4au, 0x5b9cca4fu, 0x682e6ff3u,
    0x748f82eeu, 0x78a5636fu, 0x84c87814u, 0x8cc70208u, 0x90befffau, 0xa4506cebu, 0xbef9a3f7u, 0xc67178f2u};

#define NP_ROTR(x, n) (((x) >> (n)) | ((x) << (32 - (n))))

static void np_sha_block(np_sha256 *c, const unsigned char *p)
{
    unsigned int w[64];
    for (int i = 0; i < 16; i++)
    {
        w[i] = ((unsigned int)p[i * 4] << 24) | ((unsigned int)p[i * 4 + 1] << 16) |
               ((unsigned int)p[i * 4 + 2] << 8) | (unsigned int)p[i * 4 + 3];
    }
    for (int i = 16; i < 64; i++)
    {
        unsigned int s0 = NP_ROTR(w[i - 15], 7) ^ NP_ROTR(w[i - 15], 18) ^ (w[i - 15] >> 3);
        unsigned int s1 = NP_ROTR(w[i - 2], 17) ^ NP_ROTR(w[i - 2], 19) ^ (w[i - 2] >> 10);
        w[i] = w[i - 16] + s0 + w[i - 7] + s1;
    }
    unsigned int a = c->h[0], b = c->h[1], d = c->h[2], e = c->h[3];
    unsigned int f = c->h[4], g = c->h[5], h = c->h[6], k = c->h[7];
    for (int i = 0; i < 64; i++)
    {
        unsigned int s1 = NP_ROTR(f, 6) ^ NP_ROTR(f, 11) ^ NP_ROTR(f, 25);
        unsigned int ch = (f & g) ^ (~f & h);
        unsigned int t1 = k + s1 + ch + NP_K[i] + w[i];
        unsigned int s0 = NP_ROTR(a, 2) ^ NP_ROTR(a, 13) ^ NP_ROTR(a, 22);
        unsigned int maj = (a & b) ^ (a & d) ^ (b & d);
        unsigned int t2 = s0 + maj;
        k = h;
        h = g;
        g = f;
        f = e + t1;
        e = d;
        d = b;
        b = a;
        a = t1 + t2;
    }
    c->h[0] += a;
    c->h[1] += b;
    c->h[2] += d;
    c->h[3] += e;
    c->h[4] += f;
    c->h[5] += g;
    c->h[6] += h;
    c->h[7] += k;
}

static void np_sha_init(np_sha256 *c)
{
    c->h[0] = 0x6a09e667u;
    c->h[1] = 0xbb67ae85u;
    c->h[2] = 0x3c6ef372u;
    c->h[3] = 0xa54ff53au;
    c->h[4] = 0x510e527fu;
    c->h[5] = 0x9b05688cu;
    c->h[6] = 0x1f83d9abu;
    c->h[7] = 0x5be0cd19u;
    c->len = 0;
    c->used = 0;
}

static void np_sha_update(np_sha256 *c, const unsigned char *p, size_t n)
{
    c->len += (unsigned long long)n;
    while (n > 0)
    {
        size_t room = 64 - (size_t)c->used;
        size_t take = n < room ? n : room;
        memcpy(c->buf + c->used, p, take);
        c->used += (int)take;
        p += take;
        n -= take;
        if (c->used == 64)
        {
            np_sha_block(c, c->buf);
            c->used = 0;
        }
    }
}

static void np_sha_final(np_sha256 *c, unsigned char out[32])
{
    unsigned long long bits = c->len * 8;
    unsigned char pad = 0x80;
    np_sha_update(c, &pad, 1);
    unsigned char zero = 0;
    while (c->used != 56)
    {
        np_sha_update(c, &zero, 1);
    }
    unsigned char len[8];
    for (int i = 0; i < 8; i++)
    {
        len[i] = (unsigned char)(bits >> (56 - i * 8));
    }
    np_sha_update(c, len, 8);
    for (int i = 0; i < 8; i++)
    {
        out[i * 4] = (unsigned char)(c->h[i] >> 24);
        out[i * 4 + 1] = (unsigned char)(c->h[i] >> 16);
        out[i * 4 + 2] = (unsigned char)(c->h[i] >> 8);
        out[i * 4 + 3] = (unsigned char)c->h[i];
    }
}

static void np_hex(const unsigned char raw[32], char out[65])
{
    static const char DIGITS[] = "0123456789abcdef";
    for (int i = 0; i < 32; i++)
    {
        out[i * 2] = DIGITS[raw[i] >> 4];
        out[i * 2 + 1] = DIGITS[raw[i] & 0xF];
    }
    out[64] = '\0';
}

// A buffer's hash, so the offline test can check the implementation against known vectors.
void np_sha256_hex(const void *data, unsigned int len, char hex_out[65])
{
    np_sha256 c;
    np_sha_init(&c);
    if (data != NULL && len > 0)
    {
        np_sha_update(&c, (const unsigned char *)data, len);
    }
    unsigned char raw[32];
    np_sha_final(&c, raw);
    np_hex(raw, hex_out);
}

// Streams the file in 64 KB chunks: 5 MB at attach, ~20 ms, off the game thread.
int np_hash_file(const wchar_t *path, unsigned long long *size_out, char hex_out[65])
{
    if (path == NULL || hex_out == NULL)
    {
        return 0;
    }
    HANDLE f = CreateFileW(path, GENERIC_READ, FILE_SHARE_READ | FILE_SHARE_WRITE | FILE_SHARE_DELETE, NULL,
                           OPEN_EXISTING, FILE_ATTRIBUTE_NORMAL, NULL);
    if (f == INVALID_HANDLE_VALUE)
    {
        return 0;
    }
    np_sha256 c;
    np_sha_init(&c);
    unsigned char chunk[65536];
    unsigned long long total = 0;
    for (;;)
    {
        DWORD got = 0;
        if (!ReadFile(f, chunk, (DWORD)sizeof(chunk), &got, NULL))
        {
            CloseHandle(f);
            return 0;
        }
        if (got == 0)
        {
            break;
        }
        np_sha_update(&c, chunk, got);
        total += got;
    }
    CloseHandle(f);
    unsigned char raw[32];
    np_sha_final(&c, raw);
    np_hex(raw, hex_out);
    if (size_out != NULL)
    {
        *size_out = total;
    }
    return 1;
}

// =======================================================================================================
// 4. the build guard - three questions, all read-only, all before any write
// =======================================================================================================

int np_verify_file(const wchar_t *path, char *why, int cap)
{
    unsigned long long size = 0;
    char hex[65];
    if (!np_hash_file(path, &size, hex))
    {
        if (why != NULL)
        {
            _snprintf_s(why, (size_t)cap, _TRUNCATE, "the client file could not be read");
        }
        return 0;
    }
    if (size != (unsigned long long)NP_CLIENT_SIZE)
    {
        if (why != NULL)
        {
            _snprintf_s(why, (size_t)cap, _TRUNCATE, "the client file is %u B, the supported build is %u B",
                        (unsigned int)size, (unsigned int)NP_CLIENT_SIZE);
        }
        return 0;
    }
    if (lstrcmpiA(hex, NP_CLIENT_SHA256) != 0)
    {
        if (why != NULL)
        {
            _snprintf_s(why, (size_t)cap, _TRUNCATE, "the client file's sha256 is %s, the supported build is %s", hex,
                        NP_CLIENT_SHA256);
        }
        return 0;
    }
    return 1;
}

static int np_rip_target_ok(const unsigned char *at, int len, int disp_off, const unsigned char *base,
                            unsigned int want_rva)
{
    int disp = 0;
    memcpy(&disp, at + disp_off, 4);
    long long dst = (long long)((at + len + disp) - base);
    return dst == (long long)want_rva;
}

int np_verify_image(const unsigned char *base, char *why, int cap)
{
    if (base == NULL)
    {
        if (why != NULL)
        {
            _snprintf_s(why, (size_t)cap, _TRUNCATE, "the client module is not loaded");
        }
        return 0;
    }
    // PE headers: the image must be the same build, not just the same bytes at four addresses.
    const unsigned char *d = base;
    unsigned int lfanew = 0;
    memcpy(&lfanew, d + 0x3C, 4);
    if (d[0] != 'M' || d[1] != 'Z')
    {
        if (why != NULL)
        {
            _snprintf_s(why, (size_t)cap, _TRUNCATE, "the client module has no MZ header");
        }
        return 0;
    }
    const unsigned char *nt = d + lfanew;
    if (lfanew < 0x40 || lfanew > 0x1000 || nt[0] != 'P' || nt[1] != 'E' || nt[2] != 0 || nt[3] != 0)
    {
        if (why != NULL)
        {
            _snprintf_s(why, (size_t)cap, _TRUNCATE, "the client module has no PE header");
        }
        return 0;
    }
    unsigned int size_of_image = 0;
    memcpy(&size_of_image, nt + 24 + 56, 4);
    if (size_of_image != NP_CLIENT_IMAGE_SIZE)
    {
        if (why != NULL)
        {
            _snprintf_s(why, (size_t)cap, _TRUNCATE, "the client image is SizeOfImage 0x%X, the supported build is 0x%X",
                        size_of_image, (unsigned int)NP_CLIENT_IMAGE_SIZE);
        }
        return 0;
    }

    // (1) the award function's own bytes: the function the wrapper's premise was written against.
    if (memcmp(base + NP_AWARD_RVA, NP_AWARD_ENTRY, NP_AWARD_ENTRY_LEN) != 0)
    {
        if (why != NULL)
        {
            _snprintf_s(why, (size_t)cap, _TRUNCATE, "the award at 0x%X does not match the recorded %d bytes",
                        (unsigned int)NP_AWARD_RVA, NP_AWARD_ENTRY_LEN);
        }
        return 0;
    }

    // (2) the call site: `E8 rel32` and its rel32 really lands on the award.
    if (memcmp(base + NP_SITE_RVA, NP_SITE_BYTES, NP_SITE_LEN) != 0)
    {
        if (why != NULL)
        {
            _snprintf_s(why, (size_t)cap, _TRUNCATE, "the call site at 0x%X is not E8 48 07 00 00",
                        (unsigned int)NP_SITE_RVA);
        }
        return 0;
    }
    if (!np_rip_target_ok(base + NP_SITE_RVA, NP_SITE_LEN, 1, base, NP_AWARD_RVA))
    {
        // Belt and braces: the 5 bytes above already encode this rel32, so with the bytes matching this can only
        // fire if the image were mapped somewhere the rel32 does not point - it never is. Kept because a cheap
        // independent statement of "this call is the call we think it is" is worth more than the two lines.
        if (why != NULL)
        {
            _snprintf_s(why, (size_t)cap, _TRUNCATE, "the call at 0x%X does not resolve to 0x%X",
                        (unsigned int)NP_SITE_RVA, (unsigned int)NP_AWARD_RVA);
        }
        return 0;
    }

    // (3) the two addend loads: the bytes, and the globals they actually read.
    if (memcmp(base + NP_LOAD_A_RVA, NP_LOAD_A_BYTES, NP_LOAD_A_LEN) != 0)
    {
        if (why != NULL)
        {
            _snprintf_s(why, (size_t)cap, _TRUNCATE, "the load at 0x%X is not the recorded 6 bytes",
                        (unsigned int)NP_LOAD_A_RVA);
        }
        return 0;
    }
    if (!np_rip_target_ok(base + NP_LOAD_A_RVA, NP_LOAD_A_LEN, 2, base, NP_KILL_RVA))
    {
        if (why != NULL)
        {
            _snprintf_s(why, (size_t)cap, _TRUNCATE, "the load at 0x%X does not read 0x%X",
                        (unsigned int)NP_LOAD_A_RVA, (unsigned int)NP_KILL_RVA);
        }
        return 0;
    }
    if (memcmp(base + NP_LOAD_B_RVA, NP_LOAD_B_BYTES, NP_LOAD_B_LEN) != 0)
    {
        if (why != NULL)
        {
            _snprintf_s(why, (size_t)cap, _TRUNCATE, "the load at 0x%X is not the recorded 7 bytes",
                        (unsigned int)NP_LOAD_B_RVA);
        }
        return 0;
    }
    if (!np_rip_target_ok(base + NP_LOAD_B_RVA, NP_LOAD_B_LEN, 3, base, NP_CRIT_RVA))
    {
        if (why != NULL)
        {
            _snprintf_s(why, (size_t)cap, _TRUNCATE, "the load at 0x%X does not read 0x%X",
                        (unsigned int)NP_LOAD_B_RVA, (unsigned int)NP_CRIT_RVA);
        }
        return 0;
    }
    return 1;
}

// The same four facts np_verify_image states, at the addresses the resolver found instead of the measured ones.
// This is the path a client build we have never measured takes: the payment lives as long as the four
// instructions it actually touches are still there, which is what makes the release version-tolerant without
// giving up the byte-level guard. Every address is bounded by SizeOfImage before a byte of it is read.
static int np_verify_sites(const unsigned char *base, const RS_TABLE *rs, char *why, int cap)
{
    if (base == NULL || rs == NULL || rs->ofimage == 0)
    {
        if (why != NULL)
        {
            _snprintf_s(why, (size_t)cap, _TRUNCATE, "the client image could not be scanned");
        }
        return 0;
    }
    struct
    {
        RS_SYM sym;
        int len;
        const unsigned char *want;
        const char *what;
    } blk[] = {
        {RS_AWARD, NP_AWARD_ENTRY_LEN, NP_AWARD_ENTRY, "award function"},
        {RS_SITE, NP_SITE_LEN, NP_SITE_BYTES, "call site"},
        {RS_LOAD_A, NP_LOAD_A_LEN, NP_LOAD_A_BYTES, "addend load"},
        {RS_LOAD_B, NP_LOAD_B_LEN, NP_LOAD_B_BYTES, "addend load"},
    };
    for (int i = 0; i < (int)(sizeof(blk) / sizeof(blk[0])); i++)
    {
        unsigned rva = rs_rva(rs, blk[i].sym);
        if (rva == 0 || rva + (unsigned)blk[i].len > rs->ofimage)
        {
            if (why != NULL)
            {
                _snprintf_s(why, (size_t)cap, _TRUNCATE, "the %s at rva 0x%X does not fit the image",
                            blk[i].what, rva);
            }
            return 0;
        }
        if (memcmp(base + rva, blk[i].want, (size_t)blk[i].len) != 0)
        {
            if (why != NULL)
            {
                _snprintf_s(why, (size_t)cap, _TRUNCATE, "the %s at 0x%X does not match the recorded %d bytes",
                            blk[i].what, rva, blk[i].len);
            }
            return 0;
        }
    }
    if (!np_rip_target_ok(base + rs_rva(rs, RS_SITE), NP_SITE_LEN, 1, base, rs_rva(rs, RS_AWARD)))
    {
        if (why != NULL)
        {
            _snprintf_s(why, (size_t)cap, _TRUNCATE, "the call at 0x%X does not resolve to 0x%X",
                        rs_rva(rs, RS_SITE), rs_rva(rs, RS_AWARD));
        }
        return 0;
    }
    if (!np_rip_target_ok(base + rs_rva(rs, RS_LOAD_A), NP_LOAD_A_LEN, 2, base, rs_rva(rs, RS_KILL)))
    {
        if (why != NULL)
        {
            _snprintf_s(why, (size_t)cap, _TRUNCATE, "the load at 0x%X does not read 0x%X",
                        rs_rva(rs, RS_LOAD_A), rs_rva(rs, RS_KILL));
        }
        return 0;
    }
    if (!np_rip_target_ok(base + rs_rva(rs, RS_LOAD_B), NP_LOAD_B_LEN, 3, base, rs_rva(rs, RS_CRIT)))
    {
        if (why != NULL)
        {
            _snprintf_s(why, (size_t)cap, _TRUNCATE, "the load at 0x%X does not read 0x%X",
                        rs_rva(rs, RS_LOAD_B), rs_rva(rs, RS_CRIT));
        }
        return 0;
    }
    return 1;
}

// =======================================================================================================
// 5. the hook itself - one 5-byte `call`, with every other thread frozen across the store
// =======================================================================================================

#define NP_FREEZE_MAX 256

static np_fn NP_ORIG = NULL;         // client+0x93820 - read, never written
static int *NP_KILL = NULL;          // client+0x2775F4 - held changed for one call
static int *NP_CRIT = NULL;          // client+0x2775F8 - held at 0 for one call
static volatile LONG NP_STATE = 0;   // 0 untried, 1 hooked, 2 refused, 3 off by the kill switch
static int NP_FROZEN_LOG = 0;
static void *NP_TRAMP = NULL;

// 1 only while the wrapper is installed: the publish note in frame.c asks this, so a reader of the log is told
// that no paid ev=95 exists in this session.
int nativepay_hook_live(void)
{
    return InterlockedCompareExchange(&NP_STATE, 0, 0) == 1 ? 1 : 0;
}

int np_off_present(const wchar_t *tempdir)
{
    wchar_t dir[MAX_PATH];
    wchar_t path[MAX_PATH];
    if (tempdir == NULL)
    {
        if (NP_TEMPDIR[0] != L'\0')
        {
            tempdir = NP_TEMPDIR;
        }
        else
        {
            DWORD n = GetTempPathW(MAX_PATH, dir);
            if (n == 0 || n >= MAX_PATH)
            {
                return 0;
            }
            tempdir = dir;
        }
    }
    if (_snwprintf_s(path, MAX_PATH, _TRUNCATE, L"%sprogression-tuning\\nativepay_off.txt", tempdir) < 0)
    {
        return 0;
    }
    DWORD a = GetFileAttributesW(path);
    return (a != INVALID_FILE_ATTRIBUTES && a != 0xFFFFFFFFu) ? 1 : 0;
}

// --- thread freeze: a 5-byte store is not atomic, so no thread may be executing the site while it is written ---

static HANDLE NP_THREADS[NP_FREEZE_MAX];
static int NP_THREADS_N = 0;

static int np_threads_collect(void)
{
    NP_THREADS_N = 0;
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
            if (NP_THREADS_N >= NP_FREEZE_MAX)
            {
                break;
            }
            HANDLE h = OpenThread(THREAD_SUSPEND_RESUME, FALSE, te.th32ThreadID);
            if (h != NULL)
            {
                NP_THREADS[NP_THREADS_N++] = h;
            }
        } while (Thread32Next(snap, &te));
    }
    CloseHandle(snap);
    return NP_THREADS_N;
}

static int np_freeze(int *frozen, int cap)
{
    int n = 0;
    for (int i = 0; i < NP_THREADS_N; i++)
    {
        frozen[i] = 0;
        if (i < cap && SuspendThread(NP_THREADS[i]) != (DWORD)-1)
        {
            frozen[i] = 1;
            n++;
        }
    }
    return n;
}

static void np_thaw(const int *frozen)
{
    for (int i = 0; i < NP_THREADS_N; i++)
    {
        if (frozen[i])
        {
            ResumeThread(NP_THREADS[i]);
        }
        CloseHandle(NP_THREADS[i]);
    }
    NP_THREADS_N = 0;
}

static unsigned char *np_tramp_alloc(unsigned char *client, unsigned char *site, const void *thunk)
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
            if (np_reach(site, p))
            {
                unsigned char stub[12];
                np_tramp_bytes(stub, (unsigned long long)(ULONG_PTR)thunk);
                memcpy(p, stub, 12);
                FlushInstructionCache(GetCurrentProcess(), p, 12);
                return p;
            }
            VirtualFree(p, 0, MEM_RELEASE);
        }
    }
    return NULL;
}

// =======================================================================================================
// 6. the wrapper the call site is repointed at
// =======================================================================================================

// The client's own dispatch, untouched. Renamed so the wrapper below can run the armory pay after it returns:
// that is the only place a payment can be made with the client's own award, on the drain thread, lock held.
static unsigned long long np_call_inner(const unsigned int *ev)
{
    np_fn orig = NP_ORIG;
    if (orig == NULL)
    {
        return 0; // unreachable: the site is only patched after NP_ORIG is set
    }
    if (ev == NULL)
    {
        return orig(ev);
    }
    unsigned int id = 0;
    memcpy(&id, ev, 4);
    if (id != NP_EVENT_XP_ID)
    {
        // The match boundary. This call site is inside the client's own dispatch loop, which runs for every event
        // before the `log_events` gate, so ev=109 arrives here whether or not the client is writing
        // `players\ae_events.log`. The reset runs first; the event itself is then passed to the client's own
        // function untouched, exactly as shipped.
        if (id == NP_EVENT_MATCH_START)
        {
            np_reset_fn reset = NP_RESET;
            if (reset != NULL)
            {
                reset();
            }
        }
        return orig(ev); // every other event: the client's own function, untouched, exactly as shipped
    }
    np_event e;
    if (!np_decode(ev, &e))
    {
        return orig(ev); // ev=95 with no field 45: fall back to the cfg award, exactly as the client would
    }
    if (InterlockedCompareExchange(&NP_BUSY, 1, 0) != 0)
    {
        // Two threads inside the window at once would corrupt the pair. The client drains the queue on one
        // worker thread, so this cannot happen; if it ever does, pay nothing rather than lie.
        if (InterlockedCompareExchange(&NP_CONCURRENT_NOTE, 1, 0) == 0)
        {
            np_logf("nativepay: note - a second thread entered the window; passed through untouched");
        }
        return orig(ev);
    }

    int kill_before = *NP_KILL;
    int crit_before = *NP_CRIT;
    unsigned long long rv = 0;
    int completed = 0;
    // the publish hook. Phase 0 runs before the award (the record's XP is the match's base), phase 1 after it
    // returns - and after the pair is restored, so a fault in the hook cannot leave the ints altered.
    np_paid_fn paid = NP_PAID;
    unsigned int loot = e.has44 ? (unsigned int)e.f44 : 0u;
    int amount = np_clamp45(e.f45);
    __try
    {
        if (paid != NULL)
        {
            paid(loot, amount, 0);
        }
        rv = np_call(NP_KILL, NP_CRIT, ev, orig);
        completed = 1;
    }
    __finally
    {
        InterlockedExchange(&NP_BUSY, 0);
    }
    if (paid != NULL && completed)
    {
        paid(loot, amount, 1);
    }

    LONG n = InterlockedIncrement(&NP_LINES);
    if (completed)
    {
        if (n <= NP_CAP_FIRST || (n % NP_CAP_EVERY) == 0)
        {
            char body[256];
            np_format(body, (int)sizeof(body), &e, kill_before, crit_before);
            np_emit(body);
        }
        else
        {
            InterlockedIncrement(&NP_SUPPRESSED);
        }
        // The client must have put the pair back; if it did not, say so once.
        if (*NP_KILL != kill_before || *NP_CRIT != crit_before)
        {
            np_logf("nativepay: note - the pair read %d/%d after the call, expected the restored %d/%d", *NP_KILL,
                    *NP_CRIT, kill_before, crit_before);
        }
    }
    return rv;
}

// The wrapper the client's call site is repointed at. The client's own dispatch runs first and unchanged; the
// armory pay then runs once, after it returned and while the store lock is still held. A seam that pays nothing
// (NULL) costs one load and one branch, which is what every launch before this one does.
unsigned long long nativepay_call(const unsigned int *ev)
{
    unsigned long long rv = np_call_inner(ev);
    np_pay_fn pay = NP_PAY;
    if (pay != NULL)
    {
        pay(NP_ORIG, NP_KILL, NP_CRIT);
    }
    return rv;
}

const void *nativepay_thunk_address(void)
{
    return (const void *)&nativepay_call;
}

// =======================================================================================================
// 7. the installer
// =======================================================================================================

int nativepay_install(void *client, const wchar_t *client_path)
{
    if (InterlockedCompareExchange(&NP_STATE, 0, 0) == 1)
    {
        return 1;
    }
    unsigned char *base = (unsigned char *)client;
    char why[256];

    if (np_off_present(NULL))
    {
        np_logf("nativepay: disabled by file (%s)", "%TEMP%\\progression-tuning\\nativepay_off.txt");
        InterlockedExchange(&NP_STATE, 3);
        return 0;
    }
    if (base == NULL)
    {
        np_logf("nativepay: refused - the client module is not loaded");
        InterlockedExchange(&NP_STATE, 2);
        return -1;
    }

    // Where the four instructions are in THIS image, before anything is read through them. One symbol missing and
    // the payment is off with one line naming it; the level hook, the payload and the publish are not touched.
    const RS_TABLE *rs = rs_for(base);
    if (!rs_feature_ok(rs, RS_F_NATIVEPAY))
    {
        np_logf("nativepay: refused - %s in this client, so the award, its call site and the two addends cannot be "
                "found - off",
                rs_feature_missing(rs, RS_F_NATIVEPAY) != NULL ? rs_feature_missing(rs, RS_F_NATIVEPAY) : "an address");
        InterlockedExchange(&NP_STATE, 2);
        return -1;
    }
    unsigned award_rva = rs_rva(rs, RS_AWARD);
    unsigned site_rva = rs_rva(rs, RS_SITE);
    unsigned load_a_rva = rs_rva(rs, RS_LOAD_A);
    unsigned load_b_rva = rs_rva(rs, RS_LOAD_B);
    unsigned kill_rva = rs_rva(rs, RS_KILL);
    unsigned crit_rva = rs_rva(rs, RS_CRIT);

    // Guard 1, DEMOTED TO A LOG LINE. The file on disk is identified (size + sha256), and that verdict used to
    // refuse the payment even when the four instructions it touches were unchanged. Now it only decides which
    // image guard runs below: the measured one for the build we know, the resolved-sites one for anything else.
    int pinned_file = (client_path != NULL) && np_verify_file(client_path, why, (int)sizeof(why));
    char file_why[256];
    if (!pinned_file)
    {
        _snprintf_s(file_why, sizeof(file_why), _TRUNCATE, "%s",
                    (client_path == NULL) ? "the client path is not known" : why);
    }

    // Guard 2: the image. The pinned build must be the pinned build, byte for byte, exactly as before; any other
    // image is held to the four byte-blocks at the addresses the resolver found.
    if (pinned_file)
    {
        if (!np_verify_image(base, why, (int)sizeof(why)))
        {
            np_logf("nativepay: refused - %s", why);
            InterlockedExchange(&NP_STATE, 2);
            return -1;
        }
    }
    else if (!np_verify_sites(base, rs, why, (int)sizeof(why)))
    {
        np_logf("nativepay: refused - %s", why);
        InterlockedExchange(&NP_STATE, 2);
        return -1;
    }

    // Guard 3: the two ints must be writable, committed, 4-aligned.
    {
        int *kill = (int *)(base + kill_rva);
        int *crit = (int *)(base + crit_rva);
        MEMORY_BASIC_INFORMATION mbi;
        if ((((ULONG_PTR)kill) & 3) != 0 || (((ULONG_PTR)crit) & 3) != 0 || VirtualQuery(kill, &mbi, sizeof(mbi)) == 0 ||
            mbi.State != MEM_COMMIT || (mbi.Protect & (PAGE_READWRITE | PAGE_EXECUTE_READWRITE |
                                                       PAGE_WRITECOPY | PAGE_EXECUTE_WRITECOPY)) == 0)
        {
            np_logf("nativepay: refused - the pair at 0x%X/0x%X is not writable", kill_rva, crit_rva);
            InterlockedExchange(&NP_STATE, 2);
            return -1;
        }
        NP_KILL = kill;
        NP_CRIT = crit;
    }

    char hex[65];
    unsigned long long size = 0;
    np_hash_file(client_path, &size, hex);
    np_logf("nativepay: attach - XINPUT9_1_0.dll %u B sha256 %s; award 0x%X, call site 0x%X, addend loads "
            "0x%X/0x%X all verified",
            (unsigned int)size, hex, award_rva, site_rva, load_a_rva, load_b_rva);
    if (!pinned_file)
    {
        np_logf("nativepay: note - the client is not the pinned build (%s); the four sites were verified where this "
                "image carries them", file_why);
    }

    // From here the wrapper is live the moment the 5 bytes land, so bind everything it reads first.
    NP_ORIG = (np_fn)(void *)(base + award_rva);
    InterlockedExchange(&NP_STATE, 1);

    unsigned char *site = base + site_rva;
    const void *thunk = (const void *)&nativepay_call;
    void *target = (void *)thunk;
    if (!np_reach(site, thunk))
    {
        NP_TRAMP = np_tramp_alloc(base, site, thunk);
        if (NP_TRAMP == NULL)
        {
            np_logf("nativepay: refused - the wrapper is out of rel32 range and no trampoline could be allocated");
            NP_ORIG = NULL;
            InterlockedExchange(&NP_STATE, 2);
            return -1;
        }
        target = NP_TRAMP;
    }

    unsigned char patch[NP_SITE_LEN];
    unsigned char orig[NP_SITE_LEN];
    memcpy(orig, site, NP_SITE_LEN);
    if (!np_site_patch(patch, site, target))
    {
        np_logf("nativepay: refused - the wrapper is not within rel32 range of 0x%X", site_rva);
        NP_ORIG = NULL;
        InterlockedExchange(&NP_STATE, 2);
        return -1;
    }

    DWORD old_prot = 0;
    // The shared patch gate. master.c's installer freezes every other thread for its five stores; this
    // installer does the same for its one. Both take this mutex, so the two freeze windows can never overlap - a
    // thread suspended inside the other installer's window would otherwise be resumed at the wrong depth. Taken
    // BEFORE the page is made writable and released after the read-back, so the window holds no other kernel call
    // than the freeze/resume pair it always held.
    void *gate = NP_GATE;
    if (gate != NULL)
    {
        WaitForSingleObject((HANDLE)gate, 5000);
    }
    if (!VirtualProtect(site, NP_SITE_LEN, PAGE_EXECUTE_READWRITE, &old_prot))
    {
        np_logf("nativepay: refused - the call site at 0x%X is not writable (0x%lX)", site_rva,
                (unsigned long)GetLastError());
        NP_ORIG = NULL;
        InterlockedExchange(&NP_STATE, 2);
        if (gate != NULL)
        {
            ReleaseMutex((HANDLE)gate);
        }
        return -1;
    }

    // No kernel call inside the frozen window: the page is already writable above.
    int frozen[NP_FREEZE_MAX];
    int threads = np_threads_collect();
    int frozen_n = 0;
    if (threads > 0)
    {
        frozen_n = np_freeze(frozen, NP_FREEZE_MAX);
    }
    memcpy(site, patch, NP_SITE_LEN);
    if (threads > 0)
    {
        np_thaw(frozen);
    }
    FlushInstructionCache(GetCurrentProcess(), site, NP_SITE_LEN);

    // The read-back that matters: the 5 bytes are ours and their rel32 resolves to the target.
    int ok = 0;
    {
        int rel = 0;
        memcpy(&rel, site + 1, 4);
        ok = (memcmp(site, patch, NP_SITE_LEN) == 0) && ((void *)(site + NP_SITE_LEN + rel) == target);
    }
    if (!ok)
    {
        DWORD back = 0;
        VirtualProtect(site, NP_SITE_LEN, PAGE_EXECUTE_READWRITE, &back);
        memcpy(site, orig, NP_SITE_LEN);
        FlushInstructionCache(GetCurrentProcess(), site, NP_SITE_LEN);
        VirtualProtect(site, NP_SITE_LEN, old_prot, &back);
        NP_ORIG = NULL;
        InterlockedExchange(&NP_STATE, 2);
        if (gate != NULL)
        {
            ReleaseMutex((HANDLE)gate);
        }
        np_logf("nativepay: refused - the call site did not read back as our call; the original 5 bytes restored");
        return -1;
    }

    {
        DWORD back = 0;
        VirtualProtect(site, NP_SITE_LEN, old_prot, &back);
    }
    if (gate != NULL)
    {
        ReleaseMutex((HANDLE)gate);
    }
    NP_FROZEN_LOG = frozen_n;
    np_logf("nativepay: hook installed - 5 bytes at 0x%X: %02X %02X %02X %02X %02X -> %02X %02X %02X %02X %02X "
            "(call to nativepay_call via %s 0x%08lX%08lX), %d threads frozen",
            (unsigned int)site_rva, orig[0], orig[1], orig[2], orig[3], orig[4], site[0], site[1], site[2], site[3],
            site[4], (NP_TRAMP != NULL) ? "trampoline" : "rel32",
            (unsigned long)((ULONG_PTR)target >> 32), (unsigned long)((ULONG_PTR)target & 0xFFFFFFFFu),
            NP_FROZEN_LOG);
    np_logf("nativepay: ev=95 pays the game's field 45; every other event runs the client's own award unchanged; "
            "weapon_xp_kill/crit are restored after every call (cfg untouched)");
    return 1;
}

// =======================================================================================================
// 8. attach: wait for the client module, verify, install, then keep flushing the log
// =======================================================================================================

static void np_self_dir(void)
{
    HMODULE self = NULL;
    if (!GetModuleHandleExW(GET_MODULE_HANDLE_EX_FLAG_FROM_ADDRESS | GET_MODULE_HANDLE_EX_FLAG_UNCHANGED_REFCOUNT,
                            (LPCWSTR)&np_self_dir, &self))
    {
        return;
    }
    wchar_t path[MAX_PATH];
    DWORD n = GetModuleFileNameW(self, path, MAX_PATH);
    if (n == 0 || n >= MAX_PATH)
    {
        return;
    }
    wchar_t *slash = wcsrchr(path, L'\\');
    if (slash == NULL)
    {
        return;
    }
    *(slash + 1) = L'\0';
    if (WideCharToMultiByte(CP_ACP, 0, path, -1, NP_DIR, MAX_PATH, NULL, NULL) == 0)
    {
        NP_DIR[0] = '\0';
    }
}

static DWORD WINAPI np_thread_proc(LPVOID unused)
{
    (void)unused;

    // The client is not necessarily mapped when version.dll attaches; in practice attach and the client's
    // own boot pass land in the same second. 60 s is the margin.
    HMODULE client = NULL;
    for (int i = 0; i < 300; i++)
    {
        client = GetModuleHandleA("XINPUT9_1_0.dll");
        if (client != NULL)
        {
            break;
        }
        Sleep(200);
    }
    if (client == NULL)
    {
        np_logf("nativepay: refused - the client module XINPUT9_1_0.dll is not loaded after 60 s");
    }
    else
    {
        wchar_t path[MAX_PATH];
        DWORD n = GetModuleFileNameW(client, path, MAX_PATH);
        nativepay_install((void *)client, (n > 0 && n < MAX_PATH) ? path : NULL);
    }
    np_flush();

    // From here this thread is the log's writer: the game thread never waits on a disk.
    for (;;)
    {
        DWORD w = WaitForSingleObject(NP_STOP, 500);
        np_flush();
        if (w == WAIT_OBJECT_0)
        {
            break;
        }
    }
    if (InterlockedCompareExchange(&NP_CLOSING, 0, 0) == 0)
    {
        np_flush();
    }
    return 0;
}

void nativepay_start(void)
{
    np_self_dir();
    NP_STOP = CreateEventW(NULL, TRUE, FALSE, NULL);
    NP_THREAD = CreateThread(NULL, 0, np_thread_proc, NULL, 0, NULL);
}

// =======================================================================================================
// 9. seams for the offline driver. The install path never calls these: they bind the same statics the
//    installer binds, so the SHIPPED wrapper can be driven against a fabricated event record and fake ints.
// =======================================================================================================

void nativepay_bind_for_test(int *kill, int *crit, np_fn orig)
{
    NP_KILL = kill;
    NP_CRIT = crit;
    NP_ORIG = orig;
}

void nativepay_reset_for_test(void)
{
    InterlockedExchange(&NP_LINES, 0);
    InterlockedExchange(&NP_SUPPRESSED, 0);
    InterlockedExchange(&NP_BUSY, 0);
    InterlockedExchange(&NP_CONCURRENT_NOTE, 0);
    NP_PAY = NULL;
}

// Called from DllMain(DLL_PROCESS_DETACH). Bounded: at most ~20 ms, and it gives up rather than deadlock.
void nativepay_stop(void)
{
    if (NP_THREAD == NULL)
    {
        return;
    }
    InterlockedExchange(&NP_CLOSING, 1); // the writer thread will not write a second detach flush
    if (NP_STOP != NULL)
    {
        SetEvent(NP_STOP);
    }
    int tries = 0;
    while (InterlockedCompareExchange(&NP_LOCK, 1, 0) != 0 && tries < 20)
    {
        Sleep(1);
        tries++;
    }
    if (tries >= 20)
    {
        return; // the writer thread is mid-flush; the process is going away
    }
    np_flush_locked();
    if (NP_FILE != INVALID_HANDLE_VALUE)
    {
        CloseHandle(NP_FILE);
        NP_FILE = INVALID_HANDLE_VALUE;
    }
    np_unlock();
}
