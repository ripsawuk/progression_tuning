"""progression-tuning - the offline replay for mod\\progression_tuning.

Two halves, both read-only. Nothing is installed, no game folder is written, nothing is launched.

  * static checks over mod.json and the Lua: LF, ASCII, every comment line inside the file rule
    (lower case, no punctuation, ten words at most), the manifest's own fields, one wrapper per getter,
    the embedded locksmith scope (4,203 ids, the generator's own SHA-256) kept as the fallback, the absence
    of every identifier the removed features used, and the absence of any script part;
  * a dry run of the Lua under a stubbed Kronos VM (Lua 5.1 via lupa) whose members are keyed by
    xhash, the way the client stores them (D47), whose Dvar answers by xhashdvar(name), and whose two
    contexts are the menu (Engine.InFrontend true) and a match (false).

The cases:

  1. the payload parses: two guns, a refused record, the DLL's `probe` marker and an absent payload;
  2. two guns alternate: each has its own ladder, its own level and its own banner;
  3. resume: a payload that is already at level 3 on the first sighting announces nothing;
  4. the banner fires at the exact rung - 999 is nothing, 1000 is one banner printing 2;
  5. the attachment card fires at the level that unlocks the item, and only that level's items;
  6. an absent payload draws nothing and prints exactly one line;
  7. the client's own record answers the payload's total, display only;
  8. the heartbeat, the game's notification switch, and pt_on off;
  9. the g11 reader: the header shape, the 33 parts, the bit lookup, add-only on both doors, the
     retired `all` scope, the debug unlock stand-down, pt_locks off, absent payload,
     a damaged payload, the publish-storm window, a late payload, the scan door and the give-up cap;
 10. LF, ASCII, and every comment line inside the file rule (lower case, no punctuation, ten words at
     most, one above each function or group); none of the removed features' identifiers appears. The reticle
     card and the special/mastery camo cards ship in this build (rc1-next5), so `reticle`, `reticleChallenges`,
     `mastery` and `GUNSMITH` are no longer on that list. Its remaining entries still ban the retired parallel
     implementations: the tracker, the nearest-to-completion walk, camo credit and the badge;
 11. the type filter (S1): an id answers locked when the bitmap holds its bit AND the client's own
     item type is attachment or camo - an attachment inside the shipped scope, an attachment outside
     it, and a camo all read locked; a weapon and a calling card keep the client's answer; an id with
     no bit is not even typed while the log is off; the type is cached per id; the door line is
     bounded per rebuild and silent when pt_log and pt_diag are off; pt_on off is a passthrough;
 12. the fallback: with gettypeforid absent, with itemTypes absent and with gettypeforid raising, the
     door answers exactly RC 1.0's bit AND scope, id for id, and says once which line it fell back to;
 13. the temporary S0/S1 diagnostic (`pt_diag`, one `rc1diag:` block per VM): silent when off, one bounded
     block when on, re-printable on a fresh on, absent natives reported instead of raised, no answer of
     any door changed by it, and - the load-bearing one - the source with the section cut out is the
     shipping body byte for byte;
 14. the ladder pick: the per-level cost list is not a candidate, a candidate must strictly rise, the pick
     must reproduce the client's own level or return nil, a nil pick is not kept, and the two measured
     cases (Flatline 440 -> nothing, 1,000 -> one banner; the 1911's `crossed 3 ... banner=4` unchanged);
 15. the camo map and the per-weapon list: an empty or pre-data build is not cached, the same VM locks once
     the data arrives with no rebuild, and the passthrough log is one summary line per rebuild;
 16. the tracker's list: the first entry per challenge id is kept and later repeats are dropped in place,
     the original is called with the same arguments and its answer returned, the other callers are
     untouched, and `pt_on 0` is a passthrough;
 17. the card queue: a group-1 splash holds the next card and a group-2 one never does, the read falling
     back to the native airtime when it raises, the cap releasing a stuck read, the route-B priority
     option, the order level then its unlock then camo then challenge, first in first out inside a
     kind, and the side panels: a `weaponProgression` and a `rankProgression` slot hold nothing, an
     unlock and an XP row go out in their centre card's own tick carrying the native 30 ms override and
     `immediate`, and a held slot still holds them with their card - measured in every one of the three
     load orders;
  18. the weekly card's look: a weekly crossing goes out on route B as the daily card type at the daily
     priority and airtime, its header the client's own title through the hash, the readable key and the
     value form in that order (our literal and one `none` line when none resolves), its subtitle the
     client's own description with no marked number, the shared subheader emptied when that subtitle is
     empty, one `weaponProgression` side card per reward the row pays in the same tick as the card (one
     line and nothing sent when the reward list is absent or empty), the sound alias the weekly and camo
     routes carry and the client's own table winning when this VM can reach it, the route-A level and
     daily calls unchanged, and the daily card path unchanged;
  19. the card instrument: sixty card lines then one cap line, and the sound line - one per level, daily,
     weekly and camo card carrying the sound the widget was handed, `none`, `absent` and `unread`, and
     twenty lines per VM then its own cap line;
  20. carry-forward (`docs\\CARRY-FORWARD-RECON.md` section 5): a `t10_`/`jup_`/`iw9_` ref is refused at the XP bind
      even when it has a CSV row, a foreign prestige bundle and a foreign camo band are left to the client, a
      weapon list past the old 600 stops truncating the camo map, a scope id with no type read cannot close on a
      carried ref, a bundle that answers no table is cached as a no, the camo watch and the camo bundles skip a
      carried ref without spending a try, the kind-398 gate and the attachment card refuse one, a row with no id
      is never fired, and - the control - with nothing carried the `sat_` gun's cards, levels and locks are
      exactly as they were.
      a carried id with a bit passes to the client
      an out of scope operator id passes to the client

The mod is eight `*_post.lua` parts (D96 split): main, weaponxp, splash, camos, challenges, prison,
reticles, diag. `load()` runs all eight in that fixed order; `SRC` is their concatenation and every
whole-mod check reads it. The diagnostic is quarantined in its own part: `shipping()` is the seven
parts that ship, because the diag part legitimately names the features the shipping code must not.
Everything else, including every static ban on IO, still scans all of it.

Run:  python -I tests\\test_progression_tuning.py
"""
import hashlib
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PKG = os.path.dirname(HERE)
MOD = os.path.join(PKG, "mod", "progression_tuning")
LUA_DIR = os.path.join(MOD, "lua")
MODJSON = os.path.join(MOD, "mod.json")
SCRIPTS_DIR = os.path.join(MOD, "scripts")
MAIN = "progression_tuning_main_post.lua"
WEAPONXP = "progression_tuning_weaponxp_post.lua"
SPLASH = "progression_tuning_splash_post.lua"
CAMOS = "progression_tuning_camos_post.lua"
CHALLENGES = "progression_tuning_challenges_post.lua"
PRISON = "progression_tuning_prison_post.lua"
RETICLES = "progression_tuning_reticles_post.lua"
DIAG = "progression_tuning_diag_post.lua"
LUA_FILES = [MAIN, WEAPONXP, SPLASH, CAMOS, CHALLENGES, PRISON, RETICLES, DIAG]
SHIP_FILES = [n for n in LUA_FILES if n != DIAG]
LOAD_ORDERS = {
    "harness": LUA_FILES,
    "alphabetical": sorted(LUA_FILES),
    "reversed": sorted(LUA_FILES, reverse=True),
}
LOAD_ORDER = "harness"

PARTS, HEXLEN, PARTLEN = 33, 65536, 2000
MAXID = 0x3FFFF
LS_COUNT = 4203
LS_SHA = "EC5C1479DE844E725AC0569A348B0349826783B1C0CC7598F0C949451A349581"
ACCEPT = [89575, 96171, 96192, 96202, 102671, 126597, 126619, 111457]
TOGGLES = ["pt_on", "pt_level", "pt_attach", "pt_camo", "pt_daily", "pt_log"]
REMOVED = [
    "RETIC", "badge", "Badge", "Mastery", "dedupe", "DEDUPE", "_DataSources", "NearestToCompletion",
    "TrackedChallenges", "setupweaponcamochallenges", "getcamochallengefromref", "GetCamoDataByLootID",
    "gettrackedchallengedata", "camo_credit",
    "getweaponprestigeattachmentquery", "weaponprestigeprogression",
    "getweaponprestigetokenscount", "ptsplash_c", "ptsplash_k", "ptsplash_xp",
    "ptsplash_u", "ptsplash_d", "ptsplash_m", "ptsplash_n", "ptsplash_v", "ptsplash_wxp", "zm_ch_",
    "XP_MODE", "weapon_xp_kill", "kill", "crit", "award", "parse_snapshot", "acc_for", "acc_now",
    "tier_at", "tier_in", "gsc", "progression_tuning_splash", "g14_splash",
    "g11_locks", "e3_armory", "g10_armory", "Armory", "armory",
]

passes, failures, infos = [], [], []


def check(name, cond, detail=""):
    if LOAD_ORDER != "harness":
        name = "%s [%s]" % (name, LOAD_ORDER)
    if cond:
        passes.append(name)
    else:
        failures.append((name, detail))
        print("FAIL  %s%s" % (name, ("  [" + detail + "]") if detail else ""))


def info(msg):
    infos.append(msg)
    print("info  %s" % msg)


PRELUDE = r"""
LOG = {}
function DebugPrint(s) LOG[#LOG + 1] = tostring(s) end
function LOGC() return table.concat(LOG, "\n") end

local function h32(s)
  local v = 5381
  for i = 1, #s do v = (v * 33 + string.byte(s, i)) % 4294967296 end
  return string.format("%08x", v)
end
function xhash(name) return "#x" .. h32("m:" .. string.lower(tostring(name))) end
function xhashdvar(name) return "#x" .. h32("d:" .. string.lower(tostring(name))) end

DVARS = {}
XINT = {}
DV_READS = 0
TORN = 0
NILMODE = false
NIL_NAMES = {}
function NO_DVARS() NILMODE = true end
function SET_NIL(name) NIL_NAMES[xhashdvar(name)] = true end
Dvar = {}
Dvar[xhash("GetDvarString")] = function(key)
  DV_READS = DV_READS + 1
  if TORN > 0 and DV_READS >= TORN then
    TORN = 0
    DVARS[xhashdvar("zm_g11_ver")] = "999:33:65536"
  end
  if NILMODE or NIL_NAMES[key] then return nil end
  local v = DVARS[key]
  if type(v) == "string" then return v end
  return ""
end
Dvar[xhash("GetDvarInt")] = function(key)
  local v = XINT[key]
  if type(v) == "number" then return v end
  return tonumber(DVARS[key])
end
function READS() return DV_READS end
function RESET_READS() DV_READS = 0 end

function SET_PAID(v) DVARS[xhashdvar("ptsplash_paid")] = v end
function SET_TOGGLE(name, v)
  if type(v) == "number" then XINT[xhashdvar(name)] = v else DVARS[xhashdvar(name)] = v end
end
function SET_DVAR(name, v) DVARS[xhashdvar(name)] = v end
function CLR_DVAR(name) DVARS[xhashdvar(name)] = nil; XINT[xhashdvar(name)] = nil end

Engine = {}
FRONTEND = false
Engine[xhash("InFrontend")] = function() return FRONTEND end
Engine[xhash("Localize")] = function(k)
  if k == nil then return "" end
  return "L:" .. tostring(k)
end

QUEUE = {}
ROOT = {}
function ROOT:addElement(el)
  el.parent = ROOT
  return el
end
local EL = {}
EL.__index = EL
function EL:getParent() return self.parent end
function EL:Wait(ms)
  local h = { ms = ms }
  QUEUE[#QUEUE + 1] = h
  return h
end
LUI = {}
LUI[xhash("GetRoot")] = function() return ROOT end
LUI[xhash("UIElement")] = { [xhash("new")] = function() return setmetatable({}, EL) end }

EVENTS = {}
LUI[xhash("UIRoot")] = { [xhash("ProcessEvent")] = function(root, ev)
  EVENTS[#EVENTS + 1] = ev
  return true
end }
function PUMP(n)
  local fired = 0
  for _ = 1, n do
    local h = table.remove(QUEUE, 1)
    if h == nil then break end
    fired = fired + 1
    if type(h.onComplete) == "function" then h.onComplete() end
  end
  return fired
end
function QUEUED() return #QUEUE end
function NEVENTS() return #EVENTS end
function EV(i) return EVENTS[i] end
function NAMED(n)
  local c = 0
  for i = 1, #EVENTS do
    if EVENTS[i].name == n then c = c + 1 end
  end
  return c
end
function CLEAR() EVENTS = {} end
function LASTOF(n)
  local found = nil
  for i = 1, #EVENTS do
    if EVENTS[i].name == n then found = EVENTS[i] end
  end
  return found
end

CSV = {}
CSV.weaponProgressionAchievements = { file = "wp",
  cols = { weaponRef = "weaponRef", weaponProgressionAchievementID = "weaponProgressionAchievementID",
           amount = "amount", loot = "loot" },
  [xhash("GetFile")] = function(t) return "wp" end }
CSV.gunsmithChallenges = { file = "gs", cols = { id = "id", ref = "ref", loot = "loot", amount = "amount" } }
CELLS = {}
ROWS = {}
StringTable = {}
StringTable[xhash("tablelookup")] = function(file, kc, kv, oc)
  return CELLS[tostring(file) .. "|" .. tostring(kc) .. "|" .. tostring(kv) .. "|" .. tostring(oc)]
end
StringTable[xhash("tablereadallrows")] = function(file)
  return ROWS[tostring(file)]
end
function CELL(file, kc, kv, oc, v)
  CELLS[tostring(file) .. "|" .. tostring(kc) .. "|" .. tostring(kv) .. "|" .. tostring(oc)] = v
end
function SET_GUN(ref, id)
  CELL("wp", "weaponRef", ref, "weaponProgressionAchievementID", tostring(id))
  ROWS["wp"] = ROWS["wp"] or {}
  ROWS["wp"][tostring(id)] = { weaponRef = ref }
  IDREF[tostring(id)] = ref
end

PCALLS = 0
LCALLS = 0
TYPECALLS = 0
OWNED = true
IDREF = {}
function SET_IDREF(id, ref) IDREF[tostring(id)] = ref end
PROGRESSION = {}
MINXP = {}
function SET_MINXP(ref, list)
  local t = {}
  local i = 1
  while i <= #list do t[i] = list[i]; i = i + 1 end
  MINXP[ref] = t
end
PROGRESSION[xhash("getweaponlevelminxp")] = function(c, ref, level)
  local t = MINXP[ref]
  if t == nil then return nil end
  return t[level]
end
LEVEL = {}
function SET_LEVEL(ref, n) LEVEL[ref] = n end
function PAIDTOTAL(ref)
  local txt = DVARS[xhashdvar("ptsplash_paid")]
  if type(txt) ~= "string" then return nil end
  for lid, tot in string.gmatch(txt, "(%d+):(%-?%d+):%-?%d+") do
    if LOOTREF[tostring(lid)] == ref then return tonumber(tot) end
  end
  return nil
end
function OCLVL(ref)
  if LEVEL[ref] ~= nil then return LEVEL[ref] end
  local t = MINXP[ref]
  if t == nil then return 0 end
  local tot = PAIDTOTAL(ref)
  if tot == nil then return 0 end
  local k = 0
  for i = 1, #t do
    if tot >= t[i] then k = i end
  end
  return k
end
PROGRESSION[xhash("GetWeaponLevel")] = function(c, ref)
  if LEVEL[ref] ~= nil then return LEVEL[ref] end
  local t = MINXP[ref]
  if t == nil then return nil end
  local tot = PAIDTOTAL(ref)
  if tot == nil then return nil end
  return OCLVL(ref)
end
MAXLVL = {}
function SET_MAXLEVEL(ref, n) MAXLVL[ref] = n end
PROGRESSION[xhash("getmaxweaponlevel")] = function(ref) return MAXLVL[ref] end
REWARD = {}
function SET_REWARD(ref, groups) REWARD[ref] = groups end
PROGRESSION[xhash("GetRewardUnlockedAtWeaponLevel")] = function(ref, level)
  local out = {}
  local g = REWARD[ref]
  if g == nil then return out end
  local list = g[level]
  if type(list) ~= "table" then return out end
  local i = 1
  while i <= #list do
    out[i] = { [xhash("lootid")] = list[i] }
    i = i + 1
  end
  return out
end
GATE = true
PROGRESSION[xhash("isweaponprogressionchallenge")] = function(kind, id) return GATE end
PROGRESSION[xhash("isunlockedwithid")] = function(c, id) PCALLS = PCALLS + 1; return OWNED end
PRESTIGE = {}
PREST = {}
function SET_PRESTIGE(ref, n) PREST[ref] = n end
PRESTIGE[xhash("getweaponprestigelevel")] = function(c, ref) return PREST[ref] or 0 end

LOOT = {}
LOOTREF = {}
function SET_LOOT_REF(loot, ref) LOOTREF[tostring(loot)] = ref end
LOOT[xhash("GetItemRef")] = function(id) return LOOTREF[tostring(id)] end
LOOT[xhash("getitemreffromid")] = function(id) return LOOTREF[tostring(id)] end
LOOT[xhash("gettypeforid")] = function(id) return 7 end
ITEMS = {}
function SET_ITEM_NAME(id, name) ITEMS[tostring(id)] = name end
LOOT[xhash("getitemnamebyid")] = function(id, mark)
  local n = ITEMS[tostring(id)]
  if n ~= nil then return n end
  return "ITEM " .. tostring(id)
end
LOOT[xhash("getitemimagebyid")] = function(id) return nil end
TYPES = {}
function SET_TYPE(id, t) TYPES[tostring(id)] = t end
function CLR_TYPES() TYPES = {} end
function DROP_TYPE_API() LOOT[xhash("gettypeforid")] = nil end
function DROP_TYPES() LOOT.itemTypes = nil end
function TYPE_RAISES()
  LOOT[xhash("gettypeforid")] = function(id) error("no type") end
end
LOOT[xhash("gettypeforid")] = function(id)
  TYPECALLS = TYPECALLS + 1
  local t = TYPES[tostring(id)]
  if t ~= nil then return t end
  return 7
end
LOOT.itemTypes = { ATTACHMENT = 7, CAMO = 13, WEAPON = 2, PLAYERCARD = 11 }
LOOT[xhash("isunlockedwithid")] = function(c, id) LCALLS = LCALLS + 1; return OWNED end

ATTACHMENT = {}
ATTACHMENT[xhash("getrefbyid")] = function(id) return "sat_acc_" .. tostring(id) end
BUNDLES = {}
function SET_BUNDLE(id, t) BUNDLES[tostring(id)] = t end
function PRESTIGE_BUNDLE(id, owner, name)
  BUNDLES[tostring(id)] = { [xhash("isprestige")] = true, [xhash("weaponunlock")] = owner,
                            [xhash("lootid")] = id }
end
function PLAIN_BUNDLE(id, owner)
  BUNDLES[tostring(id)] = { [xhash("isprestige")] = false, [xhash("weaponunlock")] = owner,
                            [xhash("lootid")] = id }
end
ATTACHMENT[xhash("getbundlebyid")] = function(id) return BUNDLES[tostring(id)] end
function DROP_BUNDLE_API() ATTACHMENT[xhash("getbundlebyid")] = nil end

Challenge = {}
NOTIF = false
Challenge[xhash("AreAchievementNotificationsOff")] = function() return NOTIF end
function SET_NOTIF(v) NOTIF = (v == 1 or v == true) end

OCR = 0
OCD = 0
OnlineChallenges = {}
OC = {}
function SET_OC(id, xp, rank) OC[tostring(id)] = { xp = xp, rank = rank } end
OnlineChallenges[xhash("getchallengeprogress")] = function(c, id)
  OCR = OCR + 1
  local r = OC[tostring(id)]
  if r == nil then return nil end
  local rank = r.rank
  local ref = IDREF[tostring(id)]
  if ref ~= nil then rank = OCLVL(ref) end
  return { progress = { xp = r.xp, default = r.xp, rank = rank } }
end
OnlineChallenges[xhash("getchallengedefaultprogress")] = function(c, id)
  OCD = OCD + 1
  local r = OC[tostring(id)]
  if r == nil then return nil end
  return r.xp
end
function OC_READ(id)
  local r = OnlineChallenges[xhash("getchallengeprogress")](0, id)
  if r == nil then return nil end
  return r.progress.xp, r.progress.rank
end
function OC_DEF(id) return OnlineChallenges[xhash("getchallengedefaultprogress")](0, id) end

WEAPON = {}
WD = {}
function SET_WD(ref, amounts, loots)
  local p = { [xhash("level")] = 0, [xhash("playerxp")] = 0 }
  local i = 1
  while i <= #amounts do
    local ul = {}
    local list = loots and loots[i]
    if type(list) == "table" then
      local j = 1
      while j <= #list do
        ul[j] = { [xhash("lootid")] = list[j] }
        j = j + 1
      end
    end
    p[i + 1] = { [xhash("level")] = i, [xhash("playerxp")] = amounts[i], [xhash("levelunlocks")] = ul }
    i = i + 1
  end
  WD[ref] = { [xhash("weaponProgression")] = p }
end
WEAPON[xhash("getweapondataforref")] = function(ref) return WD[ref] end
CAMODATA = {}
function SET_CAMODATA(id, ref) CAMODATA[tostring(id)] = { [xhash("weaponref")] = ref, ref = "camo_" .. tostring(id) } end
WEAPON[xhash("getcamodatabyid")] = function(id) return CAMODATA[tostring(id)] end
function DROP_CAMODATA_API() WEAPON[xhash("getcamodatabyid")] = nil end
PRESTIGE_REQ = {}
function SET_PREQ(ref, id, prestige) PRESTIGE_REQ[tostring(ref) .. "|" .. tostring(id)] = { prestige = prestige } end
WEAPON[xhash("getweaponprestigeattachmentdetails")] = function(ref, id)
  return PRESTIGE_REQ[tostring(ref) .. "|" .. tostring(id)]
end
function DROP_PREQ_API() WEAPON[xhash("getweaponprestigeattachmentdetails")] = nil end
function SET_PRESTIGE_CAMOS(fn) PRESTIGE[xhash("getweaponprestigecamos")] = fn end

PUMPS = 0
META = {}
function SET_META(id, sentinel) META[id] = { sentinel_id = sentinel } end
SLABS = {}
function SET_PARTS() for i = 0, 32 do DVARS[xhashdvar("zm_g11_" .. i)] = SLABS[i + 1] end end
function SET_G11(serial)
  SET_PARTS()
  DVARS[xhashdvar("zm_g11_arm")] = "g11"
  DVARS[xhashdvar("zm_g11_ver")] = tostring(serial) .. ":33:65536"
end
function SET_VER(v) DVARS[xhashdvar("zm_g11_ver")] = v end
function SET_PART(i, v) DVARS[xhashdvar("zm_g11_" .. i)] = v end
function SET_ARM(v) DVARS[xhashdvar("zm_g11_arm")] = v end
function CLEAR_G11()
  SET_ARM(nil)
  CLR_DVAR("zm_g11_ver")
  for i = 0, 32 do CLR_DVAR("zm_g11_" .. i) end
end
function SET_SCOPE(v) SET_DVAR("kronos_g11_scope", v) end
function CLEAR_SCOPE() CLR_DVAR("kronos_g11_scope") end
function TORN_NEXT(n) TORN = n end
function ASK_P(id) return PROGRESSION[xhash("isunlockedwithid")](0, id) end
function ASK_L(id) return LOOT[xhash("isunlockedwithid")](0, id) end
function G11(name)
  local s = rawget(_G, "ProgressionTuning")
  if type(s) ~= "table" or type(s.g11) ~= "table" then return nil end
  return s.g11[name]
end
"""

DIAGFIX = r"""
Engine[xhash("IsNetworkConnected")] = function() return true end
Engine[xhash("IsUserSignedInToDemonware")] = function(c) return true end
PROXY_LOOT = {}
PROXY_LOOT[xhash("IsOwned")] = function(c, id) return 1 end
STORE = { Bundles = {} }
STORE.Bundles[xhash("IsLootUseableOnCurrentPlatform")] = function(c, id) return true end
PROGRESSION[xhash("ShouldUnlockAll")] = function() return true end
PROGRESSION[xhash("getmaxweaponlevel")] = function(ref) return 55 end
PRESTIGE[xhash("getweaponprestigetokenscount")] = function(c, ref) return 0 end
PRESTIGE[xhash("getmaxweaponprestigelevel")] = function(ref) return 2 end
PRESTIGE[xhash("getweaponprestigecamos")] = function(ref)
  local a = { { startPrestige = 0, startLevel = 0, targetPrestige = 1, targetLevel = 55,
                camoBundle = { lootid = 107478 } } }
  local b = { { startPrestige = 2, startLevel = 1, targetPrestige = 2, targetLevel = 99,
                camoBundle = { lootid = 107467 } } }
  return a, b, {}
end
Loot = {}
Loot[xhash("IsOwned")] = function(c, sentinel) return 0 end
META = {}
function SET_META(id, sentinel) META[id] = { sentinel_id = sentinel } end
LOOT[xhash("getprogressionitemmetadata")] = function() return META end
LOOT[xhash("IsItemPermanentlyUnlocked")] = function(id, c) return false end
LOOT["#x7357FE84FAD7DD18"] = function(id, c) return false end
LOOT["#x9BFFEB098B954D5B"] = function(id, c) return false end
LOOT[xhash("isitemdefault")] = function(id) return false end
WEAPON_CAMO = {}
WEAPON_CAMO[xhash("getcamochallengefromlootid")] = function(c, id)
  return { id = 68970, ref = "sat_pi_alcor_camo_zm_base", progress = 81, amount = 100,
           normalizedProgress = 0.81, lootId = id }
end
WEAPON_CAMO[xhash("getweaponreffromchallengeref")] = function(ref) return "sat_pi_alcor" end
NearestToCompletionChallenges = {}
NearestToCompletionChallenges["#xC29622BB180395FF"] = function(c, key)
  local out = {}
  for i = 1, 14 do
    out[i] = { id = 68970, ref = "sat_pi_alcor_camo_zm_base", lootId = 68970, normalizedProgress = 0.81 }
  end
  return out
end
Game = {}
Game[xhash("GetActiveGameModeKey")] = function() return "zm" end
CSV.zmDailyChallenges = { file = "zmdaily", cols = { id = "id", ref = "ref", amount = "amount" },
  [xhash("GetFile")] = function(t) return "zmdaily" end }
CSV.aezmweeklychallenges = { file = "zmweekly", cols = { id = "id", ref = "ref", amount = "amount" },
  [xhash("GetFile")] = function(t) return "zmweekly" end }
ROWS["zmdaily"] = { ["60325"] = { id = "60325", ref = "sat_daily_zm_p3_misc", amount = "25" } }
ROWS["zmweekly"] = { ["60330"] = { id = "60330", ref = "sat_weekly_zm_s1w6", amount = "3" } }
SET_OC(60325, 19, 0)
SET_OC(60330, 52, 0)
SET_OC(68333, 2809, 2)
SET_META(126608, 104729)
SET_META(126615, 104730)
SET_MINXP("sat_pi_alcor", { 1000, 2200, 3400, 4600 })
SET_LEVEL("sat_pi_alcor", 2)
SET_PRESTIGE("sat_pi_alcor", 0)
SET_WD("sat_pi_alcor", { 2200, 3400, 4600 })
"""

SPLASHFIX = r"""
SPLASHNOW = "empty_splash_ref"
function SET_SPLASH(v) SPLASHNOW = v end
DataSources = { inGame = { MP = { splashes = {} } } }
DataSources.inGame.MP.splashes.currentSplash = { GetValue = function(self, c) return SPLASHNOW end }
LUI.SplashManager = { MessageType = {
  ChallengeComplete = { priority = 15, shouldOverride = false },
  DailyChallengeNotification = { priority = 15, shouldOverride = false },
  WeeklyChallengeSplashNotification = { priority = 10, shouldOverride = false },
  CamoChallenge = { priority = 5, shouldOverride = false },
  WeaponLevel = { priority = 28, shouldOverride = false },
  Medal = { priority = 5, shouldOverride = false } } }
LUI.SplashUtils = { HaveActiveSplashScreens = function(c)
  return SPLASHNOW ~= nil and SPLASHNOW ~= "empty_splash_ref" end }
LUI.HudManager = { GetInstance = function()
  return { activeHud = { splashManager = { messageQueue = { 1, 2 } } } } end }
"""

SCANKEY = """
local hx = string.sub(xhash("isunlockedwithid"), 3)
local first = (string.sub(hx, 1, 1) == "f") and "e" or "f"
local f = PROGRESSION[xhash("isunlockedwithid")]
PROGRESSION[xhash("isunlockedwithid")] = nil
PKEY = "#x" .. first .. string.sub(hx, 2)
PROGRESSION[PKEY] = f
function ASK_P(id) return PROGRESSION[PKEY](0, id) end
"""

SPLASHQ = r"""
SPLASHNOW = "empty_splash_ref"
DSRAISE = false
WM = {}
function SET_SPLASHNOW(v) SPLASHNOW = v end
function DS_THROW(v) DSRAISE = (v == true) end
function SET_WM(key, gid) WM[key] = { groupId = gid } end
DataSources = { inGame = { MP = { splashes = {} } } }
DataSources.inGame.MP.splashes.currentSplash = { GetValue = function(self, c)
  if DSRAISE then error("no current splash") end
  return SPLASHNOW end }
LUI.SplashUtils = { EmptySplashRef = "empty_splash_ref" }
LUI.SplashManager = { MessageType = {
  ChallengeComplete = { priority = 15 },
  DailyChallengeNotification = { priority = 15 },
  WeeklyChallengeSplashNotification = { priority = 10 },
  CamoChallenge = { priority = 5 },
  WeaponLevel = { priority = 28 },
  Medal = { priority = 5 } } }
LUI.HudManager = { GetInstance = function()
  return { activeHud = { splashManager = { widgetMap = WM } } } end }
"""

FIXTURE = r"""
SET_GUN("sat_pi_atlas", 54499)
SET_GUN("sat_sh_shepherd", 59756)
SET_LOOT_REF(88929, "sat_pi_atlas")
SET_LOOT_REF(102705, "sat_sh_shepherd")
SET_MINXP("sat_pi_atlas", { 1000, 2200, 3400, 4600 })
SET_MINXP("sat_sh_shepherd", { 500, 1500 })
SET_REWARD("sat_pi_atlas", { [1] = { 88649 }, [2] = { 88614 }, [3] = { 97706, 97707 } })
SET_REWARD("sat_sh_shepherd", { [1] = { 119621 } })
SET_ITEM_NAME(88649, "Beadline Tactical Pad")
SET_ITEM_NAME(88614, "Bowen Pixel Reflex")
SET_ITEM_NAME(97706, "Bowen Pixel Reflex")
SET_ITEM_NAME(97707, "Bowen Pixel Reflex")
SET_ITEM_NAME(119621, "Shepherd Grip")
SET_OC(54499, 0, 0)
SET_OC(59756, 0, 0)
"""

LUA_TEXT = {n: open(os.path.join(LUA_DIR, n), "rb").read().decode("ascii") for n in LUA_FILES}
SRC = "".join(LUA_TEXT[n] for n in LUA_FILES)

DIAG_START = 'local RC1D = "rc1diag"'
DIAG_END = "local RC1D_END = true"
SHIP_LUA_LEN = 159729
SHIP_LUA_SHA = "2A989E66CDEDBB05B1B29F820B301C8CCFC1E86F2E85406D63A77209D707A010"
LITERAL_SHA = "4AB72DCB79F2DA35B1FFAFDFC162FAF517B94E197D1E4AAF437CD37A6650C108"
LITERAL_REMOVED = [
    " ah=",
    " err=",
    " gi=",
    " isp=",
    " len=",
    " playing=",
    "GetSoundLengthMS",
    "IsSoundPlaying",
    "PlaySound",
    "sndprobe alias=",
    "sndprobe: no PlaySound in this vm",
    "sndprobe: raised alias=",
    "sndvm ps=",
    "ui_select_confirm",
    "uin_jup_challenge_multikills",
    "uin_jup_master_challenge_complete",
    "uin_jup_master_challenge_complete_music",
    "uin_loadout_hilite",
]
LITERAL_ADDED = [
    " - not one of ours, so no row is read for it",
    " - the camo map is truncated and",
    " belongs to ",
    " computed and it keeps the client's own answer",
    " is ",
    " is ",
    " is a prestige reward for ",
    " is not one of ours - not bound",
    " left as the client answers it",
    " mwcf=",
    " names ",
    " not kept",
    "#x37dc362a78cf1d3d3",
    "A",
    "B",
    "ChallengeComplete",
    "CamoChallenge",
    "DailyChallengeNotification",
    "DataSources",
    "EmptySplashRef",
    "GetValue",
    "HaveActiveSplashScreens",
    "HudManager",
    "MP",
    "Medal",
    "MessageType",
    "SplashManager",
    "SplashTrapSubheader",
    "SplashUtils",
    "WEEKLY CHALLENGE COMPLETE",
    "WeeklyChallengeSplashNotification",
    "WeaponLevel",
    "a",
    "acarry:",
    "b",
    "c",
    "camo bundles ",
    "camo:extra:",
    "camo:watch:",
    "camoA",
    "camoB",
    "camos",
    ": cards capped at ",
    "carried:",
    "carry-forward: pack=unknown dvar=",
    "chalD",
    "chalWB",
    "challenges",
    "challenge/jup_ch_weekly_challenge_completed",
    "core absent - no part ",
    "currentSplash",
    "dailyNotification",
    "diag",
    "empty_splash_ref",
    "foreign ref",
    "gcamo:carried:",
    "getdesclocalizedbyid",
    "getrewards",
    "glock:carried:",
    "groupId",
    " head=",
    "inGame",
    "iw9",
    "iw9_",
    "jup",
    "jup_",
    "kronos_cfwd",
    "matchobjectivetext",
    "mwcf_box_pools",
    " names ",
    " none",
    "nosplash",
    "part main armed ",
    "prestige lock: the weapon list is longer than ",
    "prison",
    "progression_tuning: part camos armed",
    "progression_tuning: part challenges armed",
    "progression_tuning: part diag armed",
    "progression_tuning: part prison armed",
    "progression_tuning: part reticles armed",
    "progression_tuning: part splash armed",
    "progression_tuning: part weaponxp armed",
    "ret",
    "reticles",
    " route=",
    " route=B",
    "sat",
    "sat_",
    "setText",
    "shouldOverride",
    "splash",
    "splash absent - no card is drawn",
    "splashck",
    "splashes",
    "splashes/daily_challenge_completed",
    "t10",
    "t10_",
    "weaponxp",
    "weaponProgression",
    "weekly body=",
    "weekly body=empty",
    "weekly card id=",
    "weekly header native=",
    "weekly header=none",
    "weekly xp id=",
    "widget",
    "widgetMap",
    "^#x%x+$",
    "^%x+$",
    "0x%x%x%x%x%x%x%x%x",
    "0x7dc362a78cf1d3d3",
    " aliases=",
    " opacity=",
    " side card refused",
    " sound=",
    ": snd ",
    ": snd capped at ",
    "GetMilliseconds",
    "SOUND_SETS",
    "_DataSources",
    "challengeComplete",
    "challengeSplash",
    "displayLocation",
    "err:side",
    "error side card: ",
    "gamer_profile",
    "generalChallenge",
    "insertTime",
    "notification_feed_opacity",
    "options",
    "settings",
    "sound",
    "uin_jup_challenge_camo_unlock",
    "uin_jup_challenge_complete",
    "unread",
    "weaponLevel",
    "diag off",
    "pt_diag_off",
]
LITERAL_RE = re.compile('"([^"\\n]*)"' + "|'([^'\\n]*)'")


def load(rt):
    """Run the eight parts in the order the active replay mode names."""
    for name in LOAD_ORDERS[LOAD_ORDER]:
        rt.execute(LUA_TEXT[name])


def where(needle):
    """The parts that carry a needle."""
    return [n for n in LUA_FILES if needle in LUA_TEXT[n]]


def literals(text):
    """Every quoted string literal, comments left out."""
    body = "".join(ln for ln in text.split("\n") if not ln.strip().startswith("--"))
    out = set()
    for m in LITERAL_RE.finditer(body):
        out.add(m.group(1) if m.group(1) is not None else m.group(2))
    return out


def diag_span():
    """(lines, start, end) of the quarantined diagnostic section, or (lines, None, None)."""
    lines = LUA_TEXT[DIAG].split("\n")
    start = end = None
    for i, ln in enumerate(lines):
        if start is None and ln.startswith(DIAG_START):
            start = i
        elif start is not None and ln.strip() == DIAG_END:
            end = i
            break
    return lines, start, end


def shipping():
    """The seven parts that ship - everything except the quarantined diagnostic."""
    return "".join(LUA_TEXT[n] for n in SHIP_FILES)



def bitmap_of(ids):
    bm = bytearray(32768)
    for i in ids:
        if 1 <= i <= MAXID:
            bm[i >> 3] |= 1 << (i & 7)
    return bytes(bm)


def slabs_of(ids):
    h = bitmap_of(ids).hex()
    return [h[i:i + PARTLEN] for i in range(0, len(h), PARTLEN)]


def lua_slabs(rt, slabs):
    rt.execute("SLABS = {" + ",".join('"%s"' % s for s in slabs) + "}")
    rt.execute("SET_PARTS()")


def new_rt(lua51, frontend=False, pre="", fixture=True, log=True, src=True):
    rt = lua51(unpack_returned_tuples=True)
    rt.execute(PRELUDE)
    rt.execute("FRONTEND = %s" % ("true" if frontend else "false"))
    if fixture:
        rt.execute(FIXTURE)
    if log:
        pre = "SET_TOGGLE('pt_log', 1) " + pre
    if pre:
        rt.execute(pre)
    if src:
        load(rt)
    return rt


def lines_of(rt):
    text = str(rt.eval("LOGC()"))
    return [ln for ln in text.split("\n") if ln]


def has_line(lines, needle):
    return any(needle in ln for ln in lines)


def count_line(lines, needle):
    return sum(1 for ln in lines if needle in ln)


def pump(rt, n):
    return rt.eval("PUMP(%d)" % n)


COMMENT_RULE = re.compile(r"^[a-z0-9_ ]+$")
COMMENT_WORDS = 10
COMMENT_MIN = 30
# user kept these lines verbatim
COMMENT_KEEP = frozenset([
    (MAIN, "a g11 (testing shit) dvar by hashed name"),
    (MAIN, "which TABLES carry our door fam"),
    (MAIN, "the tables still missing our fucking DOOR"),
    (SPLASH, "elephants love to SPLASH water. This is for popups"),
    (SPLASH, "one card per gap, worst first"),
    (SPLASH, "draws the games own level up banner (woo congrats)"),
    (PRISON, "this shit is for locking other shit, for progression yanno"),
    (RETICLES, "i love yanking and eating the reticles off my gun tbh"),
])


def src_owner(i):
    """The part that SRC line i, counting from one, comes from."""
    end = 0
    for name in LUA_FILES:
        end += LUA_TEXT[name].count("\n")
        if i <= end:
            return name
    return None


def bad_comments():
    """Every comment line, held to the file rule: lower case, no punctuation, ten words at most."""
    bad = []
    for i, ln in enumerate(SRC.split("\n"), 1):
        s = ln.strip()
        if "--" in s and not s.startswith("--"):
            bad.append("%d: not a line of its own" % i)
            continue
        if not s.startswith("--"):
            continue
        text = s[2:].strip()
        if (src_owner(i), text) in COMMENT_KEEP:
            continue
        if not text or not COMMENT_RULE.match(text) or len(text.split()) > COMMENT_WORDS:
            bad.append("%d: %s" % (i, text[:44]))
    return bad


def static_checks():
    raw_parts = {n: open(os.path.join(LUA_DIR, n), "rb").read() for n in LUA_FILES}
    mod = json.load(open(MODJSON, encoding="utf-8"))

    check("mod.json: name", mod["name"] == "Progression Tuning", mod.get("name"))
    check("mod.json: author", mod["author"] == "ripsawuk", mod.get("author"))
    check("mod.json: version 1.0", mod["version"] == "1.0", mod.get("version"))
    check("mod.json: type names the ui and the script", mod["type"] == "ui,script", mod.get("type"))
    check("mod.json: requires is empty", mod["requires"] == [])
    check("mod.json: the keys are the installed mods' six, in order",
          list(mod.keys()) == ["name", "author", "version", "type", "requires", "description"],
          ", ".join(mod.keys()))
    check("mod.json: the description is the one it carries",
          mod["description"] == "Progression tuning mod for Kronos client (v1.41+ compatible) aiming to "
                                "restore original game functionality related to progression.",
          mod.get("description", "")[:120])
    check("mod.json: the description names no removed feature",
          not any(k.lower() in mod["description"].lower()
                  for k in ("reticle", "badge", "mastery", "dedupe", "armory")),
          mod.get("description", ""))

    check("lua: LF with no BOM", all(b"\r" not in v and not v.startswith(b"\xef\xbb\xbf")
                                     for v in raw_parts.values()),
          ", ".join(n for n, v in raw_parts.items() if b"\r" in v))
    check("lua: ASCII", all(b < 128 for v in raw_parts.values() for b in v))
    bad = bad_comments()
    ncom = sum(1 for ln in SRC.split("\n") if ln.strip().startswith("--"))
    check("lua: every comment line is one lower-case line of ten words at most",
          not bad and ncom >= COMMENT_MIN and "/*" not in SRC,
          ", ".join(bad[:6]) or "%d comment lines" % ncom)
    check("lua: no trailing whitespace", not any(ln != ln.rstrip() for ln in SRC.split("\n")))
    check("lua: ends with one LF", all(v.endswith(b"\n") and not v.endswith(b"\n\n")
                                       for v in raw_parts.values()),
          ", ".join(n for n, v in raw_parts.items() if not v.endswith(b"\n")))

    ship = shipping()
    lines, dstart, dend = diag_span()
    check("diag: the temporary section is one contiguous span with its own end marker",
          dstart is not None and dend > dstart,
          "start=%s end=%s" % (dstart, dend))
    check("diag: everything outside the section is the shipping body byte for byte",
          len(ship.encode()) == SHIP_LUA_LEN
          and hashlib.sha256(ship.encode()).hexdigest().upper() == SHIP_LUA_SHA,
          "%d B" % len(ship.encode()))
    outside = [n for n in SHIP_FILES if "rc1diag" in LUA_TEXT[n]]
    check("diag: the section is one part of its own, and no other part names it",
          outside == [], " | ".join(outside))
    body = lines[dstart:dend + 1] if dstart is not None and dend is not None else []
    dbody = "\n".join(body)
    check("diag: it installs no wrapper, writes no dvar, opens no file",
          not any(("T[k]" in ln or "SetDvar" in ln or "io." in ln or "os." in ln) for ln in body))
    check("diag: no diag code assigns an engine or a lui member",
          not re.search(r"(?<![A-Za-z0-9_])en\s*\[", dbody)
          and not re.search(r"\b(?:Engine|LUI)\s*\.\s*\w+\s*=(?!=)", dbody)
          and not re.search(r"\b(?:Engine|LUI)\s*\[[^\]]*\]\s*=(?!=)", dbody)
          and 'member(en, "PlaySound")' not in SRC and "return f(a, ...)" not in SRC
          and "sp_rec" not in SRC and "SP_REC" not in SRC,
          " | ".join(ln.strip() for ln in body if "Engine" in ln or "en[" in ln)[:200])
    check("diag: it is bounded and it can be deleted by line span",
          "local RC1D_CAP = " in SRC and "local RC1D_ENTRIES = 12" in SRC
          and 'RC1D .. ": end (' in SRC and '"rc1diag"' in SRC)
    check("diag: it reads its switch the way pt_log is read, default off",
          'toggle("pt_diag", false)' in SRC and 'toggle("pt_log", false)' in SRC)
    check("diag: the card line is one bounded line and only the diag part names it",
          "local CK_CARD_CAP = 60" in SRC and "if CK_CARDS >= CK_CARD_CAP then" in SRC
          and '": cards capped at "' in SRC and "S.hooks.card = ck_card" in SRC
          and "splashck" not in ship and "ck_card" not in ship and "CK_CARD" not in ship)
    check("lua: the splash part paces on the main part's own timer step",
          "local TICK_MS = 250" in LUA_TEXT[SPLASH] and "local TICK_MS = 250" in LUA_TEXT[MAIN])
    check("lua: the weekly subtitle is one plain line - the number is never marked",
          "MarkLocalized" not in SRC and '"getDesc"' in LUA_TEXT[SPLASH]
          and 'displayLocation = "dailyNotification"' in LUA_TEXT[SPLASH])
    check("order: the alphabetical replay is the order the client arms the parts in",
          [n[len("progression_tuning_"):-len("_post.lua")] for n in LOAD_ORDERS["alphabetical"]]
          == ["camos", "challenges", "diag", "main", "prison", "reticles", "splash", "weaponxp"],
          " | ".join(LOAD_ORDERS["alphabetical"]))
    check("order: the harness order is a fourth, different order",
          LOAD_ORDERS["harness"] != LOAD_ORDERS["alphabetical"]
          and LOAD_ORDERS["harness"] != LOAD_ORDERS["reversed"]
          and len(set(tuple(v) for v in LOAD_ORDERS.values())) == 3)

    found = [k for k in REMOVED if k in ship]
    have = literals(SRC)
    gone = sorted(set(LITERAL_REMOVED) & have)
    dig = hashlib.sha256(("\n".join(sorted(have)) + "\n").encode()).hexdigest().upper()
    arm = [n for n in LUA_FILES if ("part " + n[len("progression_tuning_"):-len("_post.lua")] + " armed")
           not in LUA_TEXT[n]]
    check("lua: none of the removed identifiers appears, the literal set is the split's own, and every part arms",
          not found and not gone and dig == LITERAL_SHA and set(LITERAL_ADDED) <= have and arm == [],
          ", ".join(found + gone + arm) or "%d literals %s" % (len(have), dig[:16]))

    for token, why in (("SetDvar", "writes a dvar"), ("io.", "file IO"), ("os.", "OS calls"),
                       ("dofile", "runs a file"), ("loadfile", "loads a file"),
                       ("loadstring", "compiles a string"), ("require", "loads a module"),
                       ("debug.", "debug library")):
        check("lua: no %r (%s)" % (token, why), token not in SRC)

    check("lua: one ownership door, one name - isunlockedwithid appears once",
          ship.count('"isunlockedwithid"') == 1 and where('"isunlockedwithid"') == [MAIN],
          "%d in %s" % (ship.count('"isunlockedwithid"'), where('"isunlockedwithid"')))
    check("lua: one wrapper per getter - the ownership door, the value door, the token id reader",
          SRC.count("T[k] = w") == 1 and SRC.count("lo[k] = w") == 1
          and SRC.count("pre[k] = w") == 1
          and where("T[k] = w") == [MAIN] and where("lo[k] = w") == [PRISON]
          and where("pre[k] = w") == [PRISON],
          "%d / %d / %d in %s" % (SRC.count("T[k] = w"), SRC.count("lo[k] = w"),
                                  SRC.count("pre[k] = w"),
                                  "/".join(where("T[k] = w") + where("lo[k] = w") + where("pre[k] = w"))))
    check("lua: the prestige rules are one function each, and only the one door calls them",
          "local function gattach(n)" in SRC and "local function gcamo(n)" in SRC
          and SRC.count("if gattach(n) then return true end") == 1
          and SRC.count("if gcamo(n) then return true end") == 1)
    check("lua: the door reads the client's own item type on every ask, because a prestige reward has no bit",
          "local t = gtype(n)" in SRC and "if bit == 1 or glogging() then" not in SRC)
    check("lua: the value door is keyed by the client's own metadata and its own token accessor",
          "local function gvalinstall()" in SRC and '"getprogressionitemmetadata"' in SRC
          and '"getweaponprestigetokenlootid"' in SRC
          and "if gsent()[n] == true then ans = 0" in SRC
          and "elseif GTOK ~= nil and GTOK[n] == true then ans = 0 end" in SRC
          and "      v = f(c, id, ...)" in SRC)
    check("lua: the prestige caches are cleared on the same rebuild as the bitmap",
          "G.bundles, G.camoref, G.pcamo, G.psaid, G.psaidN = {}, {}, {}, {}, 0" in SRC)
    check("lua: no new timer and no new dispatcher",
          SRC.count(":Wait(") == 2 and "CreateEventTimer" not in SRC
          and where(":Wait(") == [MAIN] and SRC.count("local function fire(") == 1
          and where("local function fire(") == [SPLASH]
          and SRC.count("ProcessEvent") == LUA_TEXT[SPLASH].count("ProcessEvent"),
          "%d waits in %s, %d fire, %d ProcessEvent" % (
              SRC.count(":Wait("), "/".join(where(":Wait(")), SRC.count("local function fire("),
              SRC.count("ProcessEvent")))
    check("lua: the wrapper is add-only - a raised call falls through",
          "if ok and answer then return false end" in SRC and "return o(c, id, ...)" in SRC)
    check("lua: the display half answers each record getter exactly once",
          ship.count('"getchallengeprogress"') == 2 and ship.count('"getchallengedefaultprogress"') == 2
          and SRC.count('wrap_member(OC, "getchallengeprogress",') == 1
          and where('wrap_member(OC, "getchallengeprogress",') == [WEAPONXP]
          and SRC.count('wrap_member(OC, "getchallengedefaultprogress",') == 1
          and where('wrap_member(OC, "getchallengedefaultprogress",') == [WEAPONXP],
          "%d / %d, wrapped in %s" % (ship.count('"getchallengeprogress"'),
                                      ship.count('"getchallengedefaultprogress"'),
                                      "/".join(where('wrap_member(OC, "getchallengeprogress",'))))

    check("lua: reads Dvar.GetDvarString by name", '"GetDvarString"' in SRC)
    check("lua: names the arm/ver/scope dvars as the hook spells them",
          all('"%s"' % n in SRC for n in ("zm_g11_arm", "zm_g11_ver", "kronos_g11_scope")))
    check("lua: builds the 33 part names with the hook's zm_g11_<i>",
          '"zm_g11_%d"' in SRC and "for i = 0, 32" in SRC)
    check("lua: checks the header shape <serial>:33:65536",
          '"^(%d+):(%d+):(%d+)$"' in SRC and "GPARTS" in SRC and "GHEXLEN" in SRC)
    check("lua: refuses a payload whose length is not 65,536",
          "local GHEXLEN = 65536" in SRC and "refused, keeping the previous payload" in SRC)
    check("lua: the answer needs the bit AND the client's own item type",
          "glockedNow(n)" in SRC and "GTYPE_A" in SRC and "GTYPE_C" in SRC
          and "local locked = (bit == 1 and (t == GTYPE_A or t == GTYPE_C) and not gcarried(n))" in SRC)
    check("lua: a locked answer is refused when the id's own ref is carried",
          "local function gcarried(n)" in SRC and SRC.count("not gcarried(n)") == 1)
    check("lua: types come from the client's own constants and its own getter",
          '"gettypeforid"' in SRC and '"itemTypes"' in SRC and '"ATTACHMENT"' in SRC
          and '"CAMO"' in SRC and "GTYPE_A, GTYPE_C = na, nc" in SRC)
    check("lua: the type is cached per id",
          "G.typecache[n] = t" in SRC and "local c = G.typecache[n]" in SRC)
    check("lua: a missing type answers from the shipped scope, never from everything",
          "if bit == 1 and GLOCKSMITH[n] == true then return true end" in SRC
          and "answering from the " in SRC and "scope instead of the item type" in SRC)
    check("lua: the scope is read on every refresh, before the serial check",
          SRC.index("greadScope()", SRC.index("local function grefresh()"))
          < SRC.index("if v == G.ver", SRC.index("local function grefresh()")))
    check("lua: the debug unlock toggles win over every lock this file adds",
          "if G.unlock ~= nil then return false end" in SRC)

    m = re.search(r"local GUNLOCK = \{([^}]*)\}", SRC)
    named = re.findall(r'"([^"]+)"', m.group(1)) if m else []
    check("lua: the two toggles that can reach the scope are named, not hashed",
          named == ["zm_unlock_all", "zm_unlock_attachments"], ", ".join(named))

    start = SRC.index("local GCSV = [[")
    body = SRC[start + len("local GCSV = [["):]
    body = body[:body.index("]]")]
    ids = [int(x) for x in body.split()]
    check("lua: the locksmith scope is the recorded %d ids" % LS_COUNT, len(ids) == LS_COUNT, str(len(ids)))
    check("lua: the scope carries each id once, sorted", ids == sorted(ids) and len(set(ids)) == len(ids))
    check("lua: every scope id is inside the client's bitmap domain", 1 <= min(ids) and max(ids) <= MAXID,
          "%d..%d" % (min(ids), max(ids)))
    digest = hashlib.sha256(("\n".join(str(i) for i in ids) + "\n").encode()).hexdigest().upper()
    check("lua: the scope is the generator's own set (its SHA-256)", digest == LS_SHA, digest)
    check("lua: all eight acceptance ids are in the scope", all(i in set(ids) for i in ACCEPT))

    left = sorted(n for n in (os.listdir(SCRIPTS_DIR) if os.path.isdir(SCRIPTS_DIR) else [])
                  if n.lower().endswith((".gsc", ".gscc")))
    check("gsc: the mod ships no script part - the folder is absent or empty",
          left == [], ", ".join(left))

    info("lua %d B sha256 %s" % (len(SRC.encode()), hashlib.sha256(SRC.encode()).hexdigest().upper()))
    info("mod.json %d B" % os.path.getsize(MODJSON))


def payload_cases(lua51):
    rt = new_rt(lua51, pre='SET_PAID("v1;88929:1200:1200;102705:300:300")')
    pump(rt, 2)
    lines = lines_of(rt)
    check("payload: two guns are read", has_line(lines, "paid source dll - ptsplash_paid carries 2 gun(s)"),
          " | ".join(lines[:6]))
    check("payload: gun A primes at the level its total reaches",
          has_line(lines, "prime sat_pi_atlas lv=1 total=1200"))
    check("payload: gun B primes on its own ladder",
          has_line(lines, "prime sat_sh_shepherd lv=0 total=300"))

    rt2 = new_rt(lua51, pre='SET_PAID("v1;88929:12x:1;102705:300")')
    pump(rt2, 2)
    l2 = lines_of(rt2)
    check("payload: a refused record is reported and draws nothing",
          has_line(l2, "record(s) refused") or has_line(l2, "paid source empty"), " | ".join(l2))
    check("payload: a payload with no usable gun draws nothing", rt2.eval("NEVENTS()") == 0)

    rt3 = new_rt(lua51, pre='SET_PAID("probe")')
    pump(rt3, 2)
    check("payload: the DLL's probe marker is a state of its own", has_line(lines_of(rt3), "paid source probe"))
    check("payload: the probe marker draws nothing", rt3.eval("NEVENTS()") == 0)

    rt4 = new_rt(lua51, pre='SET_PAID("v1")')
    pump(rt4, 2)
    check("payload: a bare v1 with no record is empty, not ignored", has_line(lines_of(rt4), "paid source empty"))
    check("payload: an empty payload draws nothing", rt4.eval("NEVENTS()") == 0)


def two_guns(lua51):
    rt = new_rt(lua51, pre='SET_PAID("v1;88929:900:900")')
    pump(rt, 2)
    lines = lines_of(rt)
    check("two guns: the first sighting primes 0", has_line(lines, "prime sat_pi_atlas lv=0 total=900"))
    check("two guns: nothing is drawn at the prime", rt.eval("NEVENTS()") == 0)

    rt.execute('SET_PAID("v1;88929:1050:1050;102705:600:600")')
    pump(rt, 8)
    l = lines_of(rt)
    check("two guns: A crosses to level 1", has_line(l, "sat_pi_atlas crossed 1 row 54499"), " | ".join(l[-6:]))
    check("two guns: B primes at level 1 on its own ladder",
          has_line(l, "prime sat_sh_shepherd lv=1 total=600"))
    check("two guns: one banner for A", rt.eval("NAMED('completed_challenge')") == 1,
          str(rt.eval("NAMED('completed_challenge')")))

    rt.execute("CLEAR()")
    rt.execute('SET_PAID("v1;88929:1050:1050;102705:1600:1600")')
    pump(rt, 8)
    l2 = lines_of(rt)
    check("two guns: B crosses to 2 and only B",
          has_line(l2, "sat_sh_shepherd crossed 2 row 59756") and rt.eval("NAMED('completed_challenge')") == 1,
          " | ".join(l2[-6:]))
    check("two guns: A stays where it was", not has_line(l2, "sat_pi_atlas crossed 2"))


def resume(lua51):
    rt = new_rt(lua51, pre='SET_PAID("v1;88929:3400:3400")')
    pump(rt, 3)
    lines = lines_of(rt)
    check("resume: the profile's own level is primed from the total",
          has_line(lines, "prime sat_pi_atlas lv=3 total=3400"), " | ".join(lines[:6]))
    check("resume: nothing is replayed", rt.eval("NEVENTS()") == 0)

    rt.execute('SET_PAID("v1;88929:4600:4600")')
    pump(rt, 3)
    l = lines_of(rt)
    check("resume: the next crossing fires once", rt.eval("NAMED('completed_challenge')") == 1,
          str(rt.eval("NAMED('completed_challenge')")))
    check("resume: the banner prints the level's own number",
          has_line(l, "sat_pi_atlas crossed 4 row 54499 rank=4 banner=5"), " | ".join(l[-5:]))
    n = rt.eval("NEVENTS()")
    check("resume: the payload is the game's own completed_challenge",
          rt.eval("EV(%d).name" % n) == "completed_challenge"
          and int(rt.eval("EV(%d).kind" % n)) == 398)
    check("resume: the banner carries the gun's prestige",
          int(rt.eval("EV(%d).progress.prestige" % n)) == 0)


def crossing(lua51):
    rt = new_rt(lua51, pre='SET_PAID("v1;88929:999:999")')
    pump(rt, 3)
    check("crossing: 999 is level 0", has_line(lines_of(rt), "prime sat_pi_atlas lv=0 total=999"))
    check("crossing: 999 draws nothing", rt.eval("NEVENTS()") == 0)

    rt.execute('SET_PAID("v1;88929:999:999")')
    pump(rt, 3)
    check("crossing: an unchanged payload draws nothing", rt.eval("NEVENTS()") == 0)

    rt.execute('SET_PAID("v1;88929:1000:1000")')
    pump(rt, 8)
    check("crossing: exactly the rung is a crossing",
          has_line(lines_of(rt),
                   "sat_pi_atlas crossed 1 row 54499 rank=1 banner=2 total=1000 rung=1000 src=dll"),
          " | ".join(lines_of(rt)[-4:]))
    check("crossing: one banner, not two", rt.eval("NAMED('completed_challenge')") == 1)

    rt.execute("CLEAR()")
    rt.execute('SET_PAID("v1;88929:2199:2199")')
    pump(rt, 3)
    check("crossing: 2199 stays at level 1", rt.eval("NAMED('completed_challenge')") == 0)
    rt.execute('SET_PAID("v1;88929:2200:2200")')
    pump(rt, 8)
    check("crossing: 2200 is level 2", rt.eval("NAMED('completed_challenge')") == 1,
          str(rt.eval("NAMED('completed_challenge')")))


def attach_card(lua51):
    rt = new_rt(lua51, pre='SET_PAID("v1;88929:999:999")')
    pump(rt, 3)
    check("card: no card before the crossing", rt.eval("NAMED('add_message_splash_manager')") == 0)

    rt.execute('SET_PAID("v1;88929:1000:1000")')
    pump(rt, 20)
    l = lines_of(rt)
    check("card: the level's own item is drawn", rt.eval("NAMED('add_message_splash_manager')") == 1,
          str(rt.eval("NAMED('add_message_splash_manager')")))
    check("card: the banner came first", rt.eval("EVENTS[1].name") == "completed_challenge",
          str(rt.eval("EVENTS[1].name")))
    check("card: the level-2 items did not fire at level 1",
          not has_line(l, "attachment 88614") and not has_line(l, "attachment 97706"), " | ".join(l[-6:]))
    check("card: the card is the game's weaponProgression splash",
          rt.eval("LASTOF('add_message_splash_manager').options.displayLocation") == "weaponProgression")
    check("card: the card names the item",
          rt.eval("LASTOF('add_message_splash_manager').options.headerText") == "Beadline Tactical Pad")
    check("card: the crossing line carries the payload's total",
          has_line(l, "attachment 88649 Beadline Tactical Pad ref=") and has_line(l, "total=1000 rung=1000"))


def absent(lua51):
    rt = new_rt(lua51)
    pump(rt, 4)
    lines = lines_of(rt)
    check("absent: nothing is drawn", rt.eval("NEVENTS()") == 0)
    check("absent: exactly one line names the missing payload",
          count_line(lines, "paid source absent") == 1, " | ".join(lines))
    check("absent: that is the only paid line", count_line(lines, "paid source ") == 1, " | ".join(lines))
    check("absent: the display wrapper is not even installed",
          not has_line(lines, "in-match display armed"), " | ".join(lines))

    rt2 = new_rt(lua51, pre='SET_PAID("v2;88929:1000:1000")')
    pump(rt2, 3)
    check("absent: an unknown payload version is not read",
          has_line(lines_of(rt2), "paid source ignored") and rt2.eval("NEVENTS()") == 0)


def display(lua51):
    rt = new_rt(lua51, pre='SET_PAID("v1;88929:1000:1000")')
    pump(rt, 9)
    xp, rank = rt.eval("OC_READ(54499)")
    check("display: the client's own record answers the payload's total", int(xp) == 1000, str(xp))
    check("display: and the level the rung lookup gave", int(rank) == 1, str(rank))
    check("display: the plain progress reader too", int(rt.eval("OC_DEF(54499)")) == 1000)
    check("display: the row's own value is untouched in the stub", int(rt.eval("OC['54499'].xp")) == 0)
    check("display: the card level line names the display number",
          has_line(lines_of(rt), "card level ref=sat_pi_atlas row=54499 total=1000 display=2"))


def extras(lua51):
    rt = new_rt(lua51, pre='SET_PAID("v1;102705:1793:1793")')
    pump(rt, 122)
    lines = lines_of(rt)
    check("extras: the heartbeat carries the payload's own figures",
          has_line(lines, "hb tick=") and has_line(lines, "total=1793") and has_line(lines, "psrc=dll"),
          " | ".join([ln for ln in lines if "hb " in ln]))
    check("extras: the heartbeat names the gun and its level",
          has_line(lines, "first=sat_sh_shepherd") and has_line(lines, "lv=2"))

    rt2 = new_rt(lua51, pre='SET_PAID("v1;88929:999:999") SET_NOTIF(1)')
    pump(rt2, 3)
    rt2.execute('SET_PAID("v1;88929:1000:1000")')
    pump(rt2, 20)
    check("extras: the game's own notification switch silences the card",
          rt2.eval("NAMED('add_message_splash_manager')") == 0
          and has_line(lines_of(rt2), "attachment cards stand down"), " | ".join(lines_of(rt2)[-4:]))
    check("extras: but the banner still fires", rt2.eval("NAMED('completed_challenge')") == 1)

    rt3 = new_rt(lua51, pre='SET_TOGGLE("pt_on", 0) SET_PAID("v1;88929:1000:1000")')
    pump(rt3, 6)
    check("extras: pt_on off arms but draws nothing", rt3.eval("NEVENTS()") == 0)
    check("extras: and it says so", has_line(lines_of(rt3), "pt_on is off"), " | ".join(lines_of(rt3)))


def g11_reader(lua51, ls):
    ids = sorted(ls)
    eight = ACCEPT
    lit = eight + ids[:64] + [1, 2, 3]
    slabs = slabs_of(lit)

    rt = new_rt(lua51, frontend=True, src=False)
    lua_slabs(rt, slabs)
    rt.execute("SET_G11(17)")
    load(rt)
    pump(rt, 1)
    lines = lines_of(rt)

    check("g11: the menu context arms the reader",
          has_line(lines, "armed v1.0 in the menu") and has_line(lines, "g11 armed (scope locksmith, 4203 ids)"),
          " | ".join(lines[:6]))
    check("g11: both ownership doors are wrapped",
          has_line(lines, "g11 isunlockedwithid wrapped (2 of 2: PROGRESSION, LOOT)"), " | ".join(lines[:8]))
    want = "g11 rebuilt from serial 17 (locks %d, %d in scope)" % (len(lit), len(ls & set(lit)))
    check("g11: the rebuild line names the payload's locks, the serial and the in-scope count",
          has_line(lines, want), " | ".join(lines[:10]))
    check("g11: the arm line comes before the rebuild line",
          [i for i, ln in enumerate(lines) if ln.startswith("progression_tuning: g11 armed")][0]
          < [i for i, ln in enumerate(lines) if "rebuilt from serial" in ln][0])
    check("g11: the decoded lock count is the bitmap's own", int(rt.eval("G11('locks')")) == len(lit),
          str(rt.eval("G11('locks')")))
    check("g11: the scope size is the generated table's", int(rt.eval("G11('scopeCount')")) == LS_COUNT,
          str(rt.eval("G11('scopeCount')")))

    bad = [i for i in eight if rt.eval("ASK_P(%d)" % i) is not False or rt.eval("ASK_L(%d)" % i) is not False]
    check("g11: the eight acceptance ids read locked through both doors", not bad, str(bad))

    before = int(rt.eval("PCALLS"))
    for i in eight:
        rt.eval("ASK_P(%d)" % i)
    check("g11: a locked id never reaches the previous function",
          int(rt.eval("PCALLS")) == before, "%d calls" % (int(rt.eval("PCALLS")) - before))

    pc = int(rt.eval("PCALLS"))
    lc = int(rt.eval("LCALLS"))
    rt.execute("SET_TYPE(2, 2)")
    rt.eval("ASK_P(2)")
    rt.eval("ASK_L(2)")
    check("g11: an id whose bit is set but whose type is a weapon reads unchanged (both doors)",
          rt.eval("ASK_P(2)") is True and rt.eval("ASK_L(2)") is True)
    check("g11: and the previous function answers it, once per ask",
          int(rt.eval("PCALLS")) - pc == 2 and int(rt.eval("LCALLS")) - lc == 2,
          "%d / %d" % (int(rt.eval("PCALLS")) - pc, int(rt.eval("LCALLS")) - lc))

    check("g11: an id in no bitmap reads unchanged",
          rt.eval("ASK_P(150000)") is True and rt.eval("ASK_L(150000)") is True)
    check("g11: an id above the bitmap's domain reads unchanged",
          rt.eval("ASK_P(262144)") is True)

    rt.execute('SET_SCOPE("all")')
    check("g11: scope 'all' is retired - a weapon id with a bit still reads unchanged",
          rt.eval("ASK_P(2)") is True and rt.eval("ASK_L(2)") is True)
    check("g11: and the retirement says so once",
          count_line(lines_of(rt), "g11 scope all is retired") == 1,
          " | ".join([ln for ln in lines_of(rt) if "scope" in ln]))
    check("g11: a camo id with a bit is still locked under the retired 'all'",
          all(rt.eval("ASK_P(%d)" % i) is False for i in eight))
    for value in ("ALL", " all", "locksmith", "0", "true"):
        rt.execute('SET_SCOPE("%s")' % value)
        check("g11: scope %r is not 'all', and the door answers by type either way" % value,
              rt.eval("ASK_P(2)") is True)
    rt.execute("CLEAR_SCOPE()")
    check("g11: an absent scope dvar changes nothing", rt.eval("ASK_P(2)") is True)
    check("g11: going back to locksmith says so once",
          count_line(lines_of(rt), "g11 scope locksmith - 4203 ids") == 1)
    check("g11: the acceptance ids are still locked after the scope went back",
          all(rt.eval("ASK_P(%d)" % i) is False for i in eight))

    rt.execute('SET_DVAR("zm_unlock_all", "1")')
    check("g11: zm_unlock_all stands every lock this file adds down",
          all(rt.eval("ASK_P(%d)" % i) is True and rt.eval("ASK_L(%d)" % i) is True for i in eight))
    check("g11: the stand-down is logged once, naming the toggle",
          count_line(lines_of(rt),
                     "g11 debug unlock zm_unlock_all is on - every lock this file adds is stepped aside") == 1,
          " | ".join([ln for ln in lines_of(rt) if "debug unlock" in ln]))
    rt.execute('SET_DVAR("zm_unlock_all", "0")')
    check("g11: '0' is not on, so the locks come back", all(rt.eval("ASK_P(%d)" % i) is False for i in eight))
    rt.execute('SET_DVAR("zm_unlock_attachments", "2")')
    check("g11: the client's own rule - any non-zero value is on",
          all(rt.eval("ASK_P(%d)" % i) is True for i in eight))
    rt.execute('SET_DVAR("zm_unlock_attachments", "")')
    check("g11: an empty toggle value is not on", all(rt.eval("ASK_P(%d)" % i) is False for i in eight))
    rt.execute("CLR_DVAR('zm_unlock_attachments')")

    rt.execute('SET_TOGGLE("pt_on", 0)')
    pump(rt, 8)
    check("g11: pt_on off makes the reader a passthrough on both doors",
          all(rt.eval("ASK_P(%d)" % i) is True and rt.eval("ASK_L(%d)" % i) is True for i in eight))
    rt.execute('SET_TOGGLE("pt_on", 1)')
    pump(rt, 8)
    check("g11: and back on again without a reload", all(rt.eval("ASK_P(%d)" % i) is False for i in eight))


def g11_payload(lua51, ls):
    ids = sorted(ls)
    lit = ACCEPT + ids[:64] + [1, 2, 3]
    slabs = slabs_of(lit)

    rt = new_rt(lua51, frontend=True, src=False)
    lua_slabs(rt, slabs)
    rt.execute("SET_G11(5)")
    load(rt)
    pump(rt, 1)

    rt.execute('SET_VER("6:33:65536")')
    rt.execute("PUMP(8)")
    check("g11 payload: a new serial carrying the same bitmap is a skip, not a rebuild",
          int(rt.eval("G11('skips')")) == 1 and str(rt.eval("G11('ver')")) == "6:33:65536",
          "%s skips=%s" % (rt.eval("G11('ver')"), rt.eval("G11('skips')")))
    check("g11 payload: the answers are unchanged by the skip",
          all(rt.eval("ASK_P(%d)" % i) is False for i in ACCEPT))

    cleared = ACCEPT[:3]
    lua_slabs(rt, slabs_of([i for i in lit if i not in cleared]))
    rt.execute('SET_VER("7:33:65536")')
    rt.execute("PUMP(8)")
    check("g11 payload: a changed bitmap is rebuilt once, with the new counts",
          str(rt.eval("G11('ver')")) == "7:33:65536"
          and int(rt.eval("G11('locks')")) == len(lit) - len(cleared),
          "%s locks=%s" % (rt.eval("G11('ver')"), rt.eval("G11('locks')")))
    check("g11 payload: the cleared ids read unlocked", all(rt.eval("ASK_P(%d)" % i) is True for i in cleared))
    check("g11 payload: the ids still in the bitmap stay locked",
          all(rt.eval("ASK_P(%d)" % i) is False for i in ACCEPT[3:]))

    rt.execute('SET_VER("8:33:65536")')
    rt.execute("SET_PART(5, '')")
    rt.execute("PUMP(8)")
    got = rt.eval("ASK_P(%d)" % ACCEPT[3])
    l = lines_of(rt)
    check("g11 payload: a short payload is refused and the previous set kept",
          got is False and has_line(l, "g11 part 5 of 33 did not read - refused, keeping the previous payload"),
          " | ".join(l[-3:]))
    rt.execute("SET_PART(5, SLABS[6])")

    rt.execute('SET_VER("bad")')
    check("g11 payload: a header that is not <serial>:33:65536 is refused",
          (rt.eval("ASK_P(%d)" % ACCEPT[3]) is False)
          and has_line(lines_of(rt), "g11 header bad is not <serial>:33:65536 - refused, keeping the previous payload"))

    rt.execute('SET_VER("9:32:65536")')
    rt.execute("ASK_P(%d)" % ACCEPT[3])
    check("g11 payload: a header claiming 32 parts is refused too",
          has_line(lines_of(rt), "g11 header 9:32:65536 is not <serial>:33:65536"))

    rt.execute("RESET_READS()")
    rt.execute("ASK_P(%d)" % ACCEPT[3])
    check("g11 payload: an unchanged header costs the header read only - no part is read",
          int(rt.eval("READS()")) < PARTS, "%d reads" % int(rt.eval("READS()")))

    rt.execute('SET_VER("20:33:65536")')
    lua_slabs(rt, slabs_of(lit))
    rt.execute("RESET_READS()")
    rt.execute("TORN_NEXT(20)")
    rt.execute("PUMP(8)")
    check("g11 payload: a republish that lands mid-read applies nothing",
          str(rt.eval("G11('ver')")) != "20:33:65536", str(rt.eval("G11('ver')")))
    rt.execute('SET_VER("21:33:65536")')
    rt.execute("PUMP(8)")
    rt.execute("PUMP(8)")
    check("g11 payload: and the next window reads the complete payload again",
          str(rt.eval("G11('ver')")) == "21:33:65536", str(rt.eval("G11('ver')")))


def g11_absent(lua51):
    rt = new_rt(lua51, frontend=True, pre="NO_DVARS()")
    pump(rt, 4)
    l = lines_of(rt)
    check("g11 absent: a namespace that answers nil is reported as absent dvars, once",
          count_line(l, "g11 the payload dvars are not there yet") == 1, " | ".join(l))
    check("g11 absent: exactly one line says there is no payload yet",
          count_line(l, "g11 no payload yet - running on the 96 published chunks") == 1, " | ".join(l))
    check("g11 absent: every ask is a pure passthrough on both doors",
          all(rt.eval("ASK_P(%d)" % i) is True and rt.eval("ASK_L(%d)" % i) is True for i in ACCEPT))
    check("g11 absent: the previous function answers every ask", int(rt.eval("PCALLS")) >= 8,
          str(rt.eval("PCALLS")))
    check("g11 absent: nothing is decoded, so nothing can be locked",
          int(rt.eval("G11('locks')")) == 0 and int(rt.eval("G11('inScope')")) == 0)
    check("g11 absent: the reader is still armed, add-only, and answers nothing it cannot prove",
          has_line(l, "g11 isunlockedwithid wrapped (2 of 2: PROGRESSION, LOOT)"))

    rt2 = new_rt(lua51, frontend=True, pre='SET_ARM("g11") SET_VER("g11")')
    pump(rt2, 3)
    l2 = lines_of(rt2)
    check("g11 absent: a created-but-unpublished header is reported as no payload, not as absent dvars",
          count_line(l2, "g11 no payload yet") == 1
          and count_line(l2, "g11 the payload dvars are not there yet") == 0, " | ".join(l2))

    rt3 = new_rt(lua51, frontend=False)
    pump(rt3, 2)
    check("g11 absent: the match context arms the reader too",
          has_line(lines_of(rt3), "g11 armed (scope locksmith, 4203 ids)"), " | ".join(lines_of(rt3)[:4]))


def g11_order_and_cap(lua51, ls):
    ids = sorted(ls)
    lit = ids[:32]
    slabs = slabs_of(lit)

    rt = new_rt(lua51, frontend=True, src=False)
    lua_slabs(rt, slabs)
    rt.execute("SET_G11(3)")
    load(rt)
    pump(rt, 1)
    pc = int(rt.eval("PCALLS"))
    rt.execute("ASK_P(2)")
    rt.execute("ASK_P(2)")
    check("g11 order: an unlocked ask reaches the previous function exactly once per ask",
          int(rt.eval("PCALLS")) - pc == 2, "%d calls for 2 asks" % (int(rt.eval("PCALLS")) - pc))

    before = len(lines_of(rt))
    load(rt)
    l2 = lines_of(rt)
    check("g11 order: reloading the chunk does not re-arm it or stack a second wrapper",
          count_line(l2, "g11 armed (scope locksmith") == 1 and len(l2) == before, " | ".join(l2))
    pc = int(rt.eval("PCALLS"))
    rt.execute("ASK_P(2)")
    check("g11 order: and the door still answers once per ask after the reload",
          int(rt.eval("PCALLS")) - pc == 1, str(int(rt.eval("PCALLS")) - pc))

    rt2 = new_rt(lua51, frontend=True, pre="PROGRESSION = nil LOOT = nil")
    fired = int(pump(rt2, 480))
    l3 = lines_of(rt2)
    check("g11 order: the wrap wait is capped at 480 ticks", fired == 480, "%d ticks" % fired)
    check("g11 order: the wait is announced once, then the cap",
          count_line(l3, "g11 waiting for PROGRESSION / LOOT") == 1
          and count_line(l3, "g11 gave up wrapping - PROGRESSION / LOOT") == 1, " | ".join(l3))
    check("g11 order: the timer keeps running after the cap (the display half needs it)",
          int(rt2.eval("QUEUED()")) == 1, str(rt2.eval("QUEUED()")))
    check("g11 order: giving up leaves nothing wrapped",
          int(rt2.eval("G11('wrappers')")) == 0, str(rt2.eval("G11('wrappers')")))

    rt3 = lua51(unpack_returned_tuples=True)
    rt3.execute(PRELUDE)
    rt3.execute("FRONTEND = true")
    rt3.execute(FIXTURE)
    lua_slabs(rt3, slabs)
    rt3.execute("SET_G11(4)")
    rt3.execute(SCANKEY)
    load(rt3)
    l4 = lines_of(rt3)
    check("g11 order: a slot reachable only through the normalised key scan is wrapped",
          has_line(l4, "g11 isunlockedwithid wrapped (2 of 2: PROGRESSION, LOOT)")
          or has_line(l4, "g11 isunlockedwithid wrapped (1 of 2: LOOT)"),
          " | ".join([ln for ln in l4 if "wrapped" in ln]))
    check("g11 order: and it answers from the payload",
          all(rt3.eval("ASK_P(%d)" % i) is False for i in lit))

    rt4 = new_rt(lua51, frontend=True, pre="LUI = nil", src=False)
    lua_slabs(rt4, slabs)
    rt4.execute("SET_G11(1)")
    load(rt4)
    l5 = lines_of(rt4)
    check("g11 order: with no LUI root the reader says so and drops the rebuild window",
          has_line(l5, "no LUI root - the lock reader cannot poll") and rt4.eval("G11('noClock')") is True,
          " | ".join(l5))
    rt4.execute('SET_VER("2:33:65536")')
    rt4.execute("ASK_P(%d)" % ACCEPT[0])
    check("g11 order: and the next ask still picks the new serial up (no clock, no window)",
          str(rt4.eval("G11('ver')")) == "2:33:65536", str(rt4.eval("G11('ver')")))


def s1_door(lua51, ls):
    ids = sorted(ls)
    inscope = ids[:20]
    outside = [150001, 150002]
    camo = [131708, 131545]
    attach = [126608, 140701]
    plain = [(125186, 2), (200000, 11)]
    nobit = [150010, 150011]
    lit = inscope + outside + camo + attach + [i for i, _t in plain]
    slabs = slabs_of(lit)

    rt = new_rt(lua51, frontend=True, src=False)
    lua_slabs(rt, slabs)
    rt.execute("SET_TYPE(125186, 2)")
    rt.execute("SET_TYPE(200000, 11)")
    for i in camo:
        rt.execute("SET_TYPE(%d, 13)" % i)
    rt.execute("SET_G11(31)")
    load(rt)
    pump(rt, 1)
    lines = lines_of(rt)

    check("s1: the rebuild line names the type route the door will use",
          has_line(lines, "g11 rebuilt from serial 31 (locks %d, %d in scope) types=attachment,camo"
                           % (len(lit), len(ls & set(lit)))),
          " | ".join([ln for ln in lines if "rebuilt" in ln]))

    check("s1: an attachment id in the shipped scope reads locked on both doors",
          all(rt.eval("ASK_P(%d)" % i) is False and rt.eval("ASK_L(%d)" % i) is False for i in inscope))
    check("s1: an attachment id with a bit but OUTSIDE the scope reads locked - the S1 win",
          all(rt.eval("ASK_L(%d)" % i) is False for i in outside),
          str([rt.eval("ASK_L(%d)" % i) for i in outside]))
    check("s1: a camo id with a bit reads locked on both doors",
          all(rt.eval("ASK_P(%d)" % i) is False and rt.eval("ASK_L(%d)" % i) is False for i in camo))
    check("s1: an attachment with a bit still reads locked, as RC 1.0 answered",
          all(rt.eval("ASK_P(%d)" % i) is False and rt.eval("ASK_L(%d)" % i) is False for i in attach))
    check("s1: a weapon id and a calling card with a bit keep the client's own answer",
          all(rt.eval("ASK_P(%d)" % i) is True and rt.eval("ASK_L(%d)" % i) is True for i, _t in plain),
          str([(i, rt.eval("ASK_L(%d)" % i)) for i, _t in plain]))
    before = int(rt.eval("LCALLS"))
    rt.eval("ASK_L(125186)")
    check("s1: and that answer is the previous function's, not a false close",
          int(rt.eval("LCALLS")) - before == 1, str(int(rt.eval("LCALLS")) - before))
    check("s1: an id with no bit at all reads unchanged on both doors",
          all(rt.eval("ASK_P(%d)" % i) is True and rt.eval("ASK_L(%d)" % i) is True for i in nobit))
    rt.execute("SET_TYPE(150022, 13)")
    rt.eval("ASK_L(150022)")
    check("s1: a camo id with no bit is logged as bit=0 answer=pass",
          has_line(lines_of(rt), "door id=150022 type=13 bit=0 answer=pass"),
          " | ".join([ln for ln in lines_of(rt) if "door id=" in ln][:4]))
    tc = int(rt.eval("TYPECALLS"))
    rt.eval("ASK_L(150023)")
    check("s1: with the log on, a no-bit id costs one type read, because the line needs it",
          int(rt.eval("TYPECALLS")) - tc == 1, str(int(rt.eval("TYPECALLS")) - tc))

    tc = int(rt.eval("TYPECALLS"))
    for _ in range(6):
        rt.eval("ASK_L(%d)" % camo[0])
    check("s1: the type of an id is looked up once, then cached", int(rt.eval("TYPECALLS")) - tc == 0,
          str(int(rt.eval("TYPECALLS")) - tc))

    l = lines_of(rt)
    check("s1: a camo decision is logged as door id/type/bit/answer",
          has_line(l, "door id=131708 type=13 bit=1 answer=locked"),
          " | ".join([ln for ln in l if "door id=" in ln][:4]))
    check("s1: a weapon id is a door decision too, but the line is for camo ids only",
          not has_line(l, "door id=125186"), " | ".join([ln for ln in l if "door id=" in ln][:8]))
    check("s1: and a camo id with a bit answers locked exactly once in the log",
          count_line(l, "door id=131708") == 1, str(count_line(l, "door id=131708")))

    rt.execute('SET_TOGGLE("pt_on", 0)')
    pump(rt, 8)
    check("s1: pt_on off makes the door a passthrough on every class",
          all(rt.eval("ASK_L(%d)" % i) is True for i in inscope + outside + camo + attach)
          and all(rt.eval("ASK_P(%d)" % i) is True for i in inscope + camo))
    rt.execute('SET_TOGGLE("pt_on", 1)')
    pump(rt, 8)
    check("s1: and back on again without a reload",
          all(rt.eval("ASK_L(%d)" % i) is False for i in inscope + camo))

    many = [130001 + i for i in range(40)]
    lua_slabs(rt, slabs_of(lit + many))
    for i in many:
        rt.execute("SET_TYPE(%d, 13)" % i)
    door_before = count_line(lines_of(rt), "door id=")
    rt.execute('SET_VER("32:33:65536")')
    pump(rt, 8)
    pump(rt, 8)
    rt.eval("ASK_L(%d)" % camo[0])
    for i in many:
        rt.eval("ASK_L(%d)" % i)
    after = count_line(lines_of(rt), "door id=")
    check("s1: a rebuild resets the door log, and lets the same camo id be logged again",
          count_line(lines_of(rt), "door id=131708") == 2 and after - door_before == 24,
          "%d new lines, %d for 131708" % (after - door_before, count_line(lines_of(rt), "door id=131708")))
    check("s1: the door log is bounded at 24 lines per rebuild",
          after - door_before <= 24 and door_before <= 24, "%d then %d" % (door_before, after - door_before))

    quiet = new_rt(lua51, frontend=True, src=False, log=False)
    lua_slabs(quiet, slabs)
    quiet.execute("SET_G11(33)")
    load(quiet)
    pump(quiet, 1)
    for i in camo + attach:
        quiet.eval("ASK_L(%d)" % i)
    tq = int(quiet.eval("TYPECALLS"))
    quiet.eval("ASK_L(150030)")
    quiet.eval("ASK_P(150031)")
    check("s1: with pt_log and pt_diag both off, no door line is printed",
          not has_line(lines_of(quiet), "door id="),
          " | ".join([ln for ln in lines_of(quiet) if "door id=" in ln][:3]))
    check("s1: a no-bit id costs one type read now, because a prestige reward carries no bit (S3)",
          int(quiet.eval("TYPECALLS")) - tq == 2, str(int(quiet.eval("TYPECALLS")) - tq))
    tq = int(quiet.eval("TYPECALLS"))
    quiet.eval("ASK_L(150030)")
    check("s1: and the second ask for the same id is answered from the cached type",
          int(quiet.eval("TYPECALLS")) == tq, str(int(quiet.eval("TYPECALLS")) - tq))


def s1_fallback(lua51, ls):
    ids = sorted(ls)
    sample = ids[:12] + [150001, 150002, 150010]
    lit = ids[:12] + [150001, 150002]

    def run(pre):
        rt = new_rt(lua51, frontend=True, src=False, pre=pre)
        lua_slabs(rt, slabs_of(lit))
        rt.execute("SET_G11(41)")
        load(rt)
        pump(rt, 1)
        got = {}
        for i in sample:
            got[i] = (rt.eval("ASK_P(%d)" % i), rt.eval("ASK_L(%d)" % i))
        return rt, got

    rc10 = {i: (not ((i in lit) and (i in ls)), not ((i in lit) and (i in ls))) for i in sample}

    rt, got = run("DROP_TYPE_API()")
    check("s1 fallback: with no gettypeforid the door is RC 1.0's bit AND scope, id for id",
          got == rc10, str([(i, got[i], rc10[i]) for i in sample if got[i] != rc10[i]][:3]))
    check("s1 fallback: and it says which line it fell back to, once",
          count_line(lines_of(rt), "lock door: no LOOT.gettypeforid in this VM - answering from the 4203-id"
                                   " locksmith scope instead of the item type") == 1,
          " | ".join([ln for ln in lines_of(rt) if "lock door" in ln]))
    check("s1 fallback: it never widens - an out-of-scope id with a bit stays open",
          rt.eval("ASK_L(150001)") is True)

    rt2, got2 = run("DROP_TYPES()")
    check("s1 fallback: with no itemTypes the same fallback answers the same set",
          got2 == rc10, str([(i, got2[i], rc10[i]) for i in sample if got2[i] != rc10[i]][:3]))
    check("s1 fallback: and names the missing table",
          has_line(lines_of(rt2), "lock door: no LOOT.itemTypes in this VM"))

    rt3, got3 = run("TYPE_RAISES()")
    check("s1 fallback: a raising gettypeforid falls back the same way",
          got3 == rc10, str([(i, got3[i], rc10[i]) for i in sample if got3[i] != rc10[i]][:3]))
    check("s1 fallback: and says it raised",
          has_line(lines_of(rt3), "lock door: LOOT.gettypeforid raised"))

    rt4, got4 = run("")
    check("s1 fallback: with the type available the same ids answer by type, not by scope",
          got4[150001] == (False, False) and got4[ids[0]] == (False, False),
          str((got4[150001], got4[ids[0]])))


PRESTIGE_CAMO_FN = """
PRESTIGE[xhash("getmaxweaponprestigelevel")] = function(ref) return 2 end
SET_PRESTIGE_CAMOS(function(ref)
  local a = { { startPrestige = 0, startLevel = 0, targetPrestige = 1, targetLevel = 27,
                camoBundle = { lootid = 107478 } } }
  local b = { { startPrestige = 2, startLevel = 99, targetPrestige = 2, targetLevel = 149,
                camoBundle = { lootid = 132741 } } }
  return a, b, {}
end)
"""

S4_PRE = """
OWNEDN = 0
Loot = {}
Loot[xhash("IsOwned")] = function(c, id) OWNEDN = OWNEDN + 1; return 99 end
ORIG = Loot[xhash("IsOwned")]
function ASK_ORIG(id) return ORIG(0, id) end
function ASK_OWNED(id) return Loot[xhash("IsOwned")](0, id) end
function ASK_TOK(ref) return PRESTIGE[xhash("getweaponprestigetokenlootid")](ref) end
function SAME_WRAPPER() return Loot[xhash("IsOwned")] == W1 end
META[126615] = { sentinel_id = 132396 }
LOOT[xhash("getprogressionitemmetadata")] = function() return META end
PRESTIGE[xhash("getweaponprestigetokenlootid")] = function(ref) return 104729 end
"""


def s3_prestige(lua51, ls):
    def build(pre=""):
        rt = new_rt(lua51, frontend=True, src=False, pre=pre)
        lua_slabs(rt, slabs_of([150900]))
        rt.execute("SET_G11(51)")
        rt.execute('SET_PRESTIGE("sat_pi_alcor", 0)')
        rt.execute('SET_LEVEL("sat_pi_alcor", 2)')
        rt.execute('SET_PREQ("sat_pi_alcor", 126608, 1)')
        rt.execute('PRESTIGE_BUNDLE(126608, "sat_pi_alcor")')
        rt.execute('PLAIN_BUNDLE(140701, "sat_pi_alcor")')
        rt.execute('SET_CAMODATA(107478, "sat_pi_alcor")')
        rt.execute('SET_CAMODATA(132741, "sat_pi_alcor")')
        for i, t in ((126608, 7), (140701, 7), (107478, 13), (132741, 13)):
            rt.execute("SET_TYPE(%d, %d)" % (i, t))
        rt.execute(PRESTIGE_CAMO_FN)
        load(rt)
        pump(rt, 1)
        return rt

    rt = build()
    check("s3: a prestige attachment with no lock bit is locked at weapon prestige 0",
          rt.eval("ASK_L(126608)") is False and rt.eval("ASK_P(126608)") is False,
          "%s / %s" % (rt.eval("ASK_L(126608)"), rt.eval("ASK_P(126608)")))
    check("s3: the line names the id, the tier it needs, the prestige and the answer",
          has_line(lines_of(rt), "prestige id=126608 tier=1 prestige=0 answer=locked"),
          " | ".join([ln for ln in lines_of(rt) if "prestige id=" in ln][:3]))
    check("s3: an attachment its own bundle does not call a prestige reward is untouched",
          rt.eval("ASK_L(140701)") is True)

    rt.execute('SET_PRESTIGE("sat_pi_alcor", 1)')
    check("s3: it opens as soon as the weapon's own prestige reaches the tier its bundle names",
          rt.eval("ASK_L(126608)") is True)
    check("s3: a prestige camo opens once its band's prestige is reached",
          rt.eval("ASK_L(107478)") is True)

    rt.execute('SET_PRESTIGE("sat_pi_alcor", 0)')
    check("s3: and a prestige camo is locked again when the prestige is not there",
          rt.eval("ASK_L(107478)") is False, str(rt.eval("ASK_L(107478)")))
    check("s3: the camo line carries the band, the prestige, the level and the answer",
          has_line(lines_of(rt), "prestige camo id=107478 ref=sat_pi_alcor start=0/0 to=1/27"),
          " | ".join([ln for ln in lines_of(rt) if "prestige camo id=" in ln][:3]))

    check("s3: a master-band camo is locked while the weapon's level is below its band",
          rt.eval("ASK_L(132741)") is False, str(rt.eval("ASK_L(132741)")))
    rt.execute('SET_PRESTIGE("sat_pi_alcor", 2)')
    rt.execute('SET_LEVEL("sat_pi_alcor", 149)')
    check("s3: and opens at the max prestige and the level its band names",
          rt.eval("ASK_L(132741)") is True, str(rt.eval("ASK_L(132741)")))

    rt.execute('SET_PRESTIGE("sat_pi_alcor", 0)')
    rt.execute('SET_LEVEL("sat_pi_alcor", 2)')
    check("s3: back at prestige 0 the prestige attachment is locked again",
          rt.eval("ASK_L(126608)") is False)
    rt.execute('PLAIN_BUNDLE(126608, "sat_pi_alcor")')
    check("s3: a bundle already read is cached until the bitmap rebuilds",
          rt.eval("ASK_L(126608)") is False)
    lua_slabs(rt, slabs_of([150901]))
    rt.execute('SET_VER("52:33:65536")')
    pump(rt, 8)
    pump(rt, 8)
    check("s3: and the rebuild that re-reads the bitmap re-reads the bundle too",
          rt.eval("ASK_L(126608)") is True, str(rt.eval("ASK_L(126608)")))

    rt.execute("SET_TYPE(150100, 13)")
    lua_slabs(rt, slabs_of([150901, 150100]))
    rt.execute('SET_VER("53:33:65536")')
    pump(rt, 8)
    pump(rt, 8)
    check("s3: the S1 door still answers by the bitmap and the type, unchanged",
          rt.eval("ASK_L(150100)") is False and rt.eval("ASK_P(150100)") is False)

    rt.execute('SET_TOGGLE("pt_on", 0)')
    pump(rt, 8)
    check("s3: pt_on off is a passthrough on both classes",
          rt.eval("ASK_L(126608)") is True and rt.eval("ASK_L(107478)") is True
          and rt.eval("ASK_L(150100)") is True)
    rt.execute('SET_TOGGLE("pt_on", 1)')
    pump(rt, 8)
    check("s3: and back on again without a reload",
          rt.eval("ASK_L(107478)") is False and rt.eval("ASK_L(150100)") is False,
          "%s / %s" % (rt.eval("ASK_L(107478)"), rt.eval("ASK_L(150100)")))

    rt2 = build("DROP_BUNDLE_API()")
    check("s3: with no ATTACHMENT.getbundlebyid nothing closes and one line says so",
          rt2.eval("ASK_L(126608)") is True
          and count_line(lines_of(rt2), "prestige lock: no ATTACHMENT.getbundlebyid") == 1,
          " | ".join([ln for ln in lines_of(rt2) if "prestige lock" in ln][:3]))

    rt3 = build("DROP_PREQ_API()")
    check("s3: with no getweaponprestigeattachmentdetails nothing closes and one line says so",
          rt3.eval("ASK_L(126608)") is True
          and count_line(lines_of(rt3), "prestige lock: no WEAPON.getweaponprestigeattachmentdetails") == 1,
          " | ".join([ln for ln in lines_of(rt3) if "prestige lock" in ln][:3]))

    rt4 = build("DROP_CAMODATA_API()")
    check("s3: with no WEAPON.getcamodatabyid the tiles keep the client's answer, one line",
          rt4.eval("ASK_L(107478)") is True
          and count_line(lines_of(rt4), "prestige lock: no WEAPON.getcamodatabyid") == 1,
          " | ".join([ln for ln in lines_of(rt4) if "prestige lock" in ln][:3]))

    rt5 = new_rt(lua51, frontend=True, src=False)
    lua_slabs(rt5, slabs_of([150900]))
    rt5.execute("SET_G11(54)")
    rt5.execute('SET_PRESTIGE("sat_pi_alcor", 0)')
    rt5.execute('SET_LEVEL("sat_pi_alcor", 2)')
    rt5.execute('SET_CAMODATA(107478, "sat_pi_alcor")')
    rt5.execute("SET_TYPE(107478, 13)")
    load(rt5)
    pump(rt5, 1)
    check("s3: with no PRESTIGE.getweaponprestigecamos the tile keeps the client's answer, one line",
          rt5.eval("ASK_L(107478)") is True
          and count_line(lines_of(rt5), "prestige lock: no PRESTIGE.getweaponprestigecamos") == 1,
          " | ".join([ln for ln in lines_of(rt5) if "prestige lock" in ln][:3]))

    rt6 = new_rt(lua51, frontend=True, src=False)
    lua_slabs(rt6, slabs_of([150900]))
    rt6.execute("SET_G11(55)")
    rt6.execute('SET_PRESTIGE("sat_pi_alcor", 0)')
    rt6.execute('SET_BUNDLE(126608, { [xhash("isprestige")] = true })')
    rt6.execute("SET_TYPE(126608, 7)")
    load(rt6)
    pump(rt6, 1)
    check("s3: a prestige reward that names no owning weapon is a passthrough, and says so once",
          rt6.eval("ASK_L(126608)") is True
          and count_line(lines_of(rt6), "prestige lock: 126608 is a prestige reward but names no weapon") == 1,
          " | ".join([ln for ln in lines_of(rt6) if "prestige lock" in ln][:3]))


def s4_value(lua51):
    def build(pre):
        rt = new_rt(lua51, frontend=True, src=False, pre=S4_PRE + pre)
        lua_slabs(rt, slabs_of([150900]))
        rt.execute("SET_G11(61)")
        load(rt)
        pump(rt, 1)
        rt.execute("W1 = Loot[xhash(\"IsOwned\")]")
        return rt

    rt = build("")
    check("s4: the client's own answer for a sentinel is 99, which is what the label reads",
          rt.eval("ASK_ORIG(132396)") == 99)
    check("s4: the door answers 0 for a permanent-unlock sentinel", rt.eval("ASK_OWNED(132396)") == 0,
          str(rt.eval("ASK_OWNED(132396)")))
    check("s4: a gobblegum id keeps the client's own answer, untouched",
          rt.eval("ASK_OWNED(56146)") == 99, str(rt.eval("ASK_OWNED(56146)")))
    check("s4: before the game's own accessor names the token, its id is untouched too",
          rt.eval("ASK_OWNED(104729)") == 99, str(rt.eval("ASK_OWNED(104729)")))
    check("s4: the game's own accessor still answers what it answered",
          rt.eval('ASK_TOK("sat_pi_alcor")') == 104729, str(rt.eval('ASK_TOK("sat_pi_alcor")')))
    check("s4: and from then on the prestige token id answers 0 as well",
          rt.eval("ASK_OWNED(104729)") == 0, str(rt.eval("ASK_OWNED(104729)")))
    before = int(rt.eval("OWNEDN"))
    rt.eval("ASK_OWNED(56146)")
    check("s4: everything else still reaches the previous function, exactly once",
          int(rt.eval("OWNEDN")) - before == 1, str(int(rt.eval("OWNEDN")) - before))
    pump(rt, 40)
    check("s4: one wrapper only - forty ticks do not wrap the slot again",
          rt.eval("SAME_WRAPPER()") is True and rt.eval("ASK_OWNED(132396)") == 0)
    check("s4: it says once what it answers and what it leaves alone",
          count_line(lines_of(rt), "lock value: a permanent-unlock sentinel and the prestige token id answer 0") == 1,
          " | ".join([ln for ln in lines_of(rt) if "lock value" in ln][:3]))

    rt.execute('SET_TOGGLE("pt_on", 0)')
    pump(rt, 8)
    check("s4: pt_on off is a passthrough - every id answers the client's own number",
          rt.eval("ASK_OWNED(132396)") == 99 and rt.eval("ASK_OWNED(104729)") == 99,
          "%s / %s" % (rt.eval("ASK_OWNED(132396)"), rt.eval("ASK_OWNED(104729)")))

    rt2 = new_rt(lua51, frontend=True, src=False,
                 pre=S4_PRE.replace('LOOT[xhash("getprogressionitemmetadata")] = function() return META end', ""))
    lua_slabs(rt2, slabs_of([150900]))
    rt2.execute("SET_G11(62)")
    load(rt2)
    pump(rt2, 1)
    check("s4: with no metadata every id is untouched, and one line says why",
          rt2.eval("ASK_OWNED(132396)") == 99
          and count_line(lines_of(rt2), "lock value: LOOT.getprogressionitemmetadata answered no table") == 1,
          " | ".join([ln for ln in lines_of(rt2) if "lock value" in ln][:3]))

    rt3 = new_rt(lua51, frontend=True, src=False,
                 pre='LOOT[xhash("getprogressionitemmetadata")] = function() return META end\n'
                     'PRESTIGE[xhash("getweaponprestigetokenlootid")] = function(ref) return 104729 end\n')
    lua_slabs(rt3, slabs_of([150900]))
    rt3.execute("SET_G11(63)")
    load(rt3)
    pump(rt3, 1)
    check("s4: with no Loot table the mod still arms and says so once",
          count_line(lines_of(rt3), "lock value: no Loot table in this VM") == 1
          and has_line(lines_of(rt3), "g11 isunlockedwithid wrapped (2 of 2")
          , " | ".join([ln for ln in lines_of(rt3) if "lock value" in ln or "wrapped" in ln][:4]))


def diag_q6_keyed(lua51):
    def build(keyform):
        rt = new_rt(lua51, frontend=True, src=False)
        rt.execute(DIAGFIX)
        rt.execute("NC2 = {}")
        rt.execute(keyform)
        rt.execute("SET_G11(71)")
        rt.execute("SET_TOGGLE('pt_diag', 1)")
        load(rt)
        return rt

    bytekey = ("NC2[string.char(0xff,0x95,0x03,0x18,0xbb,0x22,0x96,0xc2)] = function(c, k)\n"
               "  local t = {}\n"
               "  for i = 1, 3 do t[i] = { id = 68970, ref = 'sat_pi_alcor_camo_zm_base', lootId = 68970,"
               " normalizedProgress = 0.5 } end\n"
               "  return t\n"
               "end\n"
               "NearestToCompletionChallenges = NC2\n"
               "WEAPON_CAMO[string.char(0x1b,0x85,0xad,0x86,0xa9,0xdb,0xcc,0x34)] = function(c, m, r) return nil end")

    rt = build(bytekey)
    blk = rc1d_lines(lines_of(rt))
    check("diag Q6a: the key the client builds reaches the builder - wpk/key answer function",
          has_line(blk, "Q6 nc=table xpk=nil wpk=function key=function resp=3"),
          " | ".join([ln for ln in blk if "Q6 nc=" in ln]))
    check("diag Q6a: the byte keys are eight bytes each, as the client assembles them",
          has_line(blk, "Q6 wc ref=function data=nil bytes=8/8"),
          " | ".join([ln for ln in blk if "Q6 wc " in ln]))
    check("diag Q6a: and the builder's own count and entries follow the reachable key",
          has_line(blk, "Q6 count=3 key=zm cap=12") and count_line(blk, "Q6 ") == 6,
          str(count_line(blk, "Q6 ")))

    rt2 = build("NearestToCompletionChallenges = NC2")
    blk2 = rc1d_lines(lines_of(rt2))
    check("diag Q6a: with no builder at all the one line still prints, every field nil/absent",
          has_line(blk2, "Q6 nc=table xpk=nil wpk=nil key=nil resp=nil")
          and not has_line(blk2, "Q6 count="),
          " | ".join([ln for ln in blk2 if "Q6 " in ln][:3]))


def diag_q7_fields(lua51):
    def build(rows, recs, extra=""):
        rt = new_rt(lua51, frontend=True, src=False)
        rt.execute(DIAGFIX)
        rt.execute("OC2 = {}")
        rt.execute("OnlineChallenges[xhash('getchallengeprogress')] = function(c, id) return OC2[tostring(id)] end")
        rt.execute("ROWS['zmdaily'] = {%s}" % rows)
        if recs:
            rt.execute(recs)
        if extra:
            rt.execute(extra)
        rt.execute("SET_G11(72)")
        rt.execute("SET_TOGGLE('pt_diag', 1)")
        load(rt)
        return rc1d_lines(lines_of(rt))

    one = "['55415'] = { id = '55415', ref = 'sat_daily_zm_ch_p3_misc_gobblegums', amount = '5' }"
    blk = build(one, "OC2['55415'] = { progress = { default = 5, xp = 99 } }")
    check("diag Q7a: the figure comes from progress.default, the field the client exposes",
          has_line(blk, "Q7 daily 55415 progress=5 amount=5"),
          " | ".join([ln for ln in blk if "Q7 daily" in ln]))

    zero = "['53310'] = { id = '53310', ref = 'sat_daily_zm_ch_p1_kills_melee', amount = '75' }"
    blk2 = build(zero, "OC2['53310'] = { progress = { default = 0, xp = 0 } }")
    check("diag Q7a: with no hit at all the count line still says zero",
          has_line(blk2, "Q7 daily rows=1 withprogress=0 shown=0"),
          " | ".join([ln for ln in blk2 if "Q7 daily" in ln]))
    check("diag Q7a: and the field-name line prints anyway - the line that could never print before",
          has_line(blk2, "Q7 daily rec 53310 fields=progress pfields=default,xp"),
          " | ".join([ln for ln in blk2 if " rec " in ln]))

    two = (one + ", " + zero)
    blk3 = build(two, "OC2['55415'] = { progress = { default = 5 } }\n"
                       "OC2['53310'] = { progress = { default = 0 } }")
    check("diag Q7a: a named id that holds no progress is printed on its own line",
          has_line(blk3, "Q7 daily want 53310 progress=0 rec=table"),
          " | ".join([ln for ln in blk3 if "want" in ln]))
    check("diag Q7a: a named id already among the hits is not printed twice",
          count_line(blk3, "Q7 daily want ") == 1, str(count_line(blk3, "Q7 daily want ")))

    blk4 = build(one, "", "Challenge[xhash('getchallengesprogressforkind')] = function(c, k)"
                           " return { [60325] = { progress = { default = 7 } } } end")
    check("diag Q7a: getchallengesprogressforkind's form is measured, and one of its rows is read",
          has_line(blk4, "Q7 api progress=nil fork=function")
          and has_line(blk4, "Q7 fork 585 form=c,kind n=1 first=60325 progress=7"),
          " | ".join([ln for ln in blk4 if "fork" in ln]))

    blk5 = build(one, "", "Challenge[xhash('getchallengesprogressforkind')] = function(k)"
                           " if k ~= 585 then return nil end"
                           " return { [60326] = { progress = { default = 3 } } } end")
    check("diag Q7a: the one-argument form is tried too, and named if it is the one that answers",
          has_line(blk5, "Q7 fork 585 form=kind n=1 first=60326 progress=3"),
          " | ".join([ln for ln in blk5 if "fork" in ln]))


def rc1d_lines(lines):
    return [ln for ln in lines if "rc1diag:" in ln]


def rc1d_end(lines):
    for ln in lines:
        m = re.search(r"rc1diag: end \((\d+) lines\)", ln)
        if m:
            return int(m.group(1))
    return None


def diag_off(lua51):
    rt = new_rt(lua51, frontend=True, pre=DIAGFIX)
    pump(rt, 8)
    lines = lines_of(rt)
    check("diag: off by default - not one rc1diag line", not rc1d_lines(lines),
          " | ".join(rc1d_lines(lines)[:3]))

    rt.execute("SET_TOGGLE('pt_diag', 0)")
    pump(rt, 8)
    check("diag: an explicit 0 is off too", not rc1d_lines(lines_of(rt)))


def diag_menu(lua51):
    rt = new_rt(lua51, frontend=True, src=False)
    rt.execute(DIAGFIX)
    lua_slabs(rt, slabs_of([126608, 107478, 20000]))
    rt.execute("SET_TYPE(20000, 11)")
    rt.execute("SET_G11(9)")
    rt.execute("SET_TOGGLE('pt_diag', 1)")
    load(rt)
    lines = lines_of(rt)
    blk = rc1d_lines(lines)

    check("diag: the block opens with one header naming the VM, the switch and the payload",
          has_line(blk, "rc1diag: 1 block vm=menu pt_diag=on:int=1 payload=9 locks=3 inscope=0"),
          " | ".join(blk[:2]))
    check("diag: it ends with a line that counts its own lines", rc1d_end(blk) == len(blk),
          "end=%s lines=%d" % (rc1d_end(blk), len(blk)))
    check("diag: every line of the block carries the prefix",
          all("rc1diag:" in ln for ln in blk) and blk[-1].startswith("progression_tuning: rc1diag"))
    check("diag: Q1 - a set bit outside the scope, and a scope id with no bit",
          has_line(blk, "Q1 126608 P1 attachment bit=1 scope=0 mod=true")
          and has_line(blk, "Q1 126605 level attachment bit=0 scope=1 mod=false"), " | ".join(blk[1:4]))
    check("diag: Q1 - the 1911's nine ZM camo tiers are probed by id",
          all(has_line(blk, "Q1 %d " % i) for i in (131545, 131708, 131627, 131560, 131607, 131613,
                                                    131652, 131543, 131563)))
    check("diag: Q1 - the two camo tiers S0 could not answer are named",
          has_line(blk, "Q1 131708 tier2 tundra camo") and has_line(blk, "Q1 131545 tier1 char camo"))
    check("diag: Q2 - both doors answer the ORIGINAL function, not the wrapper",
          has_line(blk, "Q2 126608 progression=boolean:true loot=boolean:true")
          or has_line(blk, "Q2 126608 progression=boolean:true"), " | ".join(blk[15:18]))
    check("diag: Q2 - the five predicates under the LOOT door, raw",
          has_line(blk, "Q2 126608 net=boolean:true dw=boolean:true proxyowned=number:1 "
                        "platform=boolean:true default=boolean:false"), " | ".join(blk[28:32]))
    check("diag: Q3 - the metadata row and its sentinel",
          has_line(blk, "Q3 126608 meta=true sentinel=104729"))
    check("diag: Q3 - the three candidates, each with its raw value",
          has_line(blk, "Q3 126608 cand_a loot_owned=number:0")
          and has_line(blk, "Q3 126608 cand_b should_unlock_all=boolean:true")
          and has_line(blk, "Q3 126608 cand_c label=boolean:false second=boolean:false named=boolean:false"),
          " | ".join([ln for ln in blk if "Q3 126608" in ln]))
    check("diag: Q4 - the gun's prestige, tokens, level and rungs from the native getters",
          has_line(blk, "Q4 sat_pi_alcor prestige=number:0 tokens=number:0 maxprestige=number:2")
          and has_line(blk, "Q4 sat_pi_alcor level=number:2 maxlevel=number:55")
          and has_line(blk, "Q4 sat_pi_alcor rung1=number:1000 rung2=number:2200 rung3=number:3400")
          and has_line(blk, "Q4 sat_pi_alcor row=68333 xp=2809"),
          " | ".join([ln for ln in blk if "Q4 " in ln]))
    check("diag: Q5 - the camo's lock answer, the band it belongs to and its chain",
          has_line(blk, "Q5 107478 unlock=boolean:true is_locked=false")
          and has_line(blk, "Q5 107478 prestige=0 start=0 to=1/55")
          and has_line(blk, "Q5 107478 chain id=68970 progress=81 amount=100"),
          " | ".join([ln for ln in blk if "Q5 " in ln]))
    check("diag: Q6 - the builder's own count, and twelve entries at most",
          has_line(blk, "Q6 count=14 key=zm cap=12") and has_line(blk, "cap=12")
          and count_line(blk, "Q6 ") == 15,
          str(count_line(blk, "Q6 ")))
    check("diag: Q6 - an entry carries the challenge, the weapon ref and the camo",
          has_line(blk, "Q6 1 id=68970 ref=sat_pi_alcor_camo_zm_base loot=68970 "
                        "weapon=sat_pi_alcor"), " | ".join([ln for ln in blk if "Q6 1 " in ln]))
    check("diag: Q7 - the daily and the weekly, read from the record, uncapped",
          has_line(blk, "Q7 daily rows=1 withprogress=1 shown=1")
          and has_line(blk, "Q7 weekly rows=1 withprogress=1 shown=1"),
          " | ".join([ln for ln in blk if "Q7 " in ln]))
    check("diag: Q7 - the record's progress, amount and status are printed raw",
          has_line(blk, "Q7 daily 60325 progress=19 amount=25 status=nil"),
          " | ".join([ln for ln in blk if "Q7 daily " in ln]))
    check("diag: Q7 - the record's own field names are printed beside it, hits or not",
          has_line(blk, "Q7 daily rec 60325 fields=") and has_line(blk, "pfields="),
          " | ".join([ln for ln in blk if " rec " in ln]))
    check("diag: Q6 - the two key forms are named on one line before anything is called",
          has_line(blk, "Q6 nc=table xpk=nil wpk=nil key=nil resp=14"),
          " | ".join([ln for ln in blk if "Q6 nc=" in ln]))
    check("diag: Q8 - the native type for the four ids the door turns on",
          all(has_line(blk, "Q8 %d type=" % i) for i in (126605, 131708, 125186, 107478)),
          " | ".join([ln for ln in blk if "Q8 " in ln]))
    check("diag: Q8 - a control id picked from the bitmap whose type is neither gate",
          has_line(blk, "Q8 control id=20000 type=11 bit=1 looked="),
          " | ".join([ln for ln in blk if "Q8 control" in ln]))
    check("diag: the block is bounded", len(blk) <= 160, str(len(blk)))

    before = len(rc1d_lines(lines_of(rt)))
    pump(rt, 60)
    check("diag: it prints once per set - further ticks add nothing",
          len(rc1d_lines(lines_of(rt))) == before, "%d -> %d" % (before, len(rc1d_lines(lines_of(rt)))))


def diag_reprint(lua51):
    rt = new_rt(lua51, frontend=True, pre=DIAGFIX)
    pump(rt, 2)
    check("diag: no block before the switch is set", not rc1d_lines(lines_of(rt)))

    rt.execute("SET_TOGGLE('pt_diag', 1)")
    pump(rt, 8)
    n1 = count_line(rc1d_lines(lines_of(rt)), "rc1diag: 1 block")
    check("diag: setting the switch prints one block", n1 == 1, str(n1))

    rt.execute("SET_TOGGLE('pt_diag', 0)")
    pump(rt, 8)
    rt.execute("SET_TOGGLE('pt_diag', 1)")
    pump(rt, 8)
    n2 = count_line(rc1d_lines(lines_of(rt)), "rc1diag: 1 block")
    check("diag: setting it again prints the block again", n2 == 2, str(n2))
    check("diag: the second block is complete too",
          len([ln for ln in rc1d_lines(lines_of(rt)) if "rc1diag: end (" in ln]) == 2)


def diag_absent(lua51):
    rt = new_rt(lua51, frontend=True, pre="SET_TOGGLE('pt_diag', 1)")
    pump(rt, 1)
    lines = lines_of(rt)
    blk = rc1d_lines(lines)
    check("diag: a VM with no natives still prints, and closes its block",
          len(blk) > 10 and rc1d_end(blk) == len(blk), "end=%s lines=%d" % (rc1d_end(blk), len(blk)))
    check("diag: a missing native is a printed line, not a raise",
          has_line(blk, "tokens=absent")
          and has_line(blk, "Q5 107478 bundle=absent")
          and has_line(blk, "Q6 nc=nil xpk=nil wpk=nil key=nil resp=nil")
          and has_line(blk, "Q7 daily table=absent"), " | ".join(blk[:4]))
    check("diag: no line of it is an error", not has_line(blk, "raised"), " | ".join(
        [ln for ln in blk if "raised" in ln]))
    check("diag: the mod is still armed and both doors still wrapped",
          has_line(lines, "g11 isunlockedwithid wrapped (2 of 2: PROGRESSION, LOOT)"))
    check("diag: and still answers with the payload it has",
          rt.eval("ASK_P(%d)" % ACCEPT[0]) is True)


def diag_neutral(lua51):
    def run(flag):
        rt = new_rt(lua51, src=False, pre=DIAGFIX + (" SET_TOGGLE('pt_diag', 1)" if flag else ""))
        lua_slabs(rt, slabs_of(ACCEPT + [126605]))
        rt.execute("SET_G11(11)")
        rt.execute('SET_PAID("v1;88929:999:999")')
        load(rt)
        pump(rt, 3)
        rt.execute('SET_PAID("v1;88929:1000:1000")')
        pump(rt, 20)
        pc, lc = int(rt.eval("PCALLS")), int(rt.eval("LCALLS"))
        ask = [rt.eval("ASK_P(%d)" % i) for i in ACCEPT]
        askl = [rt.eval("ASK_L(%d)" % i) for i in ACCEPT]
        touch = (int(rt.eval("PCALLS")) - pc, int(rt.eval("LCALLS")) - lc)
        events = [rt.eval("EV(%d).name" % i) for i in range(1, int(rt.eval("NEVENTS()")) + 1)]
        kept = [ln for ln in lines_of(rt)
                if "rc1diag:" not in ln and "door id=" not in ln and "lock door:" not in ln]
        return ask, askl, events, kept, touch

    off = run(False)
    on = run(True)
    check("diag: the doors answer identically with it on and off", off[0] == on[0] and off[1] == on[1],
          "%s vs %s" % (off[0][:3], on[0][:3]))
    check("diag: the events are the same, in the same order", off[2] == on[2], "%s vs %s" % (off[2], on[2]))
    check("diag: every other line is identical", off[3] == on[3],
          " | ".join(sorted(set(off[3]) ^ set(on[3]))[:3]))
    check("diag: a locked ask still never reaches the previous function, on or off",
          off[4] == on[4] and on[4] == (0, 0), "%s vs %s" % (off[4], on[4]))
    check("diag: a banner and its attachment card still draw with it on",
          "completed_challenge" in on[2] and "add_message_splash_manager" in on[2], str(on[2]))


def diag_match(lua51):
    rt = new_rt(lua51, frontend=False, pre=DIAGFIX + " SET_TOGGLE('pt_diag', 1)")
    pump(rt, 4)
    blk = rc1d_lines(lines_of(rt))
    check("diag: the match VM prints its own block, and says which VM it is",
          has_line(blk, "rc1diag: 1 block vm=match pt_diag=on:int=1"), " | ".join(blk[:2]))
    check("diag: the match block is closed and counted", rc1d_end(blk) == len(blk))
    n = len(blk)
    pump(rt, 40)
    check("diag: and prints once, not per tick", len(rc1d_lines(lines_of(rt))) == n, str(n))


def splashck_lines(lines):
    return [ln for ln in lines if "splashck:" in ln]


def splashck_arm(lua51):
    rt = new_rt(lua51, frontend=True, src=False)
    rt.execute(SPLASHFIX)
    load(rt)
    blk = splashck_lines(lines_of(rt))
    check("splashck: the block prints in the menu vm, seven numbered lines",
          len(blk) == 7, " | ".join(blk))
    check("splashck: the three native tables and the vm are named by type",
          has_line(blk, "splashck: 1 types vm=menu sm=table su=table hm=table"), " | ".join(blk[:1]))
    check("splashck: the splash datasource and the value behind it are both printed",
          has_line(blk, "splashck: 2 ds currentSplash=table value=empty_splash_ref"), " | ".join(blk[1:2]))
    check("splashck: the six type entries print their priority and their override flag",
          has_line(blk, "splashck: 3 mt ChallengeComplete=15/false DailyChallengeNotification=15/false "
                        "WeeklyChallengeSplashNotification=10/false")
          and has_line(blk, "splashck: 4 mt CamoChallenge=5/false WeaponLevel=28/false Medal=5/false"),
          " | ".join(blk[2:4]))
    check("splashck: the recon's getter and the native queue length are read",
          has_line(blk, "splashck: 5 active=false queue=2"), " | ".join(blk[4:5]))
    check("splashck: both headers are resolved by their readable key",
          has_line(blk, "splashck: 6 weekly=L:challenge/jup_ch_weekly_challenge_completed")
          and has_line(blk, "splashck: 7 daily=L:splashes/daily_challenge_completed"),
          " | ".join(blk[5:7]))
    check("splashck: twelve lines is the cap for one vm", len(blk) <= 12, str(len(blk)))


def splashck_absent(lua51):
    rt = new_rt(lua51)
    blk = splashck_lines(lines_of(rt))
    check("splashck: a vm with no splash natives still prints its block, and nothing raises",
          len(blk) == 7 and not has_line(blk, "raised"), " | ".join(blk))
    check("splashck: a nil parent prints nil instead of raising",
          has_line(blk, "splashck: 1 types vm=match sm=nil su=nil hm=nil")
          and has_line(blk, "splashck: 2 ds currentSplash=nil value=absent")
          and has_line(blk, "splashck: 3 mt ChallengeComplete=absent DailyChallengeNotification=absent "
                            "WeeklyChallengeSplashNotification=absent")
          and has_line(blk, "splashck: 5 active=absent queue=absent"), " | ".join(blk))


def splashck_slot(lua51):
    rt = new_rt(lua51, frontend=False, src=False)
    rt.execute(SPLASHFIX)
    load(rt)
    blk = splashck_lines(lines_of(rt))
    check("splashck: the match vm prints the same seven lines at arm",
          len(blk) == 7 and has_line(blk, "splashck: 1 types vm=match sm=table su=table hm=table"),
          " | ".join(blk[:1]))

    pump(rt, 8)
    check("splashck: an idle slot is not printed again",
          len(splashck_lines(lines_of(rt))) == 7, " | ".join(splashck_lines(lines_of(rt))[7:]))

    rt.execute('SET_SPLASH("global")')
    pump(rt, 24)
    check("splashck: a group two splash spends no transition",
          len(splashck_lines(lines_of(rt))) == 7, " | ".join(splashck_lines(lines_of(rt))[7:]))
    rt.execute('SET_SPLASH("empty_splash_ref")')
    pump(rt, 16)
    check("splashck: and its clear prints nothing either",
          len(splashck_lines(lines_of(rt))) == 7, " | ".join(splashck_lines(lines_of(rt))[7:]))

    rt.execute('SET_SPLASH("weeklyChallengeSplashNotification")')
    pump(rt, 8)
    check("splashck: the first true from the recon's getter carries the value it read",
          has_line(splashck_lines(lines_of(rt)),
                   "splashck: 8 during vm=match active=true "
                   "splash=weeklyChallengeSplashNotification queue=2"),
          " | ".join(splashck_lines(lines_of(rt))[7:]))

    rt.execute('SET_SPLASH("empty_splash_ref")')
    pump(rt, 16)
    after = splashck_lines(lines_of(rt))
    check("splashck: the clear after it is printed once, and then the slot is silent",
          has_line(after, "splashck: 9 after vm=match active=false splash=empty_splash_ref queue=2")
          and len(after) == 9, " | ".join(after[8:]))
    check("splashck: the match vm stays inside the twelve line cap", len(after) <= 12, str(len(after)))


def splashck_late(lua51):
    rt = new_rt(lua51, frontend=True, src=False)
    rt.execute("LUI = nil")
    load(rt)
    blk = splashck_lines(lines_of(rt))
    check("splashck: with no LUI at arm the block still prints, and says the tables are nil",
          len(blk) == 7 and has_line(blk, "splashck: 1 types vm=menu sm=nil su=nil hm=nil"),
          " | ".join(blk[:1]))

    rt.execute("LUI = { [xhash('GetRoot')] = function() return ROOT end }")
    rt.execute(SPLASHFIX)
    rt.eval("rawget(_G, 'ProgressionTuning').hooks.diag()")
    late = splashck_lines(lines_of(rt))
    check("splashck: the first timer step re-prints it once the hud exists",
          has_line(late, "splashck: 8 late vm=menu sm=table su=table hm=table")
          and has_line(late, "splashck: 9 late mt ChallengeComplete=15/false "
                             "WeeklyChallengeSplashNotification=10/false Medal=5/false")
          and has_line(late, "splashck: 10 late active=false queue=2"), " | ".join(late[7:]))

    rt.eval("rawget(_G, 'ProgressionTuning').hooks.diag()")
    check("splashck: and only once - a second step adds nothing",
          len(splashck_lines(lines_of(rt))) == 10, " | ".join(splashck_lines(lines_of(rt))[10:]))
    check("splashck: ten lines for a vm that armed without LUI, inside the cap",
          len(splashck_lines(lines_of(rt))) <= 12)


def splashck_order(lua51):
    rt = new_rt(lua51, frontend=True, src=False)
    rt.execute(SPLASHFIX)
    raised = ""
    try:
        load(rt)
    except Exception as exc:
        raised = str(exc)
    lines = lines_of(rt)
    blk = splashck_lines(lines)
    check("order: the eight parts load in %s order with nothing raised" % LOAD_ORDER,
          raised == "", raised[:160])
    check("order: the diag part announces its arm once in %s order" % LOAD_ORDER,
          count_line(lines, "part diag armed") == 1,
          " | ".join(ln for ln in lines if "part diag armed" in ln))
    check("order: no lua error is printed in %s order" % LOAD_ORDER,
          not has_line(lines, "attempt to call field") and not has_line(lines, "Lua Error"),
          " | ".join(ln for ln in lines if "attempt to call field" in ln)[:160])
    check("order: the diag splash check prints its seven lines in %s order" % LOAD_ORDER,
          len(blk) == 7 and has_line(blk, "splashck: 1 types vm=menu sm=table su=table hm=table"),
          " | ".join(blk))


def clock(rt):
    return int(rt.eval("rawget(_G, 'ProgressionTuning').tick"))


def dispatches(rt, n):
    """(tick, events added) for every timer step that drew something."""
    out = []
    seen = int(rt.eval("NEVENTS()"))
    for _ in range(n):
        pump(rt, 1)
        now = int(rt.eval("NEVENTS()"))
        if now > seen:
            out.append((clock(rt), now - seen))
            seen = now
    return out


def card_lines(lines):
    return [ln for ln in lines if "splashck: card " in ln]


def snd_lines(lines):
    return [ln for ln in lines if "splashck: snd " in ln and "snd capped" not in ln]


def splash_side(lua51):
    rt = pair(lua51)
    rt.execute('SET_SPLASHNOW("weaponProgression")')
    rt.execute('SET_PAID("v1;88929:1000:1000")')
    marks = dispatches(rt, 20)
    check("side: the xp side panel is not a busy slot",
          len(marks) == 1 and marks[0][1] == 2, str(marks))
    check("side: so the level card and its unlock go out together",
          drawn(rt, 2) == [("completed_challenge", 54499), ("add_message_splash_manager", None)],
          str(drawn(rt, 2)))

    rk = pair(lua51)
    rk.execute('SET_SPLASHNOW("rankProgression")')
    rk.execute('SET_PAID("v1;88929:1000:1000")')
    kmarks = dispatches(rk, 20)
    check("side: and neither is the rank unlock alias of the same widget",
          len(kmarks) == 1 and kmarks[0][1] == 2, str(kmarks))

    rh = pair(lua51)
    rh.execute('SET_SPLASHNOW("medal")')
    rh.execute('SET_PAID("v1;88929:1000:1000")')
    pump(rh, 20)
    check("side: a held slot still holds the side panel with its card",
          rh.eval("NEVENTS()") == 0, str(rh.eval("NEVENTS()")))


SOUNDFIX = r"""
CHAL_SOUNDS = { challengeSplash = { generalChallenge = "uin_jup_challenge_complete",
                                    camoChallenge = "uin_jup_challenge_camo_unlock" } }
SOUND_SETS = nil
function WITH_SOUNDS()
  SOUND_SETS = CHAL_SOUNDS
  CHAL_SOUNDS.challengeSplash.generalChallenge = "client_weekly_alias"
end
"""


def card_sounds(lua51):
    PRE = WeeklyStub + WEEKLYLOOK + SOUNDFIX
    rt = new_rt(lua51, src=False)
    rt.execute(PRE)
    rt.execute("Challenge[xhash('getrewards')] = nil")
    rt.execute("SET_WEEKLY_FLAT(60330, '3', 'sat_weekly_zm_s1w1_kills', 1)")
    rt.execute("SET_CHAL_PROGRESS(60330, 1)")
    rt.execute("SET_G11(180)")
    load(rt)
    pump(rt, 12)
    rt.execute("SET_CHAL_PROGRESS(60330, 3)")
    pump(rt, 40)
    check("S: the weekly route B card carries the alias the client plays for its kind",
          rt.eval("EV(1).options.sound") == "uin_jup_challenge_complete",
          repr(rt.eval("EV(1).options.sound")))

    rw = new_rt(lua51, src=False)
    rw.execute(PRE)
    rw.execute("WITH_SOUNDS()")
    rw.execute("SET_WEEKLY_FLAT(60330, '3', 'sat_weekly_zm_s1w1_kills', 1)")
    rw.execute("SET_CHAL_PROGRESS(60330, 1)")
    rw.execute("SET_G11(181)")
    load(rw)
    pump(rw, 12)
    rw.execute("SET_CHAL_PROGRESS(60330, 3)")
    pump(rw, 40)
    check("S: and the client own table wins when this vm can reach it",
          rw.eval("EV(1).options.sound") == "client_weekly_alias",
          repr(rw.eval("EV(1).options.sound")))

    rc = new_rt(lua51, src=False)
    rc.execute(CAMOSTUB + SOUNDFIX)
    rc.execute("SET_CAMOQ(false)")
    rc.execute("SET_CAMO_ROW('sat_pi_atlas', 57201, {100, 200, 300})")
    rc.execute("SET_CAMO_PROGRESS(57201, 90)")
    rc.execute("SET_G11(182)")
    rc.execute('SET_PAID("v1;88929:900:1")')
    load(rc)
    pump(rc, 16)
    rc.execute("SET_CAMO_PROGRESS(57201, 100)")
    pump(rc, 40)
    check("S: the camo route B card carries the camo alias",
          rc.eval("LASTOF('add_message_splash_manager').options.sound")
          == "uin_jup_challenge_camo_unlock",
          repr(rc.eval("LASTOF('add_message_splash_manager').options.sound")))

    ra = pair(lua51)
    ra.execute('SET_PAID("v1;88929:1000:1000")')
    pump(ra, 40)
    check("S: a route A level call is unchanged - no sound and no options",
          ra.eval("LASTOF('completed_challenge').options") is None
          and ra.eval("LASTOF('completed_challenge').sound") is None
          and int(ra.eval("LASTOF('completed_challenge').kind")) == 398
          and int(ra.eval("LASTOF('completed_challenge').controller")) == 0,
          str(ra.eval("LASTOF('completed_challenge')")))

    rd = new_rt(lua51, src=False)
    rd.execute(WeeklyStub + WEEKLYLOOK + SOUNDFIX)
    rd.execute("SET_DAILY_ROW(53310, '75', 'sat_daily_zm_ch_p1_kills_melee')")
    rd.execute("SET_CHAL_PROGRESS(53310, 40)")
    rd.execute("SET_G11(183)")
    load(rd)
    pump(rd, 12)
    rd.execute("SET_CHAL_PROGRESS(53310, 75)")
    pump(rd, 40)
    check("S: a route A daily call is unchanged - no sound and no options",
          rd.eval("NAMED('completed_challenge')") == 1
          and rd.eval("LASTOF('completed_challenge').options") is None
          and rd.eval("LASTOF('completed_challenge').sound") is None,
          str(rd.eval("LASTOF('completed_challenge')")))


SNDQ = r"""
SNDNOW = 1000
function SET_SNDNOW(v) SNDNOW = v end
CLIENT_SOUND = "uin_jup_challenge_complete"
function SET_CLIENT_SOUND(v) CLIENT_SOUND = v end
Engine[xhash("GetMilliseconds")] = function() return SNDNOW end
SOUND_SETS = { challengeSplash = { generalChallenge = "uin_jup_challenge_complete",
                                   camoChallenge = "uin_jup_challenge_camo_unlock" } }
_DataSources = { settings = { gamer_profile = { notification_feed_opacity =
  { GetValue = function(self, c) return 1 end } } } }
MSGQ = {}
PE = LUI[xhash("UIRoot")][xhash("ProcessEvent")]
LUI[xhash("UIRoot")][xhash("ProcessEvent")] = function(root, ev)
  PE(root, ev)
  if ev.name == "add_message_splash_manager" and ev.options ~= nil then
    MSGQ[#MSGQ + 1] = { options = ev.options, insertTime = SNDNOW }
  elseif ev.name == "completed_challenge" then
    local loc = "dailyNotification"
    if tonumber(ev.kind) == 398 then loc = "weaponLevel" end
    MSGQ[#MSGQ + 1] = { options = { displayLocation = loc, sound = CLIENT_SOUND },
                        insertTime = SNDNOW }
  end
  return true
end
LUI.HudManager = { GetInstance = function()
  return { activeHud = { splashManager = { widgetMap = WM, messageQueue = MSGQ } } } end }
function SNDQ_NEWEST() return MSGQ[#MSGQ] end
"""


def snd_line(lua51):
    rt = pair(lua51, SNDQ)
    rt.execute('SET_PAID("v1;88929:1000:1000")')
    pump(rt, 20)
    check("snd: the level card's line carries the sound the widget was handed",
          has_line(snd_lines(lines_of(rt)),
                   "splashck: snd 1 kind=level id=54499 sound=uin_jup_challenge_complete"
                   " aliases=uin_jup_challenge_complete opacity=1"),
          " | ".join(snd_lines(lines_of(rt))))

    re_ = pair(lua51, SNDQ)
    re_.execute('SET_CLIENT_SOUND("")')
    re_.execute('SET_PAID("v1;88929:1000:1000")')
    pump(re_, 20)
    check("snd: an empty alias the builder hands over is printed as none",
          has_line(snd_lines(lines_of(re_)), "kind=level id=54499 sound=none"),
          " | ".join(snd_lines(lines_of(re_))))

    ra = pair(lua51, SNDQ)
    ra.execute("SOUND_SETS = nil")
    ra.execute('SET_PAID("v1;88929:1000:1000")')
    pump(ra, 20)
    check("snd: with no client table in this vm the line says the alias is absent",
          has_line(snd_lines(lines_of(ra)), "aliases=absent"),
          " | ".join(snd_lines(lines_of(ra))))

    ro = pair(lua51, SNDQ)
    ro.execute("_DataSources = nil")
    ro.execute("DataSources = nil")
    ro.execute('SET_PAID("v1;88929:1000:1000")')
    pump(ro, 20)
    check("snd: with no profile datasource the line says the gate is absent",
          has_line(snd_lines(lines_of(ro)), "opacity=absent"),
          " | ".join(snd_lines(lines_of(ro))))

    rb = new_rt(lua51, src=False)
    rb.execute(SPLASHQ)
    load(rb)
    for kind in ("camoA", "ret", "attach", "wkxp"):
        rb.execute("rawget(_G, 'ProgressionTuning').hooks.card('%s', 7, 0, 'a')" % kind)
    check("snd: only the four sound bearing kinds get a line",
          count_line(lines_of(rb), "splashck: snd ") == 0, " | ".join(snd_lines(lines_of(rb))))

    rh = new_rt(lua51, src=False)
    rh.execute(SPLASHQ)
    load(rh)
    for i in range(1, 22):
        rh.execute("rawget(_G, 'ProgressionTuning').hooks.card('camoB', %d, 0, 'a')" % i)
    check("snd: twenty lines per vm and no more",
          len(snd_lines(lines_of(rh))) == 20,
          str(len(snd_lines(lines_of(rh)))))
    check("snd: with one cap line after the twentieth",
          count_line(lines_of(rh), "splashck: snd capped at 20") == 1
          and has_line(lines_of(rh), "splashck: snd 20 kind=camoB id=20"),
          " | ".join(snd_lines(lines_of(rh))[-2:]))


SNDOPTS = r"""
SNDNOW = 1000
CLIENT_SOUND = "alias_from_widget"
function SET_CLIENT_SOUND(v) CLIENT_SOUND = v end
NOPLAY = false
function SET_NOPLAY(v) NOPLAY = (v == true) end
Engine[xhash("GetMilliseconds")] = function() return SNDNOW end
NPLAY = 0
Engine[xhash("PlaySound")] = function(a)
  NPLAY = NPLAY + 1
  return 8000 + NPLAY
end
Engine[xhash("IsSoundPlaying")] = function(id) return false end
Engine[xhash("GetSoundLengthMS")] = function(id) return 900 end
SOUND_SETS = { challengeSplash = { generalChallenge = "uin_jup_challenge_complete",
                                   camoChallenge = "uin_jup_challenge_camo_unlock" } }
_DataSources = { settings = { gamer_profile = { notification_feed_opacity =
  { GetValue = function(self, c) return 1 end } } } }
QEMPTY = {}
WINNING = {}
PE = LUI[xhash("UIRoot")][xhash("ProcessEvent")]
LUI[xhash("UIRoot")][xhash("ProcessEvent")] = function(root, ev)
  PE(root, ev)
  if NOPLAY then return true end
  if ev.name == "add_message_splash_manager" and ev.options ~= nil
     and ev.options.sound ~= nil then
    Engine[xhash("PlaySound")](ev.options.sound)
  elseif ev.name == "completed_challenge" then
    Engine[xhash("PlaySound")](CLIENT_SOUND)
  end
  return true
end
LUI.HudManager = { GetInstance = function()
  return { activeHud = { splashManager = { widgetMap = WINNING, messageQueue = QEMPTY } } } end }
function NPLAYED() return NPLAY end
function QLEN() return #QEMPTY end
"""


def snd_engine(lua51):
    rt = pair(lua51, SNDOPTS)
    rt.execute('SET_PAID("v1;88929:1000:1000")')
    pump(rt, 20)
    got = snd_lines(lines_of(rt))
    check("snd: the engine plays the card's alias but no line reads it back",
          int(rt.eval("NPLAYED()")) >= 1 and has_line(got, "kind=level id=54499 sound=unread"),
          " | ".join(got))
    check("snd: so the line carries no engine capture and no source field",
          "src=" not in "".join(got) and not has_line(got, "alias_from_widget"),
          " | ".join(got))

    rz = pair(lua51, SNDOPTS)
    rz.execute("SET_NOPLAY(true)")
    rz.execute('SET_PAID("v1;88929:1000:1000")')
    pump(rz, 20)
    zl = snd_lines(lines_of(rz))
    check("snd: with nothing played the line reads the same - the queue is unread",
          has_line(zl, "kind=level id=54499 sound=unread")
          and has_line(got, "kind=level id=54499 sound=unread"),
          " | ".join(zl))


def diag_switch(lua51):
    off = new_rt(lua51, frontend=False, pre=DIAGFIX + " SET_TOGGLE('pt_diag', 1) "
                 "SET_TOGGLE('pt_diag_off', 1)")
    pump(off, 20)
    ol = lines_of(off)
    check("diagoff: the switch stops the block and the check block before either runs",
          not rc1d_lines(ol) and not has_line(ol, "splashck:"), " | ".join(ol[-3:]))
    check("diagoff: and it says so once", count_line(ol, "diag off") == 1,
          str(count_line(ol, "diag off")))

    on = new_rt(lua51, frontend=False, pre=DIAGFIX + " SET_TOGGLE('pt_diag', 1)")
    pump(on, 20)
    check("diagoff: without the switch the same vm prints the block and never says it is off",
          bool(rc1d_lines(lines_of(on))) and count_line(lines_of(on), "diag off") == 0,
          " | ".join(lines_of(on)[:2]))


def drawn(rt, n):
    """The first n events as (name, id), the id None when the event carries none."""
    out = []
    for i in range(1, n + 1):
        nm = rt.eval("(function() local e = EVENTS[%d] if e == nil then return 'none' end "
                     "return tostring(e.name) end)()" % i)
        idv = rt.eval("(function() local e = EVENTS[%d] if e == nil then return nil end "
                      "return e.id end)()" % i)
        out.append((str(nm), None if idv is None else int(idv)))
    return out


def pair(lua51, extra=""):
    """A vm primed at 999, ready to cross 1000 and draw the level and its item."""
    rt = new_rt(lua51, src=False)
    rt.execute(SPLASHQ)
    if extra:
        rt.execute(extra)
    rt.execute('SET_PAID("v1;88929:999:999")')
    load(rt)
    pump(rt, 10)
    return rt


def splash_slot(lua51):
    rt = pair(lua51)
    check("pace: nothing is drawn before a crossing", rt.eval("NEVENTS()") == 0,
          str(rt.eval("NEVENTS()")))
    rt.execute('SET_SPLASHNOW("medal")')
    rt.execute('SET_PAID("v1;88929:1000:1000")')
    pump(rt, 20)
    check("pace: a group one splash holds the card we queued", rt.eval("NEVENTS()") == 0,
          str(rt.eval("NEVENTS()")))
    mark = clock(rt)
    rt.execute('SET_SPLASHNOW("empty_splash_ref")')
    marks = dispatches(rt, 24)
    check("pace: it goes out on the first tick the slot is clear",
          len(marks) >= 1 and marks[0][0] == mark + 1, str(marks))
    check("pace: the level banner is the card that went first",
          drawn(rt, 1) == [("completed_challenge", 54499)], str(drawn(rt, 1)))
    check("pace: the item it unlocked rides the level card's own tick",
          len(marks) == 1 and marks[0][1] == 2, str(marks))
    check("pace: and that side card is the client's own immediate thirty",
          int(rt.eval("EVENTS[2].options.displayTimeOverride")) == 30
          and rt.eval("EVENTS[2].immediate") is True
          and rt.eval("EVENTS[2].options.displayLocation") == "weaponProgression",
          str(rt.eval("EVENTS[2].options")))
    cards = card_lines(lines_of(rt))
    check("pace: the card line names the kind, the id, the wait and the rule",
          has_line(cards, "splashck: card 1 kind=level id=54499 wait=")
          and has_line(cards, "rule=a"), " | ".join(cards))


def splash_group(lua51):
    rt = pair(lua51)
    rt.execute('SET_SPLASHNOW("global")')
    rt.execute('SET_PAID("v1;88929:1000:1000")')
    marks = dispatches(rt, 24)
    check("pace: a group two splash never holds our queue", len(marks) >= 1, str(marks))
    check("pace: and the pair still rides one tick",
          len(marks) == 1 and marks[0][1] == 2, str(marks))
    check("pace: the card line says the slot was clear",
          has_line(card_lines(lines_of(rt)), "rule=a"), " | ".join(card_lines(lines_of(rt))))

    rt2 = pair(lua51)
    rt2.execute('SET_WM("aWidgetMapOnlyType", 2)')
    rt2.execute('SET_SPLASHNOW("aWidgetMapOnlyType")')
    rt2.execute('SET_PAID("v1;88929:1000:1000")')
    check("pace: the widget map decides the group when it answers",
          len(dispatches(rt2, 20)) >= 1, "the widget map read was not used")

    rt3 = pair(lua51)
    rt3.execute('SET_WM("weaponLevel", 1)')
    rt3.execute('SET_SPLASHNOW("weaponLevel")')
    rt3.execute('SET_PAID("v1;88929:1000:1000")')
    pump(rt3, 20)
    check("pace: and a group one answer from the widget map still holds",
          rt3.eval("NEVENTS()") == 0, str(rt3.eval("NEVENTS()")))


def splash_floor(lua51):
    rt = pair(lua51)
    rt.execute("DS_THROW(true)")
    rt.execute('SET_PAID("v1;88929:1000:1000")')
    marks = dispatches(rt, 30)
    check("pace: with the read raising the card still goes out", len(marks) >= 1, str(marks))
    check("pace: and its side card still rides the same tick",
          len(marks) == 1 and marks[0][1] == 2, str(marks))
    check("pace: the card line names the floor, not the slot",
          has_line(card_lines(lines_of(rt)), "rule=b"), " | ".join(card_lines(lines_of(rt))))


def splash_cap(lua51):
    rt = pair(lua51)
    rt.execute('SET_SPLASHNOW("medal")')
    rt.execute('SET_PAID("v1;88929:1000:1000")')
    mark = clock(rt)
    check("pace: a stuck read holds the card well below the cap",
          dispatches(rt, 30) == [], "it drew before the cap")
    marks = dispatches(rt, 14)
    check("pace: the cap releases the stuck read", len(marks) == 1, str(marks))
    check("pace: and not before the native hold has run out",
          len(marks) == 1 and marks[0][0] - mark >= 34, str(marks))
    check("pace: the card line names the cap",
          has_line(card_lines(lines_of(rt)), "rule=c"), " | ".join(card_lines(lines_of(rt))))


def splash_priority(lua51):
    rt = pair(lua51)
    rt.execute('SET_PAID("v1;88929:1000:1000")')
    pump(rt, 40)
    check("prio: the attachment card carries the native progression priority",
          int(rt.eval("LASTOF('add_message_splash_manager').options.priority")) == 27,
          str(rt.eval("LASTOF('add_message_splash_manager').options.priority")))

    rt2 = new_rt(lua51, src=False)
    rt2.execute(CAMOSTUB)
    rt2.execute(SPLASHQ)
    rt2.execute("SET_CAMOQ(false)")
    rt2.execute("SET_CAMO_ROW('sat_pi_atlas', 57201, {100, 200, 300})")
    rt2.execute("SET_CAMO_PROGRESS(57201, 90)")
    rt2.execute("SET_G11(241)")
    rt2.execute('SET_PAID("v1;88929:900:1")')
    load(rt2)
    pump(rt2, 16)
    rt2.execute("SET_CAMO_PROGRESS(57201, 100)")
    pump(rt2, 40)
    check("prio: the camo card on route B outranks a medal, five no longer",
          has_line(lines_of(rt2), "camo card id=57201 row=sat_pi_atlas target=100 route=B")
          and int(rt2.eval("LASTOF('add_message_splash_manager').options.priority")) == 15,
          str(rt2.eval("LASTOF('add_message_splash_manager').options.priority")))


def splash_order(lua51):
    PRE = CAMOSTUB + """
DAILYLIST = {}
WEEKLYLIST = {}
function SET_DAILY(id, amount, ref)
  DAILYLIST[#DAILYLIST + 1] = { id = id, amount = amount, ref = ref, kind = 438 }
end
Challenge[xhash("getchallengesforcurrentgamemode")] = function(c) return DAILYLIST end
Challenge[xhash("getweeklychallenges")] = function(c, kind) return WEEKLYLIST end
Challenge[xhash("GetAEKindID")] = function(name) return 7000 end
function SET_CHAL_PROGRESS(id, v) OC[tostring(id)] = { xp = v, rank = 0 } end
"""
    rt = new_rt(lua51, src=False)
    rt.execute(PRE)
    rt.execute(SPLASHQ)
    rt.execute("PROGRESSION[xhash('isweaponprogressionchallenge')] = "
               "function(kind, id) return tostring(id) == '54499' end")
    rt.execute("SET_DAILY(53310, '75', 'sat_daily_zm_ch_p1_kills_melee')")
    rt.execute("SET_CHAL_PROGRESS(53310, 40)")
    rt.execute("SET_CAMO_ROW('sat_pi_atlas', 57201, {100, 200, 300})")
    rt.execute("SET_CAMO_PROGRESS(57201, 90)")
    rt.execute("SET_G11(242)")
    rt.execute('SET_PAID("v1;88929:900:1")')
    load(rt)
    pump(rt, 16)
    rt.execute('SET_SPLASHNOW("medal")')
    rt.execute("SET_CHAL_PROGRESS(53310, 75)")
    pump(rt, 12)
    rt.execute("SET_CAMO_PROGRESS(57201, 100)")
    rt.execute('SET_PAID("v1;88929:1000:1000")')
    pump(rt, 12)
    check("order: the held slot keeps every card in the queue",
          rt.eval("NEVENTS()") == 0, " | ".join(lines_of(rt)[-3:]))
    rt.execute('SET_SPLASHNOW("empty_splash_ref")')
    pump(rt, 90)
    seen = drawn(rt, 4)
    check("order: the level and its unlock go before the camo and the daily",
          seen == [("completed_challenge", 54499), ("add_message_splash_manager", None),
                   ("completed_challenge", 57201), ("completed_challenge", 53310)], str(seen))
    l = lines_of(rt)
    check("order: every one of the four was drawn, each with its own line",
          count_line(l, "level sat_pi_atlas crossed 1 row 54499") == 1
          and count_line(l, "attachment 88649") == 1
          and count_line(l, "camo card id=57201") == 1
          and count_line(l, "daily card id=53310") == 1, " | ".join(card_lines(l)))
    cards = card_lines(l)
    check("order: the queue names one line per centre card and no side panel",
          len(cards) == 3 and has_line(cards, "kind=level") and has_line(cards, "kind=camoA")
          and has_line(cards, "kind=chalD") and not has_line(cards, "kind=attach"),
          " | ".join(cards))

    rt.execute("CLEAR()")
    rt.execute("SET_CAMO_PROGRESS(57201, 300)")
    pump(rt, 60)
    l = lines_of(rt)
    first = next((i for i, ln in enumerate(l) if "camo card id=57201" in ln and "target=200" in ln), None)
    second = next((i for i, ln in enumerate(l) if "camo card id=57201" in ln and "target=300" in ln), None)
    check("order: two tiers of one row keep their own first in first out order",
          first is not None and second is not None and first < second, "%s %s" % (first, second))


WEEKLYLOOK = """
LOCMODE = "ok"
LOCHEAD = "SIGMA WEEKLY"
function SET_LOCMODE(m) LOCMODE = m end
Engine[xhash("Localize")] = function(k, a)
  if k == "" then return "" end
  if LOCMODE == "raise" then error("no localize table") end
  if LOCMODE == "key" then return k end
  if a ~= nil then return "B:" .. tostring(k) .. "@" .. tostring(a) end
  return LOCHEAD
end
Challenge[xhash("isweeklychallengetype")] = function(k) return k == 585 end
"""


def weekly_look(lua51):
    PRE = WeeklyStub + WEEKLYLOOK
    rt = new_rt(lua51, src=False)
    rt.execute(PRE)
    rt.execute("SET_DAILY_ROW(53310, '75', 'sat_daily_zm_ch_p1_kills_melee')")
    rt.execute("SET_WEEKLY_FLAT(60330, '3|6', 'sat_weekly_zm_s1w1_kills', 1)")
    rt.execute("SET_CHAL_PROGRESS(53310, 40)")
    rt.execute("SET_CHAL_PROGRESS(60330, 1)")
    rt.execute("SET_G11(160)")
    load(rt)
    pump(rt, 12)
    check("W: no header line is printed before a weekly card is drawn",
          not has_line(lines_of(rt), "weekly header"), " | ".join(lines_of(rt)[-4:]))
    rt.execute("SET_CHAL_PROGRESS(60330, 6)")
    marks = dispatches(rt, 60)
    l = lines_of(rt)
    check("W: a weekly crossing draws the client's own splash message, not completed_challenge",
          rt.eval("NAMED('add_message_splash_manager')") == 2
          and rt.eval("NAMED('completed_challenge')") == 0,
          "%s / %s" % (rt.eval("NAMED('add_message_splash_manager')"),
                       rt.eval("NAMED('completed_challenge')")))
    check("W: and that message is the daily card type at the daily priority, with no id, icon or camo flag",
          rt.eval("EV(1).options.displayLocation") == "dailyNotification"
          and int(rt.eval("EV(1).options.priority")) == 15
          and rt.eval("EV(1).options.splashId") is None
          and rt.eval("EV(1).options.camoUnlocked") is None
          and rt.eval("EV(1).options.icon") is None,
          "%s / %s" % (rt.eval("EV(1).options.displayLocation"), rt.eval("EV(1).options.priority")))
    check("W: the header is the title the client resolved from the native hash",
          rt.eval("EV(1).options.headerText") == "SIGMA WEEKLY"
          and count_line(l, "weekly header native=SIGMA WEEKLY") == 1,
          " | ".join([x for x in l if "weekly header" in x][:2]))
    check("W: the subtitle is the description localised with the number passed plain",
          rt.eval("EV(1).options.bodyText") == "B:desc 60330@3"
          and rt.eval("EV(2).options.bodyText") == "B:desc 60330@6",
          "%s / %s" % (rt.eval("EV(1).options.bodyText"), rt.eval("EV(2).options.bodyText")))
    check("W: one line names the weekly card and its route",
          has_line(l, "weekly card id=60330 row=sat_weekly_zm_s1w1_kills kind=585 target=3 value=6 route=B")
          and has_line(l, "weekly card id=60330 row=sat_weekly_zm_s1w1_kills kind=585 target=6 value=6 route=B"),
          " | ".join([x for x in l if "weekly card" in x][:2]))
    check("W: the card line names the kind the card actually drew",
          has_line(card_lines(l), "kind=chalWB id=60330"), " | ".join(card_lines(l)))
    check("W: the two tiers of one row go out one daily airtime apart, not one weekly",
          len(marks) == 2 and marks[1][0] - marks[0][0] >= 16, str(marks))
    check("W: the header line is printed once per vm", count_line(l, "weekly header") == 1,
          str(count_line(l, "weekly header")))

    for mode, want_body in (("raise", ""), ("key", "desc 60330")):
        rf = new_rt(lua51, src=False)
        rf.execute(PRE)
        rf.execute("SET_LOCMODE('%s')" % mode)
        rf.execute("SET_WEEKLY_FLAT(60330, '3', 'sat_weekly_zm_s1w1_kills', 1)")
        rf.execute("SET_CHAL_PROGRESS(60330, 1)")
        rf.execute("SET_G11(162)")
        load(rf)
        pump(rf, 12)
        rf.execute("SET_CHAL_PROGRESS(60330, 3)")
        pump(rf, 40)
        lf = lines_of(rf)
        check("W: the resolve %s falls back to our literal and says so once" % mode,
              rf.eval("NAMED('add_message_splash_manager')") == 1
              and rf.eval("EV(1).options.headerText") == "WEEKLY CHALLENGE COMPLETE"
              and count_line(lf, "weekly header=none") == 1
              and not has_line(lf, "weekly header native="),
              " | ".join([x for x in lf if "weekly header" in x][:2]))
        check("W: and the subtitle it could not localise never shows a key - %s" % mode,
              rf.eval("EV(1).options.bodyText") == want_body, str(rf.eval("EV(1).options.bodyText")))

    rd = new_rt(lua51, src=False)
    rd.execute(PRE)
    rd.execute("SET_DAILY_ROW(53310, '75', 'sat_daily_zm_ch_p1_kills_melee')")
    rd.execute("SET_CHAL_PROGRESS(53310, 40)")
    rd.execute("SET_G11(163)")
    load(rd)
    pump(rd, 12)
    rd.execute("SET_CHAL_PROGRESS(53310, 75)")
    pump(rd, 40)
    ld = lines_of(rd)
    check("W: a daily crossing is untouched - the client's own completed_challenge, kind 438",
          rd.eval("NAMED('completed_challenge')") == 1
          and rd.eval("NAMED('add_message_splash_manager')") == 0
          and int(rd.eval("LASTOF('completed_challenge').kind")) == 438
          and has_line(ld, "daily card id=53310 row=sat_daily_zm_ch_p1_kills_melee kind=438 target=75"),
          " | ".join([x for x in ld if "daily card" in x][:2]))
    check("W: and a daily never resolves the weekly header",
          not has_line(ld, "weekly header") and has_line(card_lines(ld), "kind=chalD id=53310"),
          " | ".join([x for x in ld if "weekly header" in x][:2]))

    rp = new_rt(lua51, src=False)
    rp.execute(PRE)
    rp.execute(SPLASHQ)
    rp.execute("PROGRESSION[xhash('isweaponprogressionchallenge')] = "
               "function(kind, id) return tostring(id) == '54499' end")
    rp.execute("SET_WEEKLY_FLAT(60330, '3', 'sat_weekly_zm_s1w1_kills', 1)")
    rp.execute("SET_CHAL_PROGRESS(60330, 1)")
    rp.execute("SET_G11(164)")
    rp.execute('SET_PAID("v1;88929:900:1")')
    load(rp)
    pump(rp, 12)
    rp.execute('SET_SPLASHNOW("medal")')
    rp.execute("SET_CHAL_PROGRESS(60330, 3)")
    pump(rp, 8)
    rp.execute('SET_PAID("v1;88929:1000:1000")')
    pump(rp, 8)
    check("W: a weekly queued first behind a held slot still waits",
          rp.eval("NEVENTS()") == 0, str(rp.eval("NEVENTS()")))
    rp.execute('SET_SPLASHNOW("empty_splash_ref")')
    pump(rp, 90)
    seen = drawn(rp, 3)
    check("W: and it goes out last, after the level banner and the item it unlocked",
          seen == [("completed_challenge", 54499), ("add_message_splash_manager", None),
                   ("add_message_splash_manager", None)], str(seen))
    check("W: that last one is the weekly on the daily type",
          rp.eval("LASTOF('add_message_splash_manager').options.displayLocation") == "dailyNotification"
          and has_line(card_lines(lines_of(rp)), "kind=chalWB id=60330"),
          str(rp.eval("LASTOF('add_message_splash_manager').options.displayLocation")))


WEEKLYGAP = r"""
SUB = { text = "" }
SUBTEXT = { setText = function(self, v, t) SUB.text = v end }
WM = { dailyNotification = { groupId = 1,
                            widget = { SplashTrapSubheader = { matchobjectivetext = SUBTEXT } } } }
LUI.SplashUtils = { EmptySplashRef = "empty_splash_ref" }
LUI.HudManager = { GetInstance = function()
  return { activeHud = { splashManager = { widgetMap = WM } } } end }
LUI[xhash("UIRoot")] = { [xhash("ProcessEvent")] = function(root, ev)
  EVENTS[#EVENTS + 1] = ev
  if ev.name == "add_message_splash_manager" and ev.options ~= nil
     and ev.options.displayLocation == "dailyNotification" then
    local b = ev.options.bodyText
    if b ~= nil and b ~= "" then SUB.text = b end
  end
  return true
end }
function SET_SUB(v) SUB.text = v end
function EVLOC(loc)
  local i = 1
  while i <= #EVENTS do
    local e = EVENTS[i]
    if e.options ~= nil and e.options.displayLocation == loc then return e end
    i = i + 1
  end
  return nil
end
function EVIDX(loc)
  local i = 1
  while i <= #EVENTS do
    local e = EVENTS[i]
    if e.options ~= nil and e.options.displayLocation == loc then return i end
    i = i + 1
  end
  return 0
end
BODYMODE = "none"
function SET_BODYMODE(m) BODYMODE = m end
RECBODY = nil
Challenge[xhash("getdesclocalizedbyid")] = function(c, id, kind)
  RECBODY = { c = c, id = id, kind = kind }
  if BODYMODE == "native" then return "ELIMINATE AN ELITE ZOMBIE" end
  if BODYMODE == "long" then return string.rep("Z", 60) end
  return ""
end
REWARDS = nil
function SET_REWARDS() REWARDS = { { type = "xp", image = "icon_xp_tokens", name = "5000 XP",
                                     amount = "5000" } } end
Challenge[xhash("getrewards")] = function(chal, kind, c) return REWARDS end
"""


def weekly_gaps(lua51):
    PRE = WeeklyStub + WEEKLYLOOK + WEEKLYGAP

    rt = new_rt(lua51, src=False)
    rt.execute(PRE)
    rt.execute("SET_BODYMODE('native')")
    rt.execute("SET_WEEKLY_FLAT(60330, '3', 'sat_weekly_zm_s1w1_kills', 1)")
    rt.execute("SET_CHAL_PROGRESS(60330, 1)")
    rt.execute("SET_G11(170)")
    load(rt)
    pump(rt, 12)
    rt.execute("SET_CHAL_PROGRESS(60330, 3)")
    pump(rt, 60)
    l = lines_of(rt)
    check("G1: the subtitle is the one the client's own call answers",
          rt.eval("EV(1).options.bodyText") == "ELIMINATE AN ELITE ZOMBIE"
          and has_line(l, "weekly body=ELIMINATE AN ELITE ZOMBIE"),
          "%s | %s" % (rt.eval("EV(1).options.bodyText"),
                       " | ".join([x for x in l if "weekly body=" in x][:2])))
    check("G1: and it is asked with the controller, the row's own id and its own kind",
          int(rt.eval("RECBODY.c")) == 0 and int(rt.eval("RECBODY.id")) == 60330
          and int(rt.eval("RECBODY.kind")) == 585, str(rt.eval("RECBODY")))

    rl = new_rt(lua51, src=False)
    rl.execute(PRE)
    rl.execute("SET_BODYMODE('long')")
    rl.execute("SET_WEEKLY_FLAT(60330, '3', 'sat_weekly_zm_s1w1_kills', 1)")
    rl.execute("SET_CHAL_PROGRESS(60330, 1)")
    rl.execute("SET_G11(176)")
    load(rl)
    pump(rl, 12)
    rl.execute("SET_CHAL_PROGRESS(60330, 3)")
    pump(rl, 60)
    check("G1: the logged body is the first forty characters",
          has_line(lines_of(rl), "weekly body=" + "Z" * 40 + "...")
          and rl.eval("EV(1).options.bodyText") == "Z" * 60,
          " | ".join([x for x in lines_of(rl) if "weekly body=" in x][:2]))

    rc = new_rt(lua51, src=False)
    rc.execute(PRE)
    rc.execute("SET_LOCMODE('raise')")
    rc.execute("SET_SUB('ELIMINATE AN ELITE ZOMBIE')")
    rc.execute("SET_WEEKLY_FLAT(60330, '3|6', 'sat_weekly_zm_s1w1_kills', 1)")
    rc.execute("SET_CHAL_PROGRESS(60330, 1)")
    rc.execute("SET_G11(171)")
    load(rc)
    pump(rc, 12)
    rc.execute("SET_CHAL_PROGRESS(60330, 3)")
    pump(rc, 60)
    lc = lines_of(rc)
    check("G1: an empty body is sent as the defined empty string, never nil",
          rc.eval("EV(1).options.bodyText") == "", repr(rc.eval("EV(1).options.bodyText")))
    check("G1: and the subheader an earlier card left is emptied, not inherited",
          rc.eval("SUB.text") == "", repr(rc.eval("SUB.text")))
    check("G1: the card says the body was empty, once",
          count_line(lc, "weekly body=empty") == 1, str(count_line(lc, "weekly body=empty")))
    rc.execute("SET_LOCMODE('ok')")
    rc.execute("SET_CHAL_PROGRESS(60330, 6)")
    pump(rc, 60)
    check("G1: the next card shows its own text, not the one before it",
          rc.eval("SUB.text") == "B:desc 60330@6" and rc.eval("EV(2).options.bodyText") == "B:desc 60330@6",
          "%s / %s" % (rc.eval("SUB.text"), rc.eval("EV(2).options.bodyText")))

    rp = new_rt(lua51, src=False)
    rp.execute(PRE)
    rp.execute("SET_BODYMODE('native')")
    rp.execute("SET_REWARDS()")
    rp.execute("SET_WEEKLY_FLAT(60330, '3', 'sat_weekly_zm_s1w1_kills', 1)")
    rp.execute("SET_CHAL_PROGRESS(60330, 1)")
    rp.execute("SET_G11(172)")
    load(rp)
    pump(rp, 12)
    rp.execute("SET_CHAL_PROGRESS(60330, 3)")
    marks = dispatches(rp, 80)
    lp = lines_of(rp)
    check("G2: the row's reward goes out as a second weaponProgression message",
          rp.eval("NAMED('add_message_splash_manager')") == 2
          and rp.eval("EVLOC('weaponProgression')") is not None,
          "%s / %s" % (rp.eval("NAMED('add_message_splash_manager')"),
                       rp.eval("EVLOC('weaponProgression')")))
    check("G2: with the client's own fields - image, the localised name, 30, no priority",
          rp.eval("EVLOC('weaponProgression').options.image") == "icon_xp_tokens"
          and rp.eval("EVLOC('weaponProgression').options.headerText") == "5000 XP"
          and int(rp.eval("EVLOC('weaponProgression').options.displayTimeOverride")) == 30
          and rp.eval("EVLOC('weaponProgression').options.priority") is None
          and int(rp.eval("EVLOC('weaponProgression').options.controllerIndex")) == 0,
          str(rp.eval("EVLOC('weaponProgression').options")))
    check("G2: it goes out in the front card's own tick, right after it",
          int(rp.eval("EVIDX('dailyNotification')")) + 1 == int(rp.eval("EVIDX('weaponProgression')"))
          and len(marks) == 1 and marks[0][1] == 2,
          "%s %s" % (rp.eval("EVIDX('dailyNotification')"), marks))
    check("G2: and it is never a centre card of its own",
          not has_line(card_lines(lp), "kind=wkxp")
          and has_line(card_lines(lp), "kind=chalWB id=60330"), " | ".join(card_lines(lp)))

    re_ = new_rt(lua51, src=False)
    re_.execute(PRE)
    re_.execute("SET_BODYMODE('native')")
    re_.execute("SET_WEEKLY_FLAT(60330, '3', 'sat_weekly_zm_s1w1_kills', 1)")
    re_.execute("SET_CHAL_PROGRESS(60330, 1)")
    re_.execute("SET_G11(173)")
    load(re_)
    pump(re_, 12)
    re_.execute("SET_CHAL_PROGRESS(60330, 3)")
    pump(re_, 60)
    le = lines_of(re_)
    check("G2: an empty reward list sends nothing, and says so once",
          re_.eval("NAMED('add_message_splash_manager')") == 1
          and count_line(le, "weekly xp id=60330 none") == 1
          and re_.eval("EVLOC('weaponProgression')") is None,
          "%s / %s" % (re_.eval("NAMED('add_message_splash_manager')"),
                       " | ".join([x for x in le if "weekly xp" in x][:2])))

    ra = new_rt(lua51, src=False)
    ra.execute(PRE)
    ra.execute("SET_BODYMODE('native')")
    ra.execute("Challenge[xhash('getrewards')] = nil")
    ra.execute("SET_WEEKLY_FLAT(60330, '3', 'sat_weekly_zm_s1w1_kills', 1)")
    ra.execute("SET_CHAL_PROGRESS(60330, 1)")
    ra.execute("SET_G11(174)")
    load(ra)
    pump(ra, 12)
    ra.execute("SET_CHAL_PROGRESS(60330, 3)")
    pump(ra, 60)
    check("G2: and a VM without Challenge.getrewards invents no XP number either",
          ra.eval("NAMED('add_message_splash_manager')") == 1
          and count_line(lines_of(ra), "weekly xp id=60330 none") == 1,
          str(ra.eval("NAMED('add_message_splash_manager')")))


WEEKLYFORM = r"""
HEADS = {}
function SET_HEAD(k, v) HEADS[k] = v end
Engine[xhash("Localize")] = function(k, a)
  if k == nil then return "" end
  if a ~= nil then return "B:" .. tostring(k) .. "@" .. tostring(a) end
  local v = HEADS[k]
  if v ~= nil then return v end
  return k
end
Challenge[xhash("isweeklychallengetype")] = function(k) return k == 585 end
"""


def weekly_heads(lua51):
    def run(seed, form):
        r = new_rt(lua51, src=False)
        r.execute(WeeklyStub + WEEKLYFORM)
        r.execute(seed)
        r.execute("SET_WEEKLY_FLAT(60330, '3', 'sat_weekly_zm_s1w1_kills', 1)")
        r.execute("SET_CHAL_PROGRESS(60330, 1)")
        r.execute("SET_G11(175)")
        load(r)
        pump(r, 12)
        r.execute("SET_CHAL_PROGRESS(60330, 3)")
        pump(r, 40)
        return r, lines_of(r)

    rh, lh = run("SET_HEAD('#x37dc362a78cf1d3d3', 'Hash Title')", "hash")
    check("G3: the engine's own hash spelling is the first form tried",
          rh.eval("EV(1).options.headerText") == "Hash Title"
          and count_line(lh, "weekly header native=Hash Title") == 1
          and not has_line(lh, "weekly header=none"),
          " | ".join([x for x in lh if "weekly header" in x][:2]))

    rk, lk = run(r"SET_HEAD('challenge/jup_ch_weekly_challenge_completed', "
                 r"'\226\150\188Weekly Challenge Completed')", "key")
    check("G3: the readable key is the second form, and its marker glyph is stripped",
          rk.eval("EV(1).options.headerText") == "Weekly Challenge Completed"
          and count_line(lk, "weekly header native=Weekly Challenge Completed") == 1,
          " | ".join([x for x in lk if "weekly header" in x][:2]))

    rv, lv = run("SET_HEAD('0x7dc362a78cf1d3d3', 'Value Title')", "value")
    check("G3: the value form the native passes is the third",
          rv.eval("EV(1).options.headerText") == "Value Title"
          and count_line(lv, "weekly header native=Value Title") == 1,
          " | ".join([x for x in lv if "weekly header" in x][:2]))

    rn, ln = run("", "none")
    check("G3: a VM that resolves none of the three keeps our literal and says one line",
          rn.eval("EV(1).options.headerText") == "WEEKLY CHALLENGE COMPLETE"
          and count_line(ln, "weekly header=none") == 1
          and not has_line(ln, "weekly header native="),
          " | ".join([x for x in ln if "weekly header" in x][:2]))
    check("G3: and one header line per VM, whichever form answered",
          all(count_line(x, "weekly header") == 1 for x in (lh, lk, lv, ln)),
          "%s %s %s %s" % tuple(count_line(x, "weekly header") for x in (lh, lk, lv, ln)))


def splashck_cap(lua51):
    rt = new_rt(lua51, frontend=True, src=False)
    rt.execute(SPLASHFIX)
    load(rt)
    rt.execute("for i = 1, 65 do local s = rawget(_G, 'ProgressionTuning') "
               "if s.hooks.card then s.hooks.card('chalWB', i, 0, 'a') end end")
    lines = lines_of(rt)
    cards = card_lines(lines)
    check("cap: sixty card lines, then nothing",
          len(cards) == 60 and has_line(cards, "splashck: card 60 kind=chalWB id=60")
          and not has_line(lines, "card 61"), "%d lines, last %s" % (len(cards), cards[-1:]))
    check("cap: one cap line, and it names sixty",
          count_line(lines, "splashck: cards capped at 60") == 1,
          " | ".join([x for x in lines if "capped" in x][:2]))


def s3_universal(lua51):
    LADDER = """
PRESTIGE[xhash("getmaxweaponprestigelevel")] = function(ref) return 2 end
PRESTIGE[xhash("getweaponprestigecamos")] = function(ref)
  if ref == "sat_pi_alcor" then
    local e = { { startPrestige = 0, startLevel = 0, targetPrestige = 1, targetLevel = 27,
                  camoBundle = { lootid = 107478 } } }
    return e, {}, {}
  end
  if ref == "sat_ar_falcon" then
    local a = { { startPrestige = 1, startLevel = 0, targetPrestige = 2, targetLevel = 27,
                  camoBundle = { lootid = 107467 } } }
    return a, {}, {}
  end
  return {}, {}, {}
end
WEAPON[xhash("enumerateweapons")] = function(cb)
  cb({ ref = "sat_ar_falcon" })
  cb({ ref = "sat_pi_alcor" })
  cb({ ref = "sat_sh_none" })
end
function DROP_ENUM() WEAPON[xhash("enumerateweapons")] = nil end
"""

    def build(after=""):
        rt = new_rt(lua51, frontend=True, src=False)
        lua_slabs(rt, slabs_of([150900]))
        rt.execute("SET_G11(81)")
        rt.execute('SET_PRESTIGE("sat_pi_alcor", 0)')
        rt.execute('SET_LEVEL("sat_pi_alcor", 2)')
        rt.execute('SET_PRESTIGE("sat_ar_falcon", 0)')
        rt.execute('SET_LEVEL("sat_ar_falcon", 2)')
        rt.execute("SET_CAMODATA(107478, nil)")
        rt.execute("SET_CAMODATA(107467, nil)")
        rt.execute("SET_CAMODATA(107480, nil)")
        rt.execute("SET_TYPE(107478, 13)")
        rt.execute("SET_TYPE(107467, 13)")
        rt.execute("SET_TYPE(107480, 13)")
        rt.execute(LADDER)
        if after:
            rt.execute(after)
        load(rt)
        pump(rt, 1)
        return rt

    rt = build()
    check("s3u: a camo whose own data names no weapon is found in the weapon's own ladder",
          rt.eval("ASK_L(107478)") is False, str(rt.eval("ASK_L(107478)")))
    check("s3u: and the band it is answered with is that ladder entry's own",
          has_line(lines_of(rt), "prestige camo id=107478 ref=sat_pi_alcor start=0/0 to=1/27"),
          " | ".join([ln for ln in lines_of(rt) if "prestige camo id=" in ln][:3]))
    check("s3u: a second weapon's ladder entry is answered on its own prestige",
          rt.eval("ASK_L(107467)") is False, str(rt.eval("ASK_L(107467)")))
    rt.execute('SET_PRESTIGE("sat_pi_alcor", 1)')
    check("s3u: and it opens when the weapon that names it reaches the band",
          rt.eval("ASK_L(107478)") is True, str(rt.eval("ASK_L(107478)")))
    check("s3u: a camo in no weapon's ladder keeps the client's own answer, and one line says so",
          rt.eval("ASK_L(107480)") is True
          and count_line(lines_of(rt), "107480 names no weapon in its own data and is in no weapon's prestige ladder") == 1,
          " | ".join([ln for ln in lines_of(rt) if "names no weapon" in ln][:3]))

    lua_slabs(rt, slabs_of([150900, 150123]))
    rt.execute('SET_VER("82:33:65536")')
    pump(rt, 8)
    pump(rt, 8)
    check("s3u: the ladder map is cleared on the same rebuild as the bitmap",
          rt.eval("ASK_L(107480)") is True and rt.eval("ASK_L(107478)") is True)

    rt2 = build("DROP_ENUM()")
    check("s3u: with no WEAPON.enumerateweapons nothing closes and one line says so",
          rt2.eval("ASK_L(107478)") is True
          and count_line(lines_of(rt2), "prestige lock: no WEAPON.enumerateweapons") == 1,
          " | ".join([ln for ln in lines_of(rt2) if "prestige lock" in ln][:4]))

    rt3 = new_rt(lua51, frontend=True, src=False)
    lua_slabs(rt3, slabs_of([150900]))
    rt3.execute("SET_G11(83)")
    rt3.execute('SET_PRESTIGE("sat_pi_alcor", 0)')
    rt3.execute('SET_LEVEL("sat_pi_alcor", 2)')
    rt3.execute("SET_CAMODATA(107478, nil)")
    rt3.execute("SET_TYPE(107478, 13)")
    load(rt3)
    pump(rt3, 1)
    check("s3u: with no PRESTIGE.getweaponprestigecamos there is nothing to scan and the tile passes",
          rt3.eval("ASK_L(107478)") is True
          and count_line(lines_of(rt3), "prestige lock: no PRESTIGE.getweaponprestigecamos") == 1)


def s4_journal(lua51):
    J = S4_PRE + '\nLOOT[xhash("IsItemPermanentlyUnlocked")] = function(id, c) return false end\n'
    rt = new_rt(lua51, frontend=True, src=False, pre=J)
    lua_slabs(rt, slabs_of([150900]))
    rt.execute("SET_G11(91)")
    load(rt)
    pump(rt, 1)
    for i in (132396, 56146, 132396, 104730):
        rt.execute("Loot[xhash(\"IsOwned\")](0, %d)" % i)
    rt.execute("SET_TOGGLE('pt_diag', 1)")
    pump(rt, 8)
    pump(rt, 8)
    blk = rc1d_lines(lines_of(rt))
    calls = [ln for ln in blk if "Q10 call id=" in ln]
    check("s4j: the door records what the client asks it, with the answer it gave",
          has_line(blk, "Q10 call id=132396 ans=0") and has_line(blk, "Q10 call id=56146 ans=99"),
          " | ".join(calls[:4]))
    check("s4j: the journal is bounded and counts every call, repeats included",
          len(calls) == 3 and has_line(blk, "Q10 calls=4 seen=3"),
          "%d rows / %s" % (len(calls), " | ".join([ln for ln in blk if "Q10 calls=" in ln][:2])))
    check("s4j: and the client's own composite for the laser's own id is printed beside it",
          has_line(blk, "Q10 item 126615 item=boolean:false"),
          " | ".join([ln for ln in blk if "Q10 item" in ln][:2]))

    rt2 = new_rt(lua51, frontend=True, src=False, pre=S4_PRE)
    lua_slabs(rt2, slabs_of([150900]))
    rt2.execute("SET_G11(92)")
    load(rt2)
    pump(rt2, 1)
    check("s4j: with the diagnostic off nothing is journalled and no Q-line prints",
          not has_line(lines_of(rt2), "Q10 ") and rt2.eval("ASK_OWNED(132396)") == 0)


def s5_watch(lua51):
    WATCH = """
PASSED = nil
ORIGFN = function(c, ds, list)
  PASSED = { c = c, ds = ds, list = list }
  return "orig"
end
WEAPON_CAMO[xhash("updatedatasourcewithchallengedata")] = ORIGFN
DSC = {}
function DSC:GetValue(c) return 9 end
DS = { count = DSC }
LASER = { bundleLootID = 126615, id = 68970 }
SET_LOOT_REF(126615, "camo_126615")
WEAPON[xhash("getcamodataforref")] = function(ref)
  if ref == "camo_126615" then return { camochallengeweaponref = "sat_pi_alcor" } end
  return nil
end
"""

    rt = new_rt(lua51, frontend=True, src=False)
    rt.execute(DIAGFIX)
    rt.execute(WATCH)
    rt.execute("SET_G11(93)")
    rt.execute("SET_TOGGLE('pt_diag', 1)")
    load(rt)
    out = rt.eval('WEAPON_CAMO[xhash("updatedatasourcewithchallengedata")](0, DS, { LASER })')
    check("s5: the observer is a pure pass-through - it returns exactly what the original returned",
          out == "orig" and rt.eval("PASSED.ds") is not None and rt.eval("PASSED.c") == 0,
          str(out))
    rt.execute("SET_TOGGLE('pt_diag', 0)")
    pump(rt, 8)
    rt.execute("SET_TOGGLE('pt_diag', 1)")
    pump(rt, 8)
    pump(rt, 8)
    blk = rc1d_lines(lines_of(rt))
    check("s5: the tracker's own call is counted and the datasource's count is read beside the list's",
          has_line(blk, "Q11 calls=1 n=1 ds=9 seen=1"),
          " | ".join([ln for ln in blk if "Q11 " in ln][:4]))
    check("s5: the row's own id and its camo's owning weapon are named, bounded",
          has_line(blk, "Q11 row id=68970 w=sat_pi_alcor"),
          " | ".join([ln for ln in blk if "Q11 row" in ln][:4]))

    rt2 = new_rt(lua51, frontend=True, src=False)
    rt2.execute(DIAGFIX)
    rt2.execute(WATCH)
    rt2.execute("SET_G11(94)")
    load(rt2)
    rt2.execute('WEAPON_CAMO[xhash("updatedatasourcewithchallengedata")](0, DS, { LASER })')
    check("s5: with pt_diag off the slot is not replaced at all",
          rt2.eval('WEAPON_CAMO[xhash("updatedatasourcewithchallengedata")] == ORIGFN') is True
          and not has_line(lines_of(rt2), "Q11 "),
          str(rt2.eval('WEAPON_CAMO[xhash("updatedatasourcewithchallengedata")] == ORIGFN')))


def ladder_pick_a3(lua51):
    FLAT = """
SET_GUN("sat_me_shockbaton", 54498)
SET_LOOT_REF(98753, "sat_me_shockbaton")
CELL("wp", "weaponRef", "sat_me_shockbaton", "amount", "1000|2200|3400|4600|5800")
SET_WD("sat_me_shockbaton", { 100, 100, 100, 150, 150, 150, 150, 150, 200, 200 })
SET_OC(54498, 0, 0)
"""
    AL = """
SET_GUN("sat_pi_alcor", 68333)
SET_LOOT_REF(125186, "sat_pi_alcor")
SET_MINXP("sat_pi_alcor", { 1000, 2200, 3400, 4600, 5800 })
SET_MAXLEVEL("sat_pi_alcor", 27)
SET_OC(68333, 0, 0)
"""
    NH = """
SET_GUN("sat_reach_test", 55001)
SET_LOOT_REF(50101, "sat_reach_test")
SET_MINXP("sat_reach_test", { 100, 100, 150 })
SET_OC(55001, 0, 0)
"""
    rt = new_rt(lua51, pre=FLAT + ' SET_PAID("v1;98753:460:1")')
    pump(rt, 4)
    check("A3: the Flatline's own total on the first sighting is level 0",
          has_line(lines_of(rt), "prime sat_me_shockbaton lv=0 total=460"),
          " | ".join([x for x in lines_of(rt) if "prime sat_me_shockbaton" in x][:3]))
    for tot in (480, 500, 560, 880, 980):
        rt.execute('SET_PAID("v1;98753:%d:%d")' % (tot, tot))
        pump(rt, 8)
    check("A3: 460 to 980 XP is no banner at all", rt.eval("NEVENTS()") == 0, str(rt.eval("NEVENTS()")))
    rt.execute('SET_PAID("v1;98753:1000:999")')
    pump(rt, 8)
    check("A3: 1,000 XP is exactly one banner, reading 2 at rung 1,000",
          rt.eval("NAMED('completed_challenge')") == 1
          and has_line(lines_of(rt),
                       "level sat_me_shockbaton crossed 1 row 54498 rank=1 banner=2 total=1000 rung=1000 src=dll"),
          " | ".join([x for x in lines_of(rt) if "crossed" in x][:3]))

    rt2 = new_rt(lua51, pre=AL + ' SET_PAID("v1;125186:4009:1")')
    pump(rt2, 5)
    l2 = lines_of(rt2)
    check("A3: the 1911 at 4,009 reads own=3 off the client's own record and primes silently at 3",
          has_line(l2, "prime sat_pi_alcor own=3 total=4009 picked=5/minxp")
          and has_line(l2, "prime sat_pi_alcor lv=3 total=4009"),
          " | ".join([x for x in l2 if "prime sat_pi_alcor" in x][:3]))
    check("A3: and the silent prime draws nothing", rt2.eval("NEVENTS()") == 0, str(rt2.eval("NEVENTS()")))
    pump(rt2, 4)
    rt2.eval("OC_READ(68333)")
    rt2.execute('SET_PAID("v1;125186:4600:2")')
    pump(rt2, 8)
    check("A3: the 1911's 4,600 crossing is exactly one banner reading 5 at rung 4,600",
          rt2.eval("NAMED('completed_challenge')") == 1
          and has_line(lines_of(rt2),
                       "level sat_pi_alcor crossed 4 row 68333 rank=4 banner=5 total=4600 rung=4600"),
          " | ".join([x for x in lines_of(rt2) if "crossed" in x][:3]))
    pump(rt2, 8)
    rt2.eval("OC_READ(68333)")
    rt2.execute('SET_PAID("v1;125186:5800:3")')
    pump(rt2, 8)
    rt2.eval("OC_READ(68333)")
    check("A3: and 5,800 is one more, reading 6 at rung 5,800",
          rt2.eval("NAMED('completed_challenge')") == 2
          and has_line(lines_of(rt2),
                       "level sat_pi_alcor crossed 5 row 68333 rank=5 banner=6 total=5800 rung=5800"),
          "%d | %s" % (rt2.eval("NAMED('completed_challenge')"),
                       " | ".join([x for x in lines_of(rt2) if "crossed" in x][:3])))
    check("A3: the level the replaced record answers is the rank plus one at every step",
          has_line(lines_of(rt2), "card level ref=sat_pi_alcor row=68333 total=4009 display=4")
          and has_line(lines_of(rt2), "card level ref=sat_pi_alcor row=68333 total=4600 display=5")
          and has_line(lines_of(rt2), "card level ref=sat_pi_alcor row=68333 total=5800 display=6"),
          " | ".join([x for x in lines_of(rt2) if "card level ref=sat_pi_alcor" in x][:4]))
    xp7, rk7 = rt2.eval("OC_READ(68333)")
    check("A3: and the record the client reads answers that same rank, not a nil",
          int(rk7) == 5 and int(xp7) == 5800, "%s / %s" % (xp7, rk7))

    rt3 = new_rt(lua51, pre=AL + ' SET_PAID("v1;99999:1:1")')
    pump(rt3, 10)
    check("A3: the wrapper is armed before the paid gun is seen in this order",
          has_line(lines_of(rt3), "in-match display armed"), " | ".join(lines_of(rt3)[:6]))
    rt3.execute('SET_PAID("v1;125186:4009:2")')
    pump(rt3, 5)
    a = [x for x in lines_of(rt2) if "prime sat_pi_alcor own=" in x][:1]
    b = [x for x in lines_of(rt3) if "prime sat_pi_alcor own=" in x][:1]
    check("A3: the pick is the same whether it runs before or after the wrapper arms",
          len(a) == 1 and a == b and has_line(lines_of(rt3), "prime sat_pi_alcor lv=3 total=4009"),
          "%s vs %s" % (a, b))
    rt3.execute('SET_PAID("v1;125186:4600:3")')
    pump(rt3, 8)
    check("A3: and the crossing after that order is the same one banner",
          rt3.eval("NAMED('completed_challenge')") == 1
          and has_line(lines_of(rt3), "crossed 4 row 68333 rank=4 banner=5 total=4600 rung=4600"),
          " | ".join([x for x in lines_of(rt3) if "crossed" in x][:2]))

    rt4 = new_rt(lua51, pre=AL + ' SET_LEVEL("sat_pi_alcor", 1) SET_PAID("v1;125186:4009:1")')
    pump(rt4, 5)
    check("A3: a pick the client's own record does not reproduce is refused, and says so",
          has_line(lines_of(rt4), "picked=0/none") and rt4.eval("NEVENTS()") == 0,
          " | ".join([x for x in lines_of(rt4) if "picked=" in x][:2]))
    rt4.execute('SET_LEVEL("sat_pi_alcor", 3)')
    rt4.execute('SET_PAID("v1;125186:4009:2")')
    pump(rt4, 5)
    check("A3: the next payment retries and primes - no deadlock",
          has_line(lines_of(rt4), "prime sat_pi_alcor lv=3 total=4009") and rt4.eval("NEVENTS()") == 0,
          " | ".join([x for x in lines_of(rt4) if "prime sat_pi_alcor" in x][:3]))
    rt4.execute('SET_PAID("v1;125186:4600:3")')
    pump(rt4, 8)
    check("A3: and the recovered gun banners exactly once, with the client's own number",
          rt4.eval("NAMED('completed_challenge')") == 1
          and has_line(lines_of(rt4), "crossed 4 row 68333 rank=4 banner=5 total=4600 rung=4600"),
          " | ".join([x for x in lines_of(rt4) if "crossed" in x][:2]))

    rt5 = new_rt(lua51, pre=NH + ' SET_LEVEL("sat_reach_test", 3) SET_PAID("v1;50101:90:1")')
    pump(rt5, 12)
    rt5.eval("OC_READ(55001)")
    xp5, rank = rt5.eval("OC_READ(55001)")
    check("A3: with no ladder picked the record keeps the client's own rank, never a nil one",
          int(rank) == 3 and has_line(lines_of(rt5), "card level ref=sat_reach_test row=55001 total=90 display=4"),
          "%s | %s" % (rank, " | ".join([x for x in lines_of(rt5) if "card level" in x][:2])))
    check("A3: and a refused pick draws neither a banner nor an attachment card",
          rt5.eval("NEVENTS()") == 0, str(rt5.eval("NEVENTS()")))
    rt5.execute('SET_MINXP("sat_reach_test", { 100, 200, 300 })')
    rt5.execute('SET_LEVEL("sat_reach_test", 0)')
    rt5.execute('SET_PAID("v1;50101:90:2")')
    pump(rt5, 5)
    check("A3: once the list rises and the record agrees the same gun primes",
          has_line(lines_of(rt5), "prime sat_reach_test lv=0 total=90") and rt5.eval("NEVENTS()") == 0,
          " | ".join([x for x in lines_of(rt5) if "prime sat_reach_test" in x][:3]))
    rt5.execute('SET_PAID("v1;50101:150:3")')
    pump(rt5, 8)
    check("A3: and the banner and its attachment card still agree at the crossing",
          rt5.eval("NAMED('completed_challenge')") == 1
          and has_line(lines_of(rt5), "crossed 1 row 55001 rank=1 banner=2 total=150 rung=100"),
          " | ".join([x for x in lines_of(rt5) if ("crossed" in x or "attachment" in x)][:3]))

    BIG = """
SET_GUN("sat_big_test", 55002)
SET_LOOT_REF(50102, "sat_big_test")
SET_MINXP("sat_big_test", { 1000, 2000, 3000, 4000, 5000, 6000 })
SET_MAXLEVEL("sat_big_test", 3)
SET_OC(55002, 0, 0)
"""
    rt6 = new_rt(lua51, pre=BIG + ' SET_PAID("v1;50102:3500:1")')
    pump(rt6, 5)
    check("A3: a list longer than the gun's own maximum is clamped to that maximum",
          has_line(lines_of(rt6), "prime sat_big_test own=3 total=3500 picked=3/minxp")
          and has_line(lines_of(rt6), "prime sat_big_test lv=3 total=3500"),
          " | ".join([x for x in lines_of(rt6) if "prime sat_big_test" in x][:3]))
    rt6.execute('SET_PAID("v1;50102:7000:2")')
    pump(rt6, 8)
    check("A3: so no phantom rung above the gun's maximum is ever announced",
          rt6.eval("NEVENTS()") == 0, str(rt6.eval("NEVENTS()")))


def ladder_pick(lua51):
    FLAT = """
SET_GUN("sat_me_shockbaton", 54498)
SET_LOOT_REF(98753, "sat_me_shockbaton")
CELL("wp", "weaponRef", "sat_me_shockbaton", "amount", "1000|2200|3400|4600|5800")
SET_WD("sat_me_shockbaton", { 100, 100, 100, 150, 150, 150, 150, 150, 200, 200 })
SET_LEVEL("sat_me_shockbaton", 0)
SET_OC(54498, 0, 0)
"""
    AL = """
SET_GUN("sat_pi_alcor", 68333)
SET_LOOT_REF(125186, "sat_pi_alcor")
SET_MINXP("sat_pi_alcor", { 1000, 2200, 3400, 4600, 5800 })
SET_OC(68333, 0, 0)
"""
    NH = """
SET_GUN("sat_reach_test", 55001)
SET_LOOT_REF(50101, "sat_reach_test")
SET_MINXP("sat_reach_test", { 100, 100, 150 })
SET_LEVEL("sat_reach_test", 0)
SET_OC(55001, 0, 0)
"""
    rt = new_rt(lua51, pre=FLAT + ' SET_PAID("v1;98753:260:1")')
    pump(rt, 4)
    l = lines_of(rt)
    check("A: the Flatline primes at level 0 on the row's own first rung, not on the bundle's costs",
          has_line(l, "prime sat_me_shockbaton lv=0 total=260"),
          " | ".join([x for x in l if "prime " in x][:3]))
    check("A: and the pick names the row's own cell - the per-level cost list is not a candidate at all",
          has_line(l, "picked=5/csv") and count_line(l, "/weapon") == 0,
          " | ".join([x for x in l if "picked=" in x][:3]))
    check("A: 260 XP draws nothing", rt.eval("NEVENTS()") == 0)
    for tot in (300, 360, 440):
        rt.execute('SET_PAID("v1;98753:%d:%d")' % (tot, tot))
        pump(rt, 8)
    check("A: 300, 360 and 440 are all still level 0 - the ten false banners are gone",
          rt.eval("NEVENTS()") == 0 and has_line(lines_of(rt), "prime sat_me_shockbaton lv=0 total=260"),
          str(rt.eval("NEVENTS()")))
    rt.execute('SET_PAID("v1;98753:1000:999")')
    pump(rt, 8)
    l2 = lines_of(rt)
    check("A: the Flatline's first real level is one banner at 1,000 XP",
          rt.eval("NAMED('completed_challenge')") == 1, str(rt.eval("NAMED('completed_challenge')")))
    check("A: and it reads level 2, the client's own number for that rung",
          has_line(l2, "level sat_me_shockbaton crossed 1 row 54498 rank=1 banner=2 total=1000 rung=1000"),
          " | ".join([x for x in l2 if "crossed" in x][:3]))

    rt2 = new_rt(lua51, pre=AL + ' SET_PAID("v1;125186:3329:1")')
    pump(rt2, 4)
    check("A: the 1911 still primes from its own minxp ladder at the level the client reports",
          has_line(lines_of(rt2), "prime sat_pi_alcor lv=2 total=3329 ladder=5/minxp"),
          " | ".join([x for x in lines_of(rt2) if "prime sat_pi_alcor" in x][:2]))
    rt2.execute('SET_PAID("v1;125186:3429:2")')
    pump(rt2, 8)
    l = lines_of(rt2)
    check("A: and the launch's own line is unchanged - crossed 3, banner 4, rung 3,400",
          has_line(l, "level sat_pi_alcor crossed 3 row 68333 rank=3 banner=4 total=3429 rung=3400"),
          " | ".join([x for x in l if "crossed" in x][:3]))
    check("A: one banner, not two", rt2.eval("NAMED('completed_challenge')") == 1)

    rt3 = new_rt(lua51, pre=NH + ' SET_PAID("v1;50101:90:1")')
    pump(rt3, 4)
    l = lines_of(rt3)
    check("A: a list that does not strictly rise is not a ladder - the pick refuses it and says why",
          has_line(l, "picked=0/none") and has_line(l, "no ladder answers for sat_reach_test (own 0)"),
          " | ".join([x for x in l if ("picked=" in x or "no ladder" in x)][:3]))
    check("A: and that refusal draws nothing", rt3.eval("NEVENTS()") == 0)
    rt3.execute('SET_MINXP("sat_reach_test", { 100, 200, 300 })')
    rt3.execute('SET_PAID("v1;50101:90:2")')
    pump(rt3, 8)
    check("A: the refusal is not kept - the next payment picks the ladder that now exists and primes",
          has_line(lines_of(rt3), "prime sat_reach_test lv=0 total=90") and rt3.eval("NEVENTS()") == 0,
          " | ".join([x for x in lines_of(rt3) if "prime sat_reach_test" in x][:3]))
    rt3.execute('SET_PAID("v1;50101:150:3")')
    pump(rt3, 8)
    check("A: and the crossing after that draws exactly one banner",
          rt3.eval("NAMED('completed_challenge')") == 1
          and has_line(lines_of(rt3),
                       "level sat_reach_test crossed 1 row 55001 rank=1 banner=2 total=150 rung=100"),
          " | ".join([x for x in lines_of(rt3) if "crossed" in x][:2]))

    rt4 = new_rt(lua51, pre=AL + ' SET_LEVEL("sat_pi_alcor", 3) SET_PAID("v1;125186:4600:1")')
    pump(rt4, 4)
    check("A: a stale own level refuses the pick instead of handing back an unverified ladder",
          has_line(lines_of(rt4), "picked=0/none") and rt4.eval("NEVENTS()") == 0,
          " | ".join([x for x in lines_of(rt4) if "picked=" in x][:2]))
    rt4.execute('SET_LEVEL("sat_pi_alcor", 4)')
    rt4.execute('SET_PAID("v1;125186:4600:2")')
    pump(rt4, 8)
    check("A: when own catches up the pick is made and the level is primed, never announced late",
          has_line(lines_of(rt4), "prime sat_pi_alcor lv=4 total=4600") and rt4.eval("NEVENTS()") == 0,
          " | ".join([x for x in lines_of(rt4) if "prime sat_pi_alcor" in x][:3]))
    rt4.execute('SET_PAID("v1;125186:5800:3")')
    pump(rt4, 8)
    check("A: and the next real crossing draws exactly one banner, never a doubled one",
          rt4.eval("NAMED('completed_challenge')") == 1
          and has_line(lines_of(rt4), "crossed 5 row 68333 rank=5 banner=6 total=5800 rung=5800"),
          " | ".join([x for x in lines_of(rt4) if "crossed" in x][:3]))


def camo_retry(lua51):
    STAGE = """
READY = false
PRESTIGE[xhash("getmaxweaponprestigelevel")] = function(ref)
  if READY then return 2 end
  return 0
end
PRESTIGE[xhash("getweaponprestigecamos")] = function(ref)
  if READY and ref == "sat_pi_alcor" then
    local a = { { startPrestige = 0, startLevel = 0, targetPrestige = 1, targetLevel = 27,
                  camoBundle = { lootid = 107478 } } }
    local b = { { startPrestige = 0, startLevel = 0, targetPrestige = 1, targetLevel = 27,
                  camoBundle = { lootid = 107480 } } }
    return a, b, {}
  end
  return {}, {}, {}
end
WEAPON[xhash("enumerateweapons")] = function(cb)
  if READY then cb({ ref = "sat_pi_alcor" }) end
end
function SET_READY() READY = true end
"""
    rt = new_rt(lua51, frontend=True, src=False)
    rt.execute(STAGE)
    rt.execute("SET_G11(86)")
    rt.execute('SET_PRESTIGE("sat_pi_alcor", 0)')
    rt.execute('SET_LEVEL("sat_pi_alcor", 2)')
    rt.execute("SET_CAMODATA(107478, nil)")
    rt.execute('SET_CAMODATA(107480, "sat_pi_alcor")')
    rt.execute("SET_TYPE(107478, 13)")
    rt.execute("SET_TYPE(107480, 13)")
    load(rt)
    pump(rt, 1)
    check("B: the first build names nothing and the map is not kept",
          rt.eval("ASK_L(107478)") is True
          and count_line(lines_of(rt), "prestige camo ids over 0 weapons - not kept") == 1,
          " | ".join([x for x in lines_of(rt) if "prestige camo ids over" in x][:3]))
    check("B: and an own-data camo whose band is not readable yet keeps the client's answer too",
          rt.eval("ASK_L(107480)") is True)

    rt.execute("SET_READY()")
    pump(rt, 10)
    check("B: the data arriving is enough - the next ask in the same VM answers locked",
          rt.eval("ASK_L(107478)") is False, str(rt.eval("ASK_L(107478)")))
    check("B: because the map was built with the data and says so",
          has_line(lines_of(rt), "the weapon ladders name 2 prestige camo ids over 1 weapons"),
          " | ".join([x for x in lines_of(rt) if "prestige camo ids over" in x][:3]))
    check("B: the own-data camo's list is rebuilt too, so its band closes in the same VM",
          rt.eval("ASK_L(107480)") is False, str(rt.eval("ASK_L(107480)")))
    check("B: and no rebuild from the client was needed for either",
          not has_line(lines_of(rt), "rebuilt from serial"))

    MANY = """
for i = 1, 12 do SET_CAMODATA(200000 + i, nil); SET_TYPE(200000 + i, 13) end
"""
    rt2 = new_rt(lua51, frontend=True, src=False)
    rt2.execute(STAGE)
    rt2.execute(MANY)
    rt2.execute("SET_G11(87)")
    load(rt2)
    pump(rt2, 1)
    for i in range(1, 13):
        rt2.execute("ASK_L(%d)" % (200000 + i))
    pump(rt2, 10)
    l = lines_of(rt2)
    check("B: the passthrough log is one summary line for the burst, not one line per id",
          count_line(l, "camo ids passed through (first 6:") == 1,
          "%d lines" % count_line(l, "camo ids passed through"))
    check("B: and it names the count of both sides",
          has_line(l, "12 of 12 camo ids passed through (first 6: "),
          " | ".join([x for x in l if "passed through" in x][:2]))

    rt3 = new_rt(lua51, frontend=True, src=False, log=False)
    rt3.execute(STAGE)
    rt3.execute(MANY)
    rt3.execute("SET_G11(88)")
    load(rt3)
    pump(rt3, 1)
    for i in range(1, 13):
        rt3.execute("ASK_L(%d)" % (200000 + i))
    pump(rt3, 10)
    l = lines_of(rt3)
    check("B: with both switches off nothing about a passthrough is printed at all",
          count_line(l, "passed through") == 0 and count_line(l, "names no weapon") == 0,
          " | ".join([x for x in l if "pass" in x or "names no weapon" in x][:3]))


def s5_dedupe(lua51):
    PRE = """
KEPT = nil
SETUP = function(list, c, ds, x)
  KEPT = { n = #list, c = c, ds = ds, x = x, ids = {} }
  for i = 1, #list do KEPT.ids[i] = list[i].id end
  return "orig-answer"
end
Challenge[xhash("setupdailychallengesdatasource")] = SETUP
DSN = { count = {} }
function E(id) return { id = id, bundleLootID = 0 } end
"""
    rt = new_rt(lua51, frontend=True, src=False)
    rt.execute(PRE)
    rt.execute("SET_G11(95)")
    load(rt)
    ready = ("rawget(_G, 'ProgressionTuning').tracker ~= nil"
             " and rawget(_G, 'ProgressionTuning').tracker.done == true")
    steps = 0
    while not rt.eval(ready) and steps < 40:
        pump(rt, 1)
        steps = steps + 1
    check("C: the tracker wrapper is installed before the client calls the list builder",
          rt.eval(ready), "%d ticks" % steps)
    call = 'Challenge[xhash("setupdailychallengesdatasource")]({%s}, 0, DSN, true)'
    out = rt.eval(call % "E(68970), E(68970), E(68970), E(57129)")
    check("C: three entries carrying one challenge id reach the client as one",
          rt.eval("KEPT.n") == 2 and rt.eval("KEPT.ids[1]") == 68970 and rt.eval("KEPT.ids[2]") == 57129,
          "%s / %s" % (rt.eval("KEPT.n"), [rt.eval("KEPT.ids[%d]" % i) for i in (1, 2)]))
    check("C: the original's answer comes back unchanged", out == "orig-answer", str(out))
    check("C: the controller, the datasource and the extra argument are forwarded as received",
          rt.eval("KEPT.c") == 0 and rt.eval("KEPT.ds == DSN") is True and rt.eval("KEPT.x == true") is True)
    out = rt.eval(call % "E(53310), E(55402), E(55415)")
    check("C: three distinct ids keep all three rows", rt.eval("KEPT.n") == 3 and out == "orig-answer",
          str(rt.eval("KEPT.n")))
    out = rt.eval(call % "E(53310), E(55402), E(55415), E(53310)")
    check("C: the daily list keeps its own order, only the repeat of an id is dropped",
          rt.eval("KEPT.n") == 3 and rt.eval("KEPT.ids[3]") == 55415, str(rt.eval("KEPT.n")))

    rt2 = new_rt(lua51, frontend=True, src=False, pre="SET_TOGGLE('pt_on', 0)")
    rt2.execute(PRE)
    rt2.execute("SET_G11(96)")
    load(rt2)
    out = rt2.eval(call % "E(68970), E(68970), E(68970)")
    check("C: with pt_on 0 the list is not touched at all",
          rt2.eval("KEPT.n") == 3 and out == "orig-answer", str(rt2.eval("KEPT.n")))

    rt.execute("SET_TOGGLE('pt_diag', 1)")
    pump(rt, 8)
    pump(rt, 8)
    blk = rc1d_lines(lines_of(rt))
    check("C: the diagnostic prints the counts and the ids it dropped, bounded",
          has_line(blk, "Q11 dedupe in=11 out=8 calls=3 dropped=68970,68970,53310"),
          " | ".join([x for x in blk if "Q11 dedupe" in x][:2]))


CAMOSTUB = """
WEAPON_CAMO = WEAPON_CAMO or {}
Game = Game or {}
SHOULD = true
CAMOQ = true
BUILT = nil
function SET_SHOULD(v) SHOULD = v end
function SET_CAMOQ(v) CAMOQ = v end
GATE = false
Challenge[xhash("shouldshowcompletionsplash")] = function(ev) return SHOULD end
Challenge[xhash("isgunsmithcamochallenge")] = function(id, kind, c) return CAMOQ end
Challenge[xhash("getDesc")] = function(id, kind) return "desc " .. tostring(id) end
Challenge[xhash("setgunsmithcamochallengesplashdata")] = function(id, kind, c, opts, reward)
  BUILT = { id = id, kind = kind, desc = reward.desc, amount = reward.amount }
  opts.camoUnlocked = "TESTCAMO"
end
CAMOLIST = {}
function SET_CAMO_ROW(ref, id, amounts)
  local t = {}
  for i = 1, #amounts do t[i] = { id = id, amount = amounts[i] } end
  CAMOLIST[ref] = t
end
WEAPON_CAMO[xhash("getmilitarycamochallenges")] = function(c, ref, mode) return CAMOLIST[ref] end
Game[xhash("GetActiveGameModeKey")] = function() return "zm" end
function SET_CAMO_PROGRESS(id, v) OC[tostring(id)] = { xp = v, rank = 0 } end
"""


def camo_splash(lua51):
    PRE = CAMOSTUB
    rt = new_rt(lua51, src=False)
    rt.execute(PRE)
    rt.execute("SET_CAMO_ROW('sat_pi_atlas', 57201, {100, 200, 300})")
    rt.execute("SET_CAMO_PROGRESS(57201, 90)")
    rt.execute("SET_G11(120)")
    rt.execute('SET_PAID("v1;88929:900:1")')
    load(rt)
    pump(rt, 12)
    l = lines_of(rt)
    check("B: the paid weapon's own camo row is the watch set, read from the client",
          has_line(l, "camo watch id=57201 ref=sat_pi_atlas tiers=3 first=100 last=300"),
          " | ".join([x for x in l if "camo watch" in x][:2]))
    check("B: the first sighting primes silently, so a row already past a tier draws nothing",
          has_line(l, "camo prime id=57201 row=sat_pi_atlas value=90 tiers=3 hits=0")
          and rt.eval("NEVENTS()") == 0, " | ".join([x for x in l if "camo prime" in x][:2]))
    rt.execute("SET_CAMO_PROGRESS(57201, 100)")
    pump(rt, 24)
    l = lines_of(rt)
    check("B: a camo row crossing its own target draws exactly one card",
          rt.eval("NAMED('completed_challenge')") == 1, str(rt.eval("NAMED('completed_challenge')")))
    check("B: and the card is the game's own completed_challenge for that row and kind",
          rt.eval("LASTOF('completed_challenge').id") == 57201
          and int(rt.eval("LASTOF('completed_challenge').kind")) == 398,
          str(rt.eval("LASTOF('completed_challenge').id")))
    check("B: the line names the row, the target it crossed and the route",
          has_line(l, "camo card id=57201 row=sat_pi_atlas target=100 route=A"),
          " | ".join([x for x in l if "camo card" in x][:2]))
    check("B: and the crossing itself is one line", count_line(l, "camo cross id=57201") == 1,
          " | ".join([x for x in l if "camo cross" in x][:2]))
    rt.execute("SET_CAMO_PROGRESS(57201, 90)")
    pump(rt, 12)
    rt.execute("SET_CAMO_PROGRESS(57201, 100)")
    pump(rt, 24)
    check("B: the same id and target never fires a second time",
          rt.eval("NAMED('completed_challenge')") == 1, str(rt.eval("NAMED('completed_challenge')")))
    rt.execute("CLEAR()")
    rt.execute("SET_CAMO_PROGRESS(57201, 300)")
    pump(rt, 48)
    check("B: two tiers crossed at once draw two cards, in the tiers' own order",
          rt.eval("NAMED('completed_challenge')") == 2
          and has_line(lines_of(rt), "camo card id=57201 row=sat_pi_atlas target=200 route=A")
          and has_line(lines_of(rt), "camo card id=57201 row=sat_pi_atlas target=300 route=A"),
          " | ".join([x for x in lines_of(rt) if "camo card" in x][:3]))
    rt.execute("SET_TOGGLE('pt_diag', 1)")
    pump(rt, 8)
    pump(rt, 8)
    blk = rc1d_lines(lines_of(rt))
    check("B: the diagnostic names the watch set, the cards it fired and every crossing it saw",
          has_line(blk, "Q12 camo watch n=1 ids=57201 fired=3 cross=4")
          and has_line(blk, "Q12 camo crossings 57201:100,57201:100,57201:200,57201:300"),
          " | ".join([x for x in blk if "Q12" in x][:3]))

    rt2 = new_rt(lua51, src=False)
    rt2.execute(PRE)
    rt2.execute("SET_CAMO_ROW('sat_pi_atlas', 57201, {100, 200, 300})")
    rt2.execute("SET_CAMO_PROGRESS(57201, 150)")
    rt2.execute("SET_G11(121)")
    rt2.execute('SET_PAID("v1;88929:900:1")')
    load(rt2)
    pump(rt2, 12)
    check("B: a row already complete at match start does not pop",
          rt2.eval("NEVENTS()") == 0 and has_line(lines_of(rt2), "camo prime id=57201"),
          " | ".join([x for x in lines_of(rt2) if "camo prime" in x][:2]))
    rt2.execute("SET_CAMO_PROGRESS(57201, 200)")
    pump(rt2, 24)
    check("B: but its next tier does, once",
          rt2.eval("NAMED('completed_challenge')") == 1
          and has_line(lines_of(rt2), "camo card id=57201 row=sat_pi_atlas target=200 route=A"),
          " | ".join([x for x in lines_of(rt2) if "camo card" in x][:2]))

    rt3 = new_rt(lua51, src=False, pre="SET_TOGGLE('pt_camo', 0)")
    rt3.execute(PRE)
    rt3.execute("SET_CAMO_ROW('sat_pi_atlas', 57201, {100, 200, 300})")
    rt3.execute("SET_CAMO_PROGRESS(57201, 90)")
    rt3.execute("SET_G11(122)")
    rt3.execute('SET_PAID("v1;88929:900:1")')
    load(rt3)
    pump(rt3, 12)
    rt3.execute("SET_CAMO_PROGRESS(57201, 100)")
    pump(rt3, 24)
    check("B: pt_camo 0 draws no camo card at all",
          rt3.eval("NEVENTS()") == 0 and not has_line(lines_of(rt3), "camo card id="),
          str(rt3.eval("NEVENTS()")))

    rt4 = new_rt(lua51, src=False)
    rt4.execute(PRE)
    rt4.execute("SET_CAMOQ(false)")
    rt4.execute("SET_CAMO_ROW('sat_pi_atlas', 57201, {100, 200, 300})")
    rt4.execute("SET_CAMO_PROGRESS(57201, 90)")
    rt4.execute("SET_G11(123)")
    rt4.execute('SET_PAID("v1;88929:900:1")')
    load(rt4)
    pump(rt4, 12)
    rt4.execute("SET_CAMO_PROGRESS(57201, 100)")
    pump(rt4, 24)
    check("B: with route A's camo gate false the game's own builder draws the card instead",
          rt4.eval("NAMED('add_message_splash_manager')") == 1
          and rt4.eval("NAMED('completed_challenge')") == 0
          and has_line(lines_of(rt4), "camo card id=57201 row=sat_pi_atlas target=100 route=B"),
          " | ".join([x for x in lines_of(rt4) if "camo card" in x][:2]))
    check("B: and route B is the client's own builder, handed the row's own desc and amount",
          rt4.eval("BUILT.id") == 57201 and int(rt4.eval("BUILT.amount")) == 100
          and str(rt4.eval("BUILT.desc")) == "desc 57201",
          str(rt4.eval("BUILT")))

    rt5 = new_rt(lua51, src=False)
    rt5.execute(PRE)
    rt5.execute("SET_SHOULD(false)")
    rt5.execute("SET_CAMO_ROW('sat_pi_atlas', 57201, {100, 200, 300})")
    rt5.execute("SET_CAMO_PROGRESS(57201, 90)")
    rt5.execute("SET_G11(124)")
    rt5.execute('SET_PAID("v1;88929:900:1")')
    load(rt5)
    pump(rt5, 12)
    rt5.execute("SET_CAMO_PROGRESS(57201, 100)")
    pump(rt5, 24)
    check("B: a gate that says no is one line and no card, never forced",
          rt5.eval("NEVENTS()") == 0
          and count_line(lines_of(rt5), "camo card id=57201 row=sat_pi_atlas target=100 no route") == 1,
          " | ".join([x for x in lines_of(rt5) if "camo card" in x][:2]))

    rt6 = new_rt(lua51, src=False)
    rt6.execute(PRE)
    rt6.execute("SET_CAMO_ROW('sat_pi_atlas', 57201, {100, 200, 300, 400, 500, 600, 700, 800, 900})")
    rt6.execute("SET_CAMO_PROGRESS(57201, 0)")
    rt6.execute("SET_G11(125)")
    rt6.execute('SET_PAID("v1;88929:900:1")')
    load(rt6)
    pump(rt6, 12)
    rt6.execute("SET_CAMO_PROGRESS(57201, 900)")
    pump(rt6, 220)
    check("B: all nine tiers of one row card in one match - no card is capped away",
          rt6.eval("NAMED('completed_challenge')") == 9
          and not has_line(lines_of(rt6), "cards this match")
          and count_line(lines_of(rt6), "camo card id=57201") == 9,
          "%s | %s" % (rt6.eval("NAMED('completed_challenge')"),
                       count_line(lines_of(rt6), "camo card id=57201")))


def daily_cards(lua51):
    PRE = CAMOSTUB + """
SHOULD = true
DAILYLIST = {}
WEEKLYLIST = {}
function SET_DAILY(id, amount, ref)
  DAILYLIST[#DAILYLIST + 1] = { id = id, amount = amount, ref = ref, kind = 438 }
end
function SET_WEEKLY(id, amount, ref)
  WEEKLYLIST[#WEEKLYLIST + 1] = { id = id, amount = amount, ref = ref, kind = 585 }
end
Challenge[xhash("getchallengesforcurrentgamemode")] = function(c) return DAILYLIST end
Challenge[xhash("getweeklychallenges")] = function(c, kind) return WEEKLYLIST end
Challenge[xhash("GetAEKindID")] = function(name) return 7000 end
function SET_CHAL_PROGRESS(id, v) OC[tostring(id)] = { xp = v, rank = 0 } end
"""
    rt = new_rt(lua51, src=False)
    rt.execute(PRE)
    rt.execute("SET_DAILY(53310, '75', 'sat_daily_zm_ch_p1_kills_melee')")
    rt.execute("SET_WEEKLY(60330, '3', 'sat_weekly_zm_s1w1_kills')")
    rt.execute("SET_CHAL_PROGRESS(53310, 40)")
    rt.execute("SET_CHAL_PROGRESS(60330, 1)")
    rt.execute("SET_G11(130)")
    load(rt)
    pump(rt, 12)
    l = lines_of(rt)
    check("D: the active daily and weekly rows are the watch set, read from the client",
          has_line(l, "chal watch n=2 daily=1 weekly=1 tries=1 why=ok")
          and has_line(l, "daily prime id=53310 row=sat_daily_zm_ch_p1_kills_melee value=40 target=75"),
          " | ".join([x for x in l if ("chal watch" in x or "daily prime" in x)][:3]))
    check("D: the first sighting primes silently", rt.eval("NEVENTS()") == 0, str(rt.eval("NEVENTS()")))
    rt.execute("SET_CHAL_PROGRESS(53310, 75)")
    pump(rt, 24)
    l = lines_of(rt)
    check("D: a completed daily draws exactly one card",
          rt.eval("NAMED('completed_challenge')") == 1, str(rt.eval("NAMED('completed_challenge')")))
    check("D: and the card carries the row's own kind, 438",
          int(rt.eval("LASTOF('completed_challenge').kind")) == 438
          and rt.eval("LASTOF('completed_challenge').id") == 53310,
          str(rt.eval("LASTOF('completed_challenge').kind")))
    check("D: the line names the row, the target and the route",
          has_line(l, "daily card id=53310 row=sat_daily_zm_ch_p1_kills_melee kind=438 target=75 value=75 route=A"),
          " | ".join([x for x in l if "daily card" in x][:2]))
    rt.execute("CLEAR()")
    rt.execute("SET_CHAL_PROGRESS(60330, 3)")
    pump(rt, 24)
    check("D: a completed weekly draws its own card, with kind 585",
          rt.eval("NAMED('completed_challenge')") == 1
          and int(rt.eval("LASTOF('completed_challenge').kind")) == 585
          and has_line(lines_of(rt), "daily card id=60330 row=sat_weekly_zm_s1w1_kills kind=585 target=3"),
          " | ".join([x for x in lines_of(rt) if "daily card" in x][:2]))
    rt.execute("SET_CHAL_PROGRESS(60330, 1)")
    pump(rt, 12)
    rt.execute("SET_CHAL_PROGRESS(60330, 3)")
    pump(rt, 24)
    check("D: the same id and amount never fires a second time",
          rt.eval("NAMED('completed_challenge')") == 1, str(rt.eval("NAMED('completed_challenge')")))
    rt.execute("SET_TOGGLE('pt_diag', 1)")
    pump(rt, 8)
    pump(rt, 8)
    blk = rc1d_lines(lines_of(rt))
    check("D: the diagnostic names the watch set, the cards it fired and every crossing it saw",
          has_line(blk, "Q13 cards watch n=2 tries=1 why=ok ids=53310/438,60330/585")
          and has_line(blk, "Q13 cards fired=2 cross=3 seen=53310:75,60330:3,60330:3"),
          " | ".join([x for x in blk if "Q13" in x][:3]))

    rt2 = new_rt(lua51, src=False)
    rt2.execute(PRE)
    rt2.execute("SET_DAILY(53310, '75', 'sat_daily_zm_ch_p1_kills_melee')")
    rt2.execute("SET_CHAL_PROGRESS(53310, 75)")
    rt2.execute("SET_G11(131)")
    load(rt2)
    pump(rt2, 12)
    check("D: a daily already complete at match start does not pop",
          rt2.eval("NEVENTS()") == 0 and has_line(lines_of(rt2), "daily prime id=53310"),
          " | ".join([x for x in lines_of(rt2) if "daily prime" in x][:2]))

    rt3 = new_rt(lua51, src=False, pre="SET_TOGGLE('pt_daily', 0)")
    rt3.execute(PRE)
    rt3.execute("SET_DAILY(53310, '75', 'sat_daily_zm_ch_p1_kills_melee')")
    rt3.execute("SET_CHAL_PROGRESS(53310, 40)")
    rt3.execute("SET_G11(132)")
    load(rt3)
    pump(rt3, 12)
    rt3.execute("SET_CHAL_PROGRESS(53310, 75)")
    pump(rt3, 24)
    check("D: pt_daily 0 draws no daily card at all",
          rt3.eval("NEVENTS()") == 0 and not has_line(lines_of(rt3), "daily card id="),
          str(rt3.eval("NEVENTS()")))

    rt4 = new_rt(lua51, src=False, pre="SET_TOGGLE('pt_daily', 0)")
    rt4.execute(PRE)
    rt4.execute("SET_DAILY(53310, '75', 'sat_daily_zm_ch_p1_kills_melee')")
    rt4.execute("SET_CHAL_PROGRESS(53310, 40)")
    rt4.execute("SET_CAMO_ROW('sat_pi_atlas', 57201, {100, 200, 300})")
    rt4.execute("SET_CAMO_PROGRESS(57201, 90)")
    rt4.execute("SET_G11(133)")
    rt4.execute('SET_PAID("v1;88929:900:1")')
    load(rt4)
    pump(rt4, 12)
    rt4.execute("SET_CAMO_PROGRESS(57201, 100)")
    rt4.execute("SET_CHAL_PROGRESS(53310, 75)")
    pump(rt4, 24)
    check("D: the daily switch does not touch the camo card - they are independent",
          rt4.eval("NAMED('completed_challenge')") == 1
          and has_line(lines_of(rt4), "camo card id=57201 row=sat_pi_atlas target=100 route=A")
          and not has_line(lines_of(rt4), "daily card id="),
          " | ".join([x for x in lines_of(rt4) if " card id=" in x][:3]))

    rt5 = new_rt(lua51, src=False, pre="SET_TOGGLE('pt_camo', 0)")
    rt5.execute(PRE)
    rt5.execute("SET_DAILY(53310, '75', 'sat_daily_zm_ch_p1_kills_melee')")
    rt5.execute("SET_CHAL_PROGRESS(53310, 40)")
    rt5.execute("SET_CAMO_ROW('sat_pi_atlas', 57201, {100, 200, 300})")
    rt5.execute("SET_CAMO_PROGRESS(57201, 90)")
    rt5.execute("SET_G11(134)")
    rt5.execute('SET_PAID("v1;88929:900:1")')
    load(rt5)
    pump(rt5, 12)
    rt5.execute("SET_CAMO_PROGRESS(57201, 100)")
    rt5.execute("SET_CHAL_PROGRESS(53310, 75)")
    pump(rt5, 24)
    check("D: and the camo switch does not touch the daily card",
          rt5.eval("NAMED('completed_challenge')") == 1
          and has_line(lines_of(rt5), "daily card id=53310") and not has_line(lines_of(rt5), "camo card id="),
          " | ".join([x for x in lines_of(rt5) if " card id=" in x][:3]))

    rt6 = new_rt(lua51, src=False)
    rt6.execute(PRE)
    rt6.execute("SET_WEEKLY(60330, '1|2|3|4|5|6|7|8|9', 'sat_weekly_zm_s1w1_kills')")
    rt6.execute("SET_CHAL_PROGRESS(60330, 0)")
    rt6.execute("SET_G11(135)")
    load(rt6)
    pump(rt6, 12)
    rt6.execute("SET_CHAL_PROGRESS(60330, 9)")
    pump(rt6, 220)
    check("D: all nine weekly tiers card in one match - no card is capped away",
          rt6.eval("NAMED('completed_challenge')") == 9
          and not has_line(lines_of(rt6), "cards this match")
          and count_line(lines_of(rt6), "daily card id=60330") == 9,
          "%s | %s" % (rt6.eval("NAMED('completed_challenge')"),
                       count_line(lines_of(rt6), "daily card id=60330")))

    rt7 = new_rt(lua51, src=False)
    rt7.execute(PRE)
    rt7.execute("SET_SHOULD(false)")
    rt7.execute("SET_DAILY(53310, '75', 'sat_daily_zm_ch_p1_kills_melee')")
    rt7.execute("SET_CHAL_PROGRESS(53310, 40)")
    rt7.execute("SET_G11(136)")
    load(rt7)
    pump(rt7, 12)
    rt7.execute("SET_CHAL_PROGRESS(53310, 75)")
    pump(rt7, 24)
    check("D: a gate that says no is one line and no card, never forced",
          rt7.eval("NEVENTS()") == 0
          and count_line(lines_of(rt7), "daily card id=53310 row=sat_daily_zm_ch_p1_kills_melee kind=438 "
                                        "target=75 no route") == 1,
          " | ".join([x for x in lines_of(rt7) if "daily card" in x][:2]))


CamoZMStub = CAMOSTUB + """
SET_GUN("sat_pi_alcor", 68333)
SET_MINXP("sat_pi_alcor", { 1000, 2200, 3400 })
SET_LOOT_REF(125186, "sat_pi_alcor")
SET_LOOT_REF(126469, "sat_me_nashira")
Enum = Enum or {}
Enum.gameModeKey = { mp = 11, zm = 12, ob = 13, br = 14 }
WEAPON_CAMO[xhash("challengegamemode")] = { ob = 4, dmz = 5, zm = 2, wz = 3, none = 0, mp = 1 }
WEAPON_CAMO[xhash("gamemodekeytochallengegamemode")] =
  { [Enum.gameModeKey.mp] = 1, [Enum.gameModeKey.zm] = 2, [Enum.gameModeKey.br] = 3, [Enum.gameModeKey.ob] = 4 }
CAMOBYMODE = {}
SEENMODE = nil
function SET_MODE_ROW(ref, mode, id, amounts)
  CAMOBYMODE[ref] = CAMOBYMODE[ref] or {}
  local t = {}
  for i = 1, #amounts do t[i] = { id = id, amount = amounts[i] } end
  CAMOBYMODE[ref][mode] = t
end
Game[xhash("GetActiveGameModeKey")] = function() return Enum.gameModeKey.zm end
function SET_MODE_KEY(k) Game[xhash("GetActiveGameModeKey")] = function() return k end end
WEAPON_CAMO[xhash("getmilitarycamochallenges")] = function(c, ref, mode)
  SEENMODE = mode
  local bym = CAMOBYMODE[ref]
  if not bym then return nil end
  return bym[mode]
end
"""


def camo_zm_rows(lua51):
    PRE = CamoZMStub
    rt = new_rt(lua51, src=False)
    rt.execute(PRE)
    rt.execute("SET_MODE_ROW('sat_pi_alcor', 1, 68922, {'5', '10', '20'})")
    rt.execute("SET_MODE_ROW('sat_pi_alcor', 2, 68970, {'100', '200', '300'})")
    rt.execute("SET_CAMO_PROGRESS(68970, 40)")
    rt.execute("SET_CAMO_PROGRESS(68922, 0)")
    rt.execute("SET_G11(140)")
    rt.execute('SET_PAID("v1;125186:900:1")')
    load(rt)
    pump(rt, 12)
    l = lines_of(rt)
    check("E: the mode key is mapped to the client's own camo challenge mode before the call",
          rt.eval("SEENMODE") == 2, str(rt.eval("SEENMODE")))
    check("E: in a Zombies match the watched row is the ZM row, and the multiplayer row is not watched",
          has_line(l, "camo watch id=68970") and not has_line(l, "camo watch id=68922")
          and not has_line(l, "68922"),
          " | ".join([x for x in l if "camo watch" in x][:2]))
    check("E: the watch line names the row, its targets and the mode it was asked for",
          has_line(l, "camo watch id=68970 ref=sat_pi_alcor tiers=3 first=100 last=300 mode=2 key=12"),
          " | ".join([x for x in l if "camo watch id=" in x][:1]))
    check("E: the first sighting primes the ZM row silently", rt.eval("NEVENTS()") == 0,
          str(rt.eval("NEVENTS()")))
    rt.execute("SET_CAMO_PROGRESS(68970, 100)")
    pump(rt, 24)
    l = lines_of(rt)
    check("E: a hundred kills on the ZM row draws exactly one card, for that row",
          rt.eval("NAMED('completed_challenge')") == 1
          and rt.eval("LASTOF('completed_challenge').id") == 68970,
          str(rt.eval("LASTOF('completed_challenge').id")))
    check("E: the card line names the row, the target and the route",
          has_line(l, "camo card id=68970 row=sat_pi_alcor target=100 route=A value=100 tier=1"),
          " | ".join([x for x in l if "camo card" in x][:2]))
    check("E: and no card is ever drawn for the multiplayer row",
          not has_line(l, "camo card id=68922") and count_line(l, "camo cross id=68970") == 1,
          " | ".join([x for x in l if "camo cross" in x][:2]))
    rt.execute("SET_CAMO_PROGRESS(68970, 200)")
    pump(rt, 24)
    check("E: the next tier is one more card, keyed by its own target",
          rt.eval("NAMED('completed_challenge')") == 2
          and has_line(lines_of(rt), "camo card id=68970 row=sat_pi_alcor target=200 route=A value=200 tier=2"),
          " | ".join([x for x in lines_of(rt) if "camo card" in x][:3]))
    rt.execute("SET_TOGGLE('pt_diag', 1)")
    pump(rt, 8)
    pump(rt, 8)
    blk = rc1d_lines(lines_of(rt))
    check("E: the diagnostic names the mode it answered and each row's value and tier count",
          has_line(blk, "Q12 camo watch n=1 ids=68970 fired=2 cross=2 mode=2 key=12")
          and has_line(blk, "Q12 camo rows 68970:200/100:h2:sat_pi_alcor"),
          " | ".join([x for x in blk if "Q12" in x][:3]))

    rt2 = new_rt(lua51, src=False)
    rt2.execute(PRE)
    rt2.execute("SET_MODE_KEY(99)")
    rt2.execute("SET_MODE_ROW('sat_pi_alcor', 1, 68922, {'5', '10', '20'})")
    rt2.execute("SET_MODE_ROW('sat_pi_alcor', 2, 68970, {'100', '200', '300'})")
    rt2.execute("SET_CAMO_PROGRESS(68922, 0)")
    rt2.execute("SET_G11(141)")
    rt2.execute('SET_PAID("v1;125186:900:1")')
    load(rt2)
    pump(rt2, 12)
    check("E: a mode key the client's map does not name falls back to its own mp, not to no mode",
          rt2.eval("SEENMODE") == 1 and has_line(lines_of(rt2), "camo watch id=68922 ref=sat_pi_alcor tiers=3"
                                                               " first=5 last=20 mode=1 key=99"),
          " | ".join([x for x in lines_of(rt2) if "camo watch id=" in x][:1]))


WeeklyStub = CAMOSTUB + """
WeeklyChallenge = WeeklyChallenge or {}
WEEKOPT = nil
WEEKLIST = {}
DAILYROWS = {}
function SET_CHAL_PROGRESS(id, v) OC[tostring(id)] = { xp = v, rank = 0 } end
function SET_DAILY_ROW(id, amount, ref)
  DAILYROWS[#DAILYROWS + 1] = { id = id, amount = amount, ref = ref, kind = 438 }
end
function SET_WEEKLY_FLAT(id, amount, ref, value)
  WEEKLIST[#WEEKLIST + 1] = { achievementID = id, data = { id = id, amount = amount, ref = ref },
                              progress = { default = value }, isComplete = false }
end
Challenge[xhash("getchallengesforcurrentgamemode")] = function(c) return DAILYROWS end
Challenge[xhash("GetAEKindID")] = function(name) return 7000 end
if WeeklyChallenge then
  WeeklyChallenge[xhash("getallweeklychallenges")] = function(c, opts)
    WEEKOPT = opts
    return WEEKLIST
  end
end
"""


def weekly_rows(lua51):
    PRE = WeeklyStub
    rt = new_rt(lua51, src=False)
    rt.execute(PRE)
    rt.execute("SET_DAILY_ROW(53310, '75', 'sat_daily_zm_ch_p1_kills_melee')")
    rt.execute("SET_WEEKLY_FLAT(60330, '3', 'sat_weekly_zm_s1w1_kills', 1)")
    rt.execute("SET_WEEKLY_FLAT(60325, '25', 'sat_weekly_zm_s1w2_medals_slaughter', 0)")
    rt.execute("SET_CHAL_PROGRESS(53310, 40)")
    rt.execute("SET_CHAL_PROGRESS(60330, 1)")
    rt.execute("SET_CHAL_PROGRESS(60325, 0)")
    rt.execute("SET_G11(150)")
    load(rt)
    pump(rt, 12)
    l = lines_of(rt)
    check("F: the weeklies come from the client's own WeeklyChallenge list, one level deep",
          has_line(l, "chal watch n=3 daily=1 weekly=2 tries=1 why=ok"),
          " | ".join([x for x in l if "chal watch" in x][:2]))
    check("F: and the client is asked for the incomplete rows only",
          rt.eval("WEEKOPT") is not None and rt.eval("WEEKOPT.includeComplete") is False,
          str(rt.eval("WEEKOPT")))
    check("F: the weekly rows are watched with their own ids, kinds and targets",
          has_line(l, "chal watch row id=60330 kind=585 ref=sat_weekly_zm_s1w1_kills target=3")
          and has_line(l, "chal watch row id=60325 kind=585"),
          " | ".join([x for x in l if "chal watch row" in x][:3]))
    rt.execute("SET_CHAL_PROGRESS(60330, 3)")
    pump(rt, 24)
    l = lines_of(rt)
    check("F: a weekly crossing its target draws exactly one card of its own kind",
          rt.eval("NAMED('completed_challenge')") == 1
          and int(rt.eval("LASTOF('completed_challenge').kind")) == 585
          and rt.eval("LASTOF('completed_challenge').id") == 60330,
          "%s / %s" % (rt.eval("LASTOF('completed_challenge').kind"),
                       rt.eval("LASTOF('completed_challenge').id")))
    check("F: and the line names the row, its kind, the target and the route",
          has_line(l, "daily card id=60330 row=sat_weekly_zm_s1w1_kills kind=585 target=3 value=3 route=A"),
          " | ".join([x for x in l if "daily card" in x][:2]))
    rt.execute("SET_CHAL_PROGRESS(60330, 1)")
    pump(rt, 12)
    rt.execute("SET_CHAL_PROGRESS(60330, 3)")
    pump(rt, 24)
    check("F: the same weekly id and amount never fires a second time",
          rt.eval("NAMED('completed_challenge')") == 1, str(rt.eval("NAMED('completed_challenge')")))
    rt.execute("SET_TOGGLE('pt_diag', 1)")
    pump(rt, 8)
    pump(rt, 8)
    blk = rc1d_lines(lines_of(rt))
    check("F: the diagnostic counts the dailies and the weeklies separately",
          has_line(blk, "Q13 cards watch n=3 tries=1 why=ok") and "daily=1 weekly=2" in "\n".join(blk),
          " | ".join([x for x in blk if "Q13 cards watch" in x][:2]))

    nested = WeeklyStub.replace('WeeklyChallenge = WeeklyChallenge or {}',
                                'WeeklyChallenge = nil')
    rt2 = new_rt(lua51, src=False)
    rt2.execute(nested)
    rt2.execute("""
Challenge[xhash("getweeklychallenges")] = function(c, kind)
  return { { numComplete = 0, isWeekLocked = false },
           { { id = 60330, amount = "3", ref = "sat_weekly_zm_s1w1_kills", kind = 585 } } }
end
""")
    rt2.execute("SET_DAILY_ROW(53310, '75', 'sat_daily_zm_ch_p1_kills_melee')")
    rt2.execute("SET_CHAL_PROGRESS(53310, 40)")
    rt2.execute("SET_CHAL_PROGRESS(60330, 1)")
    rt2.execute("SET_G11(151)")
    load(rt2)
    pump(rt2, 12)
    l2 = lines_of(rt2)
    check("F: without WeeklyChallenge in the VM, the week buckets getweeklychallenges answers are read "
          "one level down",
          has_line(l2, "chal watch n=2 daily=1 weekly=1 tries=1 why=ok")
          and has_line(l2, "chal watch row id=60330 kind=585 ref=sat_weekly_zm_s1w1_kills target=3"),
          " | ".join([x for x in l2 if "chal watch" in x][:3]))
    rt2.execute("SET_CHAL_PROGRESS(60330, 3)")
    pump(rt2, 24)
    check("F: and a weekly found that way still draws its card once",
          rt2.eval("NAMED('completed_challenge')") == 1
          and has_line(lines_of(rt2), "daily card id=60330 row=sat_weekly_zm_s1w1_kills kind=585 target=3"),
          " | ".join([x for x in lines_of(rt2) if "daily card" in x][:2]))

    rt3 = new_rt(lua51, src=False, pre="SET_TOGGLE('pt_camo', 0)")
    rt3.execute(PRE)
    rt3.execute("SET_DAILY_ROW(53310, '75', 'sat_daily_zm_ch_p1_kills_melee')")
    rt3.execute("SET_WEEKLY_FLAT(60330, '3', 'sat_weekly_zm_s1w1_kills', 1)")
    rt3.execute("SET_CAMO_ROW('sat_pi_atlas', 57201, {100, 200, 300})")
    rt3.execute("SET_CHAL_PROGRESS(53310, 40)")
    rt3.execute("SET_CHAL_PROGRESS(60330, 1)")
    rt3.execute("SET_CAMO_PROGRESS(57201, 90)")
    rt3.execute("SET_G11(152)")
    rt3.execute('SET_PAID("v1;88929:900:1")')
    load(rt3)
    pump(rt3, 12)
    rt3.execute("SET_CAMO_PROGRESS(57201, 100)")
    rt3.execute("SET_CHAL_PROGRESS(60330, 3)")
    pump(rt3, 24)
    check("F: pt_camo 0 leaves the weekly card alone - the two switches stay independent",
          rt3.eval("NAMED('completed_challenge')") == 1
          and has_line(lines_of(rt3), "daily card id=60330 row=sat_weekly_zm_s1w1_kills")
          and not has_line(lines_of(rt3), "camo card id="),
          " | ".join([x for x in lines_of(rt3) if " card id=" in x][:3]))


SweepStub = CamoZMStub + """
Challenge[xhash("GetAEKindID")] = function(name)
  if name == "ae_kind_zm_weekly" then return 585 end
  if name == "ae_kind_weekly" then return 590 end
  if name == "ae_kind_weekly_mastery" then return 592 end
  if name == "ae_kind_reticle" then return 315 end
  return nil
end
Challenge[xhash("isweeklychallengetype")] = function(k) return k == 585 or k == 590 end
DAILYROWS = {}
function SET_DAILY_ROW(id, amount, ref)
  DAILYROWS[#DAILYROWS + 1] = { id = id, amount = amount, ref = ref, kind = 438 }
end
Challenge[xhash("getchallengesforcurrentgamemode")] = function(c) return DAILYROWS end
DB = {}
function SET_DVARBOOL(name, v) DB[name] = v end
Dvar[xhash("GetDvarBool")] = function(k) return DB[k] end
WSTORE = { [585] = {}, [590] = {}, [592] = {} }
WROW = {}
function SET_WEEK(id, kind, amount, ref, value, status)
  WSTORE[kind][id] = { progress = { default = value }, status = status }
  WROW[id] = { id = id, amount = amount, ref = ref, kind = kind }
end
function SET_WEEK_STATUS(kind, id, status, value)
  WSTORE[kind][id] = { progress = { default = value }, status = status }
end
function DROP_FORK() OnlineChallenges[xhash("getchallengesprogressforkind")] = nil end
OnlineChallenges[xhash("getchallengesprogressforkind")] = function(c, kind) return WSTORE[kind] end
WeeklyChallenge = {}
WeeklyChallenge[xhash("getweeklychallengedatabyid")] = function(id) return WROW[id] end
WLIST = {}
function SET_WEEK_LIST(id, amount, ref, kind, value)
  WLIST[#WLIST + 1] = { achievementID = id, data = { id = id, amount = amount, ref = ref, kind = kind },
                        progress = { default = value }, isComplete = false }
end
function DROP_WEEK_LIST() WLIST = {} end
WeeklyChallenge[xhash("getallweeklychallenges")] = function(c, o)
  local t = {}
  for i = 1, #WLIST do t[i] = WLIST[i] end
  return t
end
"""


FamilyStub = CamoZMStub + """
SPECIALS = {}
function SET_SPECIAL(ref, loots)
  local t = {}
  for i = 1, #loots do t[i] = { lootid = loots[i] } end
  SPECIALS[ref] = t
end
WEAPON_CAMO[xhash("getspecialcamos")] = function(c, ref, mode) return SPECIALS[ref] end
CENTRY = {}
function SET_CENTRY(loot, id, amount, ref)
  CENTRY[loot] = { id = id, amount = amount, ref = ref, lootId = loot }
end
WEAPON_CAMO[xhash("getcamochallengefromlootid")] = function(c, loot) return CENTRY[loot] end
PROGS = {}
function SET_BUNDLES(ref, lists) PROGS[ref] = lists end
WEAPON_CAMO[xhash("getprogressioncamos")] = function(c, mode, ref)
  local l = PROGS[ref]
  if not l then return {}, {}, {} end
  return l[1], l[2], l[3]
end
BENTS = {}
function SET_BENTRIES(bundle, list) BENTS[bundle] = list end
WEAPON_CAMO[xhash("getcamochallengesfrombundle")] = function(c, b, ref, opts) return BENTS[b] or {} end
WEAPON_CAMO[xhash("isgatemasterychallenge")] = function(ref, mode) return false end
function SET_SPECIALS_N(ref, baseid, baseloot, n)
  local t = {}
  for i = 1, n do
    local lid = baseloot + i
    t[i] = { lootid = lid }
    CENTRY[lid] = { id = baseid + i, amount = 100 + i, ref = ref .. '_camo_zm_unique' .. i, lootId = lid }
  end
  SPECIALS[ref] = t
end
"""

ALCOR_ROWS = """
SET_MODE_ROW('sat_pi_alcor', 2, 68970, {'100', '200', '300'})
SET_SPECIAL('sat_pi_alcor', { 132704, 132755, 132716 })
SET_CENTRY(132704, 68971, 300, 'sat_pi_alcor_camo_zm_unique1')
SET_CENTRY(132755, 68972, 100, 'sat_pi_alcor_camo_zm_unique2')
SET_CENTRY(132716, 68973, 300, 'sat_pi_alcor_camo_zm_unique3')
GOLDB = { id = 9001, CamoChallenges = { { challengeid = 68976 } } }
SET_BUNDLES('sat_pi_alcor', { {}, {}, { GOLDB } })
SET_BENTRIES(GOLDB, {
  { id = 68976, amount = 15, ref = 'sat_pi_alcor_camo_zm_gold', lootId = 132916 },
  { id = 68978, amount = 3, ref = 'sat_pi_alcor_camo_zm_gold_unlock', isAdditional = true } })
"""

NASHIRA_ROWS = """
SET_GUN('sat_me_nashira', 69098)
SET_MINXP('sat_me_nashira', { 1000 })
SET_LOOT_REF(126469, 'sat_me_nashira')
SET_MODE_ROW('sat_me_nashira', 2, 69098, {'100'})
SET_SPECIAL('sat_me_nashira', { 140001 })
SET_CENTRY(140001, 69099, 50, 'sat_me_nashira_camo_zm_unique1')
NB1 = { id = 9101, CamoChallenges = { { challengeid = 69101 } } }
NB2 = { id = 9102, CamoChallenges = { { challengeid = 69102 } } }
SET_BUNDLES('sat_me_nashira', { {}, {}, { NB1, NB2 } })
SET_BENTRIES(NB1, { { id = 69101, amount = 5, ref = 'sat_me_nashira_camo_zm_gold', lootId = 150001 } })
SET_BENTRIES(NB2, { { id = 69102, amount = 7, ref = 'sat_me_nashira_camo_zm_diamond', lootId = 150002 } })
"""


def week_sweep(lua51):
    PRE = SweepStub
    rt = new_rt(lua51, src=False)
    rt.execute(PRE)
    for i in range(12):
        kind = 592 if i >= 9 else 585
        rt.execute("SET_WEEK(%d, %d, '5', 'sat_weekly_zm_t%d', 1, 1)" % (70000 + i, kind, i))
    rt.execute("SET_G11(200)")
    load(rt)
    pump(rt, 24)
    l = lines_of(rt)
    check("G: the sweep holds the client's whole weekly list, past the old window of nine",
          has_line(l, "chal sweep src=fork kind=585,590,592 n=12 done=0 prog=12"),
          " | ".join([x for x in l if "chal sweep" in x][:2]))
    check("G: and it names each weekly kind it swept with that kind's row count",
          has_line(l, "chal sweep kinds zm_weekly=585 weekly=590 mastery=592 rows=9/0/3"),
          " | ".join([x for x in l if "chal sweep kinds" in x][:1]))
    check("G: the first sweep primes silently, so no weekly is carded at match start",
          rt.eval("NEVENTS()") == 0, str(rt.eval("NEVENTS()")))
    for i in range(12):
        kind = 592 if i >= 9 else 585
        rt.execute("SET_WEEK_STATUS(%d, %d, 3, 5)" % (kind, 70000 + i))
    pump(rt, 200)
    l = lines_of(rt)
    check("G: every one of the twelve completions is carded, so no cap can hide one",
          rt.eval("NAMED('add_message_splash_manager')") == 9
          and rt.eval("NAMED('completed_challenge')") == 3
          and count_line(l, "chal week cross id=") == 12
          and not has_line(l, "cards this match"),
          "%s / %s / %s" % (rt.eval("NAMED('add_message_splash_manager')"),
                            rt.eval("NAMED('completed_challenge')"),
                            count_line(l, "chal week cross id=")))

    rt = new_rt(lua51, src=False)
    rt.execute(PRE)
    rt.execute("SET_WEEK(70100, 585, '5', 'sat_weekly_zm_a', 1, 1)")
    rt.execute("SET_WEEK(70101, 592, '9', 'sat_weekly_zm_mastery_a', 1, 1)")
    rt.execute("SET_DVARBOOL('lui_weekly_challenge_menu_enabled', true)")
    rt.execute("SET_G11(201)")
    load(rt)
    pump(rt, 24)
    rt.execute("SET_WEEK_STATUS(585, 70100, 3, 5)")
    rt.execute("SET_WEEK_STATUS(592, 70101, 3, 9)")
    pump(rt, 40)
    l = lines_of(rt)
    check("G: a weekly flip draws its card with the row's own kind, 585 and 592 - never a fixed 585",
          has_line(l, "weekly card id=70100 row=sat_weekly_zm_a kind=585 target=5 value=5 route=B")
          and has_line(l, "daily card id=70101 row=sat_weekly_zm_mastery_a kind=592 target=9 value=9 route=A"),
          " | ".join([x for x in l if " card id=" in x][:3]))
    check("G: and the weekly line carries the client's own gate, dvar and type answer",
          has_line(l, "chal week card id=70100 ref=sat_weekly_zm_a kind=585 enabled=true isweekly=true"
                      " splash=true route=B")
          and has_line(l, "chal week card id=70101 ref=sat_weekly_zm_mastery_a kind=592 enabled=true"
                          " isweekly=false splash=true route=A"),
          " | ".join([x for x in l if "chal week card" in x][:2]))
    rt.execute("SET_WEEK_STATUS(585, 70100, 1, 1)")
    pump(rt, 32)
    rt.execute("SET_WEEK_STATUS(585, 70100, 3, 5)")
    pump(rt, 32)
    check("G: the same weekly id and target never fires a second card",
          rt.eval("NAMED('add_message_splash_manager')") == 1
          and rt.eval("NAMED('completed_challenge')") == 1,
          "%s / %s" % (rt.eval("NAMED('add_message_splash_manager')"),
                       rt.eval("NAMED('completed_challenge')")))

    rt = new_rt(lua51, src=False)
    rt.execute(PRE)
    rt.execute("SET_WEEK(70200, 585, '3', 'sat_weekly_zm_done', 3, 3)")
    rt.execute("SET_G11(202)")
    load(rt)
    pump(rt, 24)
    l = lines_of(rt)
    check("G: a weekly already complete when the sweep primes draws nothing",
          has_line(l, "chal sweep src=fork kind=585,590,592 n=1 done=1 prog=1")
          and rt.eval("NEVENTS()") == 0,
          " | ".join([x for x in l if "chal sweep" in x][:1]))

    rt = new_rt(lua51, src=False)
    rt.execute(PRE)
    rt.execute("DROP_FORK()")
    rt.execute("SET_WEEK_LIST(70300, '4', 'sat_weekly_zm_list_a', 585, 1)")
    rt.execute("SET_WEEK_LIST(70301, '4', 'sat_weekly_zm_list_b', 585, 1)")
    rt.execute("SET_G11(203)")
    load(rt)
    pump(rt, 24)
    l = lines_of(rt)
    check("G: without the store call the client's own weekly list is the source, by presence",
          has_line(l, "chal sweep src=list kind=585,590,592 n=2 done=0 prog=2"),
          " | ".join([x for x in l if "chal sweep" in x][:1]))
    rt.execute("DROP_WEEK_LIST()")
    pump(rt, 40)
    l = lines_of(rt)
    check("G: a weekly that disappears from that list is carded as a completion",
          count_line(l, "chal week cross id=70300 ref=sat_weekly_zm_list_a was=1 now=gone") == 1
          and has_line(l, "weekly card id=70300 row=sat_weekly_zm_list_a kind=585 target=4 value=4 route=B"),
          " | ".join([x for x in l if "chal week cross" in x][:2]))

    rt = new_rt(lua51, src=False)
    rt.execute(PRE)
    rt.execute("DROP_FORK()")
    rt.execute("WeeklyChallenge[xhash('getallweeklychallenges')] = nil")
    rt.execute("SET_DAILY_ROW(53310, '75', 'sat_daily_zm_ch_p1_kills_melee')")
    rt.execute("SET_CAMO_PROGRESS(53310, 40)")
    rt.execute("SET_G11(204)")
    load(rt)
    pump(rt, 24)
    rt.execute("SET_CAMO_PROGRESS(53310, 75)")
    pump(rt, 40)
    l = lines_of(rt)
    check("G: with neither weekly source in the VM one line says so, once, and nothing is raised",
          count_line(l, "chal sweep unavailable - no OnlineChallenges.getchallengesprogressforkind") == 1
          and not has_line(l, "progression_tuning: error"),
          " | ".join([x for x in l if "chal sweep" in x or "error" in x][:3]))
    check("G: and the dailies still card through the untouched path",
          has_line(l, "daily card id=53310 row=sat_daily_zm_ch_p1_kills_melee kind=438 target=75"),
          " | ".join([x for x in l if "daily card" in x][:2]))


def camo_families(lua51):
    PRE = FamilyStub
    rt = new_rt(lua51, src=False)
    rt.execute(PRE)
    rt.execute(ALCOR_ROWS)
    for i in (68970, 68971, 68972, 68973, 68976, 68978):
        rt.execute("SET_CAMO_PROGRESS(%d, 0)" % i)
    rt.execute("SET_G11(210)")
    rt.execute("SET_PAID('v1;125186:900:1')")
    load(rt)
    pump(rt, 16)
    l = lines_of(rt)
    check("H: the weapon's camo rows are enumerated per family by the client's own calls",
          has_line(l, "camo rows id=68970 ref=sat_pi_alcor base=1 special=3 mastery=1 extra=1"),
          " | ".join([x for x in l if "camo rows" in x][:2]))
    check("H: a gate row is a requirement, never a watched camo",
          not has_line(l, "camo prime id=68978") and not has_line(l, "camo card id=68978"),
          " | ".join([x for x in l if "68978" in x][:2]))
    check("H: every special and the gold task prime silently",
          has_line(l, "camo prime id=68971") and has_line(l, "camo prime id=68976")
          and rt.eval("NEVENTS()") == 0, str(rt.eval("NEVENTS()")))
    rt.execute("SET_CAMO_PROGRESS(68971, 300)")
    rt.execute("SET_CAMO_PROGRESS(68976, 15)")
    pump(rt, 32)
    l = lines_of(rt)
    check("H: a special camo and a mastery camo each card on their own target, route A, kind 398",
          has_line(l, "camo card id=68971 row=sat_pi_alcor_camo_zm_unique1 target=300 route=A value=300 tier=1")
          and has_line(l, "camo card id=68976 row=sat_pi_alcor_camo_zm_gold target=15 route=A value=15 tier=1")
          and int(rt.eval("LASTOF('completed_challenge').kind")) == 398,
          " | ".join([x for x in l if "camo card" in x][:3]))
    rt.execute("SET_CAMO_PROGRESS(68970, 100)")
    pump(rt, 16)
    check("H: the military row still cards its own tiers, unchanged",
          has_line(lines_of(rt), "camo card id=68970 row=sat_pi_alcor target=100 route=A value=100 tier=1"),
          " | ".join([x for x in lines_of(rt) if "68970 row=" in x][:2]))
    rt.execute("SET_TOGGLE('pt_diag', 1)")
    pump(rt, 8)
    pump(rt, 8)
    blk = rc1d_lines(lines_of(rt))
    check("H: the diagnostic counts each family for the weapon and names the camo gate",
          has_line(blk, "Q14 camo rows n=4 sat_pi_alcor:b1/s3/m1/x1")
          and has_line(blk, "Q14 gate kind=398 id=68970 answer=true"),
          " | ".join([x for x in blk if "Q14" in x][:3]))

    rt2 = new_rt(lua51, src=False)
    rt2.execute(PRE)
    rt2.execute(NASHIRA_ROWS)
    rt2.execute("SET_CAMO_PROGRESS(69098, 0)")
    rt2.execute("SET_G11(211)")
    rt2.execute("SET_PAID('v1;126469:800:1')")
    load(rt2)
    pump(rt2, 16)
    check("H: a second weapon enumerates its own counts - one special, two mastery",
          has_line(lines_of(rt2), "camo rows id=69098 ref=sat_me_nashira base=1 special=1 mastery=2 extra=0"),
          " | ".join([x for x in lines_of(rt2) if "camo rows" in x][:2]))

    rt3 = new_rt(lua51, src=False)
    rt3.execute(PRE)
    rt3.execute(NASHIRA_ROWS)
    rt3.execute("SET_CAMO_PROGRESS(69098, 0)")
    rt3.execute("SET_G11(212)")
    rt3.execute("SET_PAID('v1;125186:900:1')")
    load(rt3)
    pump(rt3, 16)
    before = has_line(lines_of(rt3), "camo rows id=69098")
    rt3.execute("SET_PAID('v1;125186:900:1;126469:800:1')")
    pump(rt3, 16)
    check("H: a weapon that becomes held mid-match is enumerated then, not at load",
          before is False and has_line(lines_of(rt3), "camo rows id=69098 ref=sat_me_nashira"),
          "%s | %s" % (before, " | ".join([x for x in lines_of(rt3) if "camo rows" in x][:2])))

    rt4 = new_rt(lua51, src=False)
    rt4.execute(PRE)
    rt4.execute("WEAPON_CAMO[xhash('getspecialcamos')] = nil")
    rt4.execute(ALCOR_ROWS)
    rt4.execute("SET_CAMO_PROGRESS(68970, 0)")
    rt4.execute("SET_CAMO_PROGRESS(68976, 0)")
    rt4.execute("SET_G11(213)")
    rt4.execute("SET_PAID('v1;125186:900:1')")
    load(rt4)
    pump(rt4, 16)
    l4 = lines_of(rt4)
    check("H: with getspecialcamos absent one line says so and the mastery rows still arrive",
          count_line(l4, "camo special unavailable for sat_pi_alcor - no WEAPON_CAMO.getspecialcamos") == 1
          and has_line(l4, "camo rows id=68970 ref=sat_pi_alcor base=1 special=0 mastery=1")
          and not has_line(l4, "progression_tuning: error"),
          " | ".join([x for x in l4 if "camo " in x][:3]))

    rt5 = new_rt(lua51, src=False)
    rt5.execute(PRE)
    rt5.execute("WEAPON_CAMO[xhash('getprogressioncamos')] = nil")
    rt5.execute(ALCOR_ROWS)
    rt5.execute("SET_CAMO_PROGRESS(68970, 0)")
    rt5.execute("SET_CAMO_PROGRESS(68971, 0)")
    rt5.execute("SET_G11(214)")
    rt5.execute("SET_PAID('v1;125186:900:1')")
    load(rt5)
    pump(rt5, 16)
    l5 = lines_of(rt5)
    check("H: with getprogressioncamos absent one line says so and the specials still arrive",
          count_line(l5, "camo bundles unavailable for sat_pi_alcor - no WEAPON_CAMO.getprogressioncamos") == 1
          and has_line(l5, "camo rows id=68970 ref=sat_pi_alcor base=1 special=3 mastery=0")
          and not has_line(l5, "progression_tuning: error"),
          " | ".join([x for x in l5 if "camo " in x][:3]))


RetStub = SweepStub + """
CSV.reticleChallenges = { file = "ret", cols = { id = "id", ref = "ref", amount = "amount", loot = "loot" },
  [xhash("GetFile")] = function(t) return "ret" end }
ROWS["ret"] = {}
function SET_RET(id, ref, amount)
  ROWS["ret"][tostring(id)] = { id = tostring(id), ref = ref, amount = amount }
end
RETCELL = {}
RETLOOT = {}
function SET_RETDATA(id, amount, loot)
  RETCELL[id] = amount
  RETLOOT[id] = loot
end
Challenge[xhash("getreticlechallengedata")] = function(idcol, id)
  if RETCELL[id] == nil then return nil end
  return { id = id, amount = RETCELL[id], loot = RETLOOT[id], ref = "row" }
end
GUNSMITH = {}
RETMAP = {}
function SET_RETTIERS(id, loots, amounts)
  local m = {}
  for i = 1, #amounts do m[loots[i]] = { id = id, amount = amounts[i], loot = loots[i] } end
  RETMAP[id] = m
end
GUNSMITH[xhash("getreticlechallengesforcategory")] = function(c, id) return RETMAP[id] end
function DROP_RETGUNSMITH() GUNSMITH[xhash("getreticlechallengesforcategory")] = nil end
function DROP_RETAPI() CSV.reticleChallenges = nil end
function RET_KIND_OFF()
  local f = Challenge[xhash("GetAEKindID")]
  Challenge[xhash("GetAEKindID")] = function(name) return f(name) end
end
"""

RET_SETUP = """
SET_MODE_ROW('sat_pi_alcor', 2, 68970, {'100'})
SET_CAMO_PROGRESS(68970, 0)
SET_RET(66938, 'sat_ch_reticle_zm_sat_microreflex07', '200|400|600')
SET_RET(56892, 'sat_ch_reticle_zm_sat_dualzoom01', '400|800')
SET_RET(57777, 'sat_ch_reticle_mp_sat_holo01', '50|100')
SET_RETTIERS(66938, { 129198, 129223, 129222 }, { 200, 400, 600 })
SET_RETTIERS(56892, { 110067, 110055 }, { 400, 800 })
SET_RETTIERS(57777, { 111111, 111112 }, { 50, 100 })
SET_RETDATA(66938, '200|400|600', '129198|129223|129222')
SET_RETDATA(56892, '400|800', '110067|110055')
SET_RETDATA(57777, '50|100', '111111|111112')
SET_CAMO_PROGRESS(66938, 59)
SET_CAMO_PROGRESS(56892, 0)
SET_CAMO_PROGRESS(57777, 0)
"""


def reticle_rows(lua51):
    PRE = RetStub
    rt = new_rt(lua51, src=False)
    rt.execute(PRE)
    rt.execute(RET_SETUP)
    rt.execute("SET_G11(220)")
    rt.execute("SET_PAID('v1;125186:900:1')")
    load(rt)
    pump(rt, 40)
    l = lines_of(rt)
    check("I: the reticle rows come from the mode's own list, one entry per optic row",
          has_line(l, "reticle rows n=2 zm=2 mode=2 kind=315 sample=56892,66938 cap=36"),
          " | ".join([x for x in l if "reticle rows" in x][:1]))
    check("I: the multiplayer optic row is never watched in a Zombies match",
          not has_line(l, "reticle prime id=57777"), " | ".join([x for x in l if "57777" in x][:1]))
    check("I: a reticle already past its first target primes silently",
          has_line(l, "reticle prime id=66938 row=sat_ch_reticle_zm_sat_microreflex07 value=59 tiers=3 hits=0")
          and rt.eval("NEVENTS()") == 0, " | ".join([x for x in l if "reticle prime" in x][:2]))
    rt.execute("SET_CAMO_PROGRESS(66938, 200)")
    pump(rt, 40)
    l = lines_of(rt)
    check("I: a reticle tier crossing cards once, with the reticle kind and that row",
          rt.eval("NAMED('completed_challenge')") == 1
          and int(rt.eval("LASTOF('completed_challenge').kind")) == 315
          and rt.eval("LASTOF('completed_challenge').id") == 66938,
          "%s / %s / %s" % (rt.eval("NAMED('completed_challenge')"),
                            rt.eval("LASTOF('completed_challenge').kind"),
                            rt.eval("LASTOF('completed_challenge').id")))
    check("I: and the line names the row, the target and the route",
          has_line(l, "reticle card id=66938 row=sat_ch_reticle_zm_sat_microreflex07 target=200 route=A"
                      " value=200 tier=1"),
          " | ".join([x for x in l if "reticle card" in x][:2]))
    rt.execute("SET_TOGGLE('pt_diag', 1)")
    pump(rt, 8)
    pump(rt, 8)
    blk = rc1d_lines(lines_of(rt))
    check("I: the diagnostic names the reticle gate and the optic the row belongs to",
          has_line(blk, "Q14 reticle rows n=2 zm=2 kind=315")
          and has_line(blk, "Q14 gate kind=315 id=66938 answer=true")
          and has_line(blk, "Q14 reticle 66938 itemref=") and has_line(blk, "name=ITEM 129198"),
          " | ".join([x for x in blk if "Q14" in x][:3]))

    rt2 = new_rt(lua51, src=False)
    rt2.execute(PRE)
    rt2.execute("DROP_RETGUNSMITH()")
    rt2.execute(RET_SETUP)
    rt2.execute("SET_G11(221)")
    rt2.execute("SET_PAID('v1;125186:900:1')")
    load(rt2)
    pump(rt2, 40)
    l2 = lines_of(rt2)
    check("I: without GUNSMITH the tiers come from the client's own row and one line says so",
          count_line(l2, "reticle tiers - GUNSMITH.getreticlechallengesforcategory unavailable") == 1
          and has_line(l2, "reticle rows n=2 zm=2") and not has_line(l2, "progression_tuning: error"),
          " | ".join([x for x in l2 if "reticle" in x][:2]))
    rt2.execute("SET_CAMO_PROGRESS(66938, 400)")
    pump(rt2, 40)
    check("I: and a crossing still cards from that fallback, target by target",
          has_line(lines_of(rt2), "reticle card id=66938 row=sat_ch_reticle_zm_sat_microreflex07"
                                  " target=400 route=A value=400 tier=2"),
          " | ".join([x for x in lines_of(rt2) if "reticle card" in x][:2]))

    rt3 = new_rt(lua51, src=False)
    rt3.execute(PRE)
    rt3.execute("DROP_RETAPI()")
    rt3.execute(RET_SETUP)
    rt3.execute("SET_G11(222)")
    rt3.execute("SET_PAID('v1;125186:900:1')")
    load(rt3)
    pump(rt3, 40)
    l3 = lines_of(rt3)
    check("I: without CSV.reticleChallenges one line says so and nothing is raised",
          count_line(l3, "reticle rows - CSV.reticleChallenges unavailable in this VM") == 1
          and not has_line(l3, "progression_tuning: error"),
          " | ".join([x for x in l3 if "reticle" in x or "error" in x][:3]))

    rt4 = new_rt(lua51, src=False)
    rt4.execute(PRE)
    rt4.execute("""
local ek0 = Challenge[xhash("GetAEKindID")]
Challenge[xhash("GetAEKindID")] = function(name)
  if name == "ae_kind_reticle" then return nil end
  return ek0(name)
end
""")
    rt4.execute(RET_SETUP)
    rt4.execute("SET_G11(223)")
    rt4.execute("SET_PAID('v1;125186:900:1')")
    load(rt4)
    pump(rt4, 40)
    l4 = lines_of(rt4)
    check("I: without the reticle aeKind one line says so and no card route is invented",
          count_line(l4, "reticle rows - Challenge.GetAEKindID refused ae_kind_reticle") == 1
          and not has_line(l4, "progression_tuning: error"),
          " | ".join([x for x in l4 if "reticle" in x or "error" in x][:3]))

    rt5 = new_rt(lua51, src=False)
    rt5.execute(PRE)
    rt5.execute(RET_SETUP)
    rt5.execute("SET_CAMO_PROGRESS(66938, 200)")
    rt5.execute("SET_G11(224)")
    rt5.execute("SET_PAID('v1;125186:900:1')")
    load(rt5)
    pump(rt5, 48)
    check("I: a reticle row already complete at the build stays silent",
          rt5.eval("NEVENTS()") == 0
          and has_line(lines_of(rt5), "reticle prime id=66938 row=sat_ch_reticle_zm_sat_microreflex07"
                                      " value=200 tiers=3 hits=1"),
          " | ".join([x for x in lines_of(rt5) if "reticle" in x][:2]))


THREE_GUNS = """
SET_MODE_ROW('sat_pi_alcor', 2, 68970, {'100'})
SET_GUN('sat_me_nashira', 69098)
SET_MINXP('sat_me_nashira', { 1000 })
SET_LOOT_REF(126469, 'sat_me_nashira')
SET_MODE_ROW('sat_me_nashira', 2, 69098, {'100'})
SET_GUN('sat_ar_flatline', 69000)
SET_MINXP('sat_ar_flatline', { 1000 })
SET_LOOT_REF(130001, 'sat_ar_flatline')
SET_MODE_ROW('sat_ar_flatline', 2, 69000, {'100'})
SET_SPECIALS_N('sat_pi_alcor', 75000, 200000, 10)
SET_SPECIALS_N('sat_me_nashira', 76000, 210000, 10)
SET_SPECIALS_N('sat_ar_flatline', 77000, 220000, 10)
"""


def camo_bursts(lua51):
    PRE = FamilyStub
    rt = new_rt(lua51, src=False)
    rt.execute(PRE)
    rt.execute("SET_MODE_ROW('sat_pi_alcor', 2, 68970, {'100', '200', '300', '400', '500', '600', '700', '800', '900'})")
    rt.execute(ALCOR_ROWS.replace("{'100', '200', '300'}", "{'100', '200', '300', '400', '500', '600', '700', '800', '900'}"))
    for i in (68970, 68971, 68972, 68973, 68976):
        rt.execute("SET_CAMO_PROGRESS(%d, 0)" % i)
    rt.execute("SET_G11(230)")
    rt.execute("SET_PAID('v1;125186:900:1')")
    load(rt)
    pump(rt, 16)
    rt.execute("SET_CAMO_PROGRESS(68970, 900)")
    rt.execute("SET_CAMO_PROGRESS(68971, 300)")
    rt.execute("SET_CAMO_PROGRESS(68972, 100)")
    rt.execute("SET_CAMO_PROGRESS(68973, 300)")
    pump(rt, 240)
    l = lines_of(rt)
    check("J: twelve completions on one weapon in one match draw twelve cards - nothing is capped away",
          rt.eval("NAMED('completed_challenge')") == 12
          and count_line(l, "camo card id=") == 12
          and not has_line(l, "cards this match"),
          "%s | %s" % (rt.eval("NAMED('completed_challenge')"), count_line(l, "camo card id=")))
    check("J: and the three specials and the ninth military tier are all among them",
          has_line(l, "camo card id=68971 row=sat_pi_alcor_camo_zm_unique1 target=300 route=A")
          and has_line(l, "camo card id=68973 row=sat_pi_alcor_camo_zm_unique3 target=300 route=A")
          and has_line(l, "camo card id=68970 row=sat_pi_alcor target=900 route=A value=900 tier=9"),
          " | ".join([x for x in l if "camo card" in x][-3:]))

    rt2 = new_rt(lua51, src=False)
    rt2.execute(PRE)
    rt2.execute("SET_MODE_ROW('sat_pi_alcor', 2, 68970, {'100', '200', '300', '400', '500', '600', '700', '800', '900', '1000'})")
    for i in (68970, 68971, 68972, 68973, 68976):
        rt2.execute("SET_CAMO_PROGRESS(%d, 0)" % i)
    rt2.execute("SET_G11(231)")
    rt2.execute("SET_PAID('v1;125186:900:1')")
    load(rt2)
    pump(rt2, 16)
    rt2.execute("SET_CAMO_PROGRESS(68970, 1000)")
    pump(rt2, 240)
    l2 = lines_of(rt2)
    check("J: ten tiers crossing in one poll draw ten cards - a burst loses none of them",
          rt2.eval("NAMED('completed_challenge')") == 10
          and count_line(l2, "camo card id=68970") == 10
          and not has_line(l2, "cards this match"),
          "%s | %s" % (rt2.eval("NAMED('completed_challenge')"), count_line(l2, "camo card id=68970")))
    check("J: the ten are ten different targets, never the same one twice",
          len(set(x.split("target=")[1].split()[0] for x in l2 if "camo card id=68970" in x)) == 10,
          " | ".join([x for x in l2 if "camo card id=68970" in x][:3]))

    rt3 = new_rt(lua51, src=False)
    rt3.execute(PRE)
    rt3.execute(THREE_GUNS)
    for i in (75001, 76001, 77001):
        rt3.execute("SET_CAMO_PROGRESS(%d, 0)" % i)
    rt3.execute("SET_G11(232)")
    rt3.execute("SET_PAID('v1;125186:900:1;126469:800:1;130001:700:1')")
    load(rt3)
    pump(rt3, 24)
    l3 = lines_of(rt3)
    check("J: ten special rows each for three weapons all reach the watch, in sequence",
          has_line(l3, "ref=sat_ar_flatline base=1 special=10 mastery=0 extra=0 watch=10")
          and has_line(l3, "ref=sat_me_nashira base=1 special=10 mastery=0 extra=0 watch=20")
          and has_line(l3, "ref=sat_pi_alcor base=1 special=10 mastery=0 extra=0 watch=30"),
          " | ".join([x for x in l3 if "camo rows" in x][:3]))
    rt3.execute("SET_CAMO_PROGRESS(77001, 101)")
    pump(rt3, 32)
    check("J: and the third weapon's own special cards - it was not squeezed out by the first two",
          has_line(lines_of(rt3), "camo card id=77001 row=sat_ar_flatline_camo_zm_unique1 target=101 route=A"),
          " | ".join([x for x in lines_of(rt3) if "camo card" in x][:2]))
    check("J: no camo card is lost across the three weapons either",
          rt3.eval("NAMED('completed_challenge')") == 1 and not has_line(l3, "cards this match"),
          str(rt3.eval("NAMED('completed_challenge')")))


CF_HELPERS = r"""
function CF_SETGUN(ref, id, level, primed, foreign)
  local s = rawget(_G, "ProgressionTuning")
  s.guns[ref] = { ref = ref, id = id, level = level, primed = primed, ladder = { 1000, 2200 },
                  n = 2, src = "minxp", prestige = 0, foreign = foreign }
end
function CF_FOREIGN(ref) rawget(_G, "ProgressionTuning").foreign[ref] = true end
function CF_GUN(ref) return rawget(_G, "ProgressionTuning").guns[ref] end
function CF_BYID(id) return rawget(_G, "ProgressionTuning").byid[id] end
function CF_ROW(ref) return rawget(_G, "ProgressionTuning").foreign[ref] end
function CF_CAMO(k) return rawget(_G, "ProgressionTuning").camo[k] end
function CF_DRAW(k, ...) return rawget(_G, "ProgressionTuning").draw[k](...) end
"""

CF_CONTENT = r"""
SET_LOOT_REF(120001, "t10_ar_coslo")
SET_GUN("t10_ar_coslo", 38869)
SET_MINXP("t10_ar_coslo", { 1000, 2200, 3400, 4600 })
SET_MAXLEVEL("t10_ar_coslo", 27)
SET_OC(38869, 0, 0)
SET_LOOT_REF(120002, "jup_ar_mw3gun")
SET_LOOT_REF(120003, "iw9_ar_mike4")
""" + CF_HELPERS


def cf_weaponxp(lua51):
    rt = new_rt(lua51, pre=CF_CONTENT + ' SET_PAID("v1;120001:1200:1200;120002:900:900;120003:900:900;88929:900:900")')
    pump(rt, 8)
    l = lines_of(rt)
    check("cf: a carried ref that does have a csv row is still not bound",
          rt.eval("CF_GUN('t10_ar_coslo')") is None and rt.eval("CF_BYID(38869)") is None,
          str(rt.eval("CF_GUN('t10_ar_coslo')")))
    check("cf: and the ref is marked foreign, so no ladder is picked for it",
          rt.eval("CF_ROW('t10_ar_coslo')") is True)
    check("cf: one line names the loot id, the ref and the reason",
          count_line(l, "loot 120001 -> t10_ar_coslo is not one of ours - not bound") == 1,
          " | ".join([x for x in l if "not one of ours" in x][:4]))
    check("cf: each carried family is refused with one line of its own",
          count_line(l, "jup_ar_mw3gun is not one of ours") == 1
          and count_line(l, "iw9_ar_mike4 is not one of ours") == 1,
          " | ".join([x for x in l if "not one of ours" in x][:4]))
    check("cf: no level, no ladder pick and no card for any of them",
          not has_line(l, "prime t10_ar_coslo") and not has_line(l, "row 38869")
          and rt.eval("NEVENTS()") == 0, " | ".join(l[-6:]))
    check("cf: the sat_ gun in the same payload keeps its own ladder and its own level",
          has_line(l, "prime sat_pi_atlas lv=0 total=900"), " | ".join(l[-6:]))

    rt.execute('SET_PAID("v1;120001:4600:4600;120002:4600:4600;120003:4600:4600;88929:900:900")')
    pump(rt, 16)
    l = lines_of(rt)
    check("cf: a carried total past its whole ladder still draws nothing",
          rt.eval("NAMED('completed_challenge')") == 0 and rt.eval("NAMED('add_message_splash_manager')") == 0,
          " | ".join(l[-6:]))
    check("cf: and the carried row is never read twice",
          count_line(l, "not one of ours") == 3, str(count_line(l, "not one of ours")))

    rt2 = new_rt(lua51, pre=CF_HELPERS + ' SET_LOOT_REF(120006, "sat_pi_blank") SET_GUN("sat_pi_blank", 0)'
                                       ' SET_PAID("v1;120006:1200:1200")')
    pump(rt2, 4)
    l2 = lines_of(rt2)
    check("cf: a sat_ gun whose row answers id 0 is treated as a gun with no row",
          rt2.eval("CF_GUN('sat_pi_blank')") is None and rt2.eval("NEVENTS()") == 0,
          " | ".join(l2[-4:]))
    check("cf: and the existing second net says so, once",
          count_line(l2, "no progression row answers for sat_pi_blank") == 1,
          " | ".join([x for x in l2 if "no progression row" in x][:3]))

    rt3 = new_rt(lua51, pre=CF_CONTENT + ' SET_PAID("v1;120001:3400:3400")')
    rt3.execute('CF_SETGUN("t10_ar_coslo", 38869, 1, true, false) CF_FOREIGN("t10_ar_coslo")')
    pump(rt3, 16)
    l3 = lines_of(rt3)
    check("cf: a stale carried entry is stopped before any ladder or card",
          rt3.eval("CF_GUN('t10_ar_coslo')") is not None and rt3.eval("NEVENTS()") == 0
          and not has_line(l3, "prime t10_ar_coslo"),
          " | ".join(l3[-6:]))

    rt3.execute('rawget(_G, "ProgressionTuning").foreign["t10_ar_coslo"] = nil')
    rt3.execute('SET_PAID("v1;120001:3400:3400;88929:900:900")')
    pump(rt3, 16)
    check("cf: and with the flag gone its loot list is refused rather than drawn",
          rt3.eval("NAMED('completed_challenge')") == 0
          and count_line(lines_of(rt3), "row 38869 has no loot list - level 2 draws no attachment card (foreign ref)") == 1,
          " | ".join([x for x in lines_of(rt3) if "row 38869" in x][:3]))


def cf_prison(lua51, ls):
    rt = new_rt(lua51, frontend=True, src=False)
    lua_slabs(rt, slabs_of([150900]))
    rt.execute("SET_G11(201)")
    rt.execute('PRESTIGE_BUNDLE(140800, "iw9_ar_mike4")')
    rt.execute('SET_PREQ("iw9_ar_mike4", 140800, 1)')
    rt.execute('SET_PRESTIGE("iw9_ar_mike4", 0)')
    rt.execute("SET_TYPE(140800, 7)")
    rt.execute('PRESTIGE_BUNDLE(140801, "sat_pi_alcor")')
    rt.execute('SET_PREQ("sat_pi_alcor", 140801, 1)')
    rt.execute('SET_PRESTIGE("sat_pi_alcor", 0)')
    rt.execute("SET_TYPE(140801, 7)")
    rt.execute('SET_CAMODATA(140802, "t10_ar_coslo")')
    rt.execute("SET_TYPE(140802, 13)")
    load(rt)
    pump(rt, 1)
    seen = (rt.eval("ASK_L(140800)"), rt.eval("ASK_L(140801)"), rt.eval("ASK_L(140802)"))
    l = lines_of(rt)
    check("cf: an attachment whose bundle names a carried gun is left to the client",
          seen[0] is True, str(seen[0]))
    check("cf: and one line names the id, the ref and the reason",
          count_line(l, "prestige lock: 140800 is a prestige reward for iw9_ar_mike4, which is not one of ours") == 1,
          " | ".join([x for x in l if "prestige reward" in x][:3]))
    check("cf: the same shape on a sat_ ref still closes, so the door did not go blunt",
          seen[1] is False, str(seen[1]))
    check("cf: a camo whose own data names a carried gun is left to the client too",
          seen[2] is True, str(seen[2]))
    check("cf: and one line names it, with no band computed",
          count_line(l, "prestige lock: 140802 belongs to t10_ar_coslo, which is not one of ours") == 1
          and not has_line(l, "prestige camo id=140802"),
          " | ".join([x for x in l if "140802" in x][:3]))

    CAP = """
PRESTIGE[xhash("getmaxweaponprestigelevel")] = function(ref) return 2 end
PRESTIGE[xhash("getweaponprestigecamos")] = function(ref)
  if ref == "sat_w_650" then
    local a = { { startPrestige = 0, startLevel = 0, targetPrestige = 1, targetLevel = 27,
                  camoBundle = { lootid = 140810 } } }
    return a, {}, {}
  end
  return {}, {}, {}
end
%s
"""
    def capped(n):
        rt2 = new_rt(lua51, frontend=True, src=False)
        lua_slabs(rt2, slabs_of([150900]))
        rt2.execute("SET_G11(202)")
        rt2.execute(CAP % ('WEAPON[xhash("enumerateweapons")] = function(cb)\n'
                           '  for i = 1, %d do cb({ ref = "sat_w_" .. i }) end\nend' % n))
        rt2.execute("SET_CAMODATA(140810, nil)")
        rt2.execute("SET_TYPE(140810, 13)")
        rt2.execute('SET_PRESTIGE("sat_w_650", 0)')
        rt2.execute('SET_LEVEL("sat_w_650", 0)')
        load(rt2)
        pump(rt2, 1)
        return rt2

    rt2 = capped(700)
    check("cf: a prestige camo on the 650th weapon is in the map, past the old 600 cap",
          rt2.eval("ASK_L(140810)") is False, str(rt2.eval("ASK_L(140810)")))
    check("cf: and the map says how many weapons it walked",
          has_line(lines_of(rt2), "the weapon ladders name 1 prestige camo ids over 700 weapons"),
          " | ".join([x for x in lines_of(rt2) if "prestige camo ids over" in x][:2]))

    rt3 = capped(2100)
    check("cf: a list longer than the client's own weapon table is not cached at all",
          rt3.eval("ASK_L(140810)") is True, str(rt3.eval("ASK_L(140810)")))
    check("cf: and exactly one line says the map is truncated",
          count_line(lines_of(rt3), "the weapon list is longer than 2048 - the camo map is truncated") == 1,
          " | ".join([x for x in lines_of(rt3) if "truncated" in x][:2]))

    ids = sorted(ls)[:2]
    rt4 = new_rt(lua51, frontend=True, src=False, pre="DROP_TYPE_API()")
    lua_slabs(rt4, slabs_of(ids))
    rt4.execute("SET_G11(203)")
    rt4.execute('SET_CAMODATA(%d, "iw9_ar_mike4")' % ids[0])
    load(rt4)
    pump(rt4, 1)
    seen4 = (rt4.eval("ASK_L(%d)" % ids[0]), rt4.eval("ASK_L(%d)" % ids[1]))
    l4 = lines_of(rt4)
    check("cf: with no type read, a scope id tied to a carried gun is left open",
          seen4[0] is True, str(seen4[0]))
    check("cf: and one line names it",
          count_line(l4, "lock door: %d names iw9_ar_mike4, which is not one of ours" % ids[0]) == 1,
          " | ".join([x for x in l4 if "lock door: %d " % ids[0] in x][:2]))
    check("cf: a scope id with no carried ref still closes exactly as RC 1.0 answered",
          seen4[1] is False, str(seen4[1]))

    rt5 = new_rt(lua51, frontend=True, src=False)
    lua_slabs(rt5, slabs_of([150901]))
    rt5.execute("SET_G11(204)")
    rt5.execute('SET_TYPE(140820, 7)')
    rt5.execute("BUNDLECALLS = 0")
    rt5.execute('ATTACHMENT[xhash("getbundlebyid")] = function(id) BUNDLECALLS = BUNDLECALLS + 1 return nil end')
    load(rt5)
    pump(rt5, 1)
    rt5.eval("ASK_L(140820)")
    rt5.eval("ASK_L(140820)")
    check("cf: a bundle that answered no table is cached as a no, not re-asked",
          int(rt5.eval("BUNDLECALLS")) == 1, str(rt5.eval("BUNDLECALLS")))
    lua_slabs(rt5, slabs_of([150902]))
    rt5.execute('SET_VER("205:33:65536")')
    pump(rt5, 8)
    rt5.eval("ASK_L(140820)")
    check("cf: and the rebuild that re-reads the bitmap re-asks it once",
          int(rt5.eval("BUNDLECALLS")) == 2, str(rt5.eval("BUNDLECALLS")))

    scope4 = sorted(ls)[:4]
    rt6 = new_rt(lua51, frontend=True, src=False)
    lua_slabs(rt6, slabs_of(scope4 + [160001]))
    rt6.execute("SET_G11(206)")
    rt6.execute('PLAIN_BUNDLE(%d, "t10_ar_coslo")' % scope4[0])
    rt6.execute("SET_TYPE(%d, 7)" % scope4[0])
    rt6.execute('PLAIN_BUNDLE(%d, "sat_pi_alcor")' % scope4[1])
    rt6.execute("SET_TYPE(%d, 7)" % scope4[1])
    rt6.execute('SET_CAMODATA(%d, "iw9_ar_mike4")' % scope4[2])
    rt6.execute("SET_TYPE(%d, 13)" % scope4[2])
    rt6.execute('SET_CAMODATA(%d, "sat_pi_timir")' % scope4[3])
    rt6.execute("SET_TYPE(%d, 13)" % scope4[3])
    rt6.execute("SET_TYPE(160001, 21)")
    load(rt6)
    pump(rt6, 1)
    before = int(rt6.eval("LCALLS"))
    pbefore = int(rt6.eval("PCALLS"))
    carried_a = rt6.eval("ASK_L(%d)" % scope4[0])
    carried_c = rt6.eval("ASK_P(%d)" % scope4[2])
    check("cf: a carried attachment id with a bit keeps the client's own answer",
          carried_a is True, str(carried_a))
    check("cf: a carried camo id with a bit keeps the client's own answer on both doors",
          carried_c is True and rt6.eval("ASK_L(%d)" % scope4[2]) is True, str(carried_c))
    check("cf: and the client's own function is the one that answered all three",
          int(rt6.eval("LCALLS")) - before == 2 and int(rt6.eval("PCALLS")) - pbefore == 1,
          "%d / %d" % (int(rt6.eval("LCALLS")) - before, int(rt6.eval("PCALLS")) - pbefore))
    l6 = lines_of(rt6)
    check("cf: the door line says the carried camo passed",
          has_line(l6, "door id=%d type=13 bit=1 answer=pass" % scope4[2]),
          " | ".join([x for x in l6 if "door id=" in x][:4]))
    check("cf: a sat_ attachment in the scope still closes",
          rt6.eval("ASK_L(%d)" % scope4[1]) is False)
    sat_camo = rt6.eval("ASK_L(%d)" % scope4[3])
    l6 = lines_of(rt6)
    check("cf: a sat_ camo in the scope still closes",
          sat_camo is False
          and has_line(l6, "door id=%d type=13 bit=1 answer=locked" % scope4[3]),
          " | ".join([x for x in l6 if "door id=" in x][:6]))
    before = int(rt6.eval("LCALLS"))
    pbefore = int(rt6.eval("PCALLS"))
    check("cf: an out of scope operator id with a bit passes through",
          rt6.eval("ASK_L(160001)") is True and rt6.eval("ASK_P(160001)") is True
          and int(rt6.eval("LCALLS")) - before == 1 and int(rt6.eval("PCALLS")) - pbefore == 1,
          "%d / %d" % (int(rt6.eval("LCALLS")) - before, int(rt6.eval("PCALLS")) - pbefore))


def cf_camos(lua51):
    rt = new_rt(lua51, src=False)
    rt.execute(CAMOSTUB)
    rt.execute(CF_HELPERS)
    rt.execute("SET_CAMO_ROW('sat_pi_atlas', 57201, {100, 200, 300})")
    rt.execute("SET_CAMO_PROGRESS(57201, 90)")
    rt.execute("SET_G11(211)")
    rt.execute('SET_PAID("v1;88929:900:900")')
    load(rt)
    rt.execute("CF_SETGUN('t10_ar_coslo', 38869, nil, false, nil)")
    pump(rt, 40)
    l = lines_of(rt)
    check("cf: the camo watch skips a carried ref and says so once",
          count_line(l, "camo watch t10_ar_coslo - not one of ours, so no row is read for it") == 1,
          " | ".join([x for x in l if "camo watch" in x][:4]))
    check("cf: no camo row is read for it at all",
          not has_line(l, "camo watch id=38869") and rt.eval("CF_CAMO('rows')['t10_ar_coslo']") is False)
    check("cf: and no read is spent on it, so the watch set stays for our own guns",
          rt.eval("rawget(_G, 'ProgressionTuning').camo.n") == 1
          and rt.eval("rawget(_G, 'ProgressionTuning').camo.tries['t10_ar_coslo']") is None,
          str(rt.eval("rawget(_G, 'ProgressionTuning').camo.n")))
    check("cf: the camo bundles skip it the same way, one line",
          count_line(l, "camo bundles t10_ar_coslo - not one of ours, so no row is read for it") == 1
          and rt.eval("rawget(_G, 'ProgressionTuning').camo.extraBuilt['t10_ar_coslo']") is True,
          " | ".join([x for x in l if "camo bundles" in x][:3]))
    check("cf: the sat_ gun's own camo row is still the watch set",
          has_line(l, "camo watch id=57201 ref=sat_pi_atlas tiers=3"), " | ".join([x for x in l if "camo watch" in x][:3]))


def cf_splash(lua51):
    rt = new_rt(lua51, src=False)
    rt.execute(SPLASHQ)
    rt.execute(CF_HELPERS)
    rt.execute('SET_LOOT_REF(120005, "jup_ar_mw3gun")')
    rt.execute("CFGUN = { ref = 't10_ar_coslo', id = 38869, ladder = { 1000, 2200 }, n = 2, prestige = 0 }")
    rt.execute("SET_G11(221)")
    load(rt)
    pump(rt, 2)
    check("cf: the gate is answering true, so the ref is the only thing that can refuse",
          rt.eval("GATE") is True)
    rt.eval("CF_DRAW('level', CFGUN, 2, 5000)")
    check("cf: a carried ref never reaches the kind 398 event, even with a row",
          rt.eval("NEVENTS()") == 0, str(rt.eval("NEVENTS()")))
    check("cf: and the card is refused without a word about it",
          not has_line(lines_of(rt), "t10_ar_coslo"), " | ".join(lines_of(rt)[-4:]))
    rt.eval("CF_DRAW('attach', 120005, CFGUN, 1, 900)")
    check("cf: an attachment whose ref is carried forward draws no card",
          rt.eval("NEVENTS()") == 0
          and count_line(lines_of(rt), "attachment 120005 is jup_ar_mw3gun, not one of ours - no card") == 1,
          " | ".join([x for x in lines_of(rt) if "attachment 120005" in x][:2]))
    rt.eval("CF_DRAW('camo', { ref = 'sat_x_camo' }, 100, 1, 50)")
    rt.eval("CF_DRAW('ret', { ref = 'sat_x_ret' }, 100, 1, 50)")
    rt.eval("CF_DRAW('chal', { ref = 'sat_x_chal' }, 100, 50)")
    check("cf: a row object with no id is never fired, on any of the three cards",
          rt.eval("NEVENTS()") == 0, str(rt.eval("NEVENTS()")))
    rt.eval("CF_DRAW('level', { ref = 'sat_pi_atlas', id = 54499, prestige = 0 }, 1, 1200)")
    check("cf: our own ref still fires the banner, so the guard is not over-broad",
          rt.eval("NAMED('completed_challenge')") == 1
          and int(rt.eval("LASTOF('completed_challenge').kind")) == 398,
          str(rt.eval("NAMED('completed_challenge')")))


def cf_off(lua51):
    rt = new_rt(lua51, pre='SET_PAID("v1;88929:999:999")')
    pump(rt, 4)
    rt.execute('SET_PAID("v1;88929:1000:1000")')
    pump(rt, 20)
    l = lines_of(rt)
    check("cf off: with nothing carried the sat_ gun crosses and draws its banner and its item",
          has_line(l, "sat_pi_atlas crossed 1 row 54499 rank=1 banner=2 total=1000 rung=1000 src=dll")
          and rt.eval("NAMED('completed_challenge')") == 1
          and rt.eval("NAMED('add_message_splash_manager')") == 1, " | ".join(l[-6:]))
    check("cf off: and the item card is the same weaponProgression splash as before",
          rt.eval("LASTOF('add_message_splash_manager').options.displayLocation") == "weaponProgression"
          and rt.eval("LASTOF('add_message_splash_manager').options.headerText") == "Beadline Tactical Pad")
    check("cf off: nothing in the log says a ref was not one of ours",
          not has_line(l, "not one of ours"), " | ".join([x for x in l if "one of ours" in x][:2]))

    rt2 = new_rt(lua51, frontend=True, src=False)
    lua_slabs(rt2, slabs_of([150900]))
    rt2.execute("SET_G11(231)")
    rt2.execute('PRESTIGE_BUNDLE(140701, "sat_pi_alcor")')
    rt2.execute('SET_PREQ("sat_pi_alcor", 140701, 1)')
    rt2.execute('SET_PRESTIGE("sat_pi_alcor", 0)')
    rt2.execute('SET_LEVEL("sat_pi_alcor", 2)')
    rt2.execute("SET_TYPE(140701, 7)")
    rt2.execute('SET_CAMODATA(107478, "sat_pi_alcor")')
    rt2.execute("SET_TYPE(107478, 13)")
    rt2.execute(PRESTIGE_CAMO_FN)
    load(rt2)
    pump(rt2, 1)
    check("cf off: a sat_ prestige attachment and a sat_ camo both still read locked",
          rt2.eval("ASK_L(140701)") is False and rt2.eval("ASK_L(107478)") is False,
          "%s / %s" % (rt2.eval("ASK_L(140701)"), rt2.eval("ASK_L(107478)")))
    check("cf off: with the same lines the door printed before",
          has_line(lines_of(rt2), "prestige id=140701 tier=1 prestige=0 answer=locked")
          and has_line(lines_of(rt2), "prestige camo id=107478 ref=sat_pi_alcor start=0/0 to=1/27"),
          " | ".join([x for x in lines_of(rt2) if "prestige" in x][:3]))
    check("cf off: and nothing was refused for being carried forward",
          not has_line(lines_of(rt2), "not one of ours"))

    l2 = lines_of(rt2)
    check("cf: the arm line says which carry forward world this vm ran in, once",
          count_line(l2, "carry-forward: pack=unknown dvar=") == 1
          and has_line(l2, "mwcf=false"), " | ".join([x for x in l2 if "carry-forward" in x][:3]))

    rt3 = new_rt(lua51, frontend=True, src=False)
    rt3.execute('SET_DVAR("kronos_cfwd", "1")')
    rt3.execute('SET_DVAR("mwcf_box_pools", "v")')
    lua_slabs(rt3, slabs_of([150903]))
    rt3.execute("SET_G11(232)")
    load(rt3)
    pump(rt3, 1)
    check("cf: and it reads the two dvars the recon names, not a guess",
          count_line(lines_of(rt3), "carry-forward: pack=unknown dvar=1 mwcf=true") == 1,
          " | ".join([x for x in lines_of(rt3) if "carry-forward" in x][:3]))


def main():
    print("progression-tuning - offline checks")
    print("source: %d parts under %s" % (len(LUA_FILES), LUA_DIR))
    static_checks()

    global LOAD_ORDER
    if has_lupa():
        from lupa.lua51 import LuaRuntime as _Lua51  # noqa: N814
        raw = LUA_TEXT[MAIN]
        body = raw[raw.index("local GCSV = [[") + len("local GCSV = [["):]
        body = body[:body.index("]]")]
        ls = set(int(x) for x in body.split())

        def replay(lua51, ls):
            payload_cases(lua51)
            two_guns(lua51)
            resume(lua51)
            crossing(lua51)
            attach_card(lua51)
            absent(lua51)
            display(lua51)
            extras(lua51)
            g11_reader(lua51, ls)
            g11_payload(lua51, ls)
            g11_absent(lua51)
            g11_order_and_cap(lua51, ls)
            s1_door(lua51, ls)
            s1_fallback(lua51, ls)
            s3_prestige(lua51, ls)
            s3_universal(lua51)
            s4_value(lua51)
            s4_journal(lua51)
            s5_watch(lua51)
            s5_dedupe(lua51)
            ladder_pick(lua51)
            ladder_pick_a3(lua51)
            camo_splash(lua51)
            daily_cards(lua51)
            camo_zm_rows(lua51)
            weekly_rows(lua51)
            week_sweep(lua51)
            camo_families(lua51)
            camo_bursts(lua51)
            reticle_rows(lua51)
            camo_retry(lua51)
            diag_off(lua51)
            diag_menu(lua51)
            diag_reprint(lua51)
            diag_absent(lua51)
            diag_q6_keyed(lua51)
            diag_q7_fields(lua51)
            diag_neutral(lua51)
            diag_match(lua51)
            splashck_arm(lua51)
            splashck_absent(lua51)
            splashck_slot(lua51)
            splashck_late(lua51)
            splashck_order(lua51)
            splash_slot(lua51)
            splash_group(lua51)
            splash_side(lua51)
            splash_floor(lua51)
            splash_cap(lua51)
            splash_priority(lua51)
            splash_order(lua51)
            weekly_look(lua51)
            weekly_gaps(lua51)
            weekly_heads(lua51)
            card_sounds(lua51)
            splashck_cap(lua51)
            snd_line(lua51)
            snd_engine(lua51)
            diag_switch(lua51)
            cf_weaponxp(lua51)
            cf_prison(lua51, ls)
            cf_camos(lua51)
            cf_splash(lua51)
            cf_off(lua51)

        for order in LOAD_ORDERS:
            LOAD_ORDER = order
            info("replay: the eight parts load in %s order" % order)
            seen, bad = len(passes), len(failures)
            try:
                replay(_Lua51, ls)
            except Exception as exc:
                check("replay: the %s run finishes the whole suite" % order, False, repr(exc)[:200])
            info("replay: %s order - %d checks, %d failed" % (order, len(passes) - seen,
                                                              len(failures) - bad))
        LOAD_ORDER = "harness"
    else:
        info("lupa.lua51 is not installed - the dry run was skipped")

    print("")
    for path in ([MODJSON] + [os.path.join(LUA_DIR, n) for n in LUA_FILES]
                 + [os.path.abspath(__file__)]):
        data = open(path, "rb").read()
        print("HASH  %s  %d B  %s" % (os.path.relpath(path, PKG), len(data),
                                      hashlib.sha256(data).hexdigest()[:16].upper()))
    print("")
    print("%d passed, %d failed" % (len(passes), len(failures)))
    if failures:
        for name, detail in failures:
            print("FAIL  %s%s" % (name, ("  [" + detail + "]") if detail else ""))
        return 1
    return 0


def has_lupa():
    try:
        from lupa.lua51 import LuaRuntime  # noqa: F401
        return True
    except Exception:
        return False


if __name__ == "__main__":
    sys.exit(main())







