"""Find code that references a string in a PE, by linear disassembly (read-only).

    python clienthook\\tools\\find_xrefs.py <exe-or-dll> "challenges.tsv"

RIP-relative references are what a 64-bit DLL uses for its literals: `lea rdx, [rip+disp]`. This walks
.text, tracks those operands, and prints the instructions around every hit so the calling code can be
read. Read-only; nothing is written into the game.
"""
import sys

import capstone
import pefile


def rva_of(char_bytes, image_base_rva, sections):
    """The RVA an offset inside the file maps to (no relocations applied)."""
    for s in sections:
        start = s.PointerToRawData
        size = s.SizeOfRawData
        if start <= char_bytes < start + size:
            return s.VirtualAddress + (char_bytes - start)
    return None


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        return 2
    path, needle = sys.argv[1], sys.argv[2].encode()

    pe = pefile.PE(path, fast_load=True)
    data = pe.__data__
    off = data.find(needle)
    if off < 0:
        print("string not found")
        return 1
    target = rva_of(off, pe.OPTIONAL_HEADER.ImageBase, pe.sections)
    print(f"{needle.decode()} at file 0x{off:X}  rva 0x{target:X}")

    text = next(s for s in pe.sections if s.Name.startswith(b".text"))
    code = data[text.PointerToRawData:text.PointerToRawData + text.SizeOfRawData]
    base_rva = text.VirtualAddress

    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)
    md.detail = True
    md.skipdata = True

    hits = 0
    prev = []
    for insn in md.disasm(code, base_rva):
        if insn.id == 0:  # skipdata pseudo-instruction: no operands to read
            prev.append(insn)
            if len(prev) > 12:
                prev.pop(0)
            continue
        for op in insn.operands:
            if op.type == capstone.x86.X86_OP_MEM and op.mem.base == capstone.x86.X86_REG_RIP:
                ea = insn.address + insn.size + op.mem.disp
                if ea == target:
                    hits += 1
                    print(f"\n--- xref #{hits} at rva 0x{insn.address:X}")
                    for p in prev[-10:]:
                        print(f"    {p.address:08X}  {p.mnemonic:8} {p.op_str}")
                    print(f"  > {insn.address:08X}  {insn.mnemonic:8} {insn.op_str}")
        prev.append(insn)
        if len(prev) > 12:
            prev.pop(0)

    print(f"\nreferences found: {hits}")
    return 0 if hits else 3


if __name__ == "__main__":
    raise SystemExit(main())
