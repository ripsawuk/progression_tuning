// clienthook - g11: the attachment-lock payload channel (the pure half).
//
// The hook copies the client's live lock bitmap into 33 hex dvars that the mod `g11_locks` creates, so the
// menu can see every lock the client holds instead of only the 14,702 that fit in its 96 published chunks.
// Everything in THIS file is arithmetic and Windows page checks only - no client address is read here, so the
// offline driver can prove it without the game.
//
// What the numbers are:
//   * the bitmap is 32,768 B at `*(void**)(client+0x466CD8)`, ids 1..0x3FFFF, bit (id&31) of dword (id>>5);
//   * the payload is that bitmap as 65,536 lowercase hex chars, cut into 33 pieces of 2,000 - 2,000 is the
//     client's own chunk width, and sits inside the 2,047-char cap a Lua dvar read accepts;
//   * the name hash is the client's own (client+0xB8420): a first character, then a 16-byte salt read from
//     the client at rva 0x16ED38, then the rest, each `(h ^ c) * 0x10000000233`. Reproduced offline against
//     98 of the client's own constants (its `zm_ch_ver` and all 96 `zm_ch_s0..95`), which is what makes the
//     hash literals in the mod's Lua checkable without the game.

#ifndef G11_H
#define G11_H

#include <stddef.h>

#define G11_PARTS 33
#define G11_HEX 65536                      /* 2,000 x 32 + 1,536 */
#define G11_PART_CHARS 2000
#define G11_BITMAP_BYTES 32768             /* 8,192 dwords = ids 0..0x3FFFF */
#define G11_MAX_ID 0x3FFFF
#define G11_VER_CAP 32

// The mod's GSC writes this into every one of the 35 dvars it creates. The hook only ever writes when it
// reads it back, which is how "mod absent" and "hook present" cannot do anything at all.
#define G11_SENTINEL "g11"
// What the hook passes to the client's register-or-find as the default. Deliberately NOT the sentinel: if the
// dvar did not exist, the engine creates it with THIS text, the sentinel check then fails, and we stay quiet
// instead of firing on a dvar we made ourselves. The create pass below asks with the sentinel instead, so the
// same call registers a dvar the GSC made and creates one it did not.
#define G11_PROBE "g11n"

// The client's own register-or-find, `*(void**)(client+0x6C4280)` (resolved about 15 s into boot): hash, default
// text, flags, description -> dvar_t*. It creates the dvar with the default when it does not exist, which is
// what lets the hook publish from the frontend with no match.
typedef void *(*G11_REG)(unsigned long long hash, const char *def, int flags, const char *desc);

// Why a dvar in the create pass was not usable. NULL is not a failure of the client's state - it means the
// engine has not resolved its register function yet, so the caller waits and retries (the rule for a
// missing mod, kept); the other two are validation failures and latch the feature off for the session.
#define G11_D_OK 0
#define G11_D_NULL 1
#define G11_D_SLOT 2
#define G11_D_VALUE 3

typedef struct
{
    int usable;  // how many of the 35 were found or created and validated (0..G11_DVARS)
    int bad;     // index of the first unusable one, or -1
    int reason;  // G11_D_* for `bad` (G11_D_OK when usable == G11_DVARS)
} G11CREATE;

// The gate: 0 = waiting for the mod, 1 = armed, 2 = latched off for this session.
#define G11_WAIT 0
#define G11_OK 1
#define G11_REFUSE 2

typedef struct
{
    int state;              // G11_WAIT / G11_OK / G11_REFUSE
    const char *why;        // the first latch reason (never overwritten)
    int refusals;           // how many REFUSE verdicts arrived after the latch
} G11GATE;

// The latch, as a pure function: returns 1 when the caller may write, 0 when it must not.
//   G11_OK     -> armed, may write
//   G11_WAIT   -> not yet (the mod's GSC may not have run); no latch, so a later OK still arms
//   G11_REFUSE -> latched: reason kept from the first refusal, and no later verdict re-opens it
int g11_gate(G11GATE *g, int verdict, const char *reason);

// The create-and-validate pass over the payload dvars, through the client's own
// register-or-find. Every name is asked for with G11_SENTINEL as the default, so a dvar the hook creates itself
// reads back as ours and the same loop registers one the mod's GSC created a moment earlier - either order
// works, and a second pass creates nothing. All of them must be usable or nothing is: `out` is left NULL for
// every name unless `usable == n`, and `bad`/`reason` name the first that failed (`usable` then counts the ones
// that validated before it). `names` is the caller's list (`G11_NAMES` in frame.c, which the offline test
// checks against the mod's GSC).
G11CREATE g11_dvar_pass(G11_REG reg, const unsigned char salt[16], const char *const *names, int n, long slot,
                        void **out);

// 65,536 lowercase hex chars into `out` (which needs 2*n+1 bytes); no separator, no line breaks.
void g11_hex(const unsigned char *src, size_t n, char *out);
// Where part i starts in the hex string and how many chars it holds (2,000, or 1,536 for the last one).
size_t g11_part_offset(int i);
size_t g11_part_chars(int i);
// "<serial>:<parts>:<hexchars>", e.g. "17:33:65536" - the header the mod reads first and last.
int g11_ver(char *out, size_t cap, unsigned serial, int parts, int hexchars);
// How many ids the payload says are locked (popcount over the hex digits).
int g11_count_ids(const char *hex, size_t chars);

// The client's own name hash (client+0xB8420); `salt` is the 16 bytes at client rva 0x16ED38.
unsigned long long g11_hash_name(const char *name, const unsigned char salt[16]);

// VirtualQuery wrappers that answer the same questions the client asks before it trusts a slot
// (pointer non-null, query succeeds, State == MEM_COMMIT, (Protect & 0x101) == 0).
int g11_page_ok(const void *p);
int g11_page_writable(const void *p);
// `g11_page_ok(p)` and `strcmp(p, expect) == 0` - the canary shape, in one call.
int g11_sentinel_ok(const void *p, const char *expect);
// The string-value offset the client discovered for its own string dvars (0x27764C): 0..0xFF, 8-aligned.
int g11_slot_ok(long off);

// SHA-256 of a file (`bcrypt.dll` BCryptHash), 32 bytes out. 0 = computed, -1 = could not.
int g11_sha256_file(const wchar_t *path, unsigned char out[32]);
void g11_hex32(const unsigned char in[32], char out[65]);   // for the log line

#endif
