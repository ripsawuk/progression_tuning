"""Read-only PE import survey for the client-hook question (which module can we stand in front of?).

Lists a PE's static and delay imports, and flags which of them (a) the launcher catalogues as a
game file, (b) are KnownDLLs the loader takes from System32 regardless, and (c) already exist in
cod25. Writes nothing.

    python clienthook\\tools\\pe_imports.py <game>\\cod25\\cod25-cod.exe [--game <game>]

The cod25 folder the survey checks against is the target PE's own folder unless --game or
KRONOS_GAME_DIR says otherwise (either the game install - the folder holding cod25\\, or cod25 itself).

Evidence only; no claim about runtime loading is made here (that needs the process's module list).
"""
import json
import os
import sys

import pefile

SYSTEM32 = os.path.join(os.environ.get("SystemRoot", r"C:\Windows"), "System32")


def option(name):
    """The value of `--<name> <value>` or `--<name>=<value>`; "" when the option is absent."""
    for i, a in enumerate(sys.argv):
        if a == name and i + 1 < len(sys.argv):
            return sys.argv[i + 1]
        if a.startswith(name + "="):
            return a.split("=", 1)[1]
    return ""


def positionals():
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


def game_dir(target):
    """The cod25 folder: --game, then KRONOS_GAME_DIR, then the target PE's own folder. Never a constant."""
    d = (option("--game") or os.environ.get("KRONOS_GAME_DIR", "")).strip().strip('"')
    if not d:
        return os.path.dirname(os.path.abspath(target))
    if os.path.isdir(os.path.join(d, "cod25")):
        d = os.path.join(d, "cod25")
    return d


def catalogued(kronos):
    """Every path the launcher manifest or its hash snapshot names, lower-cased file names only."""
    names = set()
    for p in (os.path.join(kronos, "launcher_manifest.txt"), os.path.join(kronos, "launcher_hashes.txt")):
        if not os.path.exists(p):
            continue
        with open(p, "r", encoding="utf-8", errors="replace") as fh:
            for line in fh:
                parts = line.rstrip("\n").split("\t")
                if len(parts) >= 4:
                    names.add(os.path.basename(parts[3]).lower())
    return names


def known_dlls():
    """The OS list the loader resolves from System32 before searching the app directory."""
    try:
        import winreg
    except Exception:
        return set()
    out = set()
    for hive, key in (
        (winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Control\Session Manager\KnownDLLs"),
    ):
        try:
            with winreg.OpenKey(hive, key) as k:
                i = 0
                while True:
                    try:
                        name, value, _ = winreg.EnumValue(k, i)
                    except OSError:
                        break
                    out.add(str(value).lower())
                    i += 1
        except OSError:
            pass
    return out


def survey(path):
    pe = pefile.PE(path, fast_load=True)
    pe.parse_data_directories(
        directories=[
            pefile.DIRECTORY_ENTRY["IMAGE_DIRECTORY_ENTRY_IMPORT"],
            pefile.DIRECTORY_ENTRY["IMAGE_DIRECTORY_ENTRY_DELAY_IMPORT"],
        ]
    )

    static = []
    for entry in getattr(pe, "DIRECTORY_ENTRY_IMPORT", []) or []:
        static.append(entry.dll.decode("ascii", "replace").lower())

    delay = []
    for entry in getattr(pe, "DIRECTORY_ENTRY_DELAY_IMPORT", []) or []:
        delay.append(entry.dll.decode("ascii", "replace").lower())

    return static, delay


def main():
    args = positionals()
    if not args:
        print(__doc__)
        return 2
    target = args[0]
    game = game_dir(target)
    kronos = os.path.join(game, "kronos")

    cat = catalogued(kronos)
    known = known_dlls()
    static, delay = survey(target)

    print(f"target: {target}")
    print(f"catalogued file names: {len(cat)}   KnownDLLs: {len(known)}")
    print()
    header = f"{'module':28} {'in cod25':9} {'catalogued':11} {'KnownDLL':9} where it loads from"
    print(header)
    print("-" * len(header))

    rows = []
    for mod in sorted(set(static) | set(delay)):
        local = os.path.join(game, mod)
        in_tree = os.path.exists(local)
        if mod in known:
            where = "System32 (KnownDLL - cannot proxy)"
        elif in_tree:
            where = "cod25 (app dir first!)"
        else:
            where = "System32, unless we place one in cod25 -> app dir wins"
        rows.append(
            {
                "module": mod,
                "kind": "static" if mod in static else "delay",
                "in_cod25": in_tree,
                "catalogued": mod in cat,
                "known_dll": mod in known,
                "where": where,
            }
        )
        print(
            f"{mod:28} {str(in_tree):9} {str(mod in cat):11} {str(mod in known):9} {where}"
        )

    print()
    print("SLOTS (not a KnownDLL, not catalogued) - a file of ours in cod25 would be loaded first:")
    slots = [r for r in rows if not r["known_dll"] and not r["catalogued"]]
    if not slots:
        print("  none among this module's imports")
    for r in slots:
        print(f"  {r['module']:28} {r['kind']:6} exists_in_cod25={r['in_cod25']}")

    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "imports-survey.json")
    with open(out, "w", encoding="utf-8") as fh:
        json.dump({"target": target, "static": static, "delay": delay, "rows": rows}, fh, indent=2)
    print(f"\nwrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
