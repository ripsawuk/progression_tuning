local PART = "options"

local S = rawget(_G, "ProgressionTuning")
if type(S) ~= "table" then
  S = { parts = {}, hooks = {}, probes = {}, api = {}, g11 = {}, scope = {} }
  rawset(_G, "ProgressionTuning", S)
end
if S.parts[PART] == true then return end
S.parts[PART] = true
local A = S.api

-- logs once the core is up
local function log(s)
  local f = A.log
  if type(f) == "function" then f(s) end
end

-- says a thing once per vm
local function once(key)
  local f = A.said
  if type(f) == "function" then return f(PART .. key) end
  local k = "P_" .. key
  if S.probes[k] then return false end
  S.probes[k] = true
  return true
end

-- the returns and their count
local function pack(...) return { n = select("#", ...), ... } end

-- re emits a packed return
local function unpackAll(t)
  if unpack ~= nil then return unpack(t, 1, t.n) end
  return table.unpack(t, 1, t.n)
end

-- the listed counts and their row index
local VALUES = { 0, 1, 5, 10, 25, 99 }
local LABELS = { "0", "1", "5", "10", "25", "99" }
local NAME = "XP Token Amount"
local DESC = "Sets how many of every Level and Weapon 2XP token you own."
  .. " Battle Pass tokens are not affected."
local DROP = "Dropdown"
local ID = "pt_token_amount"

-- the permanent row beside it
local NAME2 = "Enable Double XP"
local DESC2 = "Keeps Level and Weapon Double XP active at all times while on."
  .. " Your tokens are not used up. Turn off to go back to your own tokens."
local TOG = "ToggleButton"
local ID2 = "pt_permanent"
local ONOFF = { "Off", "On" }
-- the row our two sit behind
local ANCHOR = "5a6d0000000000be"

-- the rows other parts add in their order
local EXT, EXTBY = {}, {}

-- the page row ids the menu builds a second time
local DUP = {}
for _, t in next, {
  "a1", "a2", "a3", "a4", "a5", "a9", "ad", "ae", "af", "b0", "b1", "b2",
  "b3", "b4", "b5", "b6", "b7", "b8", "b9", "ba", "bb", "bc", "bd", "be",
  "a6", "a7", "a8", "ab", "ac", "bf", "c0", "c2", "c1", "c3", "c4", "aa",
} do DUP["5a6d0000000000" .. t] = true end

-- the four option members by their printed hash
local SLOTS = {
  { name = "sections", hex = "7bf7f57679e8d050" },
  { name = "data_a", hex = "e7686f7a9907efd8" },
  { name = "data_b", hex = "9f6c4b08602983fb" },
  { name = "createoptionlist", word = "createoptionlist" },
}

-- the listed value at or below a count
local function pick(n)
  local i = #VALUES
  while i > 1 and n < VALUES[i] do i = i - 1 end
  return i
end

-- the smallest count as a row index
local function selected()
  local T = S.tokens
  local c = (type(T) == "table") and T.c or nil
  if type(c) ~= "table" then return 1 end
  local lo = nil
  local i = 1
  while i <= #c do
    local v = tonumber(c[i])
    if v ~= nil and (lo == nil or v < lo) then lo = v end
    i = i + 1
  end
  if lo == nil then return 1 end
  return pick(lo)
end

-- sets every count through the tokens part
local function setall(v)
  local n = VALUES[v]
  local T = S.tokens
  if n == nil or type(T) ~= "table" or type(T.set) ~= "function" then return end
  T.set(n)
end

-- answers the page for value and action
local function answer(c, v)
  if type(v) == "number" then setall(v) else return selected() end
end

-- answers and sets the permanent flag
local function flip(c, v)
  local T = S.tokens
  if type(T) ~= "table" then return 1 end
  if type(v) == "number" and type(T.perm) == "function" then T.perm(v == 2) end
  return (T.x == 1) and 2 or 1
end

-- the printed form of a hash key
local function printed(k)
  local ok, s = pcall(tostring, k)
  if not ok or type(s) ~= "string" then return nil end
  local h = string.match(s, "#x(%x+)")
  if h == nil then return nil end
  return string.lower(h)
end

-- true when a key is the printed hash
local function iskey(k, hex)
  local h = printed(k)
  if h == nil then return false end
  h = string.gsub(h, "^0+", "")
  local b = string.gsub(hex, "^0+", "")
  return string.sub(h, 1, #b) == b or string.sub(h, -#b) == b
end

local KEYS = {}

-- the member scan by printed hash
local function scan(O, hex)
  local found, fn = nil, nil
  pcall(function()
    local a, b = next(O)
    while a ~= nil do
      if found == nil and type(b) == "function" and iskey(a, hex) then found, fn = a, b end
      a, b = next(O, a)
    end
  end)
  return found, fn
end

-- a member by its hashed name
local function named(O, word)
  local h = rawget(_G, "xhash")
  if type(h) ~= "function" then return nil, nil end
  local okh, key = pcall(h, word)
  if not okh or key == nil then return nil, nil end
  local okv, f = pcall(function() return O[key] end)
  if okv and type(f) == "function" then return key, f end
  local hex = printed(key)
  if hex == nil then return nil, nil end
  return scan(O, hex)
end

-- the key and function of one member
local function slot(entry)
  local O = rawget(_G, "OPTIONS")
  if type(O) ~= "table" then return nil, nil end
  local k = KEYS[entry.name]
  if k ~= nil then
    local ok, f = pcall(rawget, O, k)
    if ok and type(f) == "function" then return k, f end
    KEYS[entry.name] = nil
  end
  local found, fn = nil, nil
  if entry.word ~= nil then
    found, fn = named(O, entry.word)
  else
    found, fn = scan(O, entry.hex)
  end
  if found ~= nil then KEYS[entry.name] = found end
  return found, fn
end

-- the slot and its printed hash or a miss
local function find(entry)
  local k, f = slot(entry)
  if k == nil then
    return nil, nil
  end
  return k, f
end

-- a leaf is an item not a list
local function leaf(t)
  if type(t) ~= "table" then return false end
  local k, v = next(t)
  if k == nil or next(t, k) ~= nil then return false end
  if type(v) == "table" then return printed(v) ~= nil end
  return true
end

-- the item list inside whatever shape
local function itemsOf(res)
  if type(res) ~= "table" or type(res[1]) ~= "table" then return nil end
  local first = res[1]
  if leaf(first) then return res end
  local inner, fall = nil, nil
  for _, v in next, first do
    if type(v) == "table" then
      if type(v[1]) == "table" then
        if inner == nil then inner = v end
      elseif fall == nil then
        fall = v
      end
    end
  end
  if inner == nil then inner = fall end
  if inner == nil then return nil end
  if type(inner[1]) == "table" and leaf(inner[1]) then return inner end
  return itemsOf(inner)
end

-- the key an item carries its id under
local function idKey(item)
  local k = next(item)
  if k == nil then return nil end
  if next(item, k) == nil then return k end
  k = nil
  for a, b in next, item do
    if k == nil and printed(b) ~= nil then k = a end
  end
  return k
end

-- appends our item when it is not there
local function addRow(items, id, key)
  if type(items) ~= "table" or leaf(items) then return false end
  local k = key
  if k == nil then
    if type(items[1]) ~= "table" then return false end
    k = idKey(items[1])
  end
  if k == nil then return false end
  local i = 1
  while i <= #items do
    local it = items[i]
    if type(it) == "table" and rawget(it, k) == id then return false end
    i = i + 1
  end
  local it = { [k] = id }
  local ok, meta = pcall(getmetatable, items[1])
  if ok and meta ~= nil then pcall(setmetatable, it, meta) end
  items[#items + 1] = it
  return true
end

-- the printed hash of a value
local function hexOf(v)
  if type(v) == "string" then
    local s = string.lower(v)
    if string.match(s, "^0x%x+$") then return string.sub(s, 3) end
    if string.match(s, "^%x+$") then return s end
    return nil
  end
  return printed(v)
end

-- true when a value is the anchor row
local function isAnchor(v)
  local h = hexOf(v)
  if h == nil then return false end
  return string.sub(h, 1, #ANCHOR) == ANCHOR or string.sub(h, -#ANCHOR) == ANCHOR
end

-- ours appended in their own order
local function ours(out, n, mine)
  if mine[1] ~= nil then n = n + 1; out[n] = mine[1] end
  if mine[2] ~= nil then n = n + 1; out[n] = mine[2] end
  local i = 1
  while i <= #EXT do
    local it = mine[EXT[i].id]
    if it ~= nil then n = n + 1; out[n] = it end
    i = i + 1
  end
  return n
end

-- ours placed after the anchor on a copy
local function afterAnchor(items, key)
  local anchor, rest = nil, {}
  local mine = {}
  local i = 1
  while i <= #items do
    local it = items[i]
    local v = (type(it) == "table") and rawget(it, key) or nil
    if v == ID then
      if mine[1] == nil then mine[1] = it end
    elseif v == ID2 then
      if mine[2] == nil then mine[2] = it end
    elseif v ~= nil and EXTBY[v] ~= nil then
      if mine[v] == nil then mine[v] = it end
    else
      rest[#rest + 1] = it
      if anchor == nil and isAnchor(v) then anchor = #rest end
    end
    i = i + 1
  end
  local out, n = {}, 0
  i = 1
  while i <= #rest do
    n = n + 1
    out[n] = rest[i]
    if i == anchor then n = ours(out, n, mine) end
    i = i + 1
  end
  if anchor == nil then
    n = ours(out, n, mine)
  end
  return out
end

-- writes an order back in place
local function reorder(items, key)
  local out = afterAnchor(items, key)
  local old = #items
  local i = 1
  while i <= #out do
    items[i] = out[i]
    i = i + 1
  end
  while i <= old do
    items[i] = nil
    i = i + 1
  end
end

-- the item list holding our rows
local function findMine(t, depth, acc)
  if type(t) ~= "table" or depth > 4 then return nil end
  if type(t[1]) == "table" then
    acc.any = true
    local i = 1
    while i <= #t do
      local it = t[i]
      if type(it) == "table" then
        for _, v in next, it do
          if v == ID or v == ID2 or EXTBY[v] ~= nil then return t end
        end
      end
      i = i + 1
    end
  end
  for _, v in next, t do
    if type(v) == "table" then
      local found = findMine(v, depth + 1, acc)
      if found ~= nil then return found end
    end
  end
  return nil
end

-- moves our rows after the anchor
local function move(...)
  local acc = { any = false }
  local items = nil
  local total = select("#", ...)
  local i = 1
  while i <= total and items == nil do
    local v = select(i, ...)
    if type(v) == "table" and type(v[1]) == "table" then items = findMine(v, 0, acc) end
    i = i + 1
  end
  if items == nil then return end
  local key = idKey(items[1])
  if key == nil then return end
  reorder(items, key)
end

-- the debug tab id the menu publishes
local function debugId()
  local O = rawget(_G, "OPTIONS")
  local ids = type(O) == "table" and O.TabIds or nil
  if type(ids) ~= "table" then return nil end
  return ids.DEBUG
end

-- true when this table is the debug tab
local function isDebug(tab)
  local dbg = debugId()
  if dbg == nil or type(tab) ~= "table" then return false end
  for _, v in next, tab do
    if v == dbg then return true end
  end
  return false
end

-- the three values a row type takes
local TYPES = { ToggleButton = true, Dropdown = true, SliderBarWithEditBox = true }

-- the strings labels and functions of a bundle
local function split(t, sb)
  local strs, labs, fns = {}, nil, {}
  for k, v in next, t do
    if type(v) == "function" then
      fns[#fns + 1] = k
    elseif type(v) == "table" and type(v[1]) == "string" then
      labs = k
    elseif type(v) == "string" and not TYPES[v] and (sb == nil or v ~= sb) then
      strs[#strs + 1] = k
    end
  end
  return strs, labs, fns
end

-- true when a table is a real option bundle
local function isBundle(t, sb)
  if type(t) ~= "table" then return false end
  local strs, labs, fns = split(t, sb)
  return #strs == 2 and labs ~= nil and #fns == 2
end

-- the one stock bundle copied as a template
local TPL, TPLSB = nil, nil

-- our row in the page own shape
local function mkRow(id, name, desc, labels, kind, fn)
  local tpl = TPL
  if type(tpl) ~= "table" then return nil end
  local strs, labs, fns = split(tpl, TPLSB)
  if #strs ~= 2 or labs == nil or #fns ~= 2 then return nil end
  local row = {}
  for k, v in next, tpl do row[k] = v end
  local ok, meta = pcall(getmetatable, tpl)
  if ok and meta ~= nil then pcall(setmetatable, row, meta) end
  local a, b = strs[1], strs[2]
  local va, vb = rawget(tpl, a), rawget(tpl, b)
  local nameKey, descKey = a, b
  if type(va) == "string" and type(vb) == "string" and #va > #vb then nameKey, descKey = b, a end
  for k, v in next, tpl do
    if v == TPLSB then row[k] = id end
  end
  row[nameKey] = name
  row[descKey] = desc
  row[labs] = labels
  local i = 1
  while i <= #fns do
    row[fns[i]] = fn
    i = i + 1
  end
  for k, v in next, tpl do
    if TYPES[v] then row[k] = kind end
  end
  return row
end

-- the token row the options page shows
local function tokenRow() return mkRow(ID, NAME, DESC, LABELS, DROP, answer) end

-- the permanent row the options page shows
local function permRow() return mkRow(ID2, NAME2, DESC2, ONOFF, TOG, flip) end

-- the answer a row another part owns gives the page
local function extAnswer(rec)
  return function(c, v)
    local ok, on = pcall(rec.get)
    if not ok then on = false end
    if type(v) == "number" then
      pcall(rec.set, v == 2)
      ok, on = pcall(rec.get)
      if not ok then on = false end
    end
    if on == true then return 2 end
    return 1
  end
end

-- the row another part owns the options page shows
local function extRow(rec) return mkRow(rec.id, rec.name, rec.desc, ONOFF, TOG, rec.fn) end

-- adds a row another part owns to this page
local function optrow_add(spec)
  if type(spec) ~= "table" then return false end
  local id = spec.id
  if type(id) ~= "string" or id == "" then return false end
  if type(spec.get) ~= "function" or type(spec.set) ~= "function" then return false end
  if spec.kind ~= nil and spec.kind ~= "toggle" then return false end
  if id == ID or id == ID2 then return false end
  if EXTBY[id] ~= nil then return true end
  local rec = { id = id, name = tostring(spec.name or id), desc = tostring(spec.desc or ""),
    get = spec.get, set = spec.set }
  rec.fn = extAnswer(rec)
  EXT[#EXT + 1] = rec
  EXTBY[id] = rec
  return true
end

S.api.optrow_add = optrow_add

-- picks up the rows queued before this part
local function drain()
  local q = S.optrows
  if type(q) ~= "table" then return end
  local i = 1
  while i <= #q do
    pcall(optrow_add, q[i])
    i = i + 1
  end
end

pcall(drain)

-- the first stock id in a list
local function sibling(items)
  if type(items) ~= "table" or type(items[1]) ~= "table" then return nil end
  local k = idKey(items[1])
  if k == nil then return nil end
  local i = 1
  while i <= #items do
    local v = rawget(items[i], k)
    if v ~= nil and v ~= ID and v ~= ID2 and EXTBY[v] == nil then return v end
    i = i + 1
  end
  return nil
end

-- keeps a stock bundle as the template
local function tplGrab(id)
  if TPL ~= nil or id == nil then return end
  local O = rawget(_G, "OPTIONS")
  if type(O) ~= "table" then return end
  local _, f = slot(SLOTS[2])
  if f == nil then _, f = slot(SLOTS[3]) end
  if f == nil then return end
  local ok, res = pcall(f, id, 0)
  if not ok or type(res) ~= "table" or not isBundle(res, id) then return end
  for _, v in next, res do
    if v == id then TPL, TPLSB = res, id end
  end
end

-- answers our ids and passes the rest on
local function wrapData(cur)
  return function(id, ...)
    if id == ID or id == ID2 or EXTBY[id] ~= nil then
      local b = nil
      if id == ID then
        b = tokenRow()
      elseif id == ID2 then
        b = permRow()
      else
        b = extRow(EXTBY[id])
      end
      return b
    end
    local res = cur(id, ...)
    if TPL == nil and id ~= nil and type(res) == "table" and isBundle(res, id) then
      local found = false
      for _, v in next, res do
        if v == id then found = true end
      end
      if found then TPL, TPLSB = res, id end
    end
    return res
  end
end

-- the tail of an id in its printed form
local function tail(v)
  local h = hexOf(v)
  if type(h) ~= "string" then h = printed(v) end
  if type(h) ~= "string" then return nil end
  if #h > 16 then return string.sub(h, -16) end
  return h
end

-- true when an id is one the menu builds again
local function again(v)
  local h = tail(v)
  if h == nil then return false end
  return DUP[h] == true
end

-- drops the rows the menu builds again above us
local function strip(items, key)
  if type(items) ~= "table" or key == nil then return end
  local n, run = #items, 0
  while run < n do
    local it = items[run + 1]
    local v = (type(it) == "table") and rawget(it, key) or nil
    if v == nil or not again(v) then break end
    run = run + 1
  end
  if run == 0 then return end
  local i = 1
  while i + run <= n do
    items[i] = items[i + run]
    i = i + 1
  end
  while i <= n do
    items[i] = nil
    i = i + 1
  end
end

-- true when another wrapper holds the slot
local function over(O, key, w)
  if type(O) ~= "table" or key == nil or type(w) ~= "function" then return false end
  local ok, got = pcall(rawget, O, key)
  if not ok or type(got) ~= "function" then return false end
  return got ~= w
end

-- appends our rows to a debug list
local function wrapList(cur, key)
  local w
  w = function(tab, c, idx, ...)
    local res = pack(cur(tab, c, idx, ...))
    local ok = pcall(function()
      if debugId() == nil then return end
      if not isDebug(tab) then return end
      local items = itemsOf(res[1])
      local k = (type(items) == "table" and type(items[1]) == "table") and idKey(items[1]) or nil
      tplGrab(sibling(items))
      if over(rawget(_G, "OPTIONS"), key, w) then strip(items, k) end
      addRow(items, ID, k)
      addRow(items, ID2, k)
      local i = 1
      while i <= #EXT do
        addRow(items, EXT[i].id, k)
        i = i + 1
      end
    end)
    if not ok and once("raise") then log("options append raised") end
    return unpackAll(res)
  end
  return w
end

-- the final list wrapper the page is built from
local function wrapCreate(cur)
  return function(...)
    local res = pack(cur(...))
    if not pcall(move, ...) and once("move") then log("options move raised") end
    return unpackAll(res)
  end
end

-- the slot ledger one per member
local REG = {}
local INSTALLS = 3

-- what the slot holds now
local function state(O, cur, name)
  local rec = REG[name]
  if rec == nil then return "first" end
  if cur == rec.w then return "ours" end
  if O ~= rec.table then return "rebuilt" end
  if cur == rec.inner then return "restored" end
  return "moved"
end

-- installs one member when it is ours to install
local function place(O, k, cur, name, make)
  local st = state(O, cur, name)
  if st == "ours" then return true end
  if st == "moved" then
    return true
  end
  local rec = REG[name]
  if st == "rebuilt" then rec = nil end
  if rec ~= nil and rec.n >= INSTALLS then return false end
  local w = make(cur, k)
  if not pcall(function() O[k] = w end) then return false end
  local got = nil
  pcall(function() got = O[k] end)
  if got ~= w then return false end
  REG[name] = { table = O, key = k, inner = cur, w = w, n = ((rec and rec.n) or 0) + 1 }
  return true
end

local ARMED = false

-- installs our four members when the table is up
local function arm()
  local O = rawget(_G, "OPTIONS")
  if type(O) ~= "table" then
    if once("nooptions") then log("options arm missing OPTIONS") end
    return false
  end
  local okList = false
  local k, f = find(SLOTS[1])
  if k ~= nil then okList = place(O, k, f, SLOTS[1].name, wrapList) end
  local okData = false
  local i = 2
  while i <= 3 do
    local k2, f2 = find(SLOTS[i])
    if k2 ~= nil and place(O, k2, f2, SLOTS[i].name, wrapData) then okData = true end
    i = i + 1
  end
  local okPage = false
  local k3, f3 = find(SLOTS[4])
  if k3 ~= nil then okPage = place(O, k3, f3, SLOTS[4].name, wrapCreate) end
  if okList and okData and okPage and not ARMED then
    ARMED = true
    log("options armed")
  end
  return okList and okData and okPage
end

local BW = nil

-- re arms on every menu build
local function buildhook()
  local MB = rawget(_G, "MenuBuilder")
  if type(MB) ~= "table" or type(MB.BuildRegisteredType) ~= "function" then
    if once("nomb") then log("options arm missing MenuBuilder.BuildRegisteredType") end
    return false
  end
  local cur = MB.BuildRegisteredType
  if cur == BW then return true end
  local orig = cur
  local w = function(t, data, ...)
    pcall(arm)
    return orig(t, data, ...)
  end
  if not pcall(function() MB.BuildRegisteredType = w end) then return false end
  BW = w
  return true
end

S.probes.options = function() return ARMED == true end

pcall(buildhook)
pcall(arm)

local dp = rawget(_G, "DebugPrint") or rawget(_G, "print")
if type(dp) == "function" then pcall(dp, "progression_tuning: part options armed") end

if A.ready ~= nil then A.ready() end
