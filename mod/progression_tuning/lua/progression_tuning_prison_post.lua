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
local function want(...) return A.want(...) end
local function ours(...) return A.ours(...) end

local G = S.g11
local GLOCKSMITH = S.scope
local GMAXID = 0x3FFFF
local CAMO_SCAN_GAP = 8
-- the client own weapon table size
local GCAMO_CAP = 2048
local PASS_QUIET = 8
local GMAX_TICKS = 480
local GPOLL_TICKS = 8

local function grefresh(...) return A.refresh(...) end
local function gsummary(...) return A.sum(...) end
local function glockedNow(...) return A.bit(...) end
local function ginstall(...) return A.door_install(...) end
local function gmissing(...) return A.door_missing(...) end
local function gensureWrapped(...) return A.door_retry(...) end

local GNTYPE = "gettypeforid"
local GTYPES = "itemTypes"
local GDOOR_CAP = 24
local GTYPE_A, GTYPE_C = nil, nil

-- the client own attachment and camo types
local function gtypepair()
  if GTYPE_A ~= nil then return true end
  local lo = rawget(_G, "LOOT")
  if type(lo) ~= "table" then return false end
  local _, it = member(lo, GTYPES)
  if type(it) ~= "table" then return false end
  local _, a = member(it, "ATTACHMENT")
  local _, c = member(it, "CAMO")
  local na, nc = tonumber(a), tonumber(c)
  if na == nil or nc == nil then return false end
  GTYPE_A, GTYPE_C = na, nc
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
  local f = fn_of(rawget(_G, "LOOT"), GNTYPE)
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
  local f = fn_of(rawget(_G, "ATTACHMENT"), GPBUNDLE)
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

-- a prestige attachment waits for its prestige
local function gattach(n)
  local b = gbundle(n)
  if b == nil or b == false then return false end
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
    return false
  end
  local req = nil
  local okd, d = pcall(reqf, ref, n)
  if okd and type(d) == "table" then req = gfield(d, "prestige") end
  if req == nil then return false end
  local have = gprest(ref)
  if have == nil then
    if said("gattach:prestige") then
      log("prestige lock: PRESTIGE." .. GPREF .. " cannot be read in this VM - the prestige gate keeps the"
        .. " client's own answer")
    end
    return false
  end
  local locked = have < req
  if glogging() then
    gpline("prestige id=" .. n .. " tier=" .. req .. " prestige=" .. have
      .. " answer=" .. (locked and "locked" or "open"))
  end
  return locked
end

-- the weapon a camo own data names
local function gcamoref(n)
  local c = G.camoref[n]
  if c ~= nil then return c end
  local f = fn_of(rawget(_G, "WEAPON"), GCAMODATA)
  if f == nil then
    if said("gcamo:api") then
      log("prestige lock: no WEAPON." .. GCAMODATA .. " in this VM - a camo's weapon cannot be named, so a prestige"
        .. " camo keeps the client's own answer")
    end
    return nil
  end
  local ok, b = pcall(f, n)
  if not ok or type(b) ~= "table" then return nil end
  local _, ref = member(b, "weaponref")
  if type(ref) ~= "string" or ref == "" then return nil end
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

-- one weapon own prestige camo ladder
local function gcamoload(ref)
  local pr = gprest(ref)
  local mx = gnumber(fn_of(rawget(_G, "PRESTIGE"), GPMAX), ref)
  local t = G.pcamo[ref]
  if t ~= nil and t.p == pr and t.d == mx then return t.list end
  local list, n = {}, 0
  if not ours(ref) then return list end
  local f = fn_of(rawget(_G, "PRESTIGE"), GPCAMOS)
  if f == nil then
    if said("gcamo:list") then
      log("prestige lock: no PRESTIGE." .. GPCAMOS .. " in this VM - a prestige camo's band cannot be read, so"
        .. " the tiles keep the client's own answer")
    end
    return list
  end
  local ok, g1, g2, g3 = pcall(f, ref)
  if ok then
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
  end
  if pr ~= nil and n > 0 and mx ~= nil and mx > 0 then G.pcamo[ref] = { p = pr, d = mx, list = list } end
  return list
end

-- how far a camo band has come
local function gcamoprog(e, ref)
  local pr = gprest(ref)
  if pr == nil then return nil end
  local lv = gnumber(fn_of(rawget(_G, "PROGRESSION"), GPLEVEL), 0, ref)
  if lv == nil then return nil end
  local mx = gnumber(fn_of(rawget(_G, "PRESTIGE"), GPMAX), ref)
  if mx == nil then return nil end
  local sp, tp = gfield(e, "startPrestige") or 0, gfield(e, "targetPrestige") or 0
  local sl, tl = gfield(e, "startLevel") or 0, gfield(e, "targetLevel") or 0
  local p = 0
  if sp < pr then
    p = 1
  elseif pr == sp and tl > 0 then
    p = lv / tl
  end
  if mx <= sp then
    if tl < lv then
      p = 1
    elseif lv < sl then
      p = 0
    elseif lv < tl and sl < lv then
      if mx <= pr and tl > sl then
        p = (lv - sl) / (tl - sl)
      else
        p = 0
      end
    end
  end
  return p, sp, tp, sl, tl, pr, lv
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

-- a prestige camo waits for its band
local function gcamo(n)
  if G.askSeen[n] == nil then G.askSeen[n] = true end
  local ref, e = gcamoref(n), nil
  if ref ~= nil then
    e = gcamoload(ref)[n]
  else
    local m = gcamomap()[n]
    if m ~= nil then
      ref, e = m.ref, m.e
    end
  end
  if ref ~= nil and not ours(ref) then
    if G.passSeen[n] == nil then
      G.passSeen[n] = true
      G.passAt = S.tick or 0
    end
    if S.toggles ~= nil and S.toggles.log and said("gcamo:carried:" .. n) then
      log("prestige lock: " .. n .. " belongs to " .. clip(ref, 28) .. ", which is not one of ours - no band is"
        .. " computed and it keeps the client's own answer")
    end
    return false
  end
  if ref == nil or e == nil then
    if G.passSeen[n] == nil then
      G.passSeen[n] = true
      G.passAt = S.tick or 0
    end
    if S.toggles ~= nil and S.toggles.log and said("gcamo:none:" .. n) then
      log("prestige lock: " .. n .. " names no weapon in its own data and is in no weapon's prestige ladder in this"
        .. " VM - it keeps the client's own answer")
    end
    return false
  end
  local p, sp, tp, sl, tl, pr, lv = gcamoprog(e, ref)
  if p == nil then return false end
  local locked = p < 1
  if glogging() then
    gpline("prestige camo id=" .. n .. " ref=" .. ref .. " start=" .. sp .. "/" .. sl
      .. " to=" .. tp .. "/" .. tl .. " prestige=" .. pr .. " level=" .. lv
      .. " answer=" .. (locked and "locked" or "open"))
  end
  return locked
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

-- is this item locked by us
local function glocked(id)
  gensureWrapped()
  local n = tonumber(id)
  if n == nil then return false end
  n = math.floor(n)
  if n < 1 or n > GMAXID then return false end
  grefresh()
  if G.unlock ~= nil then return false end
  local bit = 0
  if glockedNow(n) then bit = 1 end
  local t = gtype(n)
  if t == nil and bit == 1 and GLOCKSMITH[n] == true and gcarried(n) then return false end
  if t == nil then
    if bit == 1 and GLOCKSMITH[n] == true then return true end
    return false
  end
  if t == GTYPE_A then
    if gattach(n) then return true end
  elseif t == GTYPE_C then
    if gcamo(n) then return true end
  end
  local locked = (bit == 1 and (t == GTYPE_A or t == GTYPE_C) and not gcarried(n))
  if t == GTYPE_C and glogging() then gdoor(n, t, bit, locked) end
  return locked
end

-- the lock side of the tick
local function gtick()
  if not want(nil) then return end
  G.n = G.n + 1
  pcall(gcamopass)
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
  elseif G.n % GPOLL_TICKS == 0 then
    pcall(grefresh)
    pcall(gsummary)
    pcall(gvalinstall)
    pcall(gtokwatch)
  end
end

-- arms every lock piece at load
local function arm_locks()
  log("g11 armed (scope locksmith, " .. S.scopeN .. " ids)")
  pcall(ginstall)
  if G.wrappers >= 2 then pcall(grefresh) end
  pcall(gpreflight)
  pcall(gvalinstall)
  pcall(gtokwatch)
  if S.tracker ~= nil then pcall(S.tracker.install) end
end

S.locks = { answer = glocked, typepair = gtypepair, arm = arm_locks, tick = gtick }
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
