// clienthook - g11: the attachment-lock payload channel (the pure half). See g11.h for the addresses.
//
// Nothing here reads or writes a client address, so the offline driver exercises all of it without the game:
// the encoder, the splitter, the header, the popcount, the client's name hash, the canary validator and the
// latch.

#include <windows.h>
#include <ctype.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "g11.h"

// --- the latch -------------------------------------------------------------------------------------

int g11_gate(G11GATE *g, int verdict, const char *reason)
{
    if (g == NULL)
    {
        return 0;
    }
    if (g->state == G11_REFUSE)
    {
        if (verdict == G11_REFUSE)
        {
            g->refusals++;
        }
        return 0;
    }
    if (verdict == G11_REFUSE)
    {
        g->state = G11_REFUSE;
        g->why = (reason != NULL) ? reason : "unspecified";
        return 0;
    }
    if (verdict == G11_OK)
    {
        g->state = G11_OK;
        return 1;
    }
    return 0; // G11_WAIT: no latch, a later OK still arms
}

// --- the encoding ----------------------------------------------------------------------------------

void g11_hex(const unsigned char *src, size_t n, char *out)
{
    static const char DIG[] = "0123456789abcdef";
    if (src == NULL || out == NULL)
    {
        return;
    }
    for (size_t i = 0; i < n; i++)
    {
        out[i * 2] = DIG[src[i] >> 4];
        out[i * 2 + 1] = DIG[src[i] & 0x0F];
    }
    out[n * 2] = '\0';
}

size_t g11_part_offset(int i)
{
    if (i < 0 || i >= G11_PARTS)
    {
        return G11_HEX;
    }
    return (size_t)i * G11_PART_CHARS;
}

size_t g11_part_chars(int i)
{
    if (i < 0 || i >= G11_PARTS)
    {
        return 0;
    }
    size_t off = (size_t)i * G11_PART_CHARS;
    return (G11_HEX - off < G11_PART_CHARS) ? (G11_HEX - off) : G11_PART_CHARS;
}

int g11_ver(char *out, size_t cap, unsigned serial, int parts, int hexchars)
{
    if (out == NULL || cap == 0)
    {
        return 0;
    }
    int n = _snprintf_s(out, cap, _TRUNCATE, "%u:%d:%d", serial, parts, hexchars);
    return (n > 0) ? n : 0;
}

int g11_count_ids(const char *hex, size_t chars)
{
    // popcount per hex character, built once: "0".."9" then "a".."f" (the encoder only ever writes those)
    static unsigned char POP[256];
    static int ready = 0;
    if (!ready)
    {
        for (int i = 0; i < 256; i++)
        {
            POP[i] = 0;
        }
        for (int i = 0; i < 10; i++)
        {
            unsigned char v = (unsigned char)i;
            POP['0' + i] = (unsigned char)((v & 1) + ((v >> 1) & 1) + ((v >> 2) & 1) + ((v >> 3) & 1));
        }
        for (int i = 0; i < 6; i++)
        {
            unsigned char v = (unsigned char)(10 + i);
            POP['a' + i] = (unsigned char)((v & 1) + ((v >> 1) & 1) + ((v >> 2) & 1) + ((v >> 3) & 1));
            POP['A' + i] = POP['a' + i];
        }
        ready = 1;
    }
    if (hex == NULL)
    {
        return 0;
    }
    int n = 0;
    for (size_t i = 0; i < chars; i++)
    {
        n += POP[(unsigned char)hex[i]];
    }
    return n;
}

// --- the create-and-validate pass -------------------------------------------------------------------
//
// The client registers its own challenge dvars exactly this way (its `zm_ch_state`, its `zm_ch_ver` and the 96
// `zm_ch_s%d`), and the call creates the dvar when it does not exist - that is the whole reason the hook can
// publish from the frontend with no match. Because the default we pass is the SENTINEL, the create and the
// find paths converge on the same value, so:
//   * mod's GSC first -> the call finds the dvar the GSC made, canary passes (the original behaviour);
//   * hook first      -> the call creates it holding the sentinel, the GSC's later setdvar sets the same text;
//   * second pass     -> every name already exists, nothing is created, nothing changes.
// The dvar_t layout is not touched here: `slot` is the string-value offset the client discovered for its own
// string dvars, and every check is the client's own.

G11CREATE g11_dvar_pass(G11_REG reg, const unsigned char salt[16], const char *const *names, int n, long slot,
                        void **out)
{
    G11CREATE r;
    r.usable = 0;
    r.bad = -1;
    r.reason = G11_D_OK;

    if (reg == NULL || names == NULL || n <= 0 || n > 256 || out == NULL)
    {
        r.bad = 0;
        r.reason = G11_D_NULL;
        return r;
    }
    for (int i = 0; i < n; i++)
    {
        void *d = reg(g11_hash_name(names[i], salt), G11_SENTINEL, 0, "g11 payload");
        if (d == NULL)
        {
            r.bad = i;
            r.reason = G11_D_NULL; // not resolved yet, or the engine refused: the caller waits, does not latch
            break;
        }
        char **value = (char **)((char *)d + slot);
        if (!g11_page_writable(value))
        {
            r.bad = i;
            r.reason = G11_D_SLOT;
            break;
        }
        if (!g11_sentinel_ok(*value, G11_SENTINEL))
        {
            r.bad = i;
            r.reason = G11_D_VALUE;
            break;
        }
        out[i] = d;
        r.usable++;
    }
    if (r.usable != n)
    {
        // A partial set is never written with: `1800968f0`'s own rule is "validate, then use", and one bad slot
        // in the middle would otherwise leave 33 slabs pointed at two different publishes.
        for (int i = 0; i < n; i++)
        {
            out[i] = NULL;
        }
    }
    return r;
}

// --- the client's name hash -------------------------------------------------------------------------

unsigned long long g11_hash_name(const char *name, const unsigned char salt[16])
{
    const unsigned long long MUL = 0x10000000233ULL;
    const unsigned long long SEED = 0xD86A3B09566EBAACULL;

    if (name == NULL || name[0] == '\0')
    {
        return 0;
    }
    unsigned long long h =
        ((unsigned long long)(unsigned char)tolower((unsigned char)name[0]) ^ SEED) * MUL;
    if (salt != NULL)
    {
        for (int i = 0; i < 16; i++)
        {
            h = (h ^ (unsigned long long)salt[i]) * MUL;
        }
    }
    for (const char *p = name + 1; *p != '\0'; p++)
    {
        h = (h ^ (unsigned long long)(unsigned char)tolower((unsigned char)*p)) * MUL;
    }
    return h;
}

// --- the page checks the client itself uses ---------------------------------------------------------

int g11_page_ok(const void *p)
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
    // The client's own rule: VirtualQuery succeeds, State == MEM_COMMIT, (Protect & 0x101) == 0 (no
    // PAGE_GUARD, no PAGE_NOACCESS).
    if (mbi.State != MEM_COMMIT)
    {
        return 0;
    }
    if ((mbi.Protect & (PAGE_GUARD | PAGE_NOACCESS)) != 0)
    {
        return 0;
    }
    return 1;
}

int g11_page_writable(const void *p)
{
    if (!g11_page_ok(p))
    {
        return 0;
    }
    MEMORY_BASIC_INFORMATION mbi;
    if (VirtualQuery(p, &mbi, sizeof(mbi)) == 0)
    {
        return 0;
    }
    const DWORD w = PAGE_READWRITE | PAGE_WRITECOPY | PAGE_EXECUTE_READWRITE | PAGE_EXECUTE_WRITECOPY;
    return (mbi.Protect & w) != 0;
}

int g11_sentinel_ok(const void *p, const char *expect)
{
    if (!g11_page_ok(p) || expect == NULL)
    {
        return 0;
    }
    return strcmp((const char *)p, expect) == 0;
}

int g11_slot_ok(long off)
{
    return off >= 0 && off < 0x100 && (off % 8) == 0;
}

// --- SHA-256 of a file, for the client-image gate ---------------------------------------------------

typedef LONG(WINAPI *fn_bcrypt_hash)(void *alg, unsigned char *secret, unsigned long cb_secret,
                                     unsigned char *input, unsigned long cb_input, unsigned char *out,
                                     unsigned long cb_out);
typedef LONG(WINAPI *fn_bcrypt_open)(void **alg, const wchar_t *id, const wchar_t *impl, unsigned long flags);
typedef LONG(WINAPI *fn_bcrypt_close)(void *alg);

int g11_sha256_file(const wchar_t *path, unsigned char out[32])
{
    if (path == NULL || out == NULL)
    {
        return -1;
    }
    HMODULE bc = LoadLibraryW(L"bcrypt.dll");
    if (bc == NULL)
    {
        return -1;
    }
    fn_bcrypt_open pOpen = (fn_bcrypt_open)(void *)GetProcAddress(bc, "BCryptOpenAlgorithmProvider");
    fn_bcrypt_hash pHash = (fn_bcrypt_hash)(void *)GetProcAddress(bc, "BCryptHash");
    fn_bcrypt_close pClose = (fn_bcrypt_close)(void *)GetProcAddress(bc, "BCryptCloseAlgorithmProvider");
    if (pOpen == NULL || pHash == NULL)
    {
        FreeLibrary(bc);
        return -1;
    }
    HANDLE f = CreateFileW(path, GENERIC_READ, FILE_SHARE_READ | FILE_SHARE_WRITE | FILE_SHARE_DELETE,
                           NULL, OPEN_EXISTING, FILE_ATTRIBUTE_NORMAL, NULL);
    if (f == INVALID_HANDLE_VALUE)
    {
        FreeLibrary(bc);
        return -1;
    }
    void *alg = NULL;
    if (pOpen(&alg, L"SHA256", NULL, 0) != 0 || alg == NULL)
    {
        CloseHandle(f);
        FreeLibrary(bc);
        return -1;
    }
    // The whole file in one BCryptHash needs it in memory; 5 MB is fine and this runs once per session.
    LARGE_INTEGER sz;
    if (!GetFileSizeEx(f, &sz) || sz.QuadPart <= 0 || sz.QuadPart > (LONGLONG)(64 * 1024 * 1024))
    {
        if (pClose != NULL)
        {
            pClose(alg);
        }
        CloseHandle(f);
        FreeLibrary(bc);
        return -1;
    }
    unsigned long len = (unsigned long)sz.QuadPart;
    unsigned char *buf = (unsigned char *)malloc(len);
    if (buf == NULL)
    {
        if (pClose != NULL)
        {
            pClose(alg);
        }
        CloseHandle(f);
        FreeLibrary(bc);
        return -1;
    }
    unsigned long got = 0;
    int rc = -1;
    while (got < len)
    {
        DWORD chunk = 0;
        if (!ReadFile(f, buf + got, len - got, &chunk, NULL) || chunk == 0)
        {
            break;
        }
        got += chunk;
    }
    if (got == len && pHash(alg, NULL, 0, buf, len, out, 32) == 0)
    {
        rc = 0;
    }
    free(buf);
    if (pClose != NULL)
    {
        pClose(alg);
    }
    CloseHandle(f);
    FreeLibrary(bc);
    return rc;
}

void g11_hex32(const unsigned char in[32], char out[65])
{
    g11_hex(in, 32, out);
}
