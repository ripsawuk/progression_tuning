# The client hook - `clienthook`

A small DLL that sits in the game process as `cod25\version.dll`. It exists for the two things a mod folder
cannot reach: the weapon-XP the client itself commits to the profile, and the lock state a menu reads. Everything
else in this repository is Lua.

## What it does

**It pays XP with the game's own award.** The hook does not keep an XP store of its own. It takes the client's
own per-kill weapon-XP event and lets the client's award run, so the total in the profile is the client's total,
written by the client's own code, and the ladder the game derives a weapon level from is the game's own ladder.

**It publishes the client's lock state so a mod can read it.** The hook reads the client's own locked/unlocked
answer for the items in scope and publishes it as a small set of dvars (`zm_g11_arm`, `zm_g11_ver`, `zm_g11_0`
through `zm_g11_32`). The mod reads those and asks the client's own item type before it closes a door.

**It re-publishes challenge state live.** The client normally serialises its challenge and camo state at a mode
boundary. The hook asks for the same serialisation during a match, so a card drawn from a live crossing has real
data behind it instead of a stale snapshot.

**It keeps the master-prestige level honest.** The client's level function is taken at its own call sites so the
level on screen is the one the record holds.

**It fixes the BO6-operators name clash.** With the older BO6 operators add-on in the folder the client decides an
old plugin is loaded and leaves BO6 operators off. The hook neutralises that one decision at load, and logs the
byte it changed and reads it back. One byte, and the decision is the client's own, not ours.

The payload, the guard and the kill switches keep the hook out of every other process: `DllMain` asks the process
image's file name first, and anything that is not `cod25-cod.exe` gets the exports and nothing else - no hook, no
thread, no log line, no file.

## Build

Needs the Visual Studio C++ x64 tools. The toolchain is discovered, not assumed: `cl` from a developer prompt
first, then `vswhere`, then `VCINSTALLDIR`.

    clienthook\build.cmd                  -> build\version.dll and build\version.dll.sha256

`/W3` and zero warnings is a requirement, and `/Brepro` makes a rebuild from the same source reproduce the same
bytes.

## Install

The game must be closed. The folder is the install that holds `cod25\`, or `cod25` itself.

    clienthook\install.cmd --game "<the Call of Duty folder>"
    clienthook\install.cmd          (or with KRONOS_GAME_DIR set)
    clienthook\rollback.cmd --game "<the Call of Duty folder>"

Install writes `cod25\version.dll`; the proxy writes `cod25\clienthook.log` itself, one line per attach. Rollback
deletes the DLL and the folder is back to the shipped client. The release package carries the same DLL as
`cod25\version.dll`, so a user of the release does not need this folder at all.

## Tests

Every driver compiles the shipped unit it tests - the same `.c` files the DLL is built from.

    clienthook\tools\build_tests.cmd              -> the drivers in build\
    python -I clienthook\tools\test_proxy.py      -> pass-through: OK - identical
    python -I clienthook\tools\test_build24.py    -> the tree, two identical builds, the offline drivers

See `tools\README.md` for the rest. The harnesses are read-only: nothing is installed, nothing is launched, and
no file under the game folder is written. With no game folder configured they either run on what the build holds
or skip with a `SKIP` line.

## The files

    src\proxy_main.c        the 17 exports, the system-DLL resolve, the host guard, DllMain, the log
    src\frame.c             the identification pass, the event reader, the lock payload, the forced publish
    src\resolve.c           every client address, found at run time; the per-feature gate; one summary line
    src\publish.c           the forced publish's pure half: the page check, the guard, the window, the kill switch
    src\g11.c               the lock payload's pure half: hex, split, header, name hash, canary
    src\aexp.c              the client's event-log line parser
    src\master.c            the master-prestige level byte, at its call sites
    src\nativepay.c         the five bytes at the award's call site
    src\pubxp.c             the paid-XP text, the per-gun ledger and the record lookup
    src\version_proxy.def   the 17 export names
