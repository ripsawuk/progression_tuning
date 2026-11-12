 # Progression Tuning for Kronos client - rc1.0

Offline weapon progression for Call of Duty: Black Ops 7 Zombies on the Kronos client. Weapons earn XP in matches
from the game's own award, level up, unlock their attachments and move their camo challenges on, and every milestone
is announced by a popup. The release has two halves: the mod folder that draws the popups, and a small
`cod25\version.dll` that lets the game pay the XP itself

## Restored and working

- Weapon XP earned in matches, using the game's own amounts, with adjusted per level XP
- Weapon level-ups with the game's level-up banner
- Attachment unlocks announced as weapons level up
- Camo challenges progress, with a popup for each tier
- Daily challenge completion popups, with an XP reward panel
- Weekly challenge completion popups, daily-style, with XP reward panel
- Popups queue one at a time instead of overlapping
- Prestige attachments and prestige camos stay locked until earned
- Challenge trackers show one entry per challenge
- BO6 carry-forward weapons and operators work alongside the included DLL

## Known issues

- Popups are silent with Kronos carry-forward turned on
- Weekly popup title uses fixed English text, not the game's

## Still to do

- Reticle challenge locks
- Correct "permanently unlocked by prestige" label on unlocked items
- Correct XP reward amount on weekly challenges
- Lock list limited to this mod's weapons for future content
- Weapon XP and levels on BO6 carry-forward weapons
- ??

## Install

Unzip the release over the folder that holds `cod25\`. The zip keeps that layout:

    cod25\kronos\mods\progression_tuning\    the mod
    cod25\version.dll                        the DLL
    cod25\kronos\challenges.tsv              the weapon level ladder

The zip overwrites `cod25\kronos\challenges.tsv`, so copy that file to `challenges.tsv.bak` before you unzip.

Launch through the Kronos launcher and enable the mod in the mod list. The zip also carries `INSTALL.txt` and
`SHA256SUMS.txt` if you want to check the files.

## Rollback

Delete `cod25\version.dll` and `cod25\kronos\mods\progression_tuning\`, or just disable the mod in Kronos. Put your
`challenges.tsv.bak` back as `cod25\kronos\challenges.tsv`. The DLL also writes `cod25\clienthook.log`, which you
can delete. Progress you earned stays in the client's own save.

A Kronos client update may replace `challenges.tsv`. If weapons stop levelling, copy the release's copy over it
again.

## Disclaimer

Personal-use, community work. Not affiliated with, endorsed by or supported by Activision, Treyarch, or the Kronos
client's authors. Offline only, and used at your own risk.
