local PART = "reticles"

-- i love yanking and eating the reticles off my gun tbh

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
local function member(...) return A.member(...) end
local function fn_of(...) return A.fn_of(...) end
local function want(...) return A.want(...) end
local function count_passed(...) return A.count_passed(...) end
local function amounts_of(...) return A.amounts_of(...) end
local function rec_value(...) return A.rec_value(...) end
local function csv_table(...) return A.csv_table(...) end
local function csv_file(...) return A.csv_file(...) end

local CAMO_FIELDS = { "progress", "xp", "default" }
-- the kind the game reticle table answers to
local RET_KIND = 422
local RET_CAP = 36
local WATCH_GAP_TICKS = 32
local RET_POLL_TICKS = 8

local function enqueue(what, fn)
  local d = S.draw
  local q = d ~= nil and d.queue or nil
  if q == nil then
    if said("nosplash") then log("splash absent - no card is drawn") end
    return false
  end
  return q(what, fn)
end

local function ret_show(row, target, tier, value)
  local f = S.draw
  f = f ~= nil and f.ret or nil
  if f == nil then return end
  f(row, target, tier, value)
end

-- the reticle own tier list three ways
local function ret_tiers(id, cols, cell)
  local th, k = {}, 0
  local loot1 = nil
  local f = fn_of(rawget(_G, "GUNSMITH"), "getreticlechallengesforcategory")
  if f ~= nil then
    local ok, map = pcall(f, 0, id)
    if ok and type(map) == "table" then
      pcall(function()
        for key, e in pairs(map) do
          if type(e) == "table" then
            local _, amt = member(e, "amount")
            local v = tonumber(amt)
            if v ~= nil then
              k = k + 1
              th[k] = v
            end
            local lid = tonumber(key)
            if lid ~= nil and (loot1 == nil or lid < loot1) then loot1 = lid end
          end
        end
      end)
    end
  elseif said("retgunsmith") then
    log("reticle tiers - GUNSMITH.getreticlechallengesforcategory unavailable, the row's own amount is read")
  end
  if k > 0 then
    if k > 1 then table.sort(th) end
    return th, k, loot1
  end
  local amount = cell
  local df = fn_of(rawget(_G, "Challenge"), "getreticlechallengedata")
  if df ~= nil and type(cols) == "table" then
    local okd, row = pcall(df, cols.id, id)
    if okd and type(row) == "table" then
      local _, amt = member(row, "amount")
      if amt ~= nil then amount = amt end
      local _, lot = member(row, "loot")
      if type(lot) == "string" then
        for tok in string.gmatch(lot, "[^|]+") do
          local lid = tonumber(tok)
          if lid ~= nil and loot1 == nil then loot1 = lid end
          break
        end
      end
    end
  elseif said("retdata") then
    log("reticle tiers - Challenge.getreticlechallengedata unavailable, the row's own amount is read")
  end
  local th2, k2 = amounts_of(amount)
  return th2, k2, loot1
end

-- the optic rows this match can see
local function ret_rows()
  local s = S.ret
  if s.built then return end
  if s.tries >= 3 then return end
  if s.tries > 0 and S.tick % WATCH_GAP_TICKS ~= 0 then return end
  s.tries = s.tries + 1
  if S.camo.mode == nil and s.tries < 3 then return end
  local t = csv_table("reticleChallenges")
  local cols = type(t) == "table" and t.cols or nil
  if type(cols) ~= "table" then
    s.built = true
    s.why = "CSV.reticleChallenges unavailable in this VM"
    log("reticle rows - " .. s.why)
    return
  end
  local f = fn_of(rawget(_G, "StringTable"), "tablereadallrows")
  if f == nil then
    s.built = true
    s.why = "StringTable.tablereadallrows unavailable in this VM"
    log("reticle rows - " .. s.why)
    return
  end
  local idcol = cols.id
  local ok, rows = pcall(f, csv_file(t), { id = idcol, ref = cols.ref, amount = cols.amount }, idcol)
  if not ok or type(rows) ~= "table" then
    s.built = true
    s.why = "tablereadallrows answered no table for reticleChallenges"
    log("reticle rows - " .. s.why)
    return
  end
  local mode = S.camo.mode
  local token = nil
  if mode == 2 then
    token = "_zm_"
  elseif mode == 1 then
    token = "_mp_"
  elseif mode == 3 then
    token = "_wz_"
  elseif mode == 4 then
    token = "_ob_"
  end
  local pick, pn = {}, 0
  local all, an = {}, 0
  local zm = 0
  pcall(function()
    for key, row in pairs(rows) do
      local id, ref, cell = nil, nil, nil
      if type(row) == "table" then
        local _, vid = member(row, "id")
        local _, vref = member(row, "ref")
        local _, vamt = member(row, "amount")
        id = tonumber(vid)
        if type(vref) == "string" then ref = vref end
        cell = vamt
      end
      if id == nil then id = tonumber(key) end
      if id ~= nil then
        an = an + 1
        all[an] = { id = id, ref = ref or "-" }
        if type(ref) == "string" and string.find(ref, "_zm_", 1, true) ~= nil then zm = zm + 1 end
        local keep = true
        if token ~= nil then
          keep = type(ref) == "string" and string.find(ref, token, 1, true) ~= nil
        end
        if keep then
          pn = pn + 1
          pick[pn] = { id = id, ref = ref or "-", cell = cell }
        end
      end
    end
  end)
  local src, sn = pick, pn
  if sn < 1 then
    src = all
    sn = an
  end
  -- the rows carrying the most stored progress first
  local val = {}
  for j = 1, sn do
    val[src[j]] = rec_value(S.record(src[j].id), CAMO_FIELDS) or 0
  end
  table.sort(src, function(a, b)
    if val[a] ~= val[b] then return val[a] > val[b] end
    return a.id < b.id
  end)
  s.kind = RET_KIND
  local i = 1
  while i <= sn and s.n < RET_CAP do
    local r = src[i]
    local th, k, loot1 = ret_tiers(r.id, cols, r.cell)
    if k > 0 then
      s.n = s.n + 1
      s.rows[s.n] = { id = r.id, th = th, n = k, ref = r.ref, loot1 = loot1 }
    end
    i = i + 1
  end
  s.nzm = zm
  s.built = true
end

-- queues one reticle card once
local function ret_card(row, target, tier, value)
  local s = S.ret
  local key = tostring(row.id) .. ":" .. tostring(target)
  if s.done[key] == true then return false end
  if not want("camo") then return false end
  local ok = enqueue("camo", function() ret_show(row, target, tier, value) end)
  if ok then
    s.done[key] = true
  end
  return ok
end

-- every reticle row this poll
local function ret_check()
  local s = S.ret
  if s.n < 1 then return end
  local i = 1
  while i <= s.n do
    local row = s.rows[i]
    local rec = S.record(row.id)
    local v = rec_value(rec, CAMO_FIELDS)
    if v ~= nil then
      local k = tostring(row.id)
      local prev = s.seen[k]
      if prev == nil then
        s.seen[k] = v
      elseif v > prev then
        s.seen[k] = v
        local was = count_passed(row.th, row.n, prev)
        local now = count_passed(row.th, row.n, v)
        while was < now do
          was = was + 1
          local target = row.th[was]
          ret_card(row, target, was, v)
        end
      elseif v < prev then
        s.seen[k] = v
      end
    end
    i = i + 1
  end
end

S.hooks.ret = function()
  if not want(nil) then return end
  if S.tick % A.poll ~= 0 then return end
  if S.tick % RET_POLL_TICKS ~= 0 then return end
  pcall(ret_rows)
  pcall(ret_check)
end
S.probes.reticles = function() return type(A.log) == "function" and type(S.ret) == "table" end

local dp = rawget(_G, "DebugPrint") or rawget(_G, "print")
if type(dp) == "function" then pcall(dp, "progression_tuning: part reticles armed") end

if A.ready ~= nil then A.ready() end
