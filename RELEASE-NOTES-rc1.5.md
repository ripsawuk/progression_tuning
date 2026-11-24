# Progression Tuning for Kronos client - rc1.5

## What's new

- Augment research works. Research is earned from play, and what you earn is kept across restarts. When a research
  reaches its cost the game's own research-complete card is raised, with the game's own text, the **Unlock N total
  Augments** gate on the augments page opens, and the nine-rung ladder the page draws is the merged one.
- Weapon levels go past 40. A weapon above 40 now levels up and draws its level-up card like any other, because the
  ladder is read to 60 instead of stopping at 40.
- The XP token footer is the game's own text, so it reads like the rest of the menu.
- A token press is refused while permanent double XP is on, and no token is spent by it.

## Under the hood

- The hook DLL is build 40. It pays the augment research; the mod half still only draws what the client published.
- This is the leanest build so far: dead code is gone, and so are the debug lines that only ever printed once, so a
  launch log is shorter and every line left is one that fires again.
- The false `core absent - no part diag` line at boot is gone. A boot no longer claims a part is missing when none is.
- The main part is v1.5, and the table it installs carries the level 60 and augment rows.

## Known gaps

- Armory XP above the operator level cap is untested: the profile is about 80,000 XP below it, and whether the game
  stops the feed at the cap is not known yet.
- Under Unlock Armory the padlock reads the game's own "Unlocked at Level N" text.
- Not every locked skin can be earned yet: the Zombies and Endgame task skins have no challenge row of their own, and
  49 ids in the skin lists are on no list that sets their bit, so they stay open. Flight Commander is locked where it
  should not be; left as it is.
- A locked multiplayer weapon can still be carried in a saved class: the lock is answered in the menus, and the
  match's own check is not one this build wraps.
- In create-a-class, two of the four wildcards can read unlocked at a low rank where their lock bit says locked, and
  three of the four camo requirement families above have not been seen to move on a kill yet.
- The Kronos launcher's "verify" step puts the stock `challenges.tsv` back. If weapons stop levelling, an armory item
  stops earning or cards read unlocked again, copy this package's table over it again.
- With Kronos carry-forward enabled, splash popups play no sound. Disable carry-forward to restore.

## Install

Same as rc1.4, with the hook at build 40, the augments part included and the updated table - see `INSTALL.txt` in
the zip.
