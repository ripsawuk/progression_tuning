local PART = "splash"

-- elephants love to SPLASH water. This is for popups

local S = rawget(_G, "ProgressionTuning")
if type(S) ~= "table" then
  S = { parts = {}, hooks = {}, probes = {}, api = {}, g11 = {}, scope = {} }
  rawset(_G, "ProgressionTuning", S)
end
if S.parts[PART] == true then return end
S.parts[PART] = true
local A = S.api
local function log(...) return A.log(...) end
local function clip(...) return A.clip(...) end
local function said(...) return A.said(...) end
local function member(...) return A.member(...) end
local function fn_of(...) return A.fn_of(...) end
local function call(...) return A.call(...) end
local function want(...) return A.want(...) end
local function empty(...) return A.empty(...) end
local function vlog(...) return A.vlog(...) end
local function ours(...) return A.ours(...) end
local function rec_value(...) return A.rec_value(...) end

local PRIO = { level = 1, camo = 3, chal = 4, aug = 6 }
-- the main part own timer step
local TICK_MS = 250
-- the native airtime of a card in ticks
local AIR = { level = 12, camoA = 16, camoB = 12, chalD = 16, chalWB = 16, ret = 16, aug = 12 }
local AIR_MAX = 16
-- the longest native hold of one group
local HOLD_TICKS = 35
-- the native progression unlocks priority
local PROG_PRIO = 27
-- the native challenge complete priority
local CAMO_PRIO = 15
-- the native daily card priority
local DAILY_PRIO = 15
-- the native weekly title hash as the engine prints it
local WEEKLY_HASH = "#x37dc362a78cf1d3d3"
-- our words when the native title is not reachable
local WEEKLY_TITLE = "WEEKLY CHALLENGE COMPLETE"
local KIND_WEAPON = 398
local KIND_DAILY = 438
-- the registered types outside display group one
local GROUP_OTHER = { global = 2, intel = 2, challenge = 3, zmQuestTrackerSplash = 4,
                      zmTrialsTrackerSplash = 5, zmPowerup = 6, zmEchoPermUnlock = 2 }
-- the side panel types which never hold the slot
local SIDE = { weaponProgression = true, rankProgression = true }
-- the card kinds parked for the centre card they ride
local SIDE_KIND = { attach = true, wkxp = true }
-- the client own alias for each kind
local ALIAS = { generalChallenge = "uin_jup_challenge_complete",
                camoChallenge = "uin_jup_challenge_camo_unlock" }

-- the card the last dispatch drew
local LAST = nil
-- the cards parked for a centre card own seq
local PENDING = {}
local SEQ, CENTRE = 0, 0

-- the playdate rows that pay a reward card
local REWARD_ROWS = { { id = 78011, loot = 151944 }, { id = 78014, loot = 149896 } }
-- the one tier a playdate row carries
local REWARD_AT = 1
-- the progress fields a row record can carry
local REWARD_FIELDS = { "default", "progress", "xp" }
-- the poll the playdate rows are read on
local REWARD_POLL = 8
-- the two challenge states a finished row reads
local ST_FINISHED, ST_CLAIMABLE = 3, 2
S.reward = S.reward or { last = {}, bas = {}, done = {}, miss = {} }
local reward_watch = nil
local aug_watch = nil

-- the alias the client own table answers with
local function alias_of(name)
  local _, cs = member(rawget(_G, "SOUND_SETS"), "challengeSplash")
  local _, v = member(cs, name)
  if type(v) == "string" and v ~= "" then return v end
  return ALIAS[name]
end

-- fires the side cards their centre card owns
local function side_fire(seq)
  local i = 1
  while i <= #PENDING do
    local it = PENDING[i]
    if it.owner == seq or it.owner == 0 then
      table.remove(PENDING, i)
      local ok, err = pcall(it.fn)
      if not ok and said("err:side") then
        log("error side card: " .. clip(err, 60) .. " - swallowed")
      end
    else
      i = i + 1
    end
  end
end

-- impregnates a card in the queue
local function enqueue(what, fn)
  if not S.enabled or not want(nil) then return false end
  SEQ = SEQ + 1
  if SIDE_KIND[what] == true then
    PENDING[#PENDING + 1] = { fn = fn, owner = CENTRE }
    return true
  end
  CENTRE = SEQ
  S.q[#S.q + 1] = { what = what, fn = fn, prio = PRIO[what] or 9, at = S.tick or 0, seq = SEQ }
  return true
end

-- hands an event to the client own root
local function fire(ev)
  local lui = rawget(_G, "LUI")
  local getroot = fn_of(lui, "GetRoot")
  if getroot == nil then return false, "no LUI.GetRoot in this VM" end
  local okr, rootEl = pcall(getroot)
  if not okr or rootEl == nil then return false, "no LUI root" end
  local _, uir = member(lui, "UIRoot")
  local fe = (uir ~= nil) and fn_of(uir, "ProcessEvent") or nil
  if fe ~= nil then
    local ok, err = pcall(fe, rootEl, ev)
    if ok then return true, nil end
    return false, err
  end
  fe = fn_of(rootEl, "ProcessEvent")
  if fe ~= nil then
    local ok, err = pcall(fe, rootEl, ev)
    if ok then return true, nil end
    return false, err
  end
  local der = fn_of(rootEl, "dispatchEventToRoot")
  if der ~= nil then
    local ok, err = pcall(der, rootEl, ev)
    if ok then return true, nil end
    return false, err
  end
  return false, "no ProcessEvent and no dispatchEventToRoot on the root"
end

-- the client own record for a splash key
local function splash_row(key)
  local _, hm = member(rawget(_G, "LUI"), "HudManager")
  local inst = fn_of(hm, "GetInstance")
  if inst == nil then return nil end
  local ok, one = pcall(inst)
  if not ok or one == nil then return nil end
  local _, hud = member(one, "activeHud")
  local _, sm = member(hud, "splashManager")
  local _, wm = member(sm, "widgetMap")
  local _, wd = member(wm, key)
  return wd
end

-- the display group a splash key belongs to
local function group_of(key)
  if type(key) ~= "string" then return nil end
  local _, gid = member(splash_row(key), "groupId")
  gid = tonumber(gid)
  if gid ~= nil then return gid end
  return GROUP_OTHER[key] or 1
end

-- is a display group one splash showing right now
local function slot_busy()
  local node = rawget(_G, "DataSources")
  local steps = { "inGame", "MP", "splashes", "currentSplash" }
  local i = 1
  while i <= #steps do
    local _, v = member(node, steps[i])
    node = v
    if node == nil then return nil end
    i = i + 1
  end
  local gv = fn_of(node, "GetValue")
  if gv == nil then return nil end
  local ok, v = pcall(gv, node, 0)
  if not ok then return nil end
  if v == nil then return false end
  local _, su = member(rawget(_G, "LUI"), "SplashUtils")
  local _, ref = member(su, "EmptySplashRef")
  if ref ~= nil and v == ref then return false end
  if v == "empty_splash_ref" then return false end
  if SIDE[v] == true then return false end
  return group_of(v) == 1
end

-- one card per gap, worst first
local function flush()
  if reward_watch ~= nil then pcall(reward_watch) end
  if aug_watch ~= nil then pcall(aug_watch) end
  if #S.q == 0 then return end
  if S.tick < S.nextAt then return end
  local pick = 1
  for i = 2, #S.q do
    if S.q[i].prio < S.q[pick].prio then pick = i end
  end
  local item = S.q[pick]
  local waited = (S.tick - item.at) * TICK_MS
  local busy = slot_busy()
  local rule
  if busy == false then
    rule = "a"
  elseif busy == true and waited < HOLD_TICKS * TICK_MS then
    return
  else
    rule = busy and "c" or "b"
  end
  table.remove(S.q, pick)
  LAST = nil
  local ok, err = pcall(item.fn)
  if not ok and said("err:" .. tostring(item.what)) then
    log("error " .. tostring(item.what) .. ": " .. clip(err, 70) .. " - swallowed")
  end
  local card = LAST
  side_fire(item.seq)
  local air = 0
  if type(card) == "table" then air = AIR[card.kind] or AIR_MAX end
  S.nextAt = S.tick + air
  local h = S.hooks.card
  if h ~= nil then
    pcall(h, type(card) == "table" and card.kind or item.what,
      type(card) == "table" and card.id or nil, waited, rule)
  end
end

-- draws the games own level up banner (woo congrats)
local function level_splash(g, level, total)
  if not ours(g.ref) then return end
  local gate = fn_of(rawget(_G, "PROGRESSION"), "isweaponprogressionchallenge")
  if gate ~= nil then
    local okg, v = pcall(gate, KIND_WEAPON, g.id)
    if okg and v ~= true then
      if said("lgate:" .. g.id) then
        log("level card for row " .. tostring(g.id) .. " refused - isweaponprogressionchallenge is false")
      end
      return
    end
  end
  local ok, err = fire({ name = "completed_challenge", controller = 0, kind = KIND_WEAPON, id = g.id,
                         progress = { rank = level, prestige = g.prestige or 0 } })
  if ok then
    LAST = { kind = "level", id = g.id }
    log("level " .. clip(g.ref, 28) .. " crossed " .. tostring(level) .. " row " .. tostring(g.id)
      .. " rank=" .. tostring(level) .. " banner=" .. tostring(level + 1)
      .. " total=" .. tostring(total)
      .. " rung=" .. tostring(g.ladder ~= nil and g.ladder[level] or "-") .. " src=dll")
  else
    if said("err:level") then
      log("level card for row " .. tostring(g.id) .. " failed: " .. clip(err, 60))
    end
  end
end

-- is the game own splash switch off
local function notifications_off()
  local f = fn_of(rawget(_G, "Challenge"), "AreAchievementNotificationsOff")
  if f == nil then return false end
  local ok, v = pcall(f)
  return ok and v == true
end

-- draws the client own unlock card
local function attach_splash(loot, g, level, total)
  if notifications_off() then
    if said("notifoff") then vlog("attachment cards stand down - the game's own achievement splash switch is off") end
    return
  end
  local LOOT = rawget(_G, "LOOT")
  local ty = call(LOOT, "gettypeforid", loot)
  local ref = call(LOOT, "getitemreffromid", loot)
  if empty(ref) then ref = call(rawget(_G, "ATTACHMENT"), "getrefbyid", loot) end
  if empty(ref) then
    if said("aref:" .. tostring(loot)) then vlog("attachment " .. tostring(loot) .. " has no ref - no card") end
    return
  end
  if not ours(ref) then
    if said("acarry:" .. tostring(loot)) then
      vlog("attachment " .. tostring(loot) .. " is " .. clip(ref, 28) .. ", not one of ours - no card")
    end
    return
  end
  local name = call(LOOT, "getitemnamebyid", loot, true)
  local image = call(LOOT, "getitemimagebyid", loot)
  local opts = { controllerIndex = 0, displayLocation = "weaponProgression", itemRef = ref,
                 priority = PROG_PRIO, displayTimeOverride = 30 }
  if ty ~= nil then opts.itemType = ty end
  if not empty(name) then opts.headerText = name end
  if not empty(image) and image ~= "white" then opts.image = image end
  local ok, err = fire({ name = "add_message_splash_manager", immediate = true, options = opts })
  if ok then
    log("attachment " .. tostring(loot) .. " " .. (empty(name) and "?" or clip(name, 30))
      .. " ref=" .. clip(ref, 28) .. " row " .. tostring(g.id) .. " lv=" .. tostring(level)
      .. " total=" .. tostring(total)
      .. " rung=" .. tostring(g.ladder ~= nil and g.ladder[level] or "-"))
  elseif said("err:attach") then
    log("attachment " .. tostring(loot) .. " failed: " .. clip(err, 60))
  end
end

-- the item own name
local function attach_name(loot)
  local nm = call(rawget(_G, "LOOT"), "getitemnamebyid", loot, true)
  if empty(nm) then return nil end
  return nm
end

-- draws one camo completion the client own way
local function camo_show(row, target, tier, value)
  if row.id == nil then return end
  local ch = rawget(_G, "Challenge")
  if type(ch) ~= "table" then
    if said("camonochal") then log("camo card id=" .. tostring(row.id) .. " skipped - no Challenge in this VM") end
    return
  end
  local gate = call(ch, "shouldshowcompletionsplash", { kind = KIND_WEAPON, id = row.id, controller = 0 })
  if gate ~= true then
    if said("camogate:" .. tostring(row.id) .. ":" .. tostring(target)) then
      log("camo card id=" .. tostring(row.id) .. " row=" .. tostring(row.ref) .. " target="
        .. tostring(target) .. " no route - shouldshowcompletionsplash answered " .. tostring(gate))
    end
    return
  end
  local wp = call(rawget(_G, "PROGRESSION"), "isweaponprogressionchallenge", KIND_WEAPON, row.id)
  if wp == true then
    if said("camowp:" .. tostring(row.id)) then
      log("camo card id=" .. tostring(row.id) .. " row=" .. tostring(row.ref) .. " target="
        .. tostring(target) .. " no route - isweaponprogressionchallenge answered true for kind "
        .. KIND_WEAPON .. ", and that path saves the weapon's own XP")
    end
    return
  end
  local camo = call(ch, "isgunsmithcamochallenge", row.id, KIND_WEAPON, 0)
  if camo == true then
    local ok, err = fire({ name = "completed_challenge", controller = 0, kind = KIND_WEAPON, id = row.id,
                           progress = {} })
    if ok then
      LAST = { kind = "camoA", id = row.id }
      log("camo card id=" .. tostring(row.id) .. " row=" .. tostring(row.ref) .. " target="
        .. tostring(target) .. " route=A value=" .. tostring(value) .. " tier=" .. tostring(tier))
      return
    end
    if said("camoerrA:" .. tostring(row.id)) then
      log("camo card id=" .. tostring(row.id) .. " route A refused at dispatch: " .. clip(err, 50))
    end
  end
  local builder = fn_of(ch, "setgunsmithcamochallengesplashdata")
  if builder == nil then
    if said("camobuild:" .. tostring(row.id)) then
      log("camo card id=" .. tostring(row.id) .. " row=" .. tostring(row.ref) .. " target="
        .. tostring(target) .. " no route - no Challenge.setgunsmithcamochallengesplashdata in this VM")
    end
    return
  end
  local opts = { controllerIndex = 0, displayLocation = "camoChallenge", priority = CAMO_PRIO,
                 sound = alias_of("camoChallenge") }
  local reward = { desc = call(ch, "getDesc", row.id, KIND_WEAPON), amount = target, id = row.id }
  local okb, berr = pcall(builder, row.id, KIND_WEAPON, 0, opts, reward)
  if not okb then
    if said("camoberr:" .. tostring(row.id)) then
      log("camo card id=" .. tostring(row.id) .. " route B refused by the builder: " .. clip(berr, 50))
    end
    return
  end
  local ok, err = fire({ name = "add_message_splash_manager", immediate = true, options = opts })
  if ok then
    LAST = { kind = "camoB", id = row.id }
    log("camo card id=" .. tostring(row.id) .. " row=" .. tostring(row.ref) .. " target="
      .. tostring(target) .. " route=B value=" .. tostring(value) .. " tier=" .. tostring(tier))
  elseif said("camoerrB:" .. tostring(row.id)) then
    log("camo card id=" .. tostring(row.id) .. " route B refused at dispatch: " .. clip(err, 50))
  end
end

-- draws one delireticle completion
local function ret_show(row, target, tier, value)
  if row.id == nil then return end
  local ch = rawget(_G, "Challenge")
  if type(ch) ~= "table" then
    if said("retnochal") then log("reticle card id=" .. tostring(row.id) .. " skipped - no Challenge in this VM") end
    return
  end
  local kind = S.ret.kind
  local gate = call(ch, "shouldshowcompletionsplash", { kind = kind, id = row.id, controller = 0 })
  if gate ~= true then
    if said("retgate:" .. tostring(row.id) .. ":" .. tostring(target)) then
      log("reticle card id=" .. tostring(row.id) .. " row=" .. tostring(row.ref) .. " target="
        .. tostring(target) .. " no route - shouldshowcompletionsplash answered " .. tostring(gate))
    end
    return
  end
  local ok, err = fire({ name = "completed_challenge", controller = 0, kind = kind, id = row.id, progress = {} })
  if ok then
    LAST = { kind = "ret", id = row.id }
    log("reticle card id=" .. tostring(row.id) .. " row=" .. tostring(row.ref) .. " target="
      .. tostring(target) .. " route=A value=" .. tostring(value) .. " tier=" .. tostring(tier))
  elseif said("reterr:" .. tostring(row.id)) then
    log("reticle card id=" .. tostring(row.id) .. " failed: " .. clip(err, 50))
  end
end

-- is the answer still a key or hash
local function keyish(v)
  if type(v) ~= "string" or v == "" then return true end
  if string.find(v, "/", 1, true) ~= nil then return true end
  if string.match(v, "^#x%x+$") ~= nil then return true end
  if string.match(v, "0x%x%x%x%x%x%x%x%x") ~= nil then return true end
  if #v >= 12 and string.match(v, "^%x+$") ~= nil then return true end
  return false
end

-- the readable key the client resolved in the same vm
local WEEKLY_KEY = "challenge/jup_ch_weekly_challenge_completed"
-- the hash as the decompiler prints its value
local WEEKLY_VALUE = "0x7dc362a78cf1d3d3"
-- the marker glyph the client puts before the title
local WEEKLY_MARK = "\226\150\188"

-- one localise answer with the marker stripped
local function weekly_text(loc, key)
  local ok, v = pcall(loc, key)
  if not ok or type(v) ~= "string" then return nil end
  if string.sub(v, 1, #WEEKLY_MARK) == WEEKLY_MARK then v = string.sub(v, #WEEKLY_MARK + 1) end
  if empty(v) or keyish(v) then return nil end
  return v
end

-- the game own weekly title resolved now
local function weekly_native()
  local loc = fn_of(rawget(_G, "Engine"), "Localize")
  if loc == nil then return nil end
  local forms = { WEEKLY_HASH, WEEKLY_KEY, WEEKLY_VALUE }
  local i = 1
  while i <= #forms do
    local v = weekly_text(loc, forms[i])
    if v ~= nil then return v end
    i = i + 1
  end
  return nil
end

-- the header text native first
local header_said = false
local function weekly_header()
  local v = weekly_native()
  if not header_said then
    header_said = true
    if v == nil then
      log("weekly header=none")
    else
      log("weekly header native=" .. clip(v, 60))
    end
  end
  if v == nil then return WEEKLY_TITLE end
  return v
end

-- the description with a plain number
local function weekly_plain(row, target)
  local desc = call(rawget(_G, "Challenge"), "getDesc", row.id, row.kind)
  if empty(desc) then return nil end
  local loc = fn_of(rawget(_G, "Engine"), "Localize")
  if loc == nil then return nil end
  local ok, v = pcall(loc, desc, tostring(target))
  if not ok or keyish(v) then return nil end
  return v
end

-- the client own description one line per card
local function weekly_body(row, target)
  local v = call(rawget(_G, "Challenge"), "getdesclocalizedbyid", 0, row.id, row.kind)
  if empty(v) or keyish(v) then v = weekly_plain(row, target) end
  if empty(v) or keyish(v) then
    log("weekly body=empty")
    return ""
  end
  return v
end

-- empties the subheader an earlier card left behind
local function weekly_clear()
  local _, widget = member(splash_row("dailyNotification"), "widget")
  local _, sub = member(widget, "SplashTrapSubheader")
  local _, txt = member(sub, "matchobjectivetext")
  local f = fn_of(txt, "setText")
  if f == nil then return false end
  local ok = pcall(f, txt, "", 0)
  return ok
end

-- one side card for one reward
local function weekly_reward(row, e)
  local opts = { controllerIndex = 0, displayLocation = "weaponProgression", displayTimeOverride = 30 }
  local _, img = member(e, "image")
  local _, nm = member(e, "name")
  if not empty(img) then opts.image = img end
  if not empty(nm) then opts.headerText = nm end
  local ok, err = fire({ name = "add_message_splash_manager", immediate = true, options = opts })
  if not ok then return false, err end
  return true, nil
end

-- sends one side card per reward the row pays
local function weekly_pay(row)
  local list = call(rawget(_G, "Challenge"), "getrewards", { id = row.id }, row.kind, 0)
  if type(list) ~= "table" or #list == 0 then
    log("weekly xp id=" .. tostring(row.id) .. " none")
    return
  end
  local i = 1
  while i <= #list do
    local e = list[i]
    if type(e) == "table" and weekly_reward(row, e) ~= true then
      log("weekly xp id=" .. tostring(row.id) .. " side card refused")
    end
    i = i + 1
  end
end

-- the weekly card on the daily type
local function weekly_show(row, target, value)
  local body = weekly_body(row, target)
  local opts = { controllerIndex = 0, displayLocation = "dailyNotification", priority = DAILY_PRIO,
                 headerText = weekly_header(), bodyText = body,
                 sound = alias_of("generalChallenge") }
  local ok, err = fire({ name = "add_message_splash_manager", immediate = true, options = opts })
  if not ok then return false, err end
  if body == "" then weekly_clear() end
  LAST = { kind = "chalWB", id = row.id }
  log("weekly card id=" .. tostring(row.id) .. " row=" .. tostring(row.ref) .. " kind=" .. tostring(row.kind)
    .. " target=" .. tostring(target) .. " value=" .. tostring(value) .. " route=B")
  weekly_pay(row)
  return true, nil
end

-- draws one challenge completion with the row own kind
local function chal_show(row, target, value)
  if row.id == nil then return end
  local ch = rawget(_G, "Challenge")
  if type(ch) ~= "table" then
    if said("chalnochal") then log("daily card id=" .. tostring(row.id) .. " skipped - no Challenge in this VM") end
    return
  end
  local kind = row.kind
  local gate = call(ch, "shouldshowcompletionsplash", { kind = kind, id = row.id, controller = 0 })
  if gate ~= true then
    if said("chalgate:" .. tostring(row.id) .. ":" .. tostring(target)) then
      log("daily card id=" .. tostring(row.id) .. " row=" .. tostring(row.ref) .. " kind="
        .. tostring(kind) .. " target=" .. tostring(target)
        .. " no route - shouldshowcompletionsplash answered " .. tostring(gate))
    end
    return
  end
  local isw = call(ch, "isweeklychallengetype", kind)
  local ok, err
  if isw == true then
    ok, err = weekly_show(row, target, value)
  else
    ok, err = fire({ name = "completed_challenge", controller = 0, kind = kind, id = row.id, progress = {} })
    if ok then
      LAST = { kind = "chalD", id = row.id }
      log("daily card id=" .. tostring(row.id) .. " row=" .. tostring(row.ref) .. " kind=" .. tostring(kind)
        .. " target=" .. tostring(target) .. " value=" .. tostring(value) .. " route=A")
    end
  end
  if ok then
    if kind ~= KIND_DAILY then
      local en = nil
      local gb = fn_of(rawget(_G, "Dvar"), "GetDvarBool")
      if gb ~= nil then
        local oke, ve = pcall(gb, "lui_weekly_challenge_menu_enabled")
        if oke then en = ve end
      end
      log("chal week card id=" .. tostring(row.id) .. " ref=" .. clip(tostring(row.ref), 34)
        .. " kind=" .. tostring(kind) .. " enabled=" .. tostring(en) .. " isweekly=" .. tostring(isw)
        .. " splash=" .. tostring(gate) .. " route=" .. (isw == true and "B" or "A"))
    end
  elseif said("chalerr:" .. tostring(row.id)) then
    log("daily card id=" .. tostring(row.id) .. " failed: " .. clip(err, 50))
  end
end

-- is the row record finished
local function reward_done(rec)
  if type(rec) ~= "table" then return nil end
  local _, st = member(rec, "status")
  st = tonumber(st)
  if st ~= nil then return st == ST_FINISHED or st == ST_CLAIMABLE end
  local v = rec_value(rec, REWARD_FIELDS)
  if v == nil then return nil end
  return v >= REWARD_AT
end

-- draws one playdate reward as an item card
local function reward_show(e)
  if notifications_off() then
    if said("notifoff") then vlog("reward cards stand down - the game own achievement splash switch is off") end
    return
  end
  local LOOT = rawget(_G, "LOOT")
  local ref = call(LOOT, "getitemreffromid", e.loot)
  if empty(ref) then
    log("reward " .. tostring(e.loot) .. " row " .. tostring(e.id) .. " has no ref - no card")
    return
  end
  local ty = call(LOOT, "gettypeforid", e.loot)
  local name = call(LOOT, "getitemnamebyid", e.loot, true)
  local image = call(LOOT, "getitemimagebyid", e.loot)
  local opts = { controllerIndex = 0, displayLocation = "weaponProgression", itemRef = ref,
                 priority = PROG_PRIO, displayTimeOverride = 30 }
  if ty ~= nil then opts.itemType = ty end
  if not empty(name) then opts.headerText = name end
  if not empty(image) and image ~= "white" then opts.image = image end
  local ok, err = fire({ name = "add_message_splash_manager", immediate = true, options = opts })
  if ok then
    LAST = { kind = "chalD", id = e.id }
    log("reward card " .. tostring(e.loot) .. " " .. (empty(name) and "?" or clip(name, 30))
      .. " ref=" .. clip(ref, 28) .. " row " .. tostring(e.id) .. " type=" .. tostring(ty))
  elseif said("err:reward") then
    log("reward card " .. tostring(e.loot) .. " failed: " .. clip(err, 60))
  end
end

-- queues one playdate card once
local function reward_card(e)
  local r = S.reward
  local k = tostring(e.id)
  if r.done[k] == true then return false end
  if not enqueue("chal", function() reward_show(e) end) then return false end
  r.done[k] = true
  return true
end

-- one baseline reading then one cross per row
reward_watch = function()
  local r = S.reward
  if S.tick % REWARD_POLL ~= 0 then return end
  local read = S.record
  if type(read) ~= "function" then return end
  local i = 1
  while i <= #REWARD_ROWS do
    local e = REWARD_ROWS[i]
    local now = reward_done(read(e.id))
    if now ~= nil then
      local k = tostring(e.id)
      if r.bas[k] == nil then
        if r.last[k] == now then
          r.bas[k] = now
          if now then r.done[k] = true end
          vlog("reward row " .. k .. " stands " .. (now and "done" or "open"))
        else
          r.last[k] = now
        end
      elseif now ~= r.bas[k] then
        r.bas[k] = now
        if now then reward_card(e) end
      end
    else
      local k = tostring(e.id)
      r.miss[k] = (r.miss[k] or 0) + 1
      if r.miss[k] == 32 then log("reward row " .. k .. " reads nothing - no card this match") end
    end
    i = i + 1
  end
end

-- is this the match vm
local function in_match()
  local f = fn_of(rawget(_G, "Engine"), "InFrontend")
  if f == nil then return true end
  local ok, v = pcall(f)
  if not ok then return true end
  return v ~= true
end

-- the augment name one loot id answers
local function aug_name(loot)
  local nm = call(rawget(_G, "LOOT"), "getitemnamebyid", loot, true)
  if empty(nm) or keyish(nm) then return nil end
  return nm
end

-- draws one augment research completion
local function aug_show(e)
  local LOOT = rawget(_G, "LOOT")
  local image = call(LOOT, "getitemimagebyid", e.loot)
  local name = aug_name(e.loot)
  local opts = { controllerIndex = 0, displayLocation = "zmAugmentResearchComplete" }
  if not empty(image) and image ~= "white" then opts.icon = image end
  if name ~= nil then opts.bodyText = name end
  local ok, err = fire({ name = "add_message_splash_manager", immediate = true, options = opts })
  if ok then
    LAST = { kind = "aug", id = e.loot }
    log("splash augment card ref=" .. tostring(e.ref) .. " tier=" .. tostring(e.tier) .. " drawn=true")
  else
    log("splash augment card ref=" .. tostring(e.ref) .. " tier=" .. tostring(e.tier) .. " drawn=false")
    if said("augerr:" .. tostring(e.ref) .. ":" .. tostring(e.tier)) then
      vlog("augment card refused at dispatch: " .. clip(err, 50))
    end
  end
end

-- drains the crossings the augments part queued
aug_watch = function()
  local aug = S.aug
  if type(aug) ~= "table" then return end
  local list = aug.cards
  if type(list) ~= "table" or #list == 0 then return end
  if not in_match() then return end
  while #list > 0 do
    local e = table.remove(list, 1)
    if type(e) == "table" then
      if not enqueue("aug", function() aug_show(e) end) then
        if said("augoff:" .. tostring(e.ref) .. ":" .. tostring(e.tier)) then
          vlog("augment card dropped - the mod switch is off")
        end
      end
    end
  end
end

S.draw = { queue = enqueue, flush = flush, level = level_splash, attach = attach_splash,
           name = attach_name, camo = camo_show, ret = ret_show, chal = chal_show, group = group_of,
           wkhead = weekly_native }
S.probes.splash = function() return type(A.log) == "function" and type(A.member) == "function" end

local dp = rawget(_G, "DebugPrint") or rawget(_G, "print")
if type(dp) == "function" then pcall(dp, "progression_tuning: part splash armed") end

if A.ready ~= nil then A.ready() end
