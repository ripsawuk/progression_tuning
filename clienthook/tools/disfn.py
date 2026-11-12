"""Disassemble a byte range of a PE's .text (read-only).

    python clienthook\\tools\\disfn.py <pe> <start-rva-hex> <end-rva-hex>

Prints address, bytes, mnemonic and operands; `lea` targets that land in .rdata are annotated with the
ASCII they point at, which is what makes a routine readable.
"""
import sys

import capstone
import pefile


def main():
    if len(sys.argv) < 4:
        print(__doc__)
        return 2
    path = sys.argv[1]
    start = int(sys.argv[2], 16)
    end = int(sys.argv[3], 16)

    pe = pefile.PE(path, fast_load=True)
    data = pe.__data__
    text = next(s for s in pe.sections if s.Name.startswith(b".text"))

    def read(rva, n):
        off = text.PointerToRawData + (rva - text.VirtualAddress)
        return data[off:off + n]

    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)
    md.detail = True
    md.skipdata = True

    code = read(start, end - start)
    for insn in md.disasm(code, start):
        note = ""
        if insn.id != 0:
            for op in insn.operands:
                if op.type == capstone.x86.X86_OP_MEM and op.mem.base == capstone.x86.X86_REG_RIP:
                    ea = insn.address + insn.size + op.mem.disp
                    raw = None
                    for s in pe.sections:
                        if s.VirtualAddress <= ea < s.VirtualAddress + s.SizeOfRawData:
                            off = s.PointerToRawData + (ea - s.VirtualAddress)
                            raw = data[off:off + 48]
                            break
                    if raw:
                        cut = raw.split(b"\x00")[0]
                        if cut and all(0x20 <= c < 0x7F for c in cut[:24]) and len(cut) >= 3:
                            note = f"   ; \"{cut[:40].decode('ascii', 'replace')}\""
                        else:
                            note = f"   ; rva 0x{ea:X}"
        print(f"{insn.address:08X}  {insn.bytes.hex():<20} {insn.mnemonic:8} {insn.op_str}{note}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
