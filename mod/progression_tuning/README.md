# The mod - `progression_tuning`

A Kronos mod folder for Call of Duty: Black Ops 7 Zombies. It is UI Lua only: no game file is written, no GSC
logic runs, and it displays what the client hook's payload says rather than computing XP of its own.

    mod.json                              name, version, the toggles, one description
    lua\progression_tuning_main_post.lua  the core: registry, clock, payload readers, the door rule, the timer
    lua\progression_tuning_weaponxp_post.lua  the paid-XP display: gun bind, ladder pick, level crossing, TAB level
    lua\progression_tuning_splash_post.lua    the card drawing service: one queue, one airtime, a fixed order
    lua\progression_tuning_camos_post.lua     camo rows: military, special and mastery crossings
    lua\progression_tuning_challenges_post.lua  daily and weekly sweeps and their completion cards
    lua\progression_tuning_prison_post.lua    the lock door and the gunsmith scope
    lua\progression_tuning_reticles_post.lua  the optic watch (reticle unlocks are not answered yet)
    lua\progression_tuning_diag_post.lua      the temporary `rc1diag` block, `pt_diag` off by default

Kronos loads every `*_post.lua` in the folder as its own chunk. `main` is required: it holds the registry and
the API the other parts call, and it is the part that reports `core absent - no part <name>` when one is missing.
The six feature parts are optional - delete one and its feature is simply absent, the rest keep running.
