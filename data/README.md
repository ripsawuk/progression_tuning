# `data\challenges.tsv` - the weapon level ladder

This is the Kronos challenge table with its 64 weapon-progression rows rewritten as this mod's weapon level
ladder. Those 64 rows are the kind-398 rows named `sat_*_progression`, one per weapon: each row's level thresholds
(the XP a weapon needs per level) and its award rule are ours, and every other row is the client's own.

The table is not optional. The client counts the thresholds in it and pays the award it names, so with the stock
table a weapon levels on the stock curve and the mod's display disagrees with it.

| | |
|---|---|
| this file | 568,536 bytes, SHA256 `2DDFD195D46DF7F359D5F205C1B1BD9368009D4162FB6C36D89212A168A75264` |
| the stock table it replaces | 566,694 bytes, SHA256 `6952F51928A4DF44C4B15B4BDBC3E6372664E9BC9EF187D0BB722DB166057959` |

## Install and rollback

It replaces `cod25\kronos\challenges.tsv` in your install. Back that file up first - copy it to
`challenges.tsv.bak` - then copy this one over it. To roll back, put the backup back.

A Kronos client update may replace the table. If weapons stop levelling, copy this file over
`cod25\kronos\challenges.tsv` again.
