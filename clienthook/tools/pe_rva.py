"""Minimal, stdlib-only PE reader: sections, rva -> file bytes, and what an rva lands in (read-only).

    python clienthook\\tools\\pe_rva.py <pe> [rva-hex ...]

Prints the image header facts the hook work depends on (size, ImageBase, SizeOfImage), the section
table, and for every rva on the command line the section it falls in and that section's protection
characteristics. No pefile, no capstone: this is the independent reader `tools\\unwind.py` and
`tools\\xref_call.py` build on, so a bug in a third-party parser cannot be the only witness.
"""

import struct
import sys

IMAGE_SCN_MEM_EXECUTE = 0x20000000
IMAGE_SCN_MEM_READ = 0x40000000
IMAGE_SCN_MEM_WRITE = 0x80000000


class Pe:
    def __init__(self, path):
        with open(path, "rb") as fh:
            self.data = fh.read()
        d = self.data
        if d[:2] != b"MZ":
            raise ValueError("not a PE file (no MZ)")
        e = struct.unpack_from("<I", d, 0x3C)[0]
        if d[e:e + 4] != b"PE\0\0":
            raise ValueError("not a PE file (no PE signature)")
        self.e_lfanew = e
        coff = e + 4
        self.machine, self.nsec = struct.unpack_from("<HH", d, coff)
        opt_size = struct.unpack_from("<H", d, coff + 16)[0]
        opt = coff + 20
        self.magic = struct.unpack_from("<H", d, opt)[0]
        if self.magic != 0x20B:
            raise ValueError("not PE32+ (magic 0x%X)" % self.magic)
        self.image_base = struct.unpack_from("<Q", d, opt + 24)[0]
        self.size_of_image = struct.unpack_from("<I", d, opt + 56)[0]
        self.entry_rva = struct.unpack_from("<I", d, opt + 16)[0]
        self.num_dirs = struct.unpack_from("<I", d, opt + 108)[0]
        dirs = opt + 112
        self.dirs = [struct.unpack_from("<II", d, dirs + i * 8) for i in range(min(self.num_dirs, 16))]
        sec = opt + opt_size
        self.sections = []
        for i in range(self.nsec):
            base = sec + i * 40
            name = d[base:base + 8].rstrip(b"\0").decode("latin-1")
            vsize, va, rawsize, rawptr = struct.unpack_from("<IIII", d, base + 8)
            chars = struct.unpack_from("<I", d, base + 36)[0]
            self.sections.append(
                {"name": name, "va": va, "vsize": vsize, "raw": rawptr, "rawsize": rawsize, "chars": chars})

    # --- rva ---------------------------------------------------------------------------------------

    def section_of(self, rva):
        for s in self.sections:
            if s["va"] <= rva < s["va"] + max(s["vsize"], s["rawsize"]):
                return s
        return None

    def read(self, rva, n):
        s = self.section_of(rva)
        if s is None:
            raise ValueError("rva 0x%X is not in any section" % rva)
        off = s["raw"] + (rva - s["va"])
        if off + n > s["raw"] + s["rawsize"]:
            raise ValueError("rva 0x%X + %d runs past %s's raw data" % (rva, n, s["name"]))
        return self.data[off:off + n]

    def dir_rva(self, index):
        if index >= len(self.dirs):
            return 0, 0
        return self.dirs[index]

    def protection(self, s):
        bits = []
        if s["chars"] & IMAGE_SCN_MEM_READ:
            bits.append("read")
        if s["chars"] & IMAGE_SCN_MEM_WRITE:
            bits.append("write")
        if s["chars"] & IMAGE_SCN_MEM_EXECUTE:
            bits.append("exec")
        return " ".join(bits) if bits else "-"


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 2
    pe = Pe(argv[1])
    print("%s: %d B, ImageBase 0x%X, SizeOfImage 0x%X, %d sections, entry rva 0x%X"
          % (argv[1], len(pe.data), pe.image_base, pe.size_of_image, pe.nsec, pe.entry_rva))
    print("%-9s %-10s %-10s %-10s %-10s %s" % ("name", "rva", "vsize", "raw", "rawsize", "protection"))
    for s in pe.sections:
        print("%-9s 0x%08X 0x%08X 0x%08X 0x%08X %s"
              % (s["name"], s["va"], s["vsize"], s["raw"], s["rawsize"], pe.protection(s)))
    for a in argv[2:]:
        rva = int(a, 16)
        s = pe.section_of(rva)
        if s is None:
            print("rva 0x%X -> no section" % rva)
            continue
        print("rva 0x%X -> %s (%s) at file 0x%X"
              % (rva, s["name"], pe.protection(s), s["raw"] + (rva - s["va"])))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
