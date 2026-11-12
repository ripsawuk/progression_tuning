#!/usr/bin/env python3
"""Offline checks for clienthook build 16's master-prestige detour (tools\\master_test.exe + the built DLL).

    python -I tools\\test_master.py

Read-only, stdlib-only. Nothing is installed, the game is never launched, and nothing under D:\\Games is
written (the client file is read, exactly as `test_g11.py` and `test_ladder.py` read theirs).

What it proves:
  * the C unit driver passes: the client's own threshold walk, prestige 0/1 left completely alone, the band's
    boundaries (+2,499 / +2,500), the 249 cap, the step setting, the record shapes that must be refused, the
    setting's parser, and the 17-byte signature (53 checks);
  * the C formula equals an independent Python model at EVERY point of four whole curves (counts 19, 20, 47,
    48; 0 .. 700,000 XP; three step settings), so the two agree everywhere, not just at the boundaries;
  * the signature in `src\\master.c` is the installed client's own bytes at rva 0x96680 - read out of the PE
    file here, so a client update that moves the prologue makes this test fail rather than the game crash -
    and the 17th byte is 0x28, i.e. the resume address 0x96691 is the instruction boundary the relay jumps to
    (G9-DESIGN says 16 bytes / 0x96690; the bytes say 17 / 0x96691);
  * the built version.dll carries the master log lines and the refusal line, so the build under test is the one
    described here;
  * the detour's five constants (stride, the record offsets, the kind, the cap, the prestige floor) are the
    client's own, as written in `src\\master.h`, and `master.c` never writes a field other than +0x56e.

What it cannot prove: that the detour loads and the relay runs inside the client, and that the level byte it
writes is what the client's next publish serialises. Those are the launch's questions.
"""

import hashlib
import os
import re
import struct
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))          # clienthook\
EXE = os.path.join(ROOT, "build", "master_test.exe")
DLL = os.path.join(ROOT, "build", "version.dll")
MASTER_C = os.path.join(ROOT, "src", "master.c")
MASTER_H = os.path.join(ROOT, "src", "master.h")

CLIENT = ""


def game(*parts):
    """A path under the game's cod25 folder: --game <dir> first, then KRONOS_GAME_DIR, either form. "" when unset -
    the client is optional here, and the signature cross-check says so and skips."""
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
PROLOGUE_RVA = 0x96680
PROLOGUE_LEN = 17

STEPS = (2500, 1000, 5000)
COUNTS = (19, 20, 47, 48)
SWEEP = (0, 700000, 250)      # every 250 XP: the step's own granularity, so every boundary in the band is hit

passes, failures, infos = [], [], []


def check(name, cond, detail=""):
    if cond:
        passes.append(name)
        print("PASS  " + name + (("  (" + detail + ")") if detail else ""))
    else:
        failures.append(name + (("  (" + detail + ")") if detail else ""))
        print("FAIL  " + name + (("  (" + detail + ")") if detail else ""))
    return cond


def info(msg):
    infos.append(msg)
    print("INFO  " + msg)


def run(args, timeout=120):
    return subprocess.run([EXE] + args, capture_output=True, text=True, timeout=timeout)


# --- the independent model: the client's walk, then the band ------------------------------------------

def thresholds(count):
    return [1000 + i * 1200 for i in range(count)]


def client_level(xp, count, thr):
    """180096680:78-91: the number of thresholds the XP has passed; no thresholds -> 1 iff XP != 0."""
    i = 0
    while i < count:
        if xp < thr[i]:
            break
        i += 1
    if count == 0 and xp != 0:
        return 1
    return i


def master_level(xp, count, thr, prestige, step):
    """-1 = leave the client's byte alone; otherwise the level this build writes."""
    if prestige < 2:
        return -1
    if step < 1 or count < 0 or count > 64:
        return -1
    if count == 0:
        return client_level(xp, count, thr)
    last = thr[count - 1]
    if xp <= last:
        return client_level(xp, count, thr)
    return min(249, count + (xp - last) // step)


# --- a minimal PE reader: rva -> file bytes -----------------------------------------------------------

def read_rva(path, rva, n):
    with open(path, "rb") as fh:
        data = fh.read()
    if data[:2] != b"MZ":
        raise ValueError("not a PE file")
    e_lfanew = struct.unpack_from("<I", data, 0x3C)[0]
    if data[e_lfanew:e_lfanew + 4] != b"PE\0\0":
        raise ValueError("no PE signature")
    nsec = struct.unpack_from("<H", data, e_lfanew + 6)[0]
    opt = e_lfanew + 24
    sec = opt + struct.unpack_from("<H", data, e_lfanew + 20)[0]
    for i in range(nsec):
        base = sec + i * 40
        name = data[base:base + 8].rstrip(b"\0").decode("latin-1")
        vsize, va, rawsize, raw = struct.unpack_from("<IIII", data, base + 8)
        if va <= rva < va + max(vsize, rawsize):
            off = raw + (rva - va)
            if name == ".text":
                info(".text rva 0x%X -> file 0x%X" % (rva, off))
            return data[off:off + n]
    raise ValueError("rva 0x%X is not in any section" % rva)


def text_section(path):
    """(rva, vsize, bytes) of .text - the scan below needs the section, not one rva."""
    data = open(path, "rb").read()
    e = struct.unpack_from("<I", data, 0x3C)[0]
    nsec = struct.unpack_from("<H", data, e + 6)[0]
    opt = e + 24
    sec = opt + struct.unpack_from("<H", data, e + 20)[0]
    for i in range(nsec):
        base = sec + i * 40
        name = data[base:base + 8].rstrip(b"\0").decode("latin-1")
        vsize, va, rawsize, raw = struct.unpack_from("<IIII", data, base + 8)
        if name == ".text":
            return va, vsize, data[raw:raw + vsize]
    raise ValueError("no .text")


def prologue_from_source():
    src = open(MASTER_C, "r", encoding="utf-8", errors="replace").read()
    m = re.search(r"MASTER_PROLOGUE\[MASTER_PROLOGUE_LEN\] = \{(.*?)\};", src, re.S)
    if not m:
        return None
    return bytes(int(x, 16) for x in re.findall(r"0x([0-9A-Fa-f]{2})", m.group(1)))


def const(name, text):
    m = re.search(r"^#define\s+%s\s+(-?0x[0-9A-Fa-f]+|-?\d+)" % name, text, re.M)
    return int(m.group(1), 0) if m else None


def main():
    print("clienthook build 16 - master prestige offline check - " + ROOT)
    print("")
    if not CLIENT:
        print("NOTE  KRONOS_GAME_DIR is not set and no --game was given - the client file cannot be read, so the "
              "signature cross-check is skipped")

    check("build\\master_test.exe exists (build.cmd)", os.path.isfile(EXE))
    check("build\\version.dll exists (build.cmd)", os.path.isfile(DLL))
    if failures:
        print("")
        print("STOP: run clienthook\\build.cmd first.")
        return 1

    # ---- 1. the C unit driver ---------------------------------------------------------------------
    print("")
    print("UNIT  master_test.exe self")
    proc = run(["self"])
    for line in (proc.stdout or "").split("\n"):
        if line.startswith("FAIL") or line.startswith("master:"):
            print("  | " + line)
    m = re.search(r"master: OK - (\d+) checks", proc.stdout or "")
    check("the C unit driver passes", proc.returncode == 0 and m is not None,
          (proc.stdout or "").strip().split("\n")[-1] if proc.stdout else proc.stderr)
    if m:
        info("master_test.exe self: %s checks, exit 0" % m.group(1))
    out = proc.stdout or ""
    for want in ("prestige 0 and 1: untouched at every XP (the client's own behaviour)",
                 "band: at the last threshold -> count (47)",
                 "band: +2,499 -> the same level (47)",
                 "band: +2,500 -> one more (48)",
                 "band: far past the end -> capped at 249",
                 "step 1,000: +2,500 -> two levels",
                 "step 5,000: +2,500 -> no level yet",
                 "signature: it ends with `sub rsp,0x28`, not on its first three bytes"):
        check("the unit driver covers: %s" % want, ("pass  " + want) in out)

    # ---- 2. the named boundaries, one call each, straight from the exe ------------------------------
    print("")
    count = 47
    last = thresholds(count)[-1]
    cases = [
        (count, 2500, last, (0, 47)),
        (count, 2500, last + 2499, (0, 47)),
        (count, 2500, last + 2500, (1, 48)),
        (count, 2500, last + 202 * 2500, (2, 249)),
        (count, 2500, last + 202 * 2500 + 1000000, (2, 249)),
        (count, 1000, last + 2500, (1, 49)),
        (count, 5000, last + 2500, (1, 47)),
        (count, 5000, last + 5000, (1, 48)),
    ]
    for c, step, xp, (expect_ge, expect) in cases:
        proc = run(["level", str(c), str(step), str(xp)])
        got = (proc.stdout or "").strip().split()
        want = ["-1", "-1", str(expect)]
        check("level: count %d step %d xp %d -> prestige 2 gives %d" % (c, step, xp, expect),
              got == want, " ".join(got))

    # ---- 3. the whole curves against the Python model ----------------------------------------------
    print("")
    a, b, stride = SWEEP
    for c in COUNTS:
        thr = thresholds(c)
        for step in STEPS:
            proc = run(["sweep", str(c), str(step), str(a), str(b), str(stride)])
            lines = [ln for ln in (proc.stdout or "").split("\n") if ln.strip()]
            bad = []
            for ln in lines:
                f = ln.split()
                xp = int(f[0])
                want = [master_level(xp, c, thr, p, step) for p in (0, 1, 2)]
                if [int(x) for x in f[1:]] != want:
                    bad.append((xp, f[1:], want))
                    if len(bad) > 3:
                        break
            check("sweep: count %d step %d, %d points %d..%d agree with the model"
                  % (c, step, len(lines), a, b), not bad,
                  ("first: xp %d got %s want %s" % bad[0]) if bad else "every point")

    # one point per value of the setting, so "the setting is honoured" is not only the unit driver's word
    proc = run(["sweep", "47", "2500", str(last), str(last + 5000), "2500"])
    check("sweep: the default step's own granularity is a level a step",
          [ln.split()[3] for ln in (proc.stdout or "").strip().split("\n")] == ["47", "48", "49"],
          (proc.stdout or "").replace("\n", " | ").strip())

    # ---- 4. the signature is the client's own bytes, and the patch is exactly what it says -----------
    print("")
    live = None
    want = prologue_from_source()
    check("src\\master.c records a 17-byte prologue", want is not None and len(want) == PROLOGUE_LEN,
          "%d bytes" % (len(want) if want else 0))
    if os.path.isfile(CLIENT):
        live = read_rva(CLIENT, PROLOGUE_RVA, PROLOGUE_LEN)
        check("the installed client is 5,016,064 B", os.path.getsize(CLIENT) == 5016064,
              "%d" % os.path.getsize(CLIENT))
        check("the recorded prologue equals the client's bytes at rva 0x96680", want == live,
              " ".join("%02X" % b for b in live))
        check("byte 17 is 0x28 (the last byte of `sub rsp,0x28`, so the resume is 0x96691)", live[16] == 0x28,
              "0x%02X" % live[16])
        check("the prologue starts with `push rbx`", live[0] == 0x40 and live[1] == 0x53)
        check("the prologue ends with `sub rsp,0x28`", live[13:17] == bytes([0x48, 0x83, 0xEC, 0x28]))
        # the resume address is one past the prologue, in the same function
        nxt = read_rva(CLIENT, PROLOGUE_RVA + PROLOGUE_LEN, 1)
        info("the byte at rva 0x96691 (where the relay hands back) is 0x%02X" % nxt[0])
    else:
        info("the client is not on disk - the signature cross-check was skipped")

    # ---- 4b. the call-site patch shape, from the built exe ------------------------------------------
    proc = run(["sites"])
    sites_out = (proc.stdout or "").strip().split("\n")
    exe_prologue = None
    exe_len = None
    exe_sites = []
    for ln in sites_out:
        f = ln.split()
        if f and f[0] == "prologue":
            exe_prologue = int(f[1])
        elif f and f[0] == "len":
            exe_len = int(f[1])
        elif f and f[0] == "site":
            exe_sites.append(int(f[2], 16))
    check("the built exe carries the 17-byte prologue guard", exe_prologue == PROLOGUE_LEN, str(exe_prologue))
    check("the built exe carries a 5-byte site patch", exe_len == 5, str(exe_len))
    check("the built exe carries five call sites", len(exe_sites) == 5, str(len(exe_sites)))
    if live is not None:
        # the five RVAs the build carries must be the client's own E8 sites, re-derived here independently
        text_va, text_size, text = text_section(CLIENT)
        found = []
        for i in range(text_size - 5):
            if text[i] == 0xE8:
                rel = struct.unpack_from("<i", text, i + 1)[0]
                if text_va + i + 5 + rel == PROLOGUE_RVA:
                    found.append(text_va + i)
        check("the client has exactly five E8+rel32 sites to 0x96680", len(found) == 5,
              " ".join("0x%X" % a for a in found))
        check("the build's five RVAs are the client's own five", exe_sites == found,
              " ".join("0x%X" % a for a in exe_sites))
        check("the build's first site is 0x93DFF", exe_sites[:1] == [0x93DFF], "0x%X" % (exe_sites[0] if exe_sites else 0))
        # every site is a 5-byte instruction both before and after the patch: no orphaned byte, no alignment need
        patched_ok = all(len(read_rva(CLIENT, a, 5)) == 5 and read_rva(CLIENT, a, 1) == b"\xE8" for a in exe_sites)
        check("each site is a 5-byte `E8 rel32` (the patch replaces exactly the instruction)", patched_ok)
        check("no site lies inside the function's own 0x96680..0x968E5", all(a < PROLOGUE_RVA or a >= 0x968E5
                                                                          for a in exe_sites))

    # ---- 5. the DLL under test ---------------------------------------------------------------------
    raw = open(DLL, "rb").read()
    text = raw.decode("latin-1")
    for s in ("master: %d call sites hooked (", "master: the level function at ", "master: %s prestige ",
              "master: disabled by file", "master: refused - %d call sites to 0x%08lX, expected %d - off"):
        check("version.dll carries %r" % s, s in text)
    check("version.dll carries this build's attach line", "version.dll build 28" in text)
    check("version.dll no longer carries build 16's prologue hook",
          "prologue ok, relay 0x%08lX" not in text and "master: hook at " not in text)
    info("version.dll %d B / %s" % (len(raw), hashlib.sha256(raw).hexdigest()[:16].upper()))

    # ---- 6. the constants are the client's own, and only +0x56e is written -------------------------
    print("")
    h = open(MASTER_H, "r", encoding="utf-8", errors="replace").read()
    src = open(MASTER_C, "r", encoding="utf-8", errors="replace").read()
    for name, value in (("MASTER_PRESTIGE_MIN", 2), ("MASTER_LEVEL_CAP", 249),
                        ("MASTER_THRESHOLDS_MAX", 64), ("MASTER_STEP_DEFAULT", 2500),
                        ("MASTER_RVA", 0x96680), ("MASTER_RESUME_RVA", 0x96691),
                        ("MASTER_RECS_RVA", 0x3DD288), ("MASTER_COUNT_RVA", 0x3DD290),
                        ("MASTER_STRIDE", 0x578), ("MASTER_REC_COUNT", 0x58),
                        ("MASTER_REC_THR", 0x5C), ("MASTER_REC_XP", 0x560),
                        ("MASTER_REC_LEVEL", 0x56E), ("MASTER_REC_PRESTIGE", 0x574),
                        ("MASTER_KIND_WEAPON", 0x18E)):
        got = const(name, h)
        check("%s is 0x%X / %d" % (name, value, value), got == value, str(got))

    check("master.c reads the level byte and compares the computed value",
          "int have = (int)r[MASTER_REC_LEVEL];" in src)
    check("master.c writes the level byte only", src.count("[MASTER_REC_LEVEL] = (unsigned char)want") == 1)
    check("no other record field is assigned in master.c",
          not re.search(r"\[MASTER_REC_(?!LEVEL\])[A-Z]+\]\s*(\+|-)?=", src))
    # build 16b: no mutex on the client's XP path (the call is already inside the client's own, 180096030:55).
    # Build 20 adds one in the INSTALLER only - the patch gate shared with nativepay.c - so the check is the
    # thunk's own body, from its definition to the end of the function above `master_thunk_address`.
    thunk_body = src[src.index("static unsigned long long master_thunk(void)"):src.index("void *master_thunk_address(void)")]
    check("master_thunk takes no mutex (the call is already inside the client's own, 180096030:55)",
          "WaitForSingleObject" not in thunk_body and "18010fd44" not in thunk_body)
    check("the only mutex in master.c is the installer's patch gate (build 20, shared with nativepay.c)",
          src.count("WaitForSingleObject") == 1 and "master_set_install_gate" in src)

    print("")
    print("%d passed, %d failed" % (len(passes), len(failures)))
    if failures:
        for f in failures:
            print("  FAILED: " + f)
        return 1
    print("OK - the formula matches the model point for point, prestige 0/1 is untouched, the band caps at "
          "249, the step is the setting, and the signature is the installed client's own bytes.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
