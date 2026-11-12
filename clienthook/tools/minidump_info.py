"""Read a Windows minidump (read-only): modules, the exception record, the threads, and a stack walk.

    python clienthook\\tools\\minidump_info.py <dump> [--stack <thread-index>] [--words N]

Why it exists: build 20's diagnosis (`progression-tuning\\docs\\DIAG-LAUNCH11-20261110.md` 1.1) needed
to know which address in our image a thread was executing when `version.dll` had already been
unloaded, and the WER report only carries a bare offset. A minidump carries the module list (and so
proves the module is GONE from it), the exception record, and the raw stack of every thread.

No third-party module: the structures are Microsoft's published MINIDUMP_* layout, parsed by hand.
Streams read: SystemInfo(7), ModuleList(4), ThreadList(3), Exception(6), MemoryList(5)/Memory64List(9).
"""
import struct
import sys

STREAM_NAMES = {
    3: "ThreadList",
    4: "ModuleList",
    5: "MemoryList",
    6: "Exception",
    7: "SystemInfo",
    9: "Memory64List",
    15: "MiscInfo",
}


class Dump:
    def __init__(self, path):
        with open(path, "rb") as fh:
            self.data = fh.read()
        if self.data[:4] != b"MDMP":
            raise SystemExit("not a minidump (no MDMP signature)")
        (self.version, self.nstreams, self.stream_dir_rva, self.checksum,
         self.timestamp, self.flags) = struct.unpack_from("<IIIIII", self.data, 4)
        self.streams = {}
        for i in range(self.nstreams):
            off = self.stream_dir_rva + i * 12
            stype, size, rva = struct.unpack_from("<III", self.data, off)
            self.streams[stype] = (size, rva)

    def unpack(self, fmt, rva):
        return struct.unpack_from(fmt, self.data, rva)

    # -- system info ---------------------------------------------------------------------------
    def system_info(self):
        size, rva = self.streams[7]
        arch, level, rev, ncpu, product, major, minor, build, platform, csd_rva = \
            struct.unpack_from("<HHHBBIIIII", self.data, rva)
        return {"architecture": arch, "cpus": ncpu, "build": build,
                "major": major, "minor": minor, "platform": platform}

    # -- modules -------------------------------------------------------------------------------
    def modules(self):
        size, rva = self.streams[4]
        count = struct.unpack_from("<I", self.data, rva)[0]
        out = []
        for i in range(count):
            off = rva + 4 + i * 108
            base, size_of_image, checksum, timestamp, name_rva = struct.unpack_from("<QIIII", self.data, off)
            nlen = struct.unpack_from("<I", self.data, name_rva)[0]
            raw = self.data[name_rva + 4:name_rva + 4 + nlen]
            name = raw.decode("utf-16-le", "replace")
            out.append({"base": base, "size": size_of_image, "name": name})
        return out

    # -- threads -------------------------------------------------------------------------------
    def threads(self):
        size, rva = self.streams[3]
        count = struct.unpack_from("<I", self.data, rva)[0]
        out = []
        for i in range(count):
            off = rva + 4 + i * 48
            tid, suspend, prio_class, prio, teb, stack_start, stack_size, stack_rva, ctx_size, ctx_rva = \
                struct.unpack_from("<IIIIQQIIII", self.data, off)
            out.append({"tid": tid, "stack_start": stack_start, "stack_size": stack_size,
                        "stack_rva": stack_rva, "ctx_rva": ctx_rva, "ctx_size": ctx_size})
        return out

    # -- exception -----------------------------------------------------------------------------
    def exception(self):
        if 6 not in self.streams:
            return None
        size, rva = self.streams[6]
        tid, align = struct.unpack_from("<II", self.data, rva)
        stream_rva = rva + 8
        code, flags, inner, addr = struct.unpack_from("<IIQQ", self.data, stream_rva)
        nparams = struct.unpack_from("<I", self.data, stream_rva + 24)[0]
        # ExceptionInformation[15] starts at +32: NumberParameters is a ULONG at +24 and the array is
        # 8-aligned, so four padding bytes sit between them (verified: a read at +28 splits two params).
        params = struct.unpack_from("<15Q", self.data, stream_rva + 32)[:nparams]
        thread_ctx_rva = struct.unpack_from("<I", self.data, rva + 8 + 80 + 16 + 4)[0]
        return {"tid": tid, "code": code, "flags": flags, "address": addr,
                "params": params, "context_rva": thread_ctx_rva}

    # -- context (AMD64) -----------------------------------------------------------------------
    def context_amd64(self, rva):
        # CONTEXT for x64: 6 segments (WORD) + EFlags, then six 16-byte registers, then
        # Rip at offset 0xF8.
        regs = {}
        off = rva
        regs["Rax"], regs["Rcx"], regs["Rdx"], regs["Rbx"] = struct.unpack_from("<QQQQ", self.data, off + 0x78)
        regs["Rsp"], regs["Rbp"], regs["Rsi"], regs["Rdi"] = struct.unpack_from("<QQQQ", self.data, off + 0x98)
        regs["R8"], regs["R9"], regs["R10"], regs["R11"] = struct.unpack_from("<QQQQ", self.data, off + 0xB8)
        regs["R12"], regs["R13"], regs["R14"], regs["R15"] = struct.unpack_from("<QQQQ", self.data, off + 0xD8)
        regs["Rip"] = struct.unpack_from("<Q", self.data, off + 0xF8)[0]
        regs["Rsp0"] = regs["Rsp"]
        return regs


def owner_of(modules, addr):
    for m in modules:
        if m["base"] <= addr < m["base"] + m["size"]:
            return m["name"] + " +0x%X" % (addr - m["base"])
    return None


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    path = sys.argv[1]
    stack_thread = None
    words = 64
    i = 2
    while i < len(sys.argv):
        if sys.argv[i] == "--stack":
            stack_thread = int(sys.argv[i + 1])
            i += 2
        elif sys.argv[i] == "--words":
            words = int(sys.argv[i + 1])
            i += 2
        else:
            print(__doc__)
            return 2

    d = Dump(path)
    print("streams:", ", ".join("%s (%d)" % (STREAM_NAMES.get(k, k), k) for k in sorted(d.streams)))
    if 7 in d.streams:
        print("system:", d.system_info())
    mods = d.modules() if 4 in d.streams else []
    print("modules: %d" % len(mods))
    for m in mods:
        print("  %016X %8X  %s" % (m["base"], m["size"], m["name"]))

    ex = d.exception()
    if ex:
        print("\nexception: thread %d, code 0x%08X, address 0x%016X" % (ex["tid"], ex["code"], ex["address"]))
        print("  params: " + " ".join("0x%X" % p for p in ex["params"]))
        who = owner_of(mods, ex["address"])
        print("  address owner: %s" % (who or "NONE OF THE LOADED MODULES (unmapped)"))

    threads = d.threads() if 3 in d.streams else []
    print("\nthreads: %d" % len(threads))
    for idx, t in enumerate(threads):
        ctx = d.context_amd64(t["ctx_rva"])
        rip = ctx["Rip"]
        who = owner_of(mods, rip)
        mark = " <- EXCEPTION" if ex and t["tid"] == ex["tid"] else ""
        print("  [%d] tid %d  rip 0x%016X %-55s%s" % (idx, t["tid"], rip, who or "(unmapped)", mark))

    if stack_thread is not None:
        t = threads[stack_thread]
        print("\nstack of thread [%d] tid %d:" % (stack_thread, t["tid"]))
        raw = d.data[t["stack_rva"]:t["stack_rva"] + t["stack_size"]]
        ctx = d.context_amd64(t["ctx_rva"])
        sp = ctx["Rsp"]
        base = t["stack_start"]
        for n in range(min(words, len(raw) // 8)):
            addr = base + n * 8
            val = struct.unpack_from("<Q", raw, n * 8)[0]
            who = owner_of(mods, val)
            hint = ""
            if who:
                hint = " -> " + who
            note = ""
            if addr == sp:
                note = "  <- rsp"
            print("  %016X  %016X%s%s" % (addr, val, hint, note))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
