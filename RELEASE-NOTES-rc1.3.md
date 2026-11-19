# Progression Tuning for Kronos client - rc1.3

## What's new

- XP tokens work. Activating one spends it from your own count, plays the game's own success sound and toast, and
  starts its countdown.
- The countdown draws in the token menu and in the lobby, and it runs on in-game time: it falls while you play, holds
  while the game is paused, and holds in the menus.
- While a token is running the game pays double XP for that token's kind, operator or weapon, through its own
  multipliers - a kill that paid 20 pays 40.
- Debug Options has two rows of its own. **XP Token Amount** sets how many of every level and weapon token you own at
  once, from none to 99, and leaves battle pass tokens alone. **Enable Double XP** holds double XP on for as long as it
  is on, without spending a token; switch it off to go back to your own.
- **Unlock Attachments** opens attachments only. Before, flipping it opened every lock in the game - guns, cards,
  camos, everything.
- **Unlock Weapons** opens the Armory's guns, which it did not do before.
- Prestige attachments open with Unlock Attachments. They no longer wait for that weapon's prestige level.
- Weekly Challenges opens from the front end again instead of going black and bouncing back to the lobby. The menu
  compares against a clock that has no time offline; it gets one now.

## Under the hood

- The hook DLL is build 31, SHA256 `CC3CE02BFFA7AB563B50490F634D4D0CD2E4E3A95E82CE25B75DF50513945AD1`, rebuilt
  byte-identical from this commit's `clienthook\` with `build.cmd`.
- The hook registers the token channel dvar at boot and writes `cod25\players\tokens.txt` with the counts and the
  remaining seconds. That file is what carries your tokens across a restart; it is written in one piece and renamed
  into place, so a crash mid-write cannot leave a half file.
- The mod folder carries its first game script, `scripts\progression_tuning_tokens.gsc`. It reads the channel in a
  match, puts the game's own level and weapon XP multipliers on the player, widens the performance band to match, and
  writes its state back into a dvar the Lua reads. Nothing of it runs in the front end.
- The two options rows are built from a stock row of the same page, so they look and behave like the client's own.
- The weekly clock fix answers the menu's own time read where it came back empty, under the key it asked with.

## Known gaps

- The Weekly Challenges header still reads `0h 0m 0s`. The menu opens and its rows work; the header figure is not
  filled. Accepted for now.
- The token countdown moves in a match only. In the lobby the chip holds its figure until the next match.
- The two token rows sit at the bottom of the Debug Options list, after the stock rows, rather than straight after
  Extra Minor Augment Slots. They work where they are and stay there.
- Unlock Weapons and Unlock Attachments were flipped by hand in the post-match menu; neither was flipped mid-match.
- The lock-rule gaps listed in rc1.2 are unchanged: other reward types are not on the purchasable rule, ranked-play
  cards, mastery-badge cards, the BETA card and playlist-only cards still read open.
- The Kronos launcher's "verify" step puts the stock `challenges.tsv` back. If weapons stop levelling or cards read
  unlocked again, copy this package's table over it.

## Install

Same as rc1.2, with the hook at build 31, two more parts and the folder's script - see `INSTALL.txt` in the zip.
