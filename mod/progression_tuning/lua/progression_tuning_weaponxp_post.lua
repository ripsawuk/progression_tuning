local PART = "weaponxp"

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
local function vlog(...) return A.vlog(...) end
local function member(...) return A.member(...) end
local function fn_of(...) return A.fn_of(...) end
local function call(...) return A.call(...) end
local function want(...) return A.want(...) end
local function count_passed(...) return A.count_passed(...) end
local function numlist(...) return A.numlist(...) end
local function cell_pick(...) return A.cell_pick(...) end
local function gun_tries(...) return A.gun_tries(...) end
local function resolve_gun(...) return A.resolve_gun(...) end
local function ours(...) return A.ours(...) end

local MINXP_MAX = 40
local PICK_SAY_CAP = 3

local function enqueue(what, fn)
  local d = S.draw
  local q = d ~= nil and d.queue or nil
  if q == nil then
    if said("nosplash") then log("splash absent - no card is drawn") end
    return false
  end
  return q(what, fn)
end

local function level_splash(g, level, total)
  local f = S.draw
  f = f ~= nil and f.level or nil
  if f == nil then return end
  f(g, level, total)
end

local function attach_splash(loot, g, level, total)
  local f = S.draw
  f = f ~= nil and f.attach or nil
  if f == nil then return end
  f(loot, g, level, total)
end

local function attach_name(loot)
  local f = S.draw
  f = f ~= nil and f.name or nil
  if f == nil then return nil end
  return f(loot)
end

-- the weapon ref behind a loot id
local function loot_ref(lid)
  local c = S.lootref[lid]
  if c ~= nil then return c end
  local lo = rawget(_G, "LOOT")
  local r = call(lo, "GetItemRef", lid)
  if type(r) ~= "string" or r == "" then r = call(lo, "getitemreffromid", lid) end
  if type(r) ~= "string" or r == "" then r = nil end
  if r ~= nil then S.lootref[lid] = r end
  return r
end

-- the client own per level cost list
local function minxp_ladder(ref)
  local f = fn_of(rawget(_G, "PROGRESSION"), "getweaponlevelminxp")
  if f == nil then return nil, 0, "no PROGRESSION.getweaponlevelminxp in this VM" end
  local out, n, i = {}, 0, 1
  while i <= MINXP_MAX do
    local ok, v = pcall(f, 0, ref, i)
    if not ok or type(v) ~= "number" then break end
    n = n + 1
    out[n] = v
    i = i + 1
  end
  if n < 1 then return nil, 0, "getweaponlevelminxp answered no level for " .. clip(ref, 24) end
  return out, n, nil
end

-- the weapon progression table
local function weapon_data(ref)
  local f = fn_of(rawget(_G, "WEAPON"), "getweapondataforref")
  if f == nil then return nil, "no WEAPON.getweapondataforref in this VM" end
  local ok, d = pcall(f, ref)
  if not ok or type(d) ~= "table" then return nil, "getweapondataforref answered no table" end
  local _, p = member(d, "weaponProgression")
  if type(p) ~= "table" then return nil, "its weaponProgression is not a table" end
  return p, nil
end

-- the cost lists this weapon could have
local function ladders(ref)
  local mx = nil
  local mf = fn_of(rawget(_G, "PROGRESSION"), "getmaxweaponlevel")
  if mf ~= nil then
    local okm, vm = pcall(mf, ref)
    local nm = tonumber(vm)
    if okm and nm ~= nil then
      nm = math.floor(nm)
      if nm > 0 then mx = nm end
    end
  end
  local out, n = {}, 0
  -- a cost list must rise every rung
  local function rising(t, m)
    local last = nil
    local i = 1
    while i <= m do
      local v = tonumber(t[i])
      if v == nil then return false end
      if last ~= nil and v <= last then return false end
      last = v
      i = i + 1
    end
    return true
  end
  -- keeps a list that rises
  local function add(t, m, src)
    if t == nil or m < 1 then return end
    if not rising(t, m) then return end
    if mx ~= nil and m > mx then m = mx end
    n = n + 1
    out[n] = { t, m, src }
  end
  local t, m = minxp_ladder(ref)
  add(t, m, "minxp")
  local cell = cell_pick(gun_tries(ref), "amount")
  local c2, k2 = numlist(cell)
  add(c2, k2, "csv")
  return out, n
end

-- the level the profile already holds
local function own_level(ref)
  local g = S.guns[ref]
  local id = nil
  if g ~= nil then id = g.id end
  if id == nil then id = resolve_gun(ref) end
  local r = S.record(id)
  if r == nil then return nil end
  local prog = r.progress
  if type(prog) ~= "table" then return nil end
  local _, rk = member(prog, "rank")
  local n = tonumber(rk)
  if n == nil then n = 0 end
  if n < 0 then n = 0 end
  return math.floor(n)
end

-- the weapon prestige the profile holds
local function own_prestige(ref)
  local f = fn_of(rawget(_G, "PRESTIGE"), "getweaponprestigelevel")
  if f == nil then return 0 end
  local ok, v = pcall(f, 0, ref)
  if not ok then return 0 end
  local n = tonumber(v)
  if n == nil or n < 0 then return 0 end
  return math.floor(n)
end

-- the list that reproduces the client own level
local function pick_ladder(ref, total)
  local cands, n = ladders(ref)
  local own = own_level(ref)
  local info = { own = own, cands = cands, cn = n }
  if own == nil then return nil, 0, "own", info end
  local i = 1
  while i <= n do
    local c = cands[i]
    if c[2] >= 1 and count_passed(c[1], c[2], total) == own then return c[1], c[2], c[3], info end
    i = i + 1
  end
  return nil, 0, "none", info
end

-- the gun this ref already made
local function gun_for_ref(ref)
  if type(ref) ~= "string" or ref == "" then return nil end
  return S.guns[ref]
end

-- a gun to carry this ref ladder
local function new_gun(ref, id)
  local g = { ref = ref, id = id, level = nil, primed = false, ladder = nil, n = 0, src = nil,
              prestige = own_prestige(ref), foreign = not ours(ref) }
  S.guns[ref] = g
  if id ~= nil then S.byid[id] = g end
  return g
end

-- finds or makes the gun behind a loot id
local function bind_loot(lid)
  local g = S.lootgun[lid]
  if g ~= nil then return g end
  local ref = loot_ref(lid)
  if ref == nil then return nil end
  g = gun_for_ref(ref)
  if g == nil then
    if not ours(ref) then
      S.foreign[ref] = true
      if said("carried:" .. tostring(ref)) then
        vlog("loot " .. tostring(lid) .. " -> " .. clip(ref, 40) .. " is not one of ours - not bound")
      end
      return nil
    end
    local id, why = resolve_gun(ref)
    if id == nil then
      if said("gun:" .. tostring(ref)) then
        vlog("loot " .. tostring(lid) .. " -> " .. clip(ref, 40) .. " - " .. tostring(why))
      end
      return nil
    end
    g = new_gun(ref, id)
    vlog("gun " .. clip(ref, 40) .. " -> row " .. tostring(id)
      .. " prestige=" .. tostring(g.prestige))
  end
  S.lootgun[lid] = g
  return g
end

-- the items a level unlocks per the client
local function reward_loots(ref, level)
  local f = fn_of(rawget(_G, "PROGRESSION"), "GetRewardUnlockedAtWeaponLevel")
  if f == nil then return nil, 0, "no PROGRESSION.GetRewardUnlockedAtWeaponLevel in this VM" end
  local ok, list = pcall(f, ref, level)
  if not ok or type(list) ~= "table" then
    return nil, 0, "GetRewardUnlockedAtWeaponLevel answered no list for level " .. tostring(level)
  end
  local out, n = {}, 0
  local i = 1
  while i <= #list do
    local u = list[i]
    if type(u) == "table" then
      local _, lid = member(u, "lootid")
      local v = tonumber(lid)
      if v ~= nil then
        n = n + 1
        out[n] = v
      end
    end
    i = i + 1
  end
  if n < 1 then
    return nil, 0, "GetRewardUnlockedAtWeaponLevel listed no lootid for level " .. tostring(level)
  end
  return out, n, nil
end

-- same answer three ways because the client is shit
local function display_loots(g, level)
  if not ours(g.ref) then return nil, 0, "none", "foreign ref" end
  local ids, k, why = reward_loots(g.ref, level)
  if ids ~= nil then return ids, k, "reward", nil end
  local p = weapon_data(g.ref)
  if p ~= nil then
    local e = p[level + 1]
    if type(e) == "table" then
      local _, list = member(e, "levelunlocks")
      if type(list) == "table" then
        local out, m = {}, 0
        local i = 1
        while i <= #list do
          local u = list[i]
          if type(u) == "table" then
            local _, lid = member(u, "lootid")
            local v = tonumber(lid)
            if v ~= nil then
              m = m + 1
              out[m] = v
            end
          end
          i = i + 1
        end
        if m > 0 then return out, m, "weapon", nil end
      end
    end
  end
  local cell = cell_pick(gun_tries(g.ref), "loot")
  if cell == nil then
    return nil, 0, "none", tostring(why) .. "; no loot cell in either CSV"
  end
  local i = 0
  local tok = nil
  for part in string.gmatch(cell, "[^|]+") do
    i = i + 1
    if i == level then tok = part end
  end
  if tok == nil then return nil, 0, "none", tostring(why) .. "; the loot cell has no group " .. tostring(level) end
  local a, m = {}, 0
  for part in string.gmatch(tok, "[^+]+") do
    local lid = tonumber(part)
    if lid ~= nil then
      m = m + 1
      a[m] = lid
    end
  end
  if m == 0 then return nil, 0, "none", tostring(why) .. "; that group holds no loot id" end
  return a, m, "csv", nil
end

-- one card per item name at this level
local function enqueue_attach(g, level, total)
  if g.id == nil or g.foreign then return end
  local ids, k, src, why = display_loots(g, level)
  if ids == nil or k < 1 then
    if said("noloot:" .. tostring(g.id)) then
      vlog("row " .. tostring(g.id) .. " has no loot list - level " .. level .. " draws no attachment card ("
        .. tostring(why) .. ")")
    end
    return
  end
  local taken = {}
  local j = 1
  while j <= k do
    local lid = ids[j]
    local nm = attach_name(lid)
    local kk = (nm ~= nil) and ("n:" .. nm) or ("l:" .. tostring(lid))
    if not taken[kk] then
      taken[kk] = true
      enqueue("attach", function() attach_splash(lid, g, level, total) end)
    elseif said("dup:" .. tostring(g.id) .. ":" .. level .. ":" .. tostring(lid)) then
      vlog("attachment " .. tostring(lid) .. " at level " .. level .. " answers the same name as another id"
        .. " - one card per name, so the same popup is not shown twice")
    end
    j = j + 1
  end
  if said("loot:" .. tostring(g.id) .. ":" .. level) then
    vlog("row " .. tostring(g.id) .. " level " .. level .. " unlocks " .. k .. " item(s) via " .. tostring(src))
  end
end

-- announces each level this gun passed
local function step_gun(g, ent)
  if S.foreign[g.ref] == true then return end
  local total = ent.total
  if g.ladder == nil then
    local t, n, src, info = pick_ladder(g.ref, total)
    if t ~= nil then g.ladder, g.n, g.src = t, n, src end
    g.own = info.own
    if S.diag or (S.toggles ~= nil and S.toggles.log) then
      local k = S.picksaid[g.ref] or 0
      if k < PICK_SAY_CAP then
        S.picksaid[g.ref] = k + 1
        local parts, i = {}, 1
        while i <= info.cn and i <= 4 do
          local c = info.cands[i]
          parts[#parts + 1] = tostring(c[2]) .. "/" .. tostring(c[3]) .. ":"
            .. tostring(count_passed(c[1], c[2], total))
          i = i + 1
        end
        log("prime " .. clip(g.ref, 28) .. " own=" .. tostring(info.own) .. " total=" .. tostring(total)
          .. " picked=" .. tostring(n) .. "/" .. tostring(src)
          .. " cands=" .. (#parts > 0 and table.concat(parts, " ") or "none"))
      end
    end
  end
  if g.ladder == nil then
    if said("nolvl:" .. tostring(g.ref)) then
      vlog("no ladder answers for " .. clip(g.ref, 40) .. " (own " .. tostring(g.own)
        .. ") - no level banner for it, and the pick is not kept, so the next payment retries")
    end
    return
  end
  local lv = count_passed(g.ladder, g.n, total)
  if not g.primed then
    g.primed = true
    g.level = lv
    log("prime " .. clip(g.ref, 28) .. " lv=" .. tostring(lv) .. " total=" .. tostring(total)
      .. " ladder=" .. tostring(g.n) .. "/" .. tostring(g.src) .. " - the profile's own total on the first"
      .. " sighting, so the levels it already holds are not announced again")
    return
  end
  if lv <= g.level then return end
  local from = g.level
  g.level = lv
  local L = from
  while L < lv do
    L = L + 1
    local at = L
    if want("level") then
      enqueue("level", function() level_splash(g, at, total) end)
      if want("attach") then enqueue_attach(g, at, total) end
    end
  end
end

-- walks every damn gun the payload names
local function step_paid()
  if not S.paidon then return end
  local i = 1
  while i <= S.paidN do
    local lid = S.paidorder[i]
    local ent = S.paid[lid]
    if ent ~= nil then
      local g = bind_loot(lid)
      if g ~= nil then
        ent.gun = g
        g.loot = lid
        step_gun(g, ent)
      end
    end
    i = i + 1
  end
end

-- swaps one member and keeps the original
local function wrap_member(tbl, name, slot, make)
  if type(tbl) ~= "table" then return false end
  if slot.ours ~= nil and slot.key ~= nil and tbl[slot.key] == slot.ours then return false end
  local key, f = member(tbl, name)
  if type(f) ~= "function" or f == slot.ours then return false end
  slot.orig = f
  slot.ours = make(f, slot)
  slot.key = key
  tbl[key] = slot.ours
  return true
end

-- the record answers the payload total
local function live_rec_make(orig, slot)
  return function(c, id, ...)
    local r = orig(c, id, ...)
    local g = S.byid[tonumber(id)]
    if g == nil or not S.paidon then return r end
    local ent = S.paid[g.loot]
    if ent == nil or type(r) ~= "table" then return r end
    local prog = r.progress
    if type(prog) ~= "table" then return r end
    local key = tostring(ent.total) .. ":" .. tostring(g.level)
    local hit = S.live.cache[g.id]
    if hit ~= nil and hit.key == key then return hit.rec end
    local copy, out = {}, {}
    local k, v
    for k, v in pairs(prog) do copy[k] = v end
    copy.xp = ent.total
    copy.default = ent.total
    local lv = nil
    if type(g.level) == "number" then lv = g.level end
    if lv ~= nil then copy.rank = lv end
    for k, v in pairs(r) do out[k] = v end
    out.progress = copy
    S.live.cache[g.id] = { key = key, rec = out }
    local disp = nil
    if lv ~= nil then
      disp = lv + 1
    elseif type(copy.rank) == "number" then
      disp = copy.rank + 1
    end
    log("card level ref=" .. clip(g.ref, 28) .. " row=" .. tostring(g.id) .. " total=" .. tostring(ent.total)
      .. " display=" .. tostring(disp) .. " - the record answers the payload's own total")
    return out
  end
end

-- same total from the default reader
local function live_def_make(orig, slot)
  return function(c, id, ...)
    local r = orig(c, id, ...)
    local g = S.byid[tonumber(id)]
    if g == nil or not S.paidon then return r end
    local ent = S.paid[g.loot]
    if ent == nil then return r end
    return ent.total
  end
end

-- waits for the challenge table then wraps that shit
local function live_install()
  local OC = rawget(_G, "OnlineChallenges")
  if type(OC) ~= "table" then
    S.live.miss = S.live.miss + 1
    if S.live.miss == 120 and said("live:nil") then
      log("the in-match display is not armed - no OnlineChallenges table in this VM")
    end
    return false
  end
  wrap_member(OC, "getchallengeprogress", S.live.rec, live_rec_make)
  wrap_member(OC, "getchallengedefaultprogress", S.live.def, live_def_make)
  S.live.miss = 0
  if not S.live.armed then
    S.live.armed = true
    log("in-match display armed - the client's own progress reads answer ptsplash_paid's total for the guns it"
      .. " names, display only")
  end
  return true
end

S.hooks.paid = step_paid
S.hooks.live = live_install
S.probes.weaponxp = function() return type(A.log) == "function" and type(A.member) == "function" end

local dp = rawget(_G, "DebugPrint") or rawget(_G, "print")
if type(dp) == "function" then pcall(dp, "progression_tuning: part weaponxp armed") end

if A.ready ~= nil then A.ready() end
