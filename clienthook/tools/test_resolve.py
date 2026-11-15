"""Offline proof of the resolver - build 25's version tolerance. Read-only with respect to the game: the client
file is read, and every damaged copy it needs is made in %TEMP%.

    clienthook\\tools\\resolve_check\\resolve_check.c   the driver: the SHIPPED src\\resolve.c over a file on disk
    clienthook\\tools\\test_resolve.py                 this file: the assertions

WHAT IT PROVES.
  1. On the installed client every one of the ten patterns matches exactly once, and every one of the nineteen
     addresses the patterns find (or derive from what they found) is the constant the release used - so the
     resolver changes nothing about the build that is installed today.
  2. The two addresses with no pattern (`zm_ch_ver`'s dvar_t slot and the string-value slot) resolve to their
     constants only when the caller has established the identification triple (size, sha256, SizeOfImage), and
     are unresolved otherwise - and then g11 and pubxp are the only features that turn off.
  3. A copy with one byte flipped inside one pattern leaves that one symbol unresolved and every other one
     resolved: one feature off, the others on, no crash.
  4. A truncated image, an unreadable file, and the two 4,015,616 B Saturn-era loaders all end in a report with
     no symbols and every feature off - the fail-closed path, which is the one a future client build takes when
     a pattern stops matching.
  5. Cross-version validity: UNVERIFIED. There is no second modern client build on this machine (the one other
     copy of the same hash is a launch freeze copy), so this suite can only prove the negative path.
"""
import hashlib
import os
import re
import shutil
import struct
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, ".."))
EXE = os.path.join(ROOT, "build", "resolve_check.exe")


def game(*parts):
    """A path under the game's cod25 folder: --game <dir> first, then KRONOS_GAME_DIR, either form. "" when unset -
    this harness needs the client file, and main() stops with that message."""
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

# The identification triple the DLL uses (src\resolve.h). The two pattern-less symbols depend on it.
CLIENT_SIZE = 5016064
CLIENT_SHA = "88a52103c5555b2760f1e7ad13a594e8ef0440f007b45a10bddc61dda234fcfb"
CLIENT_OFIMAGE = 0x9A1000

# The two Saturn/Lumen-era loaders the audit lists (docs\RC1-VERSION-COUPLING.md 2.3). They predate the
# challenge subsystem, so every pattern misses in them. Read-only; nothing is written beside them.
OLD_LOADERS = [
    (os.path.join(os.path.dirname(os.path.dirname(ROOT)), "pap4", "XInput9_1_0.dll"),
     "063850c66ecdb342b33a92efd85060b432d073e4e6ebeeef10b0c34b949a456b"),
    (os.path.join(os.path.dirname(os.path.dirname(ROOT)), "trace", "dll", "XInput9_1_0.dll.orig"),
     "ad4ec538df97ea05426408c85dc85991bf3302032b21269b9624b834075a7f19"),
]

# Pattern name -> the symbol whose rva its match must be, and that symbol's constant. From the driver's own
# pattern order (src\resolve.c, RS_PAT_TEXT).
PATTERN_ANCHORS = [
    ("award", "award", 0x93820),
    ("site", "site", 0x930D3),
    ("loads", "load_a", 0x93E5D),
    ("pub", "pub", 0x962E0),
    ("master", "master", 0x96680),
    ("recs", "recs", 0x93BD0),
    ("serial", "serial", 0x96560),
    ("bitmap", "bitmap", 0x96313),
    ("rfn", "rfn", 0xB9790),
    ("salt", "salt", 0xB842F),
]

# symbol -> the constant the release used (docs\RC1-VERSION-COUPLING.md 1.1 and 1.2).
KNOWN = {
    "award": 0x93820, "site": 0x930D3, "load_a": 0x93E5D, "load_b": 0x93E63, "kill": 0x2775F4, "crit": 0x2775F8,
    "pub": 0x962E0, "master": 0x96680, "site0": 0x93DFF, "site1": 0x96212, "site2": 0x9723D, "site3": 0x97626,
    "site4": 0x976AC, "recs": 0x3DD288, "count": 0x3DD290, "serial": 0x3E6CBC, "bitmap": 0x466CD8,
    "rfn": 0x6C4280, "salt": 0x16ED38, "chver": 0x3E6840, "slot": 0x27764C,
}
PATTERN_SYMBOLS = ["award", "site", "load_a", "load_b", "kill", "crit", "pub", "master", "site0", "site1",
                   "site2", "site3", "site4", "recs", "count", "serial", "bitmap", "rfn", "salt"]
CONSTANT_SYMBOLS = ["chver", "slot"]
FEATURES = ["nativepay", "publish", "master", "g11", "pubxp", "boundary"]

passes = []
failures = []
notes = []


def check(what, cond, detail=""):
    if cond:
        passes.append(what)
        print("PASS  %s%s" % (what, ("  (%s)" % detail) if detail else ""))
    else:
        failures.append(what)
        print("FAIL  %s%s" % (what, ("  (%s)" % detail) if detail else ""))


def note(text):
    notes.append(text)
    print("INFO  " + text)


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def run(path, known=False):
    args = [EXE, "image", path] + (["known"] if known else [])
    r = subprocess.run(args, capture_output=True, text=True, timeout=600)
    return r.returncode, (r.stdout or "") + (r.stderr or "")


def result(out):
    m = re.search(r"^RESULT symbols=(\d+) pattern_symbols=(\d+) equal=(\d+) patterns=(\d+)/(\d+) known=(\d+)$",
                  out, re.M)
    if not m:
        return None
    return {
        "symbols": int(m.group(1)),
        "pattern_symbols": int(m.group(2)),
        "equal": int(m.group(3)),
        "patterns": int(m.group(4)),
        "patterns_total": int(m.group(5)),
        "known": int(m.group(6)),
    }


def sym_state(out):
    """symbol -> (rva, state) from the driver's own per-symbol lines."""
    got = {}
    for m in re.finditer(r"^sym (\S+)\s+rva=0x([0-9A-Fa-f]+) known=0x([0-9A-Fa-f]+) (\w+)$", out, re.M):
        got[m.group(1)] = (int(m.group(2), 16), m.group(4))
    return got


def pattern_counts(out):
    """pattern -> (count, rva)."""
    got = {}
    for m in re.finditer(r"^pattern (\S+)\s+count=(-?\d+) rva=0x([0-9A-Fa-f]+)$", out, re.M):
        got[m.group(1)] = (int(m.group(2)), int(m.group(3), 16))
    return got


def feature_states(out):
    got = {}
    for m in re.finditer(r"^feature (\S+)\s+(on|off(?: - \S+)?)$", out, re.M):
        got[m.group(1)] = m.group(2)
    return got


def scratch(name):
    d = os.path.join(tempfile.gettempdir(), "resolve-" + name)
    shutil.rmtree(d, ignore_errors=True)
    os.makedirs(d)
    return d


def rva_to_file(data, rva):
    """The file offset of an rva, by the image's own section table (the same arithmetic the loader uses)."""
    e = struct.unpack_from("<I", data, 0x3C)[0]
    nsec = struct.unpack_from("<H", data, e + 6)[0]
    optsz = struct.unpack_from("<H", data, e + 20)[0]
    sec = e + 24 + optsz
    for i in range(nsec):
        o = sec + i * 40
        vsize, va = struct.unpack_from("<II", data, o + 8)
        rawsize, rawptr = struct.unpack_from("<II", data, o + 16)
        span = max(vsize, rawsize)
        if va <= rva < va + span:
            return rawptr + (rva - va)
    return None


def main():
    print("clienthook build 29 - the resolver, over a file on disk - " + ROOT)
    print("")
    if not os.path.isfile(EXE):
        print("STOP: %s is missing - run clienthook\\tools\\build_tests.cmd." % EXE)
        return 1
    if not CLIENT:
        print("SKIP: the game folder is a setting - pass --game <dir> or set KRONOS_GAME_DIR to the game install "
              "(the folder holding cod25\\, or cod25 itself). This harness reads the client file.")
        return 0
    if not os.path.isfile(CLIENT):
        print("STOP: the client file is not at %s" % CLIENT)
        return 1

    # ---- 1. the identification triple, measured here -------------------------------------------------
    print("")
    print("IDENTIFY  the client on disk is the known build (size, sha256, SizeOfImage)")
    size = os.path.getsize(CLIENT)
    h = sha256_file(CLIENT)
    with open(CLIENT, "rb") as fh:
        head = fh.read(0x400)
    lfanew = struct.unpack_from("<I", head, 0x3C)[0]
    ofimage = struct.unpack_from("<I", head, lfanew + 24 + 56)[0] if lfanew + 60 <= len(head) else 0
    print("client  %d B / %s / SizeOfImage 0x%X" % (size, h.upper(), ofimage))
    check("the client is 5,016,064 B", size == CLIENT_SIZE, "%d" % size)
    check("its sha256 is the pinned one", h == CLIENT_SHA, h[:16] + "...")
    check("its SizeOfImage is 0x9A1000", ofimage == CLIENT_OFIMAGE, "0x%X" % ofimage)

    # ---- 2. the installed build: every pattern once, every rva the constant --------------------------
    print("")
    print("INSTALLED  resolve_check image <client> known")
    rc, out = run(CLIENT, known=True)
    check("the driver exits 0", rc == 0, "rc=%d" % rc)
    for line in out.strip().split("\n"):
        if line.startswith(("file:", "image:", "resolve:", "RESULT")):
            print("  | " + line)
    res = result(out)
    check("it reports a machine-readable result", res is not None, "no RESULT line")
    if res is None:
        print("\n%d passed, %d failed" % (len(passes), len(failures)))
        return 1
    counts = pattern_counts(out)
    check("all ten patterns matched", len(counts) == 10, "%d" % len(counts))
    for name, sym, want in PATTERN_ANCHORS:
        got = counts.get(name)
        check("pattern %s matches exactly once" % name, got is not None and got[0] == 1,
              "%d" % (got[0] if got else -1))
        check("and its match is rva 0x%X (the %s anchor)" % (want, sym), got is not None and got[1] == want,
              "0x%X" % (got[1] if got else 0))
    check("nineteen pattern-resolvable symbols resolved", res["pattern_symbols"] == 19, "%d" %
          res["pattern_symbols"])
    check("all twenty-one symbols resolved with the identification verdict", res["symbols"] == 21, "%d" %
          res["symbols"])
    check("every resolved rva equals the constant the release used", res["equal"] == 21, "%d equal" % res["equal"])
    check("the summary line is the 21/21 one", "resolve: 21/21 symbols (all)" in out)
    states = sym_state(out)
    for sym, want in KNOWN.items():
        got = states.get(sym)
        check("%s resolved to 0x%X" % (sym, want), got is not None and got[0] == want and got[1] == "equal",
              "%s 0x%X" % (got[1], got[0]) if got else "no line")
    feats = feature_states(out)
    for f in FEATURES:
        check("feature %s is on" % f, feats.get(f) == "on", feats.get(f, "absent"))
    check("no 'differs from the known build' line on the build the constants came from",
          "differs from the known build" not in out)

    # ---- 3. the two pattern-less symbols follow the identification verdict only ----------------------
    print("")
    print("CONSTANTS  the same image without the verdict: chver and slot unresolved, nothing else moves")
    rc, out2 = run(CLIENT, known=False)
    check("the driver exits 0", rc == 0, "rc=%d" % rc)
    res2 = result(out2)
    check("it reports a machine-readable result", res2 is not None, "no RESULT line")
    if res2 is not None:
        check("the nineteen pattern symbols still resolve", res2["pattern_symbols"] == 19,
              "%d" % res2["pattern_symbols"])
        check("and the two constants do not", res2["symbols"] == 19, "%d" % res2["symbols"])
        states2 = sym_state(out2)
        for sym in CONSTANT_SYMBOLS:
            got = states2.get(sym)
            check("%s is unresolved without the verdict" % sym, got is not None and got[0] == 0,
                  "0x%X" % (got[0] if got else -1))
        check("the summary names the two unresolved symbols",
              "resolve: 19/21 symbols (chver, slot)" in out2)
        feats2 = feature_states(out2)
        for f in FEATURES:
            want_off = f in ("g11", "pubxp")
            check("%s is %s without the verdict" % (f, "off" if want_off else "on"),
                  feats2.get(f, "").startswith("off") if want_off else feats2.get(f) == "on",
                  feats2.get(f, "absent"))
        check("the refusal names the symbol each feature needs",
              feats2.get("g11", "").endswith("chver") and feats2.get("pubxp", "").endswith("chver"),
              "%s / %s" % (feats2.get("g11"), feats2.get("pubxp")))

    # ---- 3b. the DLL's own order: the verdict BEFORE the first scan ----------------------------------
    # frame_identify gives rs_set_known_build its verdict and only then asks rs_for for the addresses, and a scan
    # zeroes the table it fills. This mode takes exactly that order: get it wrong and the two constants are lost
    # on the one build that has them, which is the failure this check exists to catch.
    print("")
    print("ORDER  the verdict first, then the scan (the order frame_identify and g11_arm use)")
    r = subprocess.run([EXE, "order", CLIENT, "known"], capture_output=True, text=True, timeout=600)
    out3b = (r.stdout or "") + (r.stderr or "")
    check("the driver exits 0", r.returncode == 0, "rc=%d" % r.returncode)
    res3b = result(out3b)
    check("it reports a machine-readable result", res3b is not None, "no RESULT line")
    if res3b is not None:
        check("a scan after the verdict keeps it: 21/21 symbols", res3b["symbols"] == 21,
              "%d" % res3b["symbols"])
        states3b = sym_state(out3b)
        for sym in CONSTANT_SYMBOLS:
            got = states3b.get(sym)
            check("%s survives the scan (the verdict is not reset by one)" % sym,
                  got is not None and got[0] == KNOWN[sym] and got[1] == "equal",
                  "%s 0x%X" % (got[1], got[0]) if got else "no line")
        feats3b = feature_states(out3b)
        for f in FEATURES:
            check("feature %s is on in that order" % f, feats3b.get(f) == "on", feats3b.get(f, "absent"))

    # ---- 4. one byte flipped inside one pattern -----------------------------------------------------
    print("")
    print("CORRUPT  one byte inside the award pattern, everything else untouched")
    d = scratch("corrupt")
    raw = bytearray(open(CLIENT, "rb").read())
    off = rva_to_file(raw, 0x93820)
    check("the award's rva maps to a file offset", off is not None, str(off))
    if off is not None:
        raw[off + 3] ^= 0xFF
        copy = os.path.join(d, "corrupt.dll")
        with open(copy, "wb") as fh:
            fh.write(raw)
        rc, out3 = run(copy, known=True)
        check("the driver exits 0 (no fault on a damaged image)", rc == 0, "rc=%d" % rc)
        res3 = result(out3)
        check("it reports a machine-readable result", res3 is not None, "no RESULT line")
        if res3 is not None:
            check("eighteen of the nineteen pattern symbols still resolve", res3["pattern_symbols"] == 18,
                  "%d" % res3["pattern_symbols"])
            states3 = sym_state(out3)
            got = states3.get("award")
            check("the corrupted symbol is the one that went unresolved",
                  got is not None and got[0] == 0 and got[1] == "unresolved",
                  "%s 0x%X" % (got[1], got[0]) if got else "no line")
            others = [s for s in KNOWN if s != "award" and states3.get(s, (0, ""))[0] != KNOWN[s]]
            check("every other symbol is still what it was", not others, ", ".join(others[:4]))
            feats3 = feature_states(out3)
            check("only nativepay turned off", feats3.get("nativepay", "").startswith("off"),
                  feats3.get("nativepay", "absent"))
            for f in ("publish", "master", "boundary"):
                check("%s keeps working" % f, feats3.get(f) == "on", feats3.get(f, "absent"))
            check("the refusal names the symbol the feature needed",
                  feats3.get("nativepay", "").endswith("award"), feats3.get("nativepay", "absent"))
            check("the pattern that was damaged is the one that reports a miss",
                  "pattern award   count=0" in out3,
                  [l for l in out3.split("\n") if l.startswith("pattern award")][:1])

    # ---- 5. a truncated image, and a file that is not an image at all -------------------------------
    print("")
    print("TRUNCATED  headers only, and a path that does not exist")
    d = scratch("trunc")
    short = os.path.join(d, "headers-only.dll")
    with open(CLIENT, "rb") as fh:
        with open(short, "wb") as out_fh:
            out_fh.write(fh.read(0x1000))
    rc, out4 = run(short, known=False)
    check("the driver exits 0 on a truncated image", rc == 0, "rc=%d" % rc)
    res4 = result(out4)
    check("it reports a machine-readable result", res4 is not None, "no RESULT line")
    if res4 is not None:
        check("no symbol resolves in an image with no code", res4["symbols"] == 0, "%d" % res4["symbols"])
        feats4 = feature_states(out4)
        check("every feature is off", all(feats4.get(f, "").startswith("off") for f in FEATURES),
              str(feats4))
    rc, out5 = run(os.path.join(d, "no-such-file.dll"), known=False)
    check("the driver exits 0 on a path that does not exist", rc == 0, "rc=%d" % rc)
    res5 = result(out5)
    check("and resolves nothing", res5 is not None and res5["symbols"] == 0,
          str(res5["symbols"]) if res5 else "no RESULT line")

    # ---- 6. the two Saturn-era loaders: the fail-closed path ----------------------------------------
    print("")
    print("OLD BUILD  the two 4,015,616 B loaders the audit lists")
    for path, want_sha in OLD_LOADERS:
        name = os.path.basename(path) + " (" + os.path.basename(os.path.dirname(path)) + ")"
        if not os.path.isfile(path):
            note("%s is not on this machine - skipped" % name)
            continue
        got_sha = sha256_file(path)
        check("%s is the recorded 4,015,616 B loader" % name,
              os.path.getsize(path) == 4015616 and got_sha == want_sha,
              "%d B / %s..." % (os.path.getsize(path), got_sha[:8].upper()))
        rc, out6 = run(path, known=False)
        check("%s: the driver exits 0" % name, rc == 0, "rc=%d" % rc)
        res6 = result(out6)
        check("%s: it reports a machine-readable result" % name, res6 is not None, "no RESULT line")
        if res6 is not None:
            check("%s: no symbol resolves (it has no challenge subsystem)" % name, res6["symbols"] == 0,
                  "%d" % res6["symbols"])
            check("%s: no pattern matches" % name, res6["patterns"] == 0,
                  "%d of %d" % (res6["patterns"], res6["patterns_total"]))
            feats6 = feature_states(out6)
            check("%s: every feature is off" % name,
                  all(feats6.get(f, "").startswith("off") for f in FEATURES), str(feats6))
            check("%s: the summary is the 0/21 one, and it lists every unresolved symbol" % name,
                  "resolve: 0/21 symbols (" in out6)

    # ---- 7. what this cannot prove -------------------------------------------------------------------
    print("")
    print("SCOPE  one build on this machine")
    freeze = os.path.join(ROOT, "trace", "store-launch14-20261110-145806", "XINPUT9_1_0.dll")
    if os.path.isfile(freeze):
        same = sha256_file(freeze) == h
        check("the launch freeze copy is the same build, so it is not a second data point", same,
              sha256_file(freeze)[:16] + "...")
    note("cross-version validity of the patterns is UNVERIFIED: no second modern client build exists here. One "
         "launch on such a build, or one run of this checker over it, is what would settle it.")

    print("")
    print("%d passed, %d failed, %d notes" % (len(passes), len(failures), len(notes)))
    if failures:
        for f in failures:
            print("  FAILED: " + f)
        return 1
    print("OK - every pattern matches once, every resolved rva is the constant the release used, the two "
          "pattern-less symbols follow the identification verdict, and a damaged, truncated or pre-challenge "
          "image fails closed with one line per feature.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
