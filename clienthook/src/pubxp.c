// clienthook - the PAID weapon XP, published into one dvar. See pubxp.h for the format, the record's
// offsets and what each number means.
//
// Nothing here reads or writes a client address, so the offline driver exercises all of it: the
// ledger, the format, the cap, the change-only rule, the match reset and the record lookup over a fabricated
// array.

#include <windows.h>
#include <stdio.h>
#include <string.h>

#include "pubxp.h"

void pxp_init(PXP_LEDGER *L)
{
    if (L == NULL)
    {
        return;
    }
    memset(L, 0, sizeof(*L));
    L->n = 0;
    L->dropped = 0;
    L->text[0] = '\0';
    L->shown[0] = '\0';
}

int pxp_index(const PXP_LEDGER *L, unsigned loot)
{
    if (L == NULL)
    {
        return -1;
    }
    for (int i = 0; i < L->n; i++)
    {
        if (L->g[i].loot == loot)
        {
            return i;
        }
    }
    return -1;
}

// caller holds the ledger's own lock in the DLL; this file is single-threaded by contract
static int pxp_slot(PXP_LEDGER *L, unsigned loot)
{
    int i = pxp_index(L, loot);
    if (i >= 0)
    {
        return i;
    }
    if (L->n >= PXP_MAX)
    {
        L->dropped++;
        return -1;
    }
    i = L->n++;
    memset(&L->g[i], 0, sizeof(L->g[i]));
    L->g[i].loot = loot;
    L->g[i].rec = -1;
    return i;
}

int pxp_note(PXP_LEDGER *L, unsigned loot, long long before, long long after, int paid, PXP_NOTE *out)
{
    PXP_NOTE note;
    note.added = note.capped = note.mismatch = 0;
    if (L == NULL)
    {
        if (out != NULL)
        {
            *out = note;
        }
        return 0;
    }
    int i = pxp_slot(L, loot);
    if (i < 0)
    {
        // past the cap: the client has still paid this gun, the payload simply has no room for it
        note.capped = 1;
        if (out != NULL)
        {
            *out = note;
        }
        return 0;
    }
    note.added = (L->g[i].payments == 0);
    if (!L->g[i].has_base)
    {
        // the level's first payment: this is the value `thisMatch` is measured from
        L->g[i].base = before;
        L->g[i].has_base = 1;
    }
    L->g[i].total = after;
    if (L->g[i].payments < 0xFFFFFFFFul)
    {
        L->g[i].payments++;
    }
    // the self-check: the record must have moved by exactly what was paid
    if (paid >= 0 && (after - before) != (long long)paid)
    {
        note.mismatch = 1;
    }
    if (out != NULL)
    {
        *out = note;
    }
    return pxp_render(L);
}

int pxp_reset_match(PXP_LEDGER *L)
{
    if (L == NULL)
    {
        return 0;
    }
    // IDEMPOTENT. The reset's whole effect is "no gun has a per-match base any more", so a request that arrives
    // when no gun has one has nothing to do: it returns 0 and touches nothing. That is what makes a second
    // boundary notification for the same match harmless - and it is why a payment that landed between the two
    // cannot be undone by the second one unless a base was re-established after the first (which the DLL prevents
    // by giving each boundary exactly one owner: nativepay's wrapper when it is installed, this file's ae reader
    // otherwise).
    {
        int armed = 0;
        for (int i = 0; i < L->n; i++)
        {
            if (L->g[i].has_base)
            {
                armed = 1;
                break;
            }
        }
        if (!armed)
        {
            return 0;
        }
    }
    for (int i = 0; i < L->n; i++)
    {
        L->g[i].has_base = 0;
        L->g[i].base = 0;
    }
    return pxp_render(L);
}

int pxp_render(PXP_LEDGER *L)
{
    if (L == NULL)
    {
        return 0;
    }
    char buf[PXP_TEXT_MAX];
    int n = _snprintf_s(buf, sizeof(buf), _TRUNCATE, "%s;", PXP_VERSION);
    if (n < 0)
    {
        return 0;
    }
    for (int i = 0; i < L->n; i++)
    {
        // `this` is derived from the two absolutes on every render, so a reset needs no arithmetic and a resumed
        // match cannot double count
        long long here = L->g[i].has_base ? (L->g[i].total - L->g[i].base) : 0;
        int add = _snprintf_s(buf + n, sizeof(buf) - (size_t)n, _TRUNCATE, "%s%u:%lld:%lld",
                             i ? ";" : "", L->g[i].loot, L->g[i].total, here);
        if (add < 0)
        {
            // the buffer is sized for 8 entries of 20 digits; a truncation would be a bug, not a long list
            break;
        }
        n += add;
    }
    if (strcmp(buf, L->text) == 0)
    {
        return strcmp(L->text, L->shown) == 0 ? 0 : 1;
    }
    memcpy(L->text, buf, sizeof(L->text));
    L->text[sizeof(L->text) - 1] = '\0';
    return strcmp(L->text, L->shown) == 0 ? 0 : 1;
}

void pxp_shown(PXP_LEDGER *L)
{
    if (L == NULL)
    {
        return;
    }
    memcpy(L->shown, L->text, sizeof(L->shown));
    L->shown[sizeof(L->shown) - 1] = '\0';
}

static int pxp_has_event(const unsigned char *rec)
{
    int n = *(const int *)(rec + PXP_REC_EVENT_N);
    if (n <= 0)
    {
        return 0;
    }
    if (n > PXP_EVENTS_MAX)
    {
        // the same bound the client's own parser uses (4); a longer list is not one this file reads blind
        n = PXP_EVENTS_MAX;
    }
    for (int k = 0; k < n; k++)
    {
        if (*(const unsigned *)(rec + PXP_REC_EVENTS + (size_t)k * 4) == PXP_EVENT_XP)
        {
            return 1;
        }
    }
    return 0;
}

int pxp_find_record(const unsigned char *records, int count, unsigned loot, int *kind_seen)
{
    if (kind_seen != NULL)
    {
        *kind_seen = 0;
    }
    if (records == NULL || count <= 0)
    {
        return -1;
    }
    for (int i = 0; i < count; i++)
    {
        const unsigned char *rec = records + (size_t)i * MASTER_STRIDE;
        if (*(const unsigned *)(rec + PXP_REC_OWNER) != loot)
        {
            continue;
        }
        if (!pxp_has_event(rec))
        {
            continue;
        }
        // the client's own `W` filter has already passed by here (owner == field 44) and the event is in the
        // trigger list - the kind is the additional filter, and a disagreement is reported, not used
        int kind = *(const int *)(rec + PXP_REC_KIND);
        if (kind == PXP_KIND_WEAPON)
        {
            return i;
        }
        if (kind_seen != NULL && *kind_seen == 0)
        {
            *kind_seen = kind;
        }
    }
    return -1;
}

long long pxp_record_xp(const unsigned char *record)
{
    if (record == NULL)
    {
        return 0;
    }
    long long v = 0;
    memcpy(&v, record + PXP_REC_XP, sizeof(v));
    return v;
}
