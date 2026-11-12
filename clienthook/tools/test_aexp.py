"""Offline proof for the ae_events.log parser (build 13).

    python clienthook\\tools\\test_aexp.py [path-to-ae_events.log] [--game <dir>]

Copies the log (default: the game's players\\ae_events.log, read only) into a temp dir, runs
build\\aexp_test.exe over it with several chunkings, and checks every parsed record against an
independent python parse. Also checks the facts build 13 relies on: field 45 appears exactly on the
ev=95 rows that carry field 44, and a few hand-made lines (CRLF, a missing newline, an overlong line,
a non-integer value).

The log's location is a setting, never a constant: the first positional argument, else
KRONOS_GAME_DIR (the game install - the folder holding cod25\\, or cod25 itself). With neither set
there is nothing to parse, and the run stops with that message.
"""
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
EXE = os.path.join(ROOT, "build", "aexp_test.exe")
ABSENT = -1
KEYS = (0, 31, 44, 45, 234)


def game(*parts):
    """A path under the game's cod25 folder: --game <dir> first, then KRONOS_GAME_DIR, either form. "" when unset."""
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


def positional():
    """sys.argv[1:] minus the --game option and its value."""
    out, skip = [], False
    for a in sys.argv[1:]:
        if skip:
            skip = False
            continue
        if a == "--game":
            skip = True
            continue
        if a.startswith("--game="):
            continue
        out.append(a)
    return out


DEFAULT = game("players", "ae_events.log")


def py_parse(data):
    out = []
    for raw in data.split(b"\n")[:-1]:  # only whole lines, as the C side
        if len(raw) > 2048:
            continue
        line = raw.rstrip(b"\r").decode("latin-1")
        f = line.split("\t")
        if len(f) < 2 or not f[0].isdigit() or not f[1].startswith("ev="):
            continue
        evs = f[1][3:]
        digits = ""
        for ch in evs:
            if ch.isdigit():
                digits += ch
            else:
                break
        if not digits:
            continue
        vals = {k: ABSENT for k in KEYS}
        for kv in f[2:]:
            if "=" not in kv:
                continue
            k, v = kv.split("=", 1)
            if not k.isdigit():
                continue
            neg = v.startswith("-")
            body = v[1:] if neg else v
            if not body.isdigit():
                continue
            if int(k) in vals:
                vals[int(k)] = -int(body) if neg else int(body)
        out.append("%d %d %d %d %d %d %d" % (int(f[0]), int(digits), vals[0], vals[31], vals[44], vals[45], vals[234]))
    return out


def run(path, seed, maxchunk):
    p = subprocess.run([EXE, path, str(seed), str(maxchunk)], capture_output=True, text=True)
    if p.returncode != 0:
        raise SystemExit("aexp_test.exe rc=%d %s" % (p.returncode, p.stderr))
    return p.stdout.splitlines()


def main():
    args = positional()
    src = args[0] if args else DEFAULT
    if not src:
        print("SKIP: no ae_events.log to read - pass its path, or set KRONOS_GAME_DIR (or --game <dir>) to the "
              "game install (the folder holding cod25\\, or cod25 itself)")
        sys.exit(0)
    if not os.path.isfile(src):
        print("STOP: %s is not a file" % src)
        sys.exit(2)
    tmp = tempfile.mkdtemp(prefix="aexp_")
    try:
        log = os.path.join(tmp, "ae_events.log")
        shutil.copyfile(src, log)
        data = open(log, "rb").read()
        ref = py_parse(data)
        checks = fails = 0

        def check(name, cond, detail=""):
            nonlocal checks, fails
            checks += 1
            print(("PASS " if cond else "FAIL ") + name + ("" if cond else "  " + detail))
            if not cond:
                fails += 1

        for seed, chunk in ((1, 1), (7, 13), (42, 300), (99, 4096), (5, 70000)):
            got = run(log, seed, chunk)
            first = next((i for i, (a, b) in enumerate(zip(got, ref)) if a != b), None)
            check("real log, chunk<=%d: %d records identical" % (chunk, len(ref)),
                  got == ref, "len %d vs %d, first diff at %s" % (len(got), len(ref), first))

        recs = [list(map(int, r.split())) for r in ref]
        e95 = [r for r in recs if r[1] == 95]
        with44 = sum(1 for r in e95 if r[4] != ABSENT)
        with45 = sum(1 for r in e95 if r[5] != ABSENT)
        both = sum(1 for r in e95 if r[4] != ABSENT and r[5] != ABSENT)
        check("ev=95 field 45 present exactly where 44 is (%d/%d/%d)" % (with44, with45, both),
              with44 == with45 == both and both > 0)
        check("ev=780 carries a round", any(r[1] == 780 and r[6] != ABSENT for r in recs))

        hand = (b"1700000000\tev=95\t0=20\t31=7\t45=8\t44=125186\r\n"
                b"junk line\n"
                b"1700000001\tev=780\t234=22\t240=0\n"
                b"1700000002\tev=95\t45=abc\t44=5\n"
                b"1700000003\tev=95\t45=" + b"9" * 3000 + b"\n"
                b"1700000004\tev=95\t0=5\t31=1")  # no trailing newline: must not be emitted
        hp = os.path.join(tmp, "hand.log")
        open(hp, "wb").write(hand)
        got = run(hp, 3, 5)
        want = ["1700000000 95 20 7 125186 8 -1", "1700000001 780 -1 -1 -1 -1 22", "1700000002 95 -1 -1 5 -1 -1"]
        check("hand lines (CRLF, junk, bad value, overlong, partial tail)", got == want, repr(got))

        print("%d / %d" % (checks - fails, checks))
        sys.exit(1 if fails else 0)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
