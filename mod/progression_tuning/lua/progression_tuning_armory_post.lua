local PART = "armory"

local VERSION = "v14"
local PREFIX = "progression_tuning: "
-- the armory schedule gate a key with no name
local SCHED = "0a6376439b2d40dc"
-- the tries and the ticks the retry timer runs
local MAX_TRIES = 480
-- the activation row the client asks about the active item
local ACTIVATION = 52813
local ACT_STR = tostring(ACTIVATION)
-- the wz activation row beside it
local ACT_WZ = 52814
-- the akita loot the armory tile carries
local PR_LOOT = 94890
-- the channel the hook half reads a pick on
local CH = "pt_armory_ch"
-- the record getter an arm needs
local OCG = "getchallengeprogress"

-- the 76 rows the armory work installs
local ROWS = {
  69316, 69318, 69320, 69322, 69324, 69326, 66885, 66886,
  66888, 66889, 66883, 66881, 66880, 64758, 64762, 64768,
  62981, 64764, 62979, 64766, 71365, 71367, 71369, 71376,
  71378, 71380, 74258, 74259, 74261, 74263, 75669, 75671,
  75673, 75675, 66895, 66896, 66929, 66930, 66931, 66933,
  64774, 64771, 64773, 64776, 64779, 64780, 69342, 69344,
  69346, 69348, 69350, 69352, 69354, 71381, 71383, 71386,
  71384, 71388, 74264, 75415, 74270, 74268, 74274, 74272,
  75676, 75678, 75680, 69328, 66935, 66936, 71370, 69330,
  69332, 69334, 71372, 71374,
}

local MINE = {}
-- the channel value per row built once
local CHVAL = {}
for i = 1, #ROWS do
  MINE[ROWS[i]] = true
  CHVAL[ROWS[i]] = "a=" .. ROWS[i]
end

-- every item its row and the cost it takes
local ITEMS = {
  { 126468, 69316, 250000, 1 },
  { 125262, 69318, 250000, 1 },
  { 125186, 69320, 250000, 1 },
  { 126466, 69322, 250000, 1 },
  { 126467, 69324, 250000, 1 },
  { 126469, 69326, 250000, 1 },
  { 119844, 66885, 250000, 1 },
  { 119843, 66886, 250000, 1 },
  { 122685, 66888, 250000, 1 },
  { 122673, 66889, 250000, 1 },
  { 119845, 66883, 250000, 1 },
  { 116618, 66881, 250000, 1 },
  { 102705, 66880, 250000, 1 },
  { 121205, 64758, 250000, 1 },
  { 97917, 64762, 250000, 1 },
  { 116617, 64768, 250000, 1 },
  { 97997, 62981, 250000, 1 },
  { 113930, 64764, 250000, 1 },
  { 98043, 62979, 250000, 1 },
  { 97897, 64766, 250000, 1 },
  { 133345, 71365, 250000, 1 },
  { 133344, 71367, 250000, 1 },
  { 133368, 71369, 250000, 1 },
  { 131330, 71376, 250000, 1 },
  { 130905, 71378, 250000, 1 },
  { 132997, 71380, 250000, 1 },
  { 142181, 74258, 250000, 1 },
  { 136390, 74259, 250000, 1 },
  { 142433, 74261, 250000, 1 },
  { 136389, 74263, 250000, 1 },
  { 142462, 75669, 250000, 1 },
  { 142465, 75671, 250000, 1 },
  { 142464, 75673, 250000, 1 },
  { 142463, 75675, 250000, 1 },
  { 125052, 66895, 150000, 2 },
  { 124780, 66896, 150000, 2 },
  { 119658, 66929, 150000, 2 },
  { 126591, 66930, 150000, 2 },
  { 124973, 66931, 150000, 2 },
  { 124982, 66933, 150000, 2 },
  { 94890, 64774, 150000, 2 },
  { 119853, 64771, 150000, 2 },
  { 119857, 64773, 150000, 2 },
  { 119867, 64776, 150000, 2 },
  { 119637, 64779, 150000, 2 },
  { 119626, 64780, 150000, 2 },
  { 130653, 69342, 150000, 2 },
  { 129863, 69344, 150000, 2 },
  { 129821, 69346, 150000, 2 },
  { 130328, 69348, 150000, 2 },
  { 129287, 69350, 150000, 2 },
  { 129828, 69352, 150000, 2 },
  { 133946, 69354, 150000, 2 },
  { 140458, 71381, 150000, 2 },
  { 133450, 71383, 150000, 2 },
  { 144093, 71386, 150000, 2 },
  { 140096, 71384, 150000, 2 },
  { 140923, 71388, 150000, 2 },
  { 144632, 74264, 150000, 2 },
  { 145080, 75415, 150000, 2 },
  { 145074, 74270, 150000, 2 },
  { 145085, 74268, 150000, 2 },
  { 145089, 74274, 150000, 2 },
  { 144243, 74272, 150000, 2 },
  { 150604, 75676, 150000, 2 },
  { 150646, 75678, 150000, 2 },
  { 151395, 75680, 150000, 2 },
  { 129239, 69328, 150000, 4 },
  { 98132, 66935, 150000, 4 },
  { 97507, 66936, 150000, 4 },
  { 132047, 71370, 150000, 4 },
  { 126337, 69330, 100000, 3 },
  { 130171, 69332, 100000, 3 },
  { 117946, 69334, 100000, 3 },
  { 117964, 71372, 100000, 3 },
  { 117950, 71374, 100000, 3 },
}
-- the switch each kind answers to
local SW = { "zm_unlock_weapons", "zm_unlock_attachments", "zm_unlock_fieldupgrades", "zm_unlock_scorestreaks" }
local LOCK, COST, KIND, ROWLOOT = {}, {}, {}, {}
for i = 1, #ITEMS do
  local it = ITEMS[i]
  LOCK[it[1]], COST[it[1]], KIND[it[1]], ROWLOOT[it[2]] = it[2], it[3], it[4], it[1]
end

-- every weapon version inherits the row it belongs to
local VARS = {
  [62979] = { 118978, 120852, 121076, 121800, 123035, 124106, 126283, 126492, 127115, 127188, 127410, 129232, 130208, 130590, 133963, 143988 },
  [62981] = { 119058, 120427, 122726, 129604, 130053, 133690, 133813, 134425, 135604, 138447, 145054, 146002, 146674 },
  [64758] = { 122000, 124088, 130222, 143925, 146465 },
  [64762] = { 119121, 119833, 122639, 123638, 125649, 126335, 129370, 130914, 138423, 140447, 142491, 143393, 146492 },
  [64764] = { 116988, 121404, 126504, 127155, 127315, 139096 },
  [64766] = { 119031, 119119, 119465, 119793, 120969, 121455, 122977, 124445, 124683, 125744, 126372, 127249, 128489, 130353, 130951, 132071, 133912, 136213, 146483 },
  [64768] = { 120861, 123177, 123229, 124154, 125691, 127250, 135672, 136212, 136237, 138779, 143362, 143902, 143942, 144137, 144150, 152101 },
  [64771] = { 119851, 122147, 122153, 122237, 125048, 125049, 125050, 125051, 125053, 125054, 125055, 125057, 125061, 125062, 125063, 125064, 125065, 125066, 125068, 125069, 125072, 125073, 125074, 125075, 125076, 125077, 125078, 125079, 125080, 125081, 125082, 125083, 125084, 125085, 125086, 125087, 126626, 127263, 129867, 129881, 133465, 133595, 133603, 133986, 142379, 144064, 144067, 147798, 155501 },
  [66880] = { 124399, 124730, 126566, 135915, 140173, 143479, 145908, 145958, 148814, 152639 },
  [66881] = { 124820, 125302, 126478, 127425, 129708, 129912, 136528, 136619, 139003, 140524, 143487, 146440, 150633, 152454 },
  [66883] = { 124958, 125028, 126493, 134587, 136547, 140105, 152340 },
  [66885] = { 123437, 123446, 123466, 123486, 123765, 126732, 129651, 129662, 129800, 129920, 130141, 133120, 134528, 135605, 136572, 136573, 136574, 136608, 143166, 143749, 146715 },
  [66886] = { 123538, 123560, 123706, 123707, 125238, 126215, 126405, 129786, 136138, 138457, 141115, 141179, 143995, 144418 },
  [66888] = { 124203, 125118, 148289 },
  [66889] = { 123173, 125099, 136519, 148851 },
  [66895] = { 125056, 125058, 125059, 125060, 125067, 125070, 125071, 126906 },
  [69316] = { 130714, 130723, 131287, 132994, 133630, 133674, 134595, 135913, 136593, 141139, 143250, 144253, 144743, 145930, 146460, 147372, 150310, 151393, 152834 },
  [69318] = { 129776, 129777, 130731, 130738, 131504, 132979, 133538, 133691, 136414, 139642, 142000, 142510, 143012, 143890, 143910, 144687, 150551 },
  [69320] = { 130444, 132228, 140106, 140232, 143881, 145335 },
  [69322] = { 130624, 130753, 133700, 134520, 135592, 138758, 143233, 143728, 143766, 145939, 150601 },
  [69324] = { 130757, 136002, 136609, 139125, 151516 },
  [69326] = { 129643, 129653, 140541, 144182, 146014, 150589 },
  [69342] = { 130636, 130637, 130638, 130640, 130641, 130642, 130644, 130645, 130646, 130647, 130648, 130649, 130652, 130654, 130655, 130656, 130657, 130658, 130660, 130662, 130663, 130664, 130665, 130666, 130668, 130669, 130670, 133444, 142016, 142017, 142018, 142540, 144964, 147809, 147822 },
  [71365] = { 138888, 141180, 142253, 143243, 143544, 145064, 149815, 151345 },
  [71367] = { 140818, 140896, 141083, 141149, 142562, 143819, 145489, 145810, 145918, 146500, 151543 },
  [71369] = { 140877, 141163, 150634 },
  [71376] = { 140885, 141064, 141514, 144801, 144973, 149038, 149793, 149921, 153788 },
  [71378] = { 143552, 143846, 144005, 144172, 144252, 148890, 150371, 150566, 151353, 151877 },
  [71380] = { 136490, 142418, 144097, 146450, 146453, 151570 },
  [71381] = { 140451, 140452, 140453, 140454, 140455, 140456, 140457, 140459, 140460, 140461, 140462, 140463, 140464, 140465, 140466, 140467, 140468, 140469, 140470, 140471, 140472, 140473, 140474, 140475, 140476, 140477, 140478, 140479, 140480, 140481, 140482, 140483, 140484, 140485, 140486, 140487, 140488, 140489, 140490, 140491, 140492, 140493, 140494, 140495, 142369, 144057, 144085, 147770, 147830 },
  [74258] = { 144734, 145776, 145844, 146731, 147317, 148865, 151273, 151577, 151599 },
  [74259] = { 144646, 144664, 144957, 145861, 147462, 149103, 151282, 151363, 152015 },
  [74261] = { 145852, 145992, 148901, 150582 },
  [74263] = { 144180, 150402, 151853 },
  [74268] = { 145068, 145072, 145077, 145083, 145087, 145088 },
  [75669] = { 151448, 151966, 152035, 153164 },
  [75671] = { 151472, 151503, 151922, 153766 },
  [75673] = { 151461, 152067 },
  [75675] = { 152124, 152433 },
}
-- the loot id each attachment version answers with
local VAR = {}
for row, ids in pairs(VARS) do
  local loot = ROWLOOT[row]
  if loot ~= nil and KIND[loot] == 2 then
    for i = 1, #ids do VAR[ids[i]] = loot end
  end
end

-- the ids that still answer not owned
local HOLD = {}
for i = 1, #ITEMS do
  HOLD[ITEMS[i][1]] = true
end
for row, ids in pairs(VARS) do
  local loot = ROWLOOT[row]
  if loot ~= nil and KIND[loot] == 2 then
    for i = 1, #ids do HOLD[ids[i]] = true end
  end
end

-- the version ids under each kind of row
local VARA, VARW = 0, 0
for row, ids in pairs(VARS) do
  local loot = ROWLOOT[row]
  if loot ~= nil then
    local k = KIND[loot]
    if k == 1 then
      VARW = VARW + #ids
    elseif k == 2 then
      VARA = VARA + #ids
    end
  end
end

local S = rawget(_G, "ProgressionTuning")
if type(S) ~= "table" then
  S = { parts = {}, hooks = {}, probes = {}, api = {}, g11 = {}, scope = {} }
  rawset(_G, "ProgressionTuning", S)
end
if S.parts[PART] == true then return end
S.parts[PART] = true
local A = S.api
local Ar = { tries = 0, ticks = 0, installed = false, said = false, pick = nil, hover = nil, hoverRef = nil,
  noRoute = false, seen = false, pressed = false, presses = 0, snap = 0, wrote = nil, rline = nil,
  retired = false, u = false }

-- one line through the mod log when it is up
local function log(msg)
  if type(A.log) == "function" then return A.log(msg) end
  local fn = rawget(_G, "DebugPrint") or rawget(_G, "print")
  if type(fn) == "function" then pcall(fn, PREFIX .. tostring(msg)) end
end

-- a member by name then by its hash
local function member(tbl, name)
  if type(tbl) ~= "table" then return nil end
  local ok, v = pcall(rawget, tbl, name)
  if ok and v ~= nil then return v end
  local h = rawget(_G, "xhash")
  if type(h) ~= "function" then return nil end
  local okh, k = pcall(h, name)
  if not okh or k == nil then return nil end
  local ok2, v2 = pcall(rawget, tbl, k)
  if ok2 then return v2 end
  return nil
end

-- a member only when it is a function
local function fn_of(tbl, name)
  local v = member(tbl, name)
  if type(v) == "function" then return v end
  return nil
end

-- a printed key as a hash with no leading zeros
local function key_hex(k)
  local ok, s = pcall(tostring, k)
  if not ok or type(s) ~= "string" then return nil end
  local h = string.match(s, "#x(%x+)")
  if h == nil then return nil end
  return (string.lower((string.gsub(h, "^0+", ""))))
end

-- a function member and the key it sits under
local function slot_of(tbl, name)
  if type(tbl) ~= "table" then return nil, nil end
  local ok, v = pcall(rawget, tbl, name)
  if ok and type(v) == "function" then return name, v end
  local want = nil
  local h = rawget(_G, "xhash")
  if type(h) == "function" then
    local okh, k = pcall(h, name)
    if okh and k ~= nil then
      want = key_hex(k)
      local okv, vh = pcall(rawget, tbl, k)
      if okv and type(vh) == "function" then return k, vh end
    end
  end
  local found = nil
  pcall(function()
    local k, val = next(tbl)
    while k ~= nil do
      if found == nil and type(val) == "function" then
        if (want ~= nil and key_hex(k) == want) or string.lower(tostring(k)) == string.lower(name) then
          found = k
        end
      end
      k, val = next(tbl, k)
    end
  end)
  if found == nil then return nil, nil end
  local okf, vf = pcall(rawget, tbl, found)
  if okf and type(vf) == "function" then return found, vf end
  return nil, nil
end

-- a key printed as a hash with leading zeros ignored
local function key_matches(k, hex)
  local ok, s = pcall(tostring, k)
  if not ok or type(s) ~= "string" then return false end
  local h = string.match(s, "#x(%x+)")
  if h == nil then return false end
  h = string.lower(h)
  if h == hex then return true end
  local a = string.gsub(h, "^0+", "")
  local b = string.gsub(hex, "^0+", "")
  if a == b then return true end
  return string.sub(a, 1, #b) == b or string.sub(a, -#b) == b
end

-- the gate and the key it sits under
local function gate_slot(tbl)
  local found, f = nil, nil
  pcall(function()
    local k, v = next(tbl)
    while k ~= nil do
      if found == nil and type(v) == "function" and key_matches(k, SCHED) then found, f = k, v end
      k, v = next(tbl, k)
    end
  end)
  return found, f
end

-- every value one call answered
local function pack(...) return { n = select("#", ...), ... } end
local UNPACK = rawget(_G, "unpack")
if type(UNPACK) ~= "function" then
  local t = rawget(_G, "table")
  UNPACK = type(t) == "table" and t.unpack or nil
end

-- one of the rows this part answers for
local function mine(row)
  local ok, id = pcall(function() return tonumber(row.id) end)
  if not ok or id == nil then return false end
  return MINE[id] == true
end

local OURS = setmetatable({}, { __mode = "k" })
local GK, GW = nil, nil

-- answers released for our rows and delegates the rest
local function wrap_gate()
  local tbl = rawget(_G, "ARMORY")
  if type(tbl) ~= "table" then return false end
  if GK ~= nil and rawget(tbl, GK) == GW then return true end
  local k, orig = gate_slot(tbl)
  if type(orig) ~= "function" then return false end
  if OURS[orig] then
    GK, GW = k, orig
    return true
  end
  local w = function(c, row, ...)
    if mine(row) then return true end
    local res = pack(pcall(orig, c, row, ...))
    if not res[1] then return false end
    if UNPACK == nil then return res[2] end
    return UNPACK(res, 2, res.n)
  end
  OURS[w] = true
  tbl[k] = w
  GK, GW = k, w
  return true
end

-- menu or match for the arm line
local function vm_kind()
  local f = fn_of(rawget(_G, "Engine"), "InFrontend")
  if f == nil then return "match" end
  local ok, v = pcall(f)
  if ok and v == true then return "menu" end
  return "match"
end

-- a field read through pcall so userdata is no trap
local function field(obj, name)
  if obj == nil then return nil end
  local ok, v = pcall(function() return obj[name] end)
  if ok then return v end
  return nil
end

-- the hash a name is stored under
local function hash_of(name)
  local h = rawget(_G, "xhash")
  if type(h) ~= "function" then return nil end
  local ok, k = pcall(h, name)
  if not ok then return nil end
  return k
end

-- a field by plain name then by its hash
local function hfield(obj, name)
  if obj == nil then return nil end
  local v = field(obj, name)
  if v ~= nil then return v end
  local k = hash_of(name)
  if k == nil then return nil end
  return field(obj, k)
end

-- a datasource node value or the plain value itself
local function node_value(node, c)
  if node == nil then return nil end
  local g = hfield(node, "GetValue")
  if type(g) == "function" then
    local ok, v = pcall(g, node, c)
    if ok then return v end
    return nil
  end
  local t = type(node)
  if t == "string" or t == "number" then return node end
  return nil
end

-- the model one element carries
local function element_model(el)
  local g = hfield(el, "GetDataSource")
  if type(g) ~= "function" then return nil end
  local ok, v = pcall(g, el)
  if ok then return v end
  return nil
end

-- the row and the ref one tile model names
local function model_row(ds, c)
  local t = type(ds)
  if t ~= "table" and t ~= "userdata" then return nil end
  local id = tonumber(node_value(hfield(hfield(ds, "armory_button_data"), "achievement_id"), c))
  if id == nil or not MINE[id] then return nil end
  local ref = node_value(hfield(ds, "item_ref"), c)
  if type(ref) ~= "string" then ref = nil end
  return id, ref
end

-- a field under the hash a name is stored by
local function hashed(obj, name)
  local k = hash_of(name)
  if k == nil then return nil end
  return field(obj, k)
end

-- one armory datasource every level on its hash
local function ds_of(name)
  return hashed(hashed(hashed(rawget(_G, "_DataSources"), "frontend"), "armory"), name)
end

-- the tile one focus or active datasource holds
local function ds_row(name, c)
  local node = ds_of(name)
  if node == nil then return nil end
  local id, ref = model_row(node_value(node, c), c)
  if id ~= nil then return id, ref end
  return model_row(node, c)
end

-- the row the press acted on and the routes walked
local function press_row(c, el, other)
  local tried = "el"
  local id, ref = model_row(element_model(el), c)
  if id ~= nil then return id, ref, tried end
  if other ~= nil and type(other) ~= "number" then
    tried = tried .. " arg"
    local m = element_model(other)
    if m == nil then m = other end
    id, ref = model_row(m, c)
    if id ~= nil then return id, ref, tried end
  end
  tried = tried .. " focus"
  id, ref = ds_row("armory_select_focus_item", c)
  if id ~= nil then return id, ref, tried end
  tried = tried .. " active"
  id, ref = ds_row("armory_active_item", c)
  if id ~= nil then return id, ref, tried end
  if Ar.hover ~= nil then
    tried = tried .. " hover"
    if MINE[Ar.hover] then return Ar.hover, Ar.hoverRef, tried end
  end
  return nil, nil, tried
end

local DGET, DSET

-- the channel dvar as the hash the client stores
local function dvkey()
  local h = rawget(_G, "xhashdvar")
  if type(h) == "function" then
    local ok, k = pcall(h, CH)
    if ok and k ~= nil then return k end
  end
  return CH
end

-- the dvar getter the rest of the mod uses
local function dget()
  if DGET == nil then DGET = fn_of(rawget(_G, "Dvar"), "GetDvarString") end
  if DGET == nil then return nil end
  local key = dvkey()
  local ok, v = pcall(DGET, key)
  if ok and type(v) == "string" then
    if v ~= "" then Ar.seen = true end
    return v
  end
  if key ~= CH then
    local okp, v2 = pcall(DGET, CH)
    if okp and type(v2) == "string" then
      if v2 ~= "" then Ar.seen = true end
      return v2
    end
  end
  return nil
end

-- the row the channel line names
local function chrow(v)
  if type(v) ~= "string" then return nil end
  local n = string.match(v, "^a=(%d+)")
  if n == nil then return nil end
  return tonumber(n)
end

-- the queue the channel line carries as ids
local function qlist(v)
  if type(v) ~= "string" then return nil end
  local s = string.match(v, "q=([%d,]+)")
  if s == nil then return nil end
  local out = {}
  for n in string.gmatch(s, "%d+") do
    local id = tonumber(n)
    if id == nil then return nil end
    out[#out + 1] = id
  end
  if #out == 0 then return nil end
  return out
end

-- ids as one comma separated text
local function join(list)
  local out = ""
  for i = 1, #list do
    if i > 1 then out = out .. "," end
    out = out .. list[i]
  end
  return out
end

-- the unlock field one and zero
local UON, UOFF = "1", "0"

-- the unlock flag a line carries
local function uof(v)
  if type(v) ~= "string" then return false end
  return string.match(v, ";u=(%d+)") == UON
end

-- the unlock field a line carries as text
local function ufield(v)
  if type(v) ~= "string" then return "" end
  local n = string.match(v, ";u=(%d+)")
  if n == nil then return "" end
  if n == UON then return ";u=1" end
  return ";u=0"
end

-- one channel write only after a line was read
local function dchput(val, force)
  if not (force == true or Ar.seen or Ar.pressed) then return false end
  if DSET == nil then DSET = fn_of(rawget(_G, "Dvar"), "SetDvarString") end
  if DSET == nil then return false end
  local key = dvkey()
  if not pcall(DSET, key, val) and key ~= CH then pcall(DSET, CH, val) end
  if dget() ~= val then return false end
  Ar.wrote, Ar.snap = val, Ar.presses
  return true
end

-- the pick over the row and the queue kept
local function dchwrite(id)
  local val = CHVAL[id]
  if val == nil then return false end
  local v = dget()
  local q = qlist(v)
  if q == nil then q = Ar.q end
  if q ~= nil and #q > 0 then val = val .. ";q=" .. join(q) end
  val = val .. ufield(v)
  return dchput(val)
end

-- the pick and the queue another vm left
local function seed(late)
  local v = dget()
  if type(v) ~= "string" then return false end
  Ar.u = uof(v)
  local q = qlist(v)
  if q ~= nil then Ar.q = q end
  local id = chrow(v)
  if id == nil or not MINE[id] then return false end
  if Ar.pick == id then return true end
  Ar.pick = id
  if late then
    log("armory pick " .. id .. " (seeded late)")
  else
    log("armory pick " .. id)
  end
  return true
end

-- a hook advance is a line we did not write
local function watch()
  local v = dget()
  if type(v) ~= "string" or v == Ar.rline then return false end
  Ar.rline = v
  Ar.u = uof(v)
  if v == Ar.wrote or Ar.presses ~= Ar.snap then return false end
  local id = chrow(v)
  if id == nil or not MINE[id] then return false end
  local q = qlist(v)
  if q ~= nil then Ar.q = q end
  if id == Ar.pick then return true end
  Ar.pick = id
  log("armory pick " .. id .. " (advanced)")
  return true
end

-- the unlock flag read from the channel now
local function uread()
  local ok, v = pcall(dget)
  if ok then Ar.u = uof(v) end
  return Ar.u == true
end

-- the unlock flag as its channel text
local function uw()
  if Ar.u == true then return UON end
  return UOFF
end

-- the unlock flag written into the channel line
local function dchu(on)
  Ar.u = on == true
  local v = dget()
  local a = chrow(v)
  if a == nil then a = Ar.pick or 0 end
  local val = "a=" .. a
  local q = qlist(v)
  if q ~= nil then val = val .. ";q=" .. join(q) end
  val = val .. ";u=" .. uw()
  return dchput(val, true)
end

-- the queue the page holds in its own order
local function pageq()
  local f = fn_of(rawget(_G, "ARMORY"), "getcachedarmoryachievements")
  if f == nil then return nil end
  local done = fn_of(rawget(_G, "Challenge"), "IsChallengeComplete")
  local ok, list = pcall(f)
  if not ok or type(list) ~= "table" then return nil end
  local out = {}
  pcall(function()
    for _, rec in ipairs(list) do
      local id = tonumber(field(rec, "id"))
      if id ~= nil and MINE[id] then
        local complete = false
        if done ~= nil then
          local okc, c = pcall(done, 0, id)
          complete = okc and c == true
        end
        if not complete then out[#out + 1] = id end
      end
    end
  end)
  if #out == 0 then return nil end
  return out
end

-- the queue a front end visit puts in the channel
local function armq()
  local q = Ar.q
  if q == nil then
    q = pageq()
    if q == nil then return end
    Ar.q = q
  end
  local v = dget()
  if qlist(v) ~= nil then return end
  local a = chrow(v)
  if a == nil then a = Ar.pick or 0 end
  dchput("a=" .. a .. ";q=" .. join(q) .. ufield(v))
end

-- a table copied field by field
local function copy_fields(t)
  local out = {}
  if type(t) ~= "table" then return out end
  pcall(function() for k, v in pairs(t) do out[k] = v end end)
  return out
end

-- the clients own activation when it carries one
local function client_act(rec)
  if type(rec) ~= "table" then return nil end
  local ok, v = pcall(function() return rec.progress.last_activation end)
  if not ok then return nil end
  local n = tonumber(v)
  if n == nil or n == 0 then return nil end
  return n
end

-- records written by this part so a chain passes them
local OUR_RECS = setmetatable({}, { __mode = "k" })

-- the press names one of our rows and keeps it
local function record(id, ref)
  Ar.pressed = true
  if id == Ar.pick then return end
  Ar.pick = id
  Ar.presses = Ar.presses + 1
  dchwrite(id)
  if ref ~= nil then
    log("armory pick " .. id .. " (" .. ref .. ")")
  else
    log("armory pick " .. id)
  end
end

-- the clients own press first then the row
local function wrap_press()
  local tbl = rawget(_G, "ARMORY")
  local k, orig = slot_of(tbl, "setactiveitem")
  if k == nil then return false end
  if OURS[orig] then return true end
  local w = function(menu, c, ...)
    local res = pack(pcall(orig, menu, c, ...))
    if not res[1] then return end
    local ok, id, ref, tried = pcall(press_row, c, menu, ...)
    if ok and id ~= nil then
      local okr = pcall(record, id, ref)
      if not okr then log("armory pick is not recorded - the press is the clients own") end
    elseif ok and not Ar.noRoute then
      Ar.noRoute = true
      log("armory press no row - " .. tostring(tried) .. " args=" .. type(menu) .. " "
        .. type((...)) .. " " .. type(c))
    end
    if UNPACK == nil then return res[2] end
    return UNPACK(res, 2, res.n)
  end
  OURS[w] = true
  tbl[k] = w
  return true
end

-- the last tile focused is the row a press means
local function wrap_focus()
  local tbl = rawget(_G, "ARMORY")
  local k, orig = slot_of(tbl, "setfocuseddatasource")
  if k == nil then return false end
  if OURS[orig] then return true end
  local w = function(c, tile, ...)
    pcall(function()
      local m = element_model(tile)
      if m == nil then m = tile end
      local id, ref = model_row(m, c)
      if id ~= nil then
        Ar.hover = id
        Ar.hoverRef = ref
      end
    end)
    return orig(c, tile, ...)
  end
  OURS[w] = true
  tbl[k] = w
  return true
end

local lk_arm
-- the probe line and the clients own getter behind it
local PR_SAY, OCORIG

-- the activation record answers the pick for this session
local function wrap_answer()
  local OC = rawget(_G, "OnlineChallenges")
  local k, orig = slot_of(OC, OCG)
  if k == nil then return false end
  if OCORIG == nil then OCORIG = orig end
  if OURS[orig] then return true end
  local w = function(c, id, ...)
    local res = pack(pcall(orig, c, id, ...))
    if not res[1] then return nil end
    if tonumber(id) ~= ACTIVATION then
      if UNPACK == nil then return res[2] end
      return UNPACK(res, 2, res.n)
    end
    pcall(lk_arm)
    if PR_SAY ~= nil then pcall(PR_SAY) end
    local rec = res[2]
    if OUR_RECS[rec] then return rec end
    if Ar.pick == nil then pcall(seed, true) end
    local picked = Ar.pick
    if picked == nil then return rec end
    if client_act(rec) ~= nil then return rec end
    local out = copy_fields(rec)
    local prog = copy_fields(type(rec) == "table" and rec.progress or nil)
    prog.last_activation = picked
    if prog.default == nil then prog.default = 0 end
    if out.id == nil then out.id = ACT_STR end
    out.progress = prog
    OUR_RECS[out] = true
    return out
  end
  OURS[w] = true
  OC[k] = w
  return true
end

local LK = { at = nil, at2 = nil, done = nil, sw = nil, busy = false, u = false }
local LKW = setmetatable({}, { __mode = "k" })
-- the progress fields a record carries in order
local LK_FIELDS = { "default", "progress", "xp" }

-- the progress a record holds as a number
local function lk_value(rec)
  if type(rec) ~= "table" then return nil end
  local prog = field(rec, "progress")
  if type(prog) ~= "table" then return nil end
  for i = 1, #LK_FIELDS do
    local v = tonumber(hfield(prog, LK_FIELDS[i]))
    if v ~= nil then return v end
  end
  return nil
end

-- one completion pass over the 76 rows
local function lk_pass()
  local done = {}
  local f = fn_of(rawget(_G, "Challenge"), "IsChallengeComplete")
  local g = nil
  if f == nil then g = fn_of(rawget(_G, "OnlineChallenges"), OCG) end
  for i = 1, #ITEMS do
    local it = ITEMS[i]
    local yes = false
    if f ~= nil then
      local ok, v = pcall(f, 0, it[2])
      yes = ok and v == true
    elseif g ~= nil then
      local ok, rec = pcall(g, 0, it[2])
      if ok then
        local p = lk_value(rec)
        yes = p ~= nil and p >= it[3]
      end
    end
    if yes then done[it[1]] = true end
  end
  return done
end

-- the rows and the switches read once a tick
local function lk_now()
  local t1, t2 = S.tick or -1, Ar.ticks
  if LK.done ~= nil and LK.at == t1 and LK.at2 == t2 then return LK end
  if LK.busy then return LK end
  LK.busy = true
  local sw = { all = false, t = {} }
  local dv = A.dv
  if type(dv) == "function" then
    local all = dv("zm_unlock_all")
    sw.all = all ~= nil and all ~= "" and all ~= "0"
    for i = 1, #SW do
      local v = dv(SW[i])
      sw.t[i] = v ~= nil and v ~= "" and v ~= "0"
    end
  end
  local done = lk_pass()
  LK.sw, LK.done, LK.u = sw, done, uread()
  LK.at, LK.at2 = t1, t2
  LK.busy = false
  return LK
end

-- the unlock flag the snapshot holds
local function uon()
  return lk_now().u == true
end

-- held open by its own row or by its switch
local function lk_free(loot)
  local s = lk_now()
  if s.u == true then return true end
  if s.done == nil then return false end
  if s.done[loot] == true then return true end
  if s.sw == nil then return false end
  if s.sw.all then return true end
  local k = KIND[loot]
  return k ~= nil and s.sw.t[k] == true
end

-- the clients own activation for one row now
local function pr_act(row)
  local g = OCORIG
  if g == nil then g = fn_of(rawget(_G, "OnlineChallenges"), OCG) end
  if g == nil then return "none" end
  local ok, rec = pcall(g, 0, row)
  if not ok or type(rec) ~= "table" then return "none" end
  local okv, v = pcall(function() return rec.progress.last_activation end)
  if not okv then return "none" end
  local n = tonumber(v)
  if n == nil then return "none" end
  return tostring(n)
end

-- the doors own verdict for the akita loot
local function pr_loot()
  local locks = S.locks
  if type(locks) ~= "table" then return "none" end
  local okA, locked = pcall(locks.answer, PR_LOOT)
  if okA and locked == true then return "locked" end
  local okO, open = pcall(locks.open, PR_LOOT)
  if okO and open == true then return "open" end
  return "client"
end

-- the two probe points each say this once
local PR = { act = false, door = false }

PR_SAY = function(door)
  if door == nil then
    if PR.act then return end
    if not uon() then return end
    PR.act = true
  else
    if PR.door then return end
    if not uon() then return end
    PR.door = true
  end
  local d = "none"
  if door ~= nil then d = door .. "=locked" end
  log("armory probe act=" .. pr_act(ACTIVATION) .. "/" .. pr_act(ACT_WZ)
    .. " loot=" .. pr_loot() .. " door=" .. d)
end

-- each streak ref and the loot row behind it
local STREAK = { radiation_blast = 129239, smart_gun = 98132, sniper_drone = 97507, skybreak = 132047 }

local CRAFT = { on = false, said = false }
local CKREF, CKREFD = nil, false

-- the item ref one tile carries
local function craft_ref(item)
  if type(item) ~= "table" then return nil end
  local v = rawget(item, "itemref")
  if type(v) == "string" then return v end
  if not CKREFD then
    CKREFD = true
    CKREF = hash_of("itemref")
  end
  if CKREF == nil then return nil end
  v = rawget(item, CKREF)
  if type(v) == "string" then return v end
  return nil
end

-- the loot row a streak ref answers to
local function craft_row(ref)
  if type(ref) ~= "string" then return nil end
  local loot = STREAK[ref]
  if loot == nil then return nil end
  if LOCK[loot] == nil then return nil end
  return loot
end

-- says once when the game lock raised and we lock
local function craft_say()
  if CRAFT.said then return end
  CRAFT.said = true
  log("armory craft lock raised - answering locked")
end

-- the game own answer unless the ref is a streak
local function craft_locked(c, item, orig, ...)
  local ok, locked = pcall(orig, c, item, ...)
  local loot = craft_row(craft_ref(item))
  if loot == nil then
    if ok then return locked end
    craft_say()
    return true
  end
  local okf, free = pcall(lk_free, loot)
  if okf and free == true then
    if uon() then return false end
    if ok then return locked end
    return false
  end
  return true
end

-- wraps the crafting table lock once in a match
local function craft_arm()
  if CRAFT.on then return true end
  if vm_kind() == "menu" then return false end
  local tbl = rawget(_G, "PurchaseMenuUtils")
  if type(tbl) ~= "table" then return false end
  local k, orig = slot_of(tbl, "isitemlocked")
  if k == nil or type(orig) ~= "function" then return false end
  if OURS[orig] then
    CRAFT.on = true
    return true
  end
  local w = function(c, item, ...)
    local ok, v = pcall(craft_locked, c, item, orig, ...)
    if ok then return v end
    craft_say()
    return true
  end
  OURS[w] = true
  tbl[k] = w
  CRAFT.on = true
  return true
end

-- a call through that never rethrows
local function lk_thru(f, id)
  local ok, v = pcall(f, id)
  if not ok then return nil end
  return v
end

-- locked until the row or the switch says done
local function lk_answer(locks)
  local orig = locks.answer
  if type(orig) ~= "function" then return false end
  if LKW[orig] then return true end
  local w = function(id)
    local loot = tonumber(id)
    if loot ~= nil then
      loot = math.floor(loot)
      local base = VAR[loot]
      if base ~= nil then loot = base end
      if LOCK[loot] ~= nil then
        local ok, free = pcall(lk_free, loot)
        return not (ok and free == true)
      end
    end
    local v = lk_thru(orig, id)
    if PR_SAY ~= nil and PR.door ~= true and Ar.u == true and loot ~= nil and v == true then
      pcall(PR_SAY, loot)
    end
    return v
  end
  LKW[w] = true
  locks.answer = w
  return true
end

-- the open side mirrors the lock side
local function lk_open(locks)
  local orig = locks.open
  if type(orig) ~= "function" then return false end
  if LKW[orig] then return true end
  local w = function(id)
    local loot = tonumber(id)
    if loot ~= nil then
      loot = math.floor(loot)
      local base = VAR[loot]
      if base ~= nil then loot = base end
      if LOCK[loot] ~= nil then
        local ok, free = pcall(lk_free, loot)
        return ok and free == true
      end
    end
    return lk_thru(orig, id)
  end
  LKW[w] = true
  locks.open = w
  return true
end

local OW = { tbl = nil, slot = nil, fn = nil }
local OWK = setmetatable({}, { __mode = "k" })

-- the ownership answer for the base ids and attachment versions
local function own_ask(c, id, orig)
  local loot = tonumber(id)
  if loot ~= nil then
    loot = math.floor(loot)
    if HOLD[loot] == true then
      local base = VAR[loot]
      if base == nil then base = loot end
      local ok, free = pcall(lk_free, base)
      if not (ok and free == true) then return 0 end
    end
  end
  local ok, v = pcall(orig, c, id)
  if not ok then return 0 end
  return v
end

-- the slot the client keeps its ownership getter under
local function own_slot(tbl)
  local k = hash_of("IsOwned")
  if k ~= nil then
    local f = rawget(tbl, k)
    if type(f) == "function" then return k, f end
  end
  return slot_of(tbl, "IsOwned")
end

-- wraps the ownership getter once a vm
local function wrap_own()
  local tbl = rawget(_G, "PROXY_LOOT")
  if type(tbl) ~= "table" then return false end
  if OW.tbl == tbl and OW.slot ~= nil and rawget(tbl, OW.slot) == OW.fn then return true end
  local k, orig = own_slot(tbl)
  if k == nil or type(orig) ~= "function" then return false end
  if OWK[orig] then
    OW.tbl, OW.slot, OW.fn = tbl, k, orig
    return true
  end
  local w = function(c, id)
    return own_ask(c, id, orig)
  end
  OWK[w] = true
  OURS[w] = true
  tbl[k] = w
  OW.tbl, OW.slot, OW.fn = tbl, k, w
  return true
end

-- wraps the doors two rules once each
lk_arm = function()
  local locks = S.locks
  if type(locks) ~= "table" then return false end
  local a = lk_answer(locks)
  local o = lk_open(locks)
  return a and o
end

-- wrapped or missing for the arm line
local function word(v)
  if v then return "wrapped" end
  return "missing"
end

-- the craft field the arm line carries
local function craft_word()
  if vm_kind() == "menu" then return "n/a" end
  return word(CRAFT.on)
end

-- the two members an arm needs in this vm
local function armable()
  if type(rawget(_G, "ARMORY")) ~= "table" then return false end
  return fn_of(rawget(_G, "OnlineChallenges"), OCG) ~= nil
end

-- what this vm needs in place before the timer rests
local ARMF = { gate = false, press = false, answer = false, lock = false, own = false, craft = false }
local FIELDS = { "gate", "press", "answer", "lock", "own", "craft" }

local card_word

-- installs what it can and reports what is in place
local function attempt()
  ARMF.gate = wrap_gate()
  ARMF.press = wrap_press()
  ARMF.answer = wrap_answer()
  ARMF.own = wrap_own()
  ARMF.lock = lk_arm()
  ARMF.craft = craft_arm()
  if ARMF.press then wrap_focus() end
  return ARMF
end

-- every wrapper this vm needs is in place
local function armed(st)
  if not (st.gate and st.answer and st.lock and st.own) then return false end
  if vm_kind() == "menu" then return st.press == true end
  return st.craft == true
end

local FIRST = nil
local LATE_ON = false

-- the words one arm line carries
local function arm_line(st)
  log("armory armed " .. VERSION .. " vm=" .. vm_kind() .. " gate=" .. word(st.gate)
    .. " pick=" .. word(st.press) .. " answer=" .. word(st.answer) .. " lock=" .. word(st.lock)
    .. " own=" .. word(st.own) .. " vars=" .. VARA .. "+" .. VARW .. " craft=" .. craft_word()
    .. " card=" .. card_word()
    .. " rows=" .. #ROWS .. " pick=" .. tostring(Ar.pick or 0)
    .. " q=" .. tostring(Ar.q and #Ar.q or 0))
end

-- the names that arrived after the first line once
local function late_line(st)
  if not LATE_ON or not armed(st) then return end
  LATE_ON = false
  local out = ""
  for i = 1, #FIELDS do
    local k = FIELDS[i]
    if FIRST[k] ~= true and st[k] == true then
      if out == "" then out = k else out = out .. " " .. k end
    end
  end
  if out ~= "" then log("armory late " .. out) end
end

-- tries until the line can be said or the cap
local function arm(st)
  if Ar.said then return end
  if not armable() then return end
  Ar.tries = Ar.tries + 1
  if st == nil then st = attempt() end
  local ok = st.gate and (st.press or st.answer)
  if not ok and Ar.tries < MAX_TRIES then return end
  Ar.installed, Ar.said = ok, true
  seed()
  armq()
  arm_line(st)
  FIRST = { gate = st.gate, press = st.press, answer = st.answer, lock = st.lock, own = st.own,
    craft = st.craft }
  LATE_ON = not armed(st)
end

-- the armory card the game draws for one finished row
local CARD_NAME = "ae_kind_armory"
local CARD = { kind = nil, base = nil, fired = {} }

-- the kind the armory card answers to
local function card_kind()
  if CARD.kind ~= nil then return CARD.kind end
  local ek = fn_of(rawget(_G, "Challenge"), "GetAEKindID")
  if ek == nil then return nil end
  local forms = { CARD_NAME }
  local h = hash_of(CARD_NAME)
  if h ~= nil then forms[2] = h end
  for i = 1, #forms do
    local ok, v = pcall(ek, forms[i])
    if ok then
      local n = tonumber(v)
      if n ~= nil and n > 0 then
        CARD.kind = n
        return n
      end
    end
  end
  return nil
end

-- the root and the call a card goes through
local function card_face()
  local lui = rawget(_G, "LUI")
  local getroot = fn_of(lui, "GetRoot")
  if getroot == nil then return nil end
  local okr, rootEl = pcall(getroot)
  if not okr or rootEl == nil then return nil end
  local uir = member(lui, "UIRoot")
  local fe = (uir ~= nil) and fn_of(uir, "ProcessEvent") or nil
  if fe == nil then fe = fn_of(rootEl, "ProcessEvent") end
  if fe == nil then return nil end
  return fe, rootEl
end

-- one card through the client own root
local function card_show(row, loot)
  local kind = card_kind()
  local fe, rootEl = card_face()
  if kind == nil or fe == nil then return false end
  local ok = pcall(fe, rootEl, { name = "completed_challenge", controller = 0, kind = kind, id = row,
    progress = {} })
  if ok then
    log("armory card " .. row .. " kind=" .. kind .. " loot=" .. loot)
  else
    log("armory card " .. row .. " refused")
  end
  return ok
end

-- the card field the arm line carries
card_word = function()
  if card_kind() == nil then return "missing" end
  if card_face() == nil then return "missing" end
  return "ok"
end

-- the weapon loots whose spawn entry names another gun
local PICT = {}
for i = 1, #ITEMS do
  local it = ITEMS[i]
  if it[4] == 1 then PICT[it[1]] = true end
end
local PICTN = 0
for _ in pairs(PICT) do PICTN = PICTN + 1 end

local IW = { tbl = nil, slot = nil, fn = nil }

-- the gun own picture for one of our weapon loots
local function own_picture(loot)
  local getref = fn_of(rawget(_G, "LOOT"), "GetItemRef")
  if getref == nil then return nil end
  local okR, ref = pcall(getref, loot)
  if not okR or type(ref) ~= "string" or ref == "" then return nil end
  local bw = fn_of(rawget(_G, "WEAPON"), "getbwimage")
  if bw == nil then return nil end
  local okB, pic = pcall(bw, ref)
  if not okB or type(pic) ~= "string" or pic == "" then return nil end
  return pic
end

-- the spawn entry answer swapped for the gun own picture
local function pic_ask(id, orig, ...)
  local ok, v = pcall(orig, id, ...)
  if not ok then return nil end
  local loot = tonumber(id)
  if loot == nil then return v end
  loot = math.floor(loot)
  if PICT[loot] ~= true then return v end
  local own = own_picture(loot)
  if own == nil or own == v then return v end
  return own
end

-- wraps the spawn entry picture once in a match
local function pic_arm()
  if vm_kind() == "menu" then return false end
  local tbl = rawget(_G, "COMMON_ITEM")
  if type(tbl) ~= "table" then return false end
  if IW.tbl == tbl and IW.slot ~= nil and rawget(tbl, IW.slot) == IW.fn then return true end
  local k, orig = slot_of(tbl, "GetItemSpawnEntryImageByID")
  if k == nil or type(orig) ~= "function" then return false end
  if OURS[orig] then
    IW.tbl, IW.slot, IW.fn = tbl, k, orig
    return true
  end
  local w = function(id, ...)
    return pic_ask(id, orig, ...)
  end
  OURS[w] = true
  tbl[k] = w
  IW.tbl, IW.slot, IW.fn = tbl, k, w
  log("armory picture wrapped for " .. PICTN .. " weapon loots")
  return true
end

local NW = { tbl = nil, slot = nil, fn = nil }
local GUN = {}

-- the gun own name one of our weapon loots carries
local function own_name(loot)
  local v = GUN[loot]
  if v == false then return nil end
  if v ~= nil then return v end
  local getref = fn_of(rawget(_G, "LOOT"), "GetItemRef")
  local wd = fn_of(rawget(_G, "WEAPON"), "getweapondataforref")
  local loc = fn_of(rawget(_G, "Engine"), "Localize")
  if getref == nil or wd == nil or loc == nil then
    GUN[loot] = false
    return nil
  end
  local okR, ref = pcall(getref, loot)
  if not okR or type(ref) ~= "string" or ref == "" then
    GUN[loot] = false
    return nil
  end
  local okW, data = pcall(wd, ref)
  if not okW then
    GUN[loot] = false
    return nil
  end
  local key = hfield(data, "name")
  if type(key) ~= "string" or key == "" then
    GUN[loot] = false
    return nil
  end
  local okL, text = pcall(loc, key)
  if not okL or type(text) ~= "string" or text == "" then
    GUN[loot] = false
    return nil
  end
  GUN[loot] = text
  return text
end

-- the gun own name for the spawn entry title
local function name_ask(id, orig, ...)
  local ok, v = pcall(orig, id, ...)
  local loot = tonumber(id)
  if loot ~= nil then
    loot = math.floor(loot)
    if PICT[loot] == true then
      local own = own_name(loot)
      if own ~= nil then return own end
    end
  end
  if not ok then return nil end
  return v
end

-- wraps the spawn entry name once in a match
local function name_arm()
  if vm_kind() == "menu" then return false end
  local tbl = rawget(_G, "LOOT")
  if type(tbl) ~= "table" then return false end
  if NW.tbl == tbl and NW.slot ~= nil and rawget(tbl, NW.slot) == NW.fn then return true end
  local k, orig = slot_of(tbl, "getitemnamebyid")
  if k == nil or type(orig) ~= "function" then return false end
  if OURS[orig] then
    NW.tbl, NW.slot, NW.fn = tbl, k, orig
    return true
  end
  local w = function(id, ...)
    return name_ask(id, orig, ...)
  end
  OURS[w] = true
  tbl[k] = w
  NW.tbl, NW.slot, NW.fn = tbl, k, w
  log("armory name wrapped for " .. PICTN .. " weapon loots")
  return true
end

-- the rows already done are never carded
local function card_base()
  local done = lk_now().done
  if done == nil then return false end
  for i = 1, #ITEMS do
    local it = ITEMS[i]
    if done[it[1]] == true then CARD.fired[it[2]] = true end
  end
  CARD.base = true
  return true
end

-- one card for each row that just finished
local function card_watch()
  if vm_kind() ~= "match" then return end
  if CARD.base ~= true then return card_base() end
  local done = lk_now().done
  if done == nil then return end
  for i = 1, #ITEMS do
    local it = ITEMS[i]
    local row, loot = it[2], it[1]
    if done[loot] == true and CARD.fired[row] ~= true then
      CARD.fired[row] = true
      pcall(pic_arm)
      pcall(name_arm)
      pcall(card_show, row, loot)
    end
  end
end

local TICK_MS = 250

local timerEl
local tick

-- the hud this part armed on is still there
local function live()
  if S.enabled == false then return false end
  local el = timerEl
  if el == nil then return false end
  local ok, parent = pcall(function() return el:getParent() end)
  return ok and parent ~= nil
end

-- builds one element on the lui root
local function make_el()
  local lui = rawget(_G, "LUI")
  local getroot = fn_of(lui, "GetRoot")
  if getroot == nil then return nil end
  local okR, rootEl = pcall(getroot)
  if not okR or rootEl == nil then return nil end
  local el = nil
  local newEl = fn_of(lui, "UIElement")
  if newEl ~= nil then
    local okE, v = pcall(newEl)
    if okE then el = v end
  end
  if el == nil then
    local uie = member(lui, "UIElement")
    if type(uie) == "table" then
      local f = fn_of(uie, "new")
      if f ~= nil then
        local okN, v = pcall(f)
        if okN then el = v end
      end
    end
  end
  if el == nil then return nil end
  if not pcall(function() return rootEl:addElement(el) end) then return nil end
  return el
end

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

-- one timer step that arms and watches
tick = function()
  Ar.ticks = Ar.ticks + 1
  if not Ar.retired and Ar.ticks <= MAX_TRIES then
    local ok, st = pcall(attempt)
    if not ok or type(st) ~= "table" then st = ARMF end
    pcall(arm, st)
    if Ar.said then pcall(late_line, st) end
    if armed(st) and Ar.pick ~= nil then Ar.retired = true end
  end
  if live() then
    if Ar.pick == nil then pcall(seed, Ar.installed) end
    pcall(watch)
    if Ar.said then pcall(card_watch) end
  end
  if not again() then pcall(start) end
end

S.probes.armory = function() return Ar.installed end

-- the debug row this part adds through the options part
local ROW = {
  id = "pt_unlock_armory",
  name = "Unlock Armory",
  desc = "All Armory items. Off: earn them in the Armory with XP; earned items stay unlocked.",
  kind = "toggle",
  get = function() return uread() end,
  set = function(on) return dchu(on) end,
}

-- registers the row or leaves it to options
local function rowadd()
  local f = A.optrow_add
  if type(f) == "function" then
    local ok, v = pcall(f, ROW)
    if ok then return v == true end
  end
  local q = S.optrows
  if type(q) ~= "table" then
    q = {}
    S.optrows = q
  end
  q[#q + 1] = ROW
  return false
end

pcall(attempt)
pcall(arm, ARMF)
pcall(rowadd)
if not start() then
  log("armory retry timer is not armed - no lui root")
end
if A.ready ~= nil then A.ready() end
