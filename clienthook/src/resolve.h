// clienthook - the resolver: every client address this DLL uses, found in the client's own executable sections
// at run time instead of assumed from one build.
//
// WHY. Every address in master.h, nativepay.h, publish.h and frame.c was measured in one client build
// (XINPUT9_1_0.dll 5,016,064 B, sha256 88a52103...). A client update moves them, and a fixed constant then
// either points at nothing or - worse - at something else. Each of these addresses is identifiable from the
// code around it: a byte pattern with the variable bytes wildcarded (a rel32 displacement, a slice of a
// prologue), unique in the client's executable sections, or reachable from one that is (a RIP-relative operand
// read out of a pattern-found instruction, or the `E8 rel32` callers of a pattern-found function).
//
// THE RULES.
//   * A pattern must match exactly once over the executable sections, or the symbol is unresolved. Two matches
//     is not a "probably": it is unresolved, because the wrong one is a crash.
//   * A derived address must land inside the image (rva < SizeOfImage) or the symbol is unresolved.
//   * 19 of the 21 addresses resolve this way. The other two - the `zm_ch_ver` dvar_t slot and the string-value
//     slot - have no proven-unique standalone pattern yet (docs\RC1-VERSION-COUPLING.md 2.1). They keep the
//     measured constant ONLY while the image is the known build, and the known build is identified by the same
//     three facts the release has always used: the file's size, its sha256, and SizeOfImage. The caller
//     establishes that (frame.c's identification pass, or the offline checker) and hands the verdict to
//     rs_set_known_build; this file does not guess it and does not hash 5 MB on every question.
//   * Nothing here refuses on its own. A symbol that moves is reported - `resolve: <sym> differs from the known
//     build` - because a different build is the point. A feature whose symbols are not all present turns
//     itself off with one line naming the first one missing; the other features carry on.
//
// WHAT THIS FILE IS NOT. It does not verify behaviour, only code shape: a pattern proves the bytes are the
// shape they were when it was measured, not that the client still does the same thing with them. Every feature
// still verifies what it touches (the award's 24 bytes, the sites' E8+rel32, the register function's 9-byte
// prologue, the dvar round trip), and those checks are what fail if the semantics moved.

#ifndef RESOLVE_H
#define RESOLVE_H

// The known build, the three facts the release has always been tied to (docs\RC1-VERSION-COUPLING.md 1.4).
#define RS_KNOWN_SIZE 5016064u
#define RS_KNOWN_OFIMAGE 0x9A1000u
#define RS_KNOWN_SHA "88a52103c5555b2760f1e7ad13a594e8ef0440f007b45a10bddc61dda234fcfb"

// Every address the DLL uses, in the order the notes table lists them.
typedef enum
{
    RS_AWARD = 0,      // nativepay: the client's XP award function (read, never written)
    RS_SITE,           // nativepay: the one `E8 rel32` call site it writes
    RS_LOAD_A,         // nativepay: `mov eax,[kill]`
    RS_LOAD_B,         // nativepay: `cmovne ecx,[crit]`
    RS_KILL,           // nativepay: the int holding the per-kill amount
    RS_CRIT,           // nativepay: the crit amount
    RS_PUB,            // publish: the serialise-and-publish, called from our thread
    RS_MASTER_FN,      // master: the tier/level derivation
    RS_MASTER_SITE0,   // master: the five `E8 rel32` callers of the above
    RS_MASTER_SITE1,
    RS_MASTER_SITE2,
    RS_MASTER_SITE3,
    RS_MASTER_SITE4,
    RS_RECS,           // the challenge-record array base pointer
    RS_COUNT,          // its record count
    RS_SERIAL,         // g11: the publish serial the client increments
    RS_BITMAP,         // g11: the pointer to the 32,768 B lock bitmap
    RS_RFN,            // g11/pubxp: the register-or-find function pointer slot
    RS_SALT,           // g11/pubxp: the 16-byte salt the client's name hash reads
    RS_CHVER,          // g11/pubxp: the `dvar_t*` of `zm_ch_ver` - no pattern, constant on the known build only
    RS_SLOT,           // g11/pubxp: the string-value offset - no pattern, constant on the known build only
    RS_SYM_COUNT
} RS_SYM;

// The 19 a pattern finds (or derives). RS_CHVER and RS_SLOT are the two that need the known build.
#define RS_PATTERN_SYMS 19

typedef struct
{
    unsigned rva[RS_SYM_COUNT]; // 0 = unresolved (no address this DLL uses is ever at rva 0)
    int known_build;            // set by the caller's identification pass: 1 the image is the known build
    volatile LONG reported;     // the summary has been logged for this table
    unsigned ofimage;           // SizeOfImage the scan read, for the caller's own bounds checks
} RS_TABLE;

// One scan of an RVA-mapped image. `image` must be readable for SizeOfImage bytes from its base (a loaded
// module, or a buffer laid out the same way). Fills t->rva[] and t->ofimage; known_build starts 0. Returns 1
// when the PE headers were usable (a 64-bit image with a section table inside them), 0 otherwise - and then
// every symbol is unresolved.
int rs_scan(const unsigned char *image, RS_TABLE *t);

// The scan of one image, cached: the same base gives the same table, so a feature that retries every 5 s does
// not rescan 1.36 MB of .text each time. NULL when the image's headers are unusable.
const RS_TABLE *rs_for(const void *image);

// The identification pass's verdict (frame.c computes it; the offline checker sets it itself). Only RS_CHVER
// and RS_SLOT depend on it.
void rs_set_known_build(int is_known);
int rs_known_build(void);

// The pattern table itself, for the offline checker: how many patterns, their names, and how many times one of
// them matches an image (0, 1, or 2 for "two or more"; -1 when the image's headers are unusable).
int rs_pattern_count(void);
const char *rs_pattern_name(int pattern);
int rs_pattern_hits(const unsigned char *image, int pattern, unsigned *rva);

// The measured values, the comparison baseline. These are NOT used to address anything; they exist so a moved
// symbol can be reported, and so the test can assert every resolved rva equals the one the constant held.
unsigned rs_known_rva(RS_SYM s);
const char *rs_sym_name(RS_SYM s);

unsigned rs_rva(const RS_TABLE *t, RS_SYM s); // 0 = unresolved
int rs_ok(const RS_TABLE *t, RS_SYM s);
int rs_resolved(const RS_TABLE *t);           // how many of the 21 are resolved

// The seven features, each owning the symbols it actually reads. A feature is on only when every one of its
// symbols is resolved; the first missing one is named in the refusal line.
typedef enum
{
    RS_F_NATIVEPAY = 0, // the award, its call site, the two addends and the two ints
    RS_F_PUBLISH,       // the serialiser
    RS_F_MASTER,        // the level function, its five call sites, the record array
    RS_F_G11,           // the payload channel's six data slots and its one function pointer
    RS_F_PUBXP,         // the paid-XP text: the dvar machinery and the record array
    RS_F_BOUNDARY,      // the record array alone - the match-live scan and the record lookup
    RS_F_G12,           // the reward set: the record array, the dvar machinery, nothing else
    RS_F_COUNT
} RS_FEATURE;

const char *rs_feature_name(RS_FEATURE f);
// The first symbol of `f` that is unresolved, or NULL when the feature is fully resolved.
const char *rs_feature_missing(const RS_TABLE *t, RS_FEATURE f);
int rs_feature_ok(const RS_TABLE *t, RS_FEATURE f);

// The one summary line - `resolve: <n>/21 symbols (all)`, or the unresolved ones by name - plus, per symbol,
// `resolve: <sym> differs from the known build` when it moved, and with %TEMP%\progression-tuning\
// resolve_debug.txt present, one line per symbol carrying both rvas. Logged once per table; safe to call from
// every thread (the reported flag is the latch).
void rs_report(const RS_TABLE *t);

#endif // RESOLVE_H
