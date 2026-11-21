// the operator pre cap rank xp feed for this match
autoexec progression_tuning_armory_init()
{
    level thread progression_tuning_armory_main();
}

progression_tuning_armory_main()
{
    level endon("end_game");
    level.pt_arm_prev = -1;
    level.pt_arm_acc = 0;
    level.pt_arm_beat = 0;
    level.pt_arm_s = int(getdvar("pt_armory_s", "0")) + 1;
    setdvar("pt_armory_s", level.pt_arm_s + "");
    while (true)
    {
        wait 0.5;
        progression_tuning_armory_feed();
    }
}

// publishes the pre cap xp as a running total
progression_tuning_armory_feed()
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
    if (!isdefined(p.var_8b69ecbd466a79fa))
    {
        return;
    }
    x = p.var_8b69ecbd466a79fa["rankxp"];
    if (!isdefined(x))
    {
        return;
    }
    x = int(x);
    if (level.pt_arm_prev >= 0 && x > level.pt_arm_prev)
    {
        level.pt_arm_acc = level.pt_arm_acc + (x - level.pt_arm_prev);
    }
    level.pt_arm_prev = x;
    level.pt_arm_beat = level.pt_arm_beat + 1;
    setdvar("pt_armory_xp", "s=" + level.pt_arm_s + ";x=" + level.pt_arm_acc + ";h=" + level.pt_arm_beat);
}
