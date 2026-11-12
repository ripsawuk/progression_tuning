"""Find every reference the code or data of a PE makes to one rva (read-only).

    python clienthook\\tools\\xref_call.py <pe> <rva-hex> [<size-hex>]

Three independent passes, so "nothing else references it" is a measurement and not a guess:

  1. a raw byte scan of .text for `E8 rel32` (call) and `E9 rel32` (jmp) whose target is the rva;
  2. a linear disassembly with capstone that reports every instruction whose *operand* resolves to the
     rva: a RIP-relative lea/mov (`lea rax,[rip+disp]` - how 64-bit code takes a function's address), an
     immediate, or a branch target (jmp/call, all forms, including a register-indirect `jmp rax` is not
     reachable statically, so it is reported by name only if an immediate loads i t);
  3. a scan of the whole image for the absolute VA (ImageBase + rva) stored as an 8-byte little-endian
     value, which is how a vtable or a function pointer would hold it.

It also lists the .pdata entries that begin inside [rva, rva+size), because a hook that misses a
mid-function entry point is bypassed, and every rel32 branch whose target is *inside* the given size
(the "does anything jump into the middle of the function" question).

Exit 0 always: this is a report, not an assertion. The tests assert on its output.
"""

import struct
import sys

import capstone

from pe_rva import Pe

IMAGE_DIRECTORY_ENTRY_EXCEPTION = 3


def text_range(pe):
    s = next((x for x in pe.sections if x["name"] == ".text"), None)
    if s is None:
        raise SystemExit("no .text")
    return s["va"], s["vsize"]


def raw_branches(pe, lo, hi, target, size):
    """Linear byte scan: every E8/E9 whose rel32 lands on `target`, plus those landing inside it."""
    s = pe.section_of(lo)
    code = pe.data[s["raw"]:s["raw"] + s["vsize"]]
    base = s["va"]
    hits = []
    inside = []
    for i in range(0, len(code) - 5):
        op = code[i]
        if op not in (0xE8, 0xE9):
            continue
        rel = struct.unpack_from("<i", code, i + 1)[0]
        dst = base + i + 5 + rel
        if dst == target:
            hits.append((base + i, "call" if op == 0xE8 else "jmp", dst))
        elif target <= dst < target + size and dst != target:
            inside.append((base + i, "call" if op == 0xE8 else "jmp", dst))
    return hits, inside


def disasm_refs(pe, lo, hi, target):
    s = pe.section_of(lo)
    code = pe.data[s["raw"]:s["raw"] + s["vsize"]]
    base = s["va"]
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)
    md.detail = True
    md.skipdata = True
    refs = []
    for insn in md.disasm(code, base):
        if insn.id == 0:
            continue
        for op in insn.operands:
            ea = None
            if op.type == capstone.x86.X86_OP_MEM and op.mem.base == capstone.x86.X86_REG_RIP:
                ea = insn.address + insn.size + op.mem.disp
            elif op.type == capstone.x86.X86_OP_IMM:
                ea = op.imm
                # a `jmp rel32` disassembles with the absolute target in op.imm
            if ea == target:
                refs.append((insn.address, insn.mnemonic, insn.op_str, insn.bytes.hex()))
    return refs


def absolute_values(pe, target_va):
    out = []
    needle = struct.pack("<Q", target_va)
    start = 0
    while True:
        at = pe.data.find(needle, start)
        if at < 0:
            break
        # map file offset -> rva
        sect = next((x for x in pe.sections if x["raw"] <= at < x["raw"] + x["rawsize"]), None)
        out.append((at, sect["name"] if sect else "?", (sect["va"] + at - sect["raw"]) if sect else -1))
        start = at + 1
    return out


def main(argv):
    if len(argv) < 3:
        print(__doc__)
        return 2
    pe = Pe(argv[1])
    rva = int(argv[2], 16)
    size = int(argv[3], 16) if len(argv) > 3 else 0
    target_va = pe.image_base + rva
    print("%s: rva 0x%X, absolute VA 0x%X, ImageBase 0x%X" % (argv[1], rva, target_va, pe.image_base))

    lo, hi = text_range(pe)
    print(".text rva 0x%X..0x%X (%d B)" % (lo, lo + hi, hi))
    print("")

    hits, inside = raw_branches(pe, lo, hi, rva, size or 1)
    print("raw byte scan: %d E8/E9 whose rel32 lands exactly on 0x%X" % (len(hits), rva))
    for addr, kind, _ in hits:
        print("  0x%X  %s  (bytes %s)" % (addr, kind, pe.read(addr, 5).hex()))
    print("raw byte scan: %d E8/E9 whose rel32 lands inside 0x%X+0x%X" % (len(inside), rva, size))
    for addr, kind, dst in inside:
        print("  0x%X  %s -> 0x%X" % (addr, kind, dst))
    print("")

    refs = disasm_refs(pe, lo, hi, rva)
    print("capstone operand scan: %d instructions whose operand resolves to 0x%X" % (len(refs), rva))
    for addr, mnem, ops, raw in refs:
        print("  0x%X  %-8s %s   [%s]" % (addr, mnem, ops, raw))
    print("")

    av = absolute_values(pe, target_va)
    print("absolute 8-byte pointer scan: %d occurrence(s) of 0x%X" % (len(av), target_va))
    for off, name, orva in av:
        print("  file 0x%X in %s (rva 0x%X)" % (off, name, orva))
    print("")

    # .pdata: mid-function entry points, and the entry that covers the rva
    ex_rva, ex_size = pe.dir_rva(IMAGE_DIRECTORY_ENTRY_EXCEPTION)
    entries = [struct.unpack("<III", pe.read(ex_rva + i * 12, 12)) for i in range(ex_size // 12)]
    entry = next((e for e in entries if e[0] <= rva < e[1]), None)
    if entry:
        print(".pdata: rva 0x%X is inside entry begin 0x%X end 0x%X (0x%X B)"
              % (rva, entry[0], entry[1], entry[1] - entry[0]))
        mids = [e for e in entries if entry[0] < e[0] < entry[1]]
        print(".pdata: %d entry point(s) strictly inside it%s"
              % (len(mids), "" if not mids else " -> " + ", ".join("0x%X" % m[0] for m in mids)))
    else:
        print(".pdata: rva 0x%X is not covered by any entry" % rva)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
