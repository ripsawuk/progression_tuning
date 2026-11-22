# Progression Tuning for Kronos client - rc1.4

## What's new

- The Armory works. Its 76 items are locked until you earn them: pick one and the operator XP you earn in a match
  is paid into it, and the item unlocks and draws the game's own unlock card when it reaches its cost. The next item
  in your queue then becomes the active one, and the pick is saved, so it is still your pick after a restart.
- Debug Options has an **Unlock Armory** row. On, it padlocks the Armory from the Career > Challenges page and opens
  every armory item - the base items, the attachment versions, the blueprints and the crafting-table streaks.
  Awarding pauses while it is on and what you have already earned is kept; off is the Armory as it works above.
- Blueprints follow one rule for every gun: with **Unlock Blueprints** on, a blueprint is unlocked unless its base gun
  is still locked; off, blueprints stay locked. Every blueprint is always listed.
- Debug Options no longer draws its stock rows twice; the page lists each row once and our own rows stay on it.
- The console is quieter. The parts no longer print the probe and watch lines they used to - the camo, challenge
  and card sweeps, the prestige-set count and the toggle read-back - so a launch log is short enough to read.
- Multiplayer. Every create-a-class item the table gives a level is locked until its rank - weapons, perks,
  equipment, scorestreaks, field upgrades and wildcards - and the 27 empty camo challenges on the multiplayer
  weapons now carry a requirement, so those camo tiers can count.
- Operator skins are locked until earned: the Zombies and Endgame task skins, the multiplayer ranked and prestige
  skins, the Warzone and Royale skins and the twelve level and prestige skins. A playdate completion pays Memento
  Mori for all eight crew characters and the Warden, whichever operator completes it, and draws its two item cards.

## Under the hood

- The hook DLL is build 39, SHA256 `E33F8E94DB32575E862703285350E499320D106514F8D38D10E32BBE83457867`, rebuilt
  byte-identical from this commit's `clienthook\` with `build.cmd`.
- The hook keeps `cod25\players\armory.txt` - your active armory item, your queue and the Unlock Armory setting. It
  is written in one piece and renamed into place, so a crash mid-write cannot leave a half file.
- The armory part builds the rows, the lock and the pick out of the client's own armory record, and the pay rides the
  client's own award, so the progress the Armory shows is the record's own number.
- The mod folder carries a second game script, `scripts\progression_tuning_armory.gsc`, which reads the operator XP a
  match earns and feeds it to the hook. Nothing of it runs in the front end.
- The table carries the four rows behind the playdate completion and the requirement the 27 multiplayer camo
  challenges were missing; the armory's own rows were already in it.
- The **Unlock Armory** row is added through the options part's registration API, so the Armory logic stays in its own
  part, and the padlock is the game's own disabled state on the Armory card, not a drawing of ours.
- The Multiplayer locks answer from the client's own lock bit for the six locked types, and leave an item with no
  level to the client.

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
  stops earning or cards read unlocked again, copy this package's table over it.
- With Kronos carry-forward enabled, splash popups play no sound. Disable carry-forward to restore.

## Install

Same as rc1.3, with the hook at build 39, the armory part, the folder's second script and the updated table - see
`INSTALL.txt` in the zip.
