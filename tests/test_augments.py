"""The augment part's replay: the store's ladder, the nine slots, the count and the press.

Read-only. Nothing is installed and nothing is launched. The stubbed frontend VM, its two hash
namespaces and its clock come from `test_progression_tuning.py` by import (`PRELUDE`, `lines_of`,
`has_line`, `count_line`, `pump`); this file only adds what augments need - a hash-keyed
`ZMAUGMENT` with its augment cache and its ladder rows, the game's own `cacheaugmenttierdata`
reading `Challenge.getchallengeprogress`, the count pass reading the user state, the nine slot
publisher over a datasource tree that defaults `is_unlocked` to true, the press and the read-back
the menu's research flow uses, and the hashed dev bool the tier code asks for.

The cases:

   1. the switches off: after a refresh every cached row ends on the numbers the game's own tier
      pass wrote - not the forced complete flag, not 100, not the last tier;
   2. the switches on (`zm_unlock_augments`, then `zm_unlock_all`): the forced values stand, the
      slots keep their default, the count pass never runs and a press records nothing;
   3. the arm line: exactly one line with the three fields, said once across four refreshes, plus
      one line for the owned count and the cache's key type; nothing else is ever printed;
   4. the dev bool: read from the game's own `Dvar.GetDvarBool` call during the tier pass, printed
      as `true`, as `false`, and as `unread` when no tier pass ran;
   5. the ticks: at no progress every augment slot reads false including the slots past the
      bundle's count, past the first step only the first tier reads true;
   6. the count: the number of owned augment loot ids is what the game's own count pass reads, the
      user state member and the ownership member are the same objects after a pass;
   7. the press: event 846 records the achievement id and one line, 53979 and 47576 answer
      `last_activation` with it, every other id passes through as the game's own object;
   8. the string keyed cache: a numeric twin is added to the game's own table, same row object;
   9. the chain: a foreign wrapper put above ours on the refresh, the send and the progress read is
      never wrapped again by us, and the work still happens once through it;
  10. the plain-name fixture: a table keyed by plain names is never touched, and nothing is printed;
  11. the load orders: the module present at load, the module appearing after the part's own timer
      ticks, the part loaded twice, and the timer's own pass once the table arrives;
  12. the decoy: a key one digit off the store's hash is left alone;
  13. the file rule: lowercase comments of ten words at most with no punctuation, no mention of the
      client, and no plain-name indexing of the augmented table;
  14. the research: a press of a carryover id answers 53979 with that row's sat id, and the game's
      own `getcurrentactiveresearch` body, reproduced over the fixture, returns the augment;
  15. the equip lock: the lock door answers locked for an augment id whose tier is not reached and
      open past it, the switches step the rule aside, every other id passes through;
  16. the door chain: an armory-like extender arming before and after ours stays at two wrappers,
      the depth stays the base plus two, and both rules still answer;
  17. the late door: no locks table at load, then the table arriving, then a new table after it;
  18. the channel: a press writes the sat id once, a repeat press of the same row writes nothing,
      and the next press moves the line;
  19. the restore: a saved line answers 53979 and 47576 with the row it names, says one line, and
      a line that arrives after load is seeded on a later tick;
  20. the popup: the first read and the second are the baseline, one crossing raises one native
      event with the kind and the published loot id, a reload mid match cards nothing, and a
      lower read never replays a tier;
  21. the switches and the vm: a switch on raises nothing, the menu vm raises nothing, a press in
      the match vm never writes the channel;
  22. the late popup: the card falls back to the row id while the active item is absent, then
      names the published loot id once it is there.
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

from test_progression_tuning import PRELUDE, count_line, has_line, lines_of, pump  # noqa: E402

LUA_DIR = os.path.join(ROOT, "mod", "progression_tuning", "lua")
PART = os.path.join(LUA_DIR, "progression_tuning_augments_post.lua")
PKG = ROOT

passes, failures, infos = [], [], []


def check(name, cond, detail=""):
    if cond:
        passes.append(name)
        print("PASS  " + name + (("  (" + detail + ")") if detail else ""))
    else:
        failures.append(name + (("  (" + detail + ")") if detail else ""))
        print("FAIL  " + name + (("  (" + detail + ")") if detail else ""))
    return cond


def info(msg):
    infos.append(msg)
    print("INFO  " + msg)


with open(PART, "rb") as fh:
    RAW = fh.read()
SRC = RAW.decode("utf-8")

# the members the part reaches by hash, the way the engine hands them out
ZMFIX = r"""
STORE_K = "#x0d847872560dcd8e4"
DIFF_K = "#x0d847872560dcd8e5"
REFRESH_K = "#x052e47d640bf4ca01"
COUNT_K = "#x0633a1942eeae0eaa"
SLOTS_K = "#x0bd666394faa4374c"
SEND_K = "#x0e636d3bf423fd414"
PROG_K = "#x031eee6570ef4bb8b"
USV_K = "#x0a82011d283698aa4"
DEV_K = setmetatable({}, { __tostring = function() return "xhash: #x1d428ffe65b5694d6" end })
DEVON = false
AID = 40001
BID = 40002
CID_A = 48298
CID_B = 48303
STATE_IP = 1
PROG = { [tostring(AID)] = 0, [tostring(BID)] = 0 }
STATE = { [tostring(AID)] = STATE_IP, [tostring(BID)] = STATE_IP }
function SET_PROG(id, v) PROG[tostring(id)] = v end
local function HK(n) return xhash(n) end
Challenge[HK("getchallengeprogress")] = function(c, id) return PROG[tostring(id)] or 0 end
Challenge[HK("getaeeventid")] = function(name) return 846 end
Challenge[HK("GetAEEventKeyID")] = function(name, key) return 74 end
Challenge[HK("GetAEKindID")] = function(name) return 437 end
Challenge[HK("GetFileTableByType")] = function(kind)
  return { [HK("file")] = "aug.csv", [HK("cols")] = { [0] = "id" } }
end
StringTable = StringTable or {}
ROW0 = { [HK("amount")] = "0|3|6", [HK("augment_unlocks")] = "7001+7002|7003|7004" }
StringTable[HK("tablelookuprowwithcolumndata")] = function(file, row, cols) return ROW0 end
Dvar[HK("GetDvarBool")] = function(k, d)
  if k == DEV_K then return DEVON end
  return d
end
GETSTR = Dvar[xhash("GetDvarString")]

local function row(loot)
  return { [HK("lootid")] = loot, [HK("IsUnlocked")] = true, [HK("progress")] = 0,
           [HK("displayname")] = "aug" .. loot }
end
local function rows(base)
  return { row(base), row(base + 1), row(base + 2), isResearchComplete = true, totalProgress = 100,
           currentTier = 3, isUnlocked = true, amountNeededToUnlock = "0" }
end
Z = {}
Z[STORE_K] = { sat_aug_one = rows(801), sat_aug_two = rows(901) }
Z[DIFF_K] = { decoy = rows(701) }
Z[HK("lootid_to_ref")] = { [7001] = "sat_aug_one", [7002] = "sat_aug_two" }
Z[HK("augmentresearchchallenges")] = {
  [7001] = { [HK("achievementID")] = AID, [HK("carryoverAchievementID")] = CID_A,
             [HK("amount")] = "70000|140000|275000" },
  [7002] = { [HK("achievementID")] = BID, [HK("carryoverAchievementID")] = CID_B,
             [HK("amount")] = "70000|140000|275000" },
}
Z[HK("cacheaugmenttierdata")] = function(c, ch, loot)
  local ref = Z[HK("lootid_to_ref")][loot]
  local entry = ref ~= nil and Z[STORE_K][ref] or nil
  if entry == nil then return end
  local p = Challenge[HK("getchallengeprogress")](c, ch[HK("achievementID")])
  local dev = Dvar[HK("GetDvarBool")](DEV_K, false)
  entry.currentTier = 1
  entry.totalProgress = 0
  entry.isResearchComplete = dev and true or false
  entry.tierAt = p
end
function TIER_ALL(c)
  for loot, ch in pairs(Z[HK("augmentresearchchallenges")]) do
    Z[HK("cacheaugmenttierdata")](c, ch, loot)
  end
end
function TOGGLED()
  return GETSTR(xhashdvar("zm_unlock_augments")) == "1"
      or GETSTR(xhashdvar("zm_unlock_all")) == "1"
end
CALLS = 0
Z[REFRESH_K] = function(c)
  CALLS = CALLS + 1
  TIER_ALL(c)
  for _, e in pairs(Z[STORE_K]) do e.isResearchComplete = true end
  if TOGGLED() then
    for _, e in pairs(Z[STORE_K]) do
      for i = 1, #e do if type(e[i]) == "table" then e[i][HK("progress")] = 1 end end
      e.isUnlocked, e.isResearchComplete, e.totalProgress, e.currentTier = true, true, 100, #e
    end
  end
end

BUNDLE_N = 3
PUBLISHED = 0
local ARR = {}
for i = 1, 9 do ARR[i] = {} end
local LEAF = {
  [HK("GetValue")] = function(self, c) return self.v end,
  [HK("SetValue")] = function(self, c, x) self.v = x; return true end,
}
local function dleaf(v) return setmetatable({ v = v }, { __index = LEAF }) end
for i = 1, 9 do ARR[i][HK("is_unlocked")] = dleaf(true) end
_DataSources = { [HK("zm")] = { [HK("frontend")] = { [HK("augment_select")] = {
  [HK("current_augment_research")] = ARR } } } }
ACTIVE = dleaf(107157)
_DataSources[HK("zm")][HK("frontend")][HK("augment_select")][HK("active_augment_research_item")] =
  { [HK("loot_id")] = ACTIVE }
function DROPACTIVE()
  _DataSources[HK("zm")][HK("frontend")][HK("augment_select")][HK("active_augment_research_item")] = nil
end
function PUTACTIVE()
  _DataSources[HK("zm")][HK("frontend")][HK("augment_select")][HK("active_augment_research_item")] =
    { [HK("loot_id")] = ACTIVE }
end
function CHV() return DVARS[xhashdvar("pt_research_ch")] or "" end
function SLOTV(i) return ARR[i][HK("is_unlocked")].v end
function SLALL() local s = ""; for i = 1, 9 do s = s .. (ARR[i][HK("is_unlocked")].v and "1" or "0") end; return s end
function SLRESET() for i = 1, 9 do ARR[i][HK("is_unlocked")].v = true end end
function PUB(c, ref)
  ZMAUGMENT[SLOTS_K](c, dleaf(ref))
end
Z[SLOTS_K] = function(c, item)
  PUBLISHED = PUBLISHED + 1
  local get = item and item[HK("GetValue")]
  local ref = get and get(item, c) or nil
  local list = ref and Z[STORE_K][ref] or nil
  for i = 1, BUNDLE_N do
    local e = list and list[i] or nil
    local ds = ARR[i][HK("is_unlocked")]
    if e ~= nil then ds.v = e[HK("IsUnlocked")] else ds.v = false end
  end
end

COUNTED, COUNT_ROW, COUNT_CALLS = nil, nil, 0
Z[COUNT_K] = function(c, row)
  COUNT_CALLS = COUNT_CALLS + 1
  COUNT_ROW = row
  local OP = rawget(_G, "OnlineProgression")
  local f = OP and OP[USV_K]
  local got = nil
  if type(f) == "function" then
    local r = f(c, { "k" })
    got = r and r["k"]
  end
  COUNTED = got
  for _, e in pairs(Z[STORE_K]) do e.amountNeededToUnlock = tostring(got) end
  return 0
end

OnlineProgression = {}
USV_CALLS = 0
USV_ORIG = function(c, keys) USV_CALLS = USV_CALLS + 1; return {} end
OnlineProgression[USV_K] = USV_ORIG
function USV_SAME() return OnlineProgression[USV_K] == USV_ORIG end
function USV_N() local n = 0; for _ in pairs(OnlineProgression) do n = n + 1 end; return n end

PROXY_LOOT = {}
PO_ORIG = function(c, id) return 1 end
PROXY_LOOT[HK("IsOwned")] = PO_ORIG
function PO_SAME() return PROXY_LOOT[HK("IsOwned")] == PO_ORIG end
function PO_N() local n = 0; for _ in pairs(PROXY_LOOT) do n = n + 1 end; return n end

Challenges = Challenges or {}
SENT = 0
SEND_ORIG = function(c, ev, n, ...) SENT = SENT + 1; return true end
Challenges[SEND_K] = SEND_ORIG
PROG_ROWS = {}
PROG_ORIG = function(c, id)
  local k = tostring(id)
  PROG_ROWS[k] = PROG_ROWS[k] or { progress = { xp = 0 } }
  return PROG_ROWS[k]
end
OnlineChallenges[PROG_K] = PROG_ORIG
OnlineChallenges[HK("getchallengestate")] = function(c, id) return STATE[tostring(id)] or 0 end

function GETACTIVE(c)
  local C = Z[HK("augmentresearchchallenges")]
  local gs = OnlineChallenges[HK("getchallengestate")]
  local r = OnlineChallenges[PROG_K](c, 53979)
  local sat = 0
  if r and r.progress and r.progress.last_activation then sat = r.progress.last_activation end
  for loot, ch in pairs(C) do
    local aid = ch[HK("achievementID")]
    if gs(c, aid) == STATE_IP and aid == sat then return loot end
    local co = ch[HK("carryoverAchievementID")]
    if 0 < co and gs(c, co) == STATE_IP then return loot end
  end
  return 0
end

DEPTH, DEPTHMAX = 0, 0
local function enter()
  DEPTH = DEPTH + 1
  if DEPTH > DEPTHMAX then DEPTHMAX = DEPTH end
end
SEC_A = function(id)
  enter()
  local v = id == 555
  DEPTH = DEPTH - 1
  return v
end
SEC_O = function(id)
  enter()
  local v = id == 556
  DEPTH = DEPTH - 1
  return v
end
function PRISON()
  local S = rawget(_G, "ProgressionTuning")
  if type(S) ~= "table" then
    S = { parts = {}, hooks = {}, probes = {}, api = {}, g11 = {}, scope = {} }
    rawset(_G, "ProgressionTuning", S)
  end
  S.locks = { answer = SEC_A, open = SEC_O, arm = function() end, tick = function() end }
end
function NOPRISON()
  if type(rawget(_G, "ProgressionTuning")) == "table" then ProgressionTuning.locks = nil end
end
function ANS(id) return ProgressionTuning.locks.answer(id) end
function OPN(id) return ProgressionTuning.locks.open(id) end
function FACE(w) return ProgressionTuning.locks[w] end
SEEN = {}
EXT_N = 0
local function ext(orig, own)
  local w = function(id)
    enter()
    local v = orig(id)
    DEPTH = DEPTH - 1
    if id == own then return true end
    return v
  end
  SEEN[w] = true
  return w
end
function EXT()
  local locks = ProgressionTuning.locks
  if type(locks) ~= "table" then return end
  local a = locks.answer
  if not SEEN[a] then
    EXT_N = EXT_N + 1
    locks.answer = ext(a, 777)
  end
  local o = locks.open
  if not SEEN[o] then
    locks.open = ext(o, 778)
  end
end

function MAKEZM() ZMAUGMENT = Z end
function REFRESH(c) ZMAUGMENT[REFRESH_K](c) end
function FIELD(ref, name) local e = ZMAUGMENT[STORE_K][ref]; return tostring(e and e[name]) end
function TIER(ref, i)
  local e = ZMAUGMENT[STORE_K][ref]
  local v = e and e[i] and e[i][xhash("progress")]
  return tostring(v)
end
function LOCKS(ref)
  local e = ZMAUGMENT[STORE_K][ref]
  local s = ""
  for i = 1, 3 do s = s .. (e[i][xhash("IsUnlocked")] and "1" or "0") end
  return s
end
function PRESS(id) Challenges[SEND_K](0, 846, 2, 74, id, 2048) end
function LAST(id)
  local r = OnlineChallenges[PROG_K](0, id)
  local p = r and r.progress
  return tostring(p and p.last_activation)
end
function OTHER(id)
  local r = OnlineChallenges[PROG_K](0, id)
  return tostring(r == PROG_ROWS[tostring(id)]), tostring(r and r.progress and r.progress.last_activation)
end
function STRKEYS()
  local C = Z[HK("augmentresearchchallenges")]
  C["7001"] = C[7001]
  C[7001] = nil
  C["7002"] = C[7002]
  C[7002] = nil
end
function SAMEROW(k)
  local C = Z[HK("augmentresearchchallenges")]
  return tostring(C[7001] == C[k])
end
function CACHEK() return type(next(Z[HK("augmentresearchchallenges")])) end
CARDED = 0
Z[HK("initcurrentactiveresearch")] = function(c) CARDED = CARDED + 1 end
"""

# the same table keyed the plain way - never indexed by the part
ZMPLAIN = r"""
DEV_K = setmetatable({}, { __tostring = function() return "xhash: #x1d428ffe65b5694d6" end })
Dvar[xhash("GetDvarBool")] = function(k, d) return d end
Challenge[xhash("getchallengeprogress")] = function(c, id) return 0 end
ZMAUGMENT = {}
ZMAUGMENT.augmentlist_full = { sat_aug_one = { isResearchComplete = true, totalProgress = 100, currentTier = 3 } }
ZMAUGMENT.lootid_to_ref = { [7001] = "sat_aug_one" }
ZMAUGMENT.augmentresearchchallenges = { [7001] = { achievementID = 40001, amount = "70000" } }
ZMAUGMENT.cacheaugmenttierdata = function(c, ch, loot) end
ZMAUGMENT.refresh = function(c) PLAIN_CALLS = PLAIN_CALLS + 1 end
PLAIN_CALLS = 0
PLAIN_FACE = ZMAUGMENT.refresh
function PLAIN_SAME() return ZMAUGMENT.refresh == PLAIN_FACE end
"""

# the hash-keyed table with no tier pass and no cache: nothing to re-run, nothing to read
ZMNOTIER = r"""
STORE_K = "#x0d847872560dcd8e4"
REFRESH_K = "#x052e47d640bf4ca01"
Z = {}
Z[STORE_K] = { sat_aug_one = { isResearchComplete = true, totalProgress = 100, currentTier = 3 } }
Z[REFRESH_K] = function(c) for _, e in pairs(Z[STORE_K]) do e.isResearchComplete = true end end
function MAKEZM() ZMAUGMENT = Z end
function REFRESH(c) ZMAUGMENT[REFRESH_K](c) end
function FIELD(ref, name) local e = ZMAUGMENT[STORE_K][ref]; return tostring(e and e[name]) end
FACED = true
"""


def lua51():
    from lupa.lua51 import LuaRuntime
    return LuaRuntime


def rt(fixture, extra="", part=True):
    r = lua51()(unpack_returned_tuples=True)
    r.execute(PRELUDE)
    r.execute("FRONTEND = true")
    if fixture:
        r.execute(fixture)
    if extra:
        r.execute(extra)
    if part:
        r.execute(SRC)
    return r


def val(r, expr):
    v = r.eval(expr)
    return None if v is None else str(v)


def arm_line(lines):
    out = [ln for ln in lines if "augments armed" in ln]
    return out[0] if out else ""


def owned_line(lines):
    out = [ln for ln in lines if "augments owned=" in ln]
    return out[0] if out else ""


def off(r):
    r.execute("SET_DVAR('zm_unlock_augments', '0'); SET_DVAR('zm_unlock_all', '0')")


# --- 1: the switches decide whose numbers stand ------------------------------------------------
def case_off(lua51):
    r = rt(ZMFIX + "\nMAKEZM()")
    off(r)
    r.execute("REFRESH(0)")
    check("off: a row ends incomplete, not forcibly complete", val(r, "FIELD('sat_aug_one','isResearchComplete')") == "false",
          "isResearchComplete=" + val(r, "FIELD('sat_aug_one','isResearchComplete')"))
    check("off: the total is the game's own 0, not 100", val(r, "FIELD('sat_aug_one','totalProgress')") == "0",
          "totalProgress=" + val(r, "FIELD('sat_aug_one','totalProgress')"))
    check("off: the current tier is the game's own 1, not the last", val(r, "FIELD('sat_aug_one','currentTier')") == "1",
          "currentTier=" + val(r, "FIELD('sat_aug_one','currentTier')"))
    check("off: the tier progress stays the game's own 0", val(r, "TIER('sat_aug_one',1)") == "0",
          "tier1=" + val(r, "TIER('sat_aug_one',1)"))
    check("off: the second row is re-run too", val(r, "FIELD('sat_aug_two','tierAt')") == "0",
          "tierAt=" + val(r, "FIELD('sat_aug_two','tierAt')"))
    r.execute("SET_PROG(40001, 300000); SET_PROG(40002, 100000); DEVON = true")
    r.execute("REFRESH(0)")
    check("off: a completed row and a partial row both follow the store",
          val(r, "FIELD('sat_aug_one','tierAt')") == "300000" and val(r, "FIELD('sat_aug_two','tierAt')") == "100000",
          "one=" + val(r, "FIELD('sat_aug_one','tierAt')") + " two=" + val(r, "FIELD('sat_aug_two','tierAt')"))
    check("off: the dev bool is the tier code's own answer",
          val(r, "FIELD('sat_aug_one','isResearchComplete')") == "true",
          "isResearchComplete=" + val(r, "FIELD('sat_aug_one','isResearchComplete')"))
    check("off: the refresh the game owns still ran once per call", val(r, "CALLS") == "2", "calls=" + val(r, "CALLS"))


# --- 2: the switches on leave every new answer alone -------------------------------------------
def case_on(lua51):
    r = rt(ZMFIX + "\nMAKEZM()")
    r.execute("SET_DVAR('zm_unlock_all', '0'); SET_DVAR('zm_unlock_augments', '1')")
    r.execute("SET_PROG(40001, 0)")
    r.execute("REFRESH(0)")
    check("on (augments): the forced complete stands", val(r, "FIELD('sat_aug_one','isResearchComplete')") == "true",
          "isResearchComplete=" + val(r, "FIELD('sat_aug_one','isResearchComplete')"))
    check("on (augments): the forced 100 stands", val(r, "FIELD('sat_aug_one','totalProgress')") == "100",
          "totalProgress=" + val(r, "FIELD('sat_aug_one','totalProgress')"))
    check("on (augments): the last tier stands", val(r, "FIELD('sat_aug_one','currentTier')") == "3",
          "currentTier=" + val(r, "FIELD('sat_aug_one','currentTier')"))
    check("on (augments): the tier progress stands at one", val(r, "TIER('sat_aug_one',1)") == "1",
          "tier1=" + val(r, "TIER('sat_aug_one',1)"))
    check("on: no tick is written and no count is fed",
          val(r, "LOCKS('sat_aug_one')") == "111" and val(r, "COUNT_CALLS") == "0",
          "locks=" + val(r, "LOCKS('sat_aug_one')") + " count=" + val(r, "COUNT_CALLS"))
    r.execute("PUB(0, 'sat_aug_one')")
    check("on: the slots keep the game's own default", val(r, "SLALL()") == "111111111", val(r, "SLALL()"))
    r.execute("PRESS(40001)")
    check("on: a press records nothing and says nothing",
          val(r, "ProgressionTuning.aug.active") in ("0", "0.0")
          and count_line(lines_of(r), "augments research start") == 0,
          "active=" + val(r, "ProgressionTuning.aug.active"))
    r2 = rt(ZMFIX + "\nMAKEZM()")
    r2.execute("SET_DVAR('zm_unlock_augments', '0'); SET_DVAR('zm_unlock_all', '1')")
    r2.execute("REFRESH(0)")
    check("on (all): every forced value stands with the other switch",
          val(r2, "FIELD('sat_aug_one','totalProgress')") == "100" and val(r2, "TIER('sat_aug_one',1)") == "1",
          "total=" + val(r2, "FIELD('sat_aug_one','totalProgress')") + " tier1=" + val(r2, "TIER('sat_aug_one',1)"))
    check("on: the arm line names the switches it read", "unlock=1" in arm_line(lines_of(r)),
          arm_line(lines_of(r)))


# --- 3 and 4: the two lines, and the bool the first one carries --------------------------------
def case_line(lua51):
    r = rt(ZMFIX + "\nMAKEZM()")
    off(r)
    r.execute("REFRESH(0)")
    l = lines_of(r)
    check("line: one arm line, one owned line and nothing else", len(l) == 2,
          "%d lines: %s" % (len(l), " | ".join(l[:3])))
    want = "progression_tuning: augments armed v4 unlock=0 all=0 devcomplete=false"
    check("line: the exact arm wording", arm_line(l) == want, arm_line(l))
    check("line: the owned line names the count and the key type",
          owned_line(l) == "progression_tuning: augments owned=0 keys=number", owned_line(l))
    r.execute("REFRESH(0); REFRESH(0); REFRESH(0)")
    check("line: said once over four refreshes", count_line(lines_of(r), "augments armed") == 1,
          "%d" % count_line(lines_of(r), "augments armed"))
    check("line: the owned line once as well", count_line(lines_of(r), "augments owned") == 1,
          "%d" % count_line(lines_of(r), "augments owned"))
    r3 = rt(ZMFIX + "\nMAKEZM()")
    r3.execute("SET_DVAR('zm_unlock_augments', '0'); SET_DVAR('zm_unlock_all', '0'); DEVON = true")
    r3.execute("REFRESH(0)")
    check("line: devcomplete reads the bool the game asked for",
          "devcomplete=true" in arm_line(lines_of(r3)), arm_line(lines_of(r3)))
    r4 = rt(ZMNOTIER + "\nMAKEZM()")
    off(r4)
    r4.execute("REFRESH(0)")
    check("line: no tier pass to run means no claim and no line", len(lines_of(r4)) == 0,
          " | ".join(lines_of(r4)[:2]))


# --- 5: the nine ticks follow the ladder reached ------------------------------------------------
def case_ticks(lua51):
    r = rt(ZMFIX + "\nMAKEZM()")
    off(r)
    r.execute("REFRESH(0)")
    r.execute("SLRESET(); PUB(0, 'sat_aug_one')")
    check("ticks: no progress leaves every augment entry locked", val(r, "LOCKS('sat_aug_one')") == "000",
          "locks=" + val(r, "LOCKS('sat_aug_one')"))
    check("ticks: no progress leaves all nine slots locked past the bundle count too",
          val(r, "SLALL()") == "000000000", val(r, "SLALL()"))
    r.execute("SET_PROG(40001, 70000)")
    r.execute("SET_PROG(40002, 0)")
    r.execute("REFRESH(0)")
    r.execute("SLRESET(); PUB(0, 'sat_aug_one')")
    check("ticks: past the first step only the first tier reads researched",
          val(r, "LOCKS('sat_aug_one')") == "100", "locks=" + val(r, "LOCKS('sat_aug_one')"))
    check("ticks: the first slot reads unlocked and the rest locked", val(r, "SLALL()") == "100000000",
          val(r, "SLALL()"))
    r.execute("SET_PROG(40001, 150000)")
    r.execute("REFRESH(0)")
    r.execute("SLRESET(); PUB(0, 'sat_aug_one')")
    check("ticks: past the second step two tiers read researched",
          val(r, "LOCKS('sat_aug_one')") == "110" and val(r, "SLALL()") == "110000000",
          "locks=" + val(r, "LOCKS('sat_aug_one')") + " slots=" + val(r, "SLALL()"))
    r.execute("SET_PROG(40001, 300000)")
    r.execute("REFRESH(0)")
    check("ticks: a finished ladder leaves all three tiers researched",
          val(r, "LOCKS('sat_aug_one')") == "111", "locks=" + val(r, "LOCKS('sat_aug_one')"))
    r.execute("SET_PROG(40001, 0)")
    r.execute("REFRESH(0)")
    r.execute("PUB(0, 'sat_aug_one')")
    check("ticks: a slot past the bundle count is written by the publisher wrapper",
          val(r, "SLOTV(9)") == "False", "slot9=" + val(r, "SLOTV(9)"))


# --- 6: the count the game's own ladder pass reads ----------------------------------------------
def case_count(lua51):
    r = rt(ZMFIX + "\nMAKEZM()")
    off(r)
    r.execute("REFRESH(0)")
    check("count: nothing owned feeds a zero", val(r, "COUNTED") in ("0", "0.0"), "counted=" + val(r, "COUNTED"))
    r.execute("SET_PROG(40001, 70000); SET_PROG(40002, 140000)")
    r.execute("REFRESH(0)")
    check("count: two researched tiers feed the ladders' owned ids",
          val(r, "COUNTED") in ("3", "3.0"), "counted=" + val(r, "COUNTED"))
    check("count: the game's own pass reads the row the table holds", val(r, "COUNT_ROW == ROW0") == "True",
          val(r, "COUNT_ROW == ROW0"))
    check("count: the ladder gate follows the count the pass saw",
          val(r, "FIELD('sat_aug_one','amountNeededToUnlock')") == "3",
          val(r, "FIELD('sat_aug_one','amountNeededToUnlock')"))
    check("count: the user state reader is the same function after the pass", val(r, "USV_SAME()") == "True",
          val(r, "USV_SAME()"))
    check("count: the user state table keeps its one member", val(r, "USV_N()") == "1", val(r, "USV_N()"))
    check("count: the ownership getter is the same function after the pass", val(r, "PO_SAME()") == "True",
          val(r, "PO_SAME()"))
    check("count: the ownership table keeps its one member", val(r, "PO_N()") == "1", val(r, "PO_N()"))
    before = val(r, "COUNT_CALLS")
    r.execute("REFRESH(0); REFRESH(0)")
    check("count: one feed per refresh pass", int(val(r, "COUNT_CALLS")) == int(before) + 2,
          "%s -> %s" % (before, val(r, "COUNT_CALLS")))


# --- 7: the press and the read-back -------------------------------------------------------------
def case_press(lua51):
    r = rt(ZMFIX + "\nMAKEZM()")
    off(r)
    r.execute("REFRESH(0)")
    r.execute("PRESS(40001)")
    check("press: the achievement id is recorded", val(r, "ProgressionTuning.aug.active") in ("40001", "40001.0"),
          "active=" + val(r, "ProgressionTuning.aug.active"))
    check("press: one line names the two ids",
          count_line(lines_of(r), "progression_tuning: augments research start id=40001 sat=40001") == 1,
          " | ".join([ln for ln in lines_of(r) if "research start" in ln][:2]))
    check("press: 53979 answers the activation with it", val(r, "LAST(53979)") == "40001", val(r, "LAST(53979)"))
    check("press: 47576 answers the activation with it", val(r, "LAST(47576)") == "40001", val(r, "LAST(47576)"))
    check("press: the game's own send still ran once", val(r, "SENT") == "1", "sent=" + val(r, "SENT"))
    r.execute("Challenges[SEND_K](0, 999, 2, 74, 40002, 2048)")
    check("press: another event passes through and changes nothing",
          count_line(lines_of(r), "augments research start") == 1
          and val(r, "ProgressionTuning.aug.active") in ("40001", "40001.0"),
          "active=" + val(r, "ProgressionTuning.aug.active"))
    r.execute("LAST(12345)")
    check("press: an unrelated row is the game's own object untouched",
          val(r, "OTHER(12345)") == "('true', 'nil')", val(r, "OTHER(12345)"))
    r.execute("REFRESH(0)")
    check("press: the card is asked for once the press lands",
          val(r, "CARDED") in ("1", "1.0") and r.eval("ProgressionTuning.aug.dirty") is False,
          "carded=" + val(r, "CARDED"))
    r2 = rt(ZMFIX + "\nMAKEZM()")
    off(r2)
    r2.execute("REFRESH(0)")
    r2.execute("PRESS(40002)")
    check("press: a second press moves the answer", val(r2, "LAST(53979)") == "40002"
          and count_line(lines_of(r2), "augments research start") == 1, val(r2, "LAST(53979)"))


# --- 8: the string keyed cache gets a numeric twin ----------------------------------------------
def case_alias(lua51):
    r = rt(ZMFIX + "\nMAKEZM()")
    off(r)
    r.execute("STRKEYS()")
    check("alias: the cache is string keyed to start with", val(r, "CACHEK()") == "string", val(r, "CACHEK()"))
    r.execute("SET_PROG(40001, 70000)")
    r.execute("REFRESH(0)")
    check("alias: the numeric twin is the same row object", val(r, "SAMEROW(7001)") == "true",
          val(r, "SAMEROW(7001)"))
    check("alias: the ticks still follow the ladder through the twin",
          val(r, "LOCKS('sat_aug_one')") == "100", "locks=" + val(r, "LOCKS('sat_aug_one')"))
    check("alias: the line names the string keys", "keys=string" in owned_line(lines_of(r)), owned_line(lines_of(r)))


# --- 9: the chain stays bounded under a foreign wrapper ----------------------------------------
def case_chain(lua51):
    r = rt(ZMFIX + "\nMAKEZM()")
    off(r)
    r.execute("REFRESH(0)")
    r.execute("""
      KEEP = ZMAUGMENT[REFRESH_K]
      TOP = function(c) KEEP(c); for _, e in pairs(Z[STORE_K]) do e.totalProgress = 42 end end
      ZMAUGMENT[REFRESH_K] = TOP
      KEEPS = Challenges[SEND_K]
      TOPS = function(c, ev, n, ...) return KEEPS(c, ev, n, ...) end
      Challenges[SEND_K] = TOPS
      KEEPP = OnlineChallenges[PROG_K]
      TOPP = function(c, id, ...) return KEEPP(c, id, ...) end
      OnlineChallenges[PROG_K] = TOPP
    """)
    for _ in range(6):
        pump(r, 1)
        r.execute("REFRESH(0)")
    check("chain: the refresh wrapper the foreign one holds is not wrapped again",
          val(r, "ZMAUGMENT[REFRESH_K] == TOP") == "True", val(r, "ZMAUGMENT[REFRESH_K] == TOP"))
    check("chain: the send wrapper the foreign one holds is not wrapped again",
          val(r, "Challenges[SEND_K] == TOPS") == "True", val(r, "Challenges[SEND_K] == TOPS"))
    check("chain: the progress wrapper the foreign one holds is not wrapped again",
          val(r, "OnlineChallenges[PROG_K] == TOPP") == "True", val(r, "OnlineChallenges[PROG_K] == TOPP"))
    before = val(r, "COUNT_CALLS")
    r.execute("REFRESH(0)")
    check("chain: the pass still runs once through the foreign wrapper",
          int(val(r, "COUNT_CALLS")) == int(before) + 1, "%s -> %s" % (before, val(r, "COUNT_CALLS")))
    r.execute("PRESS(40001)")
    check("chain: one press through the foreign wrapper says one line",
          count_line(lines_of(r), "augments research start") == 1,
          "%d" % count_line(lines_of(r), "augments research start"))
    check("chain: the answer still comes through the foreign wrapper", val(r, "LAST(53979)") == "40001",
          val(r, "LAST(53979)"))
    check("chain: a foreign wrapper that forces a number is answered by the next pass",
          val(r, "FIELD('sat_aug_one','totalProgress')") == "42", val(r, "FIELD('sat_aug_one','totalProgress')"))
    pump(r, 8)
    check("chain: the timer's own pass puts the store's number back",
          val(r, "FIELD('sat_aug_one','totalProgress')") == "0", val(r, "FIELD('sat_aug_one','totalProgress')"))


# --- 10, 11, 12: what must not be touched, and every load order ---------------------------------
def case_plain(lua51):
    r = rt(ZMPLAIN)
    pump(r, 3)
    r.execute("ZMAUGMENT.refresh(0)")
    check("plain: a plain-name table is never wrapped", val(r, "PLAIN_SAME()") == "True"
          and val(r, "PLAIN_CALLS") == "1", "calls=" + val(r, "PLAIN_CALLS"))
    check("plain: nothing is printed", len(lines_of(r)) == 0, " | ".join(lines_of(r)[:3]))


def case_late(lua51):
    r = rt(ZMFIX)
    pump(r, 2)
    check("late: no table yet means no wrap and no line", count_line(lines_of(r), "augments armed") == 0,
          "%d lines" % len(lines_of(r)))
    r.execute("MAKEZM()")
    pump(r, 2)
    off(r)
    r.execute("REFRESH(0)")
    check("late: the timer arms when the table arrives",
          val(r, "FIELD('sat_aug_one','totalProgress')") == "0",
          "total=" + val(r, "FIELD('sat_aug_one','totalProgress')"))
    check("late: one arm line once the table is there", count_line(lines_of(r), "augments armed") == 1,
          "%d" % count_line(lines_of(r), "augments armed"))
    check("late: the press is caught once the table is there",
          (r.execute("PRESS(40001)") or True) and val(r, "LAST(53979)") == "40001", val(r, "LAST(53979)"))


def case_late_read(lua51):
    r = rt(ZMFIX + "\nMAKEZM()\nOC_SAVE = OnlineChallenges\nOnlineChallenges = nil")
    off(r)
    pump(r, 2)
    r.execute("PRESS(40001)")
    check("late read: a press is recorded while the read table is absent",
          val(r, "ProgressionTuning.aug.active") in ("40001", "40001.0")
          and count_line(lines_of(r), "augments research start") == 1,
          "active=" + val(r, "ProgressionTuning.aug.active"))
    r.execute("OnlineChallenges = OC_SAVE")
    pump(r, 1)
    check("late read: the read is wrapped once the table arrives", val(r, "LAST(53979)") == "40001",
          val(r, "LAST(53979)"))


def case_tick_pass(lua51):
    r = rt(ZMFIX + "\nMAKEZM()")
    off(r)
    pump(r, 1)
    first = val(r, "COUNT_CALLS")
    pump(r, 8)
    check("tick: the timer runs a pass of its own", int(val(r, "COUNT_CALLS")) > int(first),
          "%s -> %s" % (first, val(r, "COUNT_CALLS")))


def case_twice(lua51):
    r = rt(ZMFIX + "\nMAKEZM()")
    r.execute(SRC)
    off(r)
    r.execute("REFRESH(0)")
    check("twice: the second load wraps nothing again", val(r, "CALLS") == "1", "calls=" + val(r, "CALLS"))
    check("twice: still one arm line", count_line(lines_of(r), "augments armed") == 1,
          "%d" % count_line(lines_of(r), "augments armed"))
    check("twice: the part kept its own marker", r.eval("ProgressionTuning.parts.augments") is True,
          str(r.eval("ProgressionTuning.parts.augments")))


def case_decoy(lua51):
    r = rt(ZMFIX + "\nMAKEZM()")
    off(r)
    r.execute("REFRESH(0)")
    check("decoy: the key one digit off the store is left alone",
          val(r, "ZMAUGMENT['#x0d847872560dcd8e5'].decoy.totalProgress") == "100",
          val(r, "ZMAUGMENT['#x0d847872560dcd8e5'].decoy.totalProgress"))


def case_blind(lua51):
    r = rt(ZMFIX + "\nMAKEZM()")
    off(r)
    r.execute("Dvar[xhash('GetDvarString')] = nil")
    r.execute("REFRESH(0)")
    check("blind: an unreadable switch leaves the pass alone",
          r.eval("ProgressionTuning.aug.devseen") is False and r.eval("ProgressionTuning.aug.said") is False,
          "devseen=" + str(r.eval("ProgressionTuning.aug.devseen")))
    check("blind: and claims nothing", len(lines_of(r)) == 0, " | ".join(lines_of(r)[:2]))


# --- 14: the press resolves the carryover twin to the sat row --------------------------------
def case_research(lua51):
    r = rt(ZMFIX + "\nMAKEZM()")
    off(r)
    r.execute("REFRESH(0)")
    r.execute("PRESS(48298)")
    check("research: a carryover press keeps the sent id",
          val(r, "ProgressionTuning.aug.active") in ("48298", "48298.0"),
          "active=" + val(r, "ProgressionTuning.aug.active"))
    check("research: 53979 answers the sat id, not the sent one", val(r, "LAST(53979)") == "40001",
          val(r, "LAST(53979)"))
    check("research: 47576 keeps the sent id", val(r, "LAST(47576)") == "48298", val(r, "LAST(47576)"))
    check("research: one line carries both ids",
          count_line(lines_of(r), "progression_tuning: augments research start id=48298 sat=40001") == 1,
          " | ".join([ln for ln in lines_of(r) if "research start" in ln][:2]))
    check("research: the active research read returns that augment", val(r, "GETACTIVE(0)") == "7001",
          val(r, "GETACTIVE(0)"))
    r2 = rt(ZMFIX + "\nMAKEZM()")
    off(r2)
    r2.execute("REFRESH(0)")
    r2.execute("PRESS(40001)")
    check("research: a sat press answers its own id", val(r2, "LAST(53979)") == "40001"
          and val(r2, "GETACTIVE(0)") == "7001", val(r2, "LAST(53979)") + " / " + val(r2, "GETACTIVE(0)"))
    r3 = rt(ZMFIX + "\nMAKEZM()")
    off(r3)
    r3.execute("REFRESH(0)")
    r3.execute("PRESS(48303)")
    check("research: the other carryover resolves to its own row", val(r3, "LAST(53979)") == "40002"
          and val(r3, "GETACTIVE(0)") == "7002", val(r3, "LAST(53979)") + " / " + val(r3, "GETACTIVE(0)"))
    r4 = rt(ZMFIX + "\nMAKEZM()")
    off(r4)
    r4.execute("REFRESH(0)")
    r4.execute("PRESS(40003)")
    check("research: an id in no row resolves to itself", val(r4, "LAST(53979)") == "40003"
          and count_line(lines_of(r4), "id=40003 sat=40003") == 1, val(r4, "LAST(53979)"))


# --- 15: the equip list is locked by the same tier rule --------------------------------------
def case_lock(lua51):
    r = rt(ZMFIX + "\nMAKEZM()")
    off(r)
    r.execute("PRISON()")
    r.execute("REFRESH(0)")
    pump(r, 1)
    check("lock: nothing researched leaves the augment ids locked",
          r.eval("ANS(801)") is True and r.eval("ANS(802)") is True and r.eval("ANS(803)") is True,
          "801=%s 802=%s" % (val(r, "ANS(801)"), val(r, "ANS(802)")))
    check("lock: the open side says no for them", r.eval("OPN(801)") is False and r.eval("OPN(903)") is False,
          "801=%s" % val(r, "OPN(801)"))
    check("lock: an id in no augment list passes through", r.eval("ANS(999)") is False
          and r.eval("ANS(555)") is True, "999=%s 555=%s" % (val(r, "ANS(999)"), val(r, "ANS(555)")))
    check("lock: the open side passes through too", r.eval("OPN(556)") is True
          and r.eval("OPN(999)") is False, val(r, "OPN(556)"))
    r.execute("SET_PROG(40001, 70000)")
    r.execute("REFRESH(0)")
    check("lock: the first tier opens and the rest stay locked", r.eval("ANS(801)") is False
          and r.eval("OPN(801)") is True and r.eval("ANS(802)") is True,
          "801=%s 802=%s" % (val(r, "ANS(801)"), val(r, "ANS(802)")))
    check("lock: the other equipment keeps its own tier", r.eval("ANS(901)") is True,
          val(r, "ANS(901)"))
    r.execute("SET_PROG(40001, 300000)")
    r.execute("REFRESH(0)")
    check("lock: a finished ladder opens every tier of that row", r.eval("ANS(803)") is False
          and r.eval("OPN(803)") is True and r.eval("ANS(903)") is True,
          "803=%s 903=%s" % (val(r, "ANS(803)"), val(r, "ANS(903)")))
    r.execute("SET_DVAR('zm_unlock_augments', '1')")
    r.execute("REFRESH(0)")
    check("lock: the switch steps the rule aside", r.eval("ANS(903)") is False
          and r.eval("OPN(903)") is False, val(r, "ANS(903)"))
    r.execute("SET_DVAR('zm_unlock_augments', '0')")
    r.execute("REFRESH(0)")
    check("lock: the rule applies again once the switch is off", r.eval("ANS(903)") is True,
          val(r, "ANS(903)"))
    check("lock: the table keeps its other members",
          val(r, "type(ProgressionTuning.locks.arm)") == "function"
          and val(r, "type(ProgressionTuning.locks.tick)") == "function", val(r, "type(ProgressionTuning.locks.arm)"))


# --- 16: the chain with an armory like extender stays bounded --------------------------------
def case_lock_chain(lua51):
    r = rt(ZMFIX + "\nMAKEZM()", "PRISON()\nEXT()")
    off(r)
    r.execute("REFRESH(0)")
    check("chain lock: the door is extended at load when the table is there",
          val(r, "FACE('answer') == SEC_A") == "False" and val(r, "EXT_N") == "1", val(r, "EXT_N"))
    before = val(r, "FACE('answer')")
    for _ in range(1, 6):
        r.execute("EXT()")
        pump(r, 8)
    check("chain lock: a later extender arm wraps ours once and no more",
          val(r, "EXT_N") == "2", val(r, "EXT_N"))
    check("chain lock: our wrapper is left where the extender put it",
          val(r, "FACE('answer')") != before and val(r, "FACE('open')") != before, "wrapped")
    first = val(r, "FACE('answer')")
    for _ in range(1, 40):
        r.execute("EXT()")
        pump(r, 1)
    check("chain lock: forty more ticks leave the same wrapper on top",
          val(r, "FACE('answer')") == first, val(r, "FACE('answer')"))
    check("chain lock: sixty arms make two extenders, not sixty",
          val(r, "EXT_N") == "2", val(r, "EXT_N"))
    check("chain lock: our rule still answers through the chain", r.eval("ANS(801)") is True
          and r.eval("ANS(999)") is False, "801=%s" % val(r, "ANS(801)"))
    check("chain lock: the extender rule still answers too", r.eval("ANS(777)") is True
          and r.eval("OPN(778)") is True, val(r, "ANS(777)"))
    check("chain lock: the depth stays the base plus two", val(r, "DEPTHMAX") == "3", val(r, "DEPTHMAX"))
    check("chain lock: the pass still runs once per refresh", int(val(r, "COUNT_CALLS")) > 0,
          val(r, "COUNT_CALLS"))


# --- 17: prison absent, then present ---------------------------------------------------------
def case_lock_late(lua51):
    r = rt(ZMFIX + "\nMAKEZM()")
    off(r)
    r.execute("REFRESH(0)")
    pump(r, 3)
    check("late lock: no table means nothing is wrapped", r.eval("ProgressionTuning.locks") is None,
          str(r.eval("ProgressionTuning.locks")))
    r.execute("PRISON()")
    check("late lock: the prison table is not wrapped before a tick", val(r, "FACE('answer') == SEC_A") == "True",
          val(r, "FACE('answer') == SEC_A"))
    pump(r, 1)
    check("late lock: the timer extends it on the next tick",
          val(r, "FACE('answer') == SEC_A") == "False", val(r, "FACE('answer') == SEC_A"))
    check("late lock: the rule answers once the table is there", r.eval("ANS(801)") is True,
          val(r, "ANS(801)"))
    r.execute("NOPRISON()")
    pump(r, 1)
    check("late lock: a missing table is survived", len(lines_of(r)) <= 3, "%d lines" % len(lines_of(r)))
    r.execute("PRISON()")
    pump(r, 1)
    check("late lock: a new table is extended again", r.eval("ANS(801)") is True
          and val(r, "FACE('answer') == SEC_A") == "False", val(r, "FACE('answer') == SEC_A"))


# --- 18: the press writes the research channel ------------------------------------------------
def case_channel(lua51):
    r = rt(ZMFIX + "\nMAKEZM()")
    off(r)
    r.execute("REFRESH(0)")
    check("channel: no press leaves the line empty", val(r, "CHV()") == "", val(r, "CHV()"))
    r.execute("PRESS(40001)")
    check("channel: a press writes the sat id", val(r, "CHV()") == "a=40001", val(r, "CHV()"))
    check("channel: one saved line names it",
          count_line(lines_of(r), "progression_tuning: augments research saved a=40001") == 1,
          " | ".join([ln for ln in lines_of(r) if "research saved" in ln][:2]))
    r.execute("REFRESH(0); REFRESH(0)")
    check("channel: later passes do not write again",
          val(r, "CHV()") == "a=40001" and count_line(lines_of(r), "augments research saved") == 1,
          "%d" % count_line(lines_of(r), "augments research saved"))
    r.execute("PRESS(48298)")
    check("channel: a carryover press keeps the sat id and says nothing new",
          val(r, "CHV()") == "a=40001" and count_line(lines_of(r), "augments research saved") == 1,
          val(r, "CHV()"))
    r.execute("PRESS(40002)")
    check("channel: the next press moves the line", val(r, "CHV()") == "a=40002"
          and count_line(lines_of(r), "augments research saved") == 2, val(r, "CHV()"))


# --- 19: a restart restores the research from the channel ------------------------------------
def case_restore(lua51):
    r = rt(ZMFIX + "\nMAKEZM()", "SET_DVAR('pt_research_ch', 'a=40001')")
    off(r)
    check("restore: 53979 answers the saved research", val(r, "LAST(53979)") == "40001",
          val(r, "LAST(53979)"))
    check("restore: 47576 answers it as well", val(r, "LAST(47576)") == "40001", val(r, "LAST(47576)"))
    check("restore: one restored line names it",
          count_line(lines_of(r), "progression_tuning: augments research restored a=40001") == 1,
          " | ".join([ln for ln in lines_of(r) if "restored" in ln][:2]))
    r.execute("REFRESH(0); REFRESH(0)")
    check("restore: said once over three passes",
          count_line(lines_of(r), "augments research restored") == 1,
          "%d" % count_line(lines_of(r), "augments research restored"))
    check("restore: the active research read returns that row", val(r, "GETACTIVE(0)") == "7001",
          val(r, "GETACTIVE(0)"))
    check("restore: the pick is not written back", count_line(lines_of(r), "research saved") == 0,
          "%d" % count_line(lines_of(r), "research saved"))


def case_restore_late(lua51):
    r = rt(ZMFIX + "\nMAKEZM()")
    off(r)
    pump(r, 1)
    check("late restore: an empty line says nothing", count_line(lines_of(r), "restored") == 0,
          "%d" % count_line(lines_of(r), "restored"))
    r.execute("SET_DVAR('pt_research_ch', 'a=40002')")
    pump(r, 8)
    check("late restore: a line that arrives is seeded on a tick", val(r, "LAST(53979)") == "40002",
          val(r, "LAST(53979)"))
    check("late restore: one line once", count_line(lines_of(r), "augments research restored") == 1,
          "%d" % count_line(lines_of(r), "augments research restored"))


# --- 20: the match vm raises one native card per tier crossing -------------------------------
def case_popup(lua51):
    r = rt(ZMFIX + "\nMAKEZM()", "FRONTEND = false")
    off(r)
    r.execute("SET_DVAR('pt_research_ch', 'a=40001')")
    r.execute("REFRESH(0)")
    check("popup: the first read is the baseline", val(r, "NAMED('ae_reward_granted')") == "0",
          val(r, "NAMED('ae_reward_granted')"))
    r.execute("REFRESH(0)")
    check("popup: the second read confirms the baseline",
          val(r, "NAMED('ae_reward_granted')") == "0", val(r, "NAMED('ae_reward_granted')"))
    r.execute("SET_PROG(40001, 70000)")
    r.execute("REFRESH(0)")
    check("popup: one tier crossing raises one card", val(r, "NAMED('ae_reward_granted')") == "1",
          val(r, "NAMED('ae_reward_granted')"))
    check("popup: the card names the kind the hud tests",
          val(r, "LASTOF('ae_reward_granted').kind") in ("437", "437.0"),
          val(r, "LASTOF('ae_reward_granted').kind"))
    check("popup: the card carries one loot id",
          val(r, "#LASTOF('ae_reward_granted').items") == "1", val(r, "#LASTOF('ae_reward_granted').items"))
    check("popup: the loot id is the one the active item publishes",
          val(r, "LASTOF('ae_reward_granted').items[1]") in ("107157", "107157.0"),
          val(r, "LASTOF('ae_reward_granted').items[1]"))
    check("popup: one line names the row and the tier",
          count_line(lines_of(r), "progression_tuning: augments tier id=40001 tier=1 sent=true") == 1,
          " | ".join([ln for ln in lines_of(r) if "augments tier" in ln][:2]))
    r.execute("REFRESH(0); REFRESH(0)")
    check("popup: the same tier does not card twice", val(r, "NAMED('ae_reward_granted')") == "1",
          val(r, "NAMED('ae_reward_granted')"))
    r.execute("SET_PROG(40001, 140000)")
    r.execute("REFRESH(0)")
    check("popup: the next tier raises the next card", val(r, "NAMED('ae_reward_granted')") == "2",
          val(r, "NAMED('ae_reward_granted')"))
    check("popup: the second line names tier two",
          count_line(lines_of(r), "augments tier id=40001 tier=2 sent=true") == 1,
          " | ".join([ln for ln in lines_of(r) if "augments tier" in ln][:2]))
    r.execute("SET_PROG(40001, 0)")
    r.execute("REFRESH(0); REFRESH(0)")
    r.execute("SET_PROG(40001, 70000)")
    r.execute("REFRESH(0)")
    check("popup: a lower read never replays a tier", val(r, "NAMED('ae_reward_granted')") == "2",
          val(r, "NAMED('ae_reward_granted')"))
    r2 = rt(ZMFIX + "\nMAKEZM()", "FRONTEND = false")
    off(r2)
    r2.execute("SET_DVAR('pt_research_ch', 'a=40001')")
    r2.execute("SET_PROG(40001, 140000)")
    r2.execute("REFRESH(0); REFRESH(0); REFRESH(0)")
    check("popup: a reload mid match cards nothing", val(r2, "NAMED('ae_reward_granted')") == "0",
          val(r2, "NAMED('ae_reward_granted')"))


def case_popup_multi(lua51):
    r = rt(ZMFIX + "\nMAKEZM()", "FRONTEND = false")
    off(r)
    r.execute("SET_DVAR('pt_research_ch', 'a=40002')")
    r.execute("REFRESH(0); REFRESH(0)")
    r.execute("SET_PROG(40002, 275000)")
    r.execute("REFRESH(0)")
    check("popup multi: three steps raise three cards",
          val(r, "NAMED('ae_reward_granted')") == "3", val(r, "NAMED('ae_reward_granted')"))
    check("popup multi: one line per tier",
          count_line(lines_of(r), "augments tier id=40002 tier=") == 3,
          "%d" % count_line(lines_of(r), "augments tier id=40002 tier="))


def case_popup_on(lua51):
    r = rt(ZMFIX + "\nMAKEZM()", "FRONTEND = false")
    r.execute("SET_DVAR('zm_unlock_augments', '0'); SET_DVAR('zm_unlock_all', '1')")
    r.execute("SET_DVAR('pt_research_ch', 'a=40001')")
    r.execute("SET_PROG(40001, 300000)")
    r.execute("REFRESH(0); REFRESH(0); REFRESH(0)")
    check("popup on: the switch raises no card", val(r, "NAMED('ae_reward_granted')") == "0",
          val(r, "NAMED('ae_reward_granted')"))
    check("popup on: and says no tier line", count_line(lines_of(r), "augments tier ") == 0,
          "%d" % count_line(lines_of(r), "augments tier "))
    r2 = rt(ZMFIX + "\nMAKEZM()")
    off(r2)
    r2.execute("SET_DVAR('pt_research_ch', 'a=40001')")
    r2.execute("REFRESH(0); REFRESH(0)")
    r2.execute("SET_PROG(40001, 70000)")
    r2.execute("REFRESH(0)")
    check("popup: the menu vm raises no card", val(r2, "NAMED('ae_reward_granted')") == "0",
          val(r2, "NAMED('ae_reward_granted')"))


def case_popup_match(lua51):
    r = rt(ZMFIX + "\nMAKEZM()", "FRONTEND = false")
    off(r)
    r.execute("REFRESH(0)")
    r.execute("PRESS(40001)")
    check("match: a press records the pick", val(r, "ProgressionTuning.aug.active") in ("40001", "40001.0"),
          val(r, "ProgressionTuning.aug.active"))
    check("match: the channel is not written", val(r, "CHV()") == "", val(r, "CHV()"))
    check("match: no saved line is said", count_line(lines_of(r), "research saved") == 0,
          "%d" % count_line(lines_of(r), "research saved"))
    check("match: 53979 still answers the pick", val(r, "LAST(53979)") == "40001",
          val(r, "LAST(53979)"))


def case_popup_late(lua51):
    r = rt(ZMFIX + "\nMAKEZM()", "FRONTEND = false\nDROPACTIVE()")
    off(r)
    r.execute("SET_DVAR('pt_research_ch', 'a=40001')")
    r.execute("REFRESH(0); REFRESH(0)")
    r.execute("SET_PROG(40001, 70000)")
    r.execute("REFRESH(0)")
    check("late popup: the card falls back to the row id",
          val(r, "LASTOF('ae_reward_granted').items[1]") in ("7001", "7001.0"),
          val(r, "LASTOF('ae_reward_granted').items[1]"))
    r.execute("PUTACTIVE()")
    r.execute("SET_PROG(40001, 140000)")
    r.execute("REFRESH(0)")
    check("late popup: the item is read once it is there",
          val(r, "LASTOF('ae_reward_granted').items[1]") in ("107157", "107157.0"),
          val(r, "LASTOF('ae_reward_granted').items[1]"))


def case_file():
    bad = []
    for i, ln in enumerate(SRC.split("\n"), 1):
        s = ln.strip()
        if "--" in s and not s.startswith("--"):
            bad.append("%d: not a line of its own" % i)
            continue
        if not s.startswith("--"):
            continue
        text = s[2:].strip()
        if not text or not re.match(r"^[a-z0-9_ ]+$", text) or len(text.split()) > 10:
            bad.append("%d: %s" % (i, text[:44]))
    check("file: every comment is lowercase, unpunctuted, ten words at most", bad == [], " | ".join(bad[:4]))
    low = SRC.lower()
    check("file: no comment or line names the client",
          "kronos" not in low and "client" not in low.split("local ")[0].replace("progression_tuning", ""),
          "kronos" if "kronos" in low else "none")
    check("file: no plain-name index of the augment table",
          ".augmentlist_full" not in SRC and '["augmentlist_full"]' not in SRC
          and ".augmentresearchchallenges=" not in SRC,
          "checked")
    check("file: ascii and lf only", b"\r" not in RAW and all(b < 128 for b in RAW), "%d B" % len(RAW))


def case_missing(lua51):
    r = lua51(unpack_returned_tuples=True)
    r.execute(PRELUDE)
    r.execute("FRONTEND = true")
    r.execute(SRC)
    pump(r, 2)
    check("bare: a vm with no augment table says nothing and raises nothing", len(lines_of(r)) == 0,
          " | ".join(lines_of(r)[:2]))
    r2 = lua51(unpack_returned_tuples=True)
    r2.execute(PRELUDE)
    r2.execute("FRONTEND = true")
    r2.execute("xhash = nil; xhashdvar = nil")
    r2.execute(SRC)
    pump(r2, 2)
    check("bare: no hash function means no attempt at all", len(lines_of(r2)) == 0, " | ".join(lines_of(r2)[:2]))


def main():
    LuaRuntime = lua51()
    info("replay: the augment part under a stubbed frontend vm")
    for case in (case_off, case_on, case_line, case_ticks, case_count, case_press, case_alias,
                 case_chain, case_plain, case_late, case_late_read, case_tick_pass, case_twice,
                 case_decoy, case_blind, case_research, case_lock, case_lock_chain, case_lock_late,
                 case_channel, case_restore, case_restore_late, case_popup, case_popup_multi,
                 case_popup_on, case_popup_match, case_popup_late, case_missing):
        info("case: " + case.__name__)
        try:
            case(LuaRuntime)
        except Exception as exc:
            check("case %s finishes" % case.__name__, False, repr(exc)[:200])
    try:
        case_file()
    except Exception as exc:
        check("the file rule runs", False, repr(exc)[:200])

    print("")
    import hashlib
    print("HASH  %s  %d B  %s" % (os.path.relpath(PART, PKG), len(RAW), hashlib.sha256(RAW).hexdigest().upper()[:16]))
    print("")
    print("%d passed, %d failed" % (len(passes), len(failures)))
    for name in failures:
        print("FAIL  " + name)
    print("augments: %d/%d" % (len(passes), len(failures)))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
