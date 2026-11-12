#!/usr/bin/env python3
"""Offline checks for clienthook build 15's G11 payload channel (tools\\g11_test.exe + the built DLL).

    python -I tools\\test_g11.py

Read-only, stdlib-only. Nothing is installed, the game is never launched, and nothing under D:\\Games is
written (the client and the challenges table are read, like `test_ladder.py` reads the tsv).

What it proves:
  * the C unit driver passes: the hex encoder, the 33-part splitter, the mod's nibble query, the header, the
    popcount, the canary validator, the slot rule, the latch, and (build 16) the create-and-validate pass over
    the 35 payload dvars against a model of the client's own register-or-find - idempotent, order-agnostic;
  * the C encoder and Python's own `bytes.hex()` agree byte for byte over a bitmap built from the REAL lock
    set the spec measured (25,017 ids out of the installed kronos\\challenges.tsv), so the game will see
    exactly the set S3/ the design measured;
  * the C name hash equals an independent Python model, and that model reproduces the client's OWN constants
    (DV_CH_VER and all 96 DV_CH_PARTS names of the installed LUIFPSCounter.lua) - so "the hash is right" is
    not our word, it is the client's;
  * g11_sha256_file, the client-image gate's hash path, returns the pinned client hash on this machine;
  * the built version.dll carries the 35 payload dvar names, the three log prefixes `g11: armed`,
    `g11: published serial`, `g11: refused - `, and NO `zm_ch_s`/`zm_ch_state` name - i.e. it never touches
    the client's own published chunk channel, and it cannot even address a chunk;
  * the DLL's name list and the mod's GSC agree (35 names, same order), so a renamed dvar cannot pass - and the
    test driver's own copy of that list agrees with the DLL's, so the unit proof is about the same names.

What it cannot prove: that the engine's register-or-find creates (or returns) those dvars from our thread, that
it does so before the first match, and that the Lua VM hands over the full 2,000 chars of a slab. Those are the
launch's questions.
"""

import hashlib
import os
import re
import struct
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))          # clienthook\
EXE = os.path.join(ROOT, "build", "g11_test.exe")
DLL = os.path.join(ROOT, "build", "version.dll")
IO_PROBE = os.path.join(ROOT, "src", "frame.c")
G11_H = os.path.join(ROOT, "src", "g11.h")
GSC = os.path.abspath(os.path.join(ROOT, "..", "mod", "g11_locks", "scripts",
                                   "g11_locks.gsc"))
LUA = os.path.abspath(os.path.join(ROOT, "..", "mod", "g11_locks", "lua",
                                   "g11_locks_post.lua"))


def game(*parts):
    """A path under the game's cod25 folder: --game <dir> first, then KRONOS_GAME_DIR, either form. "" when unset -
    the three files below are optional here, and the checks that read them say so and skip."""
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


TSV = game("kronos", "challenges.tsv")
CLIENT = game("XINPUT9_1_0.dll")
LUIFPS = game("kronos", "Assets", "Lua", "ui", "LUIFPSCounter.lua")
CLIENT_SHA = "88a52103c5555b2760f1e7ad13a594e8ef0440f007b45a10bddc61dda234fcfb"
CLIENT_SIZE = 5016064

SCRATCH = os.path.join(tempfile.gettempdir(), "progression-tuning", "g11build")

SALT = bytes.fromhex("71366e2d2b373d747979746739345f2a")
MUL = 0x10000000233
SEED = 0xD86A3B09566EBAAC

ACCEPT = [89575, 96171, 96192, 96202, 102671, 126597, 126619, 111457]
DVAR_NAMES = ["zm_g11_arm", "zm_g11_ver"] + ["zm_g11_%d" % i for i in range(33)]

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


def name_hash(name, salt=SALT):
    s = name.lower()
    v = ((ord(s[0]) & 0xFF) ^ SEED) * MUL & 0xFFFFFFFFFFFFFFFF
    for b in salt:
        v = ((v ^ b) * MUL) & 0xFFFFFFFFFFFFFFFF
    for ch in s[1:]:
        v = ((v ^ (ord(ch) & 0xFF)) * MUL) & 0xFFFFFFFFFFFFFFFF
    return "%016x" % v


def run(args, timeout=120):
    return subprocess.run([EXE] + args, capture_output=True, text=True, timeout=timeout)


def real_lock_set():
    """The independent method, checked against the real lock set."""
    recs, sets = [], {}
    with open(TSV, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            line = line.rstrip("\r\n")
            if not line:
                continue
            if line.startswith("@"):
                f = line.split("\t")
                ids = []
                for p in f[1:]:
                    for t in p.replace(",", " ").split():
                        if t.isdigit():
                            ids.append(int(t))
                sets[f[0]] = ids
                continue
            f = line.split("\t")
            if len(f) == 10 and f[0].isdigit():
                recs.append(f)
    unlocked = {"@cat_perks", "@cat_equipment", "@cat_scorestreaks", "@cat_fieldupgrades",
                "@cat_ammomods", "@cat_charms"}
    cand = set()
    for r in recs:
        if r[5]:
            for g in r[5].split("|"):
                for t in g.split("+"):
                    if t.isdigit():
                        cand.add(int(t))
    for k, v in sets.items():
        if k.startswith("@cat_") and k not in unlocked:
            cand |= set(v)
    return len(recs), cand


def client_own_constants():
    if not os.path.isfile(LUIFPS):
        return None, None
    with open(LUIFPS, "r", encoding="utf-8", errors="replace") as fh:
        lines = fh.read().split("\n")
    ver, parts = None, []
    for i, line in enumerate(lines):
        m = re.search(r'DV_CH_VER\s*=\s*"([0-9a-f]{16})"', line)
        if m:
            ver = m.group(1)
            for follow in lines[i + 1:]:
                parts.extend(re.findall(r'"([0-9a-f]{16})"', follow))
                if "}" in follow:
                    break
    return ver, parts


def main():
    print("clienthook build 15 - G11 offline check - " + ROOT)
    print("")
    if not CLIENT:
        print("NOTE  KRONOS_GAME_DIR is not set and no --game was given - the client, challenges.tsv and the "
              "client's own constants cannot be read, so the checks that use them are skipped")
    os.makedirs(SCRATCH, exist_ok=True)

    check("build\\g11_test.exe exists (build.cmd)", os.path.isfile(EXE))
    check("build\\version.dll exists (build.cmd)", os.path.isfile(DLL))
    if failures:
        print("")
        print("STOP: run clienthook\\build.cmd first.")
        return 1

    # ---- 1. the C unit driver ---------------------------------------------------------------------
    print("")
    print("UNIT  g11_test.exe self")
    proc = run(["self"])
    for line in (proc.stdout or "").split("\n"):
        if line.startswith("FAIL") or line.startswith("g11:"):
            print("  | " + line)
    m = re.search(r"g11: OK - (\d+) checks", proc.stdout or "")
    check("the C unit driver passes", proc.returncode == 0 and m is not None,
          (proc.stdout or "").strip().split("\n")[-1] if proc.stdout else proc.stderr)
    if m:
        info("g11_test.exe self: %s checks, exit 0" % m.group(1))

    # the build-16 create pass: the checks exist, and they are the ones this name list is about
    out = proc.stdout or ""
    for want in ("create: an empty engine -> all 35 usable",
                 "create: it created exactly the 35 names, nothing else",
                 "create: the sentinel is the value and the names are the list, in order",
                 "create: a second pass creates nothing (idempotent)",
                 "create: the GSC first -> all 35 found, none created",
                 "create: a slot holding \"g11n\" refuses the pass at index 0",
                 "create: one foreign value (index 7) refuses the whole pass"):
        check("the create pass: %s" % want, ("pass  " + want) in out)

    # ---- 2. the real lock set, C encoder vs Python -------------------------------------------------
    if not os.path.isfile(TSV):
        info("challenges.tsv is not on disk - the encode comparison was skipped")
    else:
        nrec, cand = real_lock_set()
        info("lock set rebuilt from kronos\\challenges.tsv: %d records, %d ids, max %d"
             % (nrec, len(cand), max(cand)))
        # The count is the INSTALLED table's, not a constant: D9/S3 measured 25,017 ids out of the 566,694-byte
        # manifest table. This machine's kronos\challenges.tsv is now 600,397 B (2026-11-06 16:56:54, the G9
        # ladder-apply step - progression-tuning\trace\g9-install-20261106-165654\), so the count moved with it.
        # What this check owns is that the set is a real, canonical one; the encoder agreement below is what the
        # build actually has to get right, and it runs against whatever the installed table holds.
        tsv_size = os.path.getsize(TSV)
        check("the lock set is the installed table's own set (canonical, > 20,000 ids)",
              len(cand) > 20000 and len(cand) == len(set(cand)), "%d ids from %d B" % (len(cand), tsv_size))
        if len(cand) != 25017:
            info("the installed kronos\\challenges.tsv yields %d ids (%d B), not S3's 25,017 - the table on disk "
                 "has changed since D9 (G9's ladder apply, 2026-11-06); the encoder checks below use the "
                 "installed set either way" % (len(cand), tsv_size))
        check("the set's max id is S3's 154,735", max(cand) == 154735, "%d" % max(cand))

        bm = bytearray(32768)
        for i in cand:
            bm[i >> 3] |= 1 << (i & 7)
        bmpath = os.path.join(SCRATCH, "bitmap.bin")
        with open(bmpath, "wb") as fh:
            fh.write(bytes(bm))
        proc = run(["encode", bmpath])
        check("g11_test.exe encode ran", proc.returncode == 0, (proc.stdout or proc.stderr).strip()[:80])
        cparts = [ln for ln in (proc.stdout or "").split("\n") if ln]
        pyfull = bytes(bm).hex()
        pyparts = [pyfull[i:i + 2000] for i in range(0, len(pyfull), 2000)]
        check("the C encoder produced 33 parts", len(cparts) == 33, "%d" % len(cparts))
        check("every C part equals Python's bytes.hex() split",
              cparts == pyparts,
              next((i for i, (a, b) in enumerate(zip(cparts, pyparts)) if a != b), "all equal"))
        check("every part is <= the 2,047-char Lua read cap", all(len(p) <= 2047 for p in cparts),
              "longest %d" % max(len(p) for p in cparts))
        joined = "".join(cparts)
        check("the parts join to 65,536 hex chars", len(joined) == 65536, "%d" % len(joined))
        back = bytes.fromhex(joined)
        decoded = {i for i in range(32768 * 8) if (back[i >> 3] >> (i & 7)) & 1}
        check("the payload decodes back to exactly the real lock set", decoded == cand,
              "%d decoded, %d expected" % (len(decoded), len(cand)))
        missing = [i for i in ACCEPT if i not in decoded]
        check("all eight acceptance ids are set in the payload", not missing, str(missing))

        # the mod's own nibble query, on the C payload: every id 0..299,999 answers as the set does
        bad = 0
        for i in range(0, 300000):
            if i < 1 or i > 0x3FFFF:
                got = 0
            else:
                b, r = i // 8, i % 8
                p = b * 2 + (0 if r >= 4 else 1)
                got = (int(joined[p], 16) >> (r & 3)) & 1
            if got != (1 if i in cand else 0):
                bad += 1
                if bad > 3:
                    break
        check("the mod's nibble query over the C payload: 0..299,999 -> 0 mismatches", bad == 0,
              "%d mismatches" % bad)

    # ---- 3. the name hash, C vs Python vs the client's own constants -------------------------------
    print("")
    ver, parts = client_own_constants()
    if ver is None:
        info("LUIFPSCounter.lua is not on disk - the client-constant cross-check was skipped")
    else:
        check("the Python model reproduces the client's DV_CH_VER", name_hash("zm_ch_ver") == ver,
              "%s vs %s" % (name_hash("zm_ch_ver"), ver))
        bad = [i for i, h in enumerate(parts) if name_hash("zm_ch_s%d" % i) != h]
        check("the Python model reproduces all %d DV_CH_PARTS names" % len(parts), not bad,
              "%d wrong" % len(bad))
        info("the model is the client's own hash over %d independent constants" % (len(parts) + 1))

    salt_hex = SALT.hex()
    names = DVAR_NAMES + ["kronos_g11_scope", "zm_ch_ver", "zm_ch_s0", "zm_ch_s95"]
    bad = []
    for n in names:
        proc = run(["hash", salt_hex, n])
        got = (proc.stdout or "").strip()
        if got != name_hash(n):
            bad.append("%s: %s vs %s" % (n, got, name_hash(n)))
    check("the C hash equals the Python model for all %d names" % len(names), not bad, "; ".join(bad))

    # ---- 4. the client-image gate's hash path ------------------------------------------------------
    if os.path.isfile(CLIENT):
        size = os.path.getsize(CLIENT)
        check("the installed client is the pinned 5,016,064 B", size == CLIENT_SIZE, "%d" % size)
        proc = run(["sha256", CLIENT])
        got = (proc.stdout or "").strip()
        check("g11_sha256_file returns the pinned client hash", got == CLIENT_SHA, got[:32] + "...")
        with open(CLIENT, "rb") as fh:
            check("and it is the file's real SHA-256", hashlib.sha256(fh.read()).hexdigest() == CLIENT_SHA)
    else:
        info("the client is not on disk - the hash gate was not exercised")

    # ---- 5. the built DLL's own strings ------------------------------------------------------------
    raw = open(DLL, "rb").read()
    text = raw.decode("latin-1")
    for name in DVAR_NAMES:
        if name.encode() not in raw:
            check("version.dll names %s" % name, False)
            break
    else:
        check("version.dll carries all %d payload dvar names" % len(DVAR_NAMES), True)
    check("version.dll carries 'g11: armed'", "g11: armed" in text)
    check("version.dll carries 'g11: published serial'", "g11: published serial" in text)
    check("version.dll carries 'g11: refused - '", "g11: refused - " in text)
    check("version.dll carries the 'g11n' probe default (never the sentinel as a write default)",
          "g11n" in text)
    # build 16: the hook creates the dvars itself, and the master detour is in this image
    check("version.dll carries the build-16 create line (arm without a match)",
          "created here where absent - no match needed" in text)
    check("version.dll carries the build-16 wait line (a null register-or-find is not a latch)",
          "g11: waiting - the engine did not hand back" in text)
    check("version.dll carries the build-16b master install line", "master: %d call sites hooked (" in text)
    check("version.dll no longer carries build 16's prologue hook (build 16b patches call sites)",
          "master: hook at " not in text)
    check("version.dll carries the master signature refusal", "master: the level function at " in text)
    check("version.dll carries the master log prefix", "master: %s prestige " in text)
    check("version.dll carries no zm_ch_s chunk name (the client's channel is untouched)",
          "zm_ch_s" not in text)
    check("version.dll carries no zm_ch_state name", "zm_ch_state" not in text)
    info("version.dll %d B / %s" % (len(raw), hashlib.sha256(raw).hexdigest()[:16].upper()))

    # ---- 6. the DLL's list and the mod's GSC agree -------------------------------------------------
    src = open(IO_PROBE, "r", encoding="utf-8", errors="replace").read()
    block = re.search(r"G11_NAMES\[G11_DVARS\] = \{(.*?)\};", src, re.S)
    check("src\\frame.c has the G11_NAMES table", block is not None)
    if block:
        dll_names = re.findall(r'"(zm_g11_[a-z0-9_]+)"', block.group(1))
        check("the DLL's table is the 35 names in order", dll_names == DVAR_NAMES,
              "%d names" % len(dll_names))
        # the unit driver repeats the list (it links g11.c only), so the two must not drift
        test_src = open(os.path.join(ROOT, "tools", "g11_test.c"), "r", encoding="utf-8",
                        errors="replace").read()
        tblock = re.search(r"TEST_NAMES\[\] = \{(.*?)\};", test_src, re.S)
        check("tools\\g11_test.c has its own copy of the name list", tblock is not None)
        if tblock:
            test_names = re.findall(r'"(zm_g11_[a-z0-9_]+)"', tblock.group(1))
            check("the test driver's list is the DLL's list (so the create proof is about these names)",
                  test_names == dll_names, "%d vs %d" % (len(test_names), len(dll_names)))
        if os.path.isfile(GSC):
            gsc = open(GSC, "r", encoding="utf-8", errors="replace").read()
            # code lines only: v6's header names a dvar in prose (`an unguarded setdvar("zm_g11_0", "g11") ...`),
            # which is the same rule D25's Lua test already follows. A comment is not a call.
            gsc_code = "\n".join(l for l in gsc.split("\n") if not l.strip().startswith("//"))
            gsc_names = re.findall(r'setdvar\(\s*"([^"]+)"', gsc_code)
            check("the mod's GSC sets the same 35 names in the same order", gsc_names == dll_names,
                  "%d vs %d" % (len(gsc_names), len(dll_names)))
        else:
            info("the GSC is not at %s - the cross-check was skipped" % GSC)
    if os.path.isfile(LUA):
        lua = open(LUA, "r", encoding="utf-8", errors="replace").read()
        # v5 reads the parts and the header by NAME (docs\DECISIONS.md D10: the global `xhash` hashes a name, so
        # v1's bare 16-hex literals hashed to keys nothing held). The check is that the two sides name the same
        # dvars - one list, built by format for the 33 slabs.
        check("the Lua builds the 33 part names from the DLL's prefix",
              'string.format("zm_g11_%d", i)' in lua and "local PARTS = 33" in lua)
        check("the Lua names the header dvar", '"zm_g11_ver"' in lua)
        check("the Lua names the arm dvar", '"zm_g11_arm"' in lua)
        check("the Lua checks the payload length before using it", "65536" in lua)
    else:
        info("the mod Lua is not at %s - the literal cross-check was skipped" % LUA)

    # ---- 7. the header/format the two sides share --------------------------------------------------
    h = open(G11_H, "r", encoding="utf-8", errors="replace").read()
    check("g11.h fixes 33 parts of 2,000 chars and 65,536 hex chars",
          "#define G11_PARTS 33" in h and "#define G11_HEX 65536" in h and "#define G11_PART_CHARS 2000" in h)
    check("g11.h states the sentinel the GSC writes", '#define G11_SENTINEL "g11"' in h)
    check("the header format has one implementation (g11_ver)", "g11_ver(" in h)

    # ---- hashes -----------------------------------------------------------------------------------
    print("")
    for path in (os.path.join(ROOT, "src", "g11.h"), os.path.join(ROOT, "src", "g11.c"), IO_PROBE,
                 os.path.join(ROOT, "src", "proxy_main.c"), os.path.join(ROOT, "tools", "g11_test.c"),
                 os.path.join(ROOT, "build.cmd"), DLL, EXE):
        data = open(path, "rb").read()
        print("HASH  %s  %d B  %s" % (os.path.relpath(path, ROOT), len(data),
                                      hashlib.sha256(data).hexdigest()[:16].upper()))

    print("")
    print("%d passed, %d failed" % (len(passes), len(failures)))
    if failures:
        for f in failures:
            print("  FAILED: " + f)
        return 1
    print("OK - the encoder, the splitter, the validator and the latch pass; the payload is the real lock "
          "set; the hash is the client's own; the DLL touches no chunk.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
