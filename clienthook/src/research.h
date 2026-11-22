// the augment research channel and the pay behind it
//
// the game menu writes one dvar
// the hook mirrors it to one file
// the pay hands match operator xp
// to the row private trigger
// the credit is the row rise

#ifndef RESEARCH_H
#define RESEARCH_H

#include <stddef.h>

#include "g11.h"
#include "armory.h"
#include "nativepay.h"

// a= then a decimal achievement id a=0 is none
#define RESEARCH_NAME "pt_research_ch"
#define RESEARCH_MAX 32
#define RESEARCH_DEFAULT "a=0"

// the row numbers the pay reads
#define RES_REC_TRIG 0x480     // the first u32 trigger
#define RES_REC_TRIGS 0x490    // how many triggers the row carries
#define RES_KIND 437           // the augment research row kind
#define RES_TRIG_FIRST 200077  // the first private trigger of the 32 rows
#define RES_TRIG_LAST 200108   // and the last
#define RES_REC_MAX 20000      // a larger array is not the game challenge table
// one look a second at most
#define RES_PAY_MIN_MS 1000

// what one look decided
#define RES_PAY_NONE 0      // nothing owed
#define RES_PAY_DONE 1      // paid and the read back matched
#define RES_PAY_SHORT 2     // the row moved less than the amount held
#define RES_PAY_COMPLETE 3  // the row reads complete
#define RES_PAY_FAULT 4     // a fault latched the pay off for the process
#define RES_PAY_NOTE 5      // a second thread was inside the window
#define RES_PAY_PAUSE 6     // unlock augments came on so the pay stopped
#define RES_PAY_RESUME 7    // unlock augments went off so the pay runs again

// what one pay look is handed
typedef struct
{
    int active;                 // the research channel answer 0 = nothing picked
    int unlocked;               // 1 = unlock augments or unlock all on
    int off;                    // the pay kill switch
    const unsigned char *recs;  // the game record array
    int n;                      // how many records it holds
} res_pay_in;

// what one look decided and the read back
typedef struct
{
    int why;              // RES_PAY_*
    int id;               // the row looked at 0 = none
    long held;            // the amount put in the award global
    long got;             // the row own rise read back
    long long progress;   // the row xp after the call
    long long top;        // the row last threshold
} res_pay_result;

// the pay as this process knows it
typedef struct
{
    unsigned long long last_look; // the look clock
    int latched;                  // a fault latched the pay off
    int paused;                   // 1 while unlock augments is on
} res_pay_state;

// 1 when s may be the channel text
int res_valid(const char *s, size_t n);
// the id out of one line 1 = read
int res_parse(const char *s, size_t n, int *a);
// a= then the id into out 0 = built
int res_build(char *out, size_t cap, int a);

// one line out of path
int res_read(const wchar_t *path, char *out, size_t cap, const char **why);
// line into path through a tmp rename
int res_write(const wchar_t *path, const char *line);

// 1 when the row is one of ours
int res_row_ours(const unsigned char *row);

// one look the gates then the call
int res_pay_look(res_pay_state *ps, const res_pay_in *in, arm_state *st, unsigned long long now,
                 np_fn orig, int *kill, int *crit, res_pay_result *out);
// one result posted to the frame thread own log pass
void res_pay_post(const res_pay_result *r);
// the frame tick writes what the pay posted
void research_pay_log(void);
// the seam on the game drain thread
void research_pay(np_fn orig, int *kill, int *crit);
// a fault outside the award latches the pay
void research_pay_latch(void);

// register the dvar with the file line
void research_arm(G11_REG reg, const unsigned char salt[16], long slot);
// the frame tick adopt and persist
void research_tick(void);
// the detach flush one last write when the file lags
void research_stop(void);
int research_armed(void);
// the active row 0 = none
int research_active(void);
// 1 while either unlock dvar reads 1
int research_paused(void);
// 1 when <tempdir>\progression-tuning\research_pay_off.txt exists
int res_pay_off_present(const wchar_t *tempdir);

#endif
