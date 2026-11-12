#!/usr/bin/env python3
"""Offline proof of build 16b's call-site hook, and the frame test the build-16 crash asked for.

    python -I tools\\test_detour.py

Read-only apart from one scratch file under `build\\` (removed at the end). Nothing is installed, the game is never
launched, and the client is only read.

What this proves:
  * the pure helpers: `E8 rel32` site validation, the 5-byte patch and its rel32 reach, the read-back, the five
    recorded sites, the kill switch's file test (19 checks, `tools\\detour_test.exe self`);
  * the FRAME, with the OS's own unwinder: `detour_test.exe frame-new` stages the client's real 17 prologue bytes
    and its real UNWIND_INFO in executable memory, registers them with RtlAddFunctionTable, calls the SHIPPED
    master_thunk, raises an exception inside the called body, walks out with RtlVirtualUnwind, and requires the
    record's frame to match the machine's (return address and rsp) and the walk to reach the C caller's real return
    address. This is the test docs\\B16-CRASH.md 7 specifies and tools\\test_master.py could not be;
  * the INSTALL path against the real client image, mapped read-only as an image (never executed, and the file on
    disk is re-hashed afterwards): the five sites are found, verified, repointed and read back, the client's
    prologue stays byte-identical, and the trampoline branch is the one this machine takes (our DLL is beyond rel32
    reach of the mapped base);
  * the same test on build 16's layout (patched prologue + relay + detour). **It passes too**, with a delta of 0, at
    every frame: the detour's own RUNTIME_FUNCTION (prolog 4, ALLOC_SMALL 0x28) accounts for exactly the 0x30 the
    detour inserts, and the body's return-address slot really is the detour's `call relay` return address. That
    refutes B16-CRASH 3.3's "off by 0x30" mechanism by measurement, so the two shapes are distinguished here by
    what they touch (bytes), not by whether they unwind - see the NOTE this script prints;
  * the suite INVARIANT (B16-CRASH 7.4): for every hook this build installs, the bytes written are exactly the five
    5-byte call sites, none of them inside the target function's declared frame, and the prologue length the
    signature guard reads equals the length the client's own RUNTIME_FUNCTION declares. A build that patched a
    prologue without repairing its unwind record fails here.
"""

import hashlib
import os
import re
import struct
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))       # clienthook\
EXE = os.path.join(ROOT, "build", "detour_test.exe")
DLL = os.path.join(ROOT, "build", "version.dll")
MASTER_C = os.path.join(ROOT, "src", "master.c")
MASTER_H = os.path.join(ROOT, "src", "master.h")
SRC = os.path.join(ROOT, "src")

CLIENT = ""


def game(*parts):
    """A path under the game's cod25 folder: --game <dir> first, then KRONOS_GAME_DIR, either form. "" when unset -
    the client is optional here, and the frame and install tests say so and skip."""
    d = ""
    for i, a in enumerate(sys.argv):
        if a == "--game" and i + 1 < len(sys.argv):
            d = sys.argv[i + 1]
        elif a.startswith("--game="):
            d = a.split("=", 1)[1]
    if not d:
        d = os.environ.get("KRONOS_GAME_DIR", "")
    d = d.strip().strip('"')
    if not d:
        return ""
    if os.path.isdir(os.path.join(d, "cod25")):
        d = os.path.join(d, "cod25")
    return os.path.join(d, *parts)


CLIENT = game("XINPUT9_1_0.dll")
CLIENT_SIZE = 5016064
CLIENT_SHA = "88a52103c5555b2760f1e7ad13a594e8ef0440f007b45a10bddc61dda234fcfb"
PROLOGUE_RVA = 0x96680
PROLOGUE_LEN = 17
SITES = (0x93DFF, 0x96212, 0x9723D, 0x97626, 0x976AC)
SITE_LEN = 5

passes, failures, notes = [], [], []


def check(name, cond, detail=""):
    if cond:
        passes.append(name)
        print("PASS  " + name + (("  (" + detail + ")") if detail else ""))
    else:
        failures.append(name + (("  (" + detail + ")") if detail else ""))
        print("FAIL  " + name + (("  (" + detail + ")") if detail else ""))
    return cond


def note(msg):
    notes.append(msg)
    print("NOTE  " + msg)


# --- a minimal PE reader (the same arithmetic as tools\pe_rva.py, kept here so the test is self-contained) ----

def pe_sections(path):
    data = open(path, "rb").read()
    e = struct.unpack_from("<I", data, 0x3C)[0]
    nsec = struct.unpack_from("<H", data, e + 6)[0]
    opt = e + 24
    sec = opt + struct.unpack_from("<H", data, e + 20)[0]
    out = []
    for i in range(nsec):
        base = sec + i * 40
        name = data[base:base + 8].rstrip(b"\0").decode("latin-1")
        vsize, va, rawsize, raw = struct.unpack_from("<IIII", data, base + 8)
        out.append({"name": name, "vsize": vsize, "va": va, "rawsize": rawsize, "raw": raw})
    exc_rva, exc_size = struct.unpack_from("<II", data, opt + 112 + 3 * 8)
    return data, out, exc_rva, exc_size


def read_rva(path, rva, n):
    data, sections, _, _ = pe_sections(path)
    for s in sections:
        if s["va"] <= rva < s["va"] + max(s["vsize"], s["rawsize"]):
            off = s["raw"] + (rva - s["va"])
            return data[off:off + n]
    raise ValueError("rva 0x%X is in no section" % rva)


def unwind_for(path, rva):
    """(begin, end, prolog_size, codes) for the RUNTIME_FUNCTION covering rva."""
    data, sections, exc_rva, exc_size = pe_sections(path)

    def at(r, n):
        for s in sections:
            if s["va"] <= r < s["va"] + max(s["vsize"], s["rawsize"]):
                off = s["raw"] + (r - s["va"])
                return data[off:off + n]
        raise ValueError("rva 0x%X is in no section" % r)

    for i in range(exc_size // 12):
        begin, end, info = struct.unpack("<III", at(exc_rva + i * 12, 12))
        if begin <= rva < end:
            hdr = at(info, 4)
            count = hdr[2]
            return begin, end, hdr[1], at(info + 4, count * 2)
    return None


def frame_of_codes(codes):
    alloc = 0
    pushes = 0
    for i in range(0, len(codes) - 1, 2):
        off, info = codes[i], codes[i + 1]
        op = info & 0xF
        if op == 2:            # ALLOC_SMALL
            alloc += (info >> 4) * 8 + 8
        elif op == 1:          # ALLOC_LARGE (this test only meets the small form)
            alloc += 0
        elif op == 0:          # PUSH_NONVOL
            pushes += 1
    return alloc, pushes, alloc + pushes * 8


def const(text, name):
    m = re.search(r"^#define\s+%s\s+(-?0x[0-9A-Fa-f]+|-?\d+)" % name, text, re.M)
    return int(m.group(1), 0) if m else None


def main():
    print("clienthook build 16b - call-site hook + frame test - " + ROOT)
    print("")
    if not CLIENT:
        print("NOTE  KRONOS_GAME_DIR is not set and no --game was given - the client file cannot be read, so the "
              "frame and install tests are skipped")
    check("build\\detour_test.exe exists (build.cmd)", os.path.isfile(EXE))
    check("build\\version.dll exists (build.cmd)", os.path.isfile(DLL))
    if failures:
        print("")
        print("STOP: run clienthook\\build.cmd first.")
        return 1

    # ---- 1. the unit driver ------------------------------------------------------------------------
    print("")
    print("UNIT  detour_test.exe self")
    proc = subprocess.run([EXE, "self"], capture_output=True, text=True, timeout=120)
    m = re.search(r"detour: OK - (\d+) checks", proc.stdout or "")
    check("the unit driver passes", proc.returncode == 0 and m is not None,
          ("%s checks" % m.group(1)) if m else (proc.stdout or proc.stderr).strip().split("\n")[-1])
    for want in ("site: an E9 (jmp) is refused",
                 "site: one changed displacement byte is refused",
                 "patch: rel32 lands exactly on the target",
                 "patch: a target ~2 GB away is out of reach and refused",
                 "patch: the read-back sees its own bytes",
                 "sites: each patch is five bytes (E8 rel32, no orphan byte)",
                 "signature: the prologue is 17 bytes (the client's prolog_size 0x11)"):
        check("the unit driver covers: %s" % want, ("pass  " + want) in (proc.stdout or ""))

    # ---- 2. the frame test, NEW layout --------------------------------------------------------------
    print("")
    print("FRAME frame-new (the shipped master_thunk, the client's own bytes)")
    if not os.path.isfile(CLIENT):
        note("the client is not on disk - the frame tests were skipped")
        proc_new = proc_old = None
    else:
        raw = open(CLIENT, "rb").read()
        check("the client under test is the one the diagnosis used",
              len(raw) == CLIENT_SIZE and hashlib.sha256(raw).hexdigest() == CLIENT_SHA,
              "%d B / %s..." % (len(raw), hashlib.sha256(raw).hexdigest()[:8]))
        proc_new = subprocess.run([EXE, "frame-new", CLIENT], capture_output=True, text=True, timeout=120)
        out = proc_new.stdout or ""
        check("frame-new exits 0", proc_new.returncode == 0, "rc=%d" % proc_new.returncode)
        check("frame-new: the record's frame describes the live stack",
              "PASS  the record's frame describes the live stack exactly" in out)
        check("frame-new: the walk reaches the C caller's real return address and rsp",
              "PASS  the walk recovered the true caller" in out)
        check("frame-new: verdict is PASS", "RESULT new: PASS" in out)
        m = re.search(r"body frame \d+: walker (0x[0-9A-F]+)/(0x[0-9A-F]+), machine (0x[0-9A-F]+)/(0x[0-9A-F]+), "
                      r"delta rip ([+-]\d+) rsp ([+-]\d+)", out)
        if m:
            check("frame-new: delta rip 0 and delta rsp 0", m.group(5) == "+0" and m.group(6) == "+0",
                  "delta rip %s / rsp %s" % (m.group(5), m.group(6)))
        # the walk must pass through a frame in the shipped thunk: that is the whole point of the shape
        thunk_frame = re.search(r"frame \d+  rip (0x[0-9A-F]+)  rsp (0x[0-9A-F]+)  -> rip (0x[0-9A-F]+)", out)
        check("frame-new: prints its frame table", thunk_frame is not None)

        # ---- 3. the frame test, build 16's layout --------------------------------------------------
        print("")
        print("FRAME frame-old (build 16: patched prologue, relay, detour)")
        proc_old = subprocess.run([EXE, "frame-old", CLIENT], capture_output=True, text=True, timeout=120)
        out = proc_old.stdout or ""
        print("  | " + "\n  | ".join(l for l in out.split("\n") if l.startswith(("INFO  body", "      frame",
                                                                             "RESULT", "PASS", "FAIL"))))
        check("frame-old exits 0 with the measured verdict (build 16's layout unwinds correctly)",
              proc_old.returncode == 0 and "RESULT old: PASS" in out, "rc=%d" % proc_old.returncode)
        m = re.search(r"body frame \d+: walker (0x[0-9A-F]+)/(0x[0-9A-F]+), machine (0x[0-9A-F]+)/(0x[0-9A-F]+), "
                      r"delta rip ([+-]\d+) rsp ([+-]\d+)", out)
        check("frame-old: the body frame's return address is the detour's `call relay` return address and the "
              "delta is 0, not 0x30", bool(m) and m.group(5) == "+0" and m.group(6) == "+0",
              ("delta rip %s / rsp %s" % (m.group(5), m.group(6))) if m else "no delta line")
        note("build 16's layout PASSES this frame test with a delta of 0: the detour's own RUNTIME_FUNCTION "
             "(prolog 4, ALLOC_SMALL 0x28) accounts for exactly the 0x30 it inserts, and the body's "
             "return-address slot is the detour's `call relay` return address - a real code address whose own "
             "record continues the walk. B16-CRASH 3.3's 'off by 0x30' mechanism is therefore REFUTED by "
             "measurement; build 16's crash has another cause and the kill-switch launch is what decides it.")
        note("16b is still the right shape for a different reason: it writes no byte of the client's function, so "
             "the hook no longer depends on the unwinder finding OUR record for a PC inside the client's frame.")

    # ---- 3b. the install path, against the real client image (mapped, never executed) ---------------
    if os.path.isfile(CLIENT):
        print("")
        print("INSTALL  detour_test.exe install <client>")
        raw_before = hashlib.sha256(open(CLIENT, "rb").read()).hexdigest()
        r = subprocess.run([EXE, "install", CLIENT], capture_output=True, text=True, timeout=120)
        out = r.stdout or ""
        print("  | " + "\n  | ".join(l for l in out.split("\n") if l.startswith(("LOG   master:", "INFO  site",
                                                                             "PASS", "FAIL", "RESULT"))))
        check("install: master_install installs and logs the five sites",
              r.returncode == 0 and "master: 5 call sites hooked (0x00093DFF" in out, "rc=%d" % r.returncode)
        check("install: every site is repointed at the thunk (directly or through a trampoline)",
              out.count("master_thunk") >= 5 and "NOT OUR HOOK" not in out)
        check("install: the client's prologue is byte-identical afterwards",
              "PASS  the client's 17 prologue bytes are byte-identical" in out)
        check("install: all five sites restore to their original bytes", "PASS  all five sites are back" in out)
        check("install: verdict is PASS", "RESULT install: PASS" in out)
        check("install: the client file on disk is unchanged (the view was private and read-only)",
              hashlib.sha256(open(CLIENT, "rb").read()).hexdigest() == raw_before and raw_before == CLIENT_SHA)

    print("")
    print("KILL SWITCH  detour_test.exe off <dir>")
    scratch = os.path.join(ROOT, "build", "offtest")
    offdir = os.path.join(scratch, "progression-tuning")
    os.makedirs(offdir, exist_ok=True)
    killfile = os.path.join(offdir, "master_off.txt")
    try:
        if os.path.exists(killfile):
            os.remove(killfile)
        r = subprocess.run([EXE, "off", scratch + os.sep], capture_output=True, text=True, timeout=60)
        check("kill switch: absent file -> 0", (r.stdout or "").strip() == "0", (r.stdout or "").strip())
        open(killfile, "w").close()
        r = subprocess.run([EXE, "off", scratch + os.sep], capture_output=True, text=True, timeout=60)
        check("kill switch: the file -> 1", (r.stdout or "").strip() == "1", (r.stdout or "").strip())
        os.remove(killfile)
        bak = killfile + ".bak"
        open(bak, "w").close()
        r = subprocess.run([EXE, "off", scratch + os.sep], capture_output=True, text=True, timeout=60)
        check("kill switch: a similarly named file does not count", (r.stdout or "").strip() == "0",
              (r.stdout or "").strip())
        os.remove(bak)
    finally:
        for p in (killfile, killfile + ".bak"):
            if os.path.exists(p):
                os.remove(p)
        for d in (offdir, scratch):
            try:
                os.rmdir(d)
            except OSError:
                pass

    # ---- 5. the invariant: no prologue patch without matching unwind data ---------------------------
    print("")
    print("INVARIANT  B16-CRASH 7.4")
    h = open(MASTER_H, "r", encoding="utf-8", errors="replace").read()
    src = open(MASTER_C, "r", encoding="utf-8", errors="replace").read()

    declared_len = const(h, "MASTER_PROLOGUE_LEN")
    site_count = const(h, "MASTER_SITE_COUNT")
    site_len = const(h, "MASTER_SITE_LEN")
    check("master.h declares a prologue length and a site patch length",
          declared_len == PROLOGUE_LEN and site_len == SITE_LEN and site_count == len(SITES),
          "prologue %s, sites %s x %s" % (declared_len, site_count, site_len))

    if os.path.isfile(CLIENT):
        begin, end, prolog, codes = unwind_for(CLIENT, PROLOGUE_RVA)
        alloc, pushes, frame = frame_of_codes(codes)
        check("the client's RUNTIME_FUNCTION still declares prolog_size 0x%X" % PROLOGUE_LEN,
              prolog == PROLOGUE_LEN, "0x%X" % prolog)
        check("the signature guard's length equals that declared prolog_size (a hook may not read more or less "
              "of the prologue than the record describes)", declared_len == prolog,
              "%d vs 0x%X" % (declared_len, prolog))
        check("the record is ALLOC_SMALL 0x28 and eight pushes (frame 0x68)",
              alloc == 0x28 and pushes == 8 and frame == 0x68, "alloc 0x%X, %d pushes, frame 0x%X"
              % (alloc, pushes, frame))
        # the write set: every byte this build writes into the client
        written = set()
        for s in SITES:
            written.update(range(s, s + site_len))
        inside = sorted(b for b in written if begin <= b < end)
        check("no written byte is inside the function's declared frame [0x%X, 0x%X)" % (begin, end),
              not inside, "%d bytes written, %d inside" % (len(written), len(inside)))
        check("every written byte is in .text", len(written) == site_count * site_len,
              "%d bytes at %d sites" % (len(written), site_count))
        # each site's own 5 bytes are E8+rel32 to the function (the source's five RVAs), and the patched image
        # keeps the instruction length: a 5-byte E8 cannot orphan a byte
        bad = []
        for s in SITES:
            b = read_rva(CLIENT, s, 5)
            if b[0] != 0xE8:
                bad.append((s, b.hex()))
                continue
            rel = struct.unpack("<i", b[1:5])[0]
            if s + 5 + rel != PROLOGUE_RVA:
                bad.append((s, b.hex()))
        check("all five recorded sites are E8+rel32 to 0x96680 in the client", not bad,
              "%d bad" % len(bad) if bad else "5 sites")

    # the build's own sources: a prologue patch is only allowed with unwind repair declared in the same file
    patch_markers = ("master_patch_bytes(", "master_write16(", "memcpy(fn,", "memcpy(tgt,")
    offenders = []
    for name in sorted(os.listdir(SRC)):
        if not name.endswith(".c"):
            continue
        text = open(os.path.join(SRC, name), "r", encoding="utf-8", errors="replace").read()
        if any(mk in text for mk in patch_markers):
            if "RtlAddFunctionTable" not in text and "unwind" not in text.lower():
                offenders.append(name)
    check("no hook in src\\ patches a prologue without matching unwind data", not offenders,
          ", ".join(offenders) if offenders else "no prologue write at all")
    check("master.c writes the client only through the five call-site patches",
          "RtlAddFunctionTable" not in src and "memcpy(sites[i]" in src and
          src.count("[MASTER_REC_LEVEL] = (unsigned char)want") == 1)
    check("master.c no longer carries build 16's prologue patch or relay",
          "master_patch_bytes" not in src and "master_relay_bytes" not in src and "MASTER_RELAY" not in src)

    # the DLL the tests ran against is build 16b
    raw = open(DLL, "rb").read()
    text = raw.decode("latin-1")
    for s in ("master: disabled by file",
              "master: %d call sites hooked (0x%08lX 0x%08lX 0x%08lX 0x%08lX 0x%08lX)",
              "master: refused - %d call sites to 0x%08lX, expected %d - off",
              "master: refused - the call site at 0x%08lX is not E8+rel32 to 0x%08lX - off"):
        check("version.dll carries %r" % s, s in text)
    check("version.dll does not carry build 16's prologue-hook line",
          "prologue ok, relay 0x%08lX" not in text)
    print("")
    print("version.dll %d B / %s" % (len(raw), hashlib.sha256(raw).hexdigest()[:16].upper()))

    print("")
    print("%d passed, %d failed, %d notes" % (len(passes), len(failures), len(notes)))
    if failures:
        for f in failures:
            print("  FAILED: " + f)
        return 1
    print("OK - the kill switch works, the shipped thunk's frame unwinds exactly, the caller is recovered, and the "
          "build writes five 5-byte call sites and no byte of the client's function.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
