// clienthook - the resolver's offline checker. The SHIPPED resolver (`src\resolve.c`, the same file the DLL is
// built from) run over a PE file on disk instead of a loaded module: the file is read, its sections are laid out
// at their RVAs in one buffer, and that buffer is the image the resolver scans.
//
//   resolve_check image <path.dll> [known]     one report, one summary, exit 0
//
// `known` says the caller has already established the identification triple (size, sha256, SizeOfImage) for this
// file, exactly as frame.c does in the game; without it the two pattern-less symbols stay unresolved and g11 and
// pubxp report themselves off.
//
// It never faults on a bad input: a file that is not a PE, a file truncated inside its own headers, or an image
// whose sections do not fit all end in a report and exit 0. What it prints is asserted by
// tools\test_resolve.py - the driver decides nothing about pass or fail.

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdarg.h>
#include <windows.h>

#include "../../src/resolve.h"

// resolve.c logs through proxy_main.c's ch_logf in the DLL; here it goes to stdout, which is what the wrapper
// reads.
void ch_logf(const char *fmt, ...)
{
    va_list ap;
    va_start(ap, fmt);
    vprintf(fmt, ap);
    va_end(ap);
    printf("\n");
    fflush(stdout);
}

static unsigned char *read_file(const char *path, size_t *len)
{
    FILE *f = fopen(path, "rb");
    if (f == NULL)
    {
        return NULL;
    }
    if (fseek(f, 0, SEEK_END) != 0)
    {
        fclose(f);
        return NULL;
    }
    long n = ftell(f);
    if (n <= 0)
    {
        fclose(f);
        return NULL;
    }
    rewind(f);
    unsigned char *buf = (unsigned char *)malloc((size_t)n);
    if (buf == NULL)
    {
        fclose(f);
        return NULL;
    }
    size_t got = fread(buf, 1, (size_t)n, f);
    fclose(f);
    if (got != (size_t)n)
    {
        free(buf);
        return NULL;
    }
    *len = (size_t)n;
    return buf;
}

// The image as the loader would lay it out: the headers at rva 0, then every section at its VirtualAddress.
// Everything the file does not carry stays zero, so a truncated file is a short image, not a read past it.
static unsigned char *map_image(const unsigned char *file, size_t len)
{
    if (file == NULL || len < 0x40)
    {
        return NULL;
    }
    if (file[0] != 'M' || file[1] != 'Z')
    {
        return NULL;
    }
    unsigned lfanew = 0;
    memcpy(&lfanew, file + 0x3C, 4);
    if (lfanew < 0x40 || lfanew + 24 > len)
    {
        return NULL;
    }
    if (file[lfanew] != 'P' || file[lfanew + 1] != 'E' || file[lfanew + 2] != 0 || file[lfanew + 3] != 0)
    {
        return NULL;
    }
    unsigned char *nt = (unsigned char *)file + lfanew;
    unsigned char *opt = nt + 24;
    unsigned magic = 0;
    unsigned ofimage = 0;
    unsigned soheaders = 0;
    memcpy(&magic, opt, 2);
    if (magic != 0x20B) // a 64-bit image, which is the only kind the client is
    {
        return NULL;
    }
    memcpy(&ofimage, opt + 56, 4);
    memcpy(&soheaders, opt + 60, 4);
    if (ofimage < 0x1000 || ofimage > 0x10000000u)
    {
        return NULL;
    }
    unsigned nsec = 0;
    unsigned optsize = 0;
    memcpy(&nsec, nt + 6, 2);
    memcpy(&optsize, nt + 20, 2);
    unsigned char *sec = opt + optsize;

    unsigned char *img = (unsigned char *)calloc(1, ofimage);
    if (img == NULL)
    {
        return NULL;
    }
    size_t head = (soheaders != 0 && soheaders < ofimage) ? soheaders : 0x1000;
    if (head > len)
    {
        head = len;
    }
    memcpy(img, file, head);

    for (unsigned i = 0; i < nsec; i++)
    {
        unsigned char *sh = sec + (size_t)i * 40;
        if ((size_t)(sh - file) + 40 > len)
        {
            break;
        }
        unsigned vsize = 0;
        unsigned va = 0;
        unsigned rawsize = 0;
        unsigned rawptr = 0;
        memcpy(&vsize, sh + 8, 4);
        memcpy(&va, sh + 12, 4);
        memcpy(&rawsize, sh + 16, 4);
        memcpy(&rawptr, sh + 20, 4);
        unsigned size = vsize != 0 ? vsize : rawsize;
        if (size == 0 || va >= ofimage)
        {
            continue;
        }
        if (size > ofimage - va)
        {
            size = ofimage - va;
        }
        if (rawptr >= len)
        {
            continue;
        }
        unsigned have = size;
        if ((size_t)rawptr + have > len)
        {
            have = (unsigned)(len - rawptr);
        }
        if (rawsize != 0 && have > rawsize)
        {
            have = rawsize;
        }
        memcpy(img + va, file + rawptr, have);
    }
    return img;
}

int main(int argc, char **argv)
{
    if (argc < 3 || (strcmp(argv[1], "image") != 0 && strcmp(argv[1], "order") != 0))
    {
        printf("usage: resolve_check image <path.dll> [known]\n");
        printf("       resolve_check order <path.dll>    the verdict before the first scan (the DLL's own order)\n");
        return 2;
    }
    int known = (argc >= 4 && strcmp(argv[3], "known") == 0) ? 1 : 0;
    int order_first = (strcmp(argv[1], "order") == 0) ? 1 : 0;

    size_t len = 0;
    unsigned char *file = read_file(argv[2], &len);
    if (file == NULL)
    {
        printf("file: could not be read\n");
        printf("resolve: 0/%d symbols (no image)\n", (int)RS_SYM_COUNT);
        printf("RESULT symbols=0 pattern_symbols=0 equal=0 patterns=0/0 known=%d\n", known);
        return 0;
    }
    printf("file: %s %lu B\n", argv[2], (unsigned long)len);

    unsigned char *img = map_image(file, len);
    free(file);
    if (img == NULL)
    {
        printf("image: the file is not a readable PE image\n");
        printf("resolve: 0/%d symbols (no image)\n", (int)RS_SYM_COUNT);
        printf("RESULT symbols=0 pattern_symbols=0 equal=0 patterns=0/0 known=%d\n", known);
        return 0;
    }

    RS_TABLE t;
    // The DLL's own order is `known` first (frame_identify's verdict), then the addresses (rs_for's scan). This
    // mode takes exactly that order, so a scan that reset the verdict would show up here rather than in game.
    if (order_first)
    {
        rs_set_known_build(known);
        printf("order: the verdict was given before the first scan\n");
    }
    int ok = rs_scan(img, &t);
    printf("image: %s, SizeOfImage 0x%lX\n", ok ? "scanned" : "the headers were unusable",
           (unsigned long)(ok ? t.ofimage : 0));

    for (int i = 0; i < rs_pattern_count(); i++)
    {
        unsigned rva = 0;
        int n = rs_pattern_hits(img, i, &rva);
        printf("pattern %-7s count=%d rva=0x%lX\n", rs_pattern_name(i), n, (unsigned long)rva);
    }

    rs_set_known_build(known);
    if (known)
    {
        t.known_build = 1;
    }
    rs_report(&t);

    int resolved = 0;
    int equal = 0;
    int pattern_syms = 0;
    for (int i = 0; i < RS_SYM_COUNT; i++)
    {
        unsigned got = rs_rva(&t, (RS_SYM)i);
        unsigned want = rs_known_rva((RS_SYM)i);
        const char *state = got == 0 ? "unresolved" : (got == want ? "equal" : "MOVED");
        printf("sym %-8s rva=0x%lX known=0x%lX %s\n", rs_sym_name((RS_SYM)i), (unsigned long)got,
               (unsigned long)want, state);
        if (got != 0)
        {
            resolved++;
            if (i < RS_PATTERN_SYMS)
            {
                pattern_syms++;
            }
        }
        if (got != 0 && got == want)
        {
            equal++;
        }
    }

    int patterns_one = 0;
    for (int i = 0; i < rs_pattern_count(); i++)
    {
        if (rs_pattern_hits(img, i, NULL) == 1)
        {
            patterns_one++;
        }
    }

    for (int f = 0; f < RS_F_COUNT; f++)
    {
        const char *miss = rs_feature_missing(&t, (RS_FEATURE)f);
        printf("feature %-9s %s%s\n", rs_feature_name((RS_FEATURE)f), miss == NULL ? "on" : "off - ",
               miss == NULL ? "" : miss);
    }

    printf("RESULT symbols=%d pattern_symbols=%d equal=%d patterns=%d/%d known=%d\n", resolved, pattern_syms,
           equal, patterns_one, rs_pattern_count(), known);
    free(img);
    return 0;
}
