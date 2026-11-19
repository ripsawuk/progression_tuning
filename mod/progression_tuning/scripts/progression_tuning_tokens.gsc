#using scripts\mp\rank;
#using scripts\mp\weaponrank;

// token channel drives the native multipliers and the damper band
autoexec progression_tuning_tokens_init()
{
    level thread progression_tuning_tokens_main();
}

progression_tuning_tokens_main()
{
    level endon("end_game");
    level.pt_tok_r = 0;
    level.pt_tok_w = 0;
    level.pt_tok_x = 0;
    level.pt_tok_rtot = 0;
    level.pt_tok_wtot = 0;
    level.pt_tok_rboost = 0;
    level.pt_tok_wboost = 0;
    level.pt_tok_seen = 0;
    level.pt_tok_n = 0;
    level.pt_tok_hb = 0;
    level.pt_tok_stage = 0;
    level.pt_tok_ready = 0;
    level.pt_tok_tries = 0;
    level.pt_tok_sig = "";
    level.pt_tok_last = gettime();
    progression_tuning_tokens_stage(1);
    logstring("pt tokens gsc armed ns unverified");
    if (getdvar("pt_tokens_ch", "") == "")
    {
        setdvar("pt_tokens_ch", "p=0;w=0;n=0");
    }
    progression_tuning_tokens_stage(2);
    while (true)
    {
        wait 0.5;
        level.pt_tok_hb = level.pt_tok_hb + 1;
        progression_tuning_tokens_stage(3);
        chan = getdvar("pt_tokens_ch", "");
        level.pt_tok_r = progression_tuning_tokens_field(chan, "p");
        level.pt_tok_w = progression_tuning_tokens_field(chan, "w");
        level.pt_tok_x = progression_tuning_tokens_field(chan, "x");
        now = gettime();
        dt = now - level.pt_tok_last;
        level.pt_tok_last = now;
        if (dt > 0)
        {
            if (level.pt_tok_r > 0 || level.pt_tok_x == 1)
            {
                level.pt_tok_rboost = level.pt_tok_rboost + dt;
            }
            if (level.pt_tok_w > 0 || level.pt_tok_x == 1)
            {
                level.pt_tok_wboost = level.pt_tok_wboost + dt;
            }
        }
        progression_tuning_tokens_players();
        progression_tuning_tokens_band();
        progression_tuning_tokens_diag();
        progression_tuning_tokens_status();
    }
}

// rank and weapon rank arrays on every real player
progression_tuning_tokens_players()
{
    level.pt_tok_rtot = 0;
    level.pt_tok_wtot = 0;
    level.pt_tok_seen = 0;
    level.pt_tok_n = 0;
    onp = level.pt_tok_r > 0 || level.pt_tok_x == 1;
    onw = level.pt_tok_w > 0 || level.pt_tok_x == 1;
    if (!isdefined(level.players))
    {
        return;
    }
    if (!isdefined(level.players.size))
    {
        return;
    }
    i = 0;
    while (i < level.players.size)
    {
        p = level.players[i];
        i = i + 1;
        if (!isdefined(p))
        {
            continue;
        }
        if (!isplayer(p))
        {
            continue;
        }
        if (isbot(p))
        {
            continue;
        }
        level.pt_tok_n = level.pt_tok_n + 1;
        if (onp)
        {
            if (!isdefined(p.rankxpmultipliers["pt_xp_token"]))
            {
                progression_tuning_tokens_stage(4);
                p rank::addrankxpmultiplier(2, "pt_xp_token");
                progression_tuning_tokens_stage(5);
            }
        }
        else if (isdefined(p.rankxpmultipliers["pt_xp_token"]))
        {
            progression_tuning_tokens_stage(6);
            p rank::removerankxpmultiplier("pt_xp_token");
            progression_tuning_tokens_stage(7);
        }
        if (onw)
        {
            if (!isdefined(p.weaponrankxpmultipliers["pt_wxp_token"]))
            {
                progression_tuning_tokens_stage(4);
                p weaponrank::addweaponrankxpmultiplier(2, "pt_wxp_token");
                progression_tuning_tokens_stage(5);
            }
        }
        else if (isdefined(p.weaponrankxpmultipliers["pt_wxp_token"]))
        {
            progression_tuning_tokens_stage(6);
            p.weaponrankxpmultipliers["pt_wxp_token"] = undefined;
            progression_tuning_tokens_stage(7);
        }
        if (level.pt_tok_seen == 0)
        {
            level.pt_tok_seen = 1;
            level.pt_tok_rtot = p rank::getrankxpmultiplier();
            level.pt_tok_wtot = p.weaponrankxpmultipliers["pt_wxp_token"] ?? 0;
        }
    }
}

// damper band captured once then scaled by boosted time
progression_tuning_tokens_band()
{
    if (level.pt_tok_ready < 0)
    {
        return;
    }
    if (level.pt_tok_ready == 0)
    {
        progression_tuning_tokens_capture();
        return;
    }
    if (level.pt_tok_rboost == 0 && level.pt_tok_wboost == 0)
    {
        return;
    }
    e = gettime();
    if (e < 1)
    {
        return;
    }
    fr = 1.0;
    if (level.pt_tok_rboost > 0)
    {
        fr = 1.0 + float(level.pt_tok_rboost) / float(e);
    }
    fw = 1.0;
    if (level.pt_tok_wboost > 0)
    {
        fw = 1.0 + float(level.pt_tok_wboost) / float(e);
    }
    if (isdefined(level.pt_tok_brl))
    {
        level.var_36d4bd62cdd6ddca = int(float(level.pt_tok_brl) * fr);
        level.var_a620a2c9949e7ccd = int(float(level.pt_tok_bru) * fr);
        level.rankxpperformancerange = int(float(level.pt_tok_brr) * fr);
    }
    if (isdefined(level.pt_tok_bwl))
    {
        level.var_c44b237177abcec4 = int(float(level.pt_tok_bwl) * fw);
        level.var_eb216489e733fd6f = int(float(level.pt_tok_bwu) * fw);
        level.weaponxpperformancerange = int(float(level.pt_tok_bwr) * fw);
    }
}

progression_tuning_tokens_capture()
{
    if (!isdefined(level.pt_tok_brl))
    {
        if (isdefined(level.var_36d4bd62cdd6ddca) && isdefined(level.var_a620a2c9949e7ccd) && isdefined(level.rankxpperformancerange))
        {
            level.pt_tok_brl = level.var_36d4bd62cdd6ddca;
            level.pt_tok_bru = level.var_a620a2c9949e7ccd;
            level.pt_tok_brr = level.rankxpperformancerange;
        }
    }
    if (!isdefined(level.pt_tok_bwl))
    {
        if (isdefined(level.var_c44b237177abcec4) && isdefined(level.var_eb216489e733fd6f) && isdefined(level.weaponxpperformancerange))
        {
            level.pt_tok_bwl = level.var_c44b237177abcec4;
            level.pt_tok_bwu = level.var_eb216489e733fd6f;
            level.pt_tok_bwr = level.weaponxpperformancerange;
        }
    }
    if (isdefined(level.pt_tok_brl) && isdefined(level.pt_tok_bwl))
    {
        level.pt_tok_ready = 1;
    }
    else
    {
        level.pt_tok_tries = level.pt_tok_tries + 1;
        if (level.pt_tok_tries < 61)
        {
            return;
        }
        level.pt_tok_ready = 1;
        if (!isdefined(level.pt_tok_brl) && !isdefined(level.pt_tok_bwl))
        {
            level.pt_tok_ready = -1;
        }
    }
    logstring("pt tokens gsc band=" + progression_tuning_tokens_bandtext() + " range=" + level.rankxpperformancerange + "/" + level.weaponxpperformancerange);
}

progression_tuning_tokens_bandtext()
{
    s = "none";
    if (isdefined(level.var_36d4bd62cdd6ddca) && isdefined(level.var_a620a2c9949e7ccd))
    {
        s = level.var_36d4bd62cdd6ddca + "/" + level.var_a620a2c9949e7ccd;
    }
    if (isdefined(level.var_c44b237177abcec4) && isdefined(level.var_eb216489e733fd6f))
    {
        s = s + "," + level.var_c44b237177abcec4 + "/" + level.var_eb216489e733fd6f;
    }
    return s;
}

// band as four ints, zeros before capture
progression_tuning_tokens_bands()
{
    rl = 0;
    ru = 0;
    wl = 0;
    wu = 0;
    if (isdefined(level.pt_tok_brl))
    {
        rl = int(level.pt_tok_brl);
        ru = int(level.pt_tok_bru);
    }
    if (isdefined(level.pt_tok_bwl))
    {
        wl = int(level.pt_tok_bwl);
        wu = int(level.pt_tok_bwu);
    }
    return rl + "/" + ru + "," + wl + "/" + wu;
}

// one channel int by key, 0 when absent
progression_tuning_tokens_field(chan, key)
{
    v = 0;
    parts = strtok(chan, "=;");
    if (!isdefined(parts))
    {
        return 0;
    }
    if (!isarray(parts))
    {
        return 0;
    }
    i = 0;
    while (i + 1 < parts.size)
    {
        if (parts[i] == key)
        {
            v = int(parts[i + 1]);
            break;
        }
        i = i + 1;
    }
    return v;
}

// stage mark plus one snapshot
progression_tuning_tokens_stage(n)
{
    level.pt_tok_stage = n;
    progression_tuning_tokens_status();
}

// the whole state as one status dvar the lua reads
progression_tuning_tokens_status()
{
    cd = 0;
    if (isdefined(level.getcustomweaponxp))
    {
        cd = 1;
    }
    s = "s=" + level.pt_tok_stage + ";h=" + level.pt_tok_hb + ";p=" + level.pt_tok_r + ";w=" + level.pt_tok_w;
    s = s + ";r=" + int(level.pt_tok_rtot) + ";wm=" + int(level.pt_tok_wtot) + ";cw=" + getdvarint(@"hash_827c38f8b953c541", 0);
    s = s + ";cd=" + cd + ";b=" + progression_tuning_tokens_bands() + ";n=" + level.pt_tok_n + ";x=" + level.pt_tok_x;
    setdvar("pt_tokens_st", s);
}

// change only console lines
progression_tuning_tokens_diag()
{
    sig = level.pt_tok_r + "|" + level.pt_tok_w + "|" + level.pt_tok_rtot + "|" + level.pt_tok_wtot;
    if (sig == level.pt_tok_sig)
    {
        return;
    }
    level.pt_tok_sig = sig;
    logstring("pt tokens gsc p=" + level.pt_tok_r + " w=" + level.pt_tok_w + " rank=" + level.pt_tok_rtot + " wpn=" + level.pt_tok_wtot + " band=" + progression_tuning_tokens_bandtext());
}
