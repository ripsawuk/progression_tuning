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

**It extends a prestige-2 weapon past its last rung.** The client's level function is taken at its own call sites;
for a weapon at prestige 2 whose XP is past its last threshold, the level continues one step per 1,800 XP, up to
250.

**It keeps the token channel's dvar alive.** The token menu's countdown lives in one dvar, `pt_tokens_ch`, but
nothing of the mod runs before a level start, so a token activated in the front end would have nowhere to be
written. The hook registers that dvar at boot from `cod25\players\tokens.txt` and saves it back to that file
whenever it changes - one ASCII line, written through a temporary file and a rename. The `players` folder is the
client's own: the hook reads it and never makes it.

**It reads the armory XP feed.** The level thread of the mod's own GSC publishes the operator's pre-cap rank XP for
the match as `pt_armory_xp` - `s=<match serial>;x=<xp this match>;h=<beat>`. The hook registers that dvar at boot,
reads it on its 250 ms thread, resets when the serial moves or when the beat goes back (a level load leaves `s` at 1),
and writes one `armory: feed` line when the total moves, at most once a second. `armory: live=0` marks the level
thread's end. The kill switch is `%TEMP%\progression-tuning\armory_feed_off.txt`.

**It pays that XP into the active armory row.** What the match earned and this process has not paid is held in the
client's own award amount - `0x2775F4`, the same int the field-45 payment uses - and the client's own award function
is called once with it, naming the row by the pick's private trigger out of the record's own trigger list. The credit
is the row's rise read back from `row+0x560`, never the amount held, and every line the pay writes is posted to the
250 ms thread so nothing opens a file on the client's drain thread. One look a second, only while the feed's beat is
inside its two-second window, only for the active pick, and only while that row is not complete. A completion is
logged, and it posts one advance request for that row: the pick's own 250 ms tick then moves `a=` to the next row in
the queue whose own status is not complete, writes `players\armory.txt`, pushes the merged line into
`pt_armory_ch`, and says `armory: advance <from> -> <to>` - or, with nothing left to earn, `a=0` and
`armory: queue done`. The pay itself still opens no file. A fault in that one call restores both globals and latches
the pay off for the process. The kill switch is `%TEMP%\progression-tuning\armory_pay_off.txt`; the advance has its
own, `%TEMP%\progression-tuning\armory_advance_off.txt`, which leaves the pay running and the pick where it is.

**It pauses while Unlock Armory is on.** The pick line carries a third field, `u=<0|1>` - the Debug Options row the
mod writes when it is flipped. While `u=1` the pay pays nothing and posts no advance; the first look after the flag
clears pays again. The hook says `armory: pay paused (unlock armory on)` and `armory: pay resumed` once each.

**It keeps the armory pick alive.** The Armory's pick has the same problem: the press happens in the front end and
the row has to outlive the process. The hook registers `pt_armory_ch` at boot from `cod25\players\armory.txt` -
`a=<row>`, the advance queue `q=<row,row,...>` and the Unlock Armory flag `u=<0|1>`, in that order - adopts every
press the mod writes to that dvar, keeps the file in step, and moves the pick on when the row it names is paid to
completion. That file is the only one it reads: with `armory.txt` absent the channel starts from `a=0`. Every line
the hook writes is said as `pick: saved <line>`, once per distinct line, so each adopted change leaves a log line of
its own.

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
    src\frame.c             the identification pass, the lock payload, the forced publish
    src\resolve.c           every client address, found at run time; the per-feature gate; one summary line
    src\publish.c           the forced publish's pure half: the page check, the guard, the window, the kill switch
    src\g11.c               the lock payload's pure half: hex, split, header, name hash, canary
    src\tokens.c            the token channel's dvar and its file: the one-line form, the tmp-and-rename write
    src\pick.c              the armory pick channel's dvar and its file, the queue and the advance
    src\armory.c            the armory xp feed, and the pay that rides the client's own award
    src\master.c            the master-prestige level byte, at its call sites
    src\nativepay.c         the five bytes at the award's call site, and the seams the frame hangs on them
    src\pubxp.c             the paid-XP text, the per-gun ledger and the record lookup
    src\version_proxy.def   the 17 export names
