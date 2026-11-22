#using scripts\common\utility;
#using scripts\mp\challenges;

autoexec progression_tuning_see_fire_init()
{
    level thread progression_tuning_see_fire_main();
}

// one shot super ee reporter driven by a console dvar
progression_tuning_see_fire_main()
{
    level endon("end_game");
    if (isdefined(level.pt_sf_run))
    {
        return;
    }
    level.pt_sf_run = 1;
    setdvar("pt_see_fire", "0");
    setdvar("pt_see_fire_state", "armed");
    while (true)
    {
        wait 1;
        p = progression_tuning_see_fire_player();
        if (!isdefined(p))
        {
            continue;
        }
        if (int(getdvar("pt_see_fire", "0")) != 1)
        {
            continue;
        }
        level utility::callsharedfunc( #"zombie_challenges", #"hash_65886d21168e150a", #"zm_sat_super_ee_complete", [ level.players[0] ] );
        setdvar("pt_see_fire_state", "fired " + level.players[0] challenges::getcurrentoperatorlootid());
        break;
    }
}

// first live player or none
progression_tuning_see_fire_player()
{
    if (!isdefined(level.players))
    {
        return;
    }
    if (!isdefined(level.players.size))
    {
        return;
    }
    if (level.players.size < 1)
    {
        return;
    }
    p = level.players[0];
    if (!isdefined(p))
    {
        return;
    }
    if (!isplayer(p))
    {
        return;
    }
    return p;
}
