// clienthook - master prestige: the weapon level derivation, hooked at its call sites.
//
// The client derives a weapon's level by counting how many of the record's own thresholds the stored XP has
// passed (client function at 0x180096680) and writes that byte at rec+0x56e - the only writer of that byte in
// the binary. It never reads the record's prestige byte rec+0x574, so at prestige 2 a gun re-earns its own
// 20..48 levels and stops: there is no master track.
//
// This file adds one: after the client's own pass, for a kind-398 record whose prestige byte is >= 2 and whose
// XP is past the record's last threshold, level = count + floor((xp - last) / step), capped at 250. Only the
// level byte is written; the status byte rec+0x56d is left at the client's own answer (3 in that band), which
// is what keeps the client from logging a bogus "tier done" and from paying a completion bonus.
//
// WHERE THE HOOK IS, AND WHY THERE. Patching the callee's prologue and replaying it from a relay leaves the
// client's own RUNTIME_FUNCTION for that function (prolog_size 0x11, ALLOC_SMALL 0x28, eight PUSH_NONVOL)
// describing a frame the patch has moved, and an unwinder cannot follow that - it crashed on every boot. So
// the function stays byte-identical and its five 5-byte E8 rel32 call sites are repointed at master_thunk, a
// normal compiled function with its own .pdata. Nothing else in the image references the function.
//
// The step is a setting, not a constant: %TEMP%\progression-tuning\master_step.txt, one integer, read once at
// install (the thunk does no file I/O - it runs on the client's own XP path). Absent or out of range = 1,800.
// The hook itself can be left off without a rebuild: if %TEMP%\progression-tuning\master_off.txt exists,
// master_install does nothing and logs "master: disabled by file". Same mechanism as nativepay's kill switch.

#ifndef MASTER_H
#define MASTER_H

#include <windows.h>

#define MASTER_PRESTIGE_MIN 2
#define MASTER_LEVEL_CAP 250
#define MASTER_THRESHOLDS_MAX 64        // the record's hard ceiling: field 5 starts at +0x15C = 0x5C + 64*4
#define MASTER_STEP_DEFAULT 1800        // flat, 1,800 XP a master level
#define MASTER_STEP_MIN 1
#define MASTER_STEP_MAX 1000000

// The client addresses this file uses, each one read off the client's own code. Nothing is guessed.
//
// Build 25: these are the MEASURED values, and the install no longer reads through them. Every address comes
// from resolve.c, which finds it in the client's own executable sections; the constants here are what the
// resolver compares its answer against (and logs when one moves), and what the offline drivers stage.
#define MASTER_RVA 0x96680              // the challenges tier function (613 B)
#define MASTER_PROLOGUE_LEN 17          // the prologue runs to the instruction boundary at 0x96691, not 0x96690:
                                        // 4883ec28 (sub rsp,0x28) is 4 bytes at 0x9668D..0x96690
#define MASTER_RESUME_RVA 0x96691       // the instruction boundary after that prologue, recorded only: nothing
                                        // jumps here - the function itself is never patched
#define MASTER_RECS_RVA 0x3DD288        // the record array pointer
#define MASTER_COUNT_RVA 0x3DD290       // its count
#define MASTER_STRIDE 0x578             // one record
#define MASTER_REC_NAME 0x0C            // the row's name, the client's own %s
#define MASTER_REC_KIND 0x08            // the record kind
#define MASTER_REC_COUNT 0x58           // thresholds count, filled by the client at 0x950d0
#define MASTER_REC_THR 0x5C             // uint[64] thresholds, filled by the client at 0x950d0
#define MASTER_REC_XP 0x560             // u64 stored XP
#define MASTER_REC_LEVEL 0x56E          // the level byte, written by the client's own pass
#define MASTER_REC_PRESTIGE 0x574       // the prestige byte
#define MASTER_KIND_WEAPON 0x18E        // kind 398: a weapon ladder row

// The five call sites, and the length of each patch. Scanning the client's .text for E8 rel32 to the function
// finds exactly these five and nothing else - no E9, no RIP-relative address, no absolute pointer, no
// mid-function .pdata entry - so a call-site hook cannot be bypassed. The install re-derives this list from
// the client's own .text at run time and refuses unless it matches exactly.
#define MASTER_SITE_COUNT 5
#define MASTER_SITE_LEN 5
extern const unsigned MASTER_SITE_RVA[MASTER_SITE_COUNT];

extern const unsigned char MASTER_PROLOGUE[MASTER_PROLOGUE_LEN];

// E8 rel32 -> client + MASTER_RVA, and a committed readable page under it. 1 = the site is the call we think
// it is. This is the per-site signature guard; a mismatch anywhere refuses the whole install.
int master_site_ok(const unsigned char *site, const unsigned char *client);
// The 5 bytes that repoint one site at target (E8 rel32), keeping the instruction the same length. Returns 0
// when target is not within rel32 reach of the site, so the caller must supply a trampoline instead.
int master_site_patch(unsigned char out[MASTER_SITE_LEN], const unsigned char *site, const void *target);
// 1 when the site already holds exactly that patch (the read-back check).
int master_site_is_patch(const unsigned char *site, const void *target);

// 1 when <tempdir>\progression-tuning\master_off.txt exists. tempdir NULL = the process's %TEMP%.
int master_off_present(const wchar_t *tempdir);

// The client's own walk, in the open: how many thresholds the XP has passed, with the client's two edge rules
// (stop at the first threshold above the XP, and a record with no thresholds reads 1 iff XP is non-zero).
// Total, so the test can check it against the client's shape at the band edges.
unsigned master_client_level(unsigned long long xp, int count, const unsigned *thr);

// The level to write for one record, or -1 when this build must not touch it (prestige < 2, a count outside
// 0..64, or a step below 1). In the band (xp > last) it is count + (xp - last)/step, capped at 250; below the
// band it is the client's own answer, which is what makes the two sides agree at the boundary and above it.
int master_level(unsigned long long xp, int count, const unsigned *thr, int prestige, int step);

// The setting: digits only, optional surrounding whitespace, 1..1,000,000; anything else is the default.
int master_step_parse(const char *text, int len);

// MASTER_PROLOGUE against the live bytes, and a committed readable page under them. Still the install's
// "is this the right function" guard - and now the only thing that touches those bytes.
int master_prologue_ok(const void *p);
// 0 = not installed (refused, or off by the kill switch), 1 = installed, -1 = refused with a log line.
// Idempotent: a second call returns the first verdict.
int master_install(HMODULE client);

// The mutex held across the five 5-byte stores, shared with nativepay.c's installer so the two
// thread-freeze windows cannot overlap. NULL (the offline drivers) = no gate.
void master_set_install_gate(void *mutex);

// The offline test's seam, and nothing else: the address of the compiled thunk, and a way to point it at a
// staged page instead of the client. master_bind_level_fn is never called by the install path - master_install
// sets the same static to client + MASTER_RVA.
void *master_thunk_address(void);
void master_bind_level_fn(void *fn);

#endif
