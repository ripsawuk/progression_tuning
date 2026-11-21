-- this shit is for locking other shit, for progression yanno

local PART = "prison"

local S = rawget(_G, "ProgressionTuning")
if type(S) ~= "table" then
  S = { parts = {}, hooks = {}, probes = {}, api = {}, g11 = {}, scope = {} }
  rawset(_G, "ProgressionTuning", S)
end
if S.parts[PART] == true then return end
S.parts[PART] = true
local A = S.api
local function log(...) return A.log(...) end
local function said(...) return A.said(...) end
local function clip(...) return A.clip(...) end
local function member(...) return A.member(...) end
local function fn_of(...) return A.fn_of(...) end
local function call(...) return A.call(...) end
local function fcache(...) return A.fcache(...) end
local function want(...) return A.want(...) end
local function ours(...) return A.ours(...) end

local G = S.g11
local GLOCKSMITH = S.scope
local GMAXID = 0x3FFFF
-- the client own weapon table size
local GCAMO_CAP = 2048
-- ticks between two tries at an empty ladder
local CAMO_SCAN_GAP = 8
-- an empty ladder reads as this table
local GCAMONIL = {}
local PASS_QUIET = 8
local GMAX_TICKS = 480
local GPOLL_TICKS = 8

local function grefresh(...) return A.refresh(...) end
local function glockedNow(...) return A.bit(...) end
local function greward(...) return A.greward(...) end
local function ginstall(...) return A.door_install(...) end
local function gmissing(...) return A.door_missing(...) end
local function gensureWrapped(...) return A.door_retry(...) end

local GNTYPE = "gettypeforid"
local GTYPES = "itemTypes"
local GNGAME = "GetActiveGameModeKey"
local GNDEFAULT = "isitemdefault"
local GNUSEABLE = "IsLootUseableOnCurrentPlatform"
local GNBUNDLE = "GetFirstBundleWithLootId"
local GNBPASS = "isbattlepassreward"
local GNBLCK = "isblackcellreward"
local GNMAP = "IsReward"
local GNDESC = "GetUnlockDescription"
local GDOOR_CAP = 24
local GCAMO_LOG_CAP = 24
local GCARD_CAP = 40
local CARD_GAP = 32
local GTYPE_A, GTYPE_C, GTYPE_R = nil, nil, nil
local GTYPE_H, GTYPE_E = nil, nil
local GTYPE_PC, GTYPE_COS, GTYPE_TOG = nil, nil, nil
local GTOGV, GTOGT = nil, nil
local GCAMO_NONE_N = 0
-- the store types by the game own names
local GCOSN = { "ATTACHMENT", "OPERATOR", "OPERATOR_SKIN", "OPERATOR_EXECUTION", "PLAYERCARD",
  "EMBLEM", "CAMO", "RETICLE", "CHARM", "STICKER", "SPRAYS", "LOAD_SCREEN", "EMOTE" }
-- the unlock switch each type answers to
local GTOGN = {
  { "WEAPON", "zm_unlock_weapons" },
  { "ATTACHMENT", "zm_unlock_attachments" }, { "CAMO", "zm_unlock_camos" },
  { "RETICLE", "zm_unlock_reticles" }, { "PLAYERCARD", "zm_unlock_cards" },
  { "EMBLEM", "zm_unlock_emblems" }, { "OPERATOR", "zm_unlock_operators" },
  { "OPERATOR_SKIN", "zm_unlock_operators" }, { "OPERATOR_EXECUTION", "zm_unlock_finishers" },
  { "CHARM", "zm_unlock_charms" }, { "STICKER", "zm_unlock_stickers" },
  { "SPRAYS", "zm_unlock_sprays" }, { "EMOTE", "zm_unlock_emotes" },
  { "LOAD_SCREEN", "zm_unlock_loadingscreens" }, { "PERK", "zm_unlock_perks" },
  { "EQUIPMENT", "zm_unlock_equipment" }, { "STREAK", "zm_unlock_scorestreaks" },
  { "SUPER", "zm_unlock_fieldupgrades" }, { "WILDCARD", "zm_unlock_wildcards" },
  { "AMMOMOD", "zm_unlock_ammomods" },
}

-- the game own type tables resolved once
local function gtypepair()
  if GTYPE_COS ~= nil then return true end
  local lo = rawget(_G, "LOOT")
  if type(lo) ~= "table" then return false end
  local _, it = member(lo, GTYPES)
  if type(it) ~= "table" then return false end
  local cos, tog = {}, {}
  for i = 1, #GCOSN do
    local _, v = member(it, GCOSN[i])
    local t = tonumber(v)
    if t ~= nil then cos[t] = true end
    if GCOSN[i] == "PLAYERCARD" then GTYPE_PC = t end
  end
  for i = 1, #GTOGN do
    local _, v = member(it, GTOGN[i][1])
    local t = tonumber(v)
    if t ~= nil then tog[t] = GTOGN[i][2] end
  end
  GTYPE_COS, GTYPE_TOG = cos, tog
  local _, a = member(it, "ATTACHMENT")
  local _, c = member(it, "CAMO")
  local _, r = member(it, "RETICLE")
  local _, h = member(it, "CHARM")
  local _, e = member(it, "EMBLEM")
  GTYPE_H, GTYPE_E = tonumber(h), tonumber(e)
  local na, nc = tonumber(a), tonumber(c)
  if na == nil or nc == nil then return true end
  GTYPE_A, GTYPE_C, GTYPE_R = na, nc, tonumber(r)
  G.typeA, G.typeC = GTYPE_A, GTYPE_C
  return true
end

-- says once why the type route fell back
local function gfallback(why)
  if said("gtype:" .. why) then
    log("lock door: " .. why .. " - answering from the " .. S.scopeN
      .. "-id locksmith scope instead of the item type")
  end
end

-- the client own item type for an id
local function gtype(n)
  local c = G.typecache[n]
  if c ~= nil then return c end
  if not gtypepair() then
    gfallback("no LOOT.itemTypes in this VM")
    return nil
  end
  local f = fcache(rawget(_G, "LOOT"), GNTYPE)
  if f == nil then
    gfallback("no LOOT.gettypeforid in this VM")
    return nil
  end
  local ok, v = pcall(f, n)
  if not ok then
    gfallback("LOOT.gettypeforid raised")
    return nil
  end
  local t = tonumber(v)
  if t == nil then
    gfallback("LOOT.gettypeforid answered no type")
    return nil
  end
  G.typecache[n] = t
  return t
end

-- the store ids a level prestige or rank list earns
local GEARN_IDS = {
  62474, 62477, 62479, 62480, 62482, 62483, 62484, 62485, 62486, 62487, 62488, 62489,
  62490, 62491, 62493, 62494, 62495, 62496, 62517, 62769, 63349, 63352, 63353, 63354,
  63355, 63356, 63357, 63358, 63359, 63360, 91985, 92016, 92060, 92061, 94352, 94415,
  98139, 98140, 98346, 98347, 98769, 98770, 112320, 112321, 112325, 112330, 112331, 112338,
  112340, 112341, 112344, 112346, 112347, 112349, 112350, 112351, 112352, 112353, 112354, 112355,
  112356, 112357, 112358, 112359, 112360, 112361, 112456, 112457, 112460, 112461, 112462, 112463,
  112467, 112468, 112469, 112470, 112471, 112472, 112743, 113111, 113113, 113114, 113115, 113244,
  113382, 113879, 113880, 113897, 113921, 113923, 114150, 114180, 114186, 117450, 121135, 121671,
  122030, 122196
}
local GEARN = {}
for i = 1, #GEARN_IDS do GEARN[GEARN_IDS[i]] = true end

-- every unlock switch read once a tick
local function gtoggles()
  local now = S.tick
  if GTOGV ~= nil and GTOGT == now then return GTOGV end
  if not gtypepair() then return nil end
  local v = {}
  for t, name in pairs(GTYPE_TOG) do
    local s = A.dv(name)
    v[t] = (s ~= nil and s ~= "" and s ~= "0")
  end
  local old = GTOGV
  GTOGV, GTOGT = v, now
  -- a changed switch starts a new answer epoch
  if old ~= nil then
    for t, on in pairs(v) do
      if old[t] ~= on then
        G.epoch = G.epoch + 1
        break
      end
    end
  end
  return v
end

-- is this type forced open by its own switch
local function gtoggle(t)
  if t == nil then return false end
  local v = gtoggles()
  return v ~= nil and v[t] == true
end

-- is a lock line wanted now
local function glogging()
  if S.toggles == nil then return false end
  if S.toggles.log then return true end
  return S.diag == true
end

-- one bounded line per camo ask
local function gdoor(n, t, bit, locked)
  if G.doorN >= GDOOR_CAP then return end
  if G.doorSaid[n] then return end
  G.doorSaid[n] = true
  G.doorN = G.doorN + 1
  log("door id=" .. n .. " type=" .. t .. " bit=" .. bit .. " answer=" .. (locked and "locked" or "pass"))
end

local GPREF = "getweaponprestigelevel"
local GPMAX = "getmaxweaponprestigelevel"
local GPLEVEL = "GetWeaponLevel"
local GPREQ = "getweaponprestigeattachmentdetails"
local GPBUNDLE = "getbundlebyid"
local GPCAMOS = "getweaponprestigecamos"
local GCAMODATA = "getcamodatabyid"
local GP_CAP = 24

-- a whole number out of a call
local function gnumber(f, ...)
  if type(f) ~= "function" then return nil end
  local ok, v = pcall(f, ...)
  if not ok then return nil end
  local n = tonumber(v)
  if n == nil then return nil end
  return math.floor(n)
end

-- the weapon own prestige level
local function gprest(ref)
  if type(ref) ~= "string" or ref == "" then return nil end
  return gnumber(fn_of(rawget(_G, "PRESTIGE"), GPREF), 0, ref)
end

-- a whole number field of a table
local function gfield(t, name)
  if type(t) ~= "table" then return nil end
  local _, v = member(t, name)
  local n = tonumber(v)
  if n == nil then return nil end
  return math.floor(n)
end

-- one prestige line per id per build
local function gpline(txt)
  if G.psaidN >= GP_CAP then return end
  if G.psaid[txt] then return end
  G.psaid[txt] = true
  G.psaidN = G.psaidN + 1
  log(txt)
end

-- the client own bundle cache
local function gbundle(n)
  local c = G.bundles[n]
  if c ~= nil then return c end
  local f = fcache(rawget(_G, "ATTACHMENT"), GPBUNDLE)
  if f == nil then
    if said("gbundle:api") then
      log("prestige lock: no ATTACHMENT." .. GPBUNDLE .. " in this VM - a prestige attachment cannot be named,"
        .. " so nothing closes on prestige alone")
    end
    return nil
  end
  local ok, b = pcall(f, n)
  if not ok or type(b) ~= "table" then
    G.bundles[n] = false
    return false
  end
  G.bundles[n] = b
  return b
end

-- one id static record built on its first ask
local function grec(n)
  local c = G.rec or {}
  G.rec = c
  local r = c[n]
  if r ~= nil then return r end
  local t = gtype(n)
  if t == nil then return nil end
  r = { t = t }
  c[n] = r
  return r
end

-- the prestige a reward needs once a session
local function greq(n, r)
  local b = gbundle(n)
  if b == nil then return nil end
  if b == false then return false end
  local _, ispr = member(b, "isprestige")
  if ispr ~= true then return false end
  local _, ref = member(b, "weaponunlock")
  if type(ref) ~= "string" or ref == "" then
    if said("gattach:owner:" .. n) then
      log("prestige lock: " .. n .. " is a prestige reward but names no weapon in its own bundle - left as the client"
        .. " answers it")
    end
    return false
  end
  if not ours(ref) then
    if said("gattach:owner:" .. n) then
      log("prestige lock: " .. n .. " is a prestige reward for " .. clip(ref, 28) .. ", which is not one of ours -"
        .. " left as the client answers it")
    end
    return false
  end
  local reqf = fn_of(rawget(_G, "WEAPON"), GPREQ)
  if reqf == nil then
    if said("gattach:req") then
      log("prestige lock: no WEAPON." .. GPREQ .. " in this VM - the prestige a reward needs cannot be read, so it"
        .. " keeps the client's own answer")
    end
    return nil
  end
  local okd, d = pcall(reqf, ref, n)
  if not okd then return nil end
  local req = nil
  if type(d) == "table" then req = gfield(d, "prestige") end
  if req == nil then return false end
  r.ref = ref
  return req
end

-- a prestige attachment waits for its prestige
local function gattach(n)
  if gtoggle(GTYPE_A) then return false end
  local r = grec(n)
  if r == nil then return false end
  if r.req == nil then r.req = greq(n, r) end
  if r.req == nil or r.req == false then return false end
  local have = gprest(r.ref)
  if have == nil then
    if said("gattach:prestige") then
      log("prestige lock: PRESTIGE." .. GPREF .. " cannot be read in this VM - the prestige gate keeps the"
        .. " client's own answer")
    end
    return false
  end
  local locked = have < r.req
  if glogging() then
    gpline("prestige id=" .. n .. " tier=" .. r.req .. " prestige=" .. have
      .. " answer=" .. (locked and "locked" or "open"))
  end
  return locked
end

-- the weapon a camo own data names
local function gcamoref(n)
  local c = G.camoref[n]
  if c ~= nil then
    if c == false then return nil end
    return c
  end
  local f = fcache(rawget(_G, "WEAPON"), GCAMODATA)
  if f == nil then
    if said("gcamo:api") then
      log("prestige lock: no WEAPON." .. GCAMODATA .. " in this VM - a camo's weapon cannot be named, so a prestige"
        .. " camo keeps the client's own answer")
    end
    return nil
  end
  local ok, b = pcall(f, n)
  if not ok then return nil end
  local ref = nil
  if type(b) == "table" then
    local _, v = member(b, "weaponref")
    if type(v) == "string" and v ~= "" then ref = v end
  end
  if ref == nil then
    G.camoref[n] = false
    return nil
  end
  G.camoref[n] = ref
  return ref
end

-- every weapon prestige camo ladders in one map
local function gcamomap()
  if G.camomap ~= nil then return G.camomap end
  if G.camoTry ~= nil and ((S.tick or 0) - G.camoTry) < CAMO_SCAN_GAP then return G.camoEmpty end
  G.camoTry = S.tick or 0
  local f = fn_of(rawget(_G, "PRESTIGE"), GPCAMOS)
  local enum = fn_of(rawget(_G, "WEAPON"), "enumerateweapons")
  if f == nil or enum == nil then
    if f ~= nil and enum == nil and said("gcamo:enum") then
      log("prestige lock: no WEAPON.enumerateweapons in this VM - a camo whose own data names no weapon cannot be tied"
        .. " to one, so it keeps the client's own answer")
    end
    return G.camoEmpty
  end
  local map = {}
  local seen, n, cut = 0, 0, false
  pcall(function()
    enum(function(w)
      if seen >= GCAMO_CAP then
        cut = true
        return
      end
      seen = seen + 1
      local _, ref = member(w, "ref")
      if type(ref) ~= "string" or ref == "" then return end
      local ok, g1, g2, g3 = pcall(f, ref)
      if not ok then return end
      local groups = { g1, g2, g3 }
      local gi = 1
      while gi <= 3 do
        local g = groups[gi]
        if type(g) == "table" then
          local j = 1
          while j <= #g do
            local e = g[j]
            local cb = nil
            if type(e) == "table" then
              local _, v = member(e, "camoBundle")
              if type(v) == "table" then cb = v end
            end
            if cb ~= nil then
              local k = gfield(cb, "lootid")
              if k ~= nil and map[k] == nil then
                map[k] = { ref = ref, e = e }
                n = n + 1
              end
            end
            j = j + 1
          end
        end
        gi = gi + 1
      end
    end)
  end)
  if cut then
    if glogging() and G.camoMissSaid < 2 then
      G.camoMissSaid = G.camoMissSaid + 1
      log("prestige lock: the weapon list is longer than " .. GCAMO_CAP .. " - the camo map is truncated and"
        .. " not kept")
    end
    return G.camoEmpty
  end
  if seen < 1 or n < 1 then
    if glogging() and G.camoMissSaid < 2 then
      G.camoMissSaid = G.camoMissSaid + 1
      log("prestige lock: the weapon ladders name " .. n .. " prestige camo ids over " .. seen
        .. " weapons - not kept, the next ask retries")
    end
    return G.camoEmpty
  end
  G.camomap = map
  if glogging() and G.camoMapSaid < 4 then
    G.camoMapSaid = G.camoMapSaid + 1
    log("prestige lock: the weapon ladders name " .. n .. " prestige camo ids over " .. seen .. " weapons")
  end
  return map
end

-- one weapon own prestige camo ladder kept for the session
local function gcamoload(ref)
  local t = G.pcamo[ref]
  if t == false then
    if (S.tick or 0) - (G.pcamoAt[ref] or 0) < GPOLL_TICKS then return GCAMONIL end
    t = nil
  end
  if t ~= nil then return t end
  local list, n = {}, 0
  if not ours(ref) then
    G.pcamo[ref] = list
    return list
  end
  local f = fn_of(rawget(_G, "PRESTIGE"), GPCAMOS)
  if f == nil then
    if said("gcamo:list") then
      log("prestige lock: no PRESTIGE." .. GPCAMOS .. " in this VM - a prestige camo's band cannot be read, so"
        .. " the tiles keep the client's own answer")
    end
    return list
  end
  local ok, g1, g2, g3 = pcall(f, ref)
  if not ok then return list end
  local groups = { g1, g2, g3 }
  local gi = 1
  while gi <= 3 do
    local g = groups[gi]
    if type(g) == "table" then
      local j = 1
      while j <= #g do
        local e = g[j]
        local cb = nil
        if type(e) == "table" then
          local _, v = member(e, "camoBundle")
          if type(v) == "table" then cb = v end
        end
        if cb ~= nil then
          local k = gfield(cb, "lootid")
          if k ~= nil and list[k] == nil then
            list[k] = e
            n = n + 1
          end
        end
        j = j + 1
      end
    end
    gi = gi + 1
  end
  if n > 0 then
    G.pcamo[ref] = list
  else
    G.pcamo[ref], G.pcamoAt[ref] = false, S.tick or 0
  end
  return list
end

-- how far a camo band has come
local function gprog(b, pr, lv)
  local p = 0
  if b.sp < pr then
    p = 1
  elseif pr == b.sp and b.tl > 0 then
    p = lv / b.tl
  end
  if b.mx <= b.sp then
    if b.tl < lv then
      p = 1
    elseif lv < b.sl then
      p = 0
    elseif lv < b.tl and b.sl < lv then
      if b.mx <= pr and b.tl > b.sl then
        p = (lv - b.sl) / (b.tl - b.sl)
      else
        p = 0
      end
    end
  end
  return p
end

-- how far a camo band has come from its natives
local function gcamoprog(e, ref)
  local pr = gprest(ref)
  if pr == nil then return nil end
  local lv = gnumber(fcache(rawget(_G, "PROGRESSION"), GPLEVEL), 0, ref)
  if lv == nil then return nil end
  local mx = gnumber(fcache(rawget(_G, "PRESTIGE"), GPMAX), ref)
  if mx == nil then return nil end
  local b = { sp = gfield(e, "startPrestige") or 0, tp = gfield(e, "targetPrestige") or 0,
              sl = gfield(e, "startLevel") or 0, tl = gfield(e, "targetLevel") or 0, mx = mx }
  return gprog(b, pr, lv), b.sp, b.tp, b.sl, b.tl, pr, lv
end

-- the weapon pair a band answers from
local function gpair(ref)
  local pr = gprest(ref)
  if pr == nil then return nil end
  return pr, gnumber(fcache(rawget(_G, "PROGRESSION"), GPLEVEL), 0, ref)
end

-- the band entry a camo sits in once
local function gband(n)
  local ref, e = gcamoref(n), nil
  if ref ~= nil then
    e = gcamoload(ref)[n]
  else
    local map = gcamomap()
    if map == G.camoEmpty then return nil end
    local m = map[n]
    if m ~= nil then ref, e = m.ref, m.e end
  end
  if ref == nil then return false end
  if not ours(ref) then return { ref = ref } end
  if e == nil then
    if G.pcamo[ref] == nil or G.pcamo[ref] == false then return nil end
    return false
  end
  local mx = gnumber(fcache(rawget(_G, "PRESTIGE"), GPMAX), ref)
  if mx == nil then return nil end
  return { ref = ref, sp = gfield(e, "startPrestige") or 0, tp = gfield(e, "targetPrestige") or 0,
           sl = gfield(e, "startLevel") or 0, tl = gfield(e, "targetLevel") or 0, mx = mx }
end

-- sums up the camo ids let through
local function gcamopass()
  if G.passAt == nil then return end
  if (S.tick or 0) - G.passAt < PASS_QUIET then return end
  local n, m = 0, 0
  pcall(function() for _ in pairs(G.passSeen) do n = n + 1 end end)
  pcall(function() for _ in pairs(G.askSeen) do m = m + 1 end end)
  G.passAt = nil
  if not glogging() or G.passSaid >= 8 then return end
  G.passSaid = G.passSaid + 1
  local ids = {}
  pcall(function()
    for k in pairs(G.passSeen) do
      if #ids < 6 then ids[#ids + 1] = tostring(k) end
    end
  end)
  log("prestige lock: " .. n .. " of " .. m .. " camo ids passed through (first 6: "
    .. table.concat(ids, ",") .. ")")
end

-- the band waits unless unlock camos is on
local function gcamo(n)
  if gtoggle(GTYPE_C) then return false end
  if G.askSeen[n] == nil then G.askSeen[n] = true end
  local r = grec(n)
  if r == nil then return false end
  if r.band == nil then r.band = gband(n) end
  local b = r.band
  if b == nil or b == false then
    if G.passSeen[n] == nil then
      G.passSeen[n] = true
      G.passAt = S.tick or 0
    end
    if S.toggles ~= nil and S.toggles.log and GCAMO_NONE_N < GCAMO_LOG_CAP
      and said("gcamo:none:" .. n) then
      GCAMO_NONE_N = GCAMO_NONE_N + 1
      log("prestige lock: " .. n .. " names no weapon in its own data and is in no weapon's prestige ladder in this"
        .. " VM - it keeps the client's own answer")
    end
    return false
  end
  if not ours(b.ref) then
    if G.passSeen[n] == nil then
      G.passSeen[n] = true
      G.passAt = S.tick or 0
    end
    if S.toggles ~= nil and S.toggles.log and said("gcamo:carried:" .. n) then
      log("prestige lock: " .. n .. " belongs to " .. clip(b.ref, 28) .. ", which is not one of ours - no band is"
        .. " computed and it keeps the client's own answer")
    end
    return false
  end
  local pr, lv = gpair(b.ref)
  if pr == nil or lv == nil then return false end
  local p = gprog(b, pr, lv)
  if glogging() then
    gpline("prestige camo id=" .. n .. " ref=" .. b.ref .. " start=" .. b.sp .. "/" .. b.sl
      .. " to=" .. b.tp .. "/" .. b.tl .. " prestige=" .. pr .. " level=" .. lv
      .. " answer=" .. (p < 1 and "locked" or "open"))
  end
  return p < 1
end

-- the weapon an id names by its own data
local function gidref(n)
  local ref = gcamoref(n)
  if ref ~= nil then return ref end
  local b = gbundle(n)
  if b == nil or b == false then return nil end
  local _, ref2 = member(b, "weaponunlock")
  if type(ref2) == "string" and ref2 ~= "" then return ref2 end
  return nil
end

local GSENT, GSENT_N, GTOK = nil, 0, {}
local GVORIG, GVWRAP, GTPW = nil, nil, nil

-- the client own sentinel ids
local function gsent()
  if GSENT ~= nil then return GSENT end
  local set, n = {}, 0
  local md = call(rawget(_G, "LOOT"), "getprogressionitemmetadata")
  if type(md) ~= "table" then
    if said("gsent:api") then
      log("lock value: LOOT.getprogressionitemmetadata answered no table in this VM - the permanent-unlock"
        .. " sentinel set is empty, so every count keeps the client's own answer")
    end
    GSENT = set
    return set
  end
  pcall(function()
    for _, row in pairs(md) do
      if type(row) == "table" then
        local id = gfield(row, "sentinel_id")
        if id ~= nil and set[id] == nil then
          set[id] = true
          n = n + 1
        end
      end
    end
  end)
  GSENT, GSENT_N = set, n
  return set
end

-- remembers every id the token reader saw
local function gtoksee(id)
  local n = tonumber(id)
  if n == nil then return end
  GTOK[math.floor(n)] = true
end

-- wraps the prestige token reader once
local function gtokwatch()
  if GTPW ~= nil then return true end
  local pre = rawget(_G, "PRESTIGE")
  if type(pre) ~= "table" then return false end
  local k, f = member(pre, "getweaponprestigetokenlootid")
  if k == nil or type(f) ~= "function" then
    if said("gtok:api") then
      log("lock value: no PRESTIGE.getweaponprestigetokenlootid in this VM - the prestige token id cannot be named,"
        .. " so its count keeps the client's own answer")
    end
    return false
  end
  local w = function(ref, ...)
    local ok, v = pcall(f, ref, ...)
    if not ok then error(v, 0) end
    gtoksee(v)
    return v
  end
  if not pcall(function() pre[k] = w end) then return false end
  GTPW = w
  return true
end

-- the value door for sentinels and tokens
local function gvalinstall()
  if GVWRAP ~= nil then return true end
  local lo = rawget(_G, "Loot")
  if lo == nil then
    if said("gval:table") then
      log("lock value: no Loot table in this VM - the permanent-unlock count keeps the client's own answer")
    end
    return false
  end
  local k, f = member(lo, "IsOwned")
  if k == nil or type(f) ~= "function" then
    if said("gval:slot") then
      log("lock value: no Loot.IsOwned in this VM - the permanent-unlock count keeps the client's own answer")
    end
    return false
  end
  local w = function(c, id, ...)
    local ans = nil
    if S.enabled and want(nil) then
      local n = tonumber(id)
      if n ~= nil then
        n = math.floor(n)
        if gsent()[n] == true then ans = 0
        elseif GTOK ~= nil and GTOK[n] == true then ans = 0 end
      end
    end
    local v
    if ans ~= nil then
      v = ans
    else
      v = f(c, id, ...)
      ans = tonumber(v)
    end
    if not G.w.quiet then
      G.w.n = G.w.n + 1
      local k = tonumber(id)
      if k ~= nil then
        k = math.floor(k)
        if G.w.seen[k] == nil and G.w.k < 10 then
          G.w.k = G.w.k + 1
          G.w.seen[k] = G.w.k
          G.w.list[G.w.k] = { id = k, ans = ans }
        end
      end
    end
    return v
  end
  local okset = pcall(function() lo[k] = w end)
  if not okset then
    if said("gval:set") then
      log("lock value: Loot.IsOwned cannot be replaced in this VM - the permanent-unlock count keeps the client's"
        .. " own answer")
    end
    return false
  end
  GVORIG, GVWRAP = f, w
  log("lock value: a permanent-unlock sentinel and the prestige token id answer 0, which is what this profile holds"
    .. " offline - a gobblegum count and every other item keep the client's own answer")
  return true
end

-- says once what this vm is missing
local function gpreflight()
  if fn_of(rawget(_G, "ATTACHMENT"), GPBUNDLE) == nil and said("gbundle:api") then
    log("prestige lock: no ATTACHMENT." .. GPBUNDLE .. " in this VM - a prestige attachment cannot be named,"
      .. " so nothing closes on prestige alone")
  end
  if fn_of(rawget(_G, "WEAPON"), GPREQ) == nil and said("gattach:req") then
    log("prestige lock: no WEAPON." .. GPREQ .. " in this VM - the prestige a reward needs cannot be read, so it"
      .. " keeps the client's own answer")
  end
  if fn_of(rawget(_G, "WEAPON"), GCAMODATA) == nil and said("gcamo:api") then
    log("prestige lock: no WEAPON." .. GCAMODATA .. " in this VM - a camo's weapon cannot be named, so a prestige"
      .. " camo keeps the client's own answer")
  end
  if fn_of(rawget(_G, "PRESTIGE"), GPCAMOS) ~= nil and fn_of(rawget(_G, "WEAPON"), "enumerateweapons") == nil
    and said("gcamo:enum") then
    log("prestige lock: no WEAPON.enumerateweapons in this VM - a camo whose own data names no weapon cannot be tied"
      .. " to one, so it keeps the client's own answer")
  end
  if fn_of(rawget(_G, "PRESTIGE"), GPCAMOS) == nil and said("gcamo:list") then
    log("prestige lock: no PRESTIGE." .. GPCAMOS .. " in this VM - a prestige camo's band cannot be read, so"
      .. " the tiles keep the client's own answer")
  end
  if fn_of(rawget(_G, "PRESTIGE"), GPREF) == nil and said("gattach:prestige") then
    log("prestige lock: PRESTIGE." .. GPREF .. " cannot be read in this VM - the prestige gate keeps the"
      .. " client's own answer")
  end
end

-- is this id tied to a foreign ref
local function gcarried(n)
  local ref = gidref(n)
  if ref == nil or ours(ref) then return false end
  if said("glock:carried:" .. ref) then
    log("lock door: " .. n .. " names " .. clip(ref, 28) .. ", which is not one of ours - left as the client"
      .. " answers it")
  end
  return true
end

-- is this id one the game ships by default
local function gdefault(n)
  local c = G.defcache or {}
  G.defcache = c
  local v = c[n]
  if v ~= nil then return v end
  local f = fcache(rawget(_G, "LOOT"), GNDEFAULT)
  if f == nil then return false end
  local ok, r = pcall(f, n)
  v = ok and r == true
  c[n] = v
  return v
end

local GOPEN = { n = 0, t = {} }

-- the platform question a store id has to pass
local function gusable(n)
  local c = G.usecache or {}
  G.usecache = c
  if c[n] ~= nil then return c[n] end
  local st = rawget(_G, "STORE")
  local _, b = member(st, "Bundles")
  local f = fcache(b, GNUSEABLE)
  if f == nil then
    if said("gopen:platform") then
      log("store open: no STORE.Bundles.IsLootUseableOnCurrentPlatform in this VM - a store id keeps the client's"
        .. " own answer")
    end
    return false
  end
  local ok, v = pcall(f, 0, n)
  if not ok then return false end
  c[n] = v == true or (type(v) == "number" and v ~= 0)
  return c[n]
end

-- a bundle the game itself can describe as an unlock
local function gbuybundle(b)
  if type(b) ~= "table" then return false end
  local f = fcache(rawget(_G, "LOOT"), GNDESC)
  if f == nil then return true end
  local ok, s = pcall(f, b)
  if not ok then return true end
  return type(s) == "string" and s ~= ""
end

-- is this id the store or a pass sells
local function gpurchasable(n)
  local c = G.buycache or {}
  G.buycache = c
  local v = c[n]
  if v ~= nil then return v end
  local yes, ran, miss = false, false, nil
  local _, b = member(rawget(_G, "STORE"), "Bundles")
  local fb = fcache(b, GNBUNDLE)
  if fb == nil then
    miss = "STORE.Bundles." .. GNBUNDLE
  else
    ran = true
    local ok, r = pcall(fb, 0, n)
    if ok and gbuybundle(r) then yes = true end
  end
  local pb = rawget(_G, "PAGEDBATTLEPASS")
  local fp = fcache(pb, GNBPASS)
  local fk = fcache(pb, GNBLCK)
  if fp == nil and fk == nil then
    if miss == nil then miss = "PAGEDBATTLEPASS." .. GNBPASS end
  else
    ran = true
    if fp ~= nil then
      local ok, r = pcall(fp, n)
      if ok and r == true then yes = true end
    end
    if fk ~= nil then
      local ok, r = pcall(fk, n)
      if ok and r == true then yes = true end
    end
  end
  local bm = rawget(_G, "BATTLEMAP")
  local fm = fcache(bm, GNMAP)
  if fm ~= nil then
    ran = true
    local ok, r = pcall(fm, 0, n)
    if ok and r == true then yes = true end
  elseif miss == nil then
    miss = "BATTLEMAP." .. GNMAP
  end
  if not ran then
    if said("cardbuy") then
      log("card lock: purchasable probe missing " .. (miss or GNMAP))
    end
    return false
  end
  c[n] = yes
  return yes
end

-- the card table an ask of this type needs
local function gcardkey(t)
  if t == nil then return nil end
  if t == GTYPE_A or t == GTYPE_C then return "gs" end
  if t == GTYPE_R then return "ret" end
  if t == GTYPE_H or t == GTYPE_E then return "sea" end
  return nil
end

-- loads that table once and again after a gap
local function gcardload(t)
  local k = gcardkey(t)
  if k == nil then return end
  local f = A.loadcard
  if f == nil then return end
  local tried = G.cardTry or {}
  G.cardTry = tried
  local now = S.tick or 0
  local at = tried[k]
  if at ~= nil and now - at < CARD_GAP then return end
  tried[k] = now
  pcall(f, k)
end

-- one line per card the inverted rule locks
local function gcardlog(n, t, buy)
  if S.toggles == nil or S.toggles.log ~= true then return end
  local seen = G.cardSaid or {}
  G.cardSaid = seen
  if seen[n] then return end
  if (G.cardN or 0) >= GCARD_CAP then return end
  seen[n] = true
  G.cardN = (G.cardN or 0) + 1
  log("card lock: " .. G.cardN .. " id=" .. n .. " type=" .. t .. " buy=" .. buy)
end

-- one answer table per epoch for both doors
local function gmemo()
  local m = G.memo
  local rule = S.locks ~= nil and S.locks.open or nil
  if m == nil or m.epoch ~= G.epoch or m.rule ~= rule then
    m = { epoch = G.epoch, rule = rule, lock = {}, open = {} }
    G.memo = m
  end
  return m
end

-- is this a store id the door opens
local function gopen(id)
  local n = tonumber(id)
  if n == nil then return false end
  n = math.floor(n)
  if n < 1 or n > GMAXID then return false end
  if G.unlock ~= nil then return false end
  local m = gmemo().open
  if m[n] ~= nil then return m[n] end
  local t = gtype(n)
  if t == nil then return false end
  local yes = false
  if gtoggle(t) then
    yes = true
  elseif glockedNow(n) and gtypepair() and GTYPE_COS[t] == true and not greward(n) and GEARN[n] ~= true then
    yes = gusable(n)
  end
  m[n] = yes
  if not yes then return false end
  GOPEN.n = GOPEN.n + 1
  GOPEN.t[t] = (GOPEN.t[t] or 0) + 1
  if GOPEN.at == nil then GOPEN.at = S.tick or 0 end
  return true
end

-- says once how many store ids opened by type
local function gopensay()
  if GOPEN.at == nil or GOPEN.said then return end
  if (S.tick or 0) - GOPEN.at < PASS_QUIET then return end
  GOPEN.said = true
  local parts = {}
  for t, c in pairs(GOPEN.t) do parts[#parts + 1] = t .. "=" .. c end
  table.sort(parts)
  log("open " .. GOPEN.n .. " store ids by type: " .. table.concat(parts, " "))
end

-- names the unlock switches once at arm
local function gdvars()
  local parts, seen = {}, {}
  for i = 1, #GTOGN do
    local name = GTOGN[i][2]
    if seen[name] == nil then
      seen[name] = true
      local v = A.dv(name)
      if v == nil or v == "" then v = "-" end
      parts[#parts + 1] = string.gsub(name, "^zm_unlock_", "") .. "=" .. v
    end
  end
  table.sort(parts)
  log("unlock dvars: " .. table.concat(parts, " "))
end

-- is this item locked by us
local function glocked(id)
  gensureWrapped()
  local n = tonumber(id)
  if n == nil then return false end
  n = math.floor(n)
  if n < 1 or n > GMAXID then return false end
  if G.hex == nil or G.noClock then pcall(grefresh) end
  if G.unlock ~= nil then return false end
  gtoggles()
  local t = gtype(n)
  gcardload(t)
  local m = gmemo().lock
  local e = m[n]
  if e ~= nil then return e.locked end
  local bit = 0
  if glockedNow(n) then bit = 1 end
  if t == nil and bit == 1 and GLOCKSMITH[n] == true and gcarried(n) then return false end
  if t == nil then
    if bit == 1 and GLOCKSMITH[n] == true then return true end
    return false
  end
  local r = grec(n)
  local live = false
  if GEARN[n] ~= true then
    if t == GTYPE_A then
      if gattach(n) then return true end
      live = r.req ~= false
    elseif t == GTYPE_C then
      if gcamo(n) then return true end
      live = r.band ~= false
    end
  end
  if gtoggle(t) then
    m[n] = { locked = false }
    return false
  end
  local locked
  if GTYPE_PC ~= nil and t == GTYPE_PC then
    local buy = 0
    locked = bit == 1 and not gdefault(n) and not gcarried(n)
    if locked and gpurchasable(n) then buy, locked = 1, false end
    if locked and not greward(n) then gcardlog(n, t, buy) end
  else
    locked = bit == 1 and greward(n) and not gdefault(n) and not gcarried(n)
  end
  if (t == GTYPE_C or t == GTYPE_R) and glogging() then gdoor(n, t, bit, locked) end
  if not live then m[n] = { locked = locked } end
  return locked
end

-- drops every answer when the game mode moves
local function gmodeclear()
  local f = G.modef
  if f == nil then
    if G.n % 32 ~= 1 then return end
    f = fn_of(rawget(_G, "Engine"), GNGAME)
    G.modef = f
    if f == nil then return end
  end
  local ok, v = pcall(f)
  if not ok then return end
  v = tostring(v)
  if G.mode == nil then
    G.mode = v
  elseif v ~= G.mode then
    G.mode, G.pcamo, G.camomap, G.memo, G.camoTry = v, {}, nil, nil, nil
    for _, r in pairs(G.rec or {}) do r.band = nil end
  end
end

-- the lock side of the tick
local function gtick()
  if not want(nil) then return end
  G.n = G.n + 1
  pcall(gtoggles)
  pcall(gcamopass)
  pcall(gopensay)
  pcall(gmodeclear)
  if S.tracker ~= nil and not S.tracker.done and G.n % 32 == 1 then pcall(S.tracker.install) end
  if G.wrappers < 2 then
    if G.gaveUp then return end
    pcall(ginstall)
    if G.wrappers >= 2 then
      pcall(grefresh)
    else
      local m = gmissing()
      log("g11 waiting for " .. (#m > 0 and table.concat(m, " / ") or "the isunlockedwithid slot"))
      if G.n >= GMAX_TICKS then
        G.gaveUp = true
        log("g11 gave up wrapping - " .. (#m > 0 and table.concat(m, " / ") or "the isunlockedwithid slot"))
      end
    end
  else
    if G.n % GPOLL_TICKS == 0 then
      pcall(grefresh)
      pcall(gvalinstall)
      pcall(gtokwatch)
    end
  end
end

-- arms every lock piece at load
local function arm_locks()
  log("g11 armed (scope locksmith, " .. S.scopeN .. " ids)")
  G.defcache, G.usecache, G.rec = {}, {}, {}
  G.buycache, G.cardSaid, G.cardN, G.cardTry = {}, {}, 0, {}
  pcall(ginstall)
  if G.wrappers >= 2 then pcall(grefresh) end
  pcall(gpreflight)
  pcall(gdvars)
  pcall(gvalinstall)
  pcall(gtokwatch)
  if S.tracker ~= nil then pcall(S.tracker.install) end
end

S.locks = { answer = glocked, open = gopen, typepair = gtypepair, arm = arm_locks, tick = gtick }
A.answer = function(id) return glocked(id) end
S.locks.view = function() return GTYPE_A, GTYPE_C, GSENT_N, GVORIG, GVWRAP, GTOK end
A.gsent, A.gtype, A.gattach = gsent, gtype, gattach
A.gbundle, A.gcamoref, A.gcamomap = gbundle, gcamoref, gcamomap
A.gcamoload, A.gcamoprog, A.gfield, A.gprest = gcamoload, gcamoprog, gfield, gprest
S.hooks.locks = gtick
S.hooks.arm = arm_locks
S.probes.prison = function() return type(A.log) == "function" and type(S.g11) == "table" end

local dp = rawget(_G, "DebugPrint") or rawget(_G, "print")
if type(dp) == "function" then pcall(dp, "progression_tuning: part prison armed") end

if A.ready ~= nil then A.ready() end
