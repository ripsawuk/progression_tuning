// clienthook - the game's own XP events, read from the client's `players\ae_events.log` stream.
//
// WHY: every XP grant the game makes goes through its own rank script (`rank.gsc`), which sends one AE
// event `mp_addxp` carrying `value` (player XP after the game's own scaling), `weapon_xp` (weapon XP after
// the round override, the hourly reduction and the gametype multiplier) and `weapon_loot_id`. The client
// logs that event as `ev=95` with field 44 = weapon_loot_id and field 45 = weapon_xp, and field 45 is
// present on exactly the rows that carry 44. The player's XP is already paid from this event; the weapon
// store is not.
//
// One line of the stream: `<unix time>\tev=<n>\t<field>=<value>\t...\n`. A WriteFile may carry part of
// a line or several, so the accumulator below only hands over whole lines.
//
// No Windows calls here: the offline driver runs the same code over a copy of a real log.

#ifndef AEXP_H
#define AEXP_H

#include <stddef.h>

#define AE_ABSENT (-1LL)

typedef struct
{
    long long t;    // unix seconds, first column
    long ev;        // the event number after "ev="
    long long f0;   // ev=95: the score event's base
    long long f31;  // ev=95: player value after the game's scaling
    long long f44;  // ev=95: weapon_loot_id; ev=123: weapon loot id of the kill
    long long f45;  // ev=95: weapon_xp after the game's scaling
    long long f234; // ev=780: round number
} AE_REC;

typedef struct
{
    char line[2048];
    size_t n;
    int overflow; // the current line outgrew the buffer: it is dropped, not parsed half
} AE_ACC;

typedef void (*ae_cb)(const AE_REC *rec, void *ctx);

// Parse one line (no newline). Returns 1 for an event line, 0 for anything else.
int ae_parse_line(const char *s, size_t n, AE_REC *out);

// Feed raw bytes; `cb` runs once per complete event line, in order.
void ae_feed(AE_ACC *acc, const char *buf, size_t n, ae_cb cb, void *ctx);

#endif // AEXP_H
