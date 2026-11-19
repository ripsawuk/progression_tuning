// clienthook - tokens: the token channel's dvar and the file behind it.
//
// The mod's Lua and GSC only run at a level start, so a token activated in the front end has no dvar to write
// to. This registers `pt_tokens_ch` at boot, seeded from `players\tokens.txt` beside the DLL, and writes the
// dvar's value back to that file whenever it changes.

#ifndef TOKENS_H
#define TOKENS_H

#include <stddef.h>

#include "g11.h"

// one ASCII line: `p=<int>;w=<int>;n=<int>` and optionally `;c=<8 comma-separated ints>`
#define TOKENS_NAME "pt_tokens_ch"
#define TOKENS_MAX 512
#define TOKENS_DEFAULT "p=0;w=0;n=0"

// 1 when `s` may be the channel's text: 1..TOKENS_MAX chars of [a-z0-9=;,] and nothing else
int tokens_valid(const char *s, size_t n);

// the file this unit reads and writes: <dll dir>players\tokens.txt
// one line out of `path`: 1 = a valid line in `out`, 0 = no file, -1 = rejected (`*why` says why)
int tokens_read(const wchar_t *path, char *out, size_t cap, const char **why);
// `line` into `path` through `path.tmp` and a replace-rename: 0 = written, -1 = not
int tokens_write(const wchar_t *path, const char *line);

// register-or-find the dvar with the file's line (or TOKENS_DEFAULT); idempotent, and a no-op until it arms
void tokens_arm(G11_REG reg, const unsigned char salt[16], long slot);
// once a second: write the dvar's value to the file when it moved
void tokens_tick(void);
// the detach flush: one last write when the file lags the dvar
void tokens_stop(void);
int tokens_armed(void);

#endif
