// Offline driver for src\aexp.c: feeds a copy of ae_events.log in pseudo-random chunk sizes (as
// WriteFile would deliver it) and prints one line per parsed event. tools\test_aexp.py compares the
// output with an independent python parse of the same file.
//
//   aexp_test.exe <file> <seed> <maxchunk>

#include <stdio.h>
#include <stdlib.h>

#include "..\src\aexp.h"

static void print_rec(const AE_REC *r, void *ctx)
{
    FILE *out = (FILE *)ctx;
    fprintf(out, "%lld %ld %lld %lld %lld %lld %lld\n", r->t, r->ev, r->f0, r->f31, r->f44, r->f45, r->f234);
}

int main(int argc, char **argv)
{
    if (argc < 4)
    {
        fprintf(stderr, "usage: aexp_test <file> <seed> <maxchunk>\n");
        return 2;
    }
    FILE *f = NULL;
    if (fopen_s(&f, argv[1], "rb") != 0 || f == NULL)
    {
        fprintf(stderr, "cannot open %s\n", argv[1]);
        return 2;
    }
    fseek(f, 0, SEEK_END);
    long size = ftell(f);
    fseek(f, 0, SEEK_SET);
    char *buf = (char *)malloc((size_t)size + 1);
    if (buf == NULL || fread(buf, 1, (size_t)size, f) != (size_t)size)
    {
        fprintf(stderr, "read failed\n");
        return 2;
    }
    fclose(f);

    unsigned long seed = strtoul(argv[2], NULL, 10);
    long maxchunk = strtol(argv[3], NULL, 10);
    if (maxchunk < 1)
        maxchunk = 1;
    static AE_ACC acc; // zeroed
    long pos = 0;
    while (pos < size)
    {
        seed = seed * 1103515245UL + 12345UL;
        long len = 1 + (long)((seed >> 8) % (unsigned long)maxchunk);
        if (pos + len > size)
            len = size - pos;
        ae_feed(&acc, buf + pos, (size_t)len, print_rec, stdout);
        pos += len;
    }
    free(buf);
    return 0;
}
