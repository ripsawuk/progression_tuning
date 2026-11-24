local PART = "augments"

-- the augment list the tiers live in
local K_STORE = "d847872560dcd8e4"
-- the pass a menu refresh runs
local K_REFRESH = "52e47d640bf4ca01"
-- the nine slot publisher
local K_SLOTS = "bd666394faa4374c"
-- the send a press goes through
local K_SEND = "e636d3bf423fd414"
-- the progress read the menu asks
local K_PROG = "31eee6570ef4bb8b"
-- the gamemode field the gate reads
local K_BUNDLE = "053308f95ad2e716"
-- the cache the count pass fills
local K_CACHE = "8ac6d3ec3791c80f"
-- the builder that owns the cache
local K_BUILD = "fbc74f64b0a3b5af"
-- the count key function by its hash
local K_UKEY = "e42ea32389c5bbae"
-- the names the count is asked under
local U_NAMES = { "zm_augments_total_unlock_count", "zm_augments_unlock_count",
  "#zm_augments_total_unlock_count", "#zm_augments_unlock_count" }
-- the native list repaint
local K_REPAINT = "236a81b14f8791e4"
-- the dev bool the tier code reads
local DEV = "d428ffe65b5694d6"
-- the two switches that want a full house
local DV_ONE, DV_TWO = "zm_unlock_augments", "zm_unlock_all"
-- the research channel a press writes
local CH = "pt_research_ch"
-- the activation rows and the start event
local ACT_A, ACT_B = 53979, 47576
local START_EVENT, START_KEY = 846, 74
local SLOTS = 9
-- a weight the fill guard computes to dark
local DARK = 0.001

local VERSION = "v11"
local PREFIX = "progression_tuning: "
local TICK_MS = 250
local PASS_TICKS = 8
local R2_PASSES = 40
local RTRIES = 4

local S = rawget(_G, "ProgressionTuning")
if type(S) ~= "table" then
  S = { parts = {}, hooks = {}, probes = {}, api = {}, g11 = {}, scope = {} }
  rawset(_G, "ProgressionTuning", S)
end
if S.parts[PART] == true then return end
S.parts[PART] = true

local G = { said = false, ownSaid = false, devseen = false, dev = nil, ticks = 0, c = 0, dirty = false,
  active = 0, sat = 0, on = nil, ix = nil, tier = {}, rows = 0, owned = 0, ev = nil, key = nil,
  cards = {}, restored = false, lkOn = false, lkMiss = false, ukey = nil, gkey = nil,
  gfed = false, ukeys = nil, utot = nil, uob = nil, gval = nil, passes = 0, rtry = 0,
  r1Said = false, r2Said = false }
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
  if type(tbl) ~= "table" then return nil end
  local ok, k = pcall(next, tbl)
  while ok and k ~= nil do
    if hex_of(k) == hex then return k end
    local got
    got, k = pcall(next, tbl, k)
    if not got then return nil end
  end
  return nil
end

-- a field through the table it sits on
local function field(tbl, k)
  if tbl == nil or k == nil then return nil end
  local ok, v = pcall(function() return tbl[k] end)
  if ok then return v end
  return nil
end

-- a field by plain name then by hash
local function hfield(tbl, name)
  local v = field(tbl, name)
  if v ~= nil then return v end
  return field(tbl, xh(name))
end

-- a member and the key it sits under
local function slot_of(tbl, name)
  if type(tbl) ~= "table" then return nil, nil end
  local ok, v = pcall(rawget, tbl, name)
  if ok and v ~= nil then return name, v end
  local h = xh(name)
  if h ~= nil then
    local ok2, v2 = pcall(rawget, tbl, h)
    if ok2 and v2 ~= nil then return h, v2 end
  end
  return nil, nil
end

-- a function member by name
local function fn_of(tbl, name)
  local _, v = slot_of(tbl, name)
  if type(v) == "function" then return v end
  return nil
end

-- a switch value by its dvar name
local function dv(name)
  local key = xhd(name)
  local _, f = slot_of(rawget(_G, "Dvar"), "GetDvarString")
  if type(f) ~= "function" or key == nil then return nil end
  local ok, v = pcall(f, key)
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
  local k, orig = slot_of(D, "GetDvarBool")
  if k == nil or type(orig) ~= "function" then return nil, nil end
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

-- a field written under the key it lives in
local function put(tbl, name, v)
  if type(tbl) ~= "table" then return false end
  local h = xh(name)
  local hp, pp = false, false
  if h ~= nil then
    local ok, rv = pcall(rawget, tbl, h)
    hp = ok and rv ~= nil
  end
  do
    local ok, rv = pcall(rawget, tbl, name)
    pp = ok and rv ~= nil
  end
  if hp then return pcall(function() tbl[h] = v end) end
  if pp then return pcall(function() tbl[name] = v end) end
  local a = pcall(function() tbl[name] = v end)
  if h == nil then return a end
  pcall(function() tbl[h] = v end)
  return a
end

-- the cached ladder rows by equipment
local function cache_of(Z)
  local _, v = slot_of(Z, "augmentresearchchallenges")
  if type(v) == "table" then return v end
  local found = nil
  pcall(function()
    local k, val = next(Z)
    while k ~= nil and found == nil do
      if type(val) == "table" then
        local _, one = next(val)
        if type(one) == "table" and type(hfield(one, "amount")) == "string" then found = val end
      end
      k, val = next(Z, k)
    end
  end)
  return found
end

-- the ref map by its first number
local function map_of(Z)
  local _, v = slot_of(Z, "lootid_to_ref")
  if type(v) == "table" then return v end
  local found = nil
  pcall(function()
    local k, val = next(Z)
    while k ~= nil and found == nil do
      if type(val) == "table" then
        local k2, v2 = next(val)
        if type(k2) == "number" and type(v2) == "string" then found = val end
      end
      k, val = next(Z, k)
    end
  end)
  return found
end

-- the ref one cached key names
local function ref_of(map, k)
  if type(map) ~= "table" then return nil end
  local n = tonumber(k)
  local ref = nil
  if n ~= nil then ref = field(map, n) end
  if type(ref) ~= "string" then ref = field(map, k) end
  if type(ref) ~= "string" and n ~= nil then ref = field(map, tostring(n)) end
  if type(ref) ~= "string" then return nil end
  return ref
end

-- the rungs one amount ladder carries
local function rung_of(ch)
  local amount = hfield(ch, "amount")
  if type(amount) ~= "string" then return 0 end
  local n = 0
  for _ in string.gmatch(amount, "[^|]+") do n = n + 1 end
  return n
end

-- the progress the row and its carryover hold
local function held(c, ch)
  local get = fn_of(rawget(_G, "Challenge"), "getchallengeprogress")
  if get == nil then return 0 end
  local p = 0
  local a = tonumber(hfield(ch, "achievementID"))
  if a ~= nil then
    local ok, v = pcall(get, c, a)
    if ok then p = p + (tonumber(v) or 0) end
  end
  local b = tonumber(hfield(ch, "carryoverAchievementID"))
  if b ~= nil then
    local ok, v = pcall(get, c, b)
    if ok then p = p + (tonumber(v) or 0) end
  end
  return p
end

-- the ladder steps one row reaches
local function steps(c, ch)
  local amount = hfield(ch, "amount")
  if type(amount) ~= "string" then return 0, 0 end
  local p = held(c, ch)
  local n = 0
  for tok in string.gmatch(amount, "[^|]+") do
    local step = tonumber(tok)
    if step == nil or p < step then break end
    n = n + 1
  end
  return n, p
end

-- the first rung of a ladder
local function first_of(amount)
  if type(amount) ~= "string" then return 0 end
  return tonumber(string.match(amount, "^[^|]+")) or 0
end

-- the share of the next rung already earned
local function share(amount, t, p)
  if type(amount) ~= "string" then return DARK end
  local i, prev, nxt = 0, 0, nil
  for tok in string.gmatch(amount, "[^|]+") do
    i = i + 1
    local v = tonumber(tok)
    if i <= t then
      if v ~= nil then prev = v end
    elseif i == t + 1 then
      nxt = v
      break
    end
  end
  if nxt == nil or nxt <= prev then return DARK end
  local f = (p - prev) / (nxt - prev)
  if f < DARK then f = DARK end
  if f > 1 then f = 1 end
  return f
end

-- the game own tier pass over every row it cached
local function retier(c, cache)
  local Z = rawget(_G, "ZMAUGMENT")
  local _, tier = slot_of(Z, "cacheaugmenttierdata")
  if type(tier) ~= "function" then return 0 end
  local n = 0
  for loot, ch in pairs(cache) do
    if type(ch) == "table" and pcall(tier, c, ch, loot) then n = n + 1 end
  end
  return n
end

-- numeric twins for string keyed rows
local function alias(cache)
  local out = {}
  for k, ch in pairs(cache) do
    if type(k) == "string" then
      local n = tonumber(k)
      if n ~= nil and field(cache, n) == nil then out[#out + 1] = { n, ch } end
    end
  end
  for i = 1, #out do cache[out[i][1]] = out[i][2] end
  return #out
end

-- how the cached rows are keyed
local function kindword(cache)
  local kind = "none"
  for k in pairs(cache) do
    if type(k) == "string" then return "string" end
    kind = "number"
  end
  return kind
end

-- the ticks the owned count and the node shares
local function ticks(c, store, cache, map, quiet)
  local owned, seen, rows = 0, {}, 0
  local tiers, items, done = {}, {}, {}
  for k, ch in pairs(cache) do
    if type(ch) == "table" and seen[ch] == nil then
      seen[ch] = true
      local ref = ref_of(map, k)
      local list = field(store, ref)
      if type(list) == "table" then
        rows = rows + 1
        local amount = hfield(ch, "amount")
        local rungs = rung_of(ch)
        local t, p = steps(c, ch)
        done[ref] = rungs > 0 and t >= rungs
        if quiet ~= true and G.lad == nil then
          G.lad = { ref = ref, rungs = rungs, first = first_of(amount), p = p }
        end
        if t > #list then t = #list end
        tiers[ref] = t
        for i = 1, #list do
          local e = list[i]
          if type(e) == "table" then
            local want = i <= t
            if quiet ~= true then
              if hfield(e, "IsUnlocked") ~= want then put(e, "IsUnlocked", want) end
              local v = DARK
              if want then v = 1 elseif i == t + 1 then v = share(amount, t, p) end
              if hfield(e, "progress") ~= v then put(e, "progress", v) end
            end
            if want then owned = owned + 1 end
            local loot = tonumber(hfield(e, "lootid"))
            if loot ~= nil then items[math.floor(loot)] = { ref = ref, i = i } end
          end
        end
      end
    end
  end
  return owned, tiers, rows, items, done
end

-- the vm this part runs in
local front

-- the switch state the lock rule reads
local hon

-- writes the research flag the game reads
local function flag(store, done)
  for ref, ok in pairs(done) do
    local list = field(store, ref)
    if type(list) == "table" then put(list, "isResearchComplete", ok == true) end
  end
end

-- clears one item second minor through the game
local function clearone(c, Z, ref, list)
  local get = fn_of(Z, "getcustomizationplayerdata")
  local refr = fn_of(Z, "refreshequippedaugmentdata")
  local slot = hfield(hfield(Z, "slot"), "bonus_minor")
  local et = hfield(list[1], "equipmenttype")
  if get == nil or refr == nil or type(slot) ~= "number" or type(et) ~= "number" then return false end
  local okg, pd = pcall(get, c, et, ref)
  if not okg or type(pd) ~= "table" then return false end
  local bm = hfield(pd, "bonusMinorAugment")
  local bget, bset = hfield(bm, "get"), hfield(bm, "set")
  if type(bget) ~= "function" or type(bset) ~= "function" then return false end
  local okv, v = pcall(bget, bm)
  if not okv or tonumber(v) == nil or tonumber(v) == 0 then return false end
  if not pcall(bset, bm, 0) then return false end
  pcall(refr, c, slot, 0)
  dp("augments bonus minor cleared ref=" .. ref)
  return true
end

-- clears every unfinished item second minor
local function clearall(c, Z, store, done)
  for ref, ok in pairs(done) do
    if ok ~= true then
      local list = field(store, ref)
      if type(list) == "table" then pcall(clearone, c, Z, ref, list) end
    end
  end
end

-- the keys this vm keeps its members under
local K = {}

-- a key filled once a table holds it
local function kfill(tbl, hex, name)
  local v = K[name]
  if v ~= nil then return v end
  v = key_hex(tbl, hex)
  if v ~= nil then K[name] = v end
  return v
end

-- a value as the line carries it
local function nn(v)
  if v == nil then return "nil" end
  return tostring(v)
end

-- the field the gate reads on the gamemode bundle
local function bundleval(b)
  if type(b) ~= "table" then return nil end
  local k = key_hex(b, K_BUNDLE)
  if k ~= nil then return field(b, k) end
  local h = xh(K_BUNDLE)
  if h == nil then return nil end
  return field(b, h)
end

-- the two keys and the bundle field once
local function r2say()
  if G.r2Said == true then return end
  local fld = nil
  local fb = fn_of(rawget(_G, "Game"), "getactivegamemodescriptbundle")
  if fb ~= nil then
    local ok, b = pcall(fb)
    if ok then fld = bundleval(b) end
  end
  if fld == nil and (G.passes or 0) < R2_PASSES then return end
  G.r2Said = true
  dp("augprobe R2 total=" .. nn(G.utot) .. " ob=" .. nn(G.uob) .. " bundle=" .. nn(fld))
end

-- the count key function the engine hands out
local function ufn()
  local C = rawget(_G, "Challenge")
  local f = fn_of(C, "getaeuserstatekey")
  if f ~= nil then return f end
  local k = key_hex(C, K_UKEY)
  if k == nil then return nil end
  local v = field(C, k)
  if type(v) == "function" then return v end
  return nil
end

-- one user state key from its name
local function ukeyof(name)
  local f = ufn()
  if f == nil then return nil end
  local h = xh(name)
  local ok, v = false, nil
  if h ~= nil then ok, v = pcall(f, h) end
  if not ok or v == nil then ok, v = pcall(f, name) end
  if not ok or v == nil then return nil end
  return v
end

-- the count the native gate asks for
local function uanswer(ctx)
  local c = type(ctx) == "table" and ctx.c or nil
  if c == nil then c = G.c end
  if type(ctx) == "table" and ctx.key ~= nil then G.gkey = ctx.key end
  if hon() ~= false then return nil end
  local Z = rawget(_G, "ZMAUGMENT")
  if type(Z) ~= "table" then return nil end
  local store, cache = field(Z, key_hex(Z, K_STORE)), cache_of(Z)
  if type(store) ~= "table" or type(cache) ~= "table" then return nil end
  local n = ticks(c, store, cache, map_of(Z), true)
  if type(n) == "number" then
    G.gval, G.gfed = n, true
  end
  return n
end

-- registers every key the count is asked under
local function ureg()
  if (G.ukeys or 0) > 0 then return G.ukey end
  local U = S.userstate
  if type(U) ~= "table" then
    U = { answer = {} }
    S.userstate = U
  end
  if type(U.answer) ~= "table" then U.answer = {} end
  local n = 0
  for i = 1, #U_NAMES do
    local key = ukeyof(U_NAMES[i])
    if key ~= nil then
      U.answer[key] = uanswer
      n = n + 1
      if i == 1 and G.utot == nil then G.utot = key end
      if i == 2 and G.uob == nil then G.uob = key end
      if G.ukey == nil then G.ukey = key end
    end
  end
  G.ukeys = n
  return G.ukey
end

-- the quick revive gate field
local function qrword()
  local Z = rawget(_G, "ZMAUGMENT")
  local e = field(field(Z, key_hex(Z, K_STORE)), ref_of(map_of(Z), 55407))
  local v = hfield(e, "isUnlocked")
  if v == nil then return "nil" end
  return tostring(v)
end

-- the native list repaint
local function repaint(c)
  local Z = rawget(_G, "ZMAUGMENT")
  local f = key_hex(Z, K_REPAINT)
  f = f ~= nil and field(Z, f) or nil
  if type(f) ~= "function" then return false end
  local ty = hfield(hfield(Z, "equipment_type"), "none")
  if ty == nil then return false end
  return pcall(f, c, ty) == true
end

-- the cache member and the builder beside it
local function ckey(Z)
  local k = slot_of(Z, "augmentresearchchallenges")
  if k ~= nil then return k end
  return key_hex(Z, K_CACHE)
end

-- the builder that owns the cache
local function bfn(Z)
  local f = fn_of(Z, "cacheaugmentresearchchallenges")
  if f ~= nil then return f end
  local k = key_hex(Z, K_BUILD)
  if k == nil then return nil end
  local v = field(Z, k)
  if type(v) == "function" then return v end
  return nil
end

-- nils the cache and lets the game build it again
local function recache(c)
  local Z = rawget(_G, "ZMAUGMENT")
  if type(Z) ~= "table" then return nil, nil, 0 end
  local k = ckey(Z)
  if k == nil then return nil, nil, 0 end
  local f = bfn(Z)
  if f == nil then return nil, nil, 0 end
  local old = field(Z, k)
  local before = type(old)
  if not pcall(function() Z[k] = nil end) then return before, nil, 0 end
  local ok = pcall(f, c)
  local now = field(Z, k)
  if not ok or type(now) ~= "table" then
    if now == nil then pcall(function() Z[k] = old end) end
    return before, type(now), 0
  end
  local n = 0
  for _ in pairs(now) do n = n + 1 end
  return before, "table", n
end

-- the count pass the game runs on its own build
local function gate(c, owned, store, done, say)
  G.gkey, G.gval = nil, nil
  local before, after, rows = recache(c)
  if G.r1Said ~= true then
    G.r1Said = true
    dp("augprobe R1 cache=" .. nn(before) .. " rebuilt=" .. nn(after) .. " rows=" .. rows)
  end
  local rebuilt = after == "table"
  if rebuilt then
    pcall(repaint, c)
    if type(done) == "table" then pcall(flag, store, done) end
  end
  if say ~= true then return end
  local fed = type(G.gval) == "number" and 1 or 0
  dp("augments gate owned=" .. owned .. " key=" .. nn(G.gkey or G.ukey)
    .. " fed=" .. fed .. " rebuilt=" .. (rebuilt and 1 or 0) .. " qr=" .. qrword())
end

-- every panel slot follows the tier
local function slots(c, t)
  local root = rawget(_G, "_DataSources") or rawget(_G, "DataSources")
  if root == nil then return 0 end
  local node = hfield(hfield(hfield(root, "zm"), "frontend"), "augment_select")
  local arr = hfield(node, "current_augment_research")
  if type(arr) ~= "table" then return 0 end
  local n = 0
  for i = 1, SLOTS do
    local slot = field(arr, i)
    if type(slot) == "table" then
      local ds = hfield(slot, "is_unlocked")
      local set = hfield(ds, "SetValue")
      if type(set) == "function" then
        local want = i <= t
        local have = nil
        local get = hfield(ds, "GetValue")
        if type(get) == "function" then
          local ok, v = pcall(get, ds, c)
          if ok then have = v end
        end
        if have ~= want and pcall(set, ds, c, want) then n = n + 1 end
      end
    end
  end
  return n
end

-- the ref one focused item names
local function ref_of_item(v, c)
  if type(v) == "string" then return v end
  if type(v) ~= "table" then return nil end
  local rv = hfield(v, "ref")
  if type(rv) == "string" then return rv end
  local g = nil
  if type(rv) == "function" then g = rv else g = hfield(rv, "GetValue") end
  if type(g) ~= "function" then return nil end
  local ok, x = pcall(g, rv or v, c)
  if ok and type(x) == "string" then return x end
  return nil
end

-- the item the publisher is drawing
local function slotted(c, item)
  local get = hfield(item, "GetValue")
  if type(get) ~= "function" then return 0 end
  local ok, v = pcall(get, item, c)
  if not ok or v == nil then return 0 end
  local ref = ref_of_item(v, c)
  if ref == nil then return 0 end
  G.last = ref
  local t = G.tier[ref]
  if t == nil then return 0 end
  return slots(c, t)
end

-- the cached row the active pick names
local function active_row()
  local sat = G.sat
  if sat == nil or sat < 1 then return nil, nil end
  local cache = cache_of(rawget(_G, "ZMAUGMENT"))
  if type(cache) ~= "table" then return nil, nil end
  local key, row = nil, nil
  for k, ch in pairs(cache) do
    if type(ch) == "table" and tonumber(hfield(ch, "achievementID")) == sat then
      if type(k) == "number" then return k, ch end
      if key == nil then key, row = k, ch end
    end
  end
  if key == nil then return nil, nil end
  return tonumber(key), row
end

-- one refresh ends on the game own numbers
local function whole(c)
  local Z = rawget(_G, "ZMAUGMENT")
  if type(Z) ~= "table" then return 0 end
  local ks = key_hex(Z, K_STORE)
  if ks == nil then return 0 end
  local store = field(Z, ks)
  local cache = cache_of(Z)
  if type(store) ~= "table" or type(cache) ~= "table" then return 0 end
  local k, o = spy_on()
  local n = 0
  local ok = pcall(function() n = retier(c, cache) end)
  spy_off(k, o)
  if not ok then n = 0 end
  local owned, tiers, rows, items, done = 0, {}, 0, {}, {}
  pcall(function()
    alias(cache)
    owned, tiers, rows, items, done = ticks(c, store, cache, map_of(Z))
  end)
  local prev = G.owned
  G.tier, G.rows, G.owned, G.ix = tiers, rows, owned, items
  if rows > 0 then
    pcall(flag, store, done)
    if front() ~= false then pcall(clearall, c, Z, store, done) end
    if owned ~= prev then
      pcall(gate, c, owned, store, done, true)
    elseif owned > 0 and G.gfed ~= true and (G.rtry or 0) < RTRIES then
      G.rtry = (G.rtry or 0) + 1
      pcall(gate, c, owned, store, done, false)
    end
    if G.ladSaid ~= true and G.lad ~= nil then
      G.ladSaid = true
      local ref, rungs, first, p = G.lad.ref, G.lad.rungs, G.lad.first, G.lad.p
      local akey, arow = active_row()
      if arow ~= nil then
        ref = ref_of(map_of(Z), akey) or ref
        rungs, first = rung_of(arow), first_of(hfield(arow, "amount"))
        local _, ap = steps(c, arow)
        p = ap
      end
      dp("augments ladder ref=" .. tostring(ref) .. " rungs=" .. rungs
        .. " first=" .. first .. " progress=" .. p)
    end
  end
  if G.last ~= nil and G.tier[G.last] ~= nil then slots(c, G.tier[G.last]) end
  if G.ownSaid ~= true and rows > 0 then
    G.ownSaid = true
    dp("augments owned=" .. owned .. " keys=" .. kindword(cache))
  end
  return n
end

local pass

-- the augment ids the toggle path answers
local function idmap(c)
  local Z = rawget(_G, "ZMAUGMENT")
  if type(Z) ~= "table" then return nil end
  local ks = key_hex(Z, K_STORE)
  if ks == nil then return nil end
  local store, cache = field(Z, ks), cache_of(Z)
  if type(store) ~= "table" or type(cache) ~= "table" then return nil end
  local _, _, rows, items = ticks(c, store, cache, map_of(Z), true)
  if rows == 0 then return nil end
  return items
end

-- the start event and the key it carries
local function startid()
  if G.ev ~= nil then return G.ev, G.key end
  local ch = rawget(_G, "Challenge")
  local fe, fk = fn_of(ch, "getaeeventid"), fn_of(ch, "GetAEEventKeyID")
  local ev, key = START_EVENT, START_KEY
  if fe ~= nil then
    local ok, v = pcall(fe, "zm_augment_start_progression")
    if ok and tonumber(v) ~= nil then ev = math.floor(tonumber(v)) end
  end
  if fk ~= nil then
    local ok, v = pcall(fk, "zm_augment_start_progression", "activate_id")
    if ok and tonumber(v) ~= nil then key = math.floor(tonumber(v)) end
  end
  G.ev, G.key = ev, key
  return ev, key
end

-- the value carried beside a key
local function pair_of(key, a, n)
  local i = 1
  while i + 1 <= n do
    if tonumber(a[i]) == key then return tonumber(a[i + 1]) end
    i = i + 2
  end
  return nil
end

-- the research row a sent id names
local function resolve(id)
  local Z = rawget(_G, "ZMAUGMENT")
  if type(Z) ~= "table" then return id end
  local cache = cache_of(Z)
  if type(cache) ~= "table" then return id end
  local sat, cer = nil, nil
  for _, ch in pairs(cache) do
    if type(ch) == "table" then
      local a = tonumber(hfield(ch, "achievementID"))
      local b = tonumber(hfield(ch, "carryoverAchievementID"))
      if a ~= nil and a == id then sat = a end
      if b ~= nil and b == id and cer == nil then cer = a end
    end
  end
  if sat ~= nil then return sat end
  if cer ~= nil then return cer end
  return id
end

-- menu or match
front = function()
  local f = fn_of(rawget(_G, "Engine"), "InFrontend")
  if f == nil then return nil end
  local ok, v = pcall(f)
  if ok then return v == true end
  return nil
end

local DGET, DSET

-- the channel dvar as the hash the engine stores
local function dvkey()
  local h = rawget(_G, "xhashdvar")
  if type(h) == "function" then
    local ok, k = pcall(h, CH)
    if ok and k ~= nil then return k end
  end
  return CH
end

-- the channel line as this vm reads it
local function dget()
  if DGET == nil then DGET = fn_of(rawget(_G, "Dvar"), "GetDvarString") end
  if DGET == nil then return nil end
  local key = dvkey()
  local ok, v = pcall(DGET, key)
  if ok and type(v) == "string" then return v end
  if key ~= CH then
    local okp, v2 = pcall(DGET, CH)
    if okp and type(v2) == "string" then return v2 end
  end
  return nil
end

-- the id the channel line names
local function chrow(v)
  if type(v) ~= "string" then return nil end
  local n = string.match(v, "^a=(%d+)")
  if n == nil then return nil end
  return tonumber(n)
end

-- one channel write read back
local function dchput(val)
  if DSET == nil then DSET = fn_of(rawget(_G, "Dvar"), "SetDvarString") end
  if DSET == nil then return false end
  local key = dvkey()
  if not pcall(DSET, key, val) and key ~= CH then pcall(DSET, CH, val) end
  return dget() == val
end

-- the pick the channel line names
local function seed()
  local id = chrow(dget())
  if id == nil or id < 1 then return false end
  if G.sat == id then return true end
  G.active, G.sat = id, id
  if G.restored ~= true then
    G.restored = true
    if front() ~= false then dp("augments research restored a=" .. id) end
  end
  return true
end

-- the pick a press writes to the channel
local function save(sat)
  if front() == false then return false end
  local val = "a=" .. sat
  if dget() == val then return true end
  if not dchput(val) then return false end
  dp("augments research saved a=" .. sat)
  return true
end

-- the loot id the active research item publishes
local function active_loot(c, key)
  local root = rawget(_G, "_DataSources") or rawget(_G, "DataSources")
  local node = hfield(hfield(hfield(root, "zm"), "frontend"), "augment_select")
  local ds = hfield(hfield(node, "active_augment_research_item"), "loot_id")
  local get = hfield(ds, "GetValue")
  if type(get) == "function" then
    local ok, v = pcall(get, ds, c)
    if ok and v ~= nil then return v end
  end
  return key
end

-- the baseline one row is read against
local BASE = {}

-- the loot one rung of the active item names
local function rung_loot(key, i)
  local Z = rawget(_G, "ZMAUGMENT")
  local ks = key_hex(Z, K_STORE)
  if ks == nil then return nil end
  local ref = ref_of(map_of(Z), key)
  local list = field(field(Z, ks), ref)
  if type(list) ~= "table" then return nil end
  local e = list[i]
  if type(e) ~= "table" then return nil end
  return tonumber(hfield(e, "lootid"))
end

-- one tier crossing queues one card
local function watch_tiers(c)
  if G.on ~= false then return end
  if front() ~= false then return end
  local key, row = active_row()
  if row == nil then return end
  local n = steps(c, row)
  local sat = G.sat
  local b = BASE[sat]
  if b == nil then
    BASE[sat] = { last = n }
    return
  end
  if b.base == nil then
    if b.last == n then b.base = n end
    b.last = n
    return
  end
  if n > b.base then
    local ref = ref_of(map_of(rawget(_G, "ZMAUGMENT")), key)
    for i = b.base + 1, n do
      local loot = rung_loot(key, i)
      if loot == nil then loot = active_loot(c, key) end
      G.cards[#G.cards + 1] = { sat = sat, tier = i, ref = ref, loot = loot }
      dp("augments tier id=" .. sat .. " tier=" .. i .. " queued")
    end
    b.base = n
  end
end

-- the press the menu sends
local function caught(ev, ...)
  local id = tonumber(ev)
  if id == nil then return end
  local one, two = dv(DV_ONE), dv(DV_TWO)
  if one == nil or two == nil then return end
  if one == "1" or two == "1" then return end
  local want, key = startid()
  if id ~= want and id ~= START_EVENT then return end
  local a = { ... }
  local v = pair_of(key, a, #a)
  if v == nil then v = tonumber(a[2]) end
  if v == nil or v < 1 then return end
  local sent = math.floor(v)
  local sat = resolve(sent)
  G.active, G.sat, G.dirty = sent, sat, true
  dp("augments research start id=" .. sent .. " sat=" .. sat)
  pcall(save, sat)
end

-- the answer the activation rows carry
local function answered(r, id)
  local n = tonumber(id)
  if n ~= ACT_A and n ~= ACT_B then return r end
  if G.active < 1 then return r end
  local act = G.active
  if n == ACT_A and G.sat >= 1 then act = G.sat end
  local t = r
  if type(t) ~= "table" then t = {} end
  local p = field(t, "progress")
  if type(p) ~= "table" then
    p = {}
    if not pcall(function() t.progress = p end) then return r end
  end
  put(p, "last_activation", act)
  return t
end

-- a pass that keeps the menu on the store
pass = function(c)
  if c == nil then c = G.c end
  G.c = c
  G.passes = (G.passes or 0) + 1
  local one, two = dv(DV_ONE), dv(DV_TWO)
  if one == nil or two == nil then return end
  local on = (one == "1") or (two == "1")
  G.on = on
  if G.sat == nil or G.sat < 1 or front() == true then pcall(seed) end
  local n = 0
  if not on then
    pcall(ureg)
    n = whole(c)
  else
    local okm, m = pcall(idmap, c)
    if okm and type(m) == "table" then G.ix = m end
  end
  if G.said ~= true and (on or n > 0) then
    G.said = true
    dp("augments armed " .. VERSION .. " unlock=" .. word(one) .. " all=" .. word(two)
      .. " devcomplete=" .. devword())
  end
  if G.dirty then
    G.dirty = false
    local _, f = slot_of(rawget(_G, "ZMAUGMENT"), "initcurrentactiveresearch")
    if type(f) == "function" then pcall(f, c) end
  end
  pcall(watch_tiers, c)
  pcall(r2say)
end

-- the wrappers this part keeps one of
local W = {}

-- puts one wrapper on a member it owns
local function arm(tag, tbl, key, make)
  if type(tbl) ~= "table" or key == nil then return false end
  local okc, cur = pcall(rawget, tbl, key)
  if not okc or type(cur) ~= "function" then return false end
  local st = W[tag]
  if st ~= nil then
    if cur == st.w then return true end
    if cur ~= st.orig then return true end
    st.orig = cur
  else
    st = { tbl = tbl, key = key, orig = cur }
    W[tag] = st
  end
  local w = make(st.orig)
  if type(w) ~= "function" then return false end
  st.w = w
  if not pcall(function() tbl[key] = w end) then return false end
  local okn, now = pcall(rawget, tbl, key)
  return okn and now == w
end

-- the refresh a menu runs
local function onrefresh(orig)
  return function(c, ...)
    local r = orig(c, ...)
    pcall(pass, c)
    return r
  end
end

-- the publisher over the nine slots
local function onslots(orig)
  return function(c, item, ...)
    local r = orig(c, item, ...)
    pcall(slotted, c, item)
    return r
  end
end

-- the send a press goes through
local function onpress(orig)
  return function(c, ev, n, ...)
    local r = orig(c, ev, n, ...)
    pcall(caught, ev, ...)
    return r
  end
end

-- the progress read the menu asks
local function onread(orig)
  return function(c, id, ...)
    local r = orig(c, id, ...)
    local ok, out = pcall(answered, r, id)
    if ok then return out end
    return r
  end
end

-- the switch state the lock rule reads
hon = function()
  if G.on ~= nil then return G.on end
  local one, two = dv(DV_ONE), dv(DV_TWO)
  if one == nil or two == nil then return nil end
  G.on = (one == "1") or (two == "1")
  return G.on
end

-- one augment id locked by the tier reached
local function locked_item(id)
  local n = tonumber(id)
  if n == nil then return nil end
  if hon() ~= false then return nil end
  local at = G.ix ~= nil and G.ix[math.floor(n)] or nil
  if at == nil then return nil end
  local t = G.tier[at.ref]
  if t == nil then return nil end
  return at.i > t
end

-- a call through that never rethrows
local function thru(f, id)
  local ok, v = pcall(f, id)
  if not ok then return nil end
  return v
end

-- an id the switch answers as not locked
local function gopen(id)
  if hon() ~= true then return false end
  local n = tonumber(id)
  if n == nil or type(G.ix) ~= "table" then return false end
  return G.ix[math.floor(n)] ~= nil
end

-- the locked side of the door
local function lk_ask(orig)
  return function(id)
    local ok, locked = pcall(locked_item, id)
    if ok and locked == true then return true end
    local okg, yes = pcall(gopen, id)
    if okg and yes then return false end
    return thru(orig, id)
  end
end

-- the open side of the door
local function lk_give(orig)
  return function(id)
    local ok, locked = pcall(locked_item, id)
    if ok and locked == false then return true end
    if ok and locked == true then return false end
    if hon() == true then
      local n = tonumber(id)
      if n ~= nil and type(G.ix) == "table" and G.ix[math.floor(n)] ~= nil then return true end
    end
    return thru(orig, id)
  end
end

-- the locks table this part extends once
local LK = { tbl = nil, a = nil, o = nil }

-- extends the lock door once per table
local function lk_arm()
  local locks = S.locks
  if type(locks) ~= "table" then return false end
  if LK.tbl == locks then return LK.a ~= nil and LK.o ~= nil end
  local a, o = locks.answer, locks.open
  if type(a) ~= "function" or type(o) ~= "function" then return false end
  local wa, wo = lk_ask(a), lk_give(o)
  locks.answer, locks.open = wa, wo
  LK.tbl, LK.a, LK.o = locks, wa, wo
  return true
end

-- says whether the lock door took the extension
local function lk_say()
  local locks = S.locks
  if type(locks) == "table" and LK.tbl == locks and LK.a ~= nil and LK.o ~= nil then
    if G.lkOn ~= true then
      G.lkOn = true
      dp("augments locks armed")
    end
    return
  end
  if G.lkMiss ~= true and type(S.parts) == "table" and S.parts.prison == true then
    G.lkMiss = true
    dp("augments locks missing")
  end
end

-- puts the wrappers this vm can reach in place
local function install()
  local Z = rawget(_G, "ZMAUGMENT")
  local ok, kf = false, nil
  if kfill(Z, K_STORE, "store") ~= nil then
    kf = kfill(Z, K_REFRESH, "refresh")
    if kf ~= nil then ok = arm("refresh", Z, kf, onrefresh) end
    if kfill(Z, K_SLOTS, "slots") ~= nil then arm("slots", Z, K.slots, onslots) end
  end
  local C = rawget(_G, "Challenges")
  if kfill(C, K_SEND, "send") ~= nil then arm("send", C, K.send, onpress) end
  local OC = rawget(_G, "OnlineChallenges")
  if kfill(OC, K_PROG, "prog") ~= nil then arm("prog", OC, K.prog, onread) end
  pcall(lk_arm)
  return ok
end

local timerEl = nil

-- a waiting element on the ui root
local function make_el()
  local lui = rawget(_G, "LUI")
  local _, getroot = slot_of(lui, "GetRoot")
  if type(getroot) ~= "function" then return nil end
  local okr, rootEl = pcall(getroot)
  if not okr or rootEl == nil then return nil end
  local el = nil
  local _, uie = slot_of(lui, "UIElement")
  local mk = nil
  if uie ~= nil then mk = fn_of(uie, "new") end
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
  pcall(ureg)
  pcall(lk_say)
  if G.dirty or G.ticks % PASS_TICKS == 1 then pcall(pass, G.c) end
  if not again() then pcall(start) end
end

S.probes.augments = function() return W.refresh ~= nil and W.refresh.w ~= nil end

pcall(install)
pcall(ureg)
pcall(seed)
pcall(start)
local api = S.api
local r = type(api) == "table" and api.ready or nil
if type(r) == "function" then pcall(r) end
