// clienthook - ae_events.log line parser. See aexp.h.

#include "aexp.h"

static int read_int(const char *p, const char *end, long long *out, const char **next)
{
    int neg = 0, any = 0;
    long long v = 0;
    if (p < end && *p == '-')
    {
        neg = 1;
        p++;
    }
    while (p < end && *p >= '0' && *p <= '9')
    {
        v = v * 10 + (*p - '0');
        any = 1;
        p++;
    }
    if (next)
        *next = p;
    if (!any)
        return 0;
    *out = neg ? -v : v;
    return 1;
}

int ae_parse_line(const char *s, size_t n, AE_REC *out)
{
    const char *p = s, *end = s + n;
    while (end > p && (end[-1] == '\r' || end[-1] == '\n'))
        end--;

    out->t = 0;
    out->ev = -1;
    out->f0 = out->f31 = out->f44 = out->f45 = out->f234 = AE_ABSENT;

    long long t = 0;
    if (!read_int(p, end, &t, &p) || p >= end || *p != '\t')
        return 0;
    out->t = t;
    p++;
    if (end - p < 4 || p[0] != 'e' || p[1] != 'v' || p[2] != '=')
        return 0;
    p += 3;
    long long ev = 0;
    if (!read_int(p, end, &ev, &p))
        return 0;
    out->ev = (long)ev;

    // `\t<key>=<value>` pairs; a value that is not an integer is skipped
    while (p < end)
    {
        if (*p != '\t')
        {
            p++;
            continue;
        }
        p++;
        long long key = 0, val = 0;
        const char *q = p;
        if (!read_int(p, end, &key, &q) || q >= end || *q != '=')
        {
            p = q;
            continue;
        }
        q++;
        const char *after = q;
        if (read_int(q, end, &val, &after) && (after == end || *after == '\t'))
        {
            switch (key)
            {
            case 0: out->f0 = val; break;
            case 31: out->f31 = val; break;
            case 44: out->f44 = val; break;
            case 45: out->f45 = val; break;
            case 234: out->f234 = val; break;
            default: break;
            }
        }
        p = after;
    }
    return 1;
}

void ae_feed(AE_ACC *acc, const char *buf, size_t n, ae_cb cb, void *ctx)
{
    for (size_t i = 0; i < n; i++)
    {
        char c = buf[i];
        if (c == '\n')
        {
            if (!acc->overflow && acc->n > 0)
            {
                AE_REC r;
                if (ae_parse_line(acc->line, acc->n, &r))
                    cb(&r, ctx);
            }
            acc->n = 0;
            acc->overflow = 0;
            continue;
        }
        if (acc->overflow)
            continue;
        if (acc->n >= sizeof(acc->line))
        {
            acc->overflow = 1;
            continue;
        }
        acc->line[acc->n++] = c;
    }
}
