local PART = "diag"

local S = rawget(_G, "ProgressionTuning")
if type(S) ~= "table" then
  S = { parts = {}, hooks = {}, probes = {}, api = {}, g11 = {}, scope = {} }
  rawset(_G, "ProgressionTuning", S)
end
if S.parts[PART] == true then return end
S.parts[PART] = true
local A = S.api
local function log(...) return A.log(...) end
local function member(...) return A.member(...) end
local function fn_of(...) return A.fn_of(...) end
local function call(...) return A.call(...) end
local function want(...) return A.want(...) end
local function csv_file(...) return A.csv_file(...) end
local function toggle(...) return A.toggle(...) end

local G = S.g11
local GLOCKSMITH = S.scope

local function lockview()
  local l = S.locks
  l = l ~= nil and l.view or nil
  if l == nil then return nil end
  return l()
end

local RC1D = "rc1diag"
-- the trial diagnostic block
local RC1D_CAP = 200
local RC1D_ENTRIES = 12
local RC1D_Q7_CAP = 8
local RC1D_DAILY = { 55415, 53334, 53310, 55402 }
local RC1D_WEEKLY = { 60325, 60326, 60338, 60366 }
local RC1D_REF = "sat_pi_alcor"
local RC1D_IDS = {
  { 126608, "P1 attachment" },
  { 126605, "level attachment" },
  { 126615, "level attachment" },
  { 126609, "level attachment" },
  { 140475, "armory muzzle" },
  { 126626, "armory muzzle" },
  { 125070, "armory optic" },
  { 125186, "weapon" },
  { 107478, "P1 camo" },
  { 107467, "P2 camo" },
  { 132741, "master100 camo" },
  { 132703, "master150 camo" },
  { 132769, "master200 camo" },
  { 107480, "master249 camo" },
  { 131545, "tier1 char camo" },
  { 131708, "tier2 tundra camo" },
  { 131627, "tier3 camo" },
  { 131560, "tier4 camo" },
  { 131607, "tier5 camo" },
  { 131613, "tier6 camo" },
  { 131652, "tier7 camo" },
  { 131543, "tier8 camo" },
  { 131563, "tier9 camo" },
}
local RC1D_PRED = { 126605, 126608, 140475, 107478 }
local RC1D_CAMO = { 107478, 107467 }
local RC1D_TYPE = { 126605, 131708, 125186, 107478 }
local RC1D_PCAMO = { 107478, 107467, 132741, 132703, 132769, 107480 }
local RC1D_LOOK = 400
local RC1D_PR, RC1D_LO

local function rc1d_capture()
  if RC1D_PR ~= nil or RC1D_LO ~= nil then return end
  local d = A.door0
  if type(d) ~= "table" then return end
  RC1D_PR, RC1D_LO = d.pr, d.lo
end
local RC1D_ON = false

-- a short printable answer
local function rc1d_txt(v)
  if type(v) == "table" then
    local c = 0
    pcall(function() for _ in pairs(v) do c = c + 1 end end)
    return "table(" .. tostring(c) .. ")"
  end
  local ok, s = pcall(tostring, v)
  if not ok or s == nil then return "?" end
  if #s > 44 then return string.sub(s, 1, 44) end
  return s
end

-- one probe as name equals answer
local function rc1d_clause(name, f, ...)
  if type(f) ~= "function" then return name .. "=absent" end
  local ok, v = pcall(f, ...)
  if not ok then return name .. "=raised" end
  return name .. "=" .. type(v) .. ":" .. rc1d_txt(v)
end

-- a table value by number or name
local function rc1d_get(t, key)
  if type(t) ~= "table" then return nil end
  local ok, v = pcall(function() return t[key] end)
  if ok and v ~= nil then return v end
  ok, v = pcall(function() return t[tostring(key)] end)
  if ok and v ~= nil then return v end
  local n = tonumber(key)
  if n ~= nil and n ~= key then
    ok, v = pcall(function() return t[n] end)
    if ok and v ~= nil then return v end
  end
  return nil
end

-- a table field by name only
local function rc1d_field(t, name)
  if type(t) ~= "table" then return nil end
  local ok, v = pcall(function() return t[name] end)
  if ok and v ~= nil then return v end
  local _, w = member(t, name)
  return w
end

-- finds a hashed member by its bytes
local function rc1d_hex(t, hex)
  if type(t) ~= "table" then return nil end
  local want = string.gsub(string.upper(hex), "^0+", "")
  local found = nil
  pcall(function()
    for k, v in pairs(t) do
      if found == nil and type(v) == "function" then
        local s = string.gsub(string.upper(tostring(k)), "[^0-9A-F]", "")
        s = string.gsub(s, "^0+", "")
        if s == want then found = v end
      end
    end
  end)
  return found
end

-- a csv table by name or hash
local function rc1d_csv(name)
  local csv = rawget(_G, "CSV")
  if type(csv) ~= "table" then return nil end
  local t = csv[name]
  if type(t) == "table" then return t end
  local _, v = member(csv, name)
  if type(v) == "table" then return v end
  return nil
end

-- the raw bytes behind a hash string
local function rc1d_bytes(hex)
  if type(hex) ~= "string" then return nil end
  local h = string.gsub(string.upper(hex), "^0*", "")
  h = string.rep("0", 16 - string.len(h)) .. h
  local out = {}
  local i = 8
  while i >= 1 do
    local v = tonumber(string.sub(h, i * 2 - 1, i * 2), 16)
    if v == nil then return nil end
    out[#out + 1] = string.char(v)
    i = i - 1
  end
  return table.concat(out)
end

-- whatever progress field the record holds
local function rc1d_prog(r)
  if type(r) ~= "table" then return 0 end
  local prog = rc1d_field(r, "progress")
  if type(prog) ~= "table" then return 0 end
  return tonumber(rc1d_field(prog, "default")) or tonumber(rc1d_field(prog, "progress"))
    or tonumber(rc1d_field(prog, "xp")) or 0
end

-- the client own record again for diag
local function rc1d_rec(id)
  local f = S.live.rec.orig
  if f == nil then
    local OC = rawget(_G, "OnlineChallenges")
    if type(OC) == "table" then
      local _, cur = member(OC, "getchallengeprogress")
      if type(cur) == "function" and cur ~= S.live.rec.ours then f = cur end
    end
  end
  if type(f) ~= "function" then return nil end
  local ok, r = pcall(f, 0, id)
  if ok then return r end
  return nil
end

-- one challenge table probed whole
local function rc1d_chal(tag, tbl, put, rec, want)
  if type(tbl) ~= "table" then put(tag .. " table=absent") return end
  local cols = rc1d_field(tbl, "cols")
  if type(cols) ~= "table" then put(tag .. " cols=absent") return end
  local f = fn_of(rawget(_G, "StringTable"), "tablereadallrows")
  if f == nil then put(tag .. " rows=absent") return end
  local idcol = rc1d_field(cols, "id")
  local ok, rows = pcall(f, csv_file(tbl), { id = idcol, ref = rc1d_field(cols, "ref"),
    amount = rc1d_field(cols, "amount") }, idcol)
  if not ok or type(rows) ~= "table" then put(tag .. " rows=none") return end
  local seen, found, hits, seenid, hitid = 0, 0, {}, {}, {}
  local first = nil
  pcall(function()
    for k, row in pairs(rows) do
      seen = seen + 1
      local id = nil
      if type(row) == "table" then id = tonumber(rc1d_field(row, "id")) end
      if id == nil then id = tonumber(k) end
      if id ~= nil then
        seenid[id] = true
        local r = rec(id)
        local pr = rc1d_prog(r)
        if first == nil then first = { id = id, rec = r } end
        if pr > 0 then
          found = found + 1
          if #hits < RC1D_Q7_CAP then
            hitid[id] = true
            hits[#hits + 1] = { id = id, rec = r, progress = pr,
              amount = rc1d_field(row, "amount"), ref = rc1d_field(row, "ref") }
          end
        end
      end
    end
  end)
  put(tag .. " rows=" .. seen .. " withprogress=" .. found .. " shown=" .. #hits)
  local i = 1
  while i <= #hits do
    local h = hits[i]
    put(tag .. " " .. rc1d_txt(h.id) .. " progress=" .. rc1d_txt(h.progress)
      .. " amount=" .. rc1d_txt(h.amount) .. " status=" .. rc1d_txt(rc1d_field(h.rec, "status"))
      .. " ref=" .. rc1d_txt(h.ref))
    i = i + 1
  end
  if first ~= nil and type(first.rec) == "table" then
    local names = {}
    pcall(function()
      for k in pairs(first.rec) do names[#names + 1] = rc1d_txt(k) end
    end)
    local pnames = {}
    local pg = rc1d_field(first.rec, "progress")
    if type(pg) == "table" then
      pcall(function()
        for k in pairs(pg) do pnames[#pnames + 1] = rc1d_txt(k) end
      end)
    end
    put(tag .. " rec " .. rc1d_txt(first.id) .. " fields=" .. table.concat(names, ",")
      .. (type(pg) == "table" and (" pfields=" .. table.concat(pnames, ",")) or " pfields=none"))
  end
  if type(want) == "table" then
    local w, shown = 1, 0
    while w <= #want do
      local id = want[w]
      if seenid[id] == true then
        shown = shown + 1
        if hitid[id] ~= true then
          local r = rec(id)
          put(tag .. " want " .. id .. " progress=" .. rc1d_txt(rc1d_prog(r))
            .. " rec=" .. (type(r) == "table" and "table" or "absent"))
        end
      end
      w = w + 1
    end
    if shown == 0 then put(tag .. " want=none") end
  end
end

-- watches the camo datasource once
local function rc1d_watch()
  if G.q.done then return true end
  local WC = rawget(_G, "WEAPON_CAMO")
  if type(WC) ~= "table" then return false end
  local k, f = member(WC, "updatedatasourcewithchallengedata")
  if k == nil or type(f) ~= "function" then return false end
  local w = function(c, ds, list, ...)
    G.q.calls = G.q.calls + 1
    local cnt, have = nil, nil
    if type(ds) == "table" then
      local _, cm = member(ds, "count")
      if type(cm) == "table" then
        local gv = fn_of(cm, "GetValue")
        if gv ~= nil then
          local okv, v = pcall(gv, cm, c)
          if okv then have = tonumber(v) end
        end
      elseif type(cm) == "number" then
        have = cm
      end
    end
    if type(list) == "table" then
      cnt = #list
      local j = 1
      while j <= cnt and #G.q.rows < 6 do
        local own = nil
        local lid = rc1d_field(list[j], "bundleLootID")
        local getref = fn_of(rawget(_G, "LOOT"), "GetItemRef")
        local getcam = fn_of(rawget(_G, "WEAPON"), "getcamodataforref")
        if lid ~= nil and getref ~= nil and getcam ~= nil then
          local ok1, r = pcall(getref, lid)
          if ok1 and r ~= nil then
            local ok2, cd = pcall(getcam, r)
            if ok2 and type(cd) == "table" then
              local _, v = member(cd, "camochallengeweaponref")
              if type(v) == "string" and v ~= "" then own = v end
            end
          end
        end
        G.q.rows[#G.q.rows + 1] = { id = rc1d_field(list[j], "id"), own = own }
        j = j + 1
      end
    end
    G.q.last = { n = cnt, ds = have }
    return f(c, ds, list, ...)
  end
  if not pcall(function() WC[k] = w end) then return false end
  G.q.done = true
  return true
end

-- prints the one diag block
local function rc1diag_run()
  local on, how = toggle("pt_diag", false)
  RC1D_ON = on
  S.diag = on
  if not on then return end
  local KIND_WEAPON = 398
  local GMAXID = 0x3FFFF
  local GPREQ = "getweaponprestigeattachmentdetails"
  local H = rawget(_G, "xhash")
  local gsent, gtype, gattach, gbundle = A.gsent, A.gtype, A.gattach, A.gbundle
  local gcamoref, gcamomap, gcamoload = A.gcamoref, A.gcamomap, A.gcamoload
  local gcamoprog, gfield, gprest = A.gcamoprog, A.gfield, A.gprest
  local glockedNow, glocked, clip, count_passed = A.bit, A.answer, A.clip, A.count_passed
  rc1d_capture()
  local GTYPE_A, GTYPE_C, GSENT_N, GVORIG, GVWRAP, GTOK = lockview()
  local S5 = S.tracker or {}
  local out, n, full = {}, 0, false
  -- appends one diag line
  local function put(t)
    if n >= RC1D_CAP - 2 then full = true return end
    n = n + 1
    out[n] = t
  end
  local LOOTT = rawget(_G, "LOOT")
  local PRG = rawget(_G, "PROGRESSION")
  local PRE = rawget(_G, "PRESTIGE")
  local EN = rawget(_G, "Engine")
  local WC = rawget(_G, "WEAPON_CAMO")
  local wcget = fn_of(WC, "getcamochallengefromlootid")
  local wcref = fn_of(WC, "getweaponreffromchallengeref")
  local prget = fn_of(PRE, "getweaponprestigecamos")
  local i = 1
  while i <= #RC1D_IDS do
    local id = RC1D_IDS[i][1]
    local bit = 0
    if glockedNow(id) then bit = 1 end
    local scope = 0
    if GLOCKSMITH[id] == true then scope = 1 end
    local ans = false
    local okg, a = pcall(glocked, id)
    if okg and a == true then ans = true end
    put("Q1 " .. id .. " " .. RC1D_IDS[i][2] .. " bit=" .. bit .. " scope=" .. scope
      .. " mod=" .. tostring(ans))
    i = i + 1
  end
  i = 1
  while i <= #RC1D_IDS do
    local id = RC1D_IDS[i][1]
    put("Q2 " .. id .. " " .. rc1d_clause("progression", RC1D_PR, 0, id)
      .. " " .. rc1d_clause("loot", RC1D_LO, 0, id))
    i = i + 1
  end
  local owned = GVORIG
  if owned == nil then owned = fn_of(rawget(_G, "Loot"), "IsOwned") end
  local isdef = fn_of(LOOTT, "isitemdefault")
  local pound = fn_of(rawget(_G, "PROXY_LOOT"), "IsOwned")
  local _, bundles = member(rawget(_G, "STORE"), "Bundles")
  local plat = fn_of(bundles, "IsLootUseableOnCurrentPlatform")
  local net = fn_of(EN, "IsNetworkConnected")
  local dw = fn_of(EN, "IsUserSignedInToDemonware")
  i = 1
  while i <= #RC1D_PRED do
    local id = RC1D_PRED[i]
    put("Q2 " .. id .. " " .. rc1d_clause("net", net)
      .. " " .. rc1d_clause("dw", dw, 0)
      .. " " .. rc1d_clause("proxyowned", pound, 0, id)
      .. " " .. rc1d_clause("platform", plat, 0, id)
      .. " " .. rc1d_clause("default", isdef, id))
    i = i + 1
  end
  local mdget = fn_of(LOOTT, "getprogressionitemmetadata")
  local md = nil
  if mdget ~= nil then
    local okm, v = pcall(mdget)
    if okm and type(v) == "table" then md = v end
  end
  local perm1 = rc1d_hex(LOOTT, "7357FE84FAD7DD18")
  local perm2 = rc1d_hex(LOOTT, "9BFFEB098B954D5B")
  local permn = fn_of(LOOTT, "IsItemPermanentlyUnlocked")
  local all = fn_of(PRG, "ShouldUnlockAll")
  if all == nil then all = fn_of(LOOTT, "ShouldUnlockAll") end
  local q3 = { 126615, 126608 }
  i = 1
  while i <= #q3 do
    local id = q3[i]
    local prow = nil
    if md ~= nil then prow = rc1d_get(md, id) end
    local sent = nil
    if type(prow) == "table" then sent = rc1d_field(prow, "sentinel_id") end
    put("Q3 " .. id .. " meta=" .. tostring(prow ~= nil) .. " sentinel=" .. rc1d_txt(sent))
    if sent ~= nil then
      put("Q3 " .. id .. " cand_a " .. rc1d_clause("loot_owned", owned, 0, sent))
    else
      put("Q3 " .. id .. " cand_a sentinel=absent")
    end
    put("Q3 " .. id .. " cand_b " .. rc1d_clause("should_unlock_all", all))
    put("Q3 " .. id .. " cand_c " .. rc1d_clause("label", perm1, id, 0)
      .. " " .. rc1d_clause("second", perm2, id, 0)
      .. " " .. rc1d_clause("named", permn, id, 0))
    i = i + 1
  end
  local ref = RC1D_REF
  put("Q4 " .. ref .. " " .. rc1d_clause("prestige", fn_of(PRE, "getweaponprestigelevel"), 0, ref)
    .. " " .. rc1d_clause("tokens", fn_of(PRE, "getweaponprestigetokenscount"), 0, ref)
    .. " " .. rc1d_clause("maxprestige", fn_of(PRE, "getmaxweaponprestigelevel"), ref))
  put("Q4 " .. ref .. " " .. rc1d_clause("level", fn_of(PRG, "GetWeaponLevel"), 0, ref)
    .. " " .. rc1d_clause("maxlevel", fn_of(PRG, "getmaxweaponlevel"), ref))
  local mx = fn_of(PRG, "getweaponlevelminxp")
  if mx ~= nil then
    put("Q4 " .. ref .. " " .. rc1d_clause("rung1", mx, 0, ref, 1)
      .. " " .. rc1d_clause("rung2", mx, 0, ref, 2)
      .. " " .. rc1d_clause("rung3", mx, 0, ref, 3))
  else
    put("Q4 " .. ref .. " rungs=absent")
  end
  local wd = fn_of(rawget(_G, "WEAPON"), "getweapondataforref")
  local wdat = nil
  if wd ~= nil then
    local okw, d = pcall(wd, ref)
    if okw and type(d) == "table" then wdat = d end
  end
  if wdat == nil then
    put("Q4 " .. ref .. " weaponData=absent")
  else
    local wp = rc1d_field(wdat, "weaponProgression")
    local cnt = 0
    if type(wp) == "table" then pcall(function() for _ in pairs(wp) do cnt = cnt + 1 end end) end
    put("Q4 " .. ref .. " weaponProgression=" .. type(wp) .. "(" .. cnt .. ")")
  end
  local rr = rc1d_rec(68333)
  local rx = "nil"
  if type(rr) == "table" then
    local rp = rc1d_field(rr, "progress")
    if type(rp) == "table" then rx = rc1d_txt(rc1d_field(rp, "xp")) end
  end
  put("Q4 " .. ref .. " row=68333 xp=" .. rx)
  i = 1
  while i <= #RC1D_CAMO do
    local id = RC1D_CAMO[i]
    local locked = "unlock=absent"
    if type(RC1D_LO) == "function" then
      local okl, v = pcall(RC1D_LO, 0, id)
      if okl then locked = "unlock=" .. type(v) .. ":" .. tostring(v)
        .. " is_locked=" .. tostring(v ~= true) end
    end
    put("Q5 " .. id .. " " .. locked)
    local b = "bundle=absent"
    if prget ~= nil then
      local okb, g1, g2, g3 = pcall(prget, ref)
      if okb then
        local groups = { g1, g2, g3 }
        local gi = 1
        while gi <= 3 do
          local g = groups[gi]
          if b == "bundle=absent" and type(g) == "table" then
            local j = 1
            while j <= #g and b == "bundle=absent" do
              local e = g[j]
              local lid = nil
              if type(e) == "table" then
                local cb = rc1d_field(e, "camoBundle")
                if type(cb) == "table" then lid = rc1d_field(cb, "lootid") end
              end
              if tonumber(lid) == id then
                b = "prestige=" .. rc1d_txt(rc1d_field(e, "startPrestige"))
                  .. " start=" .. rc1d_txt(rc1d_field(e, "startLevel"))
                  .. " to=" .. rc1d_txt(rc1d_field(e, "targetPrestige"))
                  .. "/" .. rc1d_txt(rc1d_field(e, "targetLevel"))
              end
              j = j + 1
            end
          end
          gi = gi + 1
        end
      end
    end
    put("Q5 " .. id .. " " .. b)
    local cc = "chain=absent"
    if wcget ~= nil then
      local okc, e = pcall(wcget, 0, id)
      if okc and type(e) == "table" then
        cc = "chain id=" .. rc1d_txt(rc1d_field(e, "id"))
          .. " progress=" .. rc1d_txt(rc1d_field(e, "progress"))
          .. " amount=" .. rc1d_txt(rc1d_field(e, "amount"))
          .. " np=" .. rc1d_txt(rc1d_field(e, "normalizedProgress"))
          .. " loot=" .. rc1d_txt(rc1d_field(e, "lootId"))
      elseif okc then
        cc = "chain=none"
      end
    end
    put("Q5 " .. id .. " " .. cc)
    i = i + 1
  end
  local b9 = gbundle(126608)
  local ispr9, owner9, req9 = "absent", "nil", "nil"
  if b9 ~= nil then
    local _, v9 = member(b9, "isprestige")
    ispr9 = rc1d_txt(v9)
    local _, o9 = member(b9, "weaponunlock")
    if type(o9) == "string" then
      owner9 = o9
      local rf9 = fn_of(rawget(_G, "WEAPON"), GPREQ)
      if rf9 ~= nil then
        local okd9, d9 = pcall(rf9, o9, 126608)
        if okd9 and type(d9) == "table" then req9 = rc1d_txt(rc1d_field(d9, "prestige")) end
      end
    end
  end
  local have9 = nil
  if owner9 ~= "nil" then have9 = gprest(owner9) end
  put("Q9 126608 isprestige=" .. ispr9 .. " owner=" .. owner9 .. " req=" .. req9
    .. " prestige=" .. rc1d_txt(have9) .. " answer=" .. rc1d_txt(gattach(126608)))
  i = 1
  while i <= #RC1D_PCAMO do
    local id = RC1D_PCAMO[i]
    local ref, e9 = gcamoref(id), nil
    local src = " src=own"
    if ref ~= nil then
      e9 = gcamoload(ref)[id]
    else
      local m9 = gcamomap()[id]
      if m9 ~= nil then
        ref, e9, src = m9.ref, m9.e, " src=ladder"
      end
    end
    if ref == nil then
      put("Q9 " .. id .. " camo weapon=absent ladder=" .. (G.camomap ~= nil and "built" or "none") .. " answer=false")
    elseif e9 == nil then
      put("Q9 " .. id .. " camo weapon=" .. ref .. src .. " entry=absent answer=false")
    else
      local p9, sp9, tp9, sl9, tl9, pr9, lv9 = gcamoprog(e9, ref)
      put("Q9 " .. id .. " camo weapon=" .. ref .. src .. " start=" .. rc1d_txt(sp9) .. "/" .. rc1d_txt(sl9)
        .. " to=" .. rc1d_txt(tp9) .. "/" .. rc1d_txt(tl9) .. " prestige=" .. rc1d_txt(pr9)
        .. " level=" .. rc1d_txt(lv9) .. " prog=" .. rc1d_txt(p9) .. " answer=" .. tostring(p9 ~= nil and p9 < 1))
    end
    i = i + 1
  end
  gsent()
  local tokid9 = nil
  local tlf9 = fn_of(PRE, "getweaponprestigetokenlootid")
  if tlf9 ~= nil then
    local okt9, vt9 = pcall(tlf9, RC1D_REF)
    if okt9 then tokid9 = tonumber(vt9) end
  end
  local ntok9 = 0
  if GTOK ~= nil then pcall(function() for _ in pairs(GTOK) do ntok9 = ntok9 + 1 end end) end
  put("Q10 sentinels=" .. GSENT_N .. " tokens=" .. ntok9
    .. " orig=" .. (type(GVORIG) == "function" and "fn" or "absent") .. " wrapped=" .. tostring(GVWRAP ~= nil))
  -- the value door before and after
  local q10 = function(id, tag)
    local a, b = "nil", "nil"
    G.w.quiet = true
    if GVORIG ~= nil then
      local ok1, v1 = pcall(GVORIG, 0, id)
      if ok1 then a = rc1d_txt(v1) end
    end
    local cur = fn_of(rawget(_G, "Loot"), "IsOwned")
    if cur ~= nil then
      local ok2, v2 = pcall(cur, 0, id)
      if ok2 then b = rc1d_txt(v2) end
    end
    G.w.quiet = false
    put("Q10 " .. id .. " " .. tag .. " orig=" .. a .. " answered=" .. b)
  end
  q10(132396, "sentinel")
  if tokid9 ~= nil then q10(tokid9, "token") else put("Q10 token=absent") end
  put("Q10 calls=" .. G.w.n .. " seen=" .. G.w.k)
  local jw = 1
  while jw <= G.w.k do
    put("Q10 call id=" .. G.w.list[jw].id .. " ans=" .. rc1d_txt(G.w.list[jw].ans))
    jw = jw + 1
  end
  G.w.quiet = true
  put("Q10 item 126615 " .. rc1d_clause("item", fn_of(rawget(_G, "LOOT"), "IsItemPermanentlyUnlocked"), 126615, 0))
  G.w.quiet = false
  rc1d_watch()
  put("Q11 calls=" .. G.q.calls .. " n=" .. ((G.q.last ~= nil and G.q.last.n) or "nil")
    .. " ds=" .. ((G.q.last ~= nil and G.q.last.ds) or "nil") .. " seen=" .. #G.q.rows)
  local jr = 1
  while jr <= #G.q.rows do
    put("Q11 row id=" .. rc1d_txt(G.q.rows[jr].id) .. " w=" .. (G.q.rows[jr].own or "nil"))
    jr = jr + 1
  end
  put("Q11 dedupe in=" .. S5.inN .. " out=" .. S5.outN .. " calls=" .. S5.calls
    .. " dropped=" .. (#S5.drops > 0 and table.concat(S5.drops, ",") or "none"))
  local cs, xs = S.camo, S.chal
  local cw, cn = {}, 0
  for _, crow in pairs(cs.rows) do
    if cn < 6 then
      cn = cn + 1
      cw[cn] = tostring(crow.id)
    end
  end
  table.sort(cw)
  put("Q12 camo watch n=" .. cs.n .. " ids=" .. (cn > 0 and table.concat(cw, ",") or "none")
    .. " fired=" .. cs.fired .. " cross=" .. cs.crossN
    .. " mode=" .. rc1d_txt(cs.mode) .. " key=" .. rc1d_txt(cs.key))
  put("Q12 camo crossings " .. (cs.logN > 0 and table.concat(cs.log, ",") or "none"))
  local cr, crn = {}, 0
  for _, crow in pairs(cs.rows) do
    if crn < 6 then
      crn = crn + 1
      local cv = cs.seen[tostring(crow.id)]
      cr[crn] = tostring(crow.id) .. ":" .. tostring(cv) .. "/" .. tostring(crow.th[1])
        .. ":h" .. tostring(cv ~= nil and count_passed(crow.th, crow.n, cv) or 0)
        .. ":" .. tostring(crow.ref)
    end
  end
  put("Q12 camo rows " .. (crn > 0 and table.concat(cr, " ") or "none"))
  local xw, xn, xi = {}, 0, 1
  while xi <= xs.n do
    if xn < 6 then
      xn = xn + 1
      xw[xn] = tostring(xs.rows[xi].id) .. "/" .. tostring(xs.rows[xi].kind)
    end
    xi = xi + 1
  end
  put("Q13 cards watch n=" .. xs.n .. " tries=" .. xs.tries .. " why=" .. tostring(xs.why or "ok")
    .. " ids=" .. (xn > 0 and table.concat(xw, ",") or "none")
    .. " daily=" .. tostring(xs.dailyN) .. " weekly=" .. tostring(xs.weeklyN))
  put("Q13 cards fired=" .. xs.fired .. " cross=" .. xs.crossN
    .. " seen=" .. (xs.logN > 0 and table.concat(xs.log, ",") or "none"))
  local sw, rs = xs.sweep, S.ret
  put("Q14 sweep src=" .. tostring(sw.src or "none") .. " n=" .. sw.n .. " done=" .. sw.done
    .. " prog=" .. sw.prog .. " kinds=" .. tostring(sw.kinds[1]) .. "," .. tostring(sw.kinds[2])
    .. "," .. tostring(sw.kinds[3]))
  local cq, cqn = {}, 0
  for cref, cc in pairs(cs.count) do
    cqn = cqn + 1
    cq[cqn] = tostring(cref) .. ":b" .. tostring(cc.base) .. "/s" .. tostring(cc.special)
      .. "/m" .. tostring(cc.mastery) .. "/x" .. tostring(cc.extra)
  end
  table.sort(cq)
  put("Q14 camo rows n=" .. cs.extraN .. " " .. (cqn > 0 and table.concat(cq, " ") or "none"))
  local rq, rqn = {}, 0
  local rqi = 1
  while rqi <= rs.n and rqn < 8 do
    rqn = rqn + 1
    rq[rqn] = tostring(rs.rows[rqi].id)
    rqi = rqi + 1
  end
  put("Q14 reticle rows n=" .. rs.n .. " zm=" .. rs.nzm .. " kind=" .. rc1d_txt(rs.kind)
    .. " why=" .. tostring(rs.why or "ok") .. " ids=" .. (rqn > 0 and table.concat(rq, ",") or "none"))
  local c0 = nil
  for _, crow in pairs(cs.rows) do
    c0 = crow
    break
  end
  local qch = rawget(_G, "Challenge")
  if c0 ~= nil then
    local g1 = call(qch, "shouldshowcompletionsplash", { kind = KIND_WEAPON, id = c0.id, controller = 0 })
    put("Q14 gate kind=" .. KIND_WEAPON .. " id=" .. tostring(c0.id) .. " answer=" .. rc1d_txt(g1))
  end
  if rs.n > 0 then
    local best, bv = rs.rows[1], -1
    local bi = 1
    while bi <= rs.n do
      local r = rs.rows[bi]
      local sv = rs.seen[tostring(r.id)]
      local n = tonumber(sv)
      if n == nil then n = 0 end
      if n > bv then
        bv = n
        best = r
      end
      bi = bi + 1
    end
    local r0 = best
    local g2 = call(qch, "shouldshowcompletionsplash", { kind = rs.kind, id = r0.id, controller = 0 })
    put("Q14 gate kind=" .. rc1d_txt(rs.kind) .. " id=" .. tostring(r0.id) .. " answer=" .. rc1d_txt(g2))
    local iref, iname = nil, nil
    if r0.loot1 ~= nil then
      iref = call(rawget(_G, "LOOT"), "GetItemRef", r0.loot1)
      iname = call(rawget(_G, "LOOT"), "getitemnamebyid", r0.loot1)
    end
    put("Q14 reticle " .. tostring(r0.id) .. " itemref=" .. rc1d_txt(iref) .. " name=" .. clip(iname, 34))
  end
  local gum9 = nil
  local gbt9 = rawget(_G, "GOBBLEGUM")
  if type(gbt9) == "table" then
    local _, g9 = member(gbt9, "gobblegums")
    if type(g9) == "table" then
      pcall(function()
        local k9, v9 = next(g9)
        if type(v9) == "table" then gum9 = gfield(v9, "lootid") end
        if gum9 == nil then gum9 = tonumber(k9) end
      end)
    end
  end
  if gum9 ~= nil then q10(gum9, "gum") else put("Q10 gum=absent") end
  local nbuild = nil
  local NC = rawget(_G, "NearestToCompletionChallenges")
  local wcb = rc1d_bytes("34CCDBA986AD851B")
  local ncb = rc1d_bytes("C29622BB180395FF")
  local xpk, wpk, keyk = nil, nil, nil
  if type(WC) == "table" then
    local okx, vx = pcall(function() return WC[H("34CCDBA986AD851B")] end)
    if okx then xpk = vx end
    local okw, vw = pcall(function() return WC[wcb] end)
    if okw then wpk = vw end
  end
  if type(NC) == "table" then
    local okk, vk = pcall(function() return NC[ncb] end)
    if okk then keyk = vk end
  end
  if type(keyk) == "function" then nbuild = keyk end
  if nbuild == nil then
    local f = rc1d_hex(NC, "C29622BB180395FF")
    if f ~= nil then nbuild = f end
  end
  local gmkey = nil
  local gmf = fn_of(rawget(_G, "Game"), "GetActiveGameModeKey")
  if gmf ~= nil then
    local okg, vg = pcall(gmf)
    if okg then gmkey = vg end
  end
  local resp, list = "nil", nil
  if nbuild ~= nil then
    local okn, vn = pcall(nbuild, 0, gmkey)
    if okn and type(vn) == "table" then
      list = vn
      local c = 0
      pcall(function() for _ in pairs(vn) do c = c + 1 end end)
      resp = tostring(c)
    end
  end
  put("Q6 nc=" .. type(NC) .. " xpk=" .. type(xpk) .. " wpk=" .. type(wpk)
    .. " key=" .. type(keyk) .. " resp=" .. resp)
  put("Q6 wc ref=" .. type(fn_of(WC, "getweaponreffromchallengeref"))
    .. " data=" .. type(fn_of(WC, "updatedatasourcewithchallengedata"))
    .. " bytes=" .. string.len(wcb == nil and "" or wcb) .. "/" .. string.len(ncb == nil and "" or ncb))
  if list ~= nil then
    put("Q6 count=" .. resp .. " key=" .. rc1d_txt(gmkey) .. " cap=" .. RC1D_ENTRIES)
    local j = 1
    while j <= #list and j <= RC1D_ENTRIES do
      local e = list[j]
      local cid, cref, clot, wref, npr = nil, nil, nil, nil, nil
      if type(e) == "table" then
        cid, cref, clot = rc1d_field(e, "id"), rc1d_field(e, "ref"), rc1d_field(e, "lootId")
        npr = rc1d_field(e, "normalizedProgress")
        if wcref ~= nil and cref ~= nil then
          local okr, w = pcall(wcref, cref)
          if okr then wref = w end
        end
      end
      put("Q6 " .. j .. " id=" .. rc1d_txt(cid) .. " ref=" .. rc1d_txt(cref)
        .. " loot=" .. rc1d_txt(clot) .. " weapon=" .. rc1d_txt(wref)
        .. " np=" .. rc1d_txt(npr))
      j = j + 1
    end
  end
  i = 1
  while i <= #RC1D_TYPE do
    local id = RC1D_TYPE[i]
    put("Q8 " .. id .. " type=" .. rc1d_txt(gtype(id)))
    i = i + 1
  end
  local looked, ctrl, ctype = 0, nil, nil
  local scanid = 1
  while scanid <= GMAXID and looked < RC1D_LOOK and ctrl == nil do
    if glockedNow(scanid) then
      local t = gtype(scanid)
      if t ~= nil then
        looked = looked + 1
        if t ~= GTYPE_A and t ~= GTYPE_C then ctrl, ctype = scanid, t end
      end
    end
    scanid = scanid + 1
  end
  if ctrl == nil then
    put("Q8 control=none looked=" .. looked)
  else
    put("Q8 control id=" .. ctrl .. " type=" .. rc1d_txt(ctype) .. " bit=1 looked=" .. looked)
  end
  rc1d_chal("Q7 daily", rc1d_csv("zmDailyChallenges"), put, rc1d_rec, RC1D_DAILY)
  rc1d_chal("Q7 weekly", rc1d_csv("aezmweeklychallenges"), put, rc1d_rec, RC1D_WEEKLY)
  local CHF = rawget(_G, "Challenge")
  local gpf = fn_of(CHF, "getchallengesprogress")
  local gpkf = fn_of(CHF, "getchallengesprogressforkind")
  put("Q7 api progress=" .. type(gpf) .. " fork=" .. type(gpkf))
  if gpkf ~= nil then
    local form, got = nil, nil
    local oka, va = pcall(gpkf, 0, 585)
    if oka and type(va) == "table" then
      form, got = "c,kind", va
    else
      local okb, vb = pcall(gpkf, 585)
      if okb and type(vb) == "table" then form, got = "kind", vb end
    end
    if got == nil then
      put("Q7 fork 585 form=none")
    else
      local c = 0
      pcall(function() for _ in pairs(got) do c = c + 1 end end)
      local fid, frec = nil, nil
      pcall(function() local kk, vv = next(got); fid, frec = kk, vv end)
      put("Q7 fork 585 form=" .. form .. " n=" .. c .. " first=" .. rc1d_txt(fid)
        .. " progress=" .. rc1d_txt(rc1d_prog(frec)))
    end
  end
  if full then
    put("cap=" .. RC1D_CAP .. " reached - the rest of the block is not printed")
  end
  local serial = "none"
  if G.hex ~= nil then serial = tostring(G.serial) end
  log(RC1D .. ": 1 block vm=" .. (S.front and "menu" or "match") .. " pt_diag="
    .. (on and "on" or "off") .. ":" .. tostring(how) .. " payload=" .. serial
    .. " scope=" .. (G.scopeAll and "all-retired" or "locksmith") .. " cap=" .. RC1D_CAP)
  local k = 1
  while k <= n do
    log(RC1D .. ": " .. (k + 1) .. " " .. out[k])
    k = k + 1
  end
  log(RC1D .. ": end (" .. (n + 2) .. " lines)")
end

-- prints the block when the switch goes on
local function rc1diag_poll()
  local on = toggle("pt_diag", false)
  if on then pcall(rc1d_watch) end
  if on and RC1D_ON ~= true then rc1diag_run() end
  RC1D_ON = on
  S.diag = on
end

-- the splash check state
local CK = "splashck"
local CK_CAP = 12
local CK_N, CK_ACTS, CK_SEEN, CK_SLOW = 0, 0, false, false

-- prints a check line before the api exists
local function ck_say(msg)
  if type(A.log) == "function" then return A.log(msg) end
  local fn = rawget(_G, "DebugPrint") or rawget(_G, "print")
  if type(fn) == "function" then pcall(fn, "progression_tuning: " .. tostring(msg)) end
end

-- one numbered check line twelve at most
local function ck_put(msg)
  if CK_N >= CK_CAP then return end
  CK_N = CK_N + 1
  ck_say(CK .. ": " .. CK_N .. " " .. msg)
end

-- the datasource the recon names
local function ck_ds()
  local ds = rawget(_G, "DataSources")
  if type(ds) ~= "table" then return nil end
  return rc1d_field(rc1d_field(rc1d_field(rc1d_field(ds, "inGame"), "MP"), "splashes"), "currentSplash")
end

-- what that datasource answers
local function ck_val(ds)
  if ds == nil then return "absent" end
  local f = fn_of(ds, "GetValue")
  if f == nil then return "no getter" end
  local ok, v = pcall(f, ds, 0)
  if not ok then return "raised" end
  return rc1d_txt(v)
end

-- what the datasource answers with no text
local function ck_raw()
  local ds = ck_ds()
  if ds == nil then return nil end
  local f = fn_of(ds, "GetValue")
  if f == nil then return nil end
  local ok, v = pcall(f, ds, 0)
  if not ok then return nil end
  return v
end

-- the display group the splash part names
local function ck_group(key)
  if type(key) ~= "string" then return 0 end
  local s = rawget(_G, "ProgressionTuning")
  local d = (type(s) == "table") and s.draw or nil
  local f = (type(d) == "table") and d.group or nil
  if type(f) ~= "function" then return 1 end
  local ok, g = pcall(f, key)
  if ok and type(g) == "number" then return g end
  return 1
end

-- the getter the recon named
local function ck_have(su)
  local f = fn_of(su, "HaveActiveSplashScreens")
  if f == nil then return "absent" end
  local ok, v = pcall(f, 0)
  if not ok then return "raised" end
  return v == true
end

-- how many messages the native queue holds
local function ck_queue(hm)
  local g = fn_of(hm, "GetInstance")
  if g == nil then return "absent" end
  local ok, inst = pcall(g)
  if not ok then return "raised" end
  local q = rc1d_field(rc1d_field(rc1d_field(inst, "activeHud"), "splashManager"), "messageQueue")
  if type(q) ~= "table" then return "none" end
  return #q
end

-- a header by its readable key
local function ck_loc(key)
  local f = fn_of(rawget(_G, "Engine"), "Localize")
  if f == nil then return "absent" end
  local ok, v = pcall(f, key)
  if not ok then return "raised" end
  if type(v) ~= "string" or v == "" then return "nil" end
  if #v > 56 then return string.sub(v, 1, 56) end
  return v
end

-- the weekly card header the splash part resolves
local function ck_head()
  local s = rawget(_G, "ProgressionTuning")
  local d = (type(s) == "table") and s.draw or nil
  local f = (type(d) == "table") and d.wkhead or nil
  if type(f) ~= "function" then return "absent" end
  local ok, v = pcall(f)
  if not ok then return "raised" end
  if type(v) ~= "string" or v == "" then return "none" end
  if #v > 56 then return string.sub(v, 1, 56) end
  return v
end

-- a value behind a hashed key whatever its type
local function rc1d_hval(t, hex)
  if type(t) ~= "table" then return nil end
  local want = string.gsub(string.upper(hex), "^0+", "")
  local okb, b = pcall(function() return t[rc1d_bytes(hex)] end)
  if okb and b ~= nil then return b end
  local found = nil
  pcall(function()
    for k, v in pairs(t) do
      if found == nil then
        local s = string.gsub(string.upper(tostring(k)), "[^0-9A-F]", "")
        if string.len(s) == 17 and string.sub(s, 1, 1) == "3" then s = string.sub(s, 2) end
        s = string.gsub(s, "^0+", "")
        if s == want then found = v end
      end
    end
  end)
  return found
end

-- the weekly rows as id and amount
local function rc1d_weekrows()
  local out, n = {}, 0
  local tbl = rc1d_csv("aezmweeklychallenges")
  local cols = rc1d_field(tbl, "cols")
  local f = fn_of(rawget(_G, "StringTable"), "tablereadallrows")
  if type(cols) ~= "table" or f == nil then return out, 0 end
  local idcol = rc1d_field(cols, "id")
  local ok, rows = pcall(f, csv_file(tbl), { id = idcol, amount = rc1d_field(cols, "amount") }, idcol)
  if not ok or type(rows) ~= "table" then return out, 0 end
  pcall(function()
    for k, row in pairs(rows) do
      if n < 20 then
        local id = nil
        if type(row) == "table" then id = tonumber(rc1d_field(row, "id")) end
        if id == nil then id = tonumber(k) end
        if id ~= nil then
          n = n + 1
          out[n] = { id = id, amount = tonumber(rc1d_field(row, "amount")) }
        end
      end
    end
  end)
  return out, n
end

-- one native answer as a field
local function qbf(name, f, ...)
  if type(f) ~= "function" then return " " .. name .. "=absent" end
  local ok, v = pcall(f, ...)
  if not ok then return " " .. name .. "=raised" end
  return " " .. name .. "=" .. rc1d_txt(v)
end

-- the second block its own switch and prefix
local RB = "rbdiag"
local RB_CAP = 60
local RB_ON = false

-- reads eleven questions and writes nothing
local function rc1diag_b()
  local out, n, full = {}, 0, false
  local function put(t)
    if n >= RB_CAP - 2 then full = true return end
    n = n + 1
    out[n] = t
  end
  local KIND_WEAPON = 398
  local CHF = rawget(_G, "Challenge")
  local LOOTT = rawget(_G, "LOOT")
  local LT = rawget(_G, "Loot")
  local PRG = rawget(_G, "PROGRESSION")
  local PRE = rawget(_G, "PRESTIGE")
  local WEP = rawget(_G, "WEAPON")
  local ids = {}
  local i = 1
  while i <= #RC1D_IDS do
    ids[i] = RC1D_IDS[i][1]
    i = i + 1
  end
  ids[#ids + 1] = 101644
  local wrows, wcount = rc1d_weekrows()
  local icf = fn_of(CHF, "IsChallengeComplete")
  local near, done, nnear, ndone = {}, {}, 0, 0
  i = 1
  while i <= wcount do
    local r = wrows[i]
    local rec = rc1d_rec(r.id)
    local fin = false
    if icf ~= nil then
      local okc, v = pcall(icf, 0, r.id)
      if okc and v == true then fin = true end
    end
    local e = { id = r.id, amount = r.amount or 0, progress = rc1d_prog(rec), rec = rec }
    if fin then
      if ndone < 2 then
        ndone = ndone + 1
        done[ndone] = e
      end
    else
      nnear = nnear + 1
      near[nnear] = e
    end
    i = i + 1
  end
  table.sort(near, function(a, b)
    local ax, bx = a.amount, b.amount
    if ax <= 0 then ax = 1 end
    if bx <= 0 then bx = 1 end
    if a.progress * bx ~= b.progress * ax then return a.progress * bx > b.progress * ax end
    return a.id < b.id
  end)
  local shown = 0
  for j = 1, #near do
    if shown < 3 then
      local e = near[j]
      shown = shown + 1
      put("QB1 " .. e.id .. " complete=false progress=" .. e.progress .. "/" .. e.amount
        .. " status=" .. rc1d_txt(rc1d_field(e.rec, "status")))
    end
  end
  for j = 1, #done do
    local e = done[j]
    shown = shown + 1
    put("QB1 " .. e.id .. " complete=true progress=" .. e.progress .. "/" .. e.amount
      .. " status=" .. rc1d_txt(rc1d_field(e.rec, "status")))
  end
  if shown == 0 then put("QB1 done=none") end
  local wct = rawget(_G, "WeeklyChallenge")
  local gaw = fn_of(wct, "getallweeklychallenges")
  local wlist = nil
  if gaw ~= nil then
    local okl, v = pcall(gaw, 0, { includeComplete = true })
    if okl and type(v) == "table" then wlist = v end
  end
  local wn = 0
  if wlist ~= nil then pcall(function() for _ in pairs(wlist) do wn = wn + 1 end end) end
  put("QB2 api=" .. type(wct) .. " n=" .. (wlist ~= nil and wn or "none"))
  if wlist ~= nil then
    local seen = 0
    for j = 1, #wlist do
      if seen < 3 then
        local e = wlist[j]
        if type(e) == "table" then
          seen = seen + 1
          put("QB2 " .. rc1d_txt(rc1d_field(e, "achievementID")) .. " isComplete="
            .. rc1d_txt(rc1d_field(e, "isComplete")) .. " progress="
            .. rc1d_prog(e) .. " type="
            .. rc1d_txt(rc1d_field(rc1d_field(e, "data"), "type")))
        end
      end
    end
  end
  put("QB3 hash=" .. ck_loc("hash_7dc362a78cf1d3d3") .. " x=" .. ck_loc("#x37dc362a78cf1d3d3")
    .. " hex=" .. ck_loc("0x7dc362a78cf1d3d3")
    .. " key=" .. ck_loc("challenge/jup_ch_weekly_challenge_completed") .. " wkhead=" .. ck_head())
  local kaf, kbf = fn_of(CHF, "getaekindfromid"), fn_of(CHF, "GetAEKindID")
  local msame = "false"
  if kaf ~= nil and kbf ~= nil then
    local oka, va = pcall(kaf, 315)
    local okb, vb = pcall(kbf, "ae_kind_reticle")
    local na, nb = nil, nil
    if oka then
      if type(va) == "table" then na = tonumber(rc1d_field(va, "id")) else na = tonumber(va) end
    end
    if okb then nb = tonumber(vb) end
    if na ~= nil and nb ~= nil and na == nb then msame = "true" end
  end
  put("QB4 " .. rc1d_clause("id315", kaf, 315) .. " " .. rc1d_clause("reticle", kbf, "ae_kind_reticle")
    .. " match=" .. msame)
  local livef = fn_of(LT, "IsOwned")
  local _, _, _, gorigo = lockview()
  local origf = gorigo
  if type(origf) ~= "function" then origf = livef end
  local b1, b0, same, diff = 0, 0, 0, 0
  local dips, ndip, bits = {}, 0, {}
  i = 1
  while i <= #ids do
    local id = ids[i]
    local bit = 0
    if A.bit(id) then bit = 1 end
    bits[id] = bit
    local lv, ov = nil, nil
    if livef ~= nil then
      local okl, v = pcall(livef, 0, id)
      if okl then lv = v end
    end
    if origf ~= nil then
      local oko, v = pcall(origf, 0, id)
      if oko then ov = v end
    end
    local lb = 0
    if lv ~= nil and lv ~= false and lv ~= 0 then lb = 1 end
    if bit == 1 then b1 = b1 + 1 else b0 = b0 + 1 end
    if lb == bit then
      same = same + 1
    else
      diff = diff + 1
      if ndip < 4 then
        ndip = ndip + 1
        dips[ndip] = { id = id, bit = bit, live = lv, orig = ov }
      end
    end
    i = i + 1
  end
  put("QB5 n=" .. #ids .. " bit1=" .. b1 .. " bit0=" .. b0 .. " agree=" .. same .. " diff=" .. diff)
  i = 1
  while i <= ndip do
    local d = dips[i]
    put("QB5 diff " .. d.id .. " bit=" .. d.bit .. " live=" .. rc1d_txt(d.live)
      .. " orig=" .. rc1d_txt(d.orig))
    i = i + 1
  end
  put("QB5 anchor 126605 b=" .. tostring(bits[126605]) .. " 131708 b=" .. tostring(bits[131708])
    .. " 101644 b=" .. tostring(bits[101644]))
  local six = { 126605, 131708, 101644 }
  i = 1
  while i <= #six do
    local id = six[i]
    local info = call(LT, "getlootiteminfofromid", id)
    if type(info) ~= "table" then info = call(LOOTT, "getlootiteminfofromid", id) end
    local b = A.gbundle(id)
    local cat, ty, lvl, owner, wl = "nil", "nil", "nil", "nil", "nil"
    if type(info) == "table" then
      cat = rc1d_txt(rc1d_field(info, "category"))
      ty = rc1d_txt(rc1d_field(info, "type"))
    end
    if type(b) == "table" then
      lvl = rc1d_txt(rc1d_field(b, "levelUnlock"))
      local ow = rc1d_field(b, "weaponunlock")
      if type(ow) == "string" and ow ~= "" then
        owner = ow
        wl = rc1d_txt(call(PRG, "GetWeaponLevel", 0, ow))
      end
    end
    put("QB6 " .. id .. " cat=" .. cat .. " type=" .. ty .. " lvl=" .. lvl .. " owner=" .. owner
      .. " wlevel=" .. wl)
    i = i + 1
  end
  local ppf = fn_of(LOOTT, "getprimaryprojectfromref")
  put("QB7 " .. rc1d_clause("sat", ppf, "sat_pi_alcor") .. " "
    .. rc1d_clause("t10", ppf, "t10_me_p55_bgloves"))
  local pg = rc1d_hval(PRE, "E1A4D0E8679C1CCB")
  local p0, pr = "absent", "absent"
  if pg ~= nil then
    local ok0, v0 = pcall(pg, 0)
    if ok0 then p0 = rc1d_txt(v0) end
    local okr, vr = pcall(pg, RC1D_REF)
    if okr then pr = rc1d_txt(vr) end
  end
  local b8 = call(PRG, "getactiveweaponranktablebundle", RC1D_REF)
  local bv = rc1d_hval(b8, "7C6F4A53654BFFDF")
  put("QB8 prestige0=" .. p0 .. " prestigeRef=" .. pr .. " bundle=" .. rc1d_txt(bv)
    .. " bundleType=" .. type(bv))
  local rk = "none"
  local rl = call(PRG, "getactiveweaponranktableranklist", 0)
  if type(rl) == "table" then rk = #rl end
  put("QB9 ref=" .. RC1D_REF .. " ranks=" .. rk
    .. " max=" .. rc1d_txt(call(PRG, "getmaxweaponlevel", RC1D_REF)))
  local rw = call(PRG, "GetRewardUnlockedAtWeaponLevel", RC1D_REF, 1)
  local rd = call(PRG, "GetRewardDataUnlockedAtWeaponLevel", RC1D_REF, 1)
  local nw, nd = 0, 0
  if type(rw) == "table" then nw = #rw end
  if type(rd) == "table" then nd = #rd end
  local nwp = 0
  local wdat = call(WEP, "getweapondataforref", RC1D_REF)
  local wp = rc1d_field(wdat, "weaponProgression")
  if type(wp) == "table" then
    local ul = rc1d_field(wp[2], "levelunlocks")
    if type(ul) == "table" then nwp = #ul end
  end
  local nc = 0
  local cell = A.cell_pick(A.gun_tries(RC1D_REF), "loot")
  if type(cell) == "string" then
    local first = string.match(cell, "[^|]+")
    if first ~= nil then
      for part in string.gmatch(first, "[^+]+") do
        if tonumber(part) ~= nil then nc = nc + 1 end
      end
    end
  end
  -- the three list sources one of them is stupid
  local src = "none"
  if nw > 0 then
    src = "reward"
  elseif nwp > 0 then
    src = "weapon"
  elseif nc > 0 then
    src = "csv"
  end
  local splash = A.dv("lui_use_gl_splash")
  if splash == nil or splash == "" then splash = "nil" end
  put("QB10 ref=" .. RC1D_REF .. " lvl=1 reward=" .. nw .. " rewardData=" .. nd .. " weapon=" .. nwp
    .. " csv=" .. nc .. " src=" .. src .. " splash=" .. splash)
  local cs = S.camo
  local rows = nil
  if type(cs) == "table" then rows = cs.rows end
  local c0 = nil
  if type(rows) == "table" then
    local _, first = next(rows)
    if type(first) == "table" then c0 = first end
  end
  if c0 == nil then
    put("QB11 row=none")
  else
    local cid = rc1d_field(c0, "id")
    local th = c0.th
    local our = nil
    if type(th) == "table" then
      local m = tonumber(c0.n) or 0
      our = th[m + 1]
      if our == nil then our = th[#th] end
    end
    put("QB11 id=" .. tostring(cid) .. " k398=" .. rc1d_txt(call(CHF, "GetAmount", cid, KIND_WEAPON, 0))
      .. " k400=" .. rc1d_txt(call(CHF, "GetAmount", cid, 400, 0)) .. " our=" .. rc1d_txt(our))
  end
  -- the weekly switch and a control dvar
  local WK = "lui_weekly_challenge_menu_enabled"
  put("QB12 bool=" .. type(fn_of(rawget(_G, "Dvar"), "GetDvarBool")) .. " wk=" .. tostring(A.dv(WK))
    .. " ctl=" .. tostring(A.dv("lui_use_gl_splash")))
  -- the reticle kind route and its two lookups
  local XH = rawget(_G, "xhash")
  local function p13(f, fmt, ...)
    if f == nil then return "absent" end
    local ok, v = pcall(f, ...)
    if not ok then return "raised" end
    return fmt(v)
  end
  local function k13(n)
    if kbf == nil then return "absent/absent" end
    local a = p13(kbf, rc1d_txt, n)
    local okh, h = pcall(XH, n)
    if not okh or h == nil then return a .. "/absent" end
    return a .. "/" .. p13(kbf, rc1d_txt, h)
  end
  local ssf = fn_of(CHF, "shouldshowcompletionsplash")
  local ftf = fn_of(CHF, "GetFileTableByType")
  put("QB13 aek=" .. k13("ae_kind_reticle") .. " cer=" .. k13("ae_kind_reticle_cer")
    .. " show422=" .. p13(ssf, rc1d_txt, { kind = 422, id = 66938, controller = 0 })
    .. " show315=" .. p13(ssf, rc1d_txt, { kind = 315, id = 66938, controller = 0 })
    .. " tbl422=" .. p13(ftf, type, 422, 66938) .. " tbl315=" .. p13(ftf, type, 315, 66938))
  -- the rewards payload and one operator skin
  local shex, sn = A.gset()
  local function bits(id) return (A.bit(id) and 1 or 0), (A.greward(id) and 1 or 0) end
  local b14, r14 = bits(92066)
  put("QB14 g12 set=" .. (shex ~= nil and 1 or 0) .. " n=" .. rc1d_txt(sn)
    .. " r92066=" .. r14 .. " l92066=" .. b14)
  -- three calling cards asked three ways
  local uf = fn_of(LOOTT, "IsUnlocked")
  local wf = fn_of(LOOTT, "isunlockedwithid")
  local function cardline(name, id, ref)
    local b, r = bits(id)
    put("QB15 " .. name .. "3=" .. p13(uf, rc1d_txt, 0, 11, ref) .. " " .. name .. "2="
      .. p13(wf, rc1d_txt, 0, id) .. " lock=" .. b .. " reward=" .. r)
  end
  cardline("card", 104846, "sat_ui_playercard_044")
  cardline("dark", 104916, "sat_ui_playercard_173")
  cardline("store", 6015, "ui_playercard_869")
  -- one operator skin and its item type
  local b16, r16 = bits(92066)
  put("QB16 skin=" .. p13(wf, rc1d_txt, 0, 92066) .. " lock=" .. b16 .. " reward=" .. r16
    .. " type=" .. p13(fn_of(LOOTT, "gettypeforid"), rc1d_txt, 92066))
  -- the sticker book kind and its row
  local fkf = fn_of(rawget(_G, "OnlineChallenges"), "getchallengesprogressforkind")
    or fn_of(CHF, "getchallengesprogressforkind")
  local n429, st429 = "none", "nil"
  local okf, t429 = false, nil
  if fkf ~= nil then okf, t429 = pcall(fkf, 0, 429) end
  if okf and type(t429) == "table" then
    n429 = 0
    for _ in pairs(t429) do n429 = n429 + 1 end
    st429 = rc1d_txt(rc1d_field(rc1d_get(t429, 52508), "status"))
  end
  put("QB17 show429=" .. p13(ssf, rc1d_txt, { kind = 429, id = 52508, controller = 0 })
    .. " sticker=" .. p13(fn_of(CHF, "getstickerbookchallengedata"), rc1d_txt, 0, 52508)
    .. " fork429=" .. n429 .. " st=" .. st429)
  -- the default reticle guard
  local b18, r18 = bits(109917)
  put("QB18 ret=" .. p13(wf, rc1d_txt, 0, 109917) .. " lock=" .. b18 .. " reward=" .. r18
    .. " default=" .. p13(fn_of(LOOTT, "isitemdefault"), rc1d_txt, 109917))
  -- the overview percent one line per game mode
  local af = A.answer
  if af == nil and S.locks ~= nil then af = S.locks.answer end
  local gsd = fn_of(rawget(_G, "CallingCardUtils"), "getstickerbookchallengesdata")
  local cumf = fn_of(LOOTT, "GetCumulatedProgressNormalized")
  local QMODES = { { "OB", 3 }, { "BR", 4 }, { "ZM", 5 } }
  local QCHILD_CAP = 12
  local qkids = 0
  local function qfirst(s)
    if type(s) ~= "string" then return "" end
    local p = string.find(s, "|", 1, true)
    if p == nil then return s end
    return string.sub(s, 1, p - 1)
  end
  local mi = 1
  while mi <= #QMODES do
    local mname, mid = QMODES[mi][1], QMODES[mi][2]
    local row = nil
    if gsd ~= nil then
      local okm, list = pcall(gsd, 0, mid)
      if okm and type(list) == "table" then row = list[1] end
    end
    local ref, kids = "absent", nil
    if type(row) == "table" then
      ref = rc1d_field(row, "categoryType")
      if type(ref) ~= "string" or ref == "" then ref = rc1d_field(row, "challengeImage") end
      if type(ref) ~= "string" or ref == "" then ref = rc1d_field(row, "id") end
      ref = rc1d_txt(ref)
      kids = rc1d_field(row, "subChallenges")
    end
    local den, fnum, emp, nbit, nrew, nopen, num = 0, 0, 0, 0, 0, 0, 0
    local qline = {}
    if type(kids) == "table" then den = #kids end
    local j = 1
    while j <= den do
      local kid = kids[j]
      local s1 = qfirst(rc1d_field(kid, "loot"))
      local id1 = tonumber(s1)
      local b, r, d, a = 0, 0, "absent", "absent"
      if id1 == nil then
        emp = emp + 1
      else
        id1 = math.floor(id1)
        fnum = fnum + 1
        if A.bit(id1) then b = 1 nbit = nbit + 1 end
        if A.greward(id1) then r = 1 nrew = nrew + 1 end
        if type(af) == "function" then
          local okd, v = pcall(af, id1)
          if okd then
            d = rc1d_txt(v)
            if v ~= true then nopen = nopen + 1 end
          else
            d = "raised"
          end
        end
        if type(wf) == "function" then
          local oka, v = pcall(wf, 0, id1)
          if oka then
            a = rc1d_txt(v)
            if v then num = num + 1 end
          else
            a = "raised"
          end
        end
      end
      if qkids < QCHILD_CAP then
        qkids = qkids + 1
        qline[#qline + 1] = "QB20 " .. mname .. " child " .. rc1d_txt(rc1d_field(kid, "id"))
          .. " split1=" .. s1 .. " bit=" .. b .. " reward=" .. r .. " door=" .. d .. " ans=" .. a
      end
      j = j + 1
    end
    local pct = "none"
    if den > 0 then pct = string.format("%d", math.floor(num * 100 / den + 0.5)) end
    local nat, cum = "none", "absent"
    if type(row) == "table" then
      local pv = rc1d_field(row, "progress")
      if pv ~= nil then nat = rc1d_txt(pv) end
      if cumf ~= nil then
        local okc, rf = pcall(cumf, row)
        if not okc then
          cum = "raised"
        elseif type(rf) ~= "function" then
          cum = "none"
        else
          local okv, v = pcall(rf, 0)
          if okv then cum = rc1d_txt(v) else cum = "raised" end
        end
      end
    end
    put("QB20 " .. mname .. " " .. ref .. " children=" .. den .. " firstNum=" .. fnum
      .. " empty=" .. emp .. " bit=" .. nbit .. " reward=" .. nrew .. " open=" .. nopen
      .. " num=" .. num .. " den=" .. den .. " pct=" .. pct .. " native=" .. nat .. " cum=" .. cum)
    local qi = 1
    while qi <= #qline do
      put(qline[qi])
      qi = qi + 1
    end
    mi = mi + 1
  end
  -- the five operator skins and their own getters
  local SK = { 143284, 151944, 92066, 143522, 149872 }
  local ltm = rc1d_field(LOOTT, "itemTypes")
  local sktype = tonumber(rc1d_field(ltm, "OPERATOR_SKIN")) or 8
  local skb = fn_of(LOOTT, "getscriptbundleforid")
  local _, skstore = member(rawget(_G, "STORE"), "Bundles")
  local skfirst = fn_of(skstore, "GetFirstBundleWithLootId")
  local skq = fn_of(LOOTT, "getquestrewardtypeforid")
  local skd = fn_of(LOOTT, "isitemdefault")
  local sku = fn_of(LOOTT, "isunlockedwithid")
  local skdesc = fn_of(LOOTT, "GetUnlockDescription")
  local skseason = fn_of(LOOTT, "getitemseasonbyid")
  local skprem = fn_of(LOOTT, "getispremiumforbundle")
  local function skinget(f, ...)
    if type(f) ~= "function" then return "absent" end
    local ok, v = pcall(f, ...)
    if not ok then return "err" end
    return rc1d_txt(v)
  end
  local function skinhave(v)
    if type(v) == "table" then return "y" end
    return "n"
  end
  local si = 1
  while si <= #SK do
    local sid = SK[si]
    local bundle = nil
    if skb ~= nil then
      local okb, v = pcall(skb, sktype, sid)
      if okb and type(v) == "table" then bundle = v end
    end
    local store = "err"
    if skfirst ~= nil then
      store = "n"
      local oks, sv = pcall(skfirst, 0, sid)
      if not oks then
        store = "err"
      elseif sv ~= nil then
        store = "y"
      end
    end
    local season = rc1d_txt(rc1d_field(bundle, "season"))
    if season == "nil" then season = skinget(skseason, sktype, sid) end
    local premium = rc1d_txt(rc1d_field(bundle, "ispremium"))
    if premium == "nil" and bundle ~= nil then premium = skinget(skprem, bundle) end
    local desc = "nil"
    if skdesc ~= nil and bundle ~= nil then
      local okd, d = pcall(skdesc, bundle)
      if not okd then
        desc = "err"
      elseif type(d) == "string" and d ~= "" then
        desc = string.sub(d, 1, 40)
      elseif d ~= nil then
        desc = rc1d_txt(d)
      end
    end
    local sbit, srew = 0, 0
    local okbt, vbt = pcall(A.bit, sid)
    if okbt and vbt then sbit = 1 end
    local okrw, vrw = pcall(A.greward, sid)
    if okrw and vrw then srew = 1 end
    put("QB21 skin id=" .. sid .. " bundle=" .. skinhave(bundle)
      .. " unlocktype=" .. rc1d_txt(rc1d_field(bundle, "unlocktype"))
      .. " season=" .. season .. " premium=" .. premium
      .. " quest=" .. rc1d_txt(rc1d_field(bundle, "zmquestrewardloottype"))
      .. " qtype=" .. skinget(skq, sid) .. " default=" .. skinget(skd, sid)
      .. " store=" .. store .. " desc=" .. desc
      .. " unlocked=" .. skinget(sku, 0, sid)
      .. " bit=" .. sbit .. " reward=" .. srew)
    si = si + 1
  end
  put("QB21 skin globals OPERATOR=" .. skinhave(rawget(_G, "OPERATOR"))
    .. " Operator=" .. skinhave(rawget(_G, "Operator"))
    .. " getscriptbundleforid=" .. (skb ~= nil and "y" or "n"))
  if full then
    put("cap=" .. RB_CAP .. " reached - the rest of the block is not printed")
  end
  log(RB .. ": 1 block vm=" .. (S.front and "menu" or "match") .. " ref=" .. RC1D_REF
    .. " cap=" .. RB_CAP)
  local k = 1
  while k <= n do
    log(RB .. ": " .. (k + 1) .. " " .. out[k])
    k = k + 1
  end
  log(RB .. ": end (" .. (n + 2) .. " lines)")
end

-- the five cards once the tables answer
local QB19_IDS = { 117486, 126988, 112409, 104861, 6015 }
local QB19_ON = false

local function rc1d_qb19()
  if QB19_ON then return end
  local cf = A.cards
  if type(cf) ~= "function" then return end
  local ok, k, total = pcall(cf)
  if not ok or type(k) ~= "number" or type(total) ~= "number" or total <= 0 then return end
  if k < total then return end
  QB19_ON = true
  local LOOTT = rawget(_G, "LOOT")
  local wf = fn_of(LOOTT, "isunlockedwithid")
  local tf = fn_of(LOOTT, "gettypeforid")
  local af = A.answer
  if af == nil and S.locks ~= nil then af = S.locks.answer end
  log("QB19 cards=" .. k .. "/" .. total)
  local j = 1
  while j <= #QB19_IDS do
    local id = QB19_IDS[j]
    local b, r = 0, 0
    if A.bit(id) then b = 1 end
    if A.greward(id) then r = 1 end
    log("QB19 " .. id .. " lock=" .. b .. " reward=" .. r .. qbf("type", tf, id)
      .. qbf("ans", af, id) .. qbf("native", wf, 0, id))
    j = j + 1
  end
end

-- a type entry as priority and override
local function ck_mt(mt, name)
  local e = rc1d_field(mt, name)
  if type(e) ~= "table" then return name .. "=absent" end
  return name .. "=" .. rc1d_txt(rc1d_field(e, "priority")) .. "/"
    .. rc1d_txt(rc1d_field(e, "shouldOverride"))
end

-- one line per card the splash part draws
local CK_CARD_CAP = 60
local CK_CARDS = 0
local CK_CAPPED = false

-- the display location each kind goes out on
local CK_SND_LOC = { level = { "weaponLevel" }, chalD = { "dailyNotification", "challengeComplete" },
                     chalWB = { "dailyNotification" }, camoB = { "camoChallenge" } }

-- is this location one the kind goes out on
local function ck_at(locs, loc)
  if type(locs) ~= "table" then return false end
  local i = 1
  while i <= #locs do
    if locs[i] == loc then return true end
    i = i + 1
  end
  return false
end

-- the sound the card just dispatched carries
local function ck_snd(kind)
  local hm = rc1d_field(rawget(_G, "LUI"), "HudManager")
  local g = fn_of(hm, "GetInstance")
  if g == nil then return "unread" end
  local ok, inst = pcall(g)
  if not ok or inst == nil then return "unread" end
  local q = rc1d_field(rc1d_field(rc1d_field(inst, "activeHud"), "splashManager"), "messageQueue")
  if type(q) ~= "table" then return "unread" end
  local clk = fn_of(rawget(_G, "Engine"), "GetMilliseconds")
  local now = nil
  if clk ~= nil then
    local okc, v = pcall(clk)
    if okc then now = tonumber(v) end
  end
  local locs = CK_SND_LOC[kind]
  local best, at, i = nil, nil, 1
  while i <= #q do
    local e = q[i]
    local o = rc1d_field(e, "options")
    local t = tonumber(rc1d_field(e, "insertTime"))
    local fresh = (now == nil or t == nil or t >= now - 50)
    if fresh and ck_at(locs, rc1d_field(o, "displayLocation"))
       and (at == nil or t == nil or t >= at) then
      best, at = o, t
    end
    i = i + 1
  end
  if best == nil then return "unread" end
  local s = rc1d_field(best, "sound")
  if type(s) ~= "string" or s == "" then return "none" end
  if #s > 32 then return string.sub(s, 1, 32) end
  return s
end

-- the alias the client own table answers in this vm
local function ck_alias()
  local _, cs = member(rawget(_G, "SOUND_SETS"), "challengeSplash")
  local _, v = member(cs, "generalChallenge")
  if type(v) == "string" and v ~= "" then return v end
  return "absent"
end

-- the client own gate on every option sound
local function ck_opacity()
  local ds = rawget(_G, "_DataSources") or rawget(_G, "DataSources")
  local node = rc1d_field(rc1d_field(rc1d_field(ds, "settings"), "gamer_profile"),
                          "notification_feed_opacity")
  local f = fn_of(node, "GetValue")
  if f == nil then return "absent" end
  local ok, v = pcall(f, node, 0)
  if not ok then return "raised" end
  return rc1d_txt(v)
end

-- one sound line per centre card twenty at most
local CK_SND_CAP = 20
local CK_SND_N = 0
local CK_SND_STOP = false
local CK_SND_KIND = { level = true, chalD = true, chalWB = true, camoB = true }

local function ck_snd_line(kind, id)
  if CK_SND_KIND[kind] ~= true then return end
  if CK_SND_N >= CK_SND_CAP then
    if not CK_SND_STOP then
      CK_SND_STOP = true
      ck_say(CK .. ": snd capped at " .. CK_SND_CAP)
    end
    return
  end
  CK_SND_N = CK_SND_N + 1
  local s = ck_snd(kind)
  ck_say(CK .. ": snd " .. CK_SND_N .. " kind=" .. tostring(kind) .. " id=" .. tostring(id)
    .. " sound=" .. s .. " aliases=" .. ck_alias() .. " opacity=" .. ck_opacity())
end

local function ck_card(kind, id, wait, rule)
  if CK_CARDS >= CK_CARD_CAP then
    if not CK_CAPPED then
      CK_CAPPED = true
      ck_say(CK .. ": cards capped at " .. CK_CARD_CAP)
    end
    return
  end
  CK_CARDS = CK_CARDS + 1
  ck_say(CK .. ": card " .. CK_CARDS .. " kind=" .. tostring(kind) .. " id=" .. tostring(id)
    .. " wait=" .. tostring(wait) .. " rule=" .. tostring(rule))
  ck_snd_line(kind, id)
end

-- the splash check block once per vm
local function ck_run()
  local lui = rawget(_G, "LUI")
  local sm = rc1d_field(lui, "SplashManager")
  local su = rc1d_field(lui, "SplashUtils")
  local hm = rc1d_field(lui, "HudManager")
  local ds = ck_ds()
  CK_SLOW = (type(lui) ~= "table")
  ck_put("types vm=" .. (S.front and "menu" or "match") .. " sm=" .. type(sm) .. " su=" .. type(su)
    .. " hm=" .. type(hm))
  ck_put("ds currentSplash=" .. type(ds) .. " value=" .. ck_val(ds))
  local mt = rc1d_field(sm, "MessageType")
  ck_put("mt " .. ck_mt(mt, "ChallengeComplete") .. " " .. ck_mt(mt, "DailyChallengeNotification")
    .. " " .. ck_mt(mt, "WeeklyChallengeSplashNotification"))
  ck_put("mt " .. ck_mt(mt, "CamoChallenge") .. " " .. ck_mt(mt, "WeaponLevel")
    .. " " .. ck_mt(mt, "Medal"))
  ck_put("active=" .. tostring(ck_have(su)) .. " queue=" .. tostring(ck_queue(hm)))
  ck_put("weekly=" .. ck_loc("challenge/jup_ch_weekly_challenge_completed") .. " head=" .. ck_head())
  ck_put("daily=" .. ck_loc("splashes/daily_challenge_completed"))
end

-- the same block once the hud exists
local function ck_late()
  local lui = rawget(_G, "LUI")
  local sm = rc1d_field(lui, "SplashManager")
  local su = rc1d_field(lui, "SplashUtils")
  local hm = rc1d_field(lui, "HudManager")
  ck_put("late vm=" .. (S.front and "menu" or "match") .. " sm=" .. type(sm) .. " su=" .. type(su)
    .. " hm=" .. type(hm))
  local mt = rc1d_field(sm, "MessageType")
  ck_put("late mt " .. ck_mt(mt, "ChallengeComplete")
    .. " " .. ck_mt(mt, "WeeklyChallengeSplashNotification") .. " " .. ck_mt(mt, "Medal"))
  ck_put("late active=" .. tostring(ck_have(su)) .. " queue=" .. tostring(ck_queue(hm)))
end

-- the splash slot seen on the shared timer
local function ck_poll()
  if CK_SLOW then
    CK_SLOW = false
    if type(rawget(_G, "LUI")) == "table" then ck_late() end
  end
  if CK_ACTS >= 2 then return end
  local lui = rawget(_G, "LUI")
  local rawv = ck_raw()
  local on = ck_have(rc1d_field(lui, "SplashUtils"))
  if on == true and CK_SEEN ~= true and ck_group(rawv) == 1 then
    CK_SEEN = true
    CK_ACTS = CK_ACTS + 1
    ck_put("during vm=" .. (S.front and "menu" or "match") .. " active=" .. tostring(on)
      .. " splash=" .. ck_val(ck_ds()) .. " queue=" .. tostring(ck_queue(rc1d_field(lui, "HudManager"))))
    return
  end
  if on ~= true and CK_SEEN == true then
    CK_SEEN = false
    CK_ACTS = CK_ACTS + 1
    ck_put("after vm=" .. (S.front and "menu" or "match") .. " active=" .. tostring(on)
      .. " splash=" .. ck_val(ck_ds()) .. " queue=" .. tostring(ck_queue(rc1d_field(lui, "HudManager"))))
  end
end

-- the console switch that silences the whole part
local DIAG_OFF_SAID = false
local function diag_off()
  if toggle("pt_diag_off", false) ~= true then return false end
  if DIAG_OFF_SAID ~= true then
    DIAG_OFF_SAID = true
    ck_say("diag off")
  end
  return true
end

-- the probe dvar and the last value
local SEE_DV, SEE_LAST = "pt_seeprobe", ""

-- prints each new probe value once
local function see_poll()
  if S.front ~= false then return end
  local v = A.dv(SEE_DV)
  if type(v) ~= "string" or v == "" or v == SEE_LAST then return end
  SEE_LAST = v
  log(v)
end

-- the check first then the switch
local function rc1diag_chain()
  pcall(see_poll)
  if diag_off() then
    return
  end
  pcall(ck_poll)
  rc1diag_poll()
  local don = toggle("pt_diag", false)
  if don then pcall(rc1d_qb19) end
  local bot = don and toggle("pt_diagb", false)
  if bot and RB_ON ~= true then pcall(rc1diag_b) end
  RB_ON = bot
end

-- the carry forward world this vm runs in
local function cf_arm()
  local cf, mwcf = A.dv("kronos_cfwd"), A.dv("mwcf_box_pools")
  local mw = mwcf ~= nil and mwcf ~= ""
  log("carry-forward: pack=unknown dvar=" .. tostring(cf) .. " mwcf=" .. tostring(mw))
end

-- the check and the switch once main has armed
local function rc1diag_arm()
  if diag_off() then return end
  pcall(cf_arm)
  pcall(ck_run)
  rc1diag_run()
end

local RC1D_END = true

S.hooks.diag_arm = rc1diag_arm
S.hooks.diag = rc1diag_chain
S.hooks.card = ck_card
S.probes.diag = function() return type(A.log) == "function" and type(A.toggle) == "function" end

local dp = rawget(_G, "DebugPrint") or rawget(_G, "print")
if type(dp) == "function" then pcall(dp, "progression_tuning: part diag armed") end

if A.ready ~= nil then A.ready() end
