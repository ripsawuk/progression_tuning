// clienthook - the armory pick channel the dvar and the file behind it
//
// the mod Lua runs in the front end only and cannot open a file so the pick
// has to outlive the process through a dvar registered at boot
// this unit seeds pt_armory_ch from players\armory.txt beside the dll
// and writes the dvar line back to that file whenever it moves

#ifndef PICK_H
#define PICK_H

#include <stddef.h>

#include "g11.h"

// one ascii line of a=<rowid> and optionally ;q=<rowid,rowid,...> then ;u=<0|1>
#define PICK_NAME "pt_armory_ch"
#define PICK_MAX 1024
#define PICK_DEFAULT "a=0"
// the lua queue worst case is 76 ids so 128 is room over
#define PICK_Q_MAX 128

// 1 when s may be the channel text 1..PICK_MAX chars of [a-z0-9=;,]
int pick_valid(const char *s, size_t n);

// the row the queue and the unlock flag 1 = read
// q_n -1 for no q u 0 for no u
int pick_parse(const char *s, size_t n, int *a, int *q, int q_cap, int *q_n, int *u);
// a= then ;q= then ;u= into out 0 = built
int pick_build(char *out, size_t cap, int a, const int *q, int q_n, int u);

// the queue from a record array kind 368 rows first trigger 200001..200076
// returns how many ids were copied and nothing is read from the game here
int pick_queue_native(const unsigned char *recs, int n, int *q, int cap);
// 1 complete 0 still owed -1 not a row in this array
int pick_row_state(const unsigned char *recs, int n, int id);
// the first queued id that is not done and not complete
// 0 = none left a null array only skips done
int pick_next(const unsigned char *recs, int n, int done, const int *q, int q_n);

// the file this unit reads and writes <dll dir>players\armory.txt
// one line out of path 1 = a valid line in out 0 = no file -1 = rejected
int pick_read(const wchar_t *path, char *out, size_t cap, const char **why);
// line into path through path.tmp and a replace rename 0 = written
int pick_write(const wchar_t *path, const char *line);

// register or find the dvar with the file line or PICK_DEFAULT
void pick_arm(G11_REG reg, const unsigned char salt[16], long slot);
// once a second adopt the dvar line persist a change and serve an advance
void pick_tick(void);
// the detach flush one last write when the file lags
void pick_stop(void);
int pick_armed(void);
// the active row 0 = none safe to read from any thread
int pick_active(void);
// the unlock armory flag 1 = on safe from any thread
int pick_unlocked(void);
// how many ids were copied into out
int pick_queue(int *out, int cap);
// the pay only write a completed row id 0 = none
void pick_request_advance(int done_id);
// 1 when <tempdir>\progression-tuning\armory_off.txt exists
int pick_off_present(const wchar_t *tempdir);

#endif
