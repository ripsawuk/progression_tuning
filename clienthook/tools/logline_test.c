// logline_test - the offline proof of clienthook build 29's bounded log line (a worker task's check).
//
// WHY IT EXISTS. Build 27 died inside DllMain because `log_line` formatted a 513-byte line into a 512-byte
// stack buffer with `wsprintfA`, which has no bound, and the two spare bytes landed on the /GS cookie
// (docs\B27-NOLAUNCH.md 3.3). This build formats with `_snprintf_s` + `_TRUNCATE` instead. That claim is only
// worth what a measurement makes it worth, so this driver makes it: it calls the SHIPPED `log_line` -
// compiled from `src\proxy_main.c` itself, not a copy - with texts of exactly 488 and 489 characters and with
// a 2,000-character text, then reads back the file the function wrote and checks the byte lengths.
//
// What it proves:
//   * an over-long line is TRUNCATED at the buffer's last byte, never written past it;
//   * every line still ends with CRLF, and the terminator is inside the buffer;
//   * the process is still alive afterwards (it prints, and exits 0) - build 27's equivalent call killed it.
//
// This driver never loads the DLL, and nothing here touches the game, the game folder or the client.
//
//   build\logline_test.exe  -> one line per case, then "logline: OK - N checks" (exit 0) or the failures

#include <windows.h>
#include <stdio.h>
#include <string.h>
#include <wchar.h>

// DllMain's six callees: never called here. They are declared inside DllMain's body in proxy_main.c, so
// these definitions cannot collide with anything, and with /O2 + /Gy an unreferenced DllMain is dropped.
void ch_frame_start(void)
{
}
void nativepay_start(void)
{
}
void nativepay_stop(void)
{
}
void opsfix_start(void)
{
}
void opsfix_stop(void)
{
}
void tokens_stop(void)
{
}
void pick_stop(void)
{
}
void research_stop(void)
{
}

// The shipped unit, included so the static `log_line` and the `g_armed` gate under test are this file's own.
#include "../src/proxy_main.c"

#define LINE_MAX 512 /* the buffer in log_line, and the reason this driver exists */
#define STAMP 21     /* "YYYY-MM-DD HH:MM:SS" + the two spaces before the text */
// The splitter below strips the CRLF, so a parsed line's strlen is the content: the buffer holds 511
// characters plus the terminator, the last two of which are the CRLF, so at most 509 bytes of content.
#define CONTENT_MAX (LINE_MAX - 1 - 2)

static int passes = 0;
static int failures = 0;

static void ok(int cond, const char *what, const char *detail)
{
    if (cond)
    {
        passes++;
        printf("pass  %s%s%s\n", what, detail != NULL ? " - " : "", detail != NULL ? detail : "");
    }
    else
    {
        failures++;
        printf("FAIL  %s%s%s\n", what, detail != NULL ? " - " : "", detail != NULL ? detail : "");
    }
}

// The log's own path: log_line resolves it from the module's directory, which for this exe is build\.
static void log_path(wchar_t *out)
{
    self_dir(out, MAX_PATH);
    wcscat_s(out, MAX_PATH, L"clienthook.log");
}

int main(int argc, char **argv)
{
    (void)argc;
    (void)argv;

    wchar_t path[MAX_PATH];
    log_path(path);
    // A clean file, so the byte lengths read back are this run's and nothing else's.
    DeleteFileW(path);

    // the two lengths that straddle the bound, and the brief's 2,000-character case
    static char text[2001];
    memset(text, 'x', 2000);
    text[2000] = '\0';
    const int len_488 = 488; /* 19 + 2 + 488 + 2 = 511: the last line that fits with its CRLF */
    const int len_489 = 489; /* 19 + 2 + 489 + 2 = 512: one over, so it must be cut */
    char t488[512];
    char t489[512];
    memcpy(t488, text, (size_t)len_488);
    t488[len_488] = '\0';
    memcpy(t489, text, (size_t)len_489);
    t489[len_489] = '\0';

    // The gate is set here because DllMain is what sets it in the game; nothing else in this driver writes it.
    g_armed = TRUE;

    log_line("logline: a short line (the control)");
    log_line(t488);
    log_line(t489);
    log_line(text); /* 2,000 characters: the brief's case */
    log_line("logline: the process is still here after all four");

    // The proof of life: the file the function wrote, read back byte for byte.
    FILE *fh = _wfopen(path, L"rb");
    if (fh == NULL)
    {
        printf("FAIL  log_line wrote no log at all (%ls)\n", path);
        printf("\nlogline: 0 passed, 1 FAILED\n");
        return 1;
    }
    static char raw[16384];
    size_t got = fread(raw, 1, sizeof(raw) - 1, fh);
    fclose(fh);
    raw[got] = '\0';

    // split on CRLF, keeping every byte, so a missing CRLF shows up as a longer line rather than being
    // silently normalised away
    static char lines[8][LINE_MAX + 8];
    int count = 0;
    size_t at = 0;
    while (at < got && count < 8)
    {
        size_t end = at;
        while (end + 1 < got && !(raw[end] == '\r' && raw[end + 1] == '\n'))
        {
            end++;
        }
        if (end + 1 >= got)
        {
            break;
        }
        size_t n = end - at;
        if (n > sizeof(lines[0]) - 1)
        {
            n = sizeof(lines[0]) - 1;
        }
        memcpy(lines[count], raw + at, n);
        lines[count][n] = '\0';
        count++;
        at = end + 2;
    }

    char detail[160];
    _snprintf_s(detail, sizeof(detail), _TRUNCATE, "%llu bytes of log, %d line(s) ending CRLF",
                (unsigned long long)got, count);
    ok(count == 5, "five lines were written, each terminated by CRLF", detail);

    // the byte account: every byte of the file belongs to a line, and every line paid its two CRLF bytes
    {
        size_t total = 0;
        for (int i = 0; i < count; i++)
        {
            total += strlen(lines[i]) + 2;
        }
        _snprintf_s(detail, sizeof(detail), _TRUNCATE, "%llu of %llu bytes", (unsigned long long)total,
                    (unsigned long long)got);
        ok(total == got, "every line's CRLF is in the file - no line was written without one", detail);
    }

    // the control: the stamp, then its own text, unaltered
    {
        const char *ctrl = "logline: a short line (the control)";
        int n = count >= 1 ? (int)strlen(lines[0]) : -1;
        ok(n == STAMP + (int)strlen(ctrl) && strcmp(lines[0] + STAMP, ctrl) == 0,
           "the control line is the stamp plus its own text", count >= 1 ? lines[0] : "(none)");
    }

    // the exact boundary: 488 fits with the CRLF the format adds, and is not touched
    {
        int n = count >= 2 ? (int)strlen(lines[1]) : -1;
        _snprintf_s(detail, sizeof(detail), _TRUNCATE, "%d bytes of content, %d with its CRLF", n, n + 2);
        ok(n == STAMP + len_488, "a 488-char text formats to 19+2+488 = 509 bytes of content, + CRLF = 511",
           detail);
    }

    // one character over: cut at the buffer's last byte, CRLF re-placed inside it, nothing past it
    {
        int n = count >= 3 ? (int)strlen(lines[2]) : -1;
        _snprintf_s(detail, sizeof(detail), _TRUNCATE, "%d bytes of content, %d with its CRLF", n, n + 2);
        ok(n == CONTENT_MAX, "a 489-char text is TRUNCATED to 509 bytes of content, + CRLF = 511 - not 512", detail);
        ok(n > 0 && memcmp(lines[2] + STAMP, t489, (size_t)(n - STAMP)) == 0,
           "the bytes it kept are the first ones of the text, in order", NULL);
    }

    // the brief's case: 2,000 characters in, 511 bytes out, and the process alive to say so
    {
        int n = count >= 4 ? (int)strlen(lines[3]) : -1;
        _snprintf_s(detail, sizeof(detail), _TRUNCATE, "%d bytes of content from a 2000-byte text", n);
        ok(n == CONTENT_MAX, "a 2000-char text is TRUNCATED to 509 bytes of content, + CRLF = 511", detail);
        ok(n == STAMP + len_488 && memcmp(lines[3] + STAMP, text, (size_t)len_488) == 0,
           "and the 488 characters it kept are the text's first 488", NULL);
        ok(count >= 5, "the call after it still ran, so nothing was corrupted by the long one", NULL);
    }

    // nothing above the buffer, on any line, however it was cut
    {
        int worst = 0;
        for (int i = 0; i < count; i++)
        {
            int n = (int)strlen(lines[i]);
            if (n > worst)
            {
                worst = n;
            }
        }
        _snprintf_s(detail, sizeof(detail), _TRUNCATE, "the longest line is %d bytes including its CRLF",
                    worst + 2);
        ok(worst <= CONTENT_MAX, "no line reached the buffer's 512th byte, never mind past it", detail);
    }

    printf("\n");
    if (failures == 0)
    {
        printf("logline: OK - %d checks\n", passes);
        return 0;
    }
    printf("logline: %d passed, %d FAILED\n", passes, failures);
    return 1;
}
