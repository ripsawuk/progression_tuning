"""Offline proof of clienthook build 31 - the forced publish, the native payment, the bounded log and the token
channel. Read-only
with respect to the game: nothing is installed, nothing is launched, and nothing under the game folder is written
(the client file is read, and the one driver that patches a mapped image is given a COPY of it).

    clienthook\\build.cmd                 -> build\\version.dll
    clienthook\\tools\\build_tests.cmd     -> the drivers in build\\
    python -I clienthook\\tools\\test_build24.py

NOTE ON THE NAME. This harness is called test_build24 because it was written for that build; it is the tree's
general offline proof and the banner it checks is the current one, build 31.

WHAT BUILD 24 IS. Build 23c, plus the one feature v1.0 dropped that a mod cannot do without: the client's own
serialise-and-publish (`client + 0x962E0`) called live, so the state a menu reads is taken during a match instead
of only at a mode boundary.

  ported, not redesigned   the 24-byte prologue guard (checked before every call), the fold-to-off on a mismatch
                           with one log line, the one-caller/no-lock discipline, the millisecond window, the
                           defer-not-drop coalesce, and the `publish: ...` log lines.
  added                    the guard, the window and the kill switch as a pure unit (`src\\publish.c`) with its own
                           driver; a second trigger (a record fingerprint, because camo/daily/weekly rows are
                           credited by their own events and can move with no payment); the kill switch file
                           `%TEMP%\\progression-tuning\\publish_off.txt`; the publish line at the same cadence as
                           the payment's (the first 3, then every 20th).
  unchanged                the proxy and its 17 exports, the one-file System32 resolve, the host guard, the 5 bytes
                           at 0x930D3 and its kill switch, ptsplash_paid, the g11 lock payload, master.c's five
                           call sites, the ev=109 boundary and the install gate.

WHAT IT CHECKS. artefact and pin; two clean builds byte-identical; the source tree (nine sources, where each guard
sits, the two triggers' placement); the image's strings - what it carries and what it does not; the personal-path
and identifier scan the release package uses; the client's own bytes; and every offline driver, with its count.
"""
import hashlib
import os
import re
import shutil
import struct
import subprocess
import sys
import tempfile

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
BUILD = os.path.join(ROOT, "build")
DLL = os.path.join(BUILD, "version.dll")
DLL_SHA = os.path.join(BUILD, "version.dll.sha256")
SRC = os.path.join(ROOT, "src")
PROXY = os.path.join(SRC, "proxy_main.c")
FRAME = os.path.join(SRC, "frame.c")
PUBLISH_C = os.path.join(SRC, "publish.c")
PUBLISH_H = os.path.join(SRC, "publish.h")


def game(*parts):
    """A path under the game's cod25 folder: --game <dir> first, then KRONOS_GAME_DIR, either form (the install
    folder holding cod25\\, or cod25 itself). "" when unset - the client is optional here, and the byte comparison
    says so and skips."""
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

# The builds this one must not be. Prefixes only; the full hash of each is in STATE.md.
BUILD23C_SHA = "87E5B569"     # the build this one replaces (v1.0's DLL, no forced publish)
BUILD23B_SHA = "0935EDCA"     # same tree, the match boundary moved to the payment's call site
BUILD23_SHA = "800AB36B"      # v1.0's first cut
BUILD21_SHA = "7A42F37D"      # the last full build before v1.0
BUILD20_SHA = "13AE37C8"      # the union build before the guard
BUILD22_SHA = "946026DD"      # the reduced package, never launched
SIZE_23C = 198144

# The patch sites this build writes, and nothing else: master.c's five call sites, nativepay's one.
MASTER_SITES = [0x93DFF, 0x96212, 0x9723D, 0x97626, 0x976AC]
NP_SITE = 0x930D3
PUB_RVA = 0x962E0

# The client's serialiser prologue, as publish.c carries it and as the client holds it.
PUB_SIG = bytes([0x48, 0x89, 0x5C, 0x24, 0x18, 0x55, 0x56, 0x57, 0x41, 0x54, 0x41, 0x55,
                 0x41, 0x56, 0x41, 0x57, 0x48, 0x83, 0xEC, 0x30, 0x48, 0x63, 0x05, 0xBD])

# What the package scan refuses in a source file or an image: a personal path or a private identifier. The home
# folder, the profile and the agent tool's temp folder are matched by shape, and the two private tree names are
# spelled in halves, so this scan carries neither of them itself.
_AGENT_TOOL = "open" + "code"
_PRIVATE = "project" + "-zm"
_STUDY = "kronos" + "-re"
PERSONAL = re.compile(r"[A-Za-z]:\\Users\\|/Users/|AppData|\\Temp\\" + _AGENT_TOOL
                      + r"|\.vscode|" + _PRIVATE + "|" + _STUDY + r"|\bD\d{2,3}\b|\bC\d{2}\b|launch \d+|the user")

# What build 23c dropped and this build still does not carry.
DROPPED = [
    "ladder: challenges.tsv served",
    "g10_armory_cfg",
    "tier: table loaded",
    "pay: ledger",
    "dat write via=",
    "award: armed",
    "io: observer armed",
    "nativepay: sums",
    "ae window",
    "frame: reader armed",
    "clienthook_ladder_scale.txt",
    "clienthook_g10_off.txt",
]
# What it keeps, and what the forced publish adds.
KEPT = [
    "zm_g11_arm",
    "zm_g11_ver",
    "ptsplash_paid",
    "master: %d call sites hooked",
    "nativepay: hook installed",
    "nativepay: ev=95 loot=%u f45=%d",
    "pubxp: armed",
    "g11: armed",
    "init: version.dll resolved from ",
    "publish: challenge state re-published live (#%ld)",
    "publish: armed - the client's own serialiser",
    "publish: the client build does not match rva 0x962e0 - refused, off",
    "publish: coalesced (%ld so far, min %d ms)",
    "publish: disabled by file (%s)",
    "%TEMP%\\progression-tuning\\publish_off.txt",
]
# build 23c's match boundary: the payment's own call site, so it does not need `log_events`.
KEPT_SOURCE = [
    ("src\\nativepay.h", "#define NP_EVENT_MATCH_START 0x6Du"),
    ("src\\nativepay.h", "void nativepay_set_match_reset_hook(np_reset_fn fn);"),
    ("src\\nativepay.c", "if (id == NP_EVENT_MATCH_START)"),
    ("src\\nativepay.c", "int nativepay_hook_live(void)"),
    ("src\\frame.c", "nativepay_set_match_reset_hook(pubxp_match_reset);"),
    ("src\\frame.c", "!nativepay_hook_live() && !said_nopay"),
    ("src\\nativepay.h", "typedef void (*np_reset_fn)(void);"),
]

# The files this tree ships under src\, and the only ones any scan here reads: the nine sources build.cmd names,
# their seven headers, and the export definition. A file that is not on this list is not part of the build.
SHIPPED_SRC = ["frame.c", "g11.c", "master.c", "nativepay.c", "proxy_main.c", "publish.c", "pubxp.c",
               "resolve.c", "tokens.c", "g11.h", "master.h", "nativepay.h", "publish.h", "pubxp.h", "resolve.h",
               "tokens.h", "version_proxy.def"]

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


def read(path):
    with open(path, "r", encoding="utf-8", errors="replace") as fh:
        return fh.read()


def sha256(path):
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest().upper()


def export_names(path):
    """The DLL's own export table, read from the file (no toolchain, no loader)."""
    with open(path, "rb") as fh:
        d = fh.read()
    e = struct.unpack_from("<I", d, 0x3C)[0]
    nsec = struct.unpack_from("<H", d, e + 6)[0]
    optsz = struct.unpack_from("<H", d, e + 20)[0]
    base = e + 24 + optsz
    erva = struct.unpack_from("<I", d, e + 24 + 112)[0]

    def r2o(rva):
        for i in range(nsec):
            o = base + i * 40
            va, vsz = struct.unpack_from("<II", d, o + 12)
            ro, rs = struct.unpack_from("<II", d, o + 20)
            if va <= rva < va + max(vsz, rs):
                return ro + (rva - va)
        return None

    fo = r2o(erva)
    nnames = struct.unpack_from("<I", d, fo + 24)[0]
    names_rva = struct.unpack_from("<I", d, fo + 32)[0]
    no = r2o(names_rva)
    out = []
    for i in range(nnames):
        nr = struct.unpack_from("<I", d, no + 4 * i)[0]
        o = r2o(nr)
        out.append(d[o:d.index(b"\x00", o)].decode("ascii"))
    return sorted(out)


def client_bytes(rva, n):
    """n bytes of the pinned client at an RVA, by its own section table (read-only; no toolchain)."""
    with open(CLIENT, "rb") as fh:
        data = fh.read()
    e = struct.unpack_from("<I", data, 0x3C)[0]
    nsec = struct.unpack_from("<H", data, e + 6)[0]
    opt = struct.unpack_from("<H", data, e + 20)[0]
    base = e + 24 + opt
    for i in range(nsec):
        off = base + i * 40
        va, vsize = struct.unpack_from("<II", data, off + 12)
        raw_off, raw_size = struct.unpack_from("<II", data, off + 20)
        if va <= rva < va + max(vsize, raw_size):
            fo = raw_off + (rva - va)
            return data[fo:fo + n]
    return b""


def scratch(name):
    d = os.path.join(tempfile.gettempdir(), "build24-" + name)
    shutil.rmtree(d, ignore_errors=True)
    os.makedirs(d)
    return d


def drive(exe, args, want_ok, label):
    """Run a driver, print its tail, and check its own count line carries `want_ok` checks (None = don't care)."""
    r = subprocess.run([exe] + list(args), capture_output=True, text=True, timeout=600)
    out = (r.stdout or "") + (r.stderr or "")
    last = [l for l in out.split("\n") if l.strip()]
    print("  | " + (last[-1] if last else "(no output)"))
    check("%s exits 0" % label, r.returncode == 0, "rc=%d" % r.returncode)
    if want_ok is not None:
        m = re.search(r"OK - (\d+) checks|(\d+) passed, \d+ failed", out)
        got = None
        if m:
            got = int(m.group(1) or m.group(2))
        check("%s reports its %d checks" % (label, want_ok), got == want_ok, ("%s checks" % got) if got else
              "no count line")
    return out


def build_once():
    r = subprocess.run(["cmd", "/c", os.path.join(ROOT, "build.cmd")], capture_output=True, text=True, timeout=900)
    text = (r.stdout or "") + (r.stderr or "")
    return r.returncode, text


def main():
    print("clienthook build 31 - the forced publish, the native payment, the bounded log, the token channel - " + ROOT)
    print("")
    if not CLIENT:
        print("NOTE  KRONOS_GAME_DIR is not set and no --game was given - the client file cannot be read, so the "
              "byte comparison is skipped")
    for p in (DLL, os.path.join(BUILD, "guard_test.exe"), os.path.join(BUILD, "ch_passthru_host.exe"),
              os.path.join(BUILD, "publish_test.exe")):
        if not os.path.isfile(p):
            print("STOP: %s is missing - run clienthook\\build.cmd and clienthook\\tools\\build_tests.cmd." % p)
            return 1

    # ---- 1. artefact --------------------------------------------------------------------------------
    print("")
    print("ARTEFACT")
    size = os.path.getsize(DLL)
    h = sha256(DLL)
    print("version.dll %d B / %s" % (size, h))
    pin = read(DLL_SHA).strip()
    check("build\\version.dll.sha256 records this DLL's hash", h.lower() in pin.lower(),
          pin.split()[0][:16] + "...")
    check("the image is not build 23c's (the one it replaces)", not h.startswith(BUILD23C_SHA), h[:8])
    for gone_sha, name in ((BUILD23B_SHA, "23b's"), (BUILD23_SHA, "23's"), (BUILD21_SHA, "21's"),
                           (BUILD20_SHA, "20's"), (BUILD22_SHA, "22's reduced package")):
        check("the image is not build %s" % name, not h.startswith(gone_sha), h[:8])
    raw = open(DLL, "rb").read()
    text = raw.decode("latin-1")
    check("the size is not build 23c's (the new unit and its caller changed the image)", size != SIZE_23C,
          "%d B" % size)
    check("the banner says build 31", "version.dll build 31" in text)
    for gone in ("version.dll build 30", "version.dll build 25", "version.dll build 23c",
                "version.dll build 23b", "version.dll build 23",
                "version.dll build 21", "version.dll build 20", "version.dll build 17"):
        check("the image does not carry the old banner %r" % gone, gone not in text)

    # ---- 2. two clean builds, byte-identical --------------------------------------------------------
    print("")
    print("REBUILD  build.cmd twice, /Brepro, /W3")
    rc1, out1 = build_once()
    h1 = sha256(DLL)
    rc2, out2 = build_once()
    h2 = sha256(DLL)
    check("the first build exits 0", rc1 == 0, "rc=%d" % rc1)
    check("the second build exits 0", rc2 == 0, "rc=%d" % rc2)
    check("neither build printed a warning or an error",
          "warning C" not in out1 + out2 and "error C" not in out1 + out2 and "BUILD FAILED" not in out1 + out2)
    check("two clean builds are byte-identical", h1 == h2, "%s / %s" % (h1[:16], h2[:16]))
    check("and that hash is the one the .sha256 pin records", sha256(DLL).lower() in read(DLL_SHA).lower())
    check("the artefact is the artefact measured in section 1", sha256(DLL) == h)
    check("/W3 and /Brepro are still the build's flags", "/W3" in read(os.path.join(ROOT, "build.cmd"))
          and "/Brepro" in read(os.path.join(ROOT, "build.cmd")))

    # ---- 3. the source tree -------------------------------------------------------------------------
    print("")
    print("SOURCE  one tree, the kept files, and what each one holds")
    build_cmd = read(os.path.join(ROOT, "build.cmd"))
    cl_text = "\n".join(l for l in build_cmd.replace("^", " ").split("\n") if l.strip().startswith("cl "))
    sources = sorted(set(re.findall(r"([a-z0-9_]+\.c)", cl_text)))
    check("build.cmd compiles exactly the nine sources",
          sources == ["frame.c", "g11.c", "master.c", "nativepay.c", "proxy_main.c", "publish.c",
                      "pubxp.c", "resolve.c", "tokens.c"], ", ".join(sources))
    for gone in ("io_probe.c", "ladder.c", "ladder.h", "g10seed.c", "g10seed.h", "pay.c", "pay.h", "aexp.c",
                 "aexp.h"):
        check("src\\%s is gone from the tree" % gone, not os.path.isfile(os.path.join(SRC, gone)))
    for kept in ("frame.c", "proxy_main.c", "nativepay.c", "pubxp.c", "g11.c", "master.c",
                 "publish.c", "tokens.c", "nativepay.h", "pubxp.h", "g11.h", "master.h", "publish.h",
                 "tokens.h", "version_proxy.def"):
        check("src\\%s is there" % kept, os.path.isfile(os.path.join(SRC, kept)))

    proxy = read(PROXY)
    check("the host rule is one constant with the game's image name",
          '#define CH_GAME_IMAGE L"cod25-cod.exe"' in proxy)
    check("the decision is a function of the image path (so it is unit-testable)",
          "BOOL ch_arm_for_image(const wchar_t *image_path)" in proxy)
    check("the host comes from the loader, not from argv or a file",
          "GetModuleFileNameW(NULL, path, MAX_PATH)" in proxy)
    logfn = proxy[proxy.index("static void log_line"):proxy.index("static BOOL CALLBACK load_orig")]
    check("log_line returns before it touches the disk when the process is not the game",
          logfn.index("if (!g_armed)") < logfn.index("CreateFileW"))
    dllmain = proxy[proxy.index("BOOL APIENTRY DllMain"):]
    attach = dllmain[dllmain.index("DLL_PROCESS_ATTACH"):dllmain.index("DLL_PROCESS_DETACH")]
    detach = dllmain[dllmain.index("DLL_PROCESS_DETACH"):]
    check("ATTACH asks the guard before it logs, and before the frame or the payment starts",
          attach.index("g_armed = ch_arm_here();") < attach.index("log_line(")
          and attach.index("if (!g_armed)") < attach.index("ch_frame_start();")
          and attach.index("if (!g_armed)") < attach.index("nativepay_start();"))
    check("DETACH asks the guard before it flushes or logs",
          detach.index("if (!g_armed)") < detach.index("nativepay_stop();")
          and detach.index("if (!g_armed)") < detach.index('log_line("proxy detached")'))
    check("the frame starts before the payment (the gate and the paid hook come from it)",
          attach.index("ch_frame_start();") < attach.index("nativepay_start();"))
    check("the DLL resolves the SYSTEM version.dll by full path, one file on disk",
          "GetSystemDirectoryW(path, MAX_PATH)" in proxy and "LOAD_LIBRARY_SEARCH_SYSTEM32" in proxy)
    check("this tree has exactly one DllMain",
          sum(read(os.path.join(SRC, f)).count("DllMain(HMODULE") for f in SHIPPED_SRC if f.endswith(".c")) == 1)
    check("src\\ holds exactly the shipped files, and nothing else",
          sorted(os.listdir(SRC)) == sorted(SHIPPED_SRC),
          ", ".join(sorted(set(os.listdir(SRC)) ^ set(SHIPPED_SRC))) or "same set")

    frame = read(FRAME)
    check("the frame creates its five threads and no more", frame.count("= CreateThread(NULL, 0, ") == 5,
          "%d CreateThread in frame.c" % frame.count("= CreateThread(NULL, 0, "))
    check("the fourth one is the forced publish's",
          frame.count("= CreateThread(NULL, 0, publish_thread, NULL, 0, NULL)") == 1)
    check("the publish gate is initialised before any thread can raise or honour a want",
          frame.index("pub_init(&PUB);") < frame.index("CreateThread(NULL, 0, publish_thread"))
    check("the frame patches no import slot at all (there is no reader)",
          "patch_module" not in frame and "patch_one" not in frame and "strcmp(fn, " not in frame
          and "hook_write_file" not in frame)
    check("the frame creates the install gate and hands it to both patchers",
          "master_set_install_gate(gate);" in frame and "nativepay_set_install_gate(gate);" in frame)
    check("the frame sets the paid hook before anything can call it",
          "nativepay_set_paid_hook(pubxp_on_paid);" in frame)
    check("the frame holds no event reader (no aexp, no ae_ stream state)",
          "aexp" not in frame and "ae_on_rec" not in frame and "ae_events" not in frame)
    check("the frame installs master.c's hook at the first sight of the client",
          "master_install(client);" in frame)

    # ---- 3b. the forced publish's two triggers, and where they sit ------------------------------------
    print("")
    print("PUBLISH  the ported call, its guard, and the two things that ask for one")
    paid = frame[frame.index("void pubxp_on_paid(unsigned int loot, int amount, int phase)\n{"):
                 frame.index("void pubxp_match_reset(void)\n{")]
    check("the paid hook raises the publish want exactly once", paid.count("pub_want(&PUB);") == 1,
          "%d call(s)" % paid.count("pub_want(&PUB);"))
    check("it does so on the phase that runs after the award returned, and only for a real payment",
          paid.index("if (loot == 0)") < paid.index("pub_want(&PUB);") < paid.index("if (loot != PXP_PEND_LOOT"))
    check("the want is raised before the branches that end the call early (it is not the other channel's business)",
          paid.index("pub_want(&PUB);") < paid.index("if (loot != PXP_PEND_LOOT || PXP_OFF)"))
    reset = frame[frame.index("void pubxp_match_reset(void)\n{"):]
    reset = reset[:reset.index("static void pxp_latch")]
    check("the match-start seam marks the match live before anything else",
          reset.index("pub_match_live(&PUB);") < reset.index("if (PXP_OFF || !PXP_ARMED)"),
          "the flag does not depend on the paid channel having armed")
    thread = frame[frame.index("static DWORD WINAPI publish_thread(LPVOID unused)"):frame.index(
        "// --- the ops check patch")]
    check("the thread checks the kill switch before it arms", thread.index("pub_off_present(NULL)")
          < thread.index('ch_logf("publish: armed'))
    check("a present kill switch latches the feature off and stops the thread",
          thread.index("InterlockedExchange(&PUB.off, 1);") < thread.index("return 0;"))
    check("the arm line is one line and names the target, the guard and the window",
          thread.count("publish: armed") == 1 and "rva 0x962E0" in thread and "PUB_SIG_LEN" in thread
          and "PUB_MIN_MS" in thread)
    check("the target is the client module plus the one rva, and NULL when the module is absent",
          "(const unsigned char *)client + PUB_RVA : NULL" in thread)
    check("the record scan runs before the decision, only while the module is there",
          thread.index("pub_scan_due(&PUB, now)") < thread.index("PUB_VERDICT v = pub_step"))
    check("the scan reads the same record array the paid channel reads (one source for the addresses)",
          "pxp_records(client, &recs, &n)" in thread and "pub_fingerprint(recs, n)" in thread)
    check("the call is the plain no-argument call into that address",
          "((void (*)(void))at)();" in thread)
    check("the publish line is rate-limited: the first 3, then every PUB_LOG_EACH",
          "n <= 3 || (n % PUB_LOG_EACH) == 0" in thread)
    check("every refusal is logged, and the coalesce is not a refusal",
          'publish: the client build does not match rva 0x962e0 - refused, off' in thread
          and 'publish: the client module is not loaded - off' in thread
          and 'publish: coalesced (%ld so far, min %d ms)' in thread)
    check("a latched-off feature scans nothing and calls nothing",
          thread.index("if (InterlockedCompareExchange(&PUB.off, 0, 0) != 0)") < thread.index("pub_scan_due"))

    pubc = read(PUBLISH_C)
    pubh = read(PUBLISH_H)
    sig_in_c = re.search(r"const unsigned char PUB_SIG\[PUB_SIG_LEN\] = \{(.*?)\};", pubc, re.S)
    got_sig = bytes(int(x, 16) for x in re.findall(r"0x([0-9A-Fa-f]{2})", sig_in_c.group(1))) if sig_in_c else b""
    check("the shipped signature table is the client's own 24 bytes", got_sig == PUB_SIG, got_sig.hex())
    check("the guard is a memcmp of exactly those 24 bytes over the target",
          "memcmp(at, PUB_SIG, PUB_SIG_LEN) == 0" in pubc)
    check("a failed guard latches the feature off (it does not retry into an unknown address)",
          "InterlockedExchange(&g->off, 1);" in pubc and "return PUB_REFUSED;" in pubc)
    check("a want inside the window is counted and the want is KEPT",
          "g->want, 0" not in pubc[pubc.index("InterlockedIncrement(&g->skip);"):pubc.index("return PUB_COALESCED;")],
          "the coalesce path never clears the want")
    check("the window is checked before the coalesce is counted",
          pubc.index("now_ms - g->last_ms < (unsigned long long)PUB_MIN_MS")
          < pubc.index("InterlockedIncrement(&g->skip);"))
    check("the window is measured from the start of the last call",
          "now_ms - g->last_ms < (unsigned long long)PUB_MIN_MS" in pubc)
    check("the unit's numbers are the ones stated: 1,000 ms and the first 3 then every 20th",
          "#define PUB_MIN_MS 1000" in pubh and "#define PUB_LOG_EACH 20" in pubh
          and "#define PUB_RVA 0x962E0u" in pubh and "#define PUB_SIG_LEN 24" in pubh)
    check("the kill switch is the same mechanism as the payment's and the master hook's",
          'L"%sprogression-tuning\\\\publish_off.txt"' in pubc
          and "GetFileAttributesW(path)" in pubc and "GetTempPathW(MAX_PATH, dir)" in pubc)
    check("the fingerprint covers progress, status/level and the prestige byte",
          "MASTER_REC_XP, 8" in pubc and "MASTER_REC_LEVEL - 1, 2" in pubc and "MASTER_REC_PRESTIGE, 1" in pubc)
    check("the first fingerprint is a baseline, and a move outside a match re-baselines without a want",
          pubc.index("if (!g->have_fp)") < pubc.index("if (fp == g->fp)") < pubc.index("if (!g->live)"))
    check("publish.c reads no client address (the whole gate is proved offline)",
          "0x962E0" not in pubc and "XINPUT9_1_0.dll" not in pubc)

    master = read(os.path.join(SRC, "master.c"))
    np_src = read(os.path.join(SRC, "nativepay.c"))
    check("master.c's site table is the five recorded call sites, in order",
          "{0x93DFF, 0x96212, 0x9723D, 0x97626, 0x976AC}" in master)
    check("master.c's formula is the build 21 one, with the client's own step and cap",
          "(unsigned long long)count + (xp - last) / (unsigned long long)step" in master
          and "#define MASTER_STEP_DEFAULT 1800" in read(os.path.join(SRC, "master.h"))
          and "#define MASTER_LEVEL_CAP 250" in read(os.path.join(SRC, "master.h")))
    check("nativepay.c still names its one call site 0x930D3", "0x930D3" in np_src)
    check("nativepay.c keeps its kill switch", "nativepay_off.txt" in np_src)
    check("nativepay.c's log cap is the first 3 then every 20th",
          "#define NP_CAP_FIRST 3" in np_src and "#define NP_CAP_EVERY 20" in np_src)
    check("the publish gate is the only new write path, and it writes no client code",
          "VirtualProtect" not in pubc and "PUB_RVA" in pubh)
    ranges = sorted((s, s + 5) for s in MASTER_SITES + [NP_SITE])
    check("the six written ranges are pairwise disjoint", all(a[1] <= b[0] for a, b in zip(ranges, ranges[1:])),
          ", ".join("0x%X+5" % a for a, _ in ranges))
    check("the forced publish adds no written range: it calls, it does not patch",
          "0x962E0" not in " ".join("0x%X" % s for s in MASTER_SITES + [NP_SITE]))

    # ---- 4. the image's strings ---------------------------------------------------------------------
    print("")
    print("STRINGS  what the image carries, and what it does not")
    for s in DROPPED:
        check("the image does not carry %r" % s, s not in text)
    for s in KEPT:
        check("the image carries %r" % s, s in text)
    exports = export_names(DLL)
    want_exports = sorted(["GetFileVersionInfoA", "GetFileVersionInfoByHandle", "GetFileVersionInfoExA",
                           "GetFileVersionInfoExW", "GetFileVersionInfoSizeA", "GetFileVersionInfoSizeExA",
                           "GetFileVersionInfoSizeExW", "GetFileVersionInfoSizeW", "GetFileVersionInfoW",
                           "VerFindFileA", "VerFindFileW", "VerInstallFileA", "VerInstallFileW",
                           "VerLanguageNameA", "VerLanguageNameW", "VerQueryValueA", "VerQueryValueW"])
    check("the export table is exactly the system DLL's 17 names, and nothing of ours",
          exports == want_exports, "%d exports" % len(exports))
    check("all 17 export names are in the image",
          all(n in text for n in ("GetFileVersionInfoSizeW", "GetFileVersionInfoA", "VerFindFileW",
                                  "VerInstallFileW", "VerLanguageNameW", "VerQueryValueW",
                                  "GetFileVersionInfoByHandle")))

    # ---- 4b. the package scan -----------------------------------------------------------------------
    print("")
    print("SCAN  no personal path and no private identifier, in the source or in the image")
    src_hits = []
    for f in SHIPPED_SRC:
        for m in PERSONAL.finditer(read(os.path.join(SRC, f))):
            src_hits.append("%s: %s" % (f, m.group(0)))
    check("no source file under src\\ matches the scan", not src_hits, ", ".join(src_hits[:6]))
    img_hits = sorted(set(m.group(0) for m in PERSONAL.finditer(text)))
    check("no string in the image matches the scan", not img_hits, ", ".join(img_hits[:6]))

    # ---- 4c. the match boundary, without `log_events` ------------------------------------------------
    print("")
    print("BOUNDARY  ev=109 reaches the DLL through the payment's own call site")
    for path, needle in KEPT_SOURCE:
        src_text = read(os.path.join(ROOT, path.replace("\\", os.sep)))
        check("%s carries %r" % (path, needle), needle in src_text)
    np_text = read(os.path.join(SRC, "nativepay.c"))
    wrapper = np_text[np_text.index("unsigned long long nativepay_call(const unsigned int *ev)"):
                      np_text.index("const void *nativepay_thunk_address")]
    check("the wrapper calls the hook from exactly one place", wrapper.count("reset()") == 1,
          "%d call(s)" % wrapper.count("reset()"))
    check("the hook call sits between the ev=109 test and the pass-through that follows it",
          wrapper.index("if (id == NP_EVENT_MATCH_START)") < wrapper.index("reset()")
          < wrapper.index("if (id == NP_EVENT_MATCH_START)") + 200
          and "return orig(ev);" in wrapper[wrapper.index("reset()"):wrapper.index("reset()") + 300])
    check("the hook is only called when it is set (NULL is harmless)", "reset != NULL" in wrapper)
    check("the branch only hands the event on - no other call is made there",
          wrapper[wrapper.index("if (id == NP_EVENT_MATCH_START)"):].index("return orig(ev);")
          < wrapper[wrapper.index("if (id == NP_EVENT_MATCH_START)"):].index("\n    }"))
    check("the ev=95 path cannot reach it: the branch is inside the non-95 early return",
          wrapper.index("if (id != NP_EVENT_XP_ID)") < wrapper.index("if (id == NP_EVENT_MATCH_START)")
          < wrapper.index("np_event e;"))
    check("the boundary is wired once, from the payment's own call site",
          frame.count("nativepay_set_match_reset_hook(pubxp_match_reset);") == 1
          and "pub_match_live(&PUB);" in frame)
    pubxp_c = read(os.path.join(SRC, "pubxp.c"))
    reset_fn = pubxp_c[pubxp_c.index("int pxp_reset_match"):pubxp_c.index("int pxp_render")]
    check("the reset itself is a no-op when no gun has a per-match base (idempotent)",
          "if (!armed)" in reset_fn and reset_fn.index("if (!armed)") < reset_fn.index("pxp_render(L)"))

    # ---- 4d. the token channel's dvar and the file behind it -----------------------------------------
    print("")
    print("TOKENS  a dvar from boot, one line, and the file it is saved to")
    tk = read(os.path.join(SRC, "tokens.c"))
    tkh = read(os.path.join(SRC, "tokens.h"))
    check("the channel is the one name the mod's Lua and GSC use", '#define TOKENS_NAME "pt_tokens_ch"' in tkh,
          "tokens.h")
    check("the seed line is the one the GSC writes when it creates the dvar",
          '#define TOKENS_DEFAULT "p=0;w=0;n=0"' in tkh)
    check("the form is one line of 512 chars at most", "#define TOKENS_MAX 512" in tkh)
    check("the path is the dll's own directory plus players\\tokens.txt",
          r'TK_SUBDIR L"players"' in tkh + tk and r'TK_FILE L"tokens.txt"' in tkh + tk)
    check("the client's players folder is read, never made", "CreateDirectoryW" not in tk)
    check("it is armed where the register, the hash and the slot are all proved",
          frame.index("long off = (long)*(int *)") < frame.index("tokens_arm(reg, salt, off);")
          < frame.index("g11_dvar_pass("))
    check("the value goes into the client's own string slot, not into a copy of it",
          "char **value = (char **)((char *)d + slot);" in tk and "*value = TK_DISK;" in tk)
    check("the write is a .tmp and a replace-rename, the client store's own order",
          r'_snwprintf_s(tmp, MAX_PATH, _TRUNCATE, L"%s.tmp", path)' in tk
          and "MoveFileExW(tmp, path, MOVEFILE_REPLACE_EXISTING | MOVEFILE_WRITE_THROUGH)" in tk)
    check("a value outside the alphabet is never written to the file",
          tk.count("!tokens_valid(v, n)") == 2, "%d guard(s)" % tk.count("!tokens_valid(v, n)"))
    check("the tick rides the frame's existing thread and creates none", "tokens_tick();" in frame
          and frame.count("= CreateThread(NULL, 0, ") == 5)
    check("the detach flush sits inside the armed branch",
          detach.index("if (!g_armed)") < detach.index("tokens_stop();"))
    check("the three log lines are the ones a reader of clienthook.log expects",
          '"tokens: file %s"' in tk and '"tokens: registered %s = %s"' in tk and '"tokens: saved %s"' in tk)
    check("a rejected file still registers the seed line", "strcpy_s(line, sizeof(line), TOKENS_DEFAULT);" in tk)
    check("the saved line is rate-limited after the first",
          "#define TK_LOG_MS 30000" in tk and "static int tk_may_say(ULONGLONG now)" in tk)

    # ---- 5. the client's own bytes (read-only) ------------------------------------------------------
    print("")
    print("CLIENT  the six sites still hold what the guards expect, and the publish target is where it was")
    if os.path.isfile(CLIENT):
        check("nativepay's site 0x930D3 is still E8 48 07 00 00",
              client_bytes(NP_SITE, 5) == b"\xE8\x48\x07\x00\x00", client_bytes(NP_SITE, 5).hex())
        check("master's five sites are still E8 rel32 calls",
              all(client_bytes(s, 1) == b"\xE8" for s in MASTER_SITES),
              " ".join(client_bytes(s, 1).hex() for s in MASTER_SITES))
        check("none of the six sits inside the level function's 17-byte prologue",
              all(not (0x96680 <= s < 0x96691) for s in MASTER_SITES + [NP_SITE]))
        check("the level function's own prologue is the recorded 17 bytes",
              client_bytes(0x96680, 17) == bytes([0x40, 0x53, 0x55, 0x56, 0x57, 0x41, 0x54, 0x41, 0x55, 0x41,
                                                  0x56, 0x41, 0x57, 0x48, 0x83, 0xEC, 0x28]),
              client_bytes(0x96680, 17).hex())
        check("the publish target's 24 bytes are the signature the unit carries",
              client_bytes(PUB_RVA, 24) == PUB_SIG, client_bytes(PUB_RVA, 24).hex())
        check("and that target sits outside every written range",
              all(not (s <= PUB_RVA < s + 5) for s in MASTER_SITES + [NP_SITE]))
    else:
        note("the client file is not at %s - the byte comparison was skipped" % CLIENT)

    # ---- 6. the drivers -----------------------------------------------------------------------------
    print("")
    print("DRIVERS  every offline proof, with its count")
    drive(os.path.join(BUILD, "guard_test.exe"), ["self"], 19, "guard_test self")
    if os.path.isfile(CLIENT):
        drive(os.path.join(BUILD, "nativepay_test.exe"), ["self", CLIENT], 70, "nativepay_test self")
    else:
        note("nativepay_test self reads the client for its guard checks, and the game folder is a setting - "
             "KRONOS_GAME_DIR is not set, so that driver was skipped")
    if os.path.isfile(CLIENT):
        drive(os.path.join(BUILD, "nativepay_test.exe"), ["sites", CLIENT], 9, "nativepay_test sites")
        # the install driver patches a mapped image: give it a COPY, so nothing under the game folder is used
        d = scratch("client")
        copy = os.path.join(d, "XINPUT9_1_0.dll")
        shutil.copyfile(CLIENT, copy)
        before = sha256(copy)
        drive(os.path.join(BUILD, "nativepay_test.exe"), ["install", copy], 12, "nativepay_test install")
        check("the install driver left the copied client file byte-identical", sha256(copy) == before)
    drive(os.path.join(BUILD, "nativepay_test.exe"), ["proxy", DLL], 26, "nativepay_test proxy")
    d = scratch("off")
    r = subprocess.run([os.path.join(BUILD, "nativepay_test.exe"), "off", d + os.sep], capture_output=True,
                       text=True, timeout=300)
    check("the payment's kill switch reads absent in a clean directory", (r.stdout or "").strip() == "0",
          (r.stdout or "").strip())
    os.makedirs(os.path.join(d, "progression-tuning"), exist_ok=True)
    open(os.path.join(d, "progression-tuning", "nativepay_off.txt"), "w").close()
    r = subprocess.run([os.path.join(BUILD, "nativepay_test.exe"), "off", d + os.sep], capture_output=True,
                       text=True, timeout=300)
    check("and present when its file is there", (r.stdout or "").strip() == "1", (r.stdout or "").strip())

    drive(os.path.join(BUILD, "publish_test.exe"), ["self"], 53, "publish_test self")
    d = scratch("puboff")
    r = subprocess.run([os.path.join(BUILD, "publish_test.exe"), "off", d + os.sep], capture_output=True,
                       text=True, timeout=300)
    check("the publish kill switch reads absent in a clean directory", (r.stdout or "").strip() == "0",
          (r.stdout or "").strip())
    os.makedirs(os.path.join(d, "progression-tuning"), exist_ok=True)
    open(os.path.join(d, "progression-tuning", "publish_off.txt"), "w").close()
    r = subprocess.run([os.path.join(BUILD, "publish_test.exe"), "off", d + os.sep], capture_output=True,
                       text=True, timeout=300)
    check("and present when its own file is there", (r.stdout or "").strip() == "1", (r.stdout or "").strip())
    r = subprocess.run([os.path.join(BUILD, "publish_test.exe"), "off", d + os.sep + "missing" + os.sep],
                       capture_output=True, text=True, timeout=300)
    check("a directory with no switch of its own reads absent", (r.stdout or "").strip() == "0",
          (r.stdout or "").strip())

    drive(os.path.join(BUILD, "pubxp_test.exe"), ["self"], 45, "pubxp_test self")
    # the token channel's driver never goes near the game: a fabricated dvar_t, and a folder under build\
    arm_root = os.path.join(BUILD, "tokens-arm")
    shutil.rmtree(arm_root, ignore_errors=True)
    os.makedirs(arm_root)
    drive(os.path.join(BUILD, "tokens_test.exe"), ["self"], 25, "tokens_test self")
    for mode in ("valid", "none", "bad"):
        d = os.path.join(arm_root, mode)
        os.makedirs(d, exist_ok=True)
        drive(os.path.join(BUILD, "tokens_test.exe"), ["arm", d, mode], 16, "tokens_test arm " + mode)
    # the one mode with no players folder at all: the save is skipped and the folder stays missing
    d = os.path.join(arm_root, "nofolder")
    os.makedirs(d, exist_ok=True)
    drive(os.path.join(BUILD, "tokens_test.exe"), ["arm", d, "nofolder"], 11, "tokens_test arm nofolder")
    drive(os.path.join(BUILD, "g11_test.exe"), ["self"], 51, "g11_test self")
    drive(os.path.join(BUILD, "master_test.exe"), ["self"], 53, "master_test self")
    drive(os.path.join(BUILD, "detour_test.exe"), ["self"], 19, "detour_test self")

    # the reader is gone: no shipped source names its symbols, and no kernel32 file call is taken
    reader_hits = []
    for f in SHIPPED_SRC:
        t = read(os.path.join(SRC, f))
        for needle in ("aexp", "ae_on_rec", "ae_sniff", "ae_adopt", "ae_absorb", "AE_REJECT",
                       "hook_write_file", "hook_create_file", "patch_module"):
            if needle in t:
                reader_hits.append("%s: %s" % (f, needle))
    check("no source under src\\ names the event reader", not reader_hits, ", ".join(reader_hits[:6]))

    # ---- 7. a foreign process, and the game's own name ----------------------------------------------
    print("")
    print("HOST GUARD  pass-through x3, then the armed control")
    d = scratch("pass")
    dll_copy = os.path.join(d, "version.dll")
    host_copy = os.path.join(d, "ch_passthru_host.exe")
    shutil.copyfile(DLL, dll_copy)
    shutil.copyfile(os.path.join(BUILD, "ch_passthru_host.exe"), host_copy)
    logp = os.path.join(d, "clienthook.log")
    for run in range(3):
        r = subprocess.run([host_copy, "pass", dll_copy], capture_output=True, text=True, timeout=300)
        outp = r.stdout or ""
        check("pass run %d: exit 0 and the forward answered" % (run + 1),
              r.returncode == 0 and "host: answers equal = YES" in outp, "rc=%d" % r.returncode)
        check("pass run %d: the DLL wrote no clienthook.log in a foreign process" % (run + 1),
              not os.path.isfile(logp))
    check("after three pass-through runs the directory holds only the two files",
          sorted(os.listdir(d)) == ["ch_passthru_host.exe", "version.dll"], ", ".join(sorted(os.listdir(d))))

    a = scratch("armed")
    dll_a = os.path.join(a, "version.dll")
    game = os.path.join(a, "cod25-cod.exe")
    shutil.copyfile(DLL, dll_a)
    shutil.copyfile(os.path.join(BUILD, "ch_passthru_host.exe"), game)
    r = subprocess.run([game, "armed", dll_a], capture_output=True, text=True, timeout=300)
    outp = r.stdout or ""
    armed_log = read(os.path.join(a, "clienthook.log")) if os.path.isfile(os.path.join(a, "clienthook.log")) else ""
    # the forced publish's arm line is written by ITS thread the moment it starts, so a host that exits before the
    # scheduler runs it can leave it out. Three attempts settle that without weakening the check.
    arm_runs = 1
    while "publish: armed - the client's own serialiser" not in armed_log and arm_runs < 3:
        arm_runs += 1
        shutil.rmtree(a, ignore_errors=True)
        os.makedirs(a)
        shutil.copyfile(DLL, dll_a)
        shutil.copyfile(os.path.join(BUILD, "ch_passthru_host.exe"), game)
        subprocess.run([game, "armed", dll_a], capture_output=True, text=True, timeout=300)
        armed_log = read(os.path.join(a, "clienthook.log")) if os.path.isfile(os.path.join(a, "clienthook.log")) else ""
    if arm_runs > 1:
        note("the publish arm line appeared on armed-host attempt %d of 3 (thread scheduling, not a fault)" % arm_runs)
    check("the armed control exits 0", r.returncode == 0, "rc=%d" % r.returncode)
    check("it forwarded the same export", "host: answers equal = YES" in outp)
    check("armed by the game's image name, the DLL DID write its log", os.path.isfile(os.path.join(a, "clienthook.log")),
          "%d lines" % len(armed_log.splitlines()))
    check("the log carries build 31's banner", "version.dll build 31" in armed_log)
    check("the log names the module it resolved at run time", "init: version.dll resolved from " in armed_log)
    resolved = ""
    for line in armed_log.split("\n"):
        if "init: version.dll resolved from " in line:
            resolved = line.split("init: version.dll resolved from ", 1)[1].strip().lower()
    check("and it is the SYSTEM32 version.dll, not the copy under test",
          resolved.startswith(os.path.join(os.environ.get("SystemRoot", r"C:\Windows"), "system32").lower())
          and resolved.endswith("\\version.dll"), resolved or "no line")
    check("the 17 exports resolved on the system module", "the system version.dll's 17 exports are resolved" in armed_log)
    check("the armed process ran the detach path", "proxy detached" in armed_log)
    check("the armed log carries the forced publish's arm line, and no refusal",
          "publish: armed - the client's own serialiser" in armed_log
          and "publish: the client build does not match" not in armed_log)
    note("the armed control logs the publish arm line; that host has no client module, so no publish was asked for")

    # ---- 8. this process is a foreign image too -----------------------------------------------------
    print("")
    print("FOREIGN  loading the DLL here writes nothing")
    import ctypes
    log_before = read(logp) if os.path.isfile(logp) else None
    try:
        dll = ctypes.WinDLL(DLL)
        size_q = dll.GetFileVersionInfoSizeW(os.path.join(os.environ.get("SystemRoot", r"C:\Windows"),
                                                         "System32", "notepad.exe"), None)
        ok = size_q > 0
    except OSError as exc:                                  # noqa: BLE001
        ok = False
        size_q = str(exc)
    check("the DLL forwards an export in this process", ok, "size=%s" % size_q)
    check("this process is not the game, so no clienthook.log appeared in build\\",
          not os.path.isfile(os.path.join(BUILD, "clienthook.log")))
    check("and the log of the pass-through directory is untouched by this process",
          (read(logp) if os.path.isfile(logp) else None) == log_before)

    print("")
    print("%d passed, %d failed, %d notes" % (len(passes), len(failures), len(notes)))
    if failures:
        for f in failures:
            print("  FAILED: " + f)
        return 1
    print("OK - one tree, nine sources, two identical builds, the kept features armed, the forced publish back")
    print("     with its guard, its window and its kill switch, the token channel's dvar behind its file, and")
    print("     every offline driver passing.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
