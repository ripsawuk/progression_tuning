local PART = "challenges"

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
local function numlist(...) return A.numlist(...) end
local function count_passed(...) return A.count_passed(...) end
local function note_cross(...) return A.note_cross(...) end
local function rec_value(...) return A.rec_value(...) end
local function rec_fields(...) return A.rec_fields(...) end

local CHAL_FIELDS = { "default", "progress", "xp" }
local CHAL_WATCH_CAP = 12
local WATCH_GAP_TICKS = 32
local WEEK_POLL_TICKS = 16
local KIND_DAILY = 438
local KIND_WEEKLY = 585
local KIND_STICKER = 429

local function enqueue(what, fn)
  local d = S.draw
  local q = d ~= nil and d.queue or nil
  if q == nil then
    if said("nosplash") then log("splash absent - no card is drawn") end
    return false
  end
  return q(what, fn)
end

local function chal_show(row, target, value)
  local f = S.draw
  f = f ~= nil and f.chal or nil
  if f == nil then return end
  f(row, target, value)
end

-- the daily and weekly rows to watch
local function chal_rows()
  local s = S.chal
  if s.built then return end
  if s.tries >= 4 then return end
  if s.tries > 0 and S.tick % WATCH_GAP_TICKS ~= 0 then return end
  local ch = rawget(_G, "Challenge")
  if type(ch) ~= "table" then return end
  s.tries = s.tries + 1
  local gf = fn_of(ch, "getchallengesforcurrentgamemode")
  local wf = fn_of(ch, "getweeklychallenges")
  if gf == nil then s.why = "no Challenge.getchallengesforcurrentgamemode" end
  local seen = {}
  -- keeps one challenge row
  local function add(id, th, k, kind, ref)
    if id == nil or k < 1 or s.n >= CHAL_WATCH_CAP then return false end
    if seen[id] == true then return false end
    seen[id] = true
    s.n = s.n + 1
    s.rows[s.n] = { id = id, th = th, n = k, kind = kind,
                    ref = (type(ref) == "string" and ref or "-") }
    return true
  end
  -- the row own target list
  local function thresholds(e)
    local th, k = {}, 0
    local _, amt = member(e, "amount")
    if type(amt) == "string" then
      local l, m = numlist(amt)
      local j = 1
      while j <= m do
        th[j] = l[j]
        k = k + 1
        j = j + 1
      end
    else
      local v = tonumber(amt)
      if v ~= nil then
        k = 1
        th[1] = v
      end
    end
    if k < 1 then
      local _, need = member(e, "amountNeeded")
      local v = tonumber(need)
      if v ~= nil and v > 0 then
        k = 1
        th[1] = v
      end
    end
    return th, k
  end
  -- dailies as a flat list
  local function harvest(list, kind)
    if type(list) ~= "table" then return end
    local i = 1
    while i <= #list and s.n < CHAL_WATCH_CAP do
      local e = list[i]
      if type(e) == "table" then
        local _, eid = member(e, "id")
        local id = tonumber(eid)
        local th, k = thresholds(e)
        local _, kk = member(e, "kind")
        local kd = tonumber(kk)
        if kd == nil then kd = kind end
        local _, rf = member(e, "ref")
        if add(id, th, k, kd, rf) then s.dailyN = s.dailyN + 1 end
      end
      i = i + 1
    end
  end
  -- weeklies as a flat list ranked by ratio
  local function harvest_flat(list, kind)
    if type(list) ~= "table" then return end
    local cand, cn = {}, 0
    pcall(function()
      local i = 1
      while i <= #list do
        local e = list[i]
        if type(e) == "table" then
          local _, eid = member(e, "achievementID")
          local id = tonumber(eid)
          local _, row = member(e, "data")
          if id ~= nil and type(row) == "table" then
            local th, k = thresholds(row)
            local _, rf = member(row, "ref")
            local _, kk = member(row, "kind")
            local kd = tonumber(kk)
            if kd == nil then kd = kind end
            local _, pr = member(e, "progress")
            local v = rec_value(pr, CHAL_FIELDS)
            if k > 0 then
              cn = cn + 1
              cand[cn] = { id = id, th = th, n = k, ref = rf, v = v, t = th[1], kind = kd }
            end
          end
        end
        i = i + 1
      end
    end)
    local i, j = 1, 2
    while j <= cn do
      local x = cand[j]
      i = j - 1
      while i >= 1 and (cand[i].v or 0) * x.t < (x.v or 0) * cand[i].t do
        cand[i + 1] = cand[i]
        i = i - 1
      end
      cand[i + 1] = x
      j = j + 1
    end
    i = 1
    while i <= cn and s.n < CHAL_WATCH_CAP do
      if add(cand[i].id, cand[i].th, cand[i].n, cand[i].kind, cand[i].ref) then
        s.weeklyN = s.weeklyN + 1
      end
      i = i + 1
    end
  end
  -- one row from a nested list
  local function one(e, kind)
    local _, eid = member(e, "id")
    local id = tonumber(eid)
    if id == nil then return false end
    local th, k = thresholds(e)
    local _, kk = member(e, "kind")
    local kd = tonumber(kk)
    if kd == nil then kd = kind end
    local _, rf = member(e, "ref")
    return add(id, th, k, kd, rf)
  end
  -- weeklies as groups
  local function harvest_nested(list, kind)
    if type(list) ~= "table" then return end
    local i = 1
    while i <= #list and s.n < CHAL_WATCH_CAP do
      local e = list[i]
      if type(e) == "table" then
        if not one(e, kind) then
          local j = 1
          while j <= #e and s.n < CHAL_WATCH_CAP do
            local b = e[j]
            if type(b) == "table" and one(b, kind) then
              s.weeklyN = s.weeklyN + 1
            end
            j = j + 1
          end
        else
          s.weeklyN = s.weeklyN + 1
        end
      end
      i = i + 1
    end
  end
  if gf ~= nil then
    local ok, list = pcall(gf, 0)
    if ok then harvest(list, KIND_DAILY) else s.why = "getchallengesforcurrentgamemode raised" end
  end
  local wt = rawget(_G, "WeeklyChallenge")
  local allf = fn_of(wt, "getallweeklychallenges")
  if allf ~= nil then
    local ok, list = pcall(allf, 0, { includeComplete = false })
    if ok and type(list) == "table" then
      harvest_flat(list, KIND_WEEKLY)
    else
      s.why = "WeeklyChallenge.getallweeklychallenges raised"
    end
  end
  if s.weeklyN < 1 then
    local ek = fn_of(ch, "GetAEKindID")
    if wf ~= nil and ek ~= nil then
      local okk, ekid = pcall(ek, "ae_kind_weekly")
      if okk and ekid ~= nil then
        local ok, list = pcall(wf, 0, ekid)
        if ok then harvest_nested(list, KIND_WEEKLY) end
        if s.weeklyN < 1 then s.why = "no weekly row was handed over" end
      else
        s.why = "Challenge.GetAEKindID refused ae_kind_weekly"
      end
    elseif wf == nil then
      s.why = "no Challenge.getweeklychallenges and no WeeklyChallenge in this VM"
    end
  end
  if s.n > 0 or s.tries >= 4 then s.built = true end
  if s.tries == 1 or s.n > 0 then
    log("chal watch n=" .. s.n .. " daily=" .. s.dailyN .. " weekly=" .. s.weeklyN
      .. " tries=" .. s.tries .. " why=" .. tostring(s.why or "ok"))
    local wi = 1
    while wi <= s.n and wi <= 6 do
      local row = s.rows[wi]
      log("chal watch row id=" .. tostring(row.id) .. " kind=" .. tostring(row.kind)
        .. " ref=" .. clip(tostring(row.ref), 34) .. " target=" .. tostring(row.th[1]))
      wi = wi + 1
    end
  end
end

-- queues one daily card once
local function chal_card(row, target, tier, value)
  local s = S.chal
  local key = tostring(row.id) .. ":" .. tostring(target)
  if s.done[key] == true then return false end
  if not want("chal") then return false end
  local ok = enqueue("chal", function() chal_show(row, target, value) end)
  if ok then
    s.done[key] = true
    s.fired = s.fired + 1
  end
  return ok
end

-- every watched challenge row this poll
local function chal_check()
  local s = S.chal
  if s.n < 1 then return end
  local i = 1
  while i <= s.n do
    local row = s.rows[i]
    local rec = S.record(row.id)
    local v = rec_value(rec, CHAL_FIELDS)
    if v ~= nil then
      local k = tostring(row.id)
      local prev = s.seen[k]
      if prev == nil then
        s.seen[k] = v
        vlog("daily prime id=" .. tostring(row.id) .. " row=" .. tostring(row.ref) .. " value="
          .. tostring(v) .. " target=" .. tostring(row.th[1]) .. " hits="
          .. count_passed(row.th, row.n, v) .. " raw=" .. rec_fields(rec))
      elseif v > prev then
        s.seen[k] = v
        local was = count_passed(row.th, row.n, prev)
        local now = count_passed(row.th, row.n, v)
        while was < now do
          was = was + 1
          local target = row.th[was]
          note_cross(s, k .. ":" .. tostring(target))
          vlog("daily cross id=" .. tostring(row.id) .. " row=" .. tostring(row.ref) .. " value="
            .. tostring(v) .. " was=" .. tostring(prev) .. " target=" .. tostring(target))
          chal_card(row, target, was, v)
        end
      elseif v < prev then
        s.seen[k] = v
      end
    end
    i = i + 1
  end
end

-- the weekly row own data
local function week_data(id)
  local f = fn_of(rawget(_G, "WeeklyChallenge"), "getweeklychallengedatabyid")
  if f == nil then return nil end
  local ok, row = pcall(f, id)
  if ok and type(row) == "table" then return row end
  return nil
end

-- the weekly own target
local function week_target(row)
  if type(row) ~= "table" then return nil end
  local _, amt = member(row, "amount")
  local t = tonumber(amt)
  if t == nil then
    local l = numlist(amt)
    if l[1] ~= nil then t = l[1] end
  end
  if t == nil then
    local _, need = member(row, "amountNeeded")
    t = tonumber(need)
  end
  return t
end

-- eight ids for the sweep line
local function sweep_sample(t)
  local ids, m = {}, 0
  for id in pairs(t) do
    if m < 8 then
      m = m + 1
      ids[m] = tostring(id)
    end
  end
  if m < 1 then return "none" end
  table.sort(ids)
  return table.concat(ids, ",")
end

-- sweeps every weekly row and cards the crossings
local function chal_sweep()
  local s = S.chal
  local sw = s.sweep
  if S.tick % WEEK_POLL_TICKS ~= 0 then return end
  local ch = rawget(_G, "Challenge")
  local names = { "ae_kind_zm_weekly", "ae_kind_weekly", "ae_kind_weekly_mastery" }
  local kinds, nk = {}, 0
  local byname = {}
  local ek = fn_of(ch, "GetAEKindID")
  if ek ~= nil then
    local i = 1
    while i <= 3 do
      local okk, v = pcall(ek, names[i])
      if okk and tonumber(v) ~= nil then
        nk = nk + 1
        kinds[nk] = tonumber(v)
        byname[i] = tonumber(v)
      end
      i = i + 1
    end
  end
  nk = nk + 1
  kinds[nk] = KIND_STICKER
  local now, nn = {}, 0
  local done_n, prog_n = 0, 0
  local src = nil
  local counts = {}
  -- folds one store slice into the sweep
  local function take(t, kind)
    if type(t) ~= "table" then return 0 end
    local c = 0
    for key, e in pairs(t) do
      if type(e) == "table" then
        c = c + 1
        local id = tonumber(key)
        if id ~= nil and now[id] == nil then
          local _, st = member(e, "status")
          local v = rec_value(e, CHAL_FIELDS)
          now[id] = { st = tonumber(st), v = v, k = kind }
          nn = nn + 1
          if now[id].st ~= nil and now[id].st ~= 1 and now[id].st ~= 4 then done_n = done_n + 1 end
          if v ~= nil and v > 0 then prog_n = prog_n + 1 end
        end
      end
    end
    return c
  end
  local fork = fn_of(rawget(_G, "OnlineChallenges"), "getchallengesprogressforkind")
  if fork ~= nil then
    local i = 1
    while i <= nk do
      local okk, tt = pcall(fork, 0, kinds[i])
      if okk and type(tt) == "table" then
        counts[kinds[i]] = take(tt, kinds[i])
        src = "fork"
      end
      i = i + 1
    end
  end
  if src == nil then
    local allf = fn_of(rawget(_G, "WeeklyChallenge"), "getallweeklychallenges")
    if allf ~= nil then
      local ok, list = pcall(allf, 0, { includeComplete = false })
      if ok and type(list) == "table" then
        src = "list"
        local i = 1
        while i <= #list do
          local e = list[i]
          if type(e) == "table" then
            local _, eid = member(e, "achievementID")
            local id = tonumber(eid)
            if id ~= nil and now[id] == nil then
              local _, drow = member(e, "data")
              local _, rf = member(drow, "ref")
              local _, kd = member(drow, "kind")
              local v = rec_value(e, CHAL_FIELDS)
              now[id] = { present = true, st = nil, v = v,
                          t = week_target(drow), ref = rf, k = tonumber(kd) }
              nn = nn + 1
              if v ~= nil and v > 0 then prog_n = prog_n + 1 end
            end
          end
          i = i + 1
        end
      end
    end
  end
  if src == nil then
    sw.kinds = kinds
    if said("weeksweepnil") then
      log("chal sweep unavailable - no OnlineChallenges.getchallengesprogressforkind and no "
        .. "WeeklyChallenge.getallweeklychallenges in this VM")
    end
    return
  end
  sw.src = src
  sw.kinds = kinds
  -- the three kinds as text
  local function kind_txt()
    if nk < 1 then return "none" end
    local out = {}
    local i = 1
    while i <= nk do
      out[i] = tostring(kinds[i])
      i = i + 1
    end
    return table.concat(out, ",")
  end
  -- how many rows each kind handed over
  local function rows_txt()
    local out = {}
    local i = 1
    while i <= nk do
      out[i] = tostring(counts[kinds[i]] or 0)
      i = i + 1
    end
    if nk < 1 then return "0/0/0" end
    return table.concat(out, "/")
  end
  if not sw.primed then
    sw.primed = true
    sw.prev = now
    sw.n, sw.done, sw.prog = nn, done_n, prog_n
    log("chal sweep src=" .. src .. " kind=" .. kind_txt() .. " n=" .. nn
      .. " done=" .. done_n .. " prog=" .. prog_n .. " sample=" .. sweep_sample(now))
    log("chal sweep kinds zm_weekly=" .. tostring(byname[1]) .. " weekly=" .. tostring(byname[2])
      .. " mastery=" .. tostring(byname[3]) .. " sticker=" .. tostring(KIND_STICKER)
      .. " rows=" .. rows_txt())
    return
  end
  local prev = sw.prev
  local order, on = {}, 0
  for id in pairs(now) do
    on = on + 1
    order[on] = id
  end
  table.sort(order)
  local i = 1
  while i <= on do
    local id = order[i]
    local e = now[id]
    local was = prev[id]
    local wst = nil
    if was ~= nil then wst = was.st end
    local crossed = false
    if e.st ~= nil then
      crossed = (e.st ~= 1 and e.st ~= 4) and (was == nil or wst == 1 or wst == 4)
    elseif e.t ~= nil and e.v ~= nil and e.v >= e.t then
      crossed = was == nil or was.v == nil or was.v < e.t
    end
    if crossed then
      if e.ref == nil and e.k ~= KIND_STICKER then
        local drow = week_data(id)
        if drow ~= nil then
          if e.t == nil then e.t = week_target(drow) end
          local _, rf = member(drow, "ref")
          if type(rf) == "string" then e.ref = rf end
          local _, kd = member(drow, "kind")
          local kk = tonumber(kd)
          if kk ~= nil then e.k = kk end
        end
      end
      local ref = e.ref or "-"
      local t = e.t
      if t == nil then t = e.v end
      if t == nil then t = 0 end
      local kind = e.k or KIND_WEEKLY
      local v = e.v or 0
      s.crossN = s.crossN + 1
      log("chal week cross id=" .. tostring(id) .. " ref=" .. clip(tostring(ref), 34) .. " was="
        .. tostring(wst) .. " now=" .. tostring(e.st) .. " v=" .. tostring(v) .. "/" .. tostring(t))
      chal_card({ id = id, ref = ref, kind = kind }, t, 1, v)
    end
    i = i + 1
  end
  if src == "list" then
    local gone, gn = {}, 0
    for id, was in pairs(prev) do
      if now[id] == nil and was.present == true then
        gn = gn + 1
        gone[gn] = id
      end
    end
    table.sort(gone)
    -- a vanished row still needs the game to agree
    local gate = fn_of(ch, "IsChallengeComplete")
    if gate == nil and said("weekgate") then
      log("chal week gate - no Challenge.IsChallengeComplete in this VM, the vanished row is carded")
    end
    local gi = 1
    while gi <= gn do
      local id = gone[gi]
      local was = prev[id]
      local complete = "unknown"
      if gate ~= nil then
        local ok, ans = pcall(gate, 0, id)
        if ok and ans == true then
          complete = "true"
        elseif ok and ans == false and S.record(id) ~= nil then
          complete = "false"
        end
      end
      local t = was.t
      if t == nil then t = was.v end
      if t == nil then t = 0 end
      s.crossN = s.crossN + 1
      log("chal week cross id=" .. tostring(id) .. " ref=" .. clip(tostring(was.ref or "-"), 34)
        .. " was=1 now=gone v=" .. tostring(t) .. "/" .. tostring(t) .. " complete=" .. complete)
      if complete ~= "false" then
        chal_card({ id = id, ref = was.ref or "-", kind = was.k or KIND_WEEKLY }, t, 1, t)
      end
      gi = gi + 1
    end
  end
  sw.prev = now
  if nn ~= sw.n then
    sw.n, sw.done, sw.prog = nn, done_n, prog_n
    log("chal sweep src=" .. src .. " kind=" .. kind_txt() .. " n=" .. nn
      .. " done=" .. done_n .. " prog=" .. prog_n .. " sample=" .. sweep_sample(now))
  end
end

S.hooks.chal = function()
  if not want(nil) then return end
  if S.tick % A.poll ~= 0 then return end
  pcall(chal_rows)
  pcall(chal_check)
  pcall(chal_sweep)
end
S.probes.challenges = function() return type(A.log) == "function" and type(S.chal) == "table" end

local utc_say = rawget(_G, "DebugPrint") or rawget(_G, "print")

-- one line from this part
local function utc_out(s)
  if type(utc_say) == "function" then pcall(utc_say, s) end
end

-- a member by its plain name or its hash
local function utc_at(tbl, name)
  if type(tbl) ~= "table" then return nil, nil end
  local ok, v = pcall(function() return tbl[name] end)
  if ok and v ~= nil then return name, v end
  local h = rawget(_G, "xhash")
  if type(h) ~= "function" then return nil, nil end
  local okh, key = pcall(h, name)
  if not okh or key == nil then return nil, nil end
  local ok2, v2 = pcall(function() return tbl[key] end)
  if ok2 and v2 ~= nil then return key, v2 end
  local want = string.match(tostring(key), "#x(%x+)")
  if want == nil then return nil, nil end
  want = string.gsub(string.sub(want, 2), "^0+", "")
  local got, gkey = nil, nil
  pcall(function()
    for k, val in pairs(tbl) do
      local d = string.match(tostring(k), "#x(%x+)")
      if d ~= nil then d = string.gsub(string.sub(d, 2), "^0+", "") end
      if d ~= nil and d == want then got, gkey = val, k end
    end
  end)
  return gkey, got
end

-- packs a call and spreads it back whole
local utc_up = unpack

local function utc_pack(...) return { n = select("#", ...), ... } end

local function utc_spread(t, i)
  if utc_up ~= nil then return utc_up(t, i, t.n) end
  return table.unpack(t, i, t.n)
end

-- the cod getter answer when it is a number
local function utc_cod()
  local _, f = utc_at(rawget(_G, "CoD"), "GetUTC")
  if type(f) ~= "function" then return nil end
  local ok, v = pcall(f)
  if ok and type(v) == "number" then return v end
  return nil
end

-- the original number or a filled one
local function utc_call(orig, ...)
  local r = utc_pack(pcall(orig, ...))
  if r[1] and type(r[2]) == "number" then return utc_spread(r, 2) end
  local v = utc_cod()
  if v ~= nil then return v end
  return 0
end

-- the pushed and hashed keys for a member name
local function utc_push(name)
  local cu = rawget(_G, "CLUA")
  if type(cu) == "table" and type(cu.PushXHash) == "function" then
    local ok, k = pcall(cu.PushXHash, name)
    if ok and k ~= nil then return k end
  end
  return nil
end

local function utc_hash(name)
  local h = rawget(_G, "xhash")
  if type(h) ~= "function" then return nil end
  local ok, k = pcall(h, name)
  if ok and k ~= nil then return k end
  return nil
end

-- arms the one fill once per vm
local function utc_arm()
  if S.utc == true then return true end
  local tbl = rawget(_G, "Engine")
  local key, f = utc_at(tbl, "GetUTC")
  if type(f) ~= "function" then return false end
  local function w(...) return utc_call(f, ...) end
  if not pcall(function() tbl[key] = w end) then return false end
  -- replaces a real member only
  local function put(k)
    if k == nil or k == key then return end
    if rawget(tbl, k) ~= f then return end
    pcall(function() rawset(tbl, k, w) end)
  end
  put(utc_push("GetUTC"))
  put(utc_hash("GetUTC"))
  S.utc = true
  return true
end

local utc_ok = false
pcall(function() utc_ok = utc_arm() end)
utc_out("progression_tuning: utc fill " .. (utc_ok and "armed" or "absent"))

local dp = rawget(_G, "DebugPrint") or rawget(_G, "print")
if type(dp) == "function" then pcall(dp, "progression_tuning: part challenges armed") end

if A.ready ~= nil then A.ready() end
