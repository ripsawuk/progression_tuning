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
local function gstr(...) return A.gstr(...) end
local function dv(...) return A.dv(...) end
local function empty(...) return A.empty(...) end
local function fn_of(...) return A.fn_of(...) end
local function member(...) return A.member(...) end
local function said(...) return A.said(...) end
local function vm_mark(...) return A.vm_mark(...) end

-- the eight shipped token ids weapon then operator
local TOK_IDS = { 84672, 84673, 84674, 84675, 84677, 84678, 84679, 84680 }
-- the one debug switch that stands every lock down
local UNLOCK = { "zm_unlock_all" }
-- the published challenge text a header and chunks
local CH_VER = "zm_ch_ver"
local CH_PART = "zm_ch_s"
local CH_MAX = 96
local FIRST_TICK, RETRY_TICKS, LAST_TICK = 40, 40, 240
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
  T = { done = false, n = {}, used = 0, armed = false, x = 0 }
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
local ST_MS = 30000
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
  if not said("p2clock") then return end
  log("tokens P2 clock ip=" .. (CLK.pz and 1 or 0) .. " inf=" .. (CLK.fe and 1 or 0)
    .. " ms=" .. (CLK.ms and 1 or 0))
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

-- the channel string as it stands
local function chraw()
  local v = dv(CH)
  if v == nil or empty(v) then return "missing" end
  return v
end

-- says the channel string when it moved
local function chsayraw()
  local v = chraw()
  if v == T.rawl then return end
  T.rawl = v
  log("tokens P2 raw=" .. v)
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
  chsayraw()
  if not hit and said("p2chmiss") then log("tokens ch missing") end
  return hit
end

-- says the channel when its state moved
local function chsay(force)
  local sig = math.floor(T.p / 60) .. "," .. math.floor(T.w / 60) .. ","
    .. tostring(T.p == 0) .. tostring(T.w == 0) .. ","
    .. tostring(T.paused) .. tostring(T.front)
  if force ~= true and sig == T.sig then return end
  T.sig = sig
  log("tokens P2 ch=" .. tostring(T.p) .. "/" .. tostring(T.w) .. " n=" .. tostring(T.sn)
    .. " paused=" .. (T.paused and 1 or 0) .. " front=" .. (T.front and 1 or 0))
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

-- says the counts when they moved
local function csay(force)
  local sig = "nil"
  if T.c ~= nil then sig = table.concat(T.c, ",") end
  if force ~= true and sig == T.csig then return end
  T.csig = sig
  log("tokens P4 c=" .. sig .. " src=" .. tostring(T.csrc or "seed"))
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
  if T.c ~= nil then
    T.csrc = "seed"
    csay()
  end
  return T.c
end

-- one count off its slot
local function cspend(aeid)
  local loot = AE_LOOT[aeid]
  local i = (loot ~= nil) and C_SLOT[loot] or nil
  if i == nil or T.c == nil then return end
  if T.c[i] > 0 then T.c[i] = T.c[i] - 1 end
  csay()
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
  csay(true)
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
  if c ~= nil then
    T.c, T.csrc = c, "chan"
    csay()
  end
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

-- says the answer when the seconds moved
local function say_end(p, w, now, ans)
  if p == T.p3p and w == T.p3w then return end
  T.p3p, T.p3w = p, w
  log("tokens P3 end p=" .. tostring(p) .. " w=" .. tostring(w) .. " now=" .. tostring(now)
    .. " ans=" .. tostring(ans))
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
    local ans = 0
    if now ~= nil then
      if p > 0 and wants(keys, DX_P) then
        if type(res) ~= "table" then res = {} end
        res[DX_P] = math.floor((now + p) * 1000)
        ans = 1
      end
      if sec > 0 and wants(keys, DX_W) then
        if type(res) ~= "table" then res = {} end
        res[DX_W] = math.floor((now + sec) * 1000)
        ans = 1
      end
    end
    say_end(p, sec, now, ans)
    return res
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

-- the one loc key the token menu shows
local LOC_KEY = "4849F2616A844C09"
local LOC_NAME = "hash_4849f2616a844c09"
local LOC_BYTES = string.char(0x09, 0x4C, 0x84, 0x6A, 0x61, 0xF2, 0x49, 0x48)
local LOC_OLD = "Active XP Tokens count down in real-time"
local LOC_NEW = "Active XP Tokens count down with in-game time"
local LOC_LOW = string.lower(LOC_OLD)
local LOC_OURS = setmetatable({}, { __mode = "k" })

-- says the override once with its count
local function locsay()
  T.lochit = (T.lochit or 0) + 1
  if not said("loctxt") then return end
  log("tokens txt key=" .. LOC_NAME .. " hit=" .. T.lochit)
end

-- the key in the shapes the menu may pass
local function loc_key(v)
  if type(v) == "string" then
    if string.lower(v) == LOC_NAME or v == LOC_BYTES then return true end
    return false
  end
  local ok, s = pcall(tostring, v)
  if not ok or type(s) ~= "string" then return false end
  s = string.gsub(string.upper(s), "[^0-9A-F]", "")
  if string.len(s) == 17 and string.sub(s, 1, 1) == "3" then s = string.sub(s, 2) end
  return (string.gsub(s, "^0+", "")) == LOC_KEY
end

-- answers the token footer with our own text
local function wrap_loc()
  if T.loc then return true end
  local E = rawget(_G, "Engine")
  if type(E) ~= "table" then return false end
  local k, o = member(E, "Localize")
  if k == nil or type(o) ~= "function" then return false end
  if LOC_OURS[o] then
    T.loc = true
    return true
  end
  local w = function(s, ...)
    if loc_key(s) then
      locsay()
      return LOC_NEW
    end
    local res = o(s, ...)
    if type(res) == "string" and string.lower(res) == LOC_LOW then
      locsay()
      return LOC_NEW
    end
    return res
  end
  if not pcall(function() E[k] = w end) then return false end
  local okr, got = pcall(function() return E[k] end)
  if not okr or got ~= w then return false end
  LOC_OURS[o] = true
  LOC_OURS[w] = true
  T.loc = true
  return true
end

-- the status without its heartbeat
local function stkey(v)
  return (string.gsub(v, "h=[^;]*;?", ""))
end

-- says the gsc status when it moved
local function stsay(front)
  local v = dv(ST)
  if v == nil or empty(v) then
    if said("p2stmiss") then log("tokens P2 st=missing") end
    return
  end
  local k = stkey(v)
  local ms, t = now_ms(), S.tick or 0
  local due = false
  if front ~= true then
    if ms ~= nil then
      due = T.stms ~= nil and (ms - T.stms) >= ST_MS
    else
      due = T.sttk ~= nil and (t - T.sttk) >= 120
    end
  end
  if k == T.stk and not due then return end
  T.stk = k
  if ms ~= nil then T.stms = ms else T.sttk = t end
  log("tokens P2 st=" .. v)
end

-- adds one activation to its category
local function grant(id)
  local m = MINS[id]
  if m == nil then return end
  local op = OP[id] == true
  local held = op and T.p or T.w
  if op then T.p = T.p + m * 60 else T.w = T.w + m * 60 end
  if held > 0 then
    log("tokens P2 stack own=" .. tostring(AE_LOOT[id]) .. " ch=" .. tostring(T.p) .. "/" .. tostring(T.w))
  end
  chwrite()
  chsay(true)
end

-- the countdown one tick
local function tick_chan()
  clock()
  local front, paused = flags()
  local moved = (front ~= T.front) or (paused ~= T.paused)
  T.front, T.paused = front, paused
  if psync() then moved = true end
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
          moved = true
        end
      end
    end
  end
  if hit or T.wpend then chwrite() end
  if moved then chsay() end
  stsay(front)
end

-- one answer for one table and id
local function ownof(f, id)
  if type(f) ~= "function" then return "nil" end
  local ok, v = pcall(f, 0, id)
  if not ok then return "err" end
  if v == true then return "1" end
  if v == false then return "0" end
  return clip(v, 8)
end

-- the switch the door answers to
local function unlock()
  local i = 1
  while i <= #UNLOCK do
    local v = dv(UNLOCK[i])
    if v ~= nil and v ~= "" and v ~= "0" then return UNLOCK[i] end
    i = i + 1
  end
  return nil
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
  local snd = (play ~= nil and cue ~= nil and pcall(play, cue)) and 1 or 0
  local set = fn_of(X, "settokenuselocked")
  if set ~= nil then pcall(set, p.c, false) end
  local toast = 0
  local gt = fn_of(X, "gettoastdatafromachievementid")
  local notif = fn_of(rawget(_G, "NOTIFICATIONS"), "creategenericnotification")
  if gt ~= nil and notif ~= nil and p.id ~= nil then
    local okd, d = pcall(gt, p.id)
    if okd and type(d) == "table" and d.notificationRef ~= nil then
      toast = pcall(notif, p.c, d.notificationRef, { body = d.duration }) and 1 or 0
    end
  end
  local loot = p.id ~= nil and AE_LOOT[p.id] or nil
  log("tokens Q12 done used=" .. tostring(T.used) .. " snd=" .. snd .. " toast=" .. toast
    .. " own=" .. tostring(loot) .. "=" .. tostring(T.n[p.id]))
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
  local set, ks, ss, n = {}, {}, {}, 0
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
          ss[n] = name
        end
      end
      j = j + 1
    end
    i = i + 1
  end
  if n == 0 then
    set[AE_KIND] = "fallback"
    ks[1] = tostring(AE_KIND)
    ss[1] = "fallback"
  end
  local kvals, ksrc = table.concat(ks, ","), table.concat(ss, ",")
  local line = kvals .. " src=" .. ksrc
  if T.kline ~= line then
    T.kline = line
    log("tokens Q12 kind=" .. line)
  end
  return set, kvals
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

-- the published locked ids and their count
local function chset()
  local ver = gstr(CH_VER)
  if ver == nil or empty(ver) then return nil, "nover" end
  local n = tonumber(string.match(ver, "^%d+:(%d+)$"))
  if n == nil or n < 1 or n > CH_MAX then return nil, "ver=" .. clip(ver, 20) end
  local parts, i = {}, 0
  while i < n do
    local p = gstr(CH_PART .. i)
    if p == nil or empty(p) then return nil, "chunk" .. i end
    parts[i + 1] = p
    i = i + 1
  end
  local s = table.concat(parts)
  local set, nl = {}, 0
  for ln in string.gmatch(s, "[^\n]+") do
    if string.sub(ln, 1, 1) == "l" then
      local id = tonumber(string.sub(ln, 2))
      if id ~= nil and set[id] == nil then
        set[id] = true
        nl = nl + 1
      end
    end
  end
  return { set = set, n = nl, ver = ver, bytes = #s }, nil
end

-- the one diagnostic line
local function report()
  local loot = fn_of(rawget(_G, "Loot"), "IsOwned")
  local prox = fn_of(rawget(_G, "PROXY_LOOT"), "IsOwned")
  local cells, i = {}, 1
  while i <= #TOK_IDS do
    local id = TOK_IDS[i]
    cells[i] = id .. "=" .. ownof(loot, id) .. "/" .. ownof(prox, id)
    i = i + 1
  end
  local door = unlock()
  local ch, why = chset()
  local out = "tokens Q4b own=" .. table.concat(cells, ",")
  if door ~= nil then
    out = out .. " Q7 gate=" .. door
  elseif ch == nil then
    out = out .. " Q7 lset=? why=" .. why
  else
    local hits, nh = {}, 0
    i = 1
    while i <= #TOK_IDS do
      if ch.set[TOK_IDS[i]] == true then
        nh = nh + 1
        hits[nh] = TOK_IDS[i]
      end
      i = i + 1
    end
    out = out .. " Q7 lset=" .. ch.n .. " hits=" .. (nh > 0 and table.concat(hits, ",") or "none")
      .. " ver=" .. clip(ch.ver, 20) .. " bytes=" .. ch.bytes
  end
  out = out .. " Q12 act=" .. (T.armed and "1" or "0") .. "/" .. tostring(T.used)
  return out .. " " .. vm_mark(), ch ~= nil
end

local function step()
  if not T.own then pcall(watch_count) end
  if not T.armed then pcall(install) end
  if not T.p3 then pcall(wrap_end) end
  if not T.ev then pcall(wrap_ev) end
  if not T.loc then pcall(wrap_loc) end
  pcall(release)
  pcall(tick_chan)
  if T.done then return end
  local t = S.tick or 0
  if t < FIRST_TICK then return end
  if t > FIRST_TICK and t < LAST_TICK and (t % RETRY_TICKS) ~= 0 then return end
  local okc, out, okp = pcall(report)
  if not okc then
    T.done = true
    log("tokens Q4b own=? why=" .. clip(out, 60))
    return
  end
  if okp ~= true and t < LAST_TICK then return end
  T.done = true
  log(out)
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
csay()
clock()
pcall(wrap_end)
pcall(wrap_ev)
pcall(wrap_loc)

local dp = rawget(_G, "DebugPrint") or rawget(_G, "print")
if type(dp) == "function" then pcall(dp, "progression_tuning: part tokens armed") end

chsayraw()

if A.ready ~= nil then A.ready() end
