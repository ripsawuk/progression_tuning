# Progression Tuning for Kronos client - rc1.2

## What's new

- Challenge rewards are locked by their own kind now, calling cards first. A card is locked unless you have earned it,
  bought it (store or battle pass), or the game ships it as a default.
- The Debug Options unlock switches still work the way they did: each one opens its whole type, and switching it back
  off locks that type again in the same session.
- Prestige calling-card sets up to your own prestige show as available; the sets above it stay gated.
- Weapon prestige camos and attachments wait for that weapon's own prestige level.
- Items a level, rank or prestige list earns are not locked by the new rule.
- Store items respect the platform check: an item the store says is not usable on your platform keeps the client's own
  answer.

## Under the hood

- Client hook build 30 publishes the challenge-reward set as a lock bitmap, so the mod no longer has to guess which ids
  are rewards.
- The shipped `challenges.tsv` carries 53 more calling-card ids in `@cat_cards` (3,079 -> 3,132), so those cards get a
  lock bit from the client's own builder.
- Reward tables are read a column at a time, on demand: the mod asks for a table's loot column instead of every cell,
  one table per tick. The card loader reads three tables instead of eight.
- Lock answers are cached per item and dropped when the game mode changes, so the menus do not pay twice for the same
  question.
- The hook DLL is build 30, SHA256 `FC7D673E6B9BAA49B25E1AD636C13EE74EA1131EF2AE4FFD5398A606E67767D8`, rebuilt
  byte-identical from this commit's `clienthook\` with `build.cmd`.

## Known gaps

- Other reward types - emblems, charms, stickers, sprays and the rest - are not on the purchasable rule yet, so an
  unearned one of those still reads open.
- Ranked-play calling cards stay open: Kronos does not track ranked play, so the client's own bitmap has no bit for them.
- Mastery-badge cards have no lock bit in the shipped table and stay open.
- The BETA card has no bit and stays open.
- The playlist challenge table is still not read, so the cards only that table pays stay open.
- The Kronos launcher's "verify" step puts the stock `challenges.tsv` back. If weapons stop levelling or cards read
  unlocked again, copy this package's table over it.
- Third-party HUD mods can slow the menus down. That was found while testing this build and is not this mod.

## Install

Same as rc1.1, with the hook at build 30 and the new `challenges.tsv` - see `INSTALL.txt` in the zip.
