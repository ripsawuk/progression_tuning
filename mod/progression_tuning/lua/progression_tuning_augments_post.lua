local PART = "augments"

-- the augment list the tiers live in
local K_STORE = "d847872560dcd8e4"
-- the pass a menu refresh runs
local K_REFRESH = "52e47d640bf4ca01"
-- the dev bool the tier code reads
local DEV = "d428ffe65b5694d6"
-- the two switches that want a full house
local DV_ONE, DV_TWO = "zm_unlock_augments", "zm_unlock_all"

local VERSION = "v1"
local PREFIX = "progression_tuning: "
local TICK_MS = 250

local S = rawget(_G, "ProgressionTuning")
if type(S) ~= "table" then
  S = { parts = {}, hooks = {}, probes = {}, api = {}, g11 = {}, scope = {} }
  rawset(_G, "ProgressionTuning", S)
end
if S.parts[PART] == true then return end
S.parts[PART] = true

local G = { said = false, devseen = false, dev = nil, table = nil, key = nil, wrap = nil, ticks = 0 }
S.aug = G

-- says a thing once
local function dp(msg)
  local f = rawget(_G, "DebugPrint")
  if type(f) == "function" then pcall(f, PREFIX .. msg) end
end

-- the engine hash of a name
local function xh(name)
  local f = rawget(_G, "xhash")
  if type(f) ~= "function" then return nil end
  local ok, v = pcall(f, name)
  if ok then return v end
  return nil
end

-- the engine hash of a dvar name
local function xhd(name)
  local f = rawget(_G, "xhashdvar")
  if type(f) ~= "function" then return nil end
  local ok, v = pcall(f, name)
  if ok then return v end
  return nil
end

-- the hash a key carries
local function hex_of(k)
  local ok, s = pcall(tostring, k)
  if not ok or type(s) ~= "string" then return nil end
  local h = string.match(s, "#x(%x+)")
  if h == nil then return nil end
  return string.sub(string.lower(h), -16)
end

-- a member by the hash it carries
local function key_hex(tbl, hex)
  local ok, k = pcall(next, tbl)
  while ok and k ~= nil do
    if hex_of(k) == hex then return k end
    local got
    got, k = pcall(next, tbl, k)
    if not got then return nil end
  end
  return nil
end

-- a member by its engine hash
local function named(tbl, name, want)
  local k = xh(name)
  if k == nil or type(tbl) ~= "table" then return nil, nil end
  local ok, v = pcall(function() return tbl[k] end)
  if ok and type(v) == want then return k, v end
  return nil, nil
end

-- a function by its engine hash
local function fn_by(tbl, name)
  return named(tbl, name, "function")
end

-- a table by its engine hash
local function tbl_by(tbl, name)
  return named(tbl, name, "table")
end

-- one switch value by its dvar name
local function dv(name)
  local k = xhd(name)
  local _, f = fn_by(rawget(_G, "Dvar"), "GetDvarString")
  if k == nil or f == nil then return nil end
  local ok, v = pcall(f, k)
  if not ok or v == nil then return nil end
  return tostring(v)
end

-- a switch value as the line carries it
local function word(v)
  if v == nil then return "?" end
  if v == "" then return "-" end
  return v
end

-- the dev bool as the line carries it
local function devword()
  if G.devseen ~= true then return "unread" end
  if G.dev == true then return "true" end
  return "false"
end

-- keeps the dev bool the tier code asks for
local function spy_on()
  local D = rawget(_G, "Dvar")
  local k, orig = fn_by(D, "GetDvarBool")
  if k == nil then return nil, nil end
  local wrap = function(key, ...)
    local v = orig(key, ...)
    if G.devseen ~= true and hex_of(key) == DEV then
      G.devseen, G.dev = true, (v == true)
    end
    return v
  end
  if not pcall(function() D[k] = wrap end) then return nil, nil end
  return k, orig
end

-- puts the bool reader back
local function spy_off(k, orig)
  if k == nil then return end
  local D = rawget(_G, "Dvar")
  pcall(function() D[k] = orig end)
end

-- the game own tier pass over every row it cached
local function retier(c)
  local Z = rawget(_G, "ZMAUGMENT")
  if type(Z) ~= "table" then return 0 end
  local _, tier = fn_by(Z, "cacheaugmenttierdata")
  if tier == nil then return 0 end
  local _, cache = tbl_by(Z, "augmentresearchchallenges")
  if cache == nil then return 0 end
  local n = 0
  for loot, ch in pairs(cache) do
    if type(ch) == "table" and pcall(tier, c, ch, loot) then n = n + 1 end
  end
  return n
end

-- one refresh ends on the game own numbers
local function pass(c)
  if c == nil then c = 0 end
  local one, two = dv(DV_ONE), dv(DV_TWO)
  if one == nil or two == nil then return end
  local on = (one == "1") or (two == "1")
  local n = 0
  if not on then
    local k, orig = spy_on()
    local ok = pcall(function() n = retier(c) end)
    spy_off(k, orig)
    if not ok then n = 0 end
  end
  if G.said == true then return end
  if not on and n < 1 then return end
  G.said = true
  dp("augments armed " .. VERSION .. " unlock=" .. word(one) .. " all=" .. word(two)
    .. " devcomplete=" .. devword())
end

-- wraps the refresh once a table holds it
local function install()
  local Z = rawget(_G, "ZMAUGMENT")
  if type(Z) ~= "table" then return false end
  if G.table == Z and G.wrap ~= nil then
    local ok, cur = pcall(function() return Z[G.key] end)
    if ok and cur == G.wrap then return true end
  end
  if key_hex(Z, K_STORE) == nil then return false end
  local kr = key_hex(Z, K_REFRESH)
  if kr == nil then return false end
  local okb, below = pcall(function() return Z[kr] end)
  if not okb or type(below) ~= "function" or below == G.wrap then return false end
  local wrap = function(c, ...)
    local r = below(c, ...)
    pcall(pass, c)
    return r
  end
  if not pcall(function() Z[kr] = wrap end) then return false end
  G.table, G.key, G.wrap = Z, kr, wrap
  return true
end

local timerEl = nil

-- a waiting element on the ui root
local function make_el()
  local lui = rawget(_G, "LUI")
  local _, getroot = fn_by(lui, "GetRoot")
  if getroot == nil then return nil end
  local okr, rootEl = pcall(getroot)
  if not okr or rootEl == nil then return nil end
  local el = nil
  local _, uie = tbl_by(lui, "UIElement")
  local mk = nil
  if uie ~= nil then mk = select(2, fn_by(uie, "new")) end
  if mk ~= nil then
    local okn, v = pcall(mk)
    if okn then el = v end
  end
  if el == nil then return nil end
  if not pcall(function() return rootEl:addElement(el) end) then return nil end
  return el
end

local tick

-- one wait on the element it was handed
local function again()
  local el = timerEl
  if el == nil then return false end
  local ok, parent = pcall(function() return el:getParent() end)
  if ok and parent == nil then
    timerEl = nil
    return false
  end
  if not pcall(function() el:Wait(TICK_MS).onComplete = tick end) then
    timerEl = nil
    return false
  end
  return true
end

-- the retry timer one step at a time
local function start()
  if timerEl == nil then timerEl = make_el() end
  return again()
end

-- one timer step that arms what is missing
tick = function()
  G.ticks = G.ticks + 1
  pcall(install)
  if not again() then pcall(start) end
end

S.probes.augments = function() return G.wrap ~= nil end

pcall(install)
pcall(start)
local api = S.api
local r = type(api) == "table" and api.ready or nil
if type(r) == "function" then pcall(r) end
