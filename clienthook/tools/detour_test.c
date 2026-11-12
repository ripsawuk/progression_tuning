// detour_test - the OFFLINE frame test the build-16 crash called for (docs\B16-CRASH.md 7).
//
//   detour_test.exe self                     the unit checks, then `<n> checks, 0 failed`
//   detour_test.exe off <tempdir>            the master kill switch: prints 1 when the file exists, else 0
//   detour_test.exe frame-old <client.dll>   build 16's layout (patched prologue + relay) and walk it
//   detour_test.exe frame-new <client.dll>   build 16b's layout (repointed call site + compiled thunk) and walk it
//
// `frame-*` stages the client's OWN bytes in executable memory - its 17-byte prologue read out of the file, its own
// UNWIND_INFO copied and registered with RtlAddFunctionTable - raises a real exception inside the called body, and
// asks the OS's own RtlVirtualUnwind to walk out of that frame. The verdict is a measurement, not an opinion:
//
//   body frame, machine says   rsp + 0x68 -> return address,  caller rsp  rsp + 0x70
//   body frame, walker  says   whatever RtlVirtualUnwind recovers from the live stack
//
// and the run PASSES only when the walker's answer equals the machine's (and, one frame further out, the C caller's
// real return address and rsp). It exits 0 for PASS and 1 for FAIL in both modes, so `old` failing is a result the
// test script asserts on rather than an accident.
//
// Nothing is installed, no game address is patched, and the client file is only read.

#include <windows.h>
#include <stdarg.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "../src/master.h"

// master.c logs through proxy_main.c's ch_logf; this driver never installs, so the definition only has to exist.
void ch_logf(const char *fmt, ...)
{
    va_list ap;
    va_start(ap, fmt);
    printf("LOG   ");
    vprintf(fmt, ap);
    printf("\n");
    va_end(ap);
}

// --- the client file: rva -> bytes, plus the UNWIND_INFO for one rva (stdlib only) ---------------------

typedef struct
{
    unsigned char *data;
    size_t size;
    unsigned image_base;
    int nsec;
    struct
    {
        char name[9];
        unsigned va, vsize, raw, rawsize;
    } sec[16];
    unsigned exc_rva, exc_size;
} PeFile;

static int pe_open(const char *path, PeFile *pe)
{
    FILE *f = fopen(path, "rb");
    if (f == NULL)
    {
        return 0;
    }
    fseek(f, 0, SEEK_END);
    long n = ftell(f);
    fseek(f, 0, SEEK_SET);
    memset(pe, 0, sizeof(*pe));
    pe->data = (unsigned char *)malloc((size_t)n);
    if (pe->data == NULL || fread(pe->data, 1, (size_t)n, f) != (size_t)n)
    {
        fclose(f);
        free(pe->data);
        return 0;
    }
    fclose(f);
    pe->size = (size_t)n;
    unsigned char *d = pe->data;
    if (d[0] != 'M' || d[1] != 'Z')
    {
        return 0;
    }
    unsigned e = *(unsigned *)(d + 0x3C);
    if (*(unsigned *)(d + e) != 0x4550)
    {
        return 0;
    }
    unsigned opt = e + 24;
    pe->image_base = *(unsigned *)(d + opt + 24);
    unsigned ndirs = *(unsigned *)(d + opt + 108);
    if (ndirs > 3)
    {
        pe->exc_rva = *(unsigned *)(d + opt + 112 + 3 * 8);
        pe->exc_size = *(unsigned *)(d + opt + 112 + 3 * 8 + 4);
    }
    pe->nsec = *(unsigned short *)(d + e + 6);
    unsigned sec = opt + *(unsigned short *)(d + e + 20);
    for (int i = 0; i < pe->nsec && i < 16; i++)
    {
        unsigned char *s = d + sec + i * 40;
        memcpy(pe->sec[i].name, s, 8);
        pe->sec[i].vsize = *(unsigned *)(s + 8);
        pe->sec[i].va = *(unsigned *)(s + 12);
        pe->sec[i].rawsize = *(unsigned *)(s + 16);
        pe->sec[i].raw = *(unsigned *)(s + 20);
    }
    return 1;
}

static unsigned char *pe_at(PeFile *pe, unsigned rva)
{
    for (int i = 0; i < pe->nsec; i++)
    {
        unsigned span = pe->sec[i].vsize > pe->sec[i].rawsize ? pe->sec[i].vsize : pe->sec[i].rawsize;
        if (rva >= pe->sec[i].va && rva < pe->sec[i].va + span)
        {
            unsigned off = pe->sec[i].raw + (rva - pe->sec[i].va);
            if (off < pe->size)
            {
                return pe->data + off;
            }
        }
    }
    return NULL;
}

// The RUNTIME_FUNCTION that covers `rva`: begin, end, and a pointer to its UNWIND_INFO in the file.
static int pe_unwind(PeFile *pe, unsigned rva, unsigned *begin, unsigned *end, unsigned char **info, unsigned *info_len)
{
    for (unsigned i = 0; i + 12 <= pe->exc_size; i += 12)
    {
        unsigned char *e = pe_at(pe, pe->exc_rva + i);
        if (e == NULL)
        {
            return 0;
        }
        unsigned b = *(unsigned *)(e + 0), en = *(unsigned *)(e + 4), ui = *(unsigned *)(e + 8);
        if (b == 0 && en == 0)
        {
            continue;
        }
        if (rva >= b && rva < en)
        {
            unsigned char *p = pe_at(pe, ui);
            if (p == NULL)
            {
                return 0;
            }
            unsigned count = p[2];
            unsigned len = 4 + count * 2;
            if (p[0] & 4) // UNW_FLAG_CHAININFO: one extra RUNTIME_FUNCTION follows the codes
            {
                len += 12;
            }
            *begin = b;
            *end = en;
            *info = p;
            *info_len = len;
            return 1;
        }
    }
    return 0;
}

// --- executable staging -------------------------------------------------------------------------------

static unsigned char *page_alloc(size_t n)
{
    return (unsigned char *)VirtualAlloc(NULL, n, MEM_COMMIT | MEM_RESERVE, PAGE_EXECUTE_READWRITE);
}

static int executable(DWORD64 p)
{
    MEMORY_BASIC_INFORMATION mbi;
    if (p == 0 || VirtualQuery((void *)p, &mbi, sizeof(mbi)) == 0)
    {
        return 0;
    }
    if (mbi.State != MEM_COMMIT)
    {
        return 0;
    }
    return (mbi.Protect & (PAGE_EXECUTE | PAGE_EXECUTE_READ | PAGE_EXECUTE_READWRITE | PAGE_EXECUTE_WRITECOPY))
               ? 1
               : 0;
}

static int readable(DWORD64 p, size_t n)
{
    MEMORY_BASIC_INFORMATION mbi;
    (void)n;
    if (p == 0 || VirtualQuery((void *)p, &mbi, sizeof(mbi)) == 0)
    {
        return 0;
    }
    return (mbi.State == MEM_COMMIT && (mbi.Protect & (PAGE_NOACCESS | PAGE_GUARD)) == 0) ? 1 : 0;
}

static void put64(unsigned char *p, DWORD64 v)
{
    memcpy(p, &v, 8);
}

static void put32(unsigned char *p, unsigned v)
{
    memcpy(p, &v, 4);
}

// --- RtlVirtualUnwind / RtlLookupFunctionEntry / RtlAddFunctionTable, from ntdll ----------------------

typedef PRUNTIME_FUNCTION(NTAPI *fn_lookup)(DWORD64, PDWORD64, PVOID *);
typedef PEXCEPTION_ROUTINE(NTAPI *fn_vunwind)(ULONG, DWORD64, DWORD64, PRUNTIME_FUNCTION, PCONTEXT, PVOID *,
                                              PDWORD64, PKNONVOLATILE_CONTEXT_POINTERS);
typedef BOOLEAN(NTAPI *fn_addtable)(PRUNTIME_FUNCTION, ULONG, DWORD64);

static fn_lookup g_lookup;
static fn_vunwind g_unwind;
static fn_addtable g_addtable;

static int rtl_ready(void)
{
    if (g_lookup != NULL)
    {
        return 1;
    }
    HMODULE nt = GetModuleHandleW(L"ntdll.dll");
    if (nt == NULL)
    {
        return 0;
    }
    g_lookup = (fn_lookup)GetProcAddress(nt, "RtlLookupFunctionEntry");
    g_unwind = (fn_vunwind)GetProcAddress(nt, "RtlVirtualUnwind");
    g_addtable = (fn_addtable)GetProcAddress(nt, "RtlAddFunctionTable");
    return (g_lookup != NULL && g_unwind != NULL && g_addtable != NULL) ? 1 : 0;
}

typedef struct
{
    DWORD64 rip;
    DWORD64 rsp;
    DWORD64 recovered_rip;
    DWORD64 recovered_rsp;
    int is_leaf;
    int faulted;
    int exec;
} Frame;

// Walk from (rip, rsp) and record every frame, up to `max`. The walk stops at a non-executable recovered rip: that
// is the failure this test exists to catch, so it is recorded rather than followed.
static int walk(DWORD64 rip, DWORD64 rsp, Frame *out, int max)
{
    int n = 0;
    while (n < max && rip != 0)
    {
        out[n].rip = rip;
        out[n].rsp = rsp;
        out[n].is_leaf = 0;
        out[n].faulted = 0;
        DWORD64 image_base = 0;
        PRUNTIME_FUNCTION fn = g_lookup(rip, &image_base, NULL);
        if (fn == NULL)
        {
            out[n].is_leaf = 1;
            if (!readable(rsp, 16))
            {
                out[n].faulted = 1;
                out[n].recovered_rip = 0;
                out[n].recovered_rsp = 0;
                n++;
                break;
            }
            out[n].recovered_rip = *(DWORD64 *)rsp;
            out[n].recovered_rsp = rsp + 8;
        }
        else
        {
            CONTEXT ctx;
            memset(&ctx, 0, sizeof(ctx));
            ctx.ContextFlags = CONTEXT_ALL;
            ctx.Rip = rip;
            ctx.Rsp = rsp;
            PVOID handler_data = NULL;
            DWORD64 establisher = 0;
            __try
            {
                g_unwind(0 /*UNW_FLAG_NHANDLER*/, image_base, rip, fn, &ctx, &handler_data, &establisher, NULL);
                out[n].recovered_rip = ctx.Rip;
                out[n].recovered_rsp = ctx.Rsp;
            }
            __except (EXCEPTION_EXECUTE_HANDLER)
            {
                out[n].faulted = 1;
                out[n].recovered_rip = 0;
                out[n].recovered_rsp = 0;
            }
        }
        out[n].exec = executable(out[n].recovered_rip);
        rip = out[n].recovered_rip;
        rsp = out[n].recovered_rsp;
        n++;
        if (out[n - 1].faulted || !out[n - 1].exec)
        {
            break;
        }
    }
    return n;
}

// --- the raised exception, and getting out of it alive -------------------------------------------------

#define DET_EXC 0xE000B160u

static volatile LONG g_raised = 0;
static CONTEXT g_fault;
static Frame g_frames[20];
static int g_frame_n;
static DWORD64 g_recover_stub;
static DWORD64 g_recover_stack;
static HANDLE g_veh;

// The ground truths, captured inside the handler: after the run returns, printf and the C runtime reuse the very
// stack the abandoned frames live on, so anything read later would be the harness's own scribbles.
static unsigned char *g_function_page;
static DWORD64 *g_shim_sp_slot;
static DWORD64 g_body_rsp;
static DWORD64 g_machine_ret;
static DWORD64 g_machine_rsp;
static DWORD64 g_shim_sp;
static DWORD64 g_caller_ret;

static void raiser(void)
{
    RaiseException(DET_EXC, 0, 0, NULL);
}

static LONG CALLBACK veh(EXCEPTION_POINTERS *ep)
{
    if (ep->ExceptionRecord->ExceptionCode != DET_EXC)
    {
        return EXCEPTION_CONTINUE_SEARCH;
    }
    if (g_raised)
    {
        return EXCEPTION_CONTINUE_SEARCH; // a second one means the layout is worse than a measurement
    }
    g_raised = 1;
    g_fault = *ep->ContextRecord;
    g_frame_n = walk(g_fault.Rip, g_fault.Rsp, g_frames, (int)(sizeof(g_frames) / sizeof(g_frames[0])));

    g_body_rsp = *(DWORD64 *)(g_function_page + 0x300);
    g_machine_ret = readable(g_body_rsp + 0x68, 8) ? *(DWORD64 *)(g_body_rsp + 0x68) : 0;
    g_machine_rsp = g_body_rsp + 0x70;
    g_shim_sp = *g_shim_sp_slot;
    g_caller_ret = readable(g_shim_sp, 8) ? *(DWORD64 *)g_shim_sp : 0;

    // Leave the faulting path without unwinding through it: a stub that puts the C caller's registers and rsp back
    // and lands on the shim's `ret`. Nothing between the fault and the shim is used again.
    ep->ContextRecord->Rip = g_recover_stub;
    ep->ContextRecord->Rsp = g_recover_stack;
    return EXCEPTION_CONTINUE_EXECUTION;
}

// --- staging one layout -------------------------------------------------------------------------------

typedef struct
{
    unsigned char *function_page; // the client function: prologue at +0, body at +17
    unsigned char *body;
    unsigned char *relay;
    unsigned char *detour;
    RUNTIME_FUNCTION rt[1];
} Layout;

// The shim: saves the eight nonvolatile registers the C caller owns, stores its own rsp, calls the target, and
// returns. Its recovery stub (at +0x100) reloads those registers from that save block, restores rsp and lands on the
// shim's `ret` - which is what lets the test abandon the faulting stack and still return to C, since an exception's
// context carries the *fault-time* registers (a callee's prologue may have overwritten them).
//
//   +0x00  48 89 25 <d>        mov [rip+0x40],rsp     ; the caller's rsp (the return address is at [rsp])
//   +0x07  8 pushes            rbx rbp rsi rdi r12 r13 r14 r15
//   +0x17  48 83 EC 08         sub rsp,8              ; 16-byte alignment for the call
//   +0x1B  48 B8 <8>           mov rax,<target>
//   +0x25  FF D0               call rax
//   +0x27  48 83 C4 08         add rsp,8
//   +0x2B  8 pops
//   +0x37  C3                  ret
//   +0x100 48 8B 05 <d>        mov rax,[rip+0x40]
//          mov rbx/rbp/rsi/rdi/r12..r15,[rax-8..-0x40]
//          48 89 C4            mov rsp,rax
//          FF 25 <d>           jmp qword ptr [rip+0x48]   (the shim's ret at +0x37)
static unsigned char *stage_shim(unsigned char *page, DWORD64 target, DWORD64 *shim_after)
{
    unsigned char *s = page;
    memset(s, 0xCC, 0x1000);
    s[0] = 0x48; // mov [rip+disp], rsp  -> the slot at +0x40
    s[1] = 0x89;
    s[2] = 0x25;
    put32(s + 3, (unsigned)(0x40 - 7));
    static const unsigned char pushes[16] = {0x40, 0x53, 0x55, 0x56, 0x57, 0x41, 0x54, 0x41, 0x55, 0x41, 0x56,
                                             0x41, 0x57, 0x90, 0x90, 0x90};
    memcpy(s + 7, pushes, 13);
    s[20] = 0x48; // sub rsp,8
    s[21] = 0x83;
    s[22] = 0xEC;
    s[23] = 0x08;
    s[24] = 0x48; // mov rax, imm64
    s[25] = 0xB8;
    put64(s + 26, target);
    s[34] = 0xFF; // call rax
    s[35] = 0xD0;
    s[36] = 0x48; // add rsp,8
    s[37] = 0x83;
    s[38] = 0xC4;
    s[39] = 0x08;
    s[40] = 0x41; // pop r15, r14, r13, r12
    s[41] = 0x5F;
    s[42] = 0x41;
    s[43] = 0x5E;
    s[44] = 0x41;
    s[45] = 0x5D;
    s[46] = 0x41;
    s[47] = 0x5C;
    s[48] = 0x5F; // pop rdi, rsi, rbp, rbx
    s[49] = 0x5E;
    s[50] = 0x5D;
    s[51] = 0x5B;
    s[52] = 0xC3; // ret
    *shim_after = (DWORD64)s + 52;

    unsigned char *r = s + 0x100;
    unsigned k = 0;
    r[k++] = 0x48; // mov rax,[rip+disp] -> the slot at +0x40
    r[k++] = 0x8B;
    r[k++] = 0x05;
    put32(r + k, (unsigned)(0x40 - (0x100 + 7)));
    k += 4;
    static const unsigned char loads[9][4] = {
        {0x48, 0x8B, 0x58, 0xF8}, // rbx,[rax-8]
        {0x48, 0x8B, 0x68, 0xF0}, // rbp,[rax-0x10]
        {0x48, 0x8B, 0x70, 0xE8}, // rsi,[rax-0x18]
        {0x48, 0x8B, 0x78, 0xE0}, // rdi,[rax-0x20]
        {0x4C, 0x8B, 0x60, 0xD8}, // r12,[rax-0x28]
        {0x4C, 0x8B, 0x68, 0xD0}, // r13,[rax-0x30]
        {0x4C, 0x8B, 0x70, 0xC8}, // r14,[rax-0x38]
        {0x4C, 0x8B, 0x78, 0xC0}, // r15,[rax-0x40]
    };
    for (int i = 0; i < 8; i++)
    {
        memcpy(r + k, loads[i], 4);
        k += 4;
    }
    r[k++] = 0x48; // mov rsp,rax
    r[k++] = 0x89;
    r[k++] = 0xC4;
    r[k++] = 0xFF; // jmp qword ptr [rip+disp] -> the slot at +0x48
    r[k++] = 0x25;
    put32(r + k, (unsigned)(0x48 - (0x100 + k + 4)));
    k += 4;
    put64(s + 0x48, *shim_after);

    // The shim's own UNWIND_INFO (at +0x200): prolog_size 0x18, one ALLOC_SMALL 8, eight PUSH_NONVOL - so a walk
    // through the shim is correct, exactly the requirement this build places on every piece of our own code.
    unsigned char *ui = s + 0x200;
    ui[0] = 1;
    ui[1] = 24;
    ui[2] = 9;
    ui[3] = 0;
    static const unsigned char codes[9][2] = {
        {24, (0 << 4) | 2},  // ALLOC_SMALL 8      (sub rsp,8)
        {20, (15 << 4) | 0}, // push r15
        {18, (14 << 4) | 0}, // push r14
        {16, (13 << 4) | 0}, // push r13
        {14, (12 << 4) | 0}, // push r12
        {12, (7 << 4) | 0},  // push rdi
        {11, (6 << 4) | 0},  // push rsi
        {10, (5 << 4) | 0},  // push rbp
        {9, (3 << 4) | 0},   // push rbx
    };
    memcpy(ui + 4, codes, sizeof(codes));
    return s;
}

// Build the client-side page: its own prologue bytes, then a body stub with the frame the record describes (it
// records rsp, calls the raiser, and runs the real epilogue).
static int stage_body(Layout *L, PeFile *pe)
{
    unsigned begin = 0, end = 0, info_len = 0;
    unsigned char *info = NULL;
    if (!pe_unwind(pe, MASTER_RVA, &begin, &end, &info, &info_len))
    {
        printf("FAIL  the client has no RUNTIME_FUNCTION for rva 0x%X\n", MASTER_RVA);
        return 0;
    }
    unsigned char *page = page_alloc(0x1000);
    if (page == NULL)
    {
        printf("FAIL  the staging page could not be allocated\n");
        return 0;
    }
    memset(page, 0xCC, 0x1000);
    memcpy(page, pe_at(pe, MASTER_RVA), MASTER_PROLOGUE_LEN);

    unsigned char *b = page + MASTER_PROLOGUE_LEN;
    unsigned o = 0;
    b[o++] = 0x48; // mov rax, <raiser>
    b[o++] = 0xB8;
    put64(b + o, (DWORD64)(void *)raiser);
    o += 8;
    b[o++] = 0x48; // mov [rip+disp], rsp  ; the body's own rsp, recorded
    b[o++] = 0x89;
    b[o++] = 0x25;
    put32(b + o, (unsigned)(0x300 - (MASTER_PROLOGUE_LEN + o + 4)));
    o += 4;
    b[o++] = 0xFF; // call rax
    b[o++] = 0xD0;
    b[o++] = 0x48; // add rsp,0x28
    b[o++] = 0x83;
    b[o++] = 0xC4;
    b[o++] = 0x28;
    b[o++] = 0x41; // pop r15, r14, r13, r12
    b[o++] = 0x5F;
    b[o++] = 0x41;
    b[o++] = 0x5E;
    b[o++] = 0x41;
    b[o++] = 0x5D;
    b[o++] = 0x41;
    b[o++] = 0x5C;
    b[o++] = 0x5F; // pop rdi, rsi, rbp, rbx
    b[o++] = 0x5E;
    b[o++] = 0x5D;
    b[o++] = 0x5B;
    b[o++] = 0xC3;

    // The client's own UNWIND_INFO, copied verbatim, and a RUNTIME_FUNCTION that covers the staged function.
    memcpy(page + 0x200, info, info_len);
    L->rt[0].BeginAddress = 0;
    L->rt[0].EndAddress = 0x100;
    L->rt[0].UnwindInfoAddress = 0x200;
    if (!g_addtable(L->rt, 1, (DWORD64)page))
    {
        printf("FAIL  RtlAddFunctionTable refused the staged client function\n");
        return 0;
    }
    L->function_page = page;
    L->body = b;
    return 1;
}

static volatile int g_fixups;

// The stand-in for master_fixup in the old layout: entered by `jmp`, returns to the client's caller.
static void old_fixup(void)
{
    g_fixups++;
}

// The old layout's patch, relay and detour, byte for byte the shapes build 16 shipped (tools\disfn.py of the
// crashed DLL: 80D0 sub rsp,0x28 / mov rax,[relay] / test / je / call rax / 80E2 add rsp,0x28 / jmp fixup).
static int stage_old(Layout *L)
{
    unsigned char *relay = page_alloc(0x1000);
    unsigned char *det = page_alloc(0x1000);
    static RUNTIME_FUNCTION det_rt[1];
    if (relay == NULL || det == NULL)
    {
        return 0;
    }
    memset(relay, 0xCC, 0x1000);
    memset(det, 0xCC, 0x1000);

    // the relay: the original 17 bytes, then `mov rax,<body>; jmp rax`
    memcpy(relay, L->function_page, MASTER_PROLOGUE_LEN);
    unsigned n = MASTER_PROLOGUE_LEN;
    relay[n++] = 0x48;
    relay[n++] = 0xB8;
    put64(relay + n, (DWORD64)L->body);
    n += 8;
    relay[n++] = 0xFF;
    relay[n++] = 0xE0;

    // the detour
    unsigned o = 0;
    det[o++] = 0x48; // sub rsp,0x28
    det[o++] = 0x83;
    det[o++] = 0xEC;
    det[o++] = 0x28;
    det[o++] = 0x48; // mov rax,[rip+slot]
    det[o++] = 0x8B;
    det[o++] = 0x05;
    put32(det + o, (unsigned)(0x40 - (o + 4)));
    o += 4;
    det[o++] = 0x48; // test rax,rax
    det[o++] = 0x85;
    det[o++] = 0xC0;
    det[o++] = 0x74; // je +2
    det[o++] = 0x02;
    det[o++] = 0xFF; // call rax  -> the resume is at +0x12, exactly like 80E2
    det[o++] = 0xD0;
    if (o != 0x12)
    {
        printf("FAIL  the staged detour's resume is at +0x%X, not +0x12\n", o);
        return 0;
    }
    det[o++] = 0x48; // add rsp,0x28
    det[o++] = 0x83;
    det[o++] = 0xC4;
    det[o++] = 0x28;
    det[o++] = 0x48; // mov rax,<fixup>; jmp rax   (the absolute form of build 16's `jmp master_fixup`)
    det[o++] = 0xB8;
    put64(det + o, (DWORD64)(void *)old_fixup);
    o += 8;
    det[o++] = 0xFF;
    det[o++] = 0xE0;
    put64(det + 0x40, (DWORD64)relay); // the MASTER_RELAY slot

    // its own unwind record: prolog_size 4, ALLOC_SMALL 0x28 - the DLL's .pdata for master_detour, verified with
    // tools\unwind.py (rva 0x80D0, prolog 0x4, one ALLOC_SMALL 40, no frame register)
    unsigned char *ui = det + 0x100;
    ui[0] = 1;
    ui[1] = 4;
    ui[2] = 1;
    ui[3] = 0;
    ui[4] = 4;
    ui[5] = (4 << 4) | 2;
    det_rt[0].BeginAddress = 0;
    det_rt[0].EndAddress = o;
    det_rt[0].UnwindInfoAddress = 0x100;
    if (!g_addtable(det_rt, 1, (DWORD64)det))
    {
        printf("FAIL  RtlAddFunctionTable refused the staged detour\n");
        return 0;
    }

    // the patch over the staged function's entry: `mov rax,<detour>; jmp rax` + four NOPs
    unsigned char *p = L->function_page;
    p[0] = 0x48;
    p[1] = 0xB8;
    put64(p + 2, (DWORD64)det);
    p[10] = 0xFF;
    p[11] = 0xE0;
    memset(p + 12, 0x90, 4);

    L->relay = relay;
    L->detour = det;
    return 1;
}

// --- the run and the verdict --------------------------------------------------------------------------

static Layout L;
static unsigned char *g_shim_page;
static unsigned char *g_aux_page;
static RUNTIME_FUNCTION g_shim_rt[1];

static int run_frame(int old_layout, const char *client_path)
{
    PeFile pe;
    if (!pe_open(client_path, &pe))
    {
        printf("FAIL  cannot read the client at %s\n", client_path);
        return 2;
    }
    if (!rtl_ready())
    {
        printf("FAIL  RtlLookupFunctionEntry / RtlVirtualUnwind / RtlAddFunctionTable are not available\n");
        return 2;
    }
    memset(&L, 0, sizeof(L));
    if (!stage_body(&L, &pe))
    {
        return 2;
    }
    if (old_layout && !stage_old(&L))
    {
        return 2;
    }

    g_shim_page = page_alloc(0x1000);
    g_aux_page = page_alloc(0x1000);
    if (g_shim_page == NULL || g_aux_page == NULL)
    {
        printf("FAIL  the shim pages could not be allocated\n");
        return 2;
    }
    DWORD64 shim_after = 0;
    DWORD64 target = old_layout ? (DWORD64)L.function_page : (DWORD64)master_thunk_address();
    unsigned char *shim = stage_shim(g_shim_page, target, &shim_after);
    g_recover_stub = (DWORD64)(shim + 0x100);
    g_recover_stack = (DWORD64)g_aux_page + 0xFF0;
    g_shim_sp_slot = (DWORD64 *)(shim + 0x40);
    g_function_page = L.function_page;

    // the shim's own frame, registered like any other function's
    g_shim_rt[0].BeginAddress = 0;
    g_shim_rt[0].EndAddress = 0x40;
    g_shim_rt[0].UnwindInfoAddress = 0x200;
    if (!g_addtable(g_shim_rt, 1, (DWORD64)shim))
    {
        printf("FAIL  RtlAddFunctionTable refused the shim\n");
        return 2;
    }

    if (old_layout)
    {
        printf("INFO  old: function page 0x%08lX, relay 0x%08lX, detour 0x%08lX\n",
               (unsigned long)((DWORD64)L.function_page & 0xFFFFFFFFu),
               (unsigned long)((DWORD64)L.relay & 0xFFFFFFFFu),
               (unsigned long)((DWORD64)L.detour & 0xFFFFFFFFu));
    }
    else
    {
        master_bind_level_fn(L.function_page); // the shipped thunk, calling the staged client function
        printf("INFO  new: function page 0x%08lX, thunk 0x%08lX (the shipped master_thunk)\n",
               (unsigned long)((DWORD64)L.function_page & 0xFFFFFFFFu),
               (unsigned long)((DWORD64)master_thunk_address() & 0xFFFFFFFFu));
    }
    FlushInstructionCache(GetCurrentProcess(), shim, 0x200);
    FlushInstructionCache(GetCurrentProcess(), L.function_page, 0x300);
    if (old_layout)
    {
        FlushInstructionCache(GetCurrentProcess(), L.relay, 64);
        FlushInstructionCache(GetCurrentProcess(), L.detour, 0x200);
    }

    g_raised = 0;
    g_frame_n = 0;
    g_veh = AddVectoredExceptionHandler(1, veh);
    {
        typedef void (*shim_fn)(void);
        ((shim_fn)(void *)shim)();
    }
    RemoveVectoredExceptionHandler(g_veh);

    if (!g_raised)
    {
        printf("FAIL  no exception was raised inside the staged body\n");
        return 2;
    }

    // The ground truths were captured inside the handler (see g_body_rsp/...): the stack below the recovered rsp
    // belongs to whatever ran after the exception, so it must not be read here.
    printf("INFO  fault at rip 0x%08lX rsp 0x%08lX (%d frames walked)\n",
           (unsigned long)(g_fault.Rip & 0xFFFFFFFFu), (unsigned long)(g_fault.Rsp & 0xFFFFFFFFu), g_frame_n);
    printf("INFO  body rsp 0x%08lX: the machine says return 0x%08lX, caller rsp 0x%08lX\n",
           (unsigned long)(g_body_rsp & 0xFFFFFFFFu), (unsigned long)(g_machine_ret & 0xFFFFFFFFu),
           (unsigned long)(g_machine_rsp & 0xFFFFFFFFu));
    for (int i = 0; i < g_frame_n; i++)
    {
        printf("      frame %d  rip 0x%08lX  rsp 0x%08lX  -> rip 0x%08lX rsp 0x%08lX%s%s\n", i,
               (unsigned long)(g_frames[i].rip & 0xFFFFFFFFu), (unsigned long)(g_frames[i].rsp & 0xFFFFFFFFu),
               (unsigned long)(g_frames[i].recovered_rip & 0xFFFFFFFFu),
               (unsigned long)(g_frames[i].recovered_rsp & 0xFFFFFFFFu), g_frames[i].is_leaf ? " (leaf)" : "",
               g_frames[i].faulted ? " FAULTED" : "");
    }

    int fails = 0;

    // 1. the staged function's own frame: the record's arithmetic against the machine's
    int body_frame = -1;
    for (int i = 0; i < g_frame_n; i++)
    {
        if (g_frames[i].rip >= (DWORD64)L.function_page && g_frames[i].rip < (DWORD64)L.function_page + 0x100)
        {
            body_frame = i;
            break;
        }
    }
    if (body_frame < 0)
    {
        printf("FAIL  the walk never reached a frame inside the staged function\n");
        fails++;
    }
    else
    {
        DWORD64 true_ret = g_machine_ret;
        DWORD64 true_rsp = g_machine_rsp;
        long long d_rip = (long long)true_ret - (long long)g_frames[body_frame].recovered_rip;
        long long d_rsp = (long long)true_rsp - (long long)g_frames[body_frame].recovered_rsp;
        printf("INFO  body frame %d: walker 0x%08lX/0x%08lX, machine 0x%08lX/0x%08lX, delta rip %+lld rsp %+lld\n",
               body_frame, (unsigned long)(g_frames[body_frame].recovered_rip & 0xFFFFFFFFu),
               (unsigned long)(g_frames[body_frame].recovered_rsp & 0xFFFFFFFFu),
               (unsigned long)(true_ret & 0xFFFFFFFFu), (unsigned long)(true_rsp & 0xFFFFFFFFu), d_rip, d_rsp);
        if (d_rip != 0 || d_rsp != 0)
        {
            printf("FAIL  the record's frame does not describe the live stack: off by rip %+lld / rsp %+lld\n",
                   d_rip, d_rsp);
            fails++;
        }
        else
        {
            printf("PASS  the record's frame describes the live stack exactly (return address and rsp)\n");
        }
    }

    // 2. one frame further out: the C caller's own return address and rsp
    int found_caller = 0;
    for (int i = 0; i < g_frame_n; i++)
    {
        if (g_frames[i].recovered_rip == g_caller_ret && g_frames[i].recovered_rsp == g_shim_sp + 8)
        {
            found_caller = 1;
        }
    }
    if (!found_caller)
    {
        printf("FAIL  the walk never recovered the caller: wanted rip 0x%08lX rsp 0x%08lX\n",
               (unsigned long)(g_caller_ret & 0xFFFFFFFFu), (unsigned long)((g_shim_sp + 8) & 0xFFFFFFFFu));
        fails++;
    }
    else
    {
        printf("PASS  the walk recovered the true caller (rip 0x%08lX, rsp 0x%08lX)\n",
               (unsigned long)(g_caller_ret & 0xFFFFFFFFu), (unsigned long)((g_shim_sp + 8) & 0xFFFFFFFFu));
    }

    printf("RESULT %s: %s", old_layout ? "old" : "new", fails == 0 ? "PASS\n" : "FAIL\n");
    if (fails != 0)
    {
        printf("RESULT %s: %d failing assertion(s)\n", old_layout ? "old" : "new", fails);
    }
    return fails == 0 ? 0 : 1;
}

// --- unit checks (pure helpers, no client required) ----------------------------------------------------

static int g_checks, g_fails;

static void ok(int cond, const char *what)
{
    g_checks++;
    if (cond)
    {
        printf("pass  %s\n", what);
    }
    else
    {
        g_fails++;
        printf("FAIL  %s\n", what);
    }
}

static int self(void)
{
    static unsigned char site[32];
    static unsigned char client[32];
    unsigned char patch[MASTER_SITE_LEN];

    memset(site, 0xCC, sizeof(site));
    site[0] = 0xE8;
    {
        int rel = (int)((long long)(client + MASTER_RVA) - (long long)(site + 5));
        memcpy(site + 1, &rel, 4);
    }
    ok(master_site_ok(site, client) == 1, "site: E8+rel32 to client+0x96680 passes");
    site[0] = 0xE9;
    ok(master_site_ok(site, client) == 0, "site: an E9 (jmp) is refused");
    site[0] = 0xE8;
    site[1] ^= 0x01;
    ok(master_site_ok(site, client) == 0, "site: one changed displacement byte is refused");
    site[1] ^= 0x01;
    ok(master_site_ok(NULL, client) == 0, "site: NULL is refused");
    ok(master_site_ok((const unsigned char *)1, client) == 0, "site: an unmapped site is refused");

    memset(site, 0xE8, sizeof(site));
    memset(site + 1, 0, 4);
    ok(master_site_patch(patch, site, site + 0x100) == 1, "patch: a near target is accepted");
    ok(patch[0] == 0xE8, "patch: the opcode stays E8 (the instruction keeps its length)");
    {
        int got = 0;
        memcpy(&got, patch + 1, 4);
        ok((long long)(site + 5) + got == (long long)(site + 0x100), "patch: rel32 lands exactly on the target");
    }
    ok(master_site_patch(patch, site, (void *)((ULONG_PTR)site + 0x7FFFFFF0ULL)) == 0,
       "patch: a target ~2 GB away is out of reach and refused");
    ok(master_site_patch(patch, site, site + 0x100) == 1, "patch: rebuilt for the read-back check");
    memcpy(site, patch, MASTER_SITE_LEN);
    ok(master_site_is_patch(site, site + 0x100) == 1, "patch: the read-back sees its own bytes");
    ok(master_site_is_patch(site, site + 0x200) == 0, "patch: a different target does not read back");

    ok(MASTER_SITE_COUNT == 5, "sites: the build carries exactly five");
    ok(MASTER_SITE_LEN == 5, "sites: each patch is five bytes (E8 rel32, no orphan byte)");
    ok(MASTER_SITE_RVA[0] == 0x93DFF && MASTER_SITE_RVA[1] == 0x96212 && MASTER_SITE_RVA[2] == 0x9723D &&
           MASTER_SITE_RVA[3] == 0x97626 && MASTER_SITE_RVA[4] == 0x976AC,
       "sites: the recorded five RVAs");
    ok(MASTER_PROLOGUE_LEN == 17, "signature: the prologue is 17 bytes (the client's prolog_size 0x11)");
    ok(master_thunk_address() != NULL, "thunk: the shipped master_thunk is a real function");

    // the kill switch: the negative cases here (no filesystem writes from this driver - the sandbox denies this
    // process a new directory under %TEMP%, measured 0x5). The positive case and the filename boundary are driven
    // by tools\test_detour.py through the `off <dir>` mode, which builds the file itself.
    {
        ok(master_off_present(L"C:\\__clienthook_no_such_root__\\") == 0, "kill switch: a missing root -> 0");
        ok(master_off_present(NULL) == 0, "kill switch: this machine has no master-off file right now -> 0");
    }

    printf("\n%d checks, %d failed\n", g_checks, g_fails);
    if (g_fails == 0)
    {
        printf("detour: OK - %d checks\n", g_checks);
        return 0;
    }
    printf("detour: FAIL - %d of %d checks\n", g_fails, g_checks);
    return 1;
}

// --- the install path, against the real client image (mapped, never executed) -------------------------

static int run_install(const char *client_path)
{
    wchar_t wpath[MAX_PATH];
    MultiByteToWideChar(CP_ACP, 0, client_path, -1, wpath, MAX_PATH);
    HANDLE f = CreateFileW(wpath, GENERIC_READ, FILE_SHARE_READ, NULL, OPEN_EXISTING, 0, NULL);
    if (f == INVALID_HANDLE_VALUE)
    {
        printf("FAIL  cannot open %s\n", client_path);
        return 2;
    }
    HANDLE m = CreateFileMappingW(f, NULL, PAGE_READONLY | SEC_IMAGE, 0, 0, NULL);
    if (m == NULL)
    {
        printf("FAIL  the client could not be mapped as an image (0x%lX)\n", (unsigned long)GetLastError());
        CloseHandle(f);
        return 2;
    }
    unsigned char *base = (unsigned char *)MapViewOfFile(m, FILE_MAP_READ, 0, 0, 0);
    if (base == NULL)
    {
        printf("FAIL  MapViewOfFile failed (0x%lX)\n", (unsigned long)GetLastError());
        CloseHandle(m);
        CloseHandle(f);
        return 2;
    }

    unsigned char before[MASTER_PROLOGUE_LEN];
    memcpy(before, base + MASTER_RVA, MASTER_PROLOGUE_LEN);
    unsigned char orig[MASTER_SITE_COUNT][MASTER_SITE_LEN];
    for (int i = 0; i < MASTER_SITE_COUNT; i++)
    {
        memcpy(orig[i], base + MASTER_SITE_RVA[i], MASTER_SITE_LEN);
    }

    int rc = master_install((HMODULE)base);
    printf("INFO  master_install -> %d (1 = installed; the log lines above are the real ones)\n", rc);

    int fails = 0;
    if (rc != 1)
    {
        printf("FAIL  the install refused\n");
        fails++;
    }

    // every site is now `E8 <rel32>` to code: the thunk itself, or a trampoline that jmps to it
    for (int i = 0; i < MASTER_SITE_COUNT; i++)
    {
        unsigned char *site = base + MASTER_SITE_RVA[i];
        unsigned char now[MASTER_SITE_LEN];
        memcpy(now, site, MASTER_SITE_LEN);
        int rel = 0;
        memcpy(&rel, now + 1, 4);
        DWORD64 dst = (DWORD64)site + MASTER_SITE_LEN + rel;
        unsigned char *at = (unsigned char *)dst;
        int is_thunk = (dst == (DWORD64)master_thunk_address());
        int is_tramp = 0;
        if (!is_thunk && executable(dst))
        {
            unsigned char stub[12];
            memcpy(stub, at, 12);
            DWORD64 stub_target = 0;
            memcpy(&stub_target, stub + 2, 8);
            is_tramp = stub[0] == 0x48 && stub[1] == 0xB8 && stub[10] == 0xFF && stub[11] == 0xE0 &&
                       stub_target == (DWORD64)master_thunk_address();
        }
        printf("INFO  site 0x%X -> %s 0x%08lX  (%s)\n", MASTER_SITE_RVA[i], now[0] == 0xE8 ? "E8" : "??",
               (unsigned long)(dst & 0xFFFFFFFFu),
               is_thunk ? "master_thunk" : (is_tramp ? "trampoline -> master_thunk" : "NOT OUR HOOK"));
        if (now[0] != 0xE8 || (!is_thunk && !is_tramp))
        {
            printf("FAIL  the site at 0x%X is not repointed at the thunk\n", MASTER_SITE_RVA[i]);
            fails++;
        }
    }

    if (memcmp(before, base + MASTER_RVA, MASTER_PROLOGUE_LEN) != 0)
    {
        printf("FAIL  the client's prologue changed\n");
        fails++;
    }
    else
    {
        printf("PASS  the client's 17 prologue bytes are byte-identical after the install\n");
    }

    // put the image back the way it was (this view is ours; the file on disk was never written)
    DWORD old = 0;
    for (int i = 0; i < MASTER_SITE_COUNT; i++)
    {
        unsigned char *site = base + MASTER_SITE_RVA[i];
        if (VirtualProtect(site, MASTER_SITE_LEN, PAGE_EXECUTE_READWRITE, &old))
        {
            memcpy(site, orig[i], MASTER_SITE_LEN);
            DWORD back = 0;
            VirtualProtect(site, MASTER_SITE_LEN, old, &back);
        }
    }
    int restored = 1;
    for (int i = 0; i < MASTER_SITE_COUNT; i++)
    {
        if (memcmp(base + MASTER_SITE_RVA[i], orig[i], MASTER_SITE_LEN) != 0)
        {
            restored = 0;
        }
    }
    printf(restored ? "PASS  all five sites are back to their original bytes\n"
                    : "FAIL  a site did not restore\n");
    if (!restored)
    {
        fails++;
    }

    printf("RESULT install: %s", fails == 0 ? "PASS\n" : "FAIL\n");
    UnmapViewOfFile(base);
    CloseHandle(m);
    CloseHandle(f);
    return fails == 0 ? 0 : 1;
}

int main(int argc, char **argv)
{
    setvbuf(stdout, NULL, _IONBF, 0);
    if (argc >= 2 && strcmp(argv[1], "self") == 0)
    {
        return self();
    }
    if (argc >= 3 && strcmp(argv[1], "off") == 0)
    {
        wchar_t dir[MAX_PATH];
        MultiByteToWideChar(CP_ACP, 0, argv[2], -1, dir, MAX_PATH);
        printf("%d\n", master_off_present(dir));
        return 0;
    }
    if (argc >= 3 && (strcmp(argv[1], "frame-old") == 0 || strcmp(argv[1], "frame-new") == 0))
    {
        return run_frame(strcmp(argv[1], "frame-old") == 0, argv[2]);
    }
    if (argc >= 3 && strcmp(argv[1], "install") == 0)
    {
        return run_install(argv[2]);
    }
    printf("usage: detour_test.exe self | off <tempdir> | frame-old <client.dll> | frame-new <client.dll> | "
           "install <client.dll>\n");
    return 2;
}
