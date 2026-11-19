#!/usr/bin/env python3
"""Offline proof of the native payment, as clienthook BUILD 20 ships it (build 19's suite, adapted).

    python -I clienthook\\tools\\test_nativepay.py

Read-only, except scratch directories under %TEMP%. The game is never launched and the game folder is only read
(the client file is hashed, the game exe's import table is parsed).

WHAT WAS ADAPTED from nativepay-poc\\tools\\test_nativepay.py (that folder stays build 18/19's record, and its own
suite still runs there against its own DLL):

  * the artefact paths: this build's DLL is clienthook\\build\\version.dll and its driver is
    clienthook\\build\\nativepay_test.exe, built from clienthook\\src\\nativepay.c - the SAME source the DLL uses;
  * two artefact checks: build 19's "build\\version.dll is the poc's bytes" cannot hold now that build\\ holds
    this build, so the same two slots assert that the artefact under test is not build 19's bytes and not its size;
  * the "build 17 is not in the image" section, which was the PoC's whole point: build 20 IS build 17's frame plus
    this payment, so the twenty-odd checks there now assert the union instead - build 17's lines present, build 14's
    lever write absent, and build.cmd compiling the eight sources.

Everything else - the 60 unit checks, the four sites against the client file, the real installer against the client
mapped read-only, the kill switch, the 17-name export table, the one-file proxy proof - is build 19's and is
unchanged.
"""

import hashlib
import os
import re
import shutil
import struct
import subprocess
import sys
import tempfile
from ctypes import wintypes

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # clienthook\
DLL = os.path.join(ROOT, "build", "version.dll")
DLL_SHA = DLL + ".sha256"
EXE = os.path.join(ROOT, "build", "nativepay_test.exe")
SYS_VERSION = r"C:\Windows\System32\version.dll"


def game(*parts):
    """A path under the game's cod25 folder: --game <dir> first, then KRONOS_GAME_DIR, either form (the install
    folder holding cod25\\, or cod25 itself). "" when unset - the client and the game's exe are optional here, and
    the checks that read them say so and skip."""
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
SITES = {0x93820: "the award function", 0x930D3: "the call site", 0x93E5D: "the addend load A",
         0x93E63: "the addend load B"}
POC_BUILD19_SHA = "2660920B8A165F08AAD61AF13653902EC4B32530F3461D084BBB15E578DEEA3D"
POC_SIZE = 165888

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


def sha256_of(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


# --- a minimal PE export reader (stdlib only, so the export check needs no toolchain) -------------------

def pe_sections(path):
    data = open(path, "rb").read()
    e = struct.unpack_from("<I", data, 0x3C)[0]
    nsec = struct.unpack_from("<H", data, e + 6)[0]
    opt = e + 24
    opt_size = struct.unpack_from("<H", data, e + 20)[0]
    sec = opt + opt_size
    out = []
    for i in range(nsec):
        base = sec + i * 40
        vsize, va, rawsize, raw = struct.unpack_from("<IIII", data, base + 8)
        out.append({"va": va, "vsize": vsize, "raw": raw, "rawsize": rawsize,
                    "name": data[base:base + 8].rstrip(b"\0").decode("latin-1")})
    exp_rva, exp_size = struct.unpack_from("<II", data, opt + 112 + 0 * 8)
    return data, out, exp_rva, exp_size


def rva_to_off(sections, rva):
    for s in sections:
        if s["va"] <= rva < s["va"] + max(s["vsize"], s["rawsize"]):
            return s["raw"] + (rva - s["va"])
    raise ValueError("rva 0x%X is in no section" % rva)


def exports(path):
    data, sections, exp_rva, exp_size = pe_sections(path)
    if exp_rva == 0:
        return 0, []
    off = rva_to_off(sections, exp_rva)
    base_ord = struct.unpack_from("<I", data, off + 16)[0]
    n_names = struct.unpack_from("<I", data, off + 24)[0]
    names_rva = struct.unpack_from("<I", data, off + 32)[0]
    ords_rva = struct.unpack_from("<I", data, off + 36)[0]
    names_off = rva_to_off(sections, names_rva)
    ords_off = rva_to_off(sections, ords_rva)
    out = []
    for i in range(n_names):
        name_rva = struct.unpack_from("<I", data, names_off + i * 4)[0]
        noff = rva_to_off(sections, name_rva)
        end = data.index(b"\0", noff)
        ordinal = struct.unpack_from("<H", data, ords_off + i * 2)[0] + base_ord
        out.append((data[noff:end].decode("latin-1"), ordinal))
    return len(out), sorted(out)


def imports_of(path, module_name):
    """The names this image imports from one module (stdlib PE reader again, so no toolchain)."""
    data, sections, _er, _es = pe_sections(path)
    e = struct.unpack_from("<I", data, 0x3C)[0]
    imp_rva = struct.unpack_from("<I", data, e + 24 + 120)[0]
    if imp_rva == 0:
        return []
    off = rva_to_off(sections, imp_rva)
    while True:
        ent = data[off:off + 20]
        if len(ent) < 20 or ent == b"\0" * 20:
            return []
        name_rva, ilt = struct.unpack_from("<II", ent, 12)[0], struct.unpack_from("<I", ent, 0)[0]
        noff = rva_to_off(sections, name_rva)
        name = data[noff:data.index(b"\0", noff)].decode("latin-1")
        if name.lower() == module_name.lower():
            out = []
            t = rva_to_off(sections, ilt) if ilt else 0
            while t:
                thunk = struct.unpack_from("<Q", data, t)[0]
                if thunk == 0:
                    break
                if thunk >> 63:
                    out.append("#%d" % (thunk & 0xFFFF))
                else:
                    nn = rva_to_off(sections, thunk & 0x7FFFFFFF)
                    out.append(data[nn + 2:data.index(b"\0", nn + 2)].decode("latin-1"))
                t += 8
            return out
        off += 20


def passthrough(dll_path):
    """test_proxy.py's check, on this build: both DLLs answer notepad.exe's version resource the same.
    Also asserts the two are different modules - this process has notepad's System32 version.dll loaded."""
    import ctypes
    sysroot = os.environ.get("SystemRoot", r"C:\Windows")
    sysdll = os.path.join(sysroot, "System32", "version.dll")
    target = os.path.join(sysroot, "System32", "notepad.exe")

    def ask(dll):
        size = dll.GetFileVersionInfoSizeW(target, None)
        info = q = False
        qlen = 0
        fixed = b""
        if size:
            buf = ctypes.create_string_buffer(size)
            info = bool(dll.GetFileVersionInfoW(target, 0, size, buf))
            ptr = ctypes.c_void_p()
            ln = wintypes.UINT()
            q = bool(dll.VerQueryValueW(buf, "\\", ctypes.byref(ptr), ctypes.byref(ln)))
            qlen = ln.value
            if q and ptr.value:
                fixed = ctypes.string_at(ptr, min(qlen, 16))
        lang = ctypes.create_unicode_buffer(128)
        lrc = dll.VerLanguageNameW(0x0409, lang, 128)
        return (size, info, q, qlen, fixed, lrc, lang.value)

    try:
        system = ctypes.WinDLL(sysdll)
        proxy = ctypes.WinDLL(dll_path)
    except OSError as exc:                                  # noqa: BLE001
        return False, str(exc)
    a, b = ask(system), ask(proxy)
    detail = "size %d, fixed %s, %r, distinct=%s" % (a[0], a[4][:8].hex(), a[6], proxy._handle != system._handle)
    return (a == b and a[0] != 0 and proxy._handle != system._handle), detail


def run_armed_host(scratch_dir, dll_path):
    """Run the pass-through host with the GAME's image name (build 21's arm signal), then ExitProcess.

    Build 21 arms only when the process image is cod25-cod.exe, so the armed path's log lines can no
    longer be read from this (python.exe) process. The host is copied into the directory that already
    holds the DLL copy and renamed `cod25-cod.exe`; the DLL takes its own directory from its own path, so
    the log lands beside the DLL, which is where `logp` points. ExitProcess, not FreeLibrary: the loader
    terminates the threads the armed path starts, so this proves the LOG without asking the unload
    question (that question is test_build21.py's `pass` mode, one directory over)."""
    host = os.path.join(ROOT, "build", "ch_passthru_host.exe")
    if not os.path.isfile(host):
        return (None, "build\\ch_passthru_host.exe is absent - run tools\\build_tests.cmd")
    copy = os.path.join(scratch_dir, "cod25-cod.exe")
    shutil.copyfile(host, copy)
    r = subprocess.run([copy, "armed", dll_path], capture_output=True, text=True, timeout=300)
    return (r.returncode, (r.stdout or "") + (r.stderr or ""))


def main():
    print("clienthook build 20 - the native payment, build 19's suite adapted - " + ROOT)
    print("")
    if not CLIENT:
        print("NOTE  KRONOS_GAME_DIR is not set and no --game was given - the client and the game's exe cannot be "
              "read, so the guard, sites and install checks are skipped")
    check("build\\version.dll exists (clienthook\\build.cmd)", os.path.isfile(DLL))
    check("build\\nativepay_test.exe exists (tools\\build_tests.cmd)", os.path.isfile(EXE))
    if failures:
        print("")
        print("STOP: run clienthook\\build.cmd and clienthook\\tools\\build_tests.cmd first.")
        return 1

    # ---- 1. the artefacts --------------------------------------------------------------------------
    print("")
    print("ARTEFACTS")
    raw = open(DLL, "rb").read()
    h = hashlib.sha256(raw).hexdigest()
    print("version.dll %d B / %s" % (len(raw), h.upper()))
    recorded = open(DLL_SHA, "r", encoding="ascii", errors="replace").read().strip()
    check("build\\version.dll.sha256 records this DLL's hash", h in recorded, recorded.split()[0][:16] + "...")
    # build 19's two "the installer's copy is the same bytes" slots. The PoC folder those read is not part of this
    # tree, so the same two slots assert that the artefact under test is not build 19's PoC bytes at all.
    check("the artefact is not build 19's PoC bytes", h.upper() != POC_BUILD19_SHA, "0x%s" % h.upper()[:8])
    check("the artefact is not build 19's PoC size", len(raw) != POC_SIZE, "%d B" % len(raw))

    # ---- 2. the export table: what cod25-cod.exe imports -------------------------------------------
    print("")
    print("EXPORTS  (ours vs %s)" % SYS_VERSION)
    n_ours, ours = exports(DLL)
    check("our DLL exports 17 names", n_ours == 17, "%d" % n_ours)
    if os.path.isfile(SYS_VERSION):
        n_sys, sys_exports = exports(SYS_VERSION)
        print("  system: %d named exports, ordinals %d..%d" % (n_sys, sys_exports[0][1], sys_exports[-1][1]))
        names_ours = [n for n, _ in ours]
        names_sys = [n for n, _ in sys_exports]
        for n in names_sys:
            check("the system export %s is answered" % n, n in names_ours)
        check("no export of ours is absent from the system DLL", set(names_ours) == set(names_sys),
              ", ".join(sorted(set(names_ours) ^ set(names_sys))) or "identical")
        ords_ours = dict(ours)
        check("each name keeps the system DLL's ordinal",
              all(ords_ours.get(n) == dict(sys_exports).get(n) for n in names_sys),
              "1..17" if all(ords_ours.get(n) == dict(sys_exports).get(n) for n in names_sys) else "differs")
    else:
        note("the system version.dll is not where this script expects it - the comparison was skipped")

    # ---- 3. ONE file - the proxy loads the SYSTEM version.dll by full path --------------------------
    print("")
    print("PROXY  nativepay_test.exe proxy + a pass-through in this process")
    check("the folder the DLL is built in holds no version_orig.dll (build 20 needs no side-by-side copy)",
          not os.path.exists(os.path.join(ROOT, "build", "version_orig.dll")))
    scratch_dir = os.path.join(tempfile.gettempdir(), "build20-proxy")
    shutil.rmtree(scratch_dir, ignore_errors=True)
    os.makedirs(scratch_dir)
    scratch_dll = os.path.join(scratch_dir, "version.dll")
    try:
        shutil.copyfile(DLL, scratch_dll)
        check("the copy under test has no version_orig.dll beside it",
              not os.path.exists(os.path.join(scratch_dir, "version_orig.dll")))
        r = subprocess.run([EXE, "proxy", scratch_dll], capture_output=True, text=True, timeout=300)
        outp = r.stdout or ""
        for line in outp.split("\n"):
            if line.startswith(("ours ", "system ", "pre-loaded", "     log", "     note")):
                print("  | " + line)
        check("proxy: exits 0", r.returncode == 0, "rc=%d" % r.returncode)
        m = re.search(r"nativepay: OK - (\d+) checks", outp)
        check("proxy: the driver passes every one of its checks", m is not None,
              ("%s checks" % m.group(1)) if m else (outp.strip().split("\n")[-1] if outp else "no output"))
        for want in ("proxy: the full path did NOT hand back this DLL (distinct module handles)",
                     "proxy: the resolved module's path is under the Windows system directory",
                     "proxy: and it is not this DLL's path",
                     "proxy: the module under test carries this build's banner in its own image",
                     "proxy: the system module does not carry it",
                     "proxy: all 17 version.dll exports resolve on the DLL under test",
                     "proxy: and all 17 resolve on the system DLL",
                     "proxy: GetFileVersionInfoSizeW + GetFileVersionInfoW answer identically",
                     "proxy: VerQueryValueW answers identically",
                     "proxy: the three A exports answer identically",
                     "proxy: the four Ex exports answer identically",
                     "proxy: VerFindFileW answers identically",
                     "proxy: VerFindFileA answers identically",
                     "proxy: VerLanguageNameW answers identically",
                     "proxy: VerLanguageNameA answers identically"):
            check("proxy: %r" % want, ("pass  " + want) in outp)

        # the same pass-through test_proxy.py ran for build 17, in THIS process, plus the DLL's own log line
        passthrough_ok, detail = passthrough(scratch_dll)
        check("pass-through in this process: the proxy answers like the system DLL", passthrough_ok, detail)
        logp = os.path.join(scratch_dir, "clienthook.log")
        # BUILD 21: python.exe is not the game, so this process must leave no log behind at all. The armed
        # path's own lines are read from the host whose image name IS cod25-cod.exe (tools\passthru_host.c,
        # mode `armed`, the same DLL copy in the same directory) - test_build21.py owns that proof.
        check("this process is not the game, so the proxy wrote no clienthook.log here",
              not os.path.isfile(logp))
        armed_rc, armed_out = run_armed_host(scratch_dir, scratch_dll)
        check("the armed host (image cod25-cod.exe) exits 0", armed_rc == 0,
              "rc=%s %s" % (armed_rc, (armed_out or "").strip().split("\n")[-1] if armed_out else ""))
        check("the proxy wrote its own clienthook.log beside itself", os.path.isfile(logp))
        log = open(logp, "r", encoding="ascii", errors="replace").read() if os.path.isfile(logp) else ""
        resolved = ""
        for line in log.split("\n"):
            if "init: version.dll resolved from " in line:
                resolved = line.split("init: version.dll resolved from ", 1)[1].strip().lower()
        check("the proxy's log says which module it loaded", resolved != "", resolved or "no line")
        check("and it is the system one, not itself",
              resolved.startswith(os.path.join(os.environ.get("SystemRoot", r"C:\Windows"),
                                               "system32") .lower()) and resolved.endswith("\\version.dll"),
              resolved)
        check("the proxy did not refuse to forward", "init: refused" not in log)
        check("there is still no version_orig.dll beside it afterwards",
              not os.path.exists(os.path.join(scratch_dir, "version_orig.dll")))

        # who actually imports these 17 names: only 6, and none of the three this harness cannot call
        exe = game("cod25-cod.exe")
        if os.path.isfile(exe):
            got = imports_of(exe, "version.dll")
            want = ["GetFileVersionInfoA", "GetFileVersionInfoSizeA", "GetFileVersionInfoSizeW",
                    "GetFileVersionInfoW", "VerQueryValueA", "VerQueryValueW"]
            check("cod25-cod.exe imports exactly 6 of the 17 version.dll names", sorted(got) == sorted(want),
                  ", ".join(sorted(got)))
            check("and none of VerInstallFileA/W or GetFileVersionInfoByHandle",
                  not any(n in got for n in ("VerInstallFileA", "VerInstallFileW",
                                             "GetFileVersionInfoByHandle")))
        else:
            note("the game exe is not on disk - the import check was skipped")
    finally:
        shutil.rmtree(scratch_dir, ignore_errors=True)

    # ---- 3b. the unit driver ------------------------------------------------------------------------
    print("")
    print("UNIT  nativepay_test.exe self  (src\\nativepay.c - the file the DLL is built from)")
    if not os.path.isfile(CLIENT):
        # the driver's guard checks read the client file, and its location is a setting
        note("nativepay_test.exe self needs the client file for its guard checks - set KRONOS_GAME_DIR (or pass "
             "--game <dir>) to the game install, and the unit section runs; skipped here")
    else:
        # the setting may have come from --game, which a child process does not inherit, so the path is passed too
        proc = subprocess.run([EXE, "self", CLIENT], capture_output=True, text=True, timeout=300)
        out = proc.stdout or ""
        m = re.search(r"nativepay: OK - (\d+) checks", out)
        check("the unit driver passes", proc.returncode == 0 and m is not None,
              ("%s checks" % m.group(1)) if m else (out or proc.stderr).strip().split("\n")[-1])
        for want in ("decode: field 45's value is at byte 0x70 + 8i (8-byte entries)",
                     "window: the client's function is called with kill = field 45",
                     "window: __finally restored the pair after the fault",
                     "wrapper: 420 events -> 3 lines + every 20th after that (24)",
                     "boundary: an ev=109 event calls the reset hook exactly once",
                     "boundary: the client's function is handed the SAME record, unchanged",
                     "boundary: with no hook set the event passes through untouched",
                     "boundary: an ev=95 event never calls the reset hook",
                     "sha256: the 'abc' known vector",
                     "guard: a changed byte in the call site 0x930D3 is refused",
                     "guard: another SizeOfImage is refused"):
            check("the unit driver covers: %s" % want, ("pass  " + want) in out)

    # ---- 4. the recorded signature against the file on disk ----------------------------------------
    print("")
    print("SITES  nativepay_test.exe sites <client>")
    if os.path.isfile(CLIENT):
        raw_client = open(CLIENT, "rb").read()
        check("the client under test is the one the constants were measured from",
              len(raw_client) == CLIENT_SIZE and hashlib.sha256(raw_client).hexdigest() == CLIENT_SHA,
              "%d B / %s..." % (len(raw_client), hashlib.sha256(raw_client).hexdigest()[:8].upper()))
        r = subprocess.run([EXE, "sites", CLIENT], capture_output=True, text=True, timeout=300)
        outp = r.stdout or ""
        print("  | " + "\n  | ".join(l for l in outp.split("\n") if l.startswith(("pass", "FAIL", "      ", "size",
                                                                                  "sha256", "recorded", "file"))))
        check("sites: exits 0", r.returncode == 0, "rc=%d" % r.returncode)
        for rva in sorted(SITES):
            check("sites: the %s at 0x%X matches the recorded bytes" % (SITES[rva], rva), "0x%05X  " % rva in outp)
        check("sites: the call at 0x930D3 resolves to 0x93820", "resolves to 0x93820" in outp)
        check("sites: the loads read rva 0x2775F4 and 0x2775F8",
              "reads rva 0x2775F4" in outp and "reads rva 0x2775F8" in outp)
        check("sites: verdict is OK", "nativepay: OK" in outp)

        # ---- 5. the real installer, against the client mapped read-only as an image -----------------
        print("")
        print("INSTALL  nativepay_test.exe install <client>")
        before = sha256_of(CLIENT)
        r = subprocess.run([EXE, "install", CLIENT], capture_output=True, text=True, timeout=300)
        outp = r.stdout or ""
        print("  | " + "\n  | ".join(l for l in outp.split("\n")
                                      if l.startswith(("LOG   ", "INFO  ", "FAIL", "pass  install"))))
        check("install: exits 0", r.returncode == 0, "rc=%d" % r.returncode)
        check("install: the install returns 1", "nativepay_install -> 1" in outp)
        check("install: the site now calls nativepay_call (or its trampoline)",
              "nativepay_call" in outp and "NOT OUR HOOK" not in outp)
        check("install: the award's 24 bytes are byte-identical afterwards",
              "pass  install: the award's first 24 bytes are byte-identical" in outp)
        check("install: the two ints are not written at install time",
              "pass  install: the two ints are not written at install time" in outp)
        check("install: the hook line prints the 5 bytes before and after", "E8 48 07 00 00 -> E8" in outp)
        check("install: verdict is OK", "nativepay: OK" in outp)
        check("install: the client file on disk is unchanged (the view was private and read-only)",
              sha256_of(CLIENT) == before == CLIENT_SHA)
    else:
        note("the client is not on disk - the sites and install modes were skipped")

    # ---- 6. the kill switch ------------------------------------------------------------------------
    print("")
    print("KILL SWITCH  nativepay_test.exe off <dir>")
    scratch = os.path.join(tempfile.gettempdir(), "build20-offtest")
    offdir = os.path.join(scratch, "progression-tuning")
    os.makedirs(offdir, exist_ok=True)
    killfile = os.path.join(offdir, "nativepay_off.txt")
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

    # ---- 7. ONE IMAGE: the payment AND the frame that publishes it, and the dropped features absent ------
    print("")
    print("IMAGE  one build: the payment, the payload and the published XP in the same file")
    text = raw.decode("latin-1")
    for marker in ("nativepay: hook installed", "nativepay: ev=95 pays", "nativepay: disabled by file",
                   "nativepay: refused - %s", "nativepay_off.txt"):
        check("version.dll carries %r" % marker, marker in text)
    # the frame's own evidence must be in this image too - the payment is only half of it
    for present in ("master: %d call sites hooked", "g11: armed",
                    "ptsplash_paid", "pubxp: armed", "publish: challenge state re-published live (#%ld)"):
        check("version.dll carries %r" % present, present in text)
    # and what v1.0 dropped is gone from the image, not merely disabled (the forced publish came back in build 24)
    for absent in ("ladder: challenges.tsv served", "g10_armory_cfg",
                   "tier: table loaded", "pay: ledger", "dat write via=", "io: observer armed", "award: armed",
                   "nativepay: sums", "ae window"):
        check("version.dll does NOT carry %r" % absent, absent not in text)
    build = open(os.path.join(ROOT, "build.cmd"), "r", encoding="utf-8", errors="replace").read()
    cl_text = "\n".join(l for l in build.replace("^", " ").split("\n") if l.strip().startswith("cl "))
    sources = set(re.findall(r"([a-z0-9_]+\.c)", cl_text))
    check("build.cmd's link line builds the nine sources",
          sources == {"proxy_main.c", "frame.c", "resolve.c", "publish.c", "g11.c", "tokens.c", "master.c",
                      "nativepay.c", "pubxp.c"},
          ", ".join(sorted(sources)))
    check("build.cmd compiles src\\nativepay.c (this driver's own source)", "nativepay.c" in sources)
    proxy = open(os.path.join(ROOT, "src", "proxy_main.c"), "r", encoding="utf-8", errors="replace").read()
    check("proxy_main.c starts nativepay at attach", "nativepay_start();" in proxy)
    check("proxy_main.c starts the frame at attach (the publish hook and the install gate come from it)",
          "void ch_frame_start(void);" in proxy and "ch_frame_start();" in proxy)

    print("")
    print("%d passed, %d failed, %d notes" % (len(passes), len(failures), len(notes)))
    if failures:
        for f in failures:
            print("  FAILED: " + f)
        return 1
    print("OK - one file: the system version.dll resolved by full path, the 5 bytes at 0x930D3 paying the game's "
          "own field 45, the pair restored on every path, the installer touching nothing else, and build 17's frame "
          "in the same image with build 14's lever write gone.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
