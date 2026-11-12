"""Decode the RUNTIME_FUNCTION / UNWIND_INFO a PE holds for an rva (read-only, stdlib only).

    python clienthook\\tools\\unwind.py <pe> <rva-hex> [--prove <rva-hex>]

For every .pdata entry whose begin..end covers the rva it prints the entry, the UNWIND_INFO header
(version, flags, prolog_size, code count, frame register) and the decoded unwind codes in prolog
order, then the two numbers a stack walk depends on:

    frame  = the bytes the prologue takes (alloc + 8 per pushed nonvolatile)
    return = the caller's return address sits at  rsp + frame   (rsp = after the prologue)
    caller rsp after the ret = rsp + frame + 8

It also prints every .pdata entry that *begins* inside the cover, which is the check that the
function has no mid-function entry point a call-site hook could bypass.

`--prove <rva>` prints the classification (section + protection) of an rva from `pe_rva`'s reader,
so a call site and its target can be checked to be code in one invocation.
"""

import struct
import sys

from pe_rva import Pe

IMAGE_DIRECTORY_ENTRY_EXCEPTION = 3

REGS = ["RAX", "RCX", "RDX", "RBX", "RSP", "RBP", "RSI", "RDI",
        "R8", "R9", "R10", "R11", "R12", "R13", "R14", "R15"]


def runtime_functions(pe):
    rva, size = pe.dir_rva(IMAGE_DIRECTORY_ENTRY_EXCEPTION)
    out = []
    if rva == 0 or size == 0:
        return out
    for i in range(size // 12):
        begin, end, info = struct.unpack("<III", pe.read(rva + i * 12, 12))
        if begin == 0 and end == 0:
            continue
        out.append((begin, end, info))
    return out


def decode(pe, info_rva):
    """Return (header dict, codes list). Each code: (offset, op, op_info, extra, bytes_used)."""
    hdr = pe.read(info_rva, 4)
    version = hdr[0] & 0x7
    flags = hdr[0] >> 3
    prolog_size = hdr[1]
    count = hdr[2]
    frame_reg = hdr[3] & 0xF
    frame_off = hdr[3] >> 4
    codes_bytes = pe.read(info_rva + 4, count * 2)
    slots = [(codes_bytes[i * 2], codes_bytes[i * 2 + 1]) for i in range(count)]
    codes = []
    i = 0
    while i < len(slots):
        off, info = slots[i]
        op = info & 0xF
        opinfo = info >> 4
        extra = None
        used = 1
        if op == 0:                      # UWOP_PUSH_NONVOL
            extra = REGS[opinfo]
        elif op == 1:                    # UWOP_ALLOC_LARGE
            if opinfo == 0:
                extra = slots[i + 1][0] | (slots[i + 1][1] << 8)   # 16-bit, x8
                extra *= 8
                used = 2
            else:
                extra = (slots[i + 1][0] | (slots[i + 1][1] << 8) |
                         (slots[i + 2][0] << 16) | (slots[i + 2][1] << 24))
                used = 3
        elif op == 2:                    # UWOP_ALLOC_SMALL
            extra = opinfo * 8 + 8
        elif op == 3:                    # UWOP_SET_FPREG
            extra = "rsp + %d" % (frame_off * 16)
        elif op in (4, 5):               # UWOP_SAVE_NONVOL / _FAR
            extra = REGS[opinfo]
            used = 2 if op == 4 else 3
        elif op in (8, 9):               # UWOP_SAVE_XMM128 / _FAR
            extra = "xmm%d" % opinfo
            used = 2 if op == 8 else 3
        elif op == 10:                   # UWOP_PUSH_MACHFRAME
            extra = "machine frame"
        codes.append({"offset": off, "op": op, "op_info": opinfo, "extra": extra, "used": used})
        i += used
    return ({"version": version, "flags": flags, "prolog_size": prolog_size, "count": count,
             "frame_reg": frame_reg, "frame_off": frame_off}, codes)


OP_NAMES = {0: "PUSH_NONVOL", 1: "ALLOC_LARGE", 2: "ALLOC_SMALL", 3: "SET_FPREG",
            4: "SAVE_NONVOL", 5: "SAVE_NONVOL_FAR", 6: "EPILOG", 7: "SPARE",
            8: "SAVE_XMM128", 9: "SAVE_XMM128_FAR", 10: "PUSH_MACHFRAME"}


def frame_of(codes):
    alloc = 0
    pushes = 0
    for c in codes:
        if c["op"] in (1, 2):
            alloc += int(c["extra"])
        elif c["op"] == 0:
            pushes += 1
    return alloc, pushes, alloc + pushes * 8


def main(argv):
    if len(argv) < 3:
        print(__doc__)
        return 2
    pe = Pe(argv[1])
    rva = int(argv[2], 16)
    prove = None
    if "--prove" in argv:
        prove = int(argv[argv.index("--prove") + 1], 16)

    entries = runtime_functions(pe)
    print("%s: %d .pdata entries, %d B, image base 0x%X, SizeOfImage 0x%X"
          % (argv[1], len(entries), len(pe.data), pe.image_base, pe.size_of_image))
    covering = [e for e in entries if e[0] <= rva < e[1]]
    if not covering:
        print("rva 0x%X is covered by NO RUNTIME_FUNCTION (a leaf, or outside .pdata)" % rva)
        return 1
    for begin, end, info in covering:
        hdr, codes = decode(pe, info)
        alloc, pushes, frame = frame_of(codes)
        print("")
        print("RUNTIME_FUNCTION for 0x%X: begin 0x%X end 0x%X unfoldinfo rva 0x%X (size 0x%X)"
              % (rva, begin, end, info, end - begin))
        print("  version %d  flags 0x%X  prolog_size 0x%X (%d)  codes %d  frame reg 0x%X off 0x%X"
              % (hdr["version"], hdr["flags"], hdr["prolog_size"], hdr["prolog_size"], hdr["count"],
                 hdr["frame_reg"], hdr["frame_off"]))
        for c in codes:
            print("    prolog+0x%02X  %-15s %s" % (c["offset"], OP_NAMES.get(c["op"], "?"), c["extra"]))
        print("  alloc 0x%X, %d pushes -> frame 0x%X: return address at rsp+0x%X, caller rsp rsp+0x%X"
              % (alloc, pushes, frame, frame, frame + 8))
        mids = [e for e in entries if begin < e[0] < end]
        print("  mid-function .pdata entries: %d%s"
              % (len(mids), "" if not mids else " -> " + ", ".join("0x%X" % m[0] for m in mids)))

    if prove is not None:
        s = pe.section_of(prove)
        if s is None:
            print("rva 0x%X -> no section" % prove)
        else:
            print("rva 0x%X -> %s (%s)" % (prove, s["name"], pe.protection(s)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
