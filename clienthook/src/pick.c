// clienthook - the armory pick channel and the file behind it
//
// the lua presses an item in the front end and the hook is the only side that can
// keep it so the pick lives in a dvar from boot and in one file of its own
// every field here is written by the frame 250 ms thread and by no other
// the payment thread may only read the active row or post an advance request

#include <windows.h>
#include <stdio.h>
#include <string.h>
#include <wchar.h>

#include "g11.h"
#include "master.h"
#include "resolve.h"
#include "pick.h"

void ch_logf(const char *fmt, ...);          // proxy_main.c
void ch_self_dir(wchar_t *out, DWORD cch);   // proxy_main.c

#define PK_SUBDIR L"players"
#define PK_FILE L"armory.txt"
#define PK_OLD L"pt_armory.txt"   // the name before build 38 read once as a seed
#define PK_TICK_MS 1000   // read the dvar at most this often
#define PK_LOG_MS 30000   // one saved line per this window after the first
#define PK_REC_MAX 20000  // a larger array is not the game challenge table
#define PK_REC_TRIG 0x480   // the row first u32 trigger
#define PK_REC_TRIGS 0x490  // how many triggers the row carries
#define PK_REC_STATUS 0x56D // the row status byte 3 = complete
#define PK_KIND_ARMORY 368  // the armory row kind
#define PK_TRIG_FIRST 200001 // the ladder own first private trigger
#define PK_TRIG_LAST 200076  // and the last of the 76 rows

static void *PK_DVAR;
static long PK_SLOT;
static int PK_ARMED;
static int PK_OFF;
static char PK_LINE[PICK_MAX + 1];    // the string the dvar points at today
static char PK_DISK[PICK_MAX + 1];    // what the file holds as far as this process knows
static volatile LONG PK_ADVANCE;      // a completed row id posted by the pay 0 = none
static volatile LONG PK_A;            // the active row
static volatile LONG PK_U;            // the unlock armory flag 1 = on
static int PK_Q[PICK_Q_MAX];
static int PK_QN;
static int PK_SAID_SAVE;
static int PK_SAID_BAD;
static int PK_SAID_QUEUE;
static int PK_SAID_DONE;
static ULONGLONG PK_LOG_AT;
static ULONGLONG PK_TICK_AT;

int pick_valid(const char *s, size_t n)
{
    if (s == NULL || n == 0 || n > PICK_MAX)
    {
        return 0;
    }
    for (size_t i = 0; i < n; i++)
    {
        char c = s[i];
        int ok = (c >= 'a' && c <= 'z') || (c >= '0' && c <= '9') || c == '=' || c == ';' || c == ',';
        if (!ok)
        {
            return 0;
        }
    }
    return 1;
}

// <dll dir>players\<file> the folder is never made here
static int pk_path_named(wchar_t *out, DWORD cch, const wchar_t *file)
{
    wchar_t base[MAX_PATH];
    ch_self_dir(base, MAX_PATH);
    if (base[0] == L'\0')
    {
        return 0;
    }
    return _snwprintf_s(out, cch, _TRUNCATE, L"%s" PK_SUBDIR L"\\%s", base, file) >= 0;
}

static int pk_path(wchar_t *out, DWORD cch)
{
    return pk_path_named(out, cch, PK_FILE);
}

// 1 when the client players folder is there a save into a missing folder is a skip
static int pk_folder(void)
{
    wchar_t base[MAX_PATH];
    wchar_t dir[MAX_PATH];
    ch_self_dir(base, MAX_PATH);
    if (base[0] == L'\0')
    {
        return 0;
    }
    if (_snwprintf_s(dir, MAX_PATH, _TRUNCATE, L"%s" PK_SUBDIR, base) < 0)
    {
        return 0;
    }
    DWORD a = GetFileAttributesW(dir);
    return (a != INVALID_FILE_ATTRIBUTES && (a & FILE_ATTRIBUTE_DIRECTORY) != 0) ? 1 : 0;
}

int pick_parse(const char *s, size_t n, int *a, int *q, int q_cap, int *q_n, int *u)
{
    if (s == NULL || a == NULL || q_n == NULL || u == NULL || n < 3 || !pick_valid(s, n))
    {
        return 0;
    }
    *a = 0;
    *q_n = -1;
    *u = 0;
    if (s[0] != 'a' || s[1] != '=')
    {
        return 0;
    }
    size_t i = 2;
    long long v = 0;
    size_t d = 0;
    while (i < n && s[i] >= '0' && s[i] <= '9')
    {
        v = v * 10 + (s[i] - '0');
        if (v > 2147483647LL)
        {
            return 0;
        }
        i++;
        d++;
    }
    if (d == 0)
    {
        return 0;
    }
    *a = (int)v;
    if (i == n)
    {
        return 1;
    }
    if (n - i < 3 || s[i] != ';')
    {
        return 0;
    }
    // u may follow the row or the queue
    if (s[i + 1] == 'u' && s[i + 2] == '=')
    {
        if (n - i != 4 || (s[i + 3] != '0' && s[i + 3] != '1'))
        {
            return 0;
        }
        *u = s[i + 3] - '0';
        return 1;
    }
    if (s[i + 1] != 'q' || s[i + 2] != '=')
    {
        return 0;
    }
    if (q == NULL || q_cap <= 0)
    {
        return 0;
    }
    i += 3;
    int cnt = 0;
    for (;;)
    {
        v = 0;
        d = 0;
        while (i < n && s[i] >= '0' && s[i] <= '9')
        {
            v = v * 10 + (s[i] - '0');
            if (v > 2147483647LL)
            {
                return 0;
            }
            i++;
            d++;
        }
        if (d == 0 || cnt >= q_cap)
        {
            return 0;
        }
        q[cnt++] = (int)v;
        if (i == n)
        {
            break;
        }
        if (s[i] == ',')
        {
            i++;
            continue;
        }
        if (s[i] != ';')
        {
            return 0;
        }
        break;
    }
    *q_n = cnt;
    if (i == n)
    {
        return 1;
    }
    i++;
    if (n - i != 3 || s[i] != 'u' || s[i + 1] != '=' || (s[i + 2] != '0' && s[i + 2] != '1'))
    {
        return 0;
    }
    *u = s[i + 2] - '0';
    return 1;
}

// one piece of the built line out is always terminated
static int pk_put(char *out, size_t cap, size_t *at, const char *text, size_t n)
{
    if (*at + n >= cap)
    {
        return -1;
    }
    memcpy(out + *at, text, n);
    *at += n;
    out[*at] = '\0';
    return 0;
}

// the digits of v in order 0 is one zero
static int pk_dec(char *out, int v)
{
    char rev[12];
    int n = 0;
    if (v < 0)
    {
        return 0;
    }
    do
    {
        rev[n++] = (char)('0' + (v % 10));
        v /= 10;
    } while (v != 0);
    for (int i = 0; i < n; i++)
    {
        out[i] = rev[n - 1 - i];
    }
    return n;
}

int pick_build(char *out, size_t cap, int a, const int *q, int q_n, int u)
{
    if (out == NULL || cap == 0 || a < 0 || q_n < 0 || (q_n > 0 && q == NULL))
    {
        return -1;
    }
    if (cap < 2)
    {
        return -1;
    }
    out[0] = '\0';
    size_t at = 0;
    char digits[12];
    int n = pk_dec(digits, a);
    if (pk_put(out, cap, &at, "a=", 2) != 0 || pk_put(out, cap, &at, digits, (size_t)n) != 0)
    {
        return -1;
    }
    if (q_n > 0)
    {
        if (pk_put(out, cap, &at, ";q=", 3) != 0)
        {
            return -1;
        }
        for (int i = 0; i < q_n; i++)
        {
            char piece[12];
            int len = pk_dec(piece, q[i]);
            if (len <= 0)
            {
                return -1;
            }
            if (i > 0 && pk_put(out, cap, &at, ",", 1) != 0)
            {
                return -1;
            }
            if (pk_put(out, cap, &at, piece, (size_t)len) != 0)
            {
                return -1;
            }
        }
    }
    return pk_put(out, cap, &at, (u != 0) ? ";u=1" : ";u=0", 4);
}

int pick_queue_native(const unsigned char *recs, int n, int *q, int cap)
{
    if (recs == NULL || n <= 0 || q == NULL || cap <= 0)
    {
        return 0;
    }
    int cnt = 0;
    for (int i = 0; i < n && cnt < cap; i++)
    {
        const unsigned char *r = recs + (size_t)i * MASTER_STRIDE;
        if (*(const int *)(r + MASTER_REC_KIND) != PK_KIND_ARMORY)
        {
            continue;
        }
        if (*(const int *)(r + PK_REC_TRIGS) < 1)
        {
            continue;
        }
        unsigned t = *(const unsigned *)(r + PK_REC_TRIG);
        if (t < PK_TRIG_FIRST || t > PK_TRIG_LAST)
        {
            continue;
        }
        q[cnt++] = (int)*(const unsigned long long *)r;
    }
    return cnt;
}

int pick_row_state(const unsigned char *recs, int n, int id)
{
    if (recs == NULL || n <= 0 || id <= 0)
    {
        return -1;
    }
    for (int i = 0; i < n; i++)
    {
        const unsigned char *r = recs + (size_t)i * MASTER_STRIDE;
        if (*(const unsigned long long *)r != (unsigned long long)id)
        {
            continue;
        }
        int tiers = *(const int *)(r + MASTER_REC_COUNT);
        if (tiers <= 0 || tiers > MASTER_THRESHOLDS_MAX)
        {
            return 0; // no threshold would mean complete on the first xp
        }
        if (*(const unsigned char *)(r + PK_REC_STATUS) == 3)
        {
            return 1;
        }
        long long top = *(const unsigned *)(r + MASTER_REC_THR + (size_t)(tiers - 1) * 4);
        return *(const long long *)(r + MASTER_REC_XP) >= top ? 1 : 0;
    }
    return -1;
}

int pick_next(const unsigned char *recs, int n, int done, const int *q, int q_n)
{
    if (q == NULL || q_n <= 0)
    {
        return 0;
    }
    for (int i = 0; i < q_n; i++)
    {
        if (q[i] <= 0 || q[i] == done)
        {
            continue;
        }
        if (recs != NULL && n > 0 && pick_row_state(recs, n, q[i]) != 0)
        {
            continue; // complete, or an id this array does not hold
        }
        return q[i];
    }
    return 0;
}

int pick_read(const wchar_t *path, char *out, size_t cap, const char **why)
{
    if (why != NULL)
    {
        *why = "";
    }
    if (path == NULL || out == NULL || cap == 0)
    {
        return 0;
    }
    HANDLE f = CreateFileW(path, GENERIC_READ, FILE_SHARE_READ | FILE_SHARE_WRITE | FILE_SHARE_DELETE, NULL,
                           OPEN_EXISTING, FILE_ATTRIBUTE_NORMAL, NULL);
    if (f == INVALID_HANDLE_VALUE)
    {
        DWORD e = GetLastError();
        if (e == ERROR_FILE_NOT_FOUND || e == ERROR_PATH_NOT_FOUND)
        {
            return 0;
        }
        if (why != NULL)
        {
            *why = "the file could not be opened";
        }
        return -1;
    }
    // one byte past a full line and its line ending so a longer file is seen as longer
    char buf[PICK_MAX + 3];
    DWORD got = 0;
    BOOL ok = ReadFile(f, buf, (DWORD)sizeof(buf), &got, NULL);
    CloseHandle(f);
    if (!ok)
    {
        if (why != NULL)
        {
            *why = "the file could not be read";
        }
        return -1;
    }
    size_t n = (size_t)got;
    while (n > 0 && (buf[n - 1] == '\n' || buf[n - 1] == '\r'))
    {
        n--;
    }
    if (n > PICK_MAX)
    {
        if (why != NULL)
        {
            *why = "the line is longer than 1024 chars";
        }
        return -1;
    }
    if (n == 0)
    {
        if (why != NULL)
        {
            *why = "the file is empty";
        }
        return -1;
    }
    if (!pick_valid(buf, n))
    {
        if (why != NULL)
        {
            *why = "the line carries a character outside [a-z0-9=;,]";
        }
        return -1;
    }
    if (n + 1 > cap)
    {
        if (why != NULL)
        {
            *why = "the buffer is too small";
        }
        return -1;
    }
    memcpy(out, buf, n);
    out[n] = '\0';
    return 1;
}

int pick_write(const wchar_t *path, const char *line)
{
    if (path == NULL || line == NULL)
    {
        return -1;
    }
    size_t n = strlen(line);
    if (!pick_valid(line, n))
    {
        return -1;
    }
    wchar_t tmp[MAX_PATH];
    if (_snwprintf_s(tmp, MAX_PATH, _TRUNCATE, L"%s.tmp", path) < 0)
    {
        return -1;
    }
    HANDLE f = CreateFileW(tmp, GENERIC_WRITE, 0, NULL, CREATE_ALWAYS, FILE_ATTRIBUTE_NORMAL, NULL);
    if (f == INVALID_HANDLE_VALUE)
    {
        return -1;
    }
    DWORD wrote = 0;
    BOOL ok = WriteFile(f, line, (DWORD)n, &wrote, NULL);
    if (ok && wrote == (DWORD)n)
    {
        ok = FlushFileBuffers(f);
    }
    CloseHandle(f);
    if (!ok || wrote != (DWORD)n)
    {
        DeleteFileW(tmp);
        return -1;
    }
    // the client own store does it this way rename over the old file never edit in place
    if (!MoveFileExW(tmp, path, MOVEFILE_REPLACE_EXISTING | MOVEFILE_WRITE_THROUGH))
    {
        DeleteFileW(tmp);
        return -1;
    }
    return 0;
}

// the first save is always said then one per window
static int pk_may_say(ULONGLONG now)
{
    if (!PK_SAID_SAVE)
    {
        PK_SAID_SAVE = 1;
        PK_LOG_AT = now;
        return 1;
    }
    if (now - PK_LOG_AT >= PK_LOG_MS)
    {
        PK_LOG_AT = now;
        return 1;
    }
    return 0;
}

// one write the file value only becomes the known one when the write landed
static void pk_save(const char *line, ULONGLONG now, int force)
{
    wchar_t path[MAX_PATH];
    // the folder is the client own a missing one is a skip said once never made here
    int rc = -1;
    if (pk_folder() && pk_path(path, MAX_PATH))
    {
        rc = pick_write(path, line);
    }
    if (pk_may_say(now) || force)
    {
        if (rc == 0)
        {
            ch_logf("pick: saved %s", line);
        }
        else
        {
            ch_logf("pick: save failed - %s", line);
        }
    }
    if (rc == 0)
    {
        memcpy(PK_DISK, line, strlen(line) + 1);
    }
}

// the dvar text or NULL when what it points at is not readable
static const char *pk_value(void)
{
    if (PK_DVAR == NULL)
    {
        return NULL;
    }
    const char *v = *(char **)((char *)PK_DVAR + PK_SLOT);
    if (v == NULL || !g11_page_ok(v))
    {
        return NULL;
    }
    return v;
}

// the merged line into the dvar own slot the buffer is static on purpose
static void pk_publish(void)
{
    if (pick_build(PK_LINE, sizeof(PK_LINE), (int)PK_A, PK_Q, PK_QN, (int)PK_U) != 0)
    {
        return;
    }
    char **value = (char **)((char *)PK_DVAR + PK_SLOT);
    if (!g11_page_writable(value))
    {
        return;
    }
    *value = PK_LINE;
}

// the record array the client resolves at 0x3DD288 and its count at 0x3DD290
static int pk_records(unsigned char **out, int *count)
{
    HMODULE client = GetModuleHandleW(L"XINPUT9_1_0.dll");
    if (client == NULL)
    {
        return -1;
    }
    const RS_TABLE *rs = rs_for(client);
    unsigned recs_rva = rs_rva(rs, RS_RECS);
    unsigned count_rva = rs_rva(rs, RS_COUNT);
    if (recs_rva == 0 || count_rva == 0)
    {
        return -1;
    }
    unsigned char *recs = *(unsigned char **)((BYTE *)client + recs_rva);
    int n = *(volatile int *)((BYTE *)client + count_rva);
    if (recs == NULL || n <= 0 || n > PK_REC_MAX)
    {
        return -1;
    }
    if (!g11_page_ok(recs) || !g11_page_ok(recs + (size_t)(n - 1) * MASTER_STRIDE + MASTER_REC_XP))
    {
        return -1;
    }
    *out = recs;
    *count = n;
    return 0;
}

// the queue out of the client table when the lua sent none
static int pk_native(void)
{
    unsigned char *recs = NULL;
    int n = 0;
    if (pk_records(&recs, &n) != 0)
    {
        return 0;
    }
    int q[PICK_Q_MAX];
    int got = pick_queue_native(recs, n, q, PICK_Q_MAX);
    if (got <= 0)
    {
        return 0;
    }
    memcpy(PK_Q, q, (size_t)got * sizeof(int));
    PK_QN = got;
    PK_SAID_DONE = 0;
    pk_publish();
    if (!PK_SAID_QUEUE)
    {
        PK_SAID_QUEUE = 1;
        ch_logf("pick: queue %d from the table", got);
    }
    return 1;
}

// a completed row swaps the active one for the next unpaid id in the queue
static void pk_advance(int done)
{
    unsigned char *recs = NULL;
    int n = 0;
    if (pk_records(&recs, &n) != 0)
    {
        recs = NULL;
        n = 0;
    }
    int next = pick_next(recs, n, done, PK_Q, PK_QN);
    if (next == 0)
    {
        // no row left to owe so none stays active
        PK_A = 0;
        pk_publish();
        if (strcmp(PK_LINE, PK_DISK) != 0)
        {
            pk_save(PK_LINE, GetTickCount64(), 1);
        }
        if (!PK_SAID_DONE)
        {
            PK_SAID_DONE = 1;
            ch_logf("armory: queue done");
        }
        return;
    }
    PK_A = next;
    pk_publish();
    if (strcmp(PK_LINE, PK_DISK) != 0)
    {
        pk_save(PK_LINE, GetTickCount64(), 1);
    }
    ch_logf("armory: advance %d -> %d", done, next);
}

void pick_arm(G11_REG reg, const unsigned char salt[16], long slot)
{
    if (PK_ARMED || PK_OFF || reg == NULL)
    {
        return;
    }
    if (pick_off_present(NULL))
    {
        PK_OFF = 1;
        ch_logf("pick: disabled by file (%s)", "%TEMP%\\progression-tuning\\armory_off.txt");
        return;
    }
    wchar_t path[MAX_PATH];
    // static not stack this text is the dvar default and the engine may keep the pointer
    static char line[PICK_MAX + 1];
    const char *why = "";
    int got = 0;
    int migrated = 0;
    if (!pk_folder())
    {
        got = -1;
        why = "no players folder";
    }
    else if (pk_path(path, MAX_PATH))
    {
        got = pick_read(path, line, sizeof(line), &why);
        // the older file seeds this one once and stays
        if (got == 0 && pk_path_named(path, MAX_PATH, PK_OLD))
        {
            got = pick_read(path, line, sizeof(line), &why);
            migrated = (got == 1);
        }
    }
    else
    {
        got = -1;
        why = "the dll own directory could not be named";
    }
    if (got != 1)
    {
        strcpy_s(line, sizeof(line), PICK_DEFAULT);
    }
    // our own value is the default so a dvar this call creates already holds the file line
    void *d = reg(g11_hash_name(PICK_NAME, salt), line, 0, "progression tuning armory");
    if (d == NULL)
    {
        return; // the engine register is not usable yet the caller retries
    }
    char **value = (char **)((char *)d + slot);
    if (!g11_page_writable(value))
    {
        PK_OFF = 1;
        ch_logf("pick: refused - the value slot is not writable");
        return;
    }
    if (migrated)
    {
        ch_logf("pick: file migrated from pt_armory.txt");
    }
    if (got == 1)
    {
        ch_logf("pick: file %s", line);
    }
    else if (got == 0)
    {
        ch_logf("pick: file none");
    }
    else
    {
        ch_logf("pick: file rejected: %s", why);
    }
    int a = 0;
    int qn = -1;
    int u = 0;
    int q[PICK_Q_MAX];
    if (pick_parse(line, strlen(line), &a, q, PICK_Q_MAX, &qn, &u) == 0)
    {
        a = 0;
        qn = -1;
        u = 0;
    }
    PK_A = a;
    PK_U = u;
    PK_QN = (qn > 0) ? qn : 0;
    if (qn > 0)
    {
        memcpy(PK_Q, q, (size_t)qn * sizeof(int));
    }
    strcpy_s(PK_LINE, sizeof(PK_LINE), line);
    strcpy_s(PK_DISK, sizeof(PK_DISK), line);
    *value = PK_DISK;
    PK_DVAR = d;
    PK_SLOT = slot;
    PK_ARMED = 1;
    ch_logf("pick: registered %s = %s", PICK_NAME, PK_DISK);
}

void pick_tick(void)
{
    if (!PK_ARMED || PK_OFF)
    {
        return;
    }
    ULONGLONG now = GetTickCount64();
    // the advance first so it is served before the one second channel throttle
    LONG adv = InterlockedExchange(&PK_ADVANCE, 0);
    if (adv > 0)
    {
        pk_advance((int)adv);
    }
    if (PK_TICK_AT != 0 && now - PK_TICK_AT < PK_TICK_MS)
    {
        return;
    }
    PK_TICK_AT = now;
    const char *v = pk_value();
    if (v == NULL)
    {
        return;
    }
    size_t n = strnlen(v, PICK_MAX + 1);
    int a = 0;
    int qn = -1;
    int u = 0;
    int q[PICK_Q_MAX];
    if (!pick_valid(v, n) || pick_parse(v, n, &a, q, PICK_Q_MAX, &qn, &u) == 0)
    {
        if (!PK_SAID_BAD)
        {
            PK_SAID_BAD = 1;
            ch_logf("pick: refused a line a reader would not take");
        }
        return; // nothing to write or nothing a reader would accept
    }
    if (a != (int)PK_A)
    {
        PK_A = a;
        ch_logf("armory: pick a=%d", a);
    }
    if (u != (int)PK_U)
    {
        PK_U = u;
        ch_logf("armory: pick u=%d", u);
    }
    if (qn >= 0)
    {
        // new queue new rows so done is said again
        if (qn != PK_QN || memcmp(PK_Q, q, (size_t)qn * sizeof(int)) != 0)
        {
            PK_SAID_DONE = 0;
        }
        memcpy(PK_Q, q, (size_t)qn * sizeof(int));
        PK_QN = qn;
    }
    if (PK_QN == 0)
    {
        pk_native();
    }
    char line[PICK_MAX + 1];
    if (pick_build(line, sizeof(line), (int)PK_A, PK_Q, PK_QN, (int)PK_U) == 0 && strcmp(line, PK_DISK) != 0)
    {
        pk_save(line, now, 0);
    }
}

void pick_stop(void)
{
    if (!PK_ARMED)
    {
        return;
    }
    const char *v = pk_value();
    if (v == NULL)
    {
        return;
    }
    size_t n = strnlen(v, PICK_MAX + 1);
    int a = 0;
    int qn = -1;
    int u = 0;
    int q[PICK_Q_MAX];
    if (!pick_valid(v, n) || pick_parse(v, n, &a, q, PICK_Q_MAX, &qn, &u) == 0)
    {
        return;
    }
    if (qn < 0)
    {
        qn = PK_QN;
        memcpy(q, PK_Q, (size_t)qn * sizeof(int));
    }
    char line[PICK_MAX + 1];
    if (pick_build(line, sizeof(line), a, q, qn, u) != 0 || strcmp(line, PK_DISK) == 0)
    {
        return;
    }
    pk_save(line, GetTickCount64(), 1);
}

int pick_armed(void)
{
    return PK_ARMED;
}

int pick_active(void)
{
    return (int)PK_A;
}

int pick_unlocked(void)
{
    return (int)PK_U;
}

int pick_queue(int *out, int cap)
{
    if (out == NULL || cap <= 0)
    {
        return 0;
    }
    int n = PK_QN;
    if (n > cap)
    {
        n = cap;
    }
    for (int i = 0; i < n; i++)
    {
        out[i] = PK_Q[i];
    }
    return n;
}

void pick_request_advance(int done_id)
{
    if (done_id > 0)
    {
        InterlockedExchange(&PK_ADVANCE, (LONG)done_id);
    }
}

int pick_off_present(const wchar_t *tempdir)
{
    wchar_t dir[MAX_PATH];
    wchar_t path[MAX_PATH];
    if (tempdir == NULL)
    {
        DWORD n = GetTempPathW(MAX_PATH, dir);
        if (n == 0 || n >= MAX_PATH)
        {
            return 0;
        }
        tempdir = dir;
    }
    if (_snwprintf_s(path, MAX_PATH, _TRUNCATE, L"%sprogression-tuning\\armory_off.txt", tempdir) < 0)
    {
        return 0;
    }
    DWORD a = GetFileAttributesW(path);
    return (a != INVALID_FILE_ATTRIBUTES && a != 0xFFFFFFFFu) ? 1 : 0;
}
