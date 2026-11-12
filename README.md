# Progression Tuning for Kronos client

Weapon levelling for Call of Duty: Black Ops 7 Zombies, on the Kronos client. The weapon XP the game
pays is the client's own: the hook takes the client's per-kill award and lets the client run it, so the total in
the profile - and the weapon level the game derives from it - is the game's own number, not a second progression
system bolted alongside. The mod half draws what the client already published: the level-up banner at the client's
own rung, the attachment and unlock cards, camo tiers, daily and weekly completions, and the lock state a Gunsmith
door reads.

Two pieces, and you generally want both:

| piece | what it is |
|---|---|
| the mod | `progression_tuning` - UI Lua in the Kronos mods folder. Displays; it pays nothing by itself |
| the hook | `cod25\version.dll` - the native half. It pays the XP and publishes the lock state the mod reads |

Without the hook the mod still arms and draws what the client itself published; without the mod the hook pays XP
and nothing on screen says so.

## Requirements

- Call of Duty: Black Ops 7 (2025), Zombies mode, on the **Kronos** client.
- **Offline.** Nothing here contacts a service, and nothing here is for online play.
- The release package, or a Visual Studio C++ x64 toolchain if you build from source.
- Windows x64. Nothing is installed system-wide: one DLL goes in the game folder and one folder goes in the
  Kronos mods folder.

## Install from the release package

1. Copy `cod25\kronos\mods\progression_tuning\` into `<your BO7 folder>\cod25\kronos\mods\`.
2. Copy `cod25\version.dll` into `<your BO7 folder>\cod25\`.
3. Back up `<your BO7 folder>\cod25\kronos\challenges.tsv` (copy it to `challenges.tsv.bak`), then copy
   `cod25\kronos\challenges.tsv` over it. That file is the weapon level ladder: see `data\README.md`.
4. Check the two notes in `INSTALL.txt`, or check the hashes yourself against `SHA256SUMS.txt`.
5. Launch the game through the Kronos launcher. The mod prints one `part ... armed` line per part, and the hook
   writes `cod25\clienthook.log` with one line per attach.

Enable the mod in the Kronos mod list if it is not enabled. The toggles are in `mod.json`: `pt_on`, `pt_level`,
`pt_attach`, `pt_camo`, `pt_daily`, `pt_log`.

## Rollback

Delete `cod25\version.dll` and `cod25\kronos\mods\progression_tuning\`, or just disable the mod in Kronos. Put the
backed-up `challenges.tsv.bak` back as `cod25\kronos\challenges.tsv` to return to the stock table. The DLL also
writes `cod25\clienthook.log`, which you can delete. Progress you earned stays in the client's own save.

A Kronos client update may replace `challenges.tsv`. If weapons stop levelling, copy the release's
`cod25\kronos\challenges.tsv` over it again.

## Building from source

The game folder is a setting, never a hard-coded path. Every script and harness reads `--game <dir>` first, then
`KRONOS_GAME_DIR`. Either form works: the install that holds `cod25\`, or `cod25` itself.

    set KRONOS_GAME_DIR=<your BO7 folder>

Build the hook (the toolchain is discovered, not assumed - `cl`, then `vswhere`, then `VCINSTALLDIR`):

    clienthook\build.cmd                          -> build\version.dll + build\version.dll.sha256

Build the hook's test drivers, then install:

    clienthook\tools\build_tests.cmd              -> build\*_test.exe
    clienthook\install.cmd --game "<dir>"         (the game must be closed)

The mod needs no build: `mod\progression_tuning\` is the folder you install.

## Tests

The mod's replay needs only Python 3 and the mod folder next to it:

    python -I tests\test_progression_tuning.py    -> N passed, 0 failed

It checks the Lua and the manifest statically, then (when `lupa` is installed) replays the whole mod in a Lua 5.1
runtime three times, in three different part-load orders.

The hook's offline proof is in `clienthook\tools\`, and each driver compiles the same unit the DLL is built from:

    python -I clienthook\tools\test_proxy.py      -> pass-through: OK - identical
    python -I clienthook\tools\test_build24.py    -> the tree, two identical builds, every driver
    python -I clienthook\tools\test_nativepay.py
    python -I clienthook\tools\test_g11.py
    python -I clienthook\tools\test_master.py
    python -I clienthook\tools\test_detour.py
    python -I clienthook\tools\test_aexp.py       -> skips without an event log / KRONOS_GAME_DIR
    python -I clienthook\tools\test_resolve.py    -> skips without KRONOS_GAME_DIR

Nothing in the tests installs, launches or writes anything in the game folder; with no game folder set they run
on what the build holds, or skip with a `SKIP` line.

## Layout

    mod\progression_tuning\      the mod: mod.json and eight Lua parts, the diag part included as source
    data\challenges.tsv          the weapon level ladder the release installs (see data\README.md)
    clienthook\src\              the hook: nine sources, seven headers, the export definition
    clienthook\build.cmd         build the DLL
    clienthook\install.cmd       install it, and rollback.cmd / rollback_watch.cmd to undo it
    clienthook\tools\            the offline proof, and the read-only PE readers
    tests\                       the mod's replay
    RELEASE-NOTES-rc1.0.md       what is proven, what is not, and what is not done

Two things are deliberately **not** in this repository: any copy of a game file or a table derived from one, and
any client binary other than the release's own DLL. The one exception is `data\challenges.tsv` - the weapon level
ladder, which the release installs over `cod25\kronos\challenges.tsv` (`data\README.md`). The `.dat` files and the
rest of the data a release would need are generated locally, on your own game folder.

## License

GPL-3.0. See `LICENSE`.

## Disclaimer

Personal-use, community work. Not affiliated with, endorsed by or supported by Activision, Treyarch, or the Kronos
client's authors. It works by patching a few bytes in the game process and hanging one DLL in it; use it at your own
risk, offline only.
