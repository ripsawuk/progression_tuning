"""Offline proof of clienthook build 30's g12 reward set - the second payload, walked out of the challenge table.

Read-only with respect to the game: nothing is installed, nothing is launched, and the only files written are a
staged record array and the parts it produces, both under %TEMP%. The table it measures is the in-repo one
(`data\\challenges.tsv`, the 4,584 rows the game's own record array holds).

    clienthook\\build.cmd                 -> build\\version.dll
    clienthook\\tools\\build_tests.cmd     -> the drivers in build\\
    python -I clienthook\\tools\\test_g12.py

WHAT IT CHECKS. The walk reproduces the table's own reward set through the SHIPPED `g12_collect`
(tools\\g11_test.exe `collect` over a staged array of 4,584 records at the record stride), and the row's own tier
count is what bounds it: every block past that count is filled with 0x3FFFF in the staged array, so a walk that
read one block too many would report one id more. Then the header the mod parses (`<count>:33:65536`, through the
shipped `g11_ver`), the 35 dvar names, the five log lines, and the two negative claims that keep this channel away
from the game's own chunks.

6,423 AND 6,422. The table names 6,423 distinct reward ids, but the game's own record filler keeps only THREE ids
a tier - `1800950d0:83-95` parses a tier's `+`-joined ids in a `do { } while (uVar6 < 3)` loop, so a fourth is read
and never stored - and two rows (`67504`, `67506`, both kind 900) name four. The record therefore holds 6,422, the
walk reports 6,422, and the one id the game itself drops is 131780. That is the number the launch must show:
`g12: published 6422 reward ids from 4584 records`.

The array is a model of the record block, not a copy of the game's memory: stride 0x578, the tier count at +0x58,
three ids a tier at +0x15C + k*0xC (src\\master.h, 1800950d0:58-62,86).
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
DLL_SHA = os.path.join(ROOT, "build", "version.dll.sha256")
FRAME = os.path.join(ROOT, "src", "frame.c")
G11_C = os.path.join(ROOT, "src", "g11.c")
G11_H = os.path.join(ROOT, "src", "g11.h")
MASTER_H = os.path.join(ROOT, "src", "master.h")
RESOLVE_H = os.path.join(ROOT, "src", "resolve.h")
RESOLVE_C = os.path.join(ROOT, "src", "resolve.c")
TSV = os.path.abspath(os.path.join(ROOT, "..", "data", "challenges.tsv"))

# the record block, as src\master.h and the game's own builder (180092070:53-67) have it
REC_STRIDE = 0x578
REC_COUNT = 0x58
REC_TIER_LOOT = 0x15C
REC_BLOCKS = 64          # uint[64][3]: the block array's own ceiling
REC_IDS = 3              # ids a tier
MAX_ID = 0x3FFFF

# the measured set, and the per-kind census that makes up the table's 6,423
EXPECT_TABLE_IDS = 6423   # distinct ids the table names
EXPECT_IDS = 6422         # distinct ids the game's own record filler keeps: three a tier
EXPECT_DROPPED = 131780   # the fourth id of a tier in rows 67504/67506, which 1800950d0 never stores
EXPECT_MAX = 152853
EXPECT_ROWS = 4584
EXPECT_KINDS = {400: 3098, 398: 1957, 315: 642, 0: 219, 429: 193, 900: 135, 417: 77, 592: 64, 597: 6,
                438: 0, 585: 0, 594: 0, 368: 76}

DVAR_NAMES = ["zm_g12_arm", "zm_g12_ver"] + ["zm_g12_%d" % i for i in range(33)]

SCRATCH = os.path.join(tempfile.gettempdir(), "progression-tuning", "g12build")

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


def read(path):
    with open(path, "r", encoding="utf-8", errors="replace") as fh:
        return fh.read()


def run(args, timeout=300):
    return subprocess.run([EXE] + args, capture_output=True, text=True, timeout=timeout)


def table_rows():
    """The table's 4,584 record rows: (id, kind, tier ids per tier). The 258 two-column lines are the category
    id lists the game builds its candidates from, not rows."""
    rows = []
    for line in read(TSV).splitlines():
        f = line.split("\t")
        if len(f) != 10:
            continue
        tiers = []
        for tier in f[5].split("|"):
            ids = [int(x) for x in tier.split("+") if x.strip()]
            tiers.append(ids)
        rows.append((int(f[0]), int(f[1]), tiers, f[4].split("|") if f[4] else []))
    return rows


def staged(rows, junk):
    """The record array the shipped walk reads: one 0x578-byte block a row, the row's own tier count at +0x58,
    each tier's up-to-three ids at +0x15C + k*0xC. `junk` fills every block past that count, so the bound is
    measured rather than assumed."""
    out = bytearray(REC_STRIDE * len(rows))
    for i, (_cid, _kind, tiers, thr) in enumerate(rows):
        base = i * REC_STRIDE
        n = max(len(thr), len(tiers))
        if n > REC_BLOCKS:
            n = REC_BLOCKS
        struct.pack_into("<i", out, base + REC_COUNT, n)
        for k, ids in enumerate(tiers):
            if k >= REC_BLOCKS:
                break
            for j in range(REC_IDS):
                v = ids[j] if j < len(ids) else 0
                struct.pack_into("<I", out, base + REC_TIER_LOOT + k * 0xC + j * 4, v)
        if junk is not None:
            for k in range(n, REC_BLOCKS):
                for j in range(REC_IDS):
                    struct.pack_into("<I", out, base + REC_TIER_LOOT + k * 0xC + j * 4, junk)
    return bytes(out)


def python_set(rows):
    """Every id the table names - the 6,423."""
    ids = set()
    for _cid, _kind, tiers, _thr in rows:
        for ids_ in tiers:
            for i in ids_:
                if 1 <= i <= MAX_ID:
                    ids.add(i)
    return ids


def python_record_set(rows):
    """Every id the game's own filler stores: at most three a tier (1800950d0:83-95) - the 6,422."""
    ids = set()
    for _cid, _kind, tiers, _thr in rows:
        for ids_ in tiers:
            for i in ids_[:REC_IDS]:
                if 1 <= i <= MAX_ID:
                    ids.add(i)
    return ids


def python_kinds(rows):
    per = {}
    for _cid, kind, tiers, _thr in rows:
        s = per.setdefault(kind, set())
        for ids_ in tiers:
            for i in ids_:
                if 1 <= i <= MAX_ID:
                    s.add(i)
    return {k: len(v) for k, v in per.items()}


def main():
    print("clienthook build 30 - the g12 reward set, walked out of data\\challenges.tsv - " + ROOT)
    print("")
    for p in (EXE, DLL):
        if not os.path.isfile(p):
            print("STOP: %s is missing - run clienthook\\build.cmd and clienthook\\tools\\build_tests.cmd." % p)
            return 1
    os.makedirs(SCRATCH, exist_ok=True)

    # ---- 1. the table the walk is measured against ---------------------------------------------------
    print("")
    print("TABLE  data\\challenges.tsv, its 4,584 record rows")
    if not os.path.isfile(TSV):
        print("STOP: %s is missing - this harness measures the in-repo table." % TSV)
        return 1
    rows = table_rows()
    ids = python_set(rows)
    rec_ids = python_record_set(rows)
    kinds = python_kinds(rows)
    check("the table holds %d record rows" % EXPECT_ROWS, len(rows) == EXPECT_ROWS, "%d" % len(rows))
    check("its rows name %d distinct ids" % EXPECT_TABLE_IDS, len(ids) == EXPECT_TABLE_IDS, "%d" % len(ids))
    check("the largest id is %d" % EXPECT_MAX, max(ids) == EXPECT_MAX, "%d" % max(ids))
    check("nothing sits above 0x3FFFF", all(i <= MAX_ID for i in ids), "%d above" % sum(1 for i in ids if i > MAX_ID))
    check("the per-kind census is the measured one", kinds == EXPECT_KINDS,
          ", ".join("%d:%d" % (k, kinds.get(k, -1)) for k in sorted(EXPECT_KINDS)))
    tiers_max = max(len(t) for _c, _k, t, _thr in rows)
    check("no row has more tiers than the block array holds (%d)" % REC_BLOCKS, tiers_max <= REC_BLOCKS,
          "%d tiers" % tiers_max)
    # three ids a tier is the record's capacity, and the game's filler drops a fourth rather than widening it
    check("the record's set is the table's minus the one id the game's filler drops (%d)" % EXPECT_DROPPED,
          ids - rec_ids == {EXPECT_DROPPED} and len(rec_ids) == EXPECT_IDS,
          "%d record ids, dropped %s" % (len(rec_ids), sorted(ids - rec_ids)))
    info("the table names %d ids; the record holds %d, because 1800950d0:83-95 keeps three a tier and two kind-900 "
         "rows (67504, 67506) name four" % (len(ids), len(rec_ids)))

    # ---- 2. the shipped walk over a staged array -----------------------------------------------------
    print("")
    print("WALK  g11_test.exe collect, the shipped g12_collect over 4,584 staged records")
    junk = MAX_ID  # a valid id, so a walk that read past the count would report one more
    array = staged(rows, junk)
    path = os.path.join(SCRATCH, "array.bin")
    with open(path, "wb") as fh:
        fh.write(array)
    check("the staged array is %d records at %d B" % (len(rows), REC_STRIDE),
          len(array) == len(rows) * REC_STRIDE, "%d B" % len(array))
    proc = run(["collect", path])
    out = proc.stdout or ""
    check("g11_test.exe collect ran", proc.returncode == 0, (out or proc.stderr or "").strip()[:80])
    m = re.search(r"^REWARD (\d+)$", out, re.M)
    got_ids = int(m.group(1)) if m else -1
    m = re.search(r"^RECORDS (\d+)$", out, re.M)
    got_rows = int(m.group(1)) if m else -1
    check("the walk read all %d records" % EXPECT_ROWS, got_rows == EXPECT_ROWS, "%d" % got_rows)
    check("the walk reports exactly %d reward ids" % EXPECT_IDS, got_ids == EXPECT_IDS, "%d" % got_ids)
    info("the walk's count is the record's own %d - a block read past a row's tier count would have made it %d"
         % (got_ids, got_ids + 1))

    parts = [ln for ln in out.split("\n") if re.fullmatch(r"[0-9a-f]{1536,2000}", ln)]
    check("the walk printed 33 parts", len(parts) == 33, "%d" % len(parts))
    check("every part is inside the 2,047-char dvar read cap", all(len(p) <= 2047 for p in parts),
          "longest %d" % (max(len(p) for p in parts) if parts else 0))
    joined = "".join(parts)
    check("the parts join to 65,536 hex chars", len(joined) == 65536, "%d" % len(joined))
    decoded = set()
    raw = bytes.fromhex(joined) if len(joined) == 65536 else b""
    for i in range(1, MAX_ID + 1):
        if (raw[i >> 3] >> (i & 7)) & 1:
            decoded.add(i)
    check("the payload decodes to exactly the record's set", decoded == rec_ids,
          "%d decoded, %d expected" % (len(decoded), len(rec_ids)))
    check("the payload's largest id is %d" % EXPECT_MAX, (max(decoded) if decoded else 0) == EXPECT_MAX,
          "%d" % (max(decoded) if decoded else 0))
    check("the payload's popcount is the count the header carries", len(decoded) == got_ids,
          "%d vs %d" % (len(decoded), got_ids))

    # the header the mod parses: <count>:33:65536, from the shipped g11_ver
    m = re.search(r"^HEADER (\S+)$", out, re.M)
    header = m.group(1) if m else ""
    check("the header is '<count>:33:65536'", header == "%d:33:65536" % EXPECT_IDS, header or "no line")
    check("the header's count is the popcount it protects", header.split(":")[0] == str(len(decoded)), header)

    # the bound itself: the same rows with no junk past their tier counts give the same set, and a zero-filled
    # array past the count is what the game's own rows look like
    zero = os.path.join(SCRATCH, "array-zero.bin")
    with open(zero, "wb") as fh:
        fh.write(staged(rows, None))
    proc = run(["collect", zero])
    m = re.search(r"^REWARD (\d+)$", proc.stdout or "", re.M)
    same = (proc.returncode == 0 and m is not None and int(m.group(1)) == EXPECT_IDS)
    check("an array with zeros past the tier count reports the same count", same,
          m.group(1) if m else "no line")

    # ---- 3. the built DLL's 35 names, and the log lines ----------------------------------------------
    print("")
    print("DLL  the 35 dvars, the five log lines, and the two things it must not carry")
    raw_dll = open(DLL, "rb").read()
    text = raw_dll.decode("latin-1")
    check("build\\version.dll.sha256 records this DLL's hash",
          hashlib.sha256(raw_dll).hexdigest().lower() in read(DLL_SHA).lower())
    missing = [n for n in DVAR_NAMES if n.encode() not in raw_dll]
    check("version.dll carries all %d g12 dvar names" % len(DVAR_NAMES), not missing, ", ".join(missing[:4]))
    check("version.dll carries the g11 names too (that channel is untouched)",
          all(n.encode() in raw_dll for n in ["zm_g11_arm", "zm_g11_ver", "zm_g11_0", "zm_g11_32"]))
    check("version.dll carries 'g12: armed'", "g12: armed" in text)
    check("version.dll carries 'g12: published '", "g12: published " in text)
    check("version.dll carries 'g12: refused - '", "g12: refused - " in text)
    check("version.dll carries 'g12: waiting - '", "g12: waiting - " in text)
    check("version.dll carries 'g12: disabled by file'", "g12: disabled by file" in text)
    check("version.dll carries the kill switch's own file name", "rewards_off.txt" in text)
    check("version.dll carries no zm_ch_s chunk name", "zm_ch_s" not in text)
    check("version.dll carries no zm_ch_state name", "zm_ch_state" not in text)
    check("the banner is this build's", "version.dll build 37" in text)
    check("the banner names the reward set", "zm_g12_* the challenge reward set" in text)

    # ---- 4. the source the DLL was built from --------------------------------------------------------
    print("")
    print("SOURCE  the list, the bound and the feature")
    frame = read(FRAME)
    block = re.search(r"G12_NAMES\[G11_DVARS\] = \{(.*?)\};", frame, re.S)
    check("src\\frame.c has the G12_NAMES table", block is not None)
    if block:
        dll_names = re.findall(r'"(zm_g12_[a-z0-9_]+)"', block.group(1))
        check("the table is the 35 names in order", dll_names == DVAR_NAMES, "%d names" % len(dll_names))
    check("the header is written from the count, not a serial",
          "g11_ver(G12_VERBUF, sizeof(G12_VERBUF), (unsigned)count, G11_PARTS, G11_HEX)" in frame)
    check("the header is written after the 33 parts",
          frame.index("*(char **)((BYTE *)G12_DVAR[1] + G12_SLOT) = G12_VERBUF;") >
          frame.index("*(char **)((BYTE *)G12_DVAR[2 + i] + G12_SLOT) = G12_BANK[i];"))
    check("one bank, one publish: the thread stops once the set is out",
          "static char G12_BANK[G11_PARTS][G11_PART_CHARS + 1];" in frame and "G12_DONE = 1;" in frame)
    check("the kill switch is read before the arm pass",
          frame.index("if (g12_off_present(NULL))") < frame.index("if (!G12_ARMED)"))
    mh = read(MASTER_H)
    check("master.h carries the tier-loot block and its ceiling",
          "#define MASTER_REC_TIER_LOOT 0x15C" in mh and "#define MASTER_TIER_LOOT 192" in mh)
    gc = read(G11_C)
    check("g11.c bounds the walk by the row's own tier count",
          "int tiers = *(const int *)(rec + MASTER_REC_COUNT);" in gc and "tiers > MASTER_TIER_LOOT / 3" in gc)
    check("g11.c keeps the game's own id guard", "if (id < 1 || id > G11_MAX_ID)" in gc)
    check("g11.c clears the bitmap before the walk", "memset(out, 0, G11_BITMAP_BYTES);" in gc)
    check("g12 is a resolver feature with the six symbols it reads",
          "RS_F_G12" in read(RESOLVE_H) and
          '{"g12", {RS_RECS, RS_COUNT, RS_RFN, RS_SALT, RS_CHVER, RS_SLOT, RS_SYM_COUNT}, 6}' in read(RESOLVE_C))

    # ---- 5. the driver's own three checks -------------------------------------------------------------
    print("")
    print("UNIT  the walk's edge cases, in g11_test.exe self")
    proc = run(["self"])
    out = proc.stdout or ""
    check("the unit driver passes", proc.returncode == 0,
          (out.strip().split("\n")[-1] if out.strip() else proc.stderr))
    for want in ("g12: the walk keeps 1..0x3FFFF, drops 0 and 0x40000, and stops at the row's own tier count",
                 "g12: a row with no tiers contributes nothing",
                 "g12: the kill switch reads absent in a clean directory and present with its own file"):
        check("the unit driver: %s" % want[:60], ("pass  " + want) in out)

    print("")
    print("%d passed, %d failed" % (len(passes), len(failures)))
    if failures:
        for f in failures:
            print("  FAILED: " + f)
        return 1
    print("OK - the walk reproduces the record's own set (6,422 ids, the table's 6,423 minus the one id the game's")
    print("     filler drops) and stops at each row's own tier count; the header, the 35 names and the five log "
          "lines")
    print("     are in the built DLL, and the game's own chunks are not.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
