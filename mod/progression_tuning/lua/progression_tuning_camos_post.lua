local PART = "camos"

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
local function want(...) return A.want(...) end
local function ours(...) return A.ours(...) end
local function count_passed(...) return A.count_passed(...) end
local function note_cross(...) return A.note_cross(...) end
local function amounts_of(...) return A.amounts_of(...) end
local function rec_value(...) return A.rec_value(...) end
local function rec_fields(...) return A.rec_fields(...) end

local CAMO_FIELDS = { "progress", "xp", "default" }
local CAMO_WATCH_CAP = 8
local CAMO_EXTRA_PER = 12
local WATCH_GAP_TICKS = 32

local function enqueue(what, fn)
  local d = S.draw
  local q = d ~= nil and d.queue or nil
  if q == nil then
    if said("nosplash") then log("splash absent - no card is drawn") end
    return false
  end
  return q(what, fn)
end

local function camo_show(row, target, tier, value)
  local f = S.draw
  f = f ~= nil and f.camo or nil
  if f == nil then return end
  f(row, target, tier, value)
end

-- the challenge mode this match runs
local function camo_mode(wc)
  local key = nil
  local gmf = fn_of(rawget(_G, "Game"), "GetActiveGameModeKey")
  if gmf ~= nil then
    local okm, vm = pcall(gmf)
    if okm and vm ~= nil then key = vm end
  end
  local mode = nil
  if type(wc) == "table" and key ~= nil then
    local _, map = member(wc, "gamemodekeytochallengegamemode")
    if type(map) == "table" then
      local okm, v = pcall(function() return map[key] end)
      if okm then mode = tonumber(v) end
    end
  end
  if mode == nil and type(wc) == "table" then
    local _, cm = member(wc, "challengegamemode")
    if type(cm) == "table" then
      local _, mp = member(cm, "mp")
      mode = tonumber(mp)
    end
  end
  return mode, key
end

-- the weapon own military camo row
local function camo_row(ref)
  local wc = rawget(_G, "WEAPON_CAMO")
  if type(wc) ~= "table" then return nil, "no WEAPON_CAMO table in this VM" end
  local f = fn_of(wc, "getmilitarycamochallenges")
  if f == nil then return nil, "no WEAPON_CAMO.getmilitarycamochallenges in this VM" end
  local mode, key = camo_mode(wc)
  local ok, list = pcall(f, 0, ref, mode)
  if not ok or type(list) ~= "table" then
    return nil, "getmilitarycamochallenges answered no table for " .. clip(ref, 24)
      .. " (mode key=" .. tostring(key) .. " mode=" .. tostring(mode) .. ")"
  end
  local id, th, k = nil, {}, 0
  local i = 1
  while i <= #list do
    local e = list[i]
    if type(e) == "table" then
      local _, eid = member(e, "id")
      local _, amt = member(e, "amount")
      local nid, v = tonumber(eid), tonumber(amt)
      if nid ~= nil and v ~= nil then
        id = nid
        k = k + 1
        th[k] = v
      end
    end
    i = i + 1
  end
  if id == nil or k < 1 then return nil, "no camo row for " .. clip(ref, 24) end
  return { id = id, th = th, n = k, ref = ref, mode = mode, key = key }
end

-- the special and mastery rows of one weapon
local function camo_entries(ref, mode, baseid)
  local out, n = {}, 0
  local counts = { base = 0, special = 0, mastery = 0, extra = 0, why = nil }
  local ids = {}
  if baseid ~= nil then
    ids[baseid] = true
    counts.base = 1
  end
  local wc = rawget(_G, "WEAPON_CAMO")
  if type(wc) ~= "table" then
    counts.why = "no WEAPON_CAMO table in this VM"
    return out, n, counts
  end
  if mode == nil then counts.why = "the client named no challenge mode for this match" end
  local gate = fn_of(wc, "isgatemasterychallenge")
  -- keeps one row of a family
  local function push(e, tag)
    if type(e) ~= "table" then return false end
    local _, eid = member(e, "id")
    local id = tonumber(eid)
    if id == nil or ids[id] == true then return false end
    local _, amt = member(e, "amount")
    local th, k = amounts_of(amt)
    if k < 1 then return false end
    local _, rf = member(e, "ref")
    local rfs = type(rf) == "string" and rf or ref
    local _, add = member(e, "isAdditional")
    if add == true then
      counts.extra = counts.extra + 1
      return false
    end
    if gate ~= nil and mode ~= nil then
      local okg, g = pcall(gate, rfs, mode)
      if okg and g == true then
        counts.extra = counts.extra + 1
        return false
      end
    end
    ids[id] = true
    n = n + 1
    out[n] = { id = id, th = th, n = k, ref = rfs }
    counts[tag] = counts[tag] + 1
    return true
  end
  local sf = fn_of(wc, "getspecialcamos")
  local lf = fn_of(wc, "getcamochallengefromlootid")
  if sf == nil or lf == nil then
    if said("camospecial:" .. ref) then
      log("camo special unavailable for " .. clip(ref, 28) .. " - no WEAPON_CAMO."
        .. (sf == nil and "getspecialcamos" or "getcamochallengefromlootid") .. " in this VM")
    end
  elseif mode ~= nil then
    local ok, list = pcall(sf, 0, ref, mode)
    if ok and type(list) == "table" then
      local i = 1
      while i <= #list do
        local b = list[i]
        if type(b) == "table" then
          local _, lid = member(b, "lootid")
          local loot = tonumber(lid)
          if loot ~= nil then
            local okc, e = pcall(lf, 0, loot)
            if okc then push(e, "special") end
          end
        end
        i = i + 1
      end
    end
  end
  local pf = fn_of(wc, "getprogressioncamos")
  local bf = fn_of(wc, "getcamochallengesfrombundle")
  if pf == nil or bf == nil then
    if said("camobundle:" .. ref) then
      log("camo bundles unavailable for " .. clip(ref, 28) .. " - no WEAPON_CAMO."
        .. (pf == nil and "getprogressioncamos" or "getcamochallengesfrombundle") .. " in this VM")
    end
  elseif mode ~= nil then
    local okp, a, b, c = pcall(pf, 0, mode, ref)
    if okp then
      local lists = { a, b, c }
      local li = 1
      while li <= 3 do
        local list = lists[li]
        if type(list) == "table" then
          local bi = 1
          while bi <= #list do
            local okb, ents = pcall(bf, 0, list[bi], ref, { skipFullLootTable = true })
            if okb and type(ents) == "table" then
              local ei = 1
              while ei <= #ents do
                push(ents[ei], "mastery")
                ei = ei + 1
              end
            end
            bi = bi + 1
          end
        end
        li = li + 1
      end
    end
  end
  return out, n, counts
end

-- builds every camo family once per weapon
local function camo_extra()
  local s = S.camo
  local refs, rn = {}, 0
  for ref in pairs(S.guns) do
    if type(ref) == "string" then
      rn = rn + 1
      refs[rn] = ref
    end
  end
  if rn < 1 then return end
  table.sort(refs)
  local i = 1
  while i <= rn do
    local ref = refs[i]
    if s.extraBuilt[ref] ~= true then
      if not ours(ref) then
        s.extraBuilt[ref] = true
        if said("camo:extra:" .. ref) then
          vlog("camo bundles " .. clip(ref, 28) .. " - not one of ours, so no row is read for it")
        end
      else
        local t = s.extraTries[ref] or 0
        if t < 3 and (t == 0 or S.tick % WATCH_GAP_TICKS == 0) then
          s.extraTries[ref] = t + 1
          local mode = s.mode
          if mode == nil then mode = (camo_mode(rawget(_G, "WEAPON_CAMO"))) end
          local base = s.rows[ref] or nil
          local out, n, counts = camo_entries(ref, mode, base ~= nil and base.id or nil)
          s.count[ref] = counts
          if n > 0 then
            local j = 1
            while j <= n and j <= CAMO_EXTRA_PER do
              s.extraN = s.extraN + 1
              s.extra[s.extraN] = out[j]
              j = j + 1
            end
            s.extraBuilt[ref] = true
            log("camo rows id=" .. tostring(base ~= nil and base.id or 0) .. " ref=" .. clip(ref, 28)
              .. " base=" .. tostring(counts.base) .. " special=" .. tostring(counts.special)
              .. " mastery=" .. tostring(counts.mastery) .. " extra=" .. tostring(counts.extra)
              .. " watch=" .. tostring(s.extraN)
              .. (n > CAMO_EXTRA_PER and (" clipped=" .. tostring(n - CAMO_EXTRA_PER)) or ""))
          elseif s.extraTries[ref] >= 3 then
            s.extraBuilt[ref] = true
            log("camo rows id=" .. tostring(base ~= nil and base.id or 0) .. " ref=" .. clip(ref, 28)
              .. " base=" .. tostring(counts.base) .. " special=0 mastery=0 extra=" .. tostring(counts.extra)
              .. " watch=" .. tostring(s.extraN)
              .. " - " .. tostring(counts.why or "the client listed no special or mastery row"))
          end
        end
      end
    end
    i = i + 1
  end
end

-- the military row per weapon once
local function camo_watch()
  local s = S.camo
  if s.n >= CAMO_WATCH_CAP then return end
  local refs, rn = {}, 0
  for ref in pairs(S.guns) do
    if type(ref) == "string" then
      rn = rn + 1
      refs[rn] = ref
    end
  end
  if rn < 1 then return end
  table.sort(refs)
  local i = 1
  while i <= rn do
    local ref = refs[i]
    if s.rows[ref] == nil and s.n < CAMO_WATCH_CAP then
      if not ours(ref) then
        s.rows[ref] = false
        if said("camo:watch:" .. ref) then
          vlog("camo watch " .. clip(ref, 28) .. " - not one of ours, so no row is read for it")
        end
      else
        local t = s.tries[ref] or 0
        if t < 3 and (t == 0 or S.tick % WATCH_GAP_TICKS == 0) then
          s.tries[ref] = t + 1
          local row, why = camo_row(ref)
          if row ~= nil then
            s.rows[ref] = row
            s.n = s.n + 1
            s.mode, s.key = row.mode, row.key
            log("camo watch id=" .. tostring(row.id) .. " ref=" .. clip(ref, 28) .. " tiers=" .. row.n
              .. " first=" .. tostring(row.th[1]) .. " last=" .. tostring(row.th[row.n])
              .. " mode=" .. tostring(row.mode) .. " key=" .. tostring(row.key))
          elseif s.tries[ref] == 1 then
            log("camo watch " .. clip(ref, 28) .. " - " .. tostring(why))
          end
        end
      end
    end
    i = i + 1
  end
end

-- queues one camo card once
local function camo_card(row, target, tier, value)
  local s = S.camo
  local key = tostring(row.id) .. ":" .. tostring(target)
  if s.done[key] == true then return false end
  if not want("camo") then return false end
  local ok = enqueue("camo", function() camo_show(row, target, tier, value) end)
  if ok then
    s.done[key] = true
    s.fired = s.fired + 1
  end
  return ok
end

-- walks one camo row thresholds
local function camo_step(row)
  local s = S.camo
  local rec = S.record(row.id)
  local v = rec_value(rec, CAMO_FIELDS)
  if v ~= nil then
    local k = tostring(row.id)
    local prev = s.seen[k]
    if prev == nil then
      s.seen[k] = v
      log("camo prime id=" .. tostring(row.id) .. " row=" .. tostring(row.ref) .. " value="
        .. tostring(v) .. " tiers=" .. row.n .. " hits=" .. count_passed(row.th, row.n, v)
        .. " raw=" .. rec_fields(rec))
    elseif v > prev then
      s.seen[k] = v
      local was = count_passed(row.th, row.n, prev)
      local now = count_passed(row.th, row.n, v)
      while was < now do
        was = was + 1
        local target = row.th[was]
        note_cross(s, k .. ":" .. tostring(target))
        log("camo cross id=" .. tostring(row.id) .. " row=" .. tostring(row.ref) .. " value="
          .. tostring(v) .. " was=" .. tostring(prev) .. " target=" .. tostring(target)
          .. " tier=" .. tostring(was))
        camo_card(row, target, was, v)
      end
    elseif v < prev then
      s.seen[k] = v
    end
  end
end

-- every camo row this poll
local function camo_check()
  local s = S.camo
  if s.n < 1 and s.extraN < 1 then return end
  local refs, rn = {}, 0
  for ref in pairs(s.rows) do
    rn = rn + 1
    refs[rn] = ref
  end
  table.sort(refs)
  local i = 1
  while i <= rn do
    local row = s.rows[refs[i]]
    if row ~= false then camo_step(row) end
    i = i + 1
  end
  local j = 1
  while j <= s.extraN do
    camo_step(s.extra[j])
    j = j + 1
  end
end

local S5 = { done = false, calls = 0, inN = 0, outN = 0, dropN = 0, drops = {},
             w = setmetatable({}, { __mode = "k" }) }

-- one tracker row per challenge id
local function s5compact(list)
  local n = #list
  if n < 2 then return n, 0 end
  local seen, w, r, dropped = {}, 0, 1, 0
  while r <= n do
    local e = list[r]
    local id = nil
    if type(e) == "table" then
      local _, v = member(e, "id")
      id = v
    end
    if id ~= nil and seen[id] == true then
      dropped = dropped + 1
      if #S5.drops < 6 then S5.drops[#S5.drops + 1] = tostring(id) end
    else
      if id ~= nil then seen[id] = true end
      w = w + 1
      if w ~= r then list[w] = e end
    end
    r = r + 1
  end
  if w < n then
    local i = w + 1
    while i <= n do
      list[i] = nil
      i = i + 1
    end
  end
  return w, dropped
end

-- wraps the tracker builder once brev
local function s5install()
  if S5.done then return true end
  local C = rawget(_G, "Challenge")
  if type(C) ~= "table" then return false end
  local k, f = member(C, "setupdailychallengesdatasource")
  if k == nil or type(f) ~= "function" then return false end
  if S5.w[f] == true then
    S5.done = true
    return true
  end
  local w = function(list, a, b, c, ...)
    if S.enabled and want(nil) and type(list) == "table" then
      S5.calls = S5.calls + 1
      local okc, kept, dropped = pcall(s5compact, list)
      if okc then
        S5.inN = (S5.inN or 0) + kept + dropped
        S5.outN = (S5.outN or 0) + kept
        S5.dropN = S5.dropN + dropped
      end
    end
    return f(list, a, b, c, ...)
  end
  if not pcall(function() C[k] = w end) then return false end
  S5.w[w] = true
  S5.done = true
  log("tracker: one row per challenge id, in the client's own list, before its count is set")
  return true
end

S.tracker = S5
S.tracker.install = s5install
S.hooks.camo = function()
  if not want(nil) then return end
  if S.tick % A.poll ~= 0 then return end
  pcall(camo_watch)
  pcall(camo_extra)
  pcall(camo_check)
end
S.probes.camos = function() return type(A.log) == "function" and type(S.camo) == "table" end

local dp = rawget(_G, "DebugPrint") or rawget(_G, "print")
if type(dp) == "function" then pcall(dp, "progression_tuning: part camos armed") end

if A.ready ~= nil then A.ready() end
