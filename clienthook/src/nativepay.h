// clienthook - the native payment (the award repoint, the publish hook and the install gate). See nativepay.c's
// header for what those three are.
//
// One 5-byte call-site repoint, two ints held changed for the duration of one call. No prologue patch, no detour
// inside the award, no cfg access, no record walk. The award function itself is never written:
//
//   call site   0x930D3  e8 48 07 00 00        one of exactly two calls to the award function 0x93820
//   award       0x93820  untouched, 24-byte fingerprint = the install's first guard
//   amount      0x93E5D  `mov eax,[0x2775F4]` + `0x93E63 cmovne ecx,[0x2775F8]`
//   store       0x93DD9  `add [rdi+0x560],rax` - reached by the client, not by us
//
// Every constant here was read off the supported client, XINPUT9_1_0.dll 5,016,064 B,
// sha256 88a52103c5555b2760f1e7ad13a594e8ef0440f007b45a10bddc61dda234fcfb. Any other build is refused at attach.

#ifndef NATIVEPAY_H
#define NATIVEPAY_H

// --- the one supported client build -------------------------------------------------------------------
#define NP_CLIENT_SIZE 5016064u
#define NP_CLIENT_IMAGE_SIZE 0x9A1000u

// --- code addresses we verify (and the one we write) --------------------------------------------------
#define NP_AWARD_RVA 0x93820u
#define NP_AWARD_ENTRY_LEN 24
#define NP_SITE_RVA 0x930D3u
#define NP_SITE_LEN 5
#define NP_LOAD_A_RVA 0x93E5Du
#define NP_LOAD_A_LEN 6
#define NP_LOAD_B_RVA 0x93E63u
#define NP_LOAD_B_LEN 7

// --- the two ints the X-path addend reads -------------------------------------------------------------
#define NP_KILL_RVA 0x2775F4u
#define NP_CRIT_RVA 0x2775F8u
#define NP_FIELD45_MAX 100000

// --- the event record, as the client's own dispatch and award functions read it ------------------------
//   byte 0x00  u32  event id              (the first dword the award function is handed)
//   byte 0x04  i32  entry count           (the second dword)
//   byte 0x08  u16  entry id [i]          (2 bytes each, from byte 8)
//   byte 0x70  i64  entry value [i]       (8 bytes each, from byte 0x70)
#define NP_EVENT_XP_ID 0x5Fu    // ev=95, the weapon-XP event (mp_addxp)
#define NP_EVENT_MATCH_START 0x6Du // ev=109, the match boundary (the event `ae_events.log` prints as `ev=109`)
#define NP_EVENT_ARMORY_START 853u // ev=853, the menu's armory pick (armoryutils senduserevent)
#define NP_KEY_GAMEMODE 8       // iw9_gamemode, the first key the pick carries
#define NP_KEY_ACTIVATE_ID 74   // iw9_activate_id, the armory row the page showed
#define NP_FIELD_45 0x2Du       // the game's own per-kill weapon XP, crit included
#define NP_FIELD_44 0x2Cu       // the weapon (loot) id
#define NP_ENTRY_ID_OFF 0x08u
#define NP_ENTRY_VAL_OFF 0x70u
#define NP_ENTRY_MAX 64         // this wrapper's bound; the client's own parser holds 4
#define NP_RECORD_LEN 0x200     // the client advances the record pointer by 0x200 bytes

// --- the pure half (unit-tested by the offline driver) ------------------------------------------------
typedef struct
{
    unsigned int id;
    int n;
    int has45;
    int has44;
    long long f45;
    long long f44;
} np_event;

typedef unsigned long long (*np_fn)(const unsigned int *);

extern const char NP_CLIENT_SHA256[65];
extern const unsigned char NP_AWARD_ENTRY[NP_AWARD_ENTRY_LEN];
extern const unsigned char NP_SITE_BYTES[NP_SITE_LEN];
extern const unsigned char NP_LOAD_A_BYTES[NP_LOAD_A_LEN];
extern const unsigned char NP_LOAD_B_BYTES[NP_LOAD_B_LEN];

int np_decode(const unsigned int *ev, np_event *out);
int np_clamp45(long long v);
unsigned long long np_call(int *kill, int *crit, const unsigned int *ev, np_fn orig);
int np_format(char *out, int cap, const np_event *e, int kill_before, int crit_before);
int np_reach(const void *site, const void *target);
int np_site_patch(unsigned char out[NP_SITE_LEN], const void *site, const void *target);
void np_tramp_bytes(unsigned char out[12], unsigned long long target);
int np_u64(char *out, int cap, unsigned long long v);
void np_sha256_hex(const void *data, unsigned int len, char hex_out[65]);

// --- file-level verification (the build guard) -------------------------------------------------------
int np_hash_file(const wchar_t *path, unsigned long long *size_out, char hex_out[65]);
int np_verify_file(const wchar_t *path, char *why, int cap);
int np_verify_image(const unsigned char *base, char *why, int cap);

// --- the shipped half ---------------------------------------------------------------------------------
void nativepay_start(void);
void nativepay_stop(void);
void nativepay_set_log(void (*fn)(const char *line));
void nativepay_set_tempdir(const wchar_t *dir);
int nativepay_install(void *client, const wchar_t *client_path);
unsigned long long nativepay_call(const unsigned int *ev);
const void *nativepay_thunk_address(void);
int np_off_present(const wchar_t *tempdir);

// --- the seams, all optional (NULL = no reader attached, no gate, no boundary callback) ----------------
//
// The publish hook. Called on the same thread the award runs on, with the event's loot id (field 44, 0 when the
// event did not carry one), the amount that will be / was paid, and the phase:
//   0 = the award is about to run for this ev=95   (read the record's XP: it is this match's base)
//   1 = the award returned                        (read the record's XP again: publish the new total)
// It must be cheap and must not do file I/O - frame.c's implementation only touches memory.
typedef void (*np_paid_fn)(unsigned int loot, int amount, int phase);
void nativepay_set_paid_hook(np_paid_fn fn);
// The match-boundary hook: called once for each `ev=109` (NP_EVENT_MATCH_START) the wrapper sees, before that
// event is passed to the client's own function unchanged. The call site sits in the client's dispatch loop
// which runs for every event *before* the client's `log_events` gate, so this is the match boundary whether
// or not the client is writing `players\ae_events.log`. Runs on the client's drain thread, so the same rule as
// the paid hook applies: memory only, no file I/O.
typedef void (*np_reset_fn)(void);
void nativepay_set_match_reset_hook(np_reset_fn fn);
// The armory pay seam: called once for every event the client dispatches, AFTER the client's own function has
// returned and while its store lock is still held - the one place a payment can be made with the client's own
// award. It is handed the resolved award function and the two ints that award reads as its amount. Memory only,
// no file I/O: armory.c holds the pair for exactly one call and posts what it paid to the frame thread.
typedef void (*np_pay_fn)(np_fn orig, int *kill, int *crit);
void nativepay_set_pay_hook(np_pay_fn fn);
// An optional mutex held across the 5-byte store, shared with master.c's installer so the two thread-freeze
// windows cannot overlap. The DLL passes one HANDLE to this and to master_install; NULL is a no-op.
void nativepay_set_install_gate(void *mutex);

// 1 = the wrapper is installed and will see every event (the boundary included), 0 = it is not (the kill switch,
// a refusal, or not installed yet).
int nativepay_hook_live(void);

// --- seams for the offline driver only (the install path never calls these) -----------------------------
void nativepay_bind_for_test(int *kill, int *crit, np_fn orig);
void nativepay_reset_for_test(void);

#endif
