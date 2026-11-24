local PART = "tokens"

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
local function dv(...) return A.dv(...) end
local function empty(...) return A.empty(...) end
local function fn_of(...) return A.fn_of(...) end
local function member(...) return A.member(...) end
local function said(...) return A.said(...) end

-- the aeid each shipped token activates
local AE_LOOT = {
  [48364] = 84672, [48365] = 84675, [48366] = 84673, [48367] = 84674,
  [48338] = 84677, [48355] = 84680, [48356] = 84678, [48357] = 84679,
}
-- the loot id back to its aeid
local LOOT_AE = {}
for a, l in pairs(AE_LOOT) do LOOT_AE[l] = a end
-- the kind names tried and the shipped fallback
local KIND_NAMES = { "cer_ae_kind_tokens", "ae_kind_tokens" }
local AE_KIND = 146
local AE_ACT = "activateachievement"
local AE_EV = "onachievementactivated"

local T = S.tokens
if type(T) ~= "table" then
  T = { n = {}, used = 0, armed = false, x = 0 }
  S.tokens = T
end
T.p, T.w, T.sn = T.p or 0, T.w or 0, T.sn or 0
T.acc = T.acc or 0
T.x = T.x or 0

-- the token channel the gsc reads
local CH = "pt_tokens_ch"
-- the eight counts in channel order
local C_IDS = { 84677, 84680, 84678, 84679, 84672, 84675, 84673, 84674 }
-- loot id to its slot
local C_SLOT = {}
for i, l in ipairs(C_IDS) do C_SLOT[l] = i end
-- the gsc status read only
local ST = "pt_tokens_st"
local HD = rawget(_G, "xhashdvar")
local H = rawget(_G, "xhash")
-- the menu reader and the two token end times
local US_ACT = "getuserstatesvalues"
local DX_P = "cer__doublexp__player_xp_end_time"
local DX_W = "cer__doublexp__weapon_xp_end_time"
-- the loot getters the menus read
local EV_L = { "isdoublexpactive", "isdoubleweaponxpactive" }
-- the two global event checks
local EV_B = { "isdoublexpactivebytype", "IsDoubleWeaponXPActiveByType" }
-- the tokens event triple
local EV_S = "getalldoublexpstates"
-- the global event end times
local EV_E = "GetGlobalDoubleXPEventsEndTime"
-- minutes each aeid holds
local MINS = {
  [48338] = 15, [48355] = 30, [48356] = 45, [48357] = 60,
  [48364] = 15, [48365] = 30, [48366] = 45, [48367] = 60,
}
-- the operator aeids
local OP = { [48338] = true, [48355] = true, [48356] = true, [48357] = true }

local CLK = {}
-- resolves the three engine calls once
local function clock()
  local E = rawget(_G, "Engine")
  if type(E) ~= "table" then return end
  if CLK.ms == nil then CLK.ms = fn_of(E, "GetMilliseconds") end
  if CLK.pz == nil then CLK.pz = fn_of(E, "IsPaused") end
  if CLK.fe == nil then CLK.fe = fn_of(E, "InFrontend") end
  if not said("p2ms") then return end
  if CLK.ms == nil then log("tokens clock missing GetMilliseconds") end
  if CLK.pz == nil then log("tokens clock missing IsPaused") end
  if CLK.fe == nil then log("tokens clock missing InFrontend") end
end

-- the engine milliseconds or nothing
local function now_ms()
  if CLK.ms == nil then return nil end
  local ok, v = pcall(CLK.ms)
  if ok and type(v) == "number" then return v end
  return nil
end

-- the engine own match state
local function flags()
  local front, paused = false, false
  if CLK.fe ~= nil then
    local ok, v = pcall(CLK.fe)
    front = ok and v == true
  end
  if CLK.pz ~= nil then
    local ok, v = pcall(CLK.pz)
    paused = ok and v == true
  end
  return front, paused
end

-- the counts in the c field
local function cparse(v)
  local s = string.match(v, ";c=([%d,]+)")
  if s == nil then return nil end
  local out, i = {}, 0
  for tok in string.gmatch(s, "(%d+)") do
    i = i + 1
    if i > #C_IDS then return nil end
    out[i] = tonumber(tok)
  end
  if i ~= #C_IDS then return nil end
  return out
end

-- the channel p w serial counts flag
local function chread()
  local v = dv(CH)
  if type(v) ~= "string" then return nil end
  local p, w, n = string.match(v, "p=(%d+);w=(%d+);n=(%d+)")
  if p == nil then return nil end
  local x = 0
  if string.match(v, ";x=1") ~= nil then x = 1 end
  return tonumber(p), tonumber(w), tonumber(n), cparse(v), x
end

local DSET
-- writes the channel and says if it landed
local function chwrite()
  if DSET == nil then DSET = fn_of(rawget(_G, "Dvar"), "SetDvarString") end
  if DSET == nil then return false end
  T.sn = T.sn + 1
  local parts = { "p=" .. tostring(T.p), "w=" .. tostring(T.w), "n=" .. tostring(T.sn) }
  if T.c ~= nil then parts[#parts + 1] = "c=" .. table.concat(T.c, ",") end
  parts[#parts + 1] = "x=" .. tostring(T.x or 0)
  local s = table.concat(parts, ";")
  local okh, key = pcall(HD, CH)
  if not okh or key == nil then key = CH end
  local ok = pcall(DSET, key, s)
  if not ok and key ~= CH then pcall(DSET, CH, s) end
  local _, _, n = chread()
  local hit = n == T.sn
  T.wpend = not hit
  if not hit and said("p2chmiss") then log("tokens ch missing") end
  return hit
end

local EV_OURS = setmetatable({}, { __mode = "k" })
local EV_ALL = {}

-- says the event wraps and the flag
local function evsay()
  local s = (#EV_ALL > 0) and table.concat(EV_ALL, ",") or "none"
  local sig = tostring(T.x or 0) .. ":" .. s
  if T.evs == sig then return end
  T.evs = sig
  log("tokens P6 event=" .. tostring(T.x or 0) .. " wraps=" .. s)
end

-- says the permanent flag when it moved
local function xsay()
  if T.xl == T.x then return end
  T.xl = T.x
  log("tokens P5 perm=" .. tostring(T.x))
  evsay()
end

-- the record answer for one loot id
local function own_loot(loot)
  local f = T.orig
  if f == nil then f = fn_of(rawget(_G, "Loot"), "IsOwned") end
  if f == nil then return nil end
  local ok, v = pcall(f, 0, loot)
  if ok then
    v = tonumber(v)
    if v ~= nil and v > 0 then return math.floor(v) end
    if v == false or v == 0 then return 0 end
  end
  return 0
end

-- all eight counts from the record
local function cseed()
  local out, i = {}, 1
  while i <= #C_IDS do
    local n = own_loot(C_IDS[i])
    if n == nil then return nil end
    out[i] = n
    i = i + 1
  end
  return out
end

-- seeds the counts when the channel carries none
local function cfill()
  if T.c ~= nil then return T.c end
  T.c = cseed()
  if T.c ~= nil then T.csrc = "seed" end
  return T.c
end

-- one count off its slot
local function cspend(aeid)
  local loot = AE_LOOT[aeid]
  local i = (loot ~= nil) and C_SLOT[loot] or nil
  if i == nil or T.c == nil then return end
  if T.c[i] > 0 then T.c[i] = T.c[i] - 1 end
end

-- sets every count and writes the channel once
local function cset(n)
  n = math.floor(tonumber(n) or 0)
  if n < 0 then n = 0 end
  local c, i = {}, 1
  while i <= #C_IDS do
    c[i] = n
    i = i + 1
  end
  T.c, T.csrc = c, "opt"
  chwrite()
  return true
end

-- the setter the options row calls
T.set = cset

-- sets the permanent flag and writes once
local function pset(on)
  T.x = (on == true) and 1 or 0
  T.base = nil
  xsay()
  chwrite()
  return true
end

-- the flag the permanent row sets
T.perm = pset

-- adopts the channel when another vm wrote it
local function psync()
  local p, w, n, c, x = chread()
  if p == nil or n == nil or n == T.sn then return false end
  T.p, T.w, T.sn = p, w, n
  T.base = nil
  T.x = x or 0
  xsay()
  if c ~= nil then T.c, T.csrc = c, "chan" end
  return true
end

local UTC = nil
-- the clock the menu reads for now
local function utc()
  if UTC == nil then UTC = fn_of(rawget(_G, "CoD"), "GetUTC") or false end
  local t = nil
  if UTC ~= false then
    local ok, v = pcall(UTC)
    if ok then t = tonumber(v) end
  end
  if t == nil then
    local e = fn_of(rawget(_G, "Engine"), "GetCurrentEpochTime")
    if e ~= nil then
      local ok, v = pcall(e)
      if ok then t = tonumber(v) end
    end
  end
  return t
end

-- the seconds each kind still holds
local function remain()
  local p, w = chread()
  if p == nil then return T.p, T.w end
  return p, w
end

-- does the caller ask for this end time
local function wants(keys, name)
  local ok, hit = pcall(function()
    for k, v in pairs(keys) do
      if v == name or k == name then return true end
    end
    return false
  end)
  return ok and hit == true
end

-- the installed reader and its hashed key
local function reader()
  local OP = rawget(_G, "OnlineProgression")
  if type(OP) ~= "table" then return nil end
  local k, f = member(OP, US_ACT)
  if type(f) ~= "function" then return nil end
  if type(H) == "function" then
    local okh, h = pcall(H, US_ACT)
    if okh and h ~= nil and h ~= k then
      local okv, v = pcall(function() return OP[h] end)
      if okv and type(v) == "function" then return h, v end
    end
  end
  return k, f
end

-- the registry other parts answer through
local U = S.userstate
if type(U) ~= "table" then
  U = { answer = {} }
  S.userstate = U
end
if type(U.answer) ~= "table" then U.answer = {} end

-- one key in its printed form
local function kform(k)
  local ok, s = pcall(tostring, k)
  if not ok or type(s) ~= "string" then return nil end
  local h = string.match(s, "#x(%x+)")
  if h ~= nil then return "0x" .. string.lower(h) end
  return string.lower(s)
end

-- the registered answer for one asked key
local function ufind(k)
  for rk, f in pairs(U.answer) do
    if type(f) == "function" then
      if rk == k then return f end
      local a, b = kform(rk), kform(k)
      if a ~= nil and a == b then return f end
    end
  end
  return nil
end

-- fills the registered keys the read left out
local function ustate(res, keys, c, own)
  for k, v in pairs(keys) do
    local ask = v
    if ask == nil or type(ask) == "boolean" then ask = k end
    local ours = type(own) == "table" and own[ask] == true
    local f = ufind(ask)
    if f ~= nil and not ours then
      local ok, val = pcall(f, { c = c, key = ask })
      if ok and val ~= nil then
        if type(res) ~= "table" then res = {} end
        res[ask] = val
      end
    end
  end
  return res
end

-- fills the two end times the menu reads
local function wrap_end()
  if T.p3 then return true end
  local OP = rawget(_G, "OnlineProgression")
  local k, o = reader()
  if OP == nil or k == nil then
    if said("p3miss") then log("tokens P3 wrap=0") end
    return false
  end
  local w = function(c, keys, ...)
    local res = o(c, keys, ...)
    if type(keys) ~= "table" then return res end
    local p, sec = remain()
    local now = utc()
    local own = {}
    if now ~= nil then
      if p > 0 and wants(keys, DX_P) then
        if type(res) ~= "table" then res = {} end
        res[DX_P] = math.floor((now + p) * 1000)
        own[DX_P] = true
      end
      if sec > 0 and wants(keys, DX_W) then
        if type(res) ~= "table" then res = {} end
        res[DX_W] = math.floor((now + sec) * 1000)
        own[DX_W] = true
      end
    end
    return ustate(res, keys, c, own)
  end
  if not pcall(function() OP[k] = w end) then
    if said("p3set") then log("tokens P3 wrap=0") end
    return false
  end
  T.p3 = true
  log("tokens P3 wrap=1")
  return true
end

-- the plain event answer
local function evplain(o)
  return function(...)
    if T.x == 1 then return true end
    return o(...)
  end
end

-- the answer for a global event only
local function evbytype(o)
  local _, dt = member(rawget(_G, "LOOT"), "doubleXPType")
  if type(dt) ~= "table" then return nil end
  local g, a = dt.GLOBAL, dt.ANY
  if g == nil and a == nil then return nil end
  return function(c, ty, ...)
    if T.x == 1 and (ty == g or ty == a) then return true end
    return o(c, ty, ...)
  end
end

-- the level and weapon state alone
local function evstates(o)
  return function(...)
    local p, w, b = o(...)
    if T.x == 1 then return true, true, b end
    return p, w, b
  end
end

-- no end time on the two event kinds
local function evends(o)
  local _, dt = member(rawget(_G, "PROGRESSION"), "DoubleXPType")
  if type(dt) ~= "table" or dt.PLAYER == nil or dt.WEAPON == nil then return nil end
  local p, w = dt.PLAYER, dt.WEAPON
  return function(...)
    local res = o(...)
    if T.x ~= 1 or type(res) ~= "table" then return res end
    local out = {}
    for k, v in pairs(res) do out[k] = v end
    out[p], out[w] = 0, 0
    return out
  end
end

-- replaces one member with our answer
local function evone(tbl, name, make)
  if type(tbl) ~= "table" then return false end
  local k, o = member(tbl, name)
  if k == nil or type(o) ~= "function" then return false end
  if EV_OURS[o] then return true end
  local ok, w = pcall(make, o)
  if not ok or type(w) ~= "function" then return false end
  if not pcall(function() tbl[k] = w end) then return false end
  local okr, got = pcall(function() return tbl[k] end)
  if not okr or got ~= w then return false end
  EV_OURS[o], EV_OURS[w] = true, true
  EV_ALL[#EV_ALL + 1] = name
  return true
end

-- the event the menus read while the flag holds
local function wrap_ev()
  if T.ev then return true end
  local L, P, X = rawget(_G, "LOOT"), rawget(_G, "PROGRESSION"), rawget(_G, "XPTOKENS")
  local n = 0
  local function got(v)
    if v then n = n + 1 end
  end
  got(evone(L, EV_L[1], evplain))
  got(evone(L, EV_L[2], evplain))
  got(evone(L, EV_B[1], evbytype))
  got(evone(L, EV_B[2], evbytype))
  got(evone(X, EV_S, evstates))
  got(evone(P, EV_E, evends))
  T.ev = (n >= 6) or nil
  evsay()
  return T.ev == true
end

-- says the status dvar is missing once
local function stsay()
  local v = dv(ST)
  if (v == nil or empty(v)) and said("p2stmiss") then log("tokens P2 st=missing") end
end

-- adds one activation to its category
local function grant(id)
  local m = MINS[id]
  if m == nil then return end
  local op = OP[id] == true
  if op then T.p = T.p + m * 60 else T.w = T.w + m * 60 end
  chwrite()
end

-- the countdown one tick
local function tick_chan()
  clock()
  local front, paused = flags()
  T.front, T.paused = front, paused
  psync()
  local ms = now_ms()
  local live = (not front) and (not paused) and (T.p > 0 or T.w > 0) and T.x ~= 1
  local hit = false
  if ms ~= nil then
    if T.base == nil or not live then
      T.base = ms
    else
      local d = ms - T.base
      T.base = ms
      if d > 0 then
        T.acc = T.acc + d
        local n = math.floor(T.acc / 1000)
        if n > 0 then
          T.acc = T.acc - n * 1000
          if T.p > 0 then T.p = math.max(0, T.p - n) end
          if T.w > 0 then T.w = math.max(0, T.w - n) end
          hit = true
        end
      end
    end
  end
  if hit or T.wpend then chwrite() end
  stsay()
end

-- hands one event to the game own root
local function fire(ev)
  local lui = rawget(_G, "LUI")
  local getroot = fn_of(lui, "GetRoot")
  if getroot == nil then return false end
  local okr, rootEl = pcall(getroot)
  if not okr or rootEl == nil then return false end
  local _, uir = member(lui, "UIRoot")
  local fe = (uir ~= nil) and fn_of(uir, "ProcessEvent") or nil
  if fe == nil then fe = fn_of(rootEl, "ProcessEvent") end
  if fe == nil then fe = fn_of(rootEl, "dispatchEventToRoot") end
  if fe == nil then return false end
  local okf = pcall(fe, rootEl, ev)
  return okf
end

-- the game own success steps
local function finish(p)
  T.pend = nil
  local X = rawget(_G, "XPTOKENS")
  local sets = rawget(_G, "SOUND_SETS")
  local cue = type(sets) == "table" and type(sets.popups) == "table" and sets.popups.tokenUseSuccess or nil
  local play = fn_of(rawget(_G, "Engine"), "PlaySound")
  if play ~= nil and cue ~= nil then pcall(play, cue) end
  local set = fn_of(X, "settokenuselocked")
  if set ~= nil then pcall(set, p.c, false) end
  local gt = fn_of(X, "gettoastdatafromachievementid")
  local notif = fn_of(rawget(_G, "NOTIFICATIONS"), "creategenericnotification")
  if gt ~= nil and notif ~= nil and p.id ~= nil then
    local okd, d = pcall(gt, p.id)
    if okd and type(d) == "table" and d.notificationRef ~= nil then
      pcall(notif, p.c, d.notificationRef, { body = d.duration })
    end
  end
end

-- runs the steps on the tick after the press
local function release()
  local p = T.pend
  if p == nil then return end
  if (S.tick or 0) <= p.at then return end
  finish(p)
end

-- the kind ids this vm gives its token achievement
local function token_kind()
  local set, ks, n = {}, {}, 0
  local ek = fn_of(rawget(_G, "Challenge"), "GetAEKindID")
  local h = rawget(_G, "xhash")
  local i = 1
  while ek ~= nil and i <= #KIND_NAMES do
    local name = KIND_NAMES[i]
    local forms = { name }
    if type(h) == "function" then
      local okh, hv = pcall(h, name)
      if okh and hv ~= nil then forms[2] = hv end
    end
    local j = 1
    while j <= #forms do
      local ok, v = pcall(ek, forms[j])
      if ok then
        v = tonumber(v)
        if v ~= nil and v > 0 and set[v] == nil then
          set[v] = name
          n = n + 1
          ks[n] = tostring(v)
        end
      end
      j = j + 1
    end
    i = i + 1
  end
  if n == 0 then
    set[AE_KIND] = "fallback"
    ks[1] = tostring(AE_KIND)
  end
  return set, table.concat(ks, ",")
end

-- the channel count for one activation id
local function had(aeid)
  local loot = AE_LOOT[aeid]
  local i = (loot ~= nil) and C_SLOT[loot] or nil
  if i == nil then return 0 end
  local c = cfill()
  if c == nil then return 0 end
  T.n[aeid] = c[i]
  return c[i]
end

local AE_OURS = setmetatable({}, { __mode = "k" })

-- answers the menu tiles with the local count
local function watch_count()
  if T.own then return true end
  local P = rawget(_G, "PROXY_LOOT")
  local k, o = member(P, "IsOwned")
  if k == nil or type(o) ~= "function" or AE_OURS[o] then return false end
  local w = function(c, id)
    local aeid = LOOT_AE[tonumber(id)]
    if aeid ~= nil then return had(aeid) end
    return o(c, id)
  end
  if not pcall(function() P[k] = w end) then return false end
  T.orig = o
  AE_OURS[o], AE_OURS[w] = true, true
  T.own = true
  return true
end

-- says one refusal per check per vm
local function refused(why, c, aeid, kd, kind)
  if not said("ae:" .. why) then return end
  log("tokens Q12 ae refused why=" .. why .. " kd=" .. clip(kd, 16) .. " kind=" .. tostring(kind)
    .. " aeid=" .. clip(aeid, 16) .. " c=" .. clip(c, 8))
end

-- wraps the native activation for the token kind
local function install()
  if T.armed then return true end
  local OC = rawget(_G, "OnlineChallenges")
  if type(OC) ~= "table" then return false end
  local k, o = member(OC, AE_ACT)
  if k == nil or type(o) ~= "function" then return false end
  if AE_OURS[o] then
    T.armed = true
    return true
  end
  token_kind()
  local w = function(c, aeid, kd, evid)
    local kinds, kvals = token_kind()
    local kdv = tonumber(kd)
    if kdv ~= nil and kinds[kdv] ~= nil then
      local id = tonumber(aeid)
      if id == nil or AE_LOOT[id] == nil then
        refused("notoken", c, aeid, kd, kvals)
      else
        if T.x == 1 then
          refused("perm", c, aeid, kd, kvals)
          return true
        end
        local n = had(id)
        if n > 0 and fire({ name = AE_EV, controller = c, kind = kdv, success = true, id = id }) then
          T.n[id] = n - 1
          cspend(id)
          T.used = T.used + 1
          T.pend = { c = c, at = S.tick or 0, id = id }
          grant(id)
          return true
        end
        refused(n > 0 and "fire" or "empty", c, aeid, kd, kvals)
      end
    else
      refused("kind", c, aeid, kd, kvals)
    end
    return o(c, aeid, kd, evid)
  end
  local okset = pcall(function() OC[k] = w end)
  if not okset then
    if said("ae:set") then
      log("tokens Q12 activation cannot be replaced in this vm")
    end
    return false
  end
  AE_OURS[o] = true
  AE_OURS[w] = true
  T.armed = true
  return true
end

local function step()
  if not T.own then pcall(watch_count) end
  if not T.armed then pcall(install) end
  if not T.p3 then pcall(wrap_end) end
  if not T.ev then pcall(wrap_ev) end
  pcall(release)
  pcall(tick_chan)
end

S.hooks.tokens = step
S.probes.tokens = function() return type(S.hooks.tokens) == "function" end

-- adopts the seconds and counts this vm starts with
local p0, w0, n0, c0, x0 = chread()
if p0 ~= nil then
  T.p, T.w, T.sn = p0, w0, n0 or 0
end
if x0 ~= nil then T.x = x0 end
T.xl = T.x
if c0 ~= nil then
  T.c, T.csrc = c0, "chan"
else
  cfill()
end
clock()
pcall(wrap_end)
pcall(wrap_ev)

local dp = rawget(_G, "DebugPrint") or rawget(_G, "print")
if type(dp) == "function" then pcall(dp, "progression_tuning: part tokens armed") end

if A.ready ~= nil then A.ready() end
