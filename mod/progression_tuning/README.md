# The mod - `progression_tuning`

A Kronos mod folder for Call of Duty: Black Ops 7 Zombies. It is UI Lua and two GSC scripts: no game file is
written by the mod, and it displays what the client hook's payload says rather than computing XP of its own.

    mod.json                              name, author, version, type, requires, description
    lua\progression_tuning_main_post.lua  the core: registry, clock, payload readers, the door rule, the timer
    lua\progression_tuning_weaponxp_post.lua  the paid-XP display: gun bind, ladder pick, level crossing, TAB level
    lua\progression_tuning_splash_post.lua    the card drawing service: one queue, one airtime, a fixed order
    lua\progression_tuning_camos_post.lua     camo rows: military, special and mastery crossings
    lua\progression_tuning_challenges_post.lua  daily and weekly sweeps and their completion cards
    lua\progression_tuning_prison_post.lua    the lock door and the gunsmith scope
    lua\progression_tuning_reticles_post.lua  the optic watch (reticle unlocks are not answered yet)
    lua\progression_tuning_armory_post.lua    the armory pick: the game's own armory list and its completion answer
    lua\progression_tuning_augments_post.lua  the augments part: the cache ladder and its tier crossings
    lua\progression_tuning_options_post.lua   the Debug Options rows: XP Token Amount, Enable Double XP
    lua\progression_tuning_tokens_post.lua    the XP token channel: counts, countdown, activation, the menu reads
    lua\progression_tuning_diag_post.lua      a dev part only: the `rc1diag` block, never in a release zip
    scripts\progression_tuning_tokens.gsc     the script side of the token channel: the native XP multipliers
    scripts\progression_tuning_armory.gsc     the armory XP feed: the operator's pre cap match xp in `pt_armory_xp`
    scripts\progression_tuning_see_fire.gsc   a dev probe only: fires the super ee challenge on request

Kronos loads every `*_post.lua` in the folder as its own chunk, and each file in the folder's `scripts\` as its own
GSC program. `main` is required: it holds the registry and the API the other parts call, and it is the part that
reports `core absent - no part <name>` when one is missing. The ten feature parts are optional - delete one
and its feature is simply absent, the rest keep running. The diag Lua part and `see_fire.gsc` are dev parts: they
stay in this folder and are left out of every release zip.

## The token channel

`progression_tuning_tokens_post.lua` and `scripts\progression_tuning_tokens.gsc` are the two ends of one dvar,
`pt_tokens_ch`. The Lua part counts and writes it; the script part reads it inside a match, puts the client's own
level and weapon XP multipliers on the player while a token is live, widens the performance band to match, and
writes its whole state back in `pt_tokens_st`. The same Lua part answers the menu's token tiles with the local
count, fills the double XP end times the token menu reads, and replaces the token footer's text.

The counts themselves are persisted by the hook, not by the mod: `cod25\version.dll` registers `pt_tokens_ch`
at boot and writes the file `cod25\players\tokens.txt` beside the game's own player data. That file is the
mod's memory across launches. Without the hook the part still arms and counts down, but the counts start from
the client's own record and are not kept.

The two rows the part adds to Debug Options come from `progression_tuning_options_post.lua`: `XP Token Amount`
sets every level and weapon token count at once, and `Enable Double XP` holds double XP on without using a
token up.

## The armory XP feed

`scripts\progression_tuning_armory.gsc` is a script of its own, with no part in `pt_tokens_*`. Once per half
second inside a match it reads the operator's own pre cap rank xp field and writes the running total to
`pt_armory_xp` as `s=<match serial>;x=<xp this match>;h=<beat>`. The hook registers that dvar at boot and reads
it; the script writes no file, no store and no player data.
