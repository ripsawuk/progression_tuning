"""progression-tuning - the offline replay for mod\\progression_tuning.

Two halves, both read-only. Nothing is installed, no game folder is written, nothing is launched.

  * static checks over mod.json and the Lua: LF, ASCII, every comment line inside the file rule
    (lower case, no punctuation, ten words at most), the manifest's own fields, one wrapper per getter,
    the embedded locksmith scope (4,203 ids, the generator's own SHA-256) kept as the fallback, the absence
    of every identifier the removed features used, and the absence of any script part;
  * a dry run of the Lua under a stubbed Kronos VM (Lua 5.1 via lupa) whose members are keyed by
    xhash, the way the client stores them (D47), whose Dvar answers by xhashdvar(name), and whose two
    contexts are the menu (Engine.InFrontend true) and a match (false). Its clock is `PUMP(n)`: one
    round fires every queued wait once, so two independent 250 ms timers each get n steps and neither
    steals the other's slot.

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
  21. the clock fill (`utc_fill`): a nil original answers with the cod getter's number and no cod getter
      answers 0, a number passes all four of its returns through whole, a raising original is filled, the
      wrapper lands on the plain, pushed and hashed keys wherever each holds the function it wrapped (a
      plain name reached through a metatable included) and never on a key holding another function, a vm
      with no loader table fills the found key alone, a vm with no engine or no getter says absent once,
      and one arm line and one wrap per vm.
  22. the options rows: the data member answers our two ids out of the stock bundle it was handed,
      with their labels and their kind, and passes every other id through; the list member appends both
      to the debug tab, appends them only once, keeps every return the page gave it and leaves a
      table that is not the debug tab alone; the page build moves both to sit directly after the
      anchor and leaves the stock order otherwise; the dropdown answers the 1-based index of the
      lowest current count and writes the count it is given, the toggle answers and sets the permanent
      flag, and with no page at all the part arms nothing; the same rows through both layers of the
      debug page: the inner layer puts its own rows above the stock ones and drops the dead unlock row,
      the page's second layer then takes the slot over ours and every row is still there once - the
      block the inner layer built is dropped rather than repeated - the page reads the same either way,
      and rebuilds plus a repeat hook leave one of every row.
  23. the token channel (`pt_tokens_ch`): a full line is read into its fields and written back with its
      serial risen and every other field kept; a field this build does not parse is ignored on the read
      and dropped by the next write; a line with no counts seeds them from the client's own record
      without printing a line, a line with no channel seeds nothing; a serial another vm wrote is adopted
      on the next tick by the seconds, the counts and the flag, and the same serial is not adopted twice;
      the part's own console output is its armed line and its refusals - no per write, per change or
      census line survives (`LOG_REMOVED`);
  24. the armory schedule gate: the gate answers released for a row in the 76 with a future
      start stamp while `CoD.GetUTC` is zero, the client's own answer stands for every other row
      (all of its values), a raising gate on another row gives the client's own refusal rather than
      an error, loading the file twice wraps nothing twice, and a match VM arms on the same gate and
      answer; with no gate in the table
      its own retry timer keeps trying and then says one `gate=missing` line and stops; the part
      arms on that timer alone, in a VM with no main part in it and with no main hook registered.
      And the pick (C31 a3): the client's own press runs first and its values come back unchanged,
      the row it acted on is read from the focus item, the active tile or the last tile focused
      and only when it is one of the 76, 52813 answers that row from a copied record with the
      client's own table untouched and a record the client already activated passing through, every
      other id is the client's own answer, the client's raises are swallowed into the safe answer,
      the channel is
      written and read back only when the hook put a line in it, a pick it already carries is adopted
      at arm, and a pick the hook registers after the arm is taken on a later tick of the part's own
      timer or in the 52813 answer itself, said once and with no write before it;
      a press under a padded hash is still found, and a match VM records its press too.
      And the versions (C87 a4): the table's 39 rows and 456 ids, 147 under the attachment rows and 309
      under the weapon rows, each attachment version reading locked until its row is done or its own
      switch is on, a version ask costing no completion read, and the 309 weapon versions left to the
      blueprint rule the lock door owns.
      And the crafting table: a match VM wraps the game's own item lock once, under its plain name or
      its hash, so the four streaks the armory sells read locked at the table until their row is done
      or their switch is on, every other item keeps the game's own answer (asked exactly once), a
      raising lock answers locked and still opens an earned streak, a menu VM says `craft=n/a` and
      wraps nothing, a match VM with no table says `craft=missing`, and the three load orders agree.
      And the arm timer (C87 a5): its retry runs on past a pick already seeded at the arm until the gate,
      the answer, the door, the ownership getter and the vm's own piece are in, says one `armory late`
      line naming the ones that arrived after the arm line and never one a tick, and rests once the pick
      is seeded; a vm with no door keeps it waiting for one. And the ownership getter
      (`PROXY_LOOT.IsOwned`, C87 a5/a6/a7): the 76 base ids and the 147 attachment versions answer not owned
      until their row is done or their switch is on, a blueprint id is the getter's own answer asked
      exactly once, a plain and a hashed slot and a table rebuilt after the arm are all wrapped, a
      raising getter answers not owned rather than raising, a vm with no getter says `own=missing`, and
      the three load orders agree.
      And the blueprint rule the lock door owns, for every gun (C87 a4 v12): a blueprint id is listed in
      every build list and padlocked unless its own gun is unlocked by the door's own answer for that
      base id and the blueprint switch is on, everything unlocked opens it whatever else says, the
      base comes from the game's own `WEAPON.getbaseweaponlootidfromblueprint` and is cached per id, the
      gun's own row test (`PROGRESSION.ownsBlueprintOfWeapon`) answers not owned while that gun is
      locked, an owned blueprint never opens a locked gun, no other id moves, and the three load orders
      agree.

The mod is eleven `*_post.lua` parts (D96 split): main, weaponxp, splash, camos, challenges, prison,
reticles, armory, diag, options, tokens. `load()` runs all eleven in that order; `SRC` is their
concatenation and every whole-mod check reads it. The diagnostic is quarantined in its own part:
`shipping()` is the ten parts that ship, because the diag part legitimately names the features the
shipping code must not. Everything else, including every static ban on IO, still scans all of it. The
token part reads its channel at chunk scope, so the reversed order arms it last, and it carries four
retired words the file rule and the residue scan allow by name, each pinned in `static_checks`. The
armory part arms where its gate and answer are, or on a timer of its own, and carries its own arm
wording, pinned in `PART_ARM`.

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
ARMORY = "progression_tuning_armory_post.lua"
DIAG = "progression_tuning_diag_post.lua"
OPTIONS = "progression_tuning_options_post.lua"
TOKENS = "progression_tuning_tokens_post.lua"
LUA_FILES = [MAIN, WEAPONXP, SPLASH, CAMOS, CHALLENGES, PRISON, RETICLES, ARMORY, DIAG, OPTIONS, TOKENS]
SHIP_FILES = [n for n in LUA_FILES if n != DIAG]
TEXT_FILES = LUA_FILES
# the two rows parts arm last in the reversed order: the token part reads its channel at chunk scope, and
# the diagnostic's own arm gate counts eight parts, so no original part may fall outside the first eight
CORE_LAST = [OPTIONS, TOKENS]
LOAD_ORDERS = {
    "harness": LUA_FILES,
    "alphabetical": sorted(LUA_FILES),
    "reversed": ([n for n in sorted(LUA_FILES, reverse=True) if n not in CORE_LAST] + CORE_LAST),
}
LOAD_ORDER = "harness"
# the line each part prints when it arms, where it carries its own wording
PART_ARM = {ARMORY: '"armory armed "'}

PARTS, HEXLEN, PARTLEN = 33, 65536, 2000
MAXID = 0x3FFFF
LS_COUNT = 4203
LS_SHA = "EC5C1479DE844E725AC0569A348B0349826783B1C0CC7598F0C949451A349581"
ACCEPT = [89575, 96171, 96192, 96202, 102671, 126597, 126619, 111457]
# the tokens script is rc1.4 prep's file byte for byte, the armory xp feed is a script of its own
TOKENS_GSC_LEN = 8559
TOKENS_GSC_SHA = "63EFBB2B9032C392FED53501124F77E85B3F0E15332415BF0796A2BBECDF06DC"
ARMORY_GSC = "progression_tuning_armory.gsc"
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
    "g11_locks", "e3_armory", "g10_armory",
]
# the armory words belong to the armory part alone (its own check below)
ARMORY_WORDS = ["Armory", "armory"]

# the game's own card tables, read by name - not residue of a removed feature
CARD_TABLES = ["reticleChallenges", "seasonalChallenges", "gunsmithChallenges",
               "callingCardPrestigeChallenges"]
# their stringtable paths, which the loader falls back to - the same reason
CARD_PATHS = ["ae/sat_ae_autogen_reticle_challenges.csv",
              "ae/sat_ae_autogen_seasonal_challenges.csv",
              "ae/sat_gs_challenges.csv",
              "ae/sat_ae_autogen_prestige_challenges.csv"]
# the four card tables the reward set no longer reads
DROPPED_CARDS = ["callingCardMasterChallenges", "playlistchallenges",
                 "leagueplayChallengeAchievements", "masteryBadgeAchievements"]
DROPPED_PATHS = ["ae/sat_ae_autogen_sticker_book_challenges.csv",
                 "ae/sat_ae_autogen_playlist_challenges.csv",
                 "ae/sat_leagueplay_challenge_achievements.csv",
                 "ae/sat_ae_autogen_masterybadge_challenges.csv"]
# the game's own unlock dvars, which carry no residue of a removed feature
UNLOCK_DVARS = ["zm_unlock_attachments", "zm_unlock_camos", "zm_unlock_reticles", "zm_unlock_cards",
                "zm_unlock_emblems", "zm_unlock_operators", "zm_unlock_finishers", "zm_unlock_charms",
                "zm_unlock_stickers", "zm_unlock_sprays", "zm_unlock_emotes",
                "zm_unlock_loadingscreens", "zm_unlock_perks", "zm_unlock_equipment",
                "zm_unlock_scorestreaks", "zm_unlock_fieldupgrades", "zm_unlock_wildcards",
                "zm_unlock_ammomods"]

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
Dvar[xhash("SetDvarString")] = function(key, v)
  DVARS[key] = tostring(v)
  return true
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
    local now = {}
    for i = 1, #QUEUE do now[i] = QUEUE[i] end
    if #now == 0 then break end
    QUEUE = {}
    fired = fired + 1
    for i = 1, #now do
      local h = now[i]
      if type(h.onComplete) == "function" then h.onComplete() end
    end
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
CSV.gunsmithChallenges = { file = "gs", cols = { id = 0, ref = 1, loot = 5, amount = 4 } }
CELLS = {}
ROWS = {}
ROWCOLS = {}
StringTable = {}
StringTable[xhash("tablelookup")] = function(file, kc, kv, oc)
  return CELLS[tostring(file) .. "|" .. tostring(kc) .. "|" .. tostring(kv) .. "|" .. tostring(oc)]
end
StringTable[xhash("tablereadallrows")] = function(file, cols)
  ROWCOLS[tostring(file)] = cols
  return ROWS[tostring(file)]
end
COLNUM = {}
COLCOLS = {}
StringTable[xhash("tablelookupentirecolumnbynum")] = function(file, n)
  local f = tostring(file)
  COLNUM[f] = COLNUM[f] or {}
  COLNUM[f][#COLNUM[f] + 1] = n
  local rows, cols = ROWS[f], COLCOLS[f]
  if cols == nil then
    for _, t in pairs(CSV) do
      if type(t) == "table" and type(t.cols) == "table" and tostring(t.file) == f then
        cols = t.cols
      end
    end
  end
  if rows == nil or cols == nil then return nil end
  local name = nil
  for k, v in pairs(cols) do
    if type(v) == "number" and v == n then name = k end
  end
  if name == nil then return nil end
  local keys = {}
  for k in pairs(rows) do keys[#keys + 1] = k end
  table.sort(keys, function(a, b) return (tonumber(a) or 0) < (tonumber(b) or 0) end)
  local out = {}
  for i = 1, #keys do
    local r = rows[keys[i]]
    if type(r) == "table" then out[i] = r[name] end
  end
  return out
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
function DROP_RETICLE_TYPE() LOOT.itemTypes.RETICLE = nil end
function TYPE_RAISES()
  LOOT[xhash("gettypeforid")] = function(id) error("no type") end
end
LOOT[xhash("gettypeforid")] = function(id)
  TYPECALLS = TYPECALLS + 1
  local t = TYPES[tostring(id)]
  if t ~= nil then return t end
  return 7
end
LOOT.itemTypes = { ATTACHMENT = 7, CAMO = 13, RETICLE = 14, WEAPON = 2, PLAYERCARD = 11 }
DEFID = {}
DEFCALLS = 0
function SET_DEFAULT(id) DEFID[tostring(id)] = true end
LOOT[xhash("isitemdefault")] = function(id) DEFCALLS = DEFCALLS + 1; return DEFID[tostring(id)] == true end
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
BPSRC = {}
BASECALLS = 0
function SET_BLUEPRINT(id, base) BPSRC[tostring(id)] = base end
function BASE_N() return BASECALLS end
function BASE_ZERO() BASECALLS = 0 end
function DROP_BASE() WEAPON[xhash("getbaseweaponlootidfromblueprint")] = nil end
WEAPON[xhash("getbaseweaponlootidfromblueprint")] = function(id)
  BASECALLS = BASECALLS + 1
  local b = BPSRC[tostring(id)]
  if b ~= nil then return b end
  return tonumber(id)
end
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
R_SLABS = {}
function SET_RPARTS() for i = 0, 32 do DVARS[xhashdvar("zm_g12_" .. i)] = R_SLABS[i + 1] end end
function SET_G12(serial)
  SET_RPARTS()
  DVARS[xhashdvar("zm_g12_arm")] = "g11"
  DVARS[xhashdvar("zm_g12_ver")] = tostring(serial) .. ":33:65536"
end
function SET_RVER(v) DVARS[xhashdvar("zm_g12_ver")] = v end
function SET_RPART(i, v) DVARS[xhashdvar("zm_g12_" .. i)] = v end
function CLEAR_G12()
  CLR_DVAR("zm_g12_ver")
  for i = 0, 32 do CLR_DVAR("zm_g12_" .. i) end
end
function TORN_NEXT(n) TORN = n end
function ASK_P(id) return PROGRESSION[xhash("isunlockedwithid")](0, id) end
function ASK_L(id) return LOOT[xhash("isunlockedwithid")](0, id) end
function LOAD_CARD(k) return ProgressionTuning.api.loadcard(k) end
function LOAD_ALL() LOAD_CARD('ret') LOAD_CARD('sea') LOAD_CARD('gs') end
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
SET_DVAR("pt_tokens_ch", "p=0;w=0;n=1;c=0,0,0,0,0,0,0,0;x=0")
"""

# the debug tab's page, stubbed: the four members under their printed hash, one stock list, one stock
# bundle per id, the tab id the page publishes and the builder the arm hook wraps
OPTIONSFIX = r"""
LIST = {
  { [xhash("settingId")] = "#x7a1b0000000000a1" },
  { [xhash("settingId")] = "0x5a6d0000000000be" },
  { [xhash("settingId")] = "#x2c9f0000000000d4" },
}
function STOCKBUNDLE(id)
  return { [xhash("settingId")] = id,
           [xhash("label")] = "Stock row",
           [xhash("description")] = "the stock row own description",
           [xhash("labels")] = { "Off", "On", "Auto" },
           [xhash("getter")] = function() return 1 end,
           [xhash("setter")] = function() end,
           [xhash("widgetType")] = "Dropdown" }
end
OPTIONS = { TabIds = { DEBUG = 7 } }
OPTIONS["#x7bf7f57679e8d050"] = function(tab, c, idx) return LIST, "and a second return" end
OPTIONS["#xe7686f7a9907efd8"] = function(id, c) return STOCKBUNDLE(id) end
OPTIONS["#x9f6c4b08602983fb"] = function(id, c) return STOCKBUNDLE(id) end
OPTIONS[xhash("createoptionlist")] = function(a, b, list, d)
  return function(el, c) return list end
end
BUILT = 0
MenuBuilder = { BuildRegisteredType = function(t, data) BUILT = BUILT + 1 return { t = t } end }
"""

# the debug page's two layers, stubbed the way they nest: the inner one wraps the stock section builder
# before the mod loads and the outer one wraps whatever holds the slot when the page is built
OPTIONSLAY = r"""
SID = xhash("settingId")
SNAME = xhash("settingLabel")
SDESC = xhash("settingDescription")
SLIST = xhash("optionsList")
SGLAB = xhash("labels")
STYPE = xhash("widgetType")
SGET = xhash("getter")
SSET = xhash("setter")
SKSECT = "#x7bf7f57679e8d050"
SKDA = "#xe7686f7a9907efd8"
SKDB = "#x9f6c4b08602983fb"
DEADID = "3f58d23122dd68ae"
DBGIDS = { "5a6d0000000000a1", "5a6d0000000000be", "5a6d0000000000aa" }
STOCKROWS = { "5a6d0000000000a1", "5a6d0000000000be", "5a6d0000000000aa", DEADID }
HOBJ, DBGSB = {}, {}
for _, h in ipairs(DBGIDS) do
  HOBJ[h] = setmetatable({}, { __tostring = function() return "#x3" .. h end })
  DBGSB[HOBJ[h]] = h
end
function HOF(h) return HOBJ[h] or h end
function STOCKLIST()
  local out = {}
  for i, sb in ipairs(STOCKROWS) do out[i] = { [SID] = sb } end
  return out
end
function GROUPSECS(items)
  local group = { [SNAME] = "Debug Options", [SLIST] = items }
  return { { [SNAME] = "Debug Options", [SGLAB] = "debug", [SLIST] = { group } } }
end
function STOCKSECS(tab, c, idx)
  if idx ~= nil then return { { [SNAME] = "Debug Options", [SLIST] = STOCKLIST() } } end
  return GROUPSECS(STOCKLIST())
end
function STOCKBUNDLE(id)
  if id == DEADID then return nil end
  return { [SID] = id, [SNAME] = "Stock row", [SDESC] = "a stock row of the page",
    [SGLAB] = { "Off", "On" }, [SGET] = function() return 1 end,
    [SSET] = function() end, [STYPE] = "ToggleButton" }
end
function DBGDATA(id)
  return { [SID] = id, [SNAME] = "Unlock Everything", [SDESC] = "a debug row the client builds",
    [SGLAB] = { "Off", "On" }, [SGET] = function() return 1 end,
    [SSET] = function(c, v) end, [STYPE] = "ToggleButton" }
end
OPTIONS = { TabIds = { DEBUG = 7 } }
OPTIONS[SKSECT] = STOCKSECS
OPTIONS[SKDA] = function(id, c) return STOCKBUNDLE(id) end
OPTIONS[SKDB] = function(id, c) return STOCKBUNDLE(id) end
OPTIONS[xhash("createoptionlist")] = function(a, b, list, d)
  return function(el, c) return list end
end
KHOOKS = {}
K1 = nil
function KRONOSHOOK()
  local O = OPTIONS
  if type(O) ~= "table" or type(O.TabIds) ~= "table" or O.TabIds.DEBUG == nil then return end
  local function wrap(key, make)
    local cur = O[key]
    if type(cur) ~= "function" or cur == KHOOKS[key] then return end
    KHOOKS[key] = make(cur)
    O[key] = KHOOKS[key]
  end
  wrap(SKSECT, function(orig)
    return function(tab, c, idx, ...)
      if not (type(tab) == "table" and tab[SID] == O.TabIds.DEBUG) then return orig(tab, c, idx, ...) end
      local stock = orig(tab, c)
      local s1 = stock and stock[1]
      local g1 = s1 and s1[SLIST] and s1[SLIST][1]
      local items = {}
      for _, h in ipairs(DBGIDS) do items[#items + 1] = { [SID] = HOF(h) } end
      if g1 then
        for _, it in ipairs(g1[SLIST] or {}) do
          local sb = it[SID]
          if tostring(sb) ~= DEADID then items[#items + 1] = { [SID] = sb } end
        end
      end
      local group = { [SNAME] = g1 and g1[SNAME], [SLIST] = items }
      local secs = { { [SNAME] = s1 and s1[SNAME], [SGLAB] = "debug", [SLIST] = { group } } }
      if idx then return secs[idx] and secs[idx][SLIST] end
      return secs
    end
  end)
  wrap(SKDA, function(orig)
    return function(sb, ...)
      if sb ~= nil and DBGSB[sb] then return DBGDATA(sb) end
      return orig(sb, ...)
    end
  end)
  wrap(SKDB, function(orig)
    return function(sb, c, ...)
      if sb ~= nil and DBGSB[sb] then return DBGDATA(sb) end
      return orig(sb, c, ...)
    end
  end)
end
KRONOSHOOK()
K1 = OPTIONS[SKSECT]
TAB = { [SID] = 7, "debug" }
function IDS(secs)
  local group = secs[1] and secs[1][SLIST] and secs[1][SLIST][1]
  local out = {}
  for _, it in ipairs(group and group[SLIST] or {}) do out[#out + 1] = tostring(it[SID]) end
  return table.concat(out, ",")
end
function K1LIST() return IDS(K1(TAB, 0)) end
function PAGELIST()
  local secs = OPTIONS[SKSECT](TAB, 0)
  local closer = OPTIONS[xhash("createoptionlist")](TAB, 0, secs, false)
  closer(nil, 0)
  return IDS(secs)
end
function DLBL(hexname, id)
  local f = OPTIONS[hexname]
  local b = type(f) == "function" and f(id, 0) or nil
  if type(b) ~= "table" then return "nil" end
  return tostring(b[SID]) .. "|" .. tostring(b[SNAME]) .. "|" .. tostring(b[STYPE])
end
"""

# the client's own record for the eight token ids, in the channel's own order
TOKENREC = r"""
TOKCNT = { [84677] = 1, [84680] = 2, [84678] = 3, [84679] = 4,
           [84672] = 5, [84675] = 6, [84673] = 7, [84674] = 8 }
Loot = { [xhash("IsOwned")] = function(c, id) return TOKCNT[id] or 0 end }
"""

LUA_TEXT = {n: open(os.path.join(LUA_DIR, n), "rb").read().decode("ascii") for n in TEXT_FILES}
SRC = "".join(LUA_TEXT[n] for n in LUA_FILES)

DIAG_START = 'local RC1D = "rc1diag"'
DIAG_END = "local RC1D_END = true"
SHIP_LUA_LEN = 268492
SHIP_LUA_SHA = "39F20C78A680416A8F3D6C46D872910F2D7426C4FDB153F712FF41124A7A275E"
LITERAL_SHA = "A033D299979E9976FE4CFF18DA441BB1DBB35D92C8498FF4D9A6914064981E28"
# the console cleanup of 2026-11-19: every line it took out
LOG_REMOVED = [
    " Q12 act=",
    " Q7 gate=",
    " Q7 lset=",
    " Q7 lset=? why=",
    " ch=",
    " complete=",
    " front=",
    " hit=",
    " ids (header ",
    " inf=",
    " ms=",
    " paused=",
    " snd=",
    " toast=",
    " ver=",
    "g12 rewards ",
    "options items ",
    "options row added",
    "prestige sets: player prestige %s from %s, %s sets open",
    "tokens P2 ch=",
    "tokens P2 raw=",
    "tokens P2 st=",
    "tokens P3 end p=",
    "tokens P4 c=",
    "tokens Q12 done used=",
    "tokens Q12 kind=",
    "tokens Q4b own=",
    "tokens Q4b own=? why=",
    "tokens txt key=",
    "weekly body=",
    "zm_ch_s",
    "zm_ch_ver",
]
LITERAL_REMOVED = [
    " (locks ",
    " 153766=",
    " ah=",
    " b=",
    " err=",
    " gi=",
    " in scope)",
    " inscope=",
    " isp=",
    " len=",
    " locks=",
    " plain=",
    " playing=",
    "v4",
    "v5",
    "v8",
    "Challenge.GetAEKindID refused ae_kind_reticle",
    "GL_HACK",
    "GetSoundLengthMS",
    "GetWeaponBlueprints",
    "IsSoundPlaying",
    "armory check bp ",
    "armory check bp missing",
    "armory check door 151472=",
    "armory check list win=",
    "armory check owned 151472=",
    "armory check progression 151472=",
    "getweaponmpref",
    "isunlocked",
    "no Challenge.GetAEKindID in this VM",
    "sat_sm_civet",
    "sndprobe alias=",
    "sndprobe: no PlaySound in this vm",
    "sndprobe: raised alias=",
    "sndvm ps=",
    "ui_select_confirm",
    "uin_jup_challenge_multikills",
    "uin_jup_master_challenge_complete",
    "uin_jup_master_challenge_complete_music",
    "uin_loadout_hilite",
    "withid",
]
LITERAL_ADDED = [
    " ",
    " - not one of ours, so no row is read for it",
    " (seeded late)",
    " - the camo map is truncated and",
    " (advanced)",
    " 101644 b=",
    " 131708 b=",
    " agree=",
    " aliases=",
    "answer",
    "armory card ",
    "armory late ",
    "armory picture wrapped for ",
    "armory name wrapped for ",
    " weapon loots",
    " belongs to ",
    " bit0=",
    " bit1=",
    " bundle=",
    " bundleType=",
    " buy=",
    " cat=",
    " cer=",
    " child ",
    " children=",
    " col=",
    " complete=false progress=",
    " complete=true progress=",
    " computed and it keeps the client's own answer",
    " craft=",
    " card=",
    "craft",
    " csv=",
    " ctl=",
    " cum=",
    "CLUA",
    "COMMON_ITEM",
    "GetItemSpawnEntryImageByID",
    "getbwimage",
    "armory craft lock raised - answering locked",
    "card lock: ",
    "card lock: purchasable probe missing ",
    "cardbuy",
    " default=",
    " den=",
    " diff=",
    " door=",
    " empty=",
    " file=",
    " firstNum=",
    " fork429=",
    "gate",
    " head=",
    " hex=",
    " ids=",
    " is ",
    " is a prestige reward for ",
    " is not one of ours - not bound",
    " isComplete=",
    " k398=",
    " k400=",
    " key=",
    " l92066=",
    " left as the client answers it",
    " live=",
    " lock=",
    "lock",
    " lvl=",
    " lvl=1 reward=",
    " max=",
    " mwcf=",
    " names ",
    " native=",
    " none",
    "n/a",
    " not kept",
    " num=",
    " opacity=",
    " open=",
    " our=",
    " pct=",
    " prestigeRef=",
    "press",
    " r92066=",
    " ranks=",
    " reward=",
    " rewardData=",
    " route=",
    " route=B",
    " rows=",
    " show315=",
    " show422=",
    " side card refused",
    " sound=",
    " split1=",
    " src=",
    " st=",
    " sticker=",
    " store ids by type: ",
    " tbl315=",
    " tbl422=",
    " types=attachment,camo,reticle",
    " vars=",
    " vm=",
    "v12",
    " why=",
    " wkhead=",
    " wlevel=",
    " x=",
    "#x37dc362a78cf1d3d3",
    "%d",
    "/absent",
    "0x%x%x%x%x%x%x%x%x",
    "0x7dc362a78cf1d3d3",
    "+",
    "2=",
    "3",
    "3=",
    "7C6F4A53654BFFDF",
    ": cards capped at ",
    ": snd ",
    ": snd capped at ",
    "=",
    "?",
    "A",
    "AMMOMOD",
    "ATTACHMENT",
    "B",
    "BATTLEMAP.",
    "BR",
    "Bundles",
    "CHARM",
    "CallingCardUtils",
    "CamoChallenge",
    "ChallengeComplete",
    "DailyChallengeNotification",
    "DataSources",
    "Dvar",
    "E1A4D0E8679C1CCB",
    "EMBLEM",
    "EMOTE",
    "EQUIPMENT",
    "EmptySplashRef",
    "GetAmount",
    "GetCumulatedProgressNormalized",
    "GetFileTableByType",
    "GetFirstBundleWithLootId",
    "GetMilliseconds",
    "GetRewardDataUnlockedAtWeaponLevel",
    "GetUnlockDescription",
    "GetValue",
    "HaveActiveSplashScreens",
    "HudManager",
    "IsChallengeComplete",
    "IsLootUseableOnCurrentPlatform",
    "IsReward",
    "IsUnlocked",
    "isitemlocked",
    "itemref",
    "LOAD_SCREEN",
    "MP",
    "Medal",
    "MessageType",
    "OB",
    "OPERATOR",
    "OPERATOR_EXECUTION",
    "OPERATOR_SKIN",
    "PAGEDBATTLEPASS.",
    "PERK",
    "PurchaseMenuUtils",
    "PLAYERCARD",
    "QB1 ",
    "QB1 done=none",
    "QB10 ref=",
    "QB11 id=",
    "QB11 row=none",
    "QB12 bool=",
    "QB13 aek=",
    "QB14 g12 set=",
    "QB15 ",
    "QB16 skin=",
    "QB17 show429=",
    "QB18 ret=",
    "QB19 ",
    "QB19 cards=",
    "QB2 ",
    "QB2 api=",
    "QB20 ",
    "QB3 hash=",
    "QB4 ",
    "QB5 anchor 126605 b=",
    "QB5 diff ",
    "QB5 n=",
    "QB6 ",
    "QB7 ",
    "QB8 prestige0=",
    "QB9 ref=",
    "RETICLE",
    "SOUND_SETS",
    "SPRAYS",
    "STICKER",
    "STORE",
    "STORE.Bundles.",
    "STREAK",
    "SUPER",
    "SplashManager",
    "SplashTrapSubheader",
    "SplashUtils",
    "WEEKLY CHALLENGE COMPLETE",
    "WILDCARD",
    "WeaponLevel",
    "WeeklyChallengeSplashNotification",
    "ZM",
    "^#x%x+$",
    "^%x+$",
    "^zm_unlock_",
    "_DataSources",
    "a",
    "absent",
    "absent/absent",
    "acarry:",
    "ae/sat_ae_autogen_prestige_challenges.csv",
    "ae/sat_ae_autogen_reticle_challenges.csv",
    "ae/sat_ae_autogen_seasonal_challenges.csv",
    "ae/sat_gs_challenges.csv",
    "ae_kind_armory",
    "ae_kind_reticle_cer",
    "ans",
    "b",
    "c",
    "callingCardPrestigeChallenges",
    "camo bundles ",
    "camo:extra:",
    "camo:watch:",
    "camoA",
    "camoB",
    "camos",
    "card",
    "card table ",
    "carried:",
    "carry-forward: pack=unknown dvar=",
    "category",
    "chal week gate - no Challenge.IsChallengeComplete in this VM, the vanished row is carded",
    "chalD",
    "chalWB",
    "challenge/jup_ch_weekly_challenge_completed",
    "challengeComplete",
    "challengeSplash",
    "challenges",
    "core absent - no part ",
    "currentSplash",
    "dailyNotification",
    "dark",
    "diag",
    "diag off",
    "displayLocation",
    "empty_splash_ref",
    "err:side",
    "error side card: ",
    "false",
    "foreign ref",
    "g12",
    "gamer_profile",
    "gcamo:carried:",
    "generalChallenge",
    "getactiveweaponranktablebundle",
    "getactiveweaponranktableranklist",
    "getaekindfromid",
    "getchallengestate",
    "getdesclocalizedbyid",
    "getlootiteminfofromid",
    "getplayerprestigelevel",
    "getprimaryprojectfromref",
    "getrewards",
    "getstickerbookchallengedata",
    "getstickerbookchallengesdata",
    "glock:carried:",
    "gopen:platform",
    "groupId",
    "gunsmithChallenges",
    "handle",
    "hash_7dc362a78cf1d3d3",
    "id315",
    "inGame",
    "insertTime",
    "isComplete",
    "isbattlepassreward",
    "isblackcellreward",
    "iw9",
    "iw9_",
    "jup",
    "jup_",
    "kronos_cfwd",
    "levelUnlock",
    "lui_use_gl_splash",
    "lui_weekly_challenge_menu_enabled",
    "matchobjectivetext",
    "mwcf_box_pools",
    "native",
    "nil",
    "no rows",
    "nosplash",
    "notification_feed_opacity",
    "off",
    "open ",
    "options",
    "part main armed ",
    "path",
    "prestige lock: the weapon list is longer than ",
    "prison",
    "progression_tuning: part camos armed",
    "progression_tuning: part challenges armed",
    "progression_tuning: part diag armed",
    "progression_tuning: part prison armed",
    "progression_tuning: part reticles armed",
    "progression_tuning: part splash armed",
    "progression_tuning: part weaponxp armed",
    "pt_diag_off",
    "pt_diagb",
    "raised",
    "rbdiag",
    " refused",
    "ret",
    "reticle",
    "reticleChallenges",
    "reticles",
    "sat",
    "sat_",
    "sat_ui_playercard_044",
    "sat_ui_playercard_173",
    "seasonalChallenges",
    "setText",
    "settings",
    "shouldOverride",
    "sound",
    "splash",
    "splash absent - no card is drawn",
    "splashck",
    "splashes",
    "splashes/daily_challenge_completed",
    "store",
    "store open: no STORE.Bundles.IsLootUseableOnCurrentPlatform in this VM - a store id keeps the client's",
    "t10",
    "t10_",
    "t10_me_p55_bgloves",
    "tablelookupentirecolumnbynum",
    "true",
    "type",
    "ui_playercard_869",
    "uin_jup_challenge_camo_unlock",
    "uin_jup_challenge_complete",
    "unlock dvars: ",
    "unread",
    "weaponLevel",
    "weaponProgression",
    "weaponxp",
    "weekgate",
    "weekly body=empty",
    "weekly card id=",
    "weekly header native=",
    "weekly header=none",
    "weekly xp id=",
    "widget",
    "widgetMap",
    "xhashdvar",
    "zm_g11_",
    "zm_g12_",
    "zm_g12_ver",
    "zm_local_prestige",
    "zm_unlock_ammomods",
    "zm_unlock_camos",
    "zm_unlock_cards",
    "zm_unlock_charms",
    "zm_unlock_emblems",
    "zm_unlock_emotes",
    "zm_unlock_equipment",
    "zm_unlock_fieldupgrades",
    "zm_unlock_finishers",
    "zm_unlock_loadingscreens",
    "zm_unlock_operators",
    "zm_unlock_perks",
    "zm_unlock_reticles",
    "zm_unlock_scorestreaks",
    "zm_unlock_sprays",
    "zm_unlock_stickers",
    "zm_unlock_weapons",
    "zm_unlock_wildcards",
    # the two rows parts: the page's own members, the two ids, the channel and its log lines
    " aeid=",
    " kd=",
    " wraps=",
    " no bundle",
    "4849F2616A844C09",
    "5a6d0000000000be",
    "7bf7f57679e8d050",
    "9f6c4b08602983fb",
    ";c=([%d,]+)",
    ";x=1",
    "=#x",
    "=missing",
    "Active XP Tokens count down in real-time",
    "Active XP Tokens count down with in-game time",
    "DoubleXPType",
    "Dropdown",
    "Enable Double XP",
    "GetCurrentEpochTime",
    "GetGlobalDoubleXPEventsEndTime",
    "IsDoubleWeaponXPActiveByType",
    "IsPaused",
    "Keeps Level and Weapon Double XP active at all times while on.",
    "MenuBuilder",
    "NOTIFICATIONS",
    "OPTIONS",
    "Off",
    "On",
    "OnlineProgression",
    "P_",
    "SetDvarString",
    "Sets how many of every Level and Weapon 2XP token you own.",
    "ToggleButton",
    "XP Token Amount",
    "XPTOKENS",
    "activateachievement",
    "ae:",
    "ae:set",
    "ae_kind_tokens",
    "cer__doublexp__player_xp_end_time",
    "cer__doublexp__weapon_xp_end_time",
    "cer_ae_kind_tokens",
    "chan",
    "createoptionlist",
    "creategenericnotification",
    "data_a",
    "data_b",
    "e7686f7a9907efd8",
    "fallback",
    "getalldoublexpstates",
    "gettoastdatafromachievementid",
    "getuserstatesvalues",
    "hash_4849f2616a844c09",
    "isdoubleweaponxpactive",
    "isdoublexpactive",
    "isdoublexpactivebytype",
    "onachievementactivated",
    "opt",
    "options anchor missing",
    "options armed",
    "options data id=",
    "options move skip ",
    "options row moved after=",
    "options slot ",
    "progression_tuning: part options armed",
    "progression_tuning: part tokens armed",
    "pt_permanent",
    "pt_token_amount",
    "pt_tokens_ch",
    "pt_tokens_st",
    "sections",
    "seed",
    "settokenuselocked",
    "tokens P3 wrap=1",
    "tokens P5 perm=",
    "tokens P6 event=",
    " q=",
    "%d+",
    ",",
    ";q=",
    "Challenge",
    "IsChallengeComplete",
    "^a=(%d+)",
    "getcachedarmoryachievements",
    "id",
    "q=([%d,]+)",
]
LITERAL_RE = re.compile('"([^"\\n]*)"' + "|'([^'\\n]*)'")


def load(rt):
    """Run the parts in the order the active replay mode names."""
    for name in LOAD_ORDERS[LOAD_ORDER]:
        rt.execute(LUA_TEXT[name])


def where(needle):
    """The parts that carry a needle."""
    return [n for n in LUA_FILES if needle in LUA_TEXT[n]]


def rebuild_block():
    """The lines the serial rebuild resets, from the door tally to the tracker."""
    m = re.search(r"  G\.doorSaid, G\.doorN = \{\}, 0\n(.*?)\n  if S\.tracker", SRC, re.S)
    return m.group(0) if m else ""


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
    """The nine parts that ship - everything except the quarantined diagnostic."""
    return "".join(LUA_TEXT[n] for n in SHIP_FILES)


def tokens_first():
    """What the token part does when it is read before the part that fills its api, or None."""
    try:
        from lupa.lua51 import LuaRuntime
    except Exception:
        return "lupa absent"
    rt = LuaRuntime(unpack_returned_tuples=True)
    rt.execute(PRELUDE)
    rt.execute("FRONTEND = false")
    try:
        rt.execute(LUA_TEXT[TOKENS])
    except Exception as exc:
        return str(exc)
    return None


def diag_quarantine():
    """The diagnostic part with its quarantined span left out."""
    lines, start, end = diag_span()
    if start is None or end is None:
        return LUA_TEXT[DIAG]
    return "\n".join(lines[:start] + lines[end + 1:])


def door_owners(texts):
    """The parts that name the ownership door, from a part-to-text map."""
    return [n for n in LUA_FILES if '"isunlockedwithid"' in texts.get(n, "")]



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


def lua_rslabs(rt, slabs):
    rt.execute("R_SLABS = {" + ",".join('"%s"' % s for s in slabs) + "}")
    rt.execute("SET_RPARTS()")


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


def num(rt, expr):
    """A lua number, with a nil read as zero - the parts leave a zero out of their own tables."""
    v = rt.eval(expr)
    return 0 if v is None else int(v)


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
# no comment line in the tokens part is excused from the rule any more
COMMENT_DEBT = frozenset([])
# the retired words the tokens part carries as reads of the client's own channel, and not as its own
TOKENS_RESIDUE_KEEP = [
    "-- the token channel the gsc reads",
    "-- the gsc status read only",
]


def src_owner(i):
    """The part that SRC line i, counting from one, comes from."""
    end = 0
    for name in LUA_FILES:
        end += LUA_TEXT[name].count("\n")
        if i <= end:
            return name
    return None


def bad_comments():
    """Every comment line, held to the file rule, and the ones kept by name."""
    bad, owed = [], []
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
        if (src_owner(i), text) in COMMENT_DEBT:
            owed.append(text)
            continue
        if not text or not COMMENT_RULE.match(text) or len(text.split()) > COMMENT_WORDS:
            bad.append("%d: %s" % (i, text[:44]))
    return bad, owed


def static_checks():
    raw_parts = {n: open(os.path.join(LUA_DIR, n), "rb").read() for n in TEXT_FILES}
    mod = json.load(open(MODJSON, encoding="utf-8"))

    check("mod.json: name", mod["name"] == "Progression Tuning", mod.get("name"))
    check("mod.json: author", mod["author"] == "ripsawuk", mod.get("author"))
    check("mod.json: version 1.3", mod["version"] == "1.3", mod.get("version"))
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
    bad, owed = bad_comments()
    ncom = sum(1 for ln in SRC.split("\n") if ln.strip().startswith("--"))
    check("lua: every comment line is one lower-case line of ten words at most",
          not bad and ncom >= COMMENT_MIN and "/*" not in SRC,
          ", ".join(bad[:6]) or "%d comment lines" % ncom)
    check("lua: the tokens part owes the comment rule nothing by name",
          not owed, " | ".join(owed))
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
          and "splashck" not in ship and not re.search(r"\bck_card\b", ship) and "CK_CARD" not in ship)
    check("lua: the splash part paces on the main part's own timer step",
          "local TICK_MS = 250" in LUA_TEXT[SPLASH] and "local TICK_MS = 250" in LUA_TEXT[MAIN])
    check("lua: the weekly subtitle is one plain line - the number is never marked",
          "MarkLocalized" not in SRC and '"getDesc"' in LUA_TEXT[SPLASH]
          and 'displayLocation = "dailyNotification"' in LUA_TEXT[SPLASH])
    check("order: the alphabetical replay is the order the client arms the parts in",
          [n[len("progression_tuning_"):-len("_post.lua")] for n in LOAD_ORDERS["alphabetical"]]
          == ["armory", "camos", "challenges", "diag", "main", "options", "prison", "reticles",
              "splash", "tokens", "weaponxp"],
          " | ".join(LOAD_ORDERS["alphabetical"]))
    check("order: the harness order is a fourth, different order",
          LOAD_ORDERS["harness"] != LOAD_ORDERS["alphabetical"]
          and LOAD_ORDERS["harness"] != LOAD_ORDERS["reversed"]
          and len(set(tuple(v) for v in LOAD_ORDERS.values())) == 3)
    check("order: the reversed replay keeps the nine original parts reversed and the two new last",
          LOAD_ORDERS["reversed"][-2:] == CORE_LAST
          and LOAD_ORDERS["reversed"][:-2] == [n for n in sorted(LUA_FILES, reverse=True)
                                               if n not in CORE_LAST],
          " | ".join(LOAD_ORDERS["reversed"]))
    check("lua: the diagnostic's arm gate still counts eight parts, and there are eleven",
          "for _ in pairs(S.parts) do n = n + 1 end" in LUA_TEXT[MAIN]
          and "if n < 8 then return end" in LUA_TEXT[MAIN] and len(LUA_FILES) == 11)
    first = tokens_first()
    check("order: the token part read before the part that fills its api raises at chunk scope",
          first in (None, "lupa absent") or "dv' (a nil value)" in first, str(first)[-80:])

    scan = ship.replace('"RETICLE"', "").replace(LUA_TEXT[ARMORY], "")
    for name in CARD_TABLES + CARD_PATHS + UNLOCK_DVARS:
        scan = scan.replace('"%s"' % name, "")
    for word in TOKENS_RESIDUE_KEEP:
        scan = scan.replace(word, "")
    found = [k for k in REMOVED if k in scan]
    check("lua: the retired channel name and the gsc word are reads and prose, once each, in tokens",
          all(sum(LUA_TEXT[n].count(w) for n in LUA_FILES) == 1 for w in TOKENS_RESIDUE_KEEP)
          and all(w in LUA_TEXT[TOKENS] for w in TOKENS_RESIDUE_KEEP),
          " | ".join(w for w in TOKENS_RESIDUE_KEEP if LUA_TEXT[TOKENS].count(w) != 1))
    others = [n for n in SHIP_FILES if n != ARMORY
              and any(w in LUA_TEXT[n] for w in ARMORY_WORDS)]
    check("lua: the armory words live in the armory part alone",
          others == [], " | ".join(others))
    drop = [k for k in DROPPED_CARDS + DROPPED_PATHS if k in ship]
    check("lua: the four dropped card tables are named nowhere in the shipped parts",
          drop == [], " | ".join(drop))
    gone = [k for k in ("GCARD_SLOW", "cardTry", "cardDone", "cardIdx", "cardst",
                        "cardTick", "cardSaid", "card rewards ", "gloadcards")
            if k in LUA_TEXT[MAIN]]
    check("lua: the round robin is gone - no per tick index, no slow retry, no union line",
          gone == [] and 'A.loadcard = gloadcard' in LUA_TEXT[MAIN], " | ".join(gone))
    check("lua: the loader holds the three reward tables and their short keys",
          LUA_TEXT[MAIN].count('{ key = "') == 3
          and all('key = "%s"' % k in LUA_TEXT[MAIN] for k in ("ret", "sea", "gs")))
    have = literals(SRC)
    gone = sorted(set(LITERAL_REMOVED + LOG_REMOVED) & have)
    dig = hashlib.sha256(("\n".join(sorted(have)) + "\n").encode()).hexdigest().upper()
    arm = [n for n in LUA_FILES if PART_ARM.get(n, "part " + n[len("progression_tuning_"):-len("_post.lua")]
                                                 + " armed") not in LUA_TEXT[n]]
    check("lua: none of the removed identifiers appears, the literal set is the split's own, and every part arms",
          not found and not gone and dig == LITERAL_SHA and set(LITERAL_ADDED) <= have and arm == [],
          ", ".join(found + gone + arm) or "%d literals %s" % (len(have), dig[:16]))

    # two parts write one dvar each, the armory pick channel and the token channel; every other part stays write-free
    writes = ship.replace(LUA_TEXT[ARMORY], "")
    for token, why in (("SetDvar", "writes a dvar"), ("io.", "file IO"), ("os.", "OS calls"),
                       ("dofile", "runs a file"), ("loadfile", "loads a file"),
                       ("loadstring", "compiles a string"), ("require", "loads a module"),
                       ("debug.", "debug library")):
        body = writes.replace('"SetDvarString"', "") if token == "SetDvar" else SRC
        check("lua: no %r (%s)" % (token, why), token not in body)
    check("lua: the two dvar writes are the armory channel and the token channel, one part each",
          [n for n in LUA_FILES if "SetDvar" in LUA_TEXT[n]] == [ARMORY, TOKENS]
          and LUA_TEXT[ARMORY].count("SetDvar") == 1 and where("pt_armory_ch") == [ARMORY]
          and LUA_TEXT[ARMORY].count('"pt_armory_ch"') == 1
          and [n for n in LUA_FILES if '"SetDvarString"' in LUA_TEXT[n]] == [ARMORY, TOKENS]
          and sum(LUA_TEXT[n].count('"SetDvarString"') for n in LUA_FILES) == 2
          and '"PlaySound"' in LUA_TEXT[TOKENS] and SRC.count('"PlaySound"') == 1,
          " | ".join(n for n in LUA_FILES if "SetDvar" in LUA_TEXT[n]))
    check("lua: the queue is the game's own armory list filtered to ours and its own completion answer",
          '"getcachedarmoryachievements"' in LUA_TEXT[ARMORY]
          and '"IsChallengeComplete"' in LUA_TEXT[ARMORY] and "MINE[id]" in LUA_TEXT[ARMORY])
    check("lua: the seed reads a merged line and the writer keeps the queue it read",
          'string.match(v, "^a=(%d+)")' in LUA_TEXT[ARMORY]
          and 'string.match(v, "q=([%d,]+)")' in LUA_TEXT[ARMORY]
          and 'val = val .. ";q=" .. join(q)' in LUA_TEXT[ARMORY])
    check("lua: one channel writer, so the arm and the press cannot disagree",
          LUA_TEXT[ARMORY].count("dchput(") == 3 and LUA_TEXT[ARMORY].count("return dchput(val)") == 1,
          "%d call(s)" % LUA_TEXT[ARMORY].count("dchput("))
    check("lua: the armory part never rethrows - every call through is a pcall with a safe answer",
          "error(" not in LUA_TEXT[ARMORY] and LUA_TEXT[ARMORY].count("pcall(orig") == 7
          and "if not res[1] then return false end" in LUA_TEXT[ARMORY]
          and "if not res[1] then return end" in LUA_TEXT[ARMORY]
          and "if not res[1] then return nil end" in LUA_TEXT[ARMORY]
          and "if not ok then return 0 end" in LUA_TEXT[ARMORY]
          and "local ok, locked = pcall(orig, c, item, ...)" in LUA_TEXT[ARMORY]
          and "local ok, v = pcall(orig, id, ...)" in LUA_TEXT[ARMORY],
          "%d error call(s), %d call(s) through" % (LUA_TEXT[ARMORY].count("error("),
                                                    LUA_TEXT[ARMORY].count("pcall(orig")))
    check("lua: the blueprint rule and its window never rethrow either",
          LUA_TEXT[PRISON].count("error(") == 1 and "if not res[1] then return {} end" in LUA_TEXT[PRISON]
          and LUA_TEXT[PRISON].count("pcall(") >= 20
          and "getbaseweaponlootidfromblueprint" in LUA_TEXT[PRISON]
          and "ownsBlueprintOfWeapon" in LUA_TEXT[PRISON]
          and "ownsBlueprintOfWeapon" not in LUA_TEXT[ARMORY]
          and "getmodifications" in LUA_TEXT[PRISON]
          and "getmodifications" not in LUA_TEXT[ARMORY],
          "%d error call(s), %d pcall(s)" % (LUA_TEXT[PRISON].count("error("),
                                             LUA_TEXT[PRISON].count("pcall(")))

    texts = {n: LUA_TEXT[n] for n in LUA_FILES}
    texts[DIAG] = diag_quarantine()
    check("lua: one ownership door, one name - isunlockedwithid appears once",
          ship.count('"isunlockedwithid"') == 1 and door_owners(texts) == [MAIN],
          "%d in %s" % (ship.count('"isunlockedwithid"'), door_owners(texts)))
    check("lua: the ownership-door guard still flags a part that names it",
          door_owners({MAIN: LUA_TEXT[MAIN],
                       PRISON: 'local w = fn_of(L, "isunlockedwithid")'}) == [MAIN, PRISON]
          and door_owners({DIAG: 'local w = fn_of(L, "isunlockedwithid")'}) == [DIAG],
          "shipped=%s unquarantined=%s"
          % (door_owners({MAIN: LUA_TEXT[MAIN],
                          PRISON: 'local w = fn_of(L, "isunlockedwithid")'}),
             door_owners({DIAG: 'local w = fn_of(L, "isunlockedwithid")'})))
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
    check("lua: the unlock camos toggle stands the prestige band aside",
          '{ "CAMO", "zm_unlock_camos" }' in SRC and "if gtoggle(GTYPE_C) then return false end" in SRC)
    check("lua: the door reads the client's own item type, because a prestige reward has no bit",
          "local t = gtype(n)" in SRC and "if bit == 1 or glogging() then" not in SRC)
    check("lua: the value door is keyed by the client's own metadata and its own token accessor",
          "local function gvalinstall()" in SRC and '"getprogressionitemmetadata"' in SRC
          and '"getweaponprestigetokenlootid"' in SRC
          and "if gsent()[n] == true then ans = 0" in SRC
          and "elseif GTOK ~= nil and GTOK[n] == true then ans = 0 end" in SRC
          and "      v = f(c, id, ...)" in SRC)
    blk = rebuild_block()
    check("lua: the rebuild keeps the static caches and clears only the tallies",
          "G.psaid, G.psaidN = {}, 0" in blk
          and "G.camoMapSaid, G.camoMissSaid = 0, 0" in blk
          and not re.search(r"G\.(?:bundles|camoref|pcamo|camomap|camoTry)\b", blk)
          and "G.doorSaid, G.doorN = {}, 0" in blk,
          " | ".join(ln.strip() for ln in blk.split("\n"))[:200])
    check("lua: no reader walks the 65536-char payload to count it",
          "gcountLocks" not in SRC and "gcountScope" not in SRC and "GBITS" not in SRC
          and "for i = 1, GHEXLEN" not in SRC)
    check("lua: no new timer, and the only dispatchers are the splash queue, the token event and the armory card",
          SRC.count(":Wait(") == 3 and "CreateEventTimer" not in SRC
          and where(":Wait(") == [MAIN, ARMORY]
          and LUA_TEXT[MAIN].count(":Wait(") == 2 and LUA_TEXT[ARMORY].count(":Wait(") == 1
          and SRC.count("local function fire(") == 2
          and where("local function fire(") == [SPLASH, TOKENS]
          and where("ProcessEvent") == [SPLASH, ARMORY, TOKENS]
          and SRC.count("ProcessEvent") == (LUA_TEXT[SPLASH].count("ProcessEvent")
                                            + LUA_TEXT[ARMORY].count("ProcessEvent")
                                            + LUA_TEXT[TOKENS].count("ProcessEvent")),
          "%d waits in %s, %d fire, %d ProcessEvent" % (
              SRC.count(":Wait("), "/".join(where(":Wait(")), SRC.count("local function fire("),
              SRC.count("ProcessEvent")))
    check("lua: the wrapper is add-only - a raised call falls through",
          "if ok and answer then return false end" in SRC and "return o(c, id, ...)" in SRC)
    check("lua: the display half answers each record getter exactly once",
          ship.count('"getchallengeprogress"') == 3 and ship.count('"getchallengedefaultprogress"') == 2
          and SRC.count('wrap_member(OC, "getchallengeprogress",') == 1
          and where('wrap_member(OC, "getchallengeprogress",') == [WEAPONXP]
          and SRC.count('wrap_member(OC, "getchallengedefaultprogress",') == 1
          and where('wrap_member(OC, "getchallengedefaultprogress",') == [WEAPONXP]
          and LUA_TEXT[ARMORY].count('"getchallengeprogress"') == 1
          and "if tonumber(id) ~= ACTIVATION then" in LUA_TEXT[ARMORY]
          and "local res = pack(pcall(orig, c, id, ...))" in LUA_TEXT[ARMORY]
          and "if not res[1] then return nil end" in LUA_TEXT[ARMORY],
          "%d / %d, wrapped in %s" % (ship.count('"getchallengeprogress"'),
                                      ship.count('"getchallengedefaultprogress"'),
                                      "/".join(where('wrap_member(OC, "getchallengeprogress",'))))

    check("lua: reads Dvar.GetDvarString by name", '"GetDvarString"' in SRC)
    check("lua: names the arm/ver/scope dvars as the hook spells them",
          all('"%s"' % n in SRC for n in ("zm_g11_arm", "zm_g11_ver", "kronos_g11_scope")))
    check("lua: builds the 33 part names under both payload prefixes",
          'gnames("zm_g11_")' in SRC and 'gnames("zm_g12_")' in SRC
          and "for i = 0, 32" in SRC and 'prefix .. "%d"' in SRC)
    check("lua: checks the header shape <serial>:33:65536",
          '"^(%d+):(%d+):(%d+)$"' in SRC and "GPARTS" in SRC and "GHEXLEN" in SRC)
    check("lua: refuses a payload whose length is not 65,536",
          "local GHEXLEN = 65536" in SRC and "refused, keeping the previous payload" in SRC)
    check("lua: the answer needs the bit AND the reward set AND the client's own item type",
          "glockedNow(n)" in SRC and "GTYPE_A" in SRC and "GTYPE_C" in SRC and "GTYPE_R" in SRC
          and "locked = bit == 1 and greward(n) and not gdefault(n) and not gcarried(n)" in SRC)
    check("lua: a locked answer is refused when the id's own ref is carried, on both rules",
          "local function gcarried(n)" in SRC and SRC.count("not gcarried(n)") == 2)
    check("lua: types come from the client's own constants and its own getter",
          '"gettypeforid"' in SRC and '"itemTypes"' in SRC and '"ATTACHMENT"' in SRC
          and '"CAMO"' in SRC and '"RETICLE"' in SRC and "GTYPE_A, GTYPE_C, GTYPE_R = na, nc, tonumber(r)" in SRC)
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
    check("lua: the one switch that stands every lock down is named, not hashed",
          named == ["zm_unlock_all"], ", ".join(named))

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

    scripts = sorted(n for n in (os.listdir(SCRIPTS_DIR) if os.path.isdir(SCRIPTS_DIR) else [])
                     if n.lower().endswith((".gsc", ".gscc")))
    shipped = {n: open(os.path.join(SCRIPTS_DIR, n), "rb").read().decode("utf-8", "replace").lower()
               for n in scripts}
    storing = [n for n in scripts if "nengine_store_" in shipped[n]]
    check("gsc: no shipped script calls nengine_store_ (the g10 store crash, D42/D43)",
          storing == [], ", ".join(storing))

    tkraw = open(os.path.join(SCRIPTS_DIR, "progression_tuning_tokens.gsc"), "rb").read()
    check("gsc: the tokens script is rc1.3's file byte for byte",
          len(tkraw) == TOKENS_GSC_LEN and hashlib.sha256(tkraw).hexdigest().upper() == TOKENS_GSC_SHA,
          "%d B %s" % (len(tkraw), hashlib.sha256(tkraw).hexdigest().upper()))

    ar = shipped.get(ARMORY_GSC, "")
    check("gsc: the armory script runs one level thread and arms it once",
          ar.count("level thread ") == 1 and ar.count("autoexec ") == 1,
          "%d thread(s), %d autoexec" % (ar.count("level thread "), ar.count("autoexec ")))
    endon = ar.find('level endon("end_game");')
    first_state = ar.find("level.pt_arm_prev = -1;")
    check("gsc: the armory thread stands down on end_game before any state it keeps",
          endon != -1 and first_state != -1 and endon < first_state, "endon at %d" % endon)
    check("gsc: the feed's four fields start on level, the serial from its own dvar",
          ar.count("level.pt_arm_prev = -1;") == 1 and ar.count("level.pt_arm_acc = 0;") == 1
          and ar.count("level.pt_arm_beat = 0;") == 1
          and ar.count('level.pt_arm_s = int(getdvar("pt_armory_s", "0")) + 1;') == 1
          and ar.count('setdvar("pt_armory_s", level.pt_arm_s + "");') == 1)
    feed = re.search(r"\nprogression_tuning_armory_feed\(\)\s*\n?\{(.*?)\n\}", ar, re.S)
    body = feed.group(1) if feed else ""
    check("gsc: the feed reads the operator's pre cap rank xp field",
          'p.var_8b69ecbd466a79fa["rankxp"]' in body and "x = int(x);" in body)
    check("gsc: the feed's total lives on level, never in a bare local",
          "level.pt_arm_acc = level.pt_arm_acc + (x - level.pt_arm_prev);" in body
          and "level.pt_arm_prev = x;" in body
          and "level.pt_arm_beat = level.pt_arm_beat + 1;" in body)
    check("gsc: the feed publishes the hook's dvar with the three fields",
          'setdvar("pt_armory_xp", "s=" + level.pt_arm_s + ";x=" + level.pt_arm_acc + ";h=" + level.pt_arm_beat);'
          in body)
    loop = ar.find("while (true)")
    call = ar.find("progression_tuning_armory_feed();")
    wait = ar.find("wait 0.5;")
    check("gsc: the feed is called from the one loop, after its wait, with no thread of its own",
          loop != -1 and wait != -1 and loop < wait < call and ar.count("progression_tuning_armory_feed();") == 1)
    check("gsc: the armory script writes dvars only, no store, no playerdata, no notify",
          ar.count("setdvar(") == 2 and "nengine_store_" not in ar and "setplayerdata" not in ar
          and "notify(" not in ar, "%d setdvar" % ar.count("setdvar("))
    check("gsc: the armory script never reads or writes the token channel",
          "pt_tokens" not in ar)

    info("lua %d B sha256 %s" % (len(SRC.encode()), hashlib.sha256(SRC.encode()).hexdigest().upper()))
    info("mod.json %d B" % os.path.getsize(MODJSON))


def payload_cases(lua51):
    rt = new_rt(lua51, pre='SET_PAID("v1;88929:1200:1200;102705:300:300")')
    pump(rt, 2)
    lines = lines_of(rt)
    check("payload: two guns are read", has_line(lines, "paid source dll - ptsplash_paid carries 2 gun(s)"),
          " | ".join(lines[:6]))
    check("payload: gun A primes at the level its total reaches",
          num(rt, "ProgressionTuning.guns['sat_pi_atlas'].level") == 1)
    check("payload: gun B primes on its own ladder",
          num(rt, "ProgressionTuning.guns['sat_sh_shepherd'].level") == 0)

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
    check("two guns: the first sighting primes 0",
          num(rt, "ProgressionTuning.guns['sat_pi_atlas'].level") == 0)
    check("two guns: nothing is drawn at the prime", rt.eval("NEVENTS()") == 0)

    rt.execute('SET_PAID("v1;88929:1050:1050;102705:600:600")')
    pump(rt, 8)
    l = lines_of(rt)
    check("two guns: A crosses to level 1", has_line(l, "sat_pi_atlas crossed 1 row 54499"), " | ".join(l[-6:]))
    check("two guns: B primes at level 1 on its own ladder",
          num(rt, "ProgressionTuning.guns['sat_sh_shepherd'].level") == 1)
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
          num(rt, "ProgressionTuning.guns['sat_pi_atlas'].level") == 3, " | ".join(lines[:6]))
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
    check("crossing: 999 is level 0",
          num(rt, "ProgressionTuning.guns['sat_pi_atlas'].level") == 0)
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
    check("extras: the payload is read into the part's own state, with the dll as its source",
          num(rt, "ProgressionTuning.paidN") == 1
          and num(rt, "ProgressionTuning.paid[102705].total") == 1793
          and rt.eval("ProgressionTuning.paidon") is True
          and rt.eval("ProgressionTuning.paidsaid") == "dll",
          "%s / %s" % (rt.eval("ProgressionTuning.paidN"), rt.eval("ProgressionTuning.paidsaid")))
    check("extras: the gun it pays binds its own ref and its ladder's level, with no line at all",
          rt.eval("ProgressionTuning.lootgun[102705].ref") == "sat_sh_shepherd"
          and num(rt, "ProgressionTuning.lootgun[102705].level") == 2
          and count_line(lines, "hb tick=") == 0,
          " | ".join([ln for ln in lines if "hb " in ln][:2]))

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
    lua_rslabs(rt, slabs_of(eight + ids[:64]))
    rt.execute("SET_G11(17)")
    rt.execute("SET_G12(%d)" % len(eight + ids[:64]))
    load(rt)
    pump(rt, 1)
    lines = lines_of(rt)

    check("g11: the menu context arms the reader",
          has_line(lines, "armed v1.3 in the menu") and has_line(lines, "g11 armed (scope locksmith, 4203 ids)"),
          " | ".join(lines[:6]))
    check("g11: both ownership doors are wrapped",
          has_line(lines, "g11 isunlockedwithid wrapped (2 of 2: PROGRESSION, LOOT)"), " | ".join(lines[:8]))
    want = "g11 rebuilt from serial 17 types=attachment,camo,reticle"
    check("g11: the rebuild line names the serial and the type route it will use",
          has_line(lines, want), " | ".join(lines[:10]))
    check("g11: the arm line comes before the rebuild line",
          [i for i, ln in enumerate(lines) if ln.startswith("progression_tuning: g11 armed")][0]
          < [i for i, ln in enumerate(lines) if "rebuilt from serial" in ln][0])
    check("g11: the rebuild keeps no lock count of its own - the dll's own log carries it",
          rt.eval("G11('locks')") is None and rt.eval("G11('inScope')") is None,
          "%s / %s" % (rt.eval("G11('locks')"), rt.eval("G11('inScope')")))
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
    pump(rt, 8)
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
    pump(rt, 8)
    check("g11: an absent scope dvar changes nothing", rt.eval("ASK_P(2)") is True)
    check("g11: going back to locksmith prints nothing and leaves the door on the client's type",
          count_line(lines_of(rt), "g11 scope locksmith") == 0
          and rt.eval("ASK_P(2)") is True,
          " | ".join([ln for ln in lines_of(rt) if "scope" in ln]))
    check("g11: the acceptance ids are still locked after the scope went back",
          all(rt.eval("ASK_P(%d)" % i) is False for i in eight))

    rt.execute('SET_DVAR("zm_unlock_all", "1")')
    pump(rt, 8)
    check("g11: zm_unlock_all stands every lock this file adds down",
          all(rt.eval("ASK_P(%d)" % i) is True and rt.eval("ASK_L(%d)" % i) is True for i in eight))
    check("g11: the stand-down is logged once, naming the toggle",
          count_line(lines_of(rt),
                     "g11 debug unlock zm_unlock_all is on - every lock this file adds is stepped aside") == 1,
          " | ".join([ln for ln in lines_of(rt) if "debug unlock" in ln]))
    rt.execute('SET_DVAR("zm_unlock_all", "0")')
    pump(rt, 8)
    check("g11: '0' is not on, so the locks come back", all(rt.eval("ASK_P(%d)" % i) is False for i in eight))
    rt.execute('SET_DVAR("zm_unlock_attachments", "2")')
    pump(rt, 8)
    check("g11: the client's own rule - any non-zero value is on",
          all(rt.eval("ASK_P(%d)" % i) is True for i in eight))
    rt.execute('SET_DVAR("zm_unlock_attachments", "")')
    pump(rt, 8)
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
    lua_rslabs(rt, slabs_of(lit))
    rt.execute("SET_G11(5)")
    rt.execute("SET_G12(%d)" % len(lit))
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
    check("g11 payload: a changed bitmap is rebuilt once, on the new serial",
          str(rt.eval("G11('ver')")) == "7:33:65536"
          and int(rt.eval("G11('skips')")) == 1,
          "%s skips=%s" % (rt.eval("G11('ver')"), rt.eval("G11('skips')")))
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
    pump(rt, 8)
    check("g11 payload: a header that is not <serial>:33:65536 is refused",
          (rt.eval("ASK_P(%d)" % ACCEPT[3]) is False)
          and has_line(lines_of(rt), "g11 header bad is not <serial>:33:65536 - refused, keeping the previous payload"))

    rt.execute('SET_VER("9:32:65536")')
    pump(rt, 8)
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
          rt.eval("G11('hex')") is None and rt.eval("G11('serial')") is None
          and rt.eval("G11('locks')") is None)
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
    check("g11 order: the wait is announced, then the cap once",
          count_line(l3, "g11 waiting for PROGRESSION / LOOT") >= 1
          and count_line(l3, "card table ") == 0
          and count_line(l3, "g11 gave up wrapping - PROGRESSION / LOOT") == 1, " | ".join(l3))
    check("g11 order: the main timer and the armory watch both keep running after the cap",
          int(rt2.eval("QUEUED()")) == 2, str(rt2.eval("QUEUED()")))
    check("g11 order: giving up leaves nothing wrapped",
          int(rt2.eval("G11('wrappers')")) == 0, str(rt2.eval("G11('wrappers')")))

    rt3 = lua51(unpack_returned_tuples=True)
    rt3.execute(PRELUDE)
    rt3.execute("FRONTEND = true")
    rt3.execute(FIXTURE)
    lua_slabs(rt3, slabs)
    lua_rslabs(rt3, slabs)
    rt3.execute("SET_G11(4)")
    rt3.execute("SET_G12(%d)" % len(lit))
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
    camo_r = [131546]
    attach = [126608, 140701]
    plain = [(150003, 2), (200000, 11)]
    nobit = [150010, 150011]
    lit = inscope + outside + camo + camo_r + attach + [i for i, _t in plain]
    rewards = inscope + outside + camo_r + attach
    slabs = slabs_of(lit)

    rt = new_rt(lua51, frontend=True, src=False)
    lua_slabs(rt, slabs)
    lua_rslabs(rt, slabs_of(rewards))
    rt.execute("SET_TYPE(150003, 2)")
    rt.execute("SET_TYPE(200000, 11)")
    for i in camo + camo_r:
        rt.execute("SET_TYPE(%d, 13)" % i)
    rt.execute("SET_G11(31)")
    rt.execute("SET_G12(%d)" % len(rewards))
    load(rt)
    pump(rt, 1)
    lines = lines_of(rt)

    check("s1: the rebuild line names the type route the door will use",
          has_line(lines, "g11 rebuilt from serial 31 types=attachment,camo,reticle"),
          " | ".join([ln for ln in lines if "rebuilt" in ln]))

    check("s1: an attachment id in the shipped scope reads locked on both doors",
          all(rt.eval("ASK_P(%d)" % i) is False and rt.eval("ASK_L(%d)" % i) is False for i in inscope))
    check("s1: an attachment id with a bit but OUTSIDE the scope reads locked - the S1 win",
          all(rt.eval("ASK_L(%d)" % i) is False for i in outside),
          str([rt.eval("ASK_L(%d)" % i) for i in outside]))
    check("s1: a camo id with a bit and no reward reads open on both doors",
          all(rt.eval("ASK_P(%d)" % i) is True and rt.eval("ASK_L(%d)" % i) is True for i in camo),
          str([(i, rt.eval("ASK_L(%d)" % i)) for i in camo]))
    check("s1: a camo the challenge set pays reads locked on both doors",
          all(rt.eval("ASK_P(%d)" % i) is False and rt.eval("ASK_L(%d)" % i) is False for i in camo_r),
          str([(i, rt.eval("ASK_L(%d)" % i)) for i in camo_r]))
    check("s1: an attachment with a bit still reads locked, as RC 1.0 answered",
          all(rt.eval("ASK_P(%d)" % i) is False and rt.eval("ASK_L(%d)" % i) is False for i in attach))
    check("s1: a weapon id with a bit keeps the client's own answer",
          rt.eval("ASK_P(%d)" % plain[0][0]) is True and rt.eval("ASK_L(%d)" % plain[0][0]) is True,
          str(rt.eval("ASK_L(%d)" % plain[0][0])))
    check("s1: a calling card with a bit and no paying table reads locked on both doors",
          rt.eval("ASK_P(%d)" % plain[1][0]) is False and rt.eval("ASK_L(%d)" % plain[1][0]) is False,
          str(rt.eval("ASK_L(%d)" % plain[1][0])))
    before = int(rt.eval("LCALLS"))
    rt.eval("ASK_L(150003)")
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
          has_line(l, "door id=131708 type=13 bit=1 answer=pass"),
          " | ".join([ln for ln in l if "door id=" in ln][:4]))
    check("s1: a weapon id is a door decision too, but the line is for camo ids only",
          not has_line(l, "door id=125186"), " | ".join([ln for ln in l if "door id=" in ln][:8]))
    check("s1: and a camo id with a bit answers once in the log",
          count_line(l, "door id=131708") == 1, str(count_line(l, "door id=131708")))

    rt.execute('SET_TOGGLE("pt_on", 0)')
    pump(rt, 8)
    check("s1: pt_on off makes the door a passthrough on every class",
          all(rt.eval("ASK_L(%d)" % i) is True for i in inscope + outside + camo + attach)
          and all(rt.eval("ASK_P(%d)" % i) is True for i in inscope + camo))
    rt.execute('SET_TOGGLE("pt_on", 1)')
    pump(rt, 8)
    check("s1: and back on again without a reload",
          all(rt.eval("ASK_L(%d)" % i) is False for i in inscope)
          and all(rt.eval("ASK_L(%d)" % i) is True for i in camo))

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


def g12_door(lua51, ls):
    card = [200000, 200001]
    store = [6015]
    dflt = [104846]
    camo = [131708]
    attach = [126608]
    ret = [129198]
    lit = card + store + dflt + camo + attach + ret
    rewards = card + dflt

    rt = new_rt(lua51, frontend=True, src=False)
    lua_slabs(rt, slabs_of(lit))
    lua_rslabs(rt, slabs_of(rewards))
    rt.execute("SET_G11(71)")
    rt.execute("SET_G12(%d)" % len(rewards))
    for i in card + store + dflt:
        rt.execute("SET_TYPE(%d, 11)" % i)
    rt.execute("SET_DEFAULT(%d)" % dflt[0])
    rt.execute("SET_TYPE(%d, 13)" % camo[0])
    rt.execute("SET_TYPE(%d, 7)" % attach[0])
    rt.execute("SET_TYPE(%d, 14)" % ret[0])
    load(rt)
    pump(rt, 1)
    lines = lines_of(rt)

    check("g12: the reader keeps the reward set without printing a line naming it",
          count_line(lines, "g12 rewards") == 0,
          " | ".join([x for x in lines if "g12 " in x][:4]))
    check("g12: and the set it kept is that payload's own",
          int(rt.eval("G11('setn')")) == len(rewards), str(rt.eval("G11('setn')")))

    check("g12: a career card that is a challenge reward reads locked on both doors",
          all(rt.eval("ASK_P(%d)" % i) is False and rt.eval("ASK_L(%d)" % i) is False for i in card),
          str([(i, rt.eval("ASK_L(%d)" % i)) for i in card]))
    check("g12: a store card with a bit and nothing selling it reads locked on both doors",
          rt.eval("ASK_P(%d)" % store[0]) is False and rt.eval("ASK_L(%d)" % store[0]) is False,
          str(rt.eval("ASK_L(%d)" % store[0])))
    check("g12: a reward the game ships by default keeps the client's own answer",
          rt.eval("ASK_P(%d)" % dflt[0]) is True and rt.eval("ASK_L(%d)" % dflt[0]) is True,
          str(rt.eval("ASK_L(%d)" % dflt[0])))
    check("g12: an attachment, a camo and a reticle with a bit and no reward read open",
          all(rt.eval("ASK_L(%d)" % i) is True for i in camo + attach + ret),
          str([(i, rt.eval("ASK_L(%d)" % i)) for i in camo + attach + ret]))
    for i in card + store + dflt:
        rt.eval("ASK_L(%d)" % i)
        rt.eval("ASK_P(%d)" % i)
    check("g12: no reward line is printed, however many times the door is asked",
          count_line(lines_of(rt), "g12 rewards") == 0
          and int(rt.eval("G11('setn')")) == len(rewards),
          str(count_line(lines_of(rt), "g12 rewards")))

    rt2 = new_rt(lua51, frontend=True, src=False)
    lua_slabs(rt2, slabs_of([150900]))
    rt2.execute("SET_G11(72)")
    rt2.execute('SET_PRESTIGE("sat_pi_alcor", 0)')
    rt2.execute('SET_LEVEL("sat_pi_alcor", 2)')
    rt2.execute('SET_CAMODATA(107478, "sat_pi_alcor")')
    rt2.execute("SET_TYPE(107478, 13)")
    rt2.execute(PRESTIGE_CAMO_FN)
    load(rt2)
    pump(rt2, 1)
    check("g12: a camo with no bit below its band is locked with the toggle off",
          rt2.eval("ASK_L(107478)") is False, str(rt2.eval("ASK_L(107478)")))
    rt2.execute('SET_DVAR("zm_unlock_camos", "1")')
    pump(rt2, 1)
    check("g12: and unlock camos steps the band aside, bit or no bit",
          rt2.eval("ASK_L(107478)") is True, str(rt2.eval("ASK_L(107478)")))
    band = count_line(lines_of(rt2), "prestige camo id=107478")
    for _ in range(3):
        rt2.eval("ASK_L(107478)")
    check("g12: with the toggle on the band computes no band at all",
          count_line(lines_of(rt2), "prestige camo id=107478") == band,
          " | ".join([x for x in lines_of(rt2) if "prestige camo" in x][:2]))
    rt2.execute('SET_DVAR("zm_unlock_camos", "0")')
    pump(rt2, 1)
    check("g12: and off again locks it back in the same vm",
          rt2.eval("ASK_L(107478)") is False, str(rt2.eval("ASK_L(107478)")))

    rt3 = new_rt(lua51, frontend=True, src=False)
    lua_slabs(rt3, slabs_of([200000]))
    rt3.execute("SET_G11(73)")
    rt3.execute("SET_TYPE(200000, 12)")
    load(rt3)
    pump(rt3, 1)
    check("g12: with no reward payload a career emblem keeps today's answer",
          rt3.eval("ASK_P(200000)") is True and rt3.eval("ASK_L(200000)") is True,
          str(rt3.eval("ASK_L(200000)")))
    check("g12: and no reward line is printed", not has_line(lines_of(rt3), "g12 rewards"),
          " | ".join([x for x in lines_of(rt3) if "g12" in x][:2]))

    rt4 = new_rt(lua51, frontend=True, src=False)
    lua_slabs(rt4, slabs_of([200000]))
    lua_rslabs(rt4, slabs_of([200000]))
    rt4.execute("SET_G11(74)")
    rt4.execute('SET_RVER("2:33:65536")')
    rt4.execute("SET_TYPE(200000, 12)")
    load(rt4)
    pump(rt4, 4)
    check("g12: the count is the header's own, and the 33 parts latch the set",
          int(rt4.eval("G11('setn')")) == 2 and rt4.eval("ASK_L(200000)") is False,
          "%s / %s" % (rt4.eval("G11('setn')"), rt4.eval("ASK_L(200000)")))
    lua_rslabs(rt4, slabs_of([200000, 200001]))
    pump(rt4, 1)
    ask = rt4.eval("ASK_L(200000)")
    check("g12: a later read of the static set changes nothing",
          int(rt4.eval("G11('setn')")) == 2 and ask is False,
          "%s / %s" % (rt4.eval("G11('setn')"), ask))
    check("g12: and the latch prints nothing while the set stands",
          count_line(lines_of(rt4), "g12 rewards") == 0
          and int(rt4.eval("G11('setn')")) == 2,
          str(count_line(lines_of(rt4), "g12 rewards")))

    rt5 = new_rt(lua51, frontend=True, src=False)
    lua_slabs(rt5, slabs_of([200000]))
    lua_rslabs(rt5, slabs_of([200000]))
    rt5.execute("SET_G11(75)")
    rt5.execute('SET_RVER("g12")')
    rt5.execute("SET_TYPE(200000, 12)")
    load(rt5)
    pump(rt5, 1)
    check("g12: the sentinel header the hook leaves at boot is not a payload",
          rt5.eval("G11('sethex')") is None and rt5.eval("ASK_L(200000)") is True,
          str(rt5.eval("G11('setn')")))


def s1_reticle(lua51, ls):
    ret = [129198, 129199]
    ret_r = [129199]
    dflt = [109901]
    camo = [131708]
    attach = [126608]
    nobit = 129300
    lit = ret + dflt + camo + attach
    slabs = slabs_of(lit)

    def run(pre=""):
        rt = new_rt(lua51, frontend=True, src=False, pre=pre)
        lua_slabs(rt, slabs)
        lua_rslabs(rt, slabs_of(ret_r))
        for i in ret + dflt:
            rt.execute("SET_TYPE(%d, 14)" % i)
        rt.execute("SET_TYPE(%d, 13)" % camo[0])
        rt.execute("SET_TYPE(%d, 7)" % attach[0])
        rt.execute("SET_DEFAULT(%d)" % dflt[0])
        rt.execute("SET_G11(51)")
        rt.execute("SET_G12(%d)" % len(ret_r))
        load(rt)
        pump(rt, 1)
        return rt

    rt = run()
    lines = lines_of(rt)
    check("s1 reticle: the rebuild line names the reticle type beside the two",
          has_line(lines, "types=attachment,camo,reticle"),
          " | ".join([ln for ln in lines if "rebuilt" in ln]))
    check("s1 reticle: a reticle id with a bit and no reward reads open on both doors",
          all(rt.eval("ASK_P(%d)" % i) is True and rt.eval("ASK_L(%d)" % i) is True for i in [ret[0]]),
          str([(i, rt.eval("ASK_L(%d)" % i)) for i in ret]))
    check("s1 reticle: a reticle the challenge set pays reads locked on both doors",
          all(rt.eval("ASK_P(%d)" % i) is False and rt.eval("ASK_L(%d)" % i) is False for i in ret_r),
          str([(i, rt.eval("ASK_L(%d)" % i)) for i in ret_r]))
    check("s1 reticle: a default reticle with a bit keeps the client's own answer",
          all(rt.eval("ASK_P(%d)" % i) is True and rt.eval("ASK_L(%d)" % i) is True for i in dflt),
          str([(i, rt.eval("ASK_L(%d)" % i)) for i in dflt]))
    check("s1 reticle: a reticle with no bit at all reads unchanged on both doors",
          rt.eval("ASK_P(%d)" % nobit) is True and rt.eval("ASK_L(%d)" % nobit) is True,
          str(rt.eval("ASK_L(%d)" % nobit)))
    check("s1 reticle: an attachment and a camo with a bit read open beside it",
          all(rt.eval("ASK_L(%d)" % i) is True for i in camo + attach),
          str([(i, rt.eval("ASK_L(%d)" % i)) for i in camo + attach]))
    lines = lines_of(rt)
    check("s1 reticle: a reticle decision is logged as type 14",
          has_line(lines, "door id=129198 type=14 bit=1 answer=pass")
          and has_line(lines, "door id=129199 type=14 bit=1 answer=locked"),
          " | ".join([ln for ln in lines if "door id=" in ln][:6]))
    check("s1 reticle: and the default reticle is logged as a pass",
          has_line(lines, "door id=109901 type=14 bit=1 answer=pass"),
          " | ".join([ln for ln in lines if "door id=" in ln][:6]))

    rt2 = run("DROP_RETICLE_TYPE()")
    check("s1 reticle: with no RETICLE in itemTypes a paid reticle still closes",
          all(rt2.eval("ASK_P(%d)" % i) is True for i in [ret[0]])
          and all(rt2.eval("ASK_L(%d)" % i) is False for i in ret_r),
          str([(i, rt2.eval("ASK_L(%d)" % i)) for i in ret]))
    check("s1 reticle: and the door is unchanged for an attachment and a camo with a bit",
          all(rt2.eval("ASK_L(%d)" % i) is True for i in camo + attach),
          str([(i, rt2.eval("ASK_L(%d)" % i)) for i in camo + attach]))
    check("s1 reticle: and no reticle line is printed when the type is missing",
          not has_line(lines_of(rt2), "type=14"),
          " | ".join([ln for ln in lines_of(rt2) if "door id=" in ln][:4]))


def s1_fallback(lua51, ls):
    ids = sorted(ls)
    sample = ids[:12] + [150001, 150002, 150010]
    lit = ids[:12] + [150001, 150002]

    def run(pre):
        rt = new_rt(lua51, frontend=True, src=False, pre=pre)
        lua_slabs(rt, slabs_of(lit))
        lua_rslabs(rt, slabs_of(lit))
        rt.execute("SET_G11(41)")
        rt.execute("SET_G12(%d)" % len(lit))
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
        lua_rslabs(rt, slabs_of([150100]))
        rt.execute("SET_G11(51)")
        rt.execute("SET_G12(1)")
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
    check("s3: a bundle already read is cached",
          rt.eval("ASK_L(126608)") is False)
    lua_slabs(rt, slabs_of([150901]))
    rt.execute('SET_VER("52:33:65536")')
    pump(rt, 8)
    pump(rt, 8)
    check("s3: and the rebuild that re-reads the bitmap keeps that bundle answer",
          rt.eval("ASK_L(126608)") is False, str(rt.eval("ASK_L(126608)")))
    rt.execute("rawget(_G, 'ProgressionTuning').g11.bundles = {}")
    rt.execute("rawget(_G, 'ProgressionTuning').g11.rec = {}")
    check("s3: so dropping both caches is what re-reads the bundle",
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
    lua_rslabs(rt, slabs_of([126608]))
    rt.execute("SET_TYPE(20000, 11)")
    rt.execute("SET_G11(9)")
    rt.execute("SET_G12(1)")
    rt.execute("SET_TOGGLE('pt_diag', 1)")
    load(rt)
    lines = lines_of(rt)
    blk = rc1d_lines(lines)

    check("diag: the block opens with one header naming the VM, the switch and the payload",
          has_line(blk, "rc1diag: 1 block vm=menu pt_diag=on:int=1 payload=9 scope=locksmith"),
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
                if "rc1diag:" not in ln and "door id=" not in ln and "lock door:" not in ln
                and "card table " not in ln]
        cards = (int(rt.eval("G11('cardK')") or 0),
                 len([ln for ln in lines_of(rt) if "card table " in ln and "why=" not in ln]))
        return ask, askl, events, kept, touch, cards

    off = run(False)
    on = run(True)
    check("diag: the doors answer identically with it on and off", off[0] == on[0] and off[1] == on[1],
          "%s vs %s" % (off[0][:3], on[0][:3]))
    check("diag: the events are the same, in the same order", off[2] == on[2], "%s vs %s" % (off[2], on[2]))
    check("diag: every other line is identical", off[3] == on[3],
          " | ".join(sorted(set(off[3]) ^ set(on[3]))[:3]))
    check("diag: the same tables load, on or off, and neither run prints a census line",
          off[5] == on[5] and off[5][1] == 0,
          "%s vs %s" % (str(off[5]), str(on[5])))
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


QB_WEEKS = r"""
Challenge[xhash('IsChallengeComplete')] = function(c, id) return id == 60333 or id == 60334 end
ROWS['zmweekly'] = {
  ['60330'] = { id = '60330', ref = 'w1', amount = '3' },
  ['60331'] = { id = '60331', ref = 'w2', amount = '10' },
  ['60332'] = { id = '60332', ref = 'w3', amount = '10' },
  ['60333'] = { id = '60333', ref = 'w4', amount = '10' },
  ['60334'] = { id = '60334', ref = 'w5', amount = '10' } }
SET_OC(60331, 1, 0)
SET_OC(60332, 9, 0)
SET_OC(60333, 5, 0)
SET_OC(60334, 10, 0)
WeeklyChallenge = {}
WeeklyChallenge[xhash('getallweeklychallenges')] = function(c, opts)
  return { { achievementID = 60330, isComplete = false, progress = { default = 52 },
             data = { type = 'weekly' } },
           { achievementID = 60333, isComplete = true, progress = { default = 5 },
             data = { type = 'weekly2' } } }
end
"""

QB_CAMO_ROW = ("(function() local s = rawget(_G, 'ProgressionTuning').camo.rows"
               " for k in pairs(s) do s[k] = nil end"
               " s['probe'] = { id = 107478, th = { 100, 200 }, n = 0 } end)()")


def rb_lines(lines):
    return [ln for ln in lines if "rbdiag:" in ln]


def rb_end(lines):
    for ln in lines:
        m = re.search(r"rbdiag: end \((\d+) lines\)", ln)
        if m:
            return int(m.group(1))
    return None


def rb_rt(lua51, extra="", b=True, d=True, frontend=True, slabs=None, after="", rslabs=None,
          ticks=8):
    rt = new_rt(lua51, frontend=frontend, src=False)
    rt.execute(DIAGFIX)
    if extra:
        rt.execute(extra)
    if slabs:
        lua_slabs(rt, slabs_of(slabs))
        rt.execute("SET_G11(21)")
    if rslabs:
        lua_rslabs(rt, slabs_of(rslabs))
        rt.execute("SET_G12(%d)" % len(rslabs))
    if d:
        rt.execute("SET_TOGGLE('pt_diag', 1)")
    if b:
        rt.execute("SET_TOGGLE('pt_diagb', 1)")
    load(rt)
    if after:
        rt.eval(after)
    pump(rt, ticks)
    return rt


def diag_qb_gate(lua51):
    rt = rb_rt(lua51, b=False)
    check("diag B: the second switch on its own prints nothing - it is off by default",
          not rb_lines(lines_of(rt)), " | ".join(rb_lines(lines_of(rt))[:3]))

    rt.execute("SET_TOGGLE('pt_diagb', 1)")
    pump(rt, 8)
    blk = rb_lines(lines_of(rt))
    check("diag B: the second switch prints one block that names its vm, its ref and its cap",
          count_line(blk, "rbdiag: 1 block") == 1
          and has_line(blk, "rbdiag: 1 block vm=menu ref=sat_pi_alcor cap=40"), " | ".join(blk[:2]))
    check("diag B: it closes with a line that counts its own lines", rb_end(blk) == len(blk),
          "end=%s lines=%d" % (rb_end(blk), len(blk)))
    check("diag B: every line of it carries the prefix",
          all("rbdiag:" in ln for ln in blk) and blk[-1].startswith("progression_tuning: rbdiag"),
          " | ".join(blk[:2]))
    check("diag B: the block is bounded", len(blk) <= 40, str(len(blk)))
    n = len(blk)
    pump(rt, 40)
    check("diag B: it prints once per switch on, not once per tick",
          len(rb_lines(lines_of(rt))) == n, str(n))

    rt.execute("SET_TOGGLE('pt_diag', 0)")
    pump(rt, 8)
    rt.execute("SET_TOGGLE('pt_diagb', 0)")
    pump(rt, 8)
    rt.execute("SET_TOGGLE('pt_diagb', 1)")
    pump(rt, 8)
    check("diag B: the first switch silences it too",
          len(rb_lines(lines_of(rt))) == n, str(len(rb_lines(lines_of(rt)))))


def diag_qb_weeklies(lua51):
    rt = rb_rt(lua51, extra=QB_WEEKS)
    blk = rb_lines(lines_of(rt))
    check("diag B: QB1 - the three weeklies nearest completion, worst first",
          has_line(blk, "QB1 60330 complete=false progress=52/3 status=nil")
          and has_line(blk, "QB1 60332 complete=false progress=9/10 status=nil")
          and has_line(blk, "QB1 60331 complete=false progress=1/10 status=nil"),
          " | ".join([ln for ln in blk if "QB1 " in ln]))
    check("diag B: QB1 - the two the native already calls complete",
          has_line(blk, "QB1 60333 complete=true progress=5/10 status=nil")
          and has_line(blk, "QB1 60334 complete=true progress=10/10 status=nil"),
          " | ".join([ln for ln in blk if "QB1 " in ln]))
    check("diag B: QB2 - the api, its count and one row's own fields",
          has_line(blk, "QB2 api=table n=2")
          and has_line(blk, "QB2 60330 isComplete=false progress=52 type=weekly")
          and has_line(blk, "QB2 60333 isComplete=true progress=5 type=weekly2"),
          " | ".join([ln for ln in blk if "QB2 " in ln]))
    check("diag B: QB3 - the same title tried four ways beside the mod's own answer",
          has_line(blk, "QB3 hash=L:hash_7dc362a78cf1d3d3")
          and has_line(blk, " hex=L:0x7dc362a78cf1d3d3")
          and has_line(blk, "key=L:challenge/jup_ch_weekly_challenge_completed")
          and has_line(blk, "wkhead=L:#x37dc362a78cf1d3d3"),
          " | ".join([ln for ln in blk if "QB3 " in ln]))

    bare = rb_rt(lua51, extra="ROWS['zmweekly'] = {}")
    blk2 = rb_lines(lines_of(bare))
    check("diag B: a vm with no weekly api and no weekly rows still answers both",
          has_line(blk2, "QB2 api=nil n=none") and has_line(blk2, "QB1 done=none")
          and not has_line(blk2, "raised"),
          " | ".join([ln for ln in blk2 if "QB1 " in ln or "QB2 " in ln]))


def diag_qb_kinds(lua51):
    agree = ("Challenge[xhash('getaekindfromid')] = function(id) return { id = 30 } end\n"
             "Challenge[xhash('GetAEKindID')] = function(n) return 30 end")
    rt = rb_rt(lua51, extra=agree)
    blk = rb_lines(lines_of(rt))
    check("diag B: QB4 - the kind a challenge id carries, beside the kind a name resolves",
          has_line(blk, "QB4 id315=table:table(1) reticle=number:30 match=true"),
          " | ".join([ln for ln in blk if "QB4 " in ln]))

    no = ("Challenge[xhash('getaekindfromid')] = function(id) return { id = 31 } end\n"
          "Challenge[xhash('GetAEKindID')] = function(n) return 30 end")
    rt2 = rb_rt(lua51, extra=no)
    blk2 = rb_lines(lines_of(rt2))
    check("diag B: QB4 - and says so when the two disagree",
          has_line(blk2, "reticle=number:30 match=false"),
          " | ".join([ln for ln in blk2 if "QB4 " in ln]))


def diag_qb_owned(lua51):
    extra = ("Loot[xhash('IsOwned')] = function(c, id)"
             " if tonumber(id) == 126605 or tonumber(id) == 131708 then return 1 end return 0 end\n"
             "Loot[xhash('getlootiteminfofromid')] = function(id)"
             " if tonumber(id) == 126605 then return { category = 'attachment', type = 7 } end"
             " return { category = 'camo' } end\n"
             "SET_BUNDLE(126605, { levelUnlock = 7, [xhash('weaponunlock')] = 'sat_pi_alcor' })")
    rt = rb_rt(lua51, extra=extra, slabs=[126605, 101644])
    blk = rb_lines(lines_of(rt))
    check("diag B: QB5 - the payload bit against the client's own answer, id by id",
          has_line(blk, "QB5 n=24 bit1=2 bit0=22 agree=22 diff=2"),
          " | ".join([ln for ln in blk if "QB5 " in ln]))
    check("diag B: QB5 - the two that disagree are named with both answers",
          has_line(blk, "QB5 diff 131708 bit=0 live=1")
          and has_line(blk, "QB5 diff 101644 bit=1 live=0"),
          " | ".join([ln for ln in blk if "QB5 diff" in ln]))
    check("diag B: QB5 - the three anchors are named whether they agree or not",
          has_line(blk, "QB5 anchor 126605 b=1 131708 b=0 101644 b=1"),
          " | ".join([ln for ln in blk if "QB5 anchor" in ln]))
    check("diag B: QB6 - the item's category, its level, its owner and the owner's level",
          has_line(blk, "QB6 126605 cat=attachment type=7 lvl=7 owner=sat_pi_alcor wlevel=2")
          and has_line(blk, "QB6 131708 cat=camo type=nil lvl=nil owner=nil wlevel=nil"),
          " | ".join([ln for ln in blk if "QB6 " in ln]))


def diag_qb_ladder(lua51):
    extra = ("RBB = { [string.char(0xdf,0xff,0x4b,0x65,0x53,0x4a,0x6f,0x7c)] = 1800 }\n"
             "PRESTIGE[string.char(0xcb,0x1c,0x9c,0x67,0xe8,0xd0,0xa4,0xe1)] ="
             " function(c) return 1800 end\n"
             "PROGRESSION[xhash('getactiveweaponranktablebundle')] = function(c) return RBB end\n"
             "PROGRESSION[xhash('getactiveweaponranktableranklist')] = function(c)"
             " return { { rank = 0 }, { rank = 1 }, { rank = 2 } } end")
    rt = rb_rt(lua51, extra=extra)
    blk = rb_lines(lines_of(rt))
    q8 = [ln for ln in blk if "QB8 " in ln]
    check("diag B: QB8 - the prestige getter answers twice and the bundle field is read",
          len(q8) == 1 and q8[0].count("1800") == 3 and has_line(q8, "bundleType=number"),
          " | ".join(q8))
    check("diag B: QB9 - the rank list's length beside the level ceiling",
          has_line(blk, "QB9 ref=sat_pi_alcor ranks=3 max=55"),
          " | ".join([ln for ln in blk if "QB9 " in ln]))


def diag_qb_sources(lua51):
    rt = rb_rt(lua51, extra="SET_REWARD('sat_pi_alcor', { [1] = { 126605 } })\n"
                           "Challenge[xhash('GetAmount')] = function(id, k, c)"
                           " if k == 398 then return 81 end return 100 end",
                after=QB_CAMO_ROW)
    blk = rb_lines(lines_of(rt))
    check("diag B: QB10 - the reward list is the source the card would use",
          has_line(blk, "QB10 ref=sat_pi_alcor lvl=1 reward=1 rewardData=0 weapon=0 csv=0 "
                        "src=reward splash=nil"),
          " | ".join([ln for ln in blk if "QB10 " in ln]))
    check("diag B: QB11 - the row's own amount for the kind and for our target, both raw",
          has_line(blk, "QB11 id=107478 k398=81 k400=100 our=100"),
          " | ".join([ln for ln in blk if "QB11 " in ln]))

    rt2 = rb_rt(lua51, extra="SET_WD('sat_pi_alcor', { 2200, 3400 }, { { 126605 } })")
    check("diag B: QB10 - with no reward list the weapon data answers instead",
          has_line(rb_lines(lines_of(rt2)), "reward=0 rewardData=0 weapon=1 csv=0 src=weapon"),
          " | ".join([ln for ln in rb_lines(lines_of(rt2)) if "QB10 " in ln]))

    rt3 = rb_rt(lua51, extra="CELL('wp', 'weaponRef', 'sat_pi_alcor', 'loot', '126605|130000')")
    blk3 = rb_lines(lines_of(rt3))
    check("diag B: QB10 - and the csv cell is the last of the three",
          has_line(blk3, "reward=0 rewardData=0 weapon=0 csv=1 src=csv"),
          " | ".join([ln for ln in blk3 if "QB10 " in ln]))
    check("diag B: QB11 - a vm with no camo row says so instead of printing nothing",
          has_line(blk3, "QB11 row=none"), " | ".join([ln for ln in blk3 if "QB11 " in ln]))


def diag_qb_dvar(lua51):
    rt = rb_rt(lua51, extra="SET_DVAR('lui_weekly_challenge_menu_enabled', '1')"
                            " SET_DVAR('lui_use_gl_splash', '1')")
    blk = rb_lines(lines_of(rt))
    check("diag B: QB12 - the weekly switch and its control read by the api's own dvar read",
          has_line(blk, "QB12 bool=nil wk=1 ctl=1"),
          " | ".join([ln for ln in blk if "QB12 " in ln]))

    rt2 = rb_rt(lua51, extra="Dvar[xhash('GetDvarBool')] = function(k) return true end"
                             " SET_DVAR('lui_weekly_challenge_menu_enabled', '1')")
    blk2 = rb_lines(lines_of(rt2))
    check("diag B: QB12 - and the bool getter is named by type when the vm carries one",
          has_line(blk2, "QB12 bool=function wk=1 ctl="),
          " | ".join([ln for ln in blk2 if "QB12 " in ln]))


QB_KINDS = r"""
Challenge[xhash('GetAEKindID')] = function(n)
  if n == 'ae_kind_reticle' or n == xhash('ae_kind_reticle') then return 422 end
  if n == 'ae_kind_reticle_cer' or n == xhash('ae_kind_reticle_cer') then return 315 end
  return nil
end
Challenge[xhash('shouldshowcompletionsplash')] = function(o) return tonumber(o.kind) == 422 end
Challenge[xhash('GetFileTableByType')] = function(kind, id)
  if tonumber(kind) == 422 then return { aeID = tonumber(id) } end
  return nil
end
"""


def diag_qb_reticle(lua51):
    rt = rb_rt(lua51, extra=QB_KINDS)
    blk = rb_lines(lines_of(rt))
    check("diag B: QB13 - both reticle kinds by plain name and by hashed key, both splash answers,"
          " both table answers by type",
          has_line(blk, "QB13 aek=422/422 cer=315/315 show422=true show315=false"
                        " tbl422=table tbl315=nil"),
          " | ".join([ln for ln in blk if "QB13 " in ln]))

    bare = rb_rt(lua51)
    blk2 = rb_lines(lines_of(bare))
    check("diag B: QB13 - a vm with none of the three natives answers absent, and raises nothing",
          has_line(blk2, "QB13 aek=absent/absent cer=absent/absent show422=absent show315=absent"
                         " tbl422=absent tbl315=absent")
          and not has_line(blk2, "raised"),
          " | ".join([ln for ln in blk2 if "QB13 " in ln or "raised" in ln]))


QB_STICKER = r"""
LOOT[xhash('IsUnlocked')] = function(c, x, ref)
  if ref == 'sat_ui_playercard_173' then return true end
  return false
end
LOOT[xhash('isunlockedwithid')] = function(c, id)
  if tonumber(id) == 109917 or tonumber(id) == 104916 then return true end
  return false
end
LOOT[xhash('isitemdefault')] = function(id) return tonumber(id) == 109917 end
Challenge[xhash('shouldshowcompletionsplash')] = function(o) return tonumber(o.kind) == 429 end
Challenge[xhash('getstickerbookchallengedata')] = function(c, id)
  if tonumber(id) == 52508 then return { categoryNum = 1 } end
  return nil
end
OnlineChallenges[xhash('getchallengesprogressforkind')] = function(c, kind)
  if tonumber(kind) == 429 then return { ['52508'] = { status = 3 } } end
  return {}
end
SET_TYPE(92066, 11)
SET_TYPE(109917, 14)
SET_TYPE(104846, 11)
SET_TYPE(6015, 11)
"""


def diag_qb_rewards(lua51):
    rt = rb_rt(lua51, extra=QB_STICKER, slabs=[92066, 104846, 109917], rslabs=[92066, 104916])
    blk = rb_lines(lines_of(rt))
    check("diag B: QB14 - the rewards set, its count and the one id both payloads carry",
          has_line(blk, "QB14 g12 set=1 n=2 r92066=1 l92066=1"),
          " | ".join([ln for ln in blk if "QB14 " in ln]))
    check("diag B: QB15 - three calling cards, each asked with a ref and with an id, beside both bits",
          has_line(blk, "QB15 card3=false card2=false lock=1 reward=0")
          and has_line(blk, "QB15 dark3=true dark2=true lock=0 reward=1")
          and has_line(blk, "QB15 store3=false store2=false lock=0 reward=0"),
          " | ".join([ln for ln in blk if "QB15 " in ln]))
    check("diag B: QB16 - the operator skin's own answer, both bits and its item type",
          has_line(blk, "QB16 skin=false lock=1 reward=1 type=11"),
          " | ".join([ln for ln in blk if "QB16 " in ln]))
    check("diag B: QB17 - the sticker book splash answer, its data, its fork count and its status",
          has_line(blk, "QB17 show429=true sticker=table(1) fork429=1 st=3"),
          " | ".join([ln for ln in blk if "QB17 " in ln]))
    check("diag B: QB18 - the default reticle's answer, both bits and the default guard",
          has_line(blk, "QB18 ret=true lock=1 reward=0 default=true"),
          " | ".join([ln for ln in blk if "QB18 " in ln]))
    check("diag B: the block still closes inside its cap", len(blk) <= 40, str(len(blk)))

    bare = rb_rt(lua51)
    blk2 = rb_lines(lines_of(bare))
    check("diag B: QB14 - a vm with no rewards payload says so",
          has_line(blk2, "QB14 g12 set=0 n=nil r92066=0 l92066=0"),
          " | ".join([ln for ln in blk2 if "QB14 " in ln]))
    check("diag B: QB15 - a vm with no three argument reader answers absent and raises nothing",
          has_line(blk2, "QB15 card3=absent card2=true lock=0 reward=0")
          and has_line(blk2, "QB15 dark3=absent dark2=true lock=0 reward=0")
          and has_line(blk2, "QB15 store3=absent store2=true lock=0 reward=0"),
          " | ".join([ln for ln in blk2 if "QB15 " in ln]))
    check("diag B: QB17 - a vm with none of the sticker book natives answers absent",
          has_line(blk2, "QB17 show429=absent sticker=absent fork429=none st=nil"),
          " | ".join([ln for ln in blk2 if "QB17 " in ln]))
    check("diag B: QB16 and QB18 - a vm with no rewards set still answers both",
          has_line(blk2, "QB16 skin=true lock=0 reward=0 type=7")
          and has_line(blk2, "QB18 ret=true lock=0 reward=0 default=false")
          and not has_line(blk2, "raised"),
          " | ".join([ln for ln in blk2 if "QB16 " in ln or "QB18 " in ln or "raised" in ln]))


CARD_ROWS = r"""
CSV.callingCardPrestigeChallenges = { file = "ccprestige",
  cols = { id = 0, loot = 6, prestige = 14 } }
CSV.reticleChallenges = { file = "ret", cols = { id = 0, loot = 5 },
  [xhash("GetFile")] = function(t) return "ret" end }
CSV.seasonalChallenges = { file = "seas", cols = { id = 0, loot = 6 } }
CSV.gunsmithChallenges = { file = "gs", cols = { id = 0, loot = 5 } }
ROWS["ccprestige"] = { ["3"] = { id = "80001", prestige = "1" } }
ROWS["ret"] = { ["1"] = { loot = "117486" },
                ["2"] = { loot = "200010|200011+200012" } }
ROWS["seas"] = { ["3"] = { loot = "||200020" } }
ROWS["gs"] = { ["4"] = { loot = "112409" }, ["5"] = { loot = "126988" } }
"""

CARD_ROWS_RAISE = r"""
GETFILECALLS = 0
CSV.callingCardPrestigeChallenges = { file = "ccprestige",
  cols = { id = 0, loot = 6, prestige = 14 } }
CSV.reticleChallenges = { file = "ret", cols = { id = 0, loot = 5 },
  [xhash("GetFile")] = function(t) GETFILECALLS = GETFILECALLS + 1; error("no file", 0) end }
CSV.seasonalChallenges = { file = "seas", cols = { id = 0, loot = 6 } }
CSV.gunsmithChallenges = { file = "gs", cols = { id = 0, loot = 5 } }
ROWS["ccprestige"] = { ["3"] = { id = "80001", prestige = "1" } }
ROWS["ret"] = { ["1"] = { loot = "117486" } }
ROWS["seas"] = { ["3"] = { loot = "200020" } }
ROWS["gs"] = { ["4"] = { loot = "112409" } }
"""

CARD_ROWS_PATH = r"""
COLCOLS["ae/sat_ae_autogen_reticle_challenges.csv"] = { id = 0, loot = 5 }
CSV.callingCardPrestigeChallenges = { file = "ccprestige",
  cols = { id = 0, loot = 6, prestige = 14 } }
CSV.seasonalChallenges = { file = "seas", cols = { id = 0, loot = 6 } }
CSV.gunsmithChallenges = { file = "gs", cols = { id = 0, loot = 5 } }
ROWS["ccprestige"] = { ["3"] = { id = "80001", prestige = "1" } }
ROWS["ae/sat_ae_autogen_reticle_challenges.csv"] = { ["1"] = { loot = "117486" } }
ROWS["seas"] = { ["3"] = { loot = "200020" } }
ROWS["gs"] = { ["4"] = { loot = "112409" } }
"""

CARD_ROWS_MISS = r"""
GSREFUSE = 3
local colmiss = StringTable[xhash("tablelookupentirecolumnbynum")]
StringTable[xhash("tablelookupentirecolumnbynum")] = function(file, n)
  if tostring(file) == "gs" and GSREFUSE > 0 then
    GSREFUSE = GSREFUSE - 1
    error("gs not ready", 0)
  end
  return colmiss(file, n)
end
CSV.callingCardPrestigeChallenges = { file = "ccprestige",
  cols = { id = 0, loot = 6, prestige = 14 } }
CSV.reticleChallenges = { file = "ret", cols = { id = 0, loot = 5 } }
CSV.seasonalChallenges = { file = "seas", cols = { id = 0, loot = 6 } }
CSV.gunsmithChallenges = { file = "gs", cols = { id = 0, loot = 5 } }
ROWS["ccprestige"] = { ["3"] = { id = "80001", prestige = "1" } }
ROWS["ret"] = { ["1"] = { loot = "117486" } }
ROWS["seas"] = { ["3"] = { loot = "200020" } }
ROWS["gs"] = { ["4"] = { loot = "112409" }, ["5"] = { loot = "126988" } }
"""

CARD_TYPES = r"""
SET_TYPE(117486, 11)
SET_TYPE(126988, 11)
SET_TYPE(112409, 11)
SET_TYPE(104861, 11)
SET_TYPE(6015, 11)
SET_TYPE(200011, 11)
SET_TYPE(200012, 11)
SET_TYPE(200020, 11)
"""

PRESTIGE_SETS = r"""
CS = {}
CSCALLS = 0
function SET_CS(id, st) CS[tostring(id)] = st end
function DROP_CS() OnlineChallenges[xhash("getchallengestate")] = nil end
function ADD_CS()
  OnlineChallenges[xhash("getchallengestate")] = function(c, id)
    CSCALLS = CSCALLS + 1
    return CS[tostring(id)]
  end
end
ADD_CS()
function ASK_CS(id) return OnlineChallenges[xhash("getchallengestate")](0, id) end
PPLAYER = 0
PPCALLS = 0
function SET_PPLAYER(n) PPLAYER = n end
function DROP_PPLAYER() PRESTIGE[xhash("getplayerprestigelevel")] = nil end
PRESTIGE[xhash("getplayerprestigelevel")] = function(c) PPCALLS = PPCALLS + 1; return PPLAYER end
CSV.callingCardPrestigeChallenges = { file = "ccprestige",
  cols = { id = 0, loot = 6, prestige = 14 } }
ROWS["ccprestige"] = {
  ["1"] = { id = "80001", loot = "200020", prestige = "1" },
  ["2"] = { id = "80002", loot = "200021", prestige = "3" },
  ["3"] = { id = "80003", loot = "200022", prestige = "5" } }
"""

QB20_ROWS = r"""
CallingCardUtils = {}
CallingCardUtils[xhash('getstickerbookchallengesdata')] = function(c, mode)
  if mode == 3 then
    return { { categoryType = 'cat_wc_total', progress = 0.25,
      subChallenges = {
        { id = 70001, loot = '117486|70002', amounts = '20|30' },
        { id = 70003, loot = '|70004', amounts = '|5' },
        { id = 70005, loot = '6015', amounts = '9' } } } }
  end
  if mode == 4 then
    return { { categoryType = 'cat_br_total',
      subChallenges = { { id = 70010, loot = '126988', amounts = '4' } } } }
  end
  return { { categoryType = 'cat_zm_total', progress = 1,
    subChallenges = { { id = 70020, loot = '112409', amounts = '3' },
                      { id = 70021, loot = '112409', amounts = '3' } } } }
end
"""

QB20_MANY = r"""
CallingCardUtils = {}
CallingCardUtils[xhash('getstickerbookchallengesdata')] = function(c, mode)
  local out = {}
  for i = 1, 14 do
    out[i] = { id = 70100 + i, loot = '104861', amounts = '2' }
  end
  return { { categoryType = 'cat_many', subChallenges = out } }
end
"""

QB20_CUM = r"""
LOOT[xhash('GetCumulatedProgressNormalized')] = function(row)
  if type(row) ~= 'table' then error('no row', 0) end
  return function(c) return 0.5 end
end
"""


def g32_cards(lua51):
    def door(pre="", slabs=(), n=81, ticks=8, cards=True):
        rt = new_rt(lua51, frontend=True, src=False)
        if pre:
            rt.execute(pre)
        lua_slabs(rt, slabs_of(list(slabs)))
        rt.execute("SET_G11(%d)" % n)
        load(rt)
        pump(rt, ticks)
        if cards:
            rt.eval("LOAD_ALL()")
        return rt

    boot = door(CARD_ROWS + CARD_TYPES + READ_COUNT,
                [117486, 200011, 200012, 200020, 112409, 126988, 104861, 6015],
                n=87, ticks=8, cards=False)
    lb = lines_of(boot)
    check("g32 cards: at boot only the prestige table is read",
          reads(boot, "ccprestige") == 2 and reads(boot, "ret") == 0
          and reads(boot, "seas") == 0 and reads(boot, "gs") == 0,
          "%d / %d / %d / %d" % (reads(boot, "ccprestige"), reads(boot, "ret"),
                                 reads(boot, "seas"), reads(boot, "gs")))
    check("g32 cards: and the boot prints no card table line, its one read left in the state alone",
          count_line(lb, "card table ") == 0
          and boot.eval("G11('cardK')") is None and reads(boot, "ccprestige") == 2,
          " | ".join([x for x in lb if "card table" in x][:3]))
    check("g32 cards: the prestige table is read for its id and prestige columns alone",
          boot.eval("table.concat(COLNUM['ccprestige'], ',')") == "0,14",
          str(boot.eval("table.concat(COLNUM['ccprestige'], ',')")))
    check("g32 cards: a table no one has asked for pays nothing yet",
          boot.eval("G11('gset2')") is None and boot.eval("ASK_L(117486)") is False,
          str(boot.eval("ASK_L(117486)")))

    rt = door(CARD_ROWS + CARD_TYPES + READ_COUNT,
              [117486, 200011, 200012, 200020, 112409, 126988, 104861, 6015])
    lines = lines_of(rt)
    check("g32 cards: each lazy table is read once, on its own loot column",
          [reads(rt, f) for f in ("ret", "seas", "gs")] == [1, 1, 1]
          and [rt.eval("COLNUM['%s'][1]" % f) for f in ("ret", "seas", "gs")] == [5, 6, 5],
          str([rt.eval("COLNUM['%s'][1]" % f) for f in ("ret", "seas", "gs")]))
    check("g32 cards: no card table is ever expanded to its rows",
          [int(rt.eval("(ROWREADS['%s'] or 0)" % f))
           for f in ("ret", "seas", "gs", "ccprestige")] == [0] * 4,
          str([int(rt.eval("(ROWREADS['%s'] or 0)" % f))
               for f in ("ret", "seas", "gs", "ccprestige")]))
    check("g32 cards: the three lazy tables join their ids and print no line",
          count_line(lines, "card table ") == 0
          and rt.eval("G11('cardK')") == 3
          and [reads(rt, f) for f in ("ret", "seas", "gs")] == [1, 1, 1],
          " | ".join([x for x in lines if "card table" in x]))
    check("g32 cards: the ids join one reward set and it counts three tables",
          rt.eval("G11('cardK')") == 3
          and all(rt.eval("G11('gset2')[%d]" % i) is True
                  for i in (117486, 200010, 200011, 200012, 200020, 112409, 126988)),
          str(rt.eval("G11('cardK')")))
    check("g32 cards: a card one of the game tables pays is locked by its bit",
          rt.eval("ASK_L(117486)") is False and rt.eval("ASK_P(117486)") is False,
          str(rt.eval("ASK_L(117486)")))
    check("g32 cards: both halves of a bar split and both halves of a plus split are in the set",
          rt.eval("ASK_L(200011)") is False and rt.eval("ASK_L(200012)") is False,
          "%s / %s" % (rt.eval("ASK_L(200011)"), rt.eval("ASK_L(200012)")))
    check("g32 cards: an empty cell token adds no id and the id beside it does",
          rt.eval("ASK_L(200020)") is False, str(rt.eval("ASK_L(200020)")))
    check("g32 cards: both gunsmith rows lock the same way",
          rt.eval("ASK_L(112409)") is False and rt.eval("ASK_L(126988)") is False,
          "%s / %s" % (rt.eval("ASK_L(112409)"), rt.eval("ASK_L(126988)")))
    check("g32 cards: a beta card no table pays locks by its bit alone",
          rt.eval("ASK_L(104861)") is False, str(rt.eval("ASK_L(104861)")))
    check("g32 cards: a store card with a bit and no bundle locks too",
          rt.eval("ASK_L(6015)") is False, str(rt.eval("ASK_L(6015)")))

    one = door(CARD_ROWS + CARD_TYPES + READ_COUNT, [112409], n=88, cards=False)
    e0 = int(one.eval("G11('epoch')"))
    first = one.eval("LOAD_CARD('gs')")
    e1 = int(one.eval("G11('epoch')"))
    check("g32 cards: one ask loads its own table, joins the ids and bumps the epoch",
          first is True and reads(one, "gs") == 1 and e1 > e0
          and one.eval("G11('gset2')[112409]") is True,
          "%s / %d / %d" % (first, e0, e1))
    again = one.eval("LOAD_CARD('gs')")
    check("g32 cards: and a second ask for it reads nothing and moves nothing",
          again is True and reads(one, "gs") == 1 and int(one.eval("G11('epoch')")) == e1
          and count_line(lines_of(one), "card table ") == 0,
          "%s / %d / %d" % (again, reads(one, "gs"), int(one.eval("G11('epoch')"))))
    check("g32 cards: a key that is no table of ours loads nothing",
          one.eval("LOAD_CARD('master')") is False and reads(one, "ret") == 0,
          str(one.eval("LOAD_CARD('master')")))

    order = door(CARD_ROWS + CARD_TYPES + READ_COUNT, [117486, 200020], n=84, cards=False)
    check("g32 cards: nothing is loaded until an ask, and the count says so",
          order.eval("ProgressionTuning.api.cards()") == (None, 3),
          str(order.eval("ProgressionTuning.api.cards()")))
    check("g32 cards: three asks load the three tables in that order, one epoch each",
          [order.eval("LOAD_CARD('%s')" % k) for k in ("sea", "gs", "ret")] == [True, True, True]
          and order.eval("ProgressionTuning.api.cards()") == (3, 3)
          and int(order.eval("G11('epoch')")) > 0,
          str(order.eval("ProgressionTuning.api.cards()")))
    check("g32 cards: the order the tables load in does not change the set",
          all(order.eval("G11('gset2')[%d]" % i) is True
              for i in (117486, 200010, 200011, 200012, 200020, 112409, 126988))
          and order.eval("ASK_L(200020)") is False,
          str(order.eval("ASK_L(200020)")))
    check("g32 cards: and the prestige table is read once, whatever the asks",
          reads(order, "ccprestige") == 2 and reads(order, "ret") == 1,
          "%d / %d" % (reads(order, "ccprestige"), reads(order, "ret")))

    bare = door(CARD_ROWS + CARD_TYPES, [117486], n=85, cards=False)
    bare.execute("StringTable[xhash('tablelookupentirecolumnbynum')] = nil")
    check("g32 cards: with no column reader an ask answers false and raises nothing",
          bare.eval("LOAD_CARD('ret')") is False and not has_line(lines_of(bare), "raised"),
          str(bare.eval("LOAD_CARD('ret')")))

    other = door(CARD_ROWS + CARD_TYPES, [117486], n=86, cards=False)
    check("g32 cards: a fresh vm starts with no table loaded, whatever the last one did",
          other.eval("G11('cardK')") is None and other.eval("G11('gset2')") is None,
          "%s / %s" % (other.eval("G11('cardK')"), other.eval("G11('gset2')")))
    e2 = int(other.eval("G11('epoch')"))
    other.eval("LOAD_CARD('sea')")
    pump(other, 20)
    check("g32 cards: a quiet tick after a load leaves the epoch where the load left it",
          int(other.eval("G11('epoch')")) > e2
          and int(other.eval("G11('epoch')")) == e2 + 1,
          "%d / %d" % (e2, int(other.eval("G11('epoch')"))))

    rt2 = door(CARD_ROWS + CARD_TYPES, [104861, 6015], n=82)
    check("g32 cards: the same table id with no bit stays open",
          rt2.eval("ASK_L(117486)") is True, str(rt2.eval("ASK_L(117486)")))

    rt3 = door(CARD_TYPES, [117486, 200011], n=83, cards=False)
    check("g32 cards: with no card tables the set is never built and the bit alone closes the card",
          rt3.eval("G11('gset2')") is None and rt3.eval("ASK_L(117486)") is False,
          str(rt3.eval("ASK_L(117486)")))
    check("g32 cards: and no table line is printed", not has_line(lines_of(rt3), "card table"),
          " | ".join([x for x in lines_of(rt3) if "card" in x][:2]))

    rt4 = rb_rt(lua51, extra=CARD_ROWS + CARD_TYPES, after="LOAD_ALL()",
                slabs=[117486, 126988, 112409, 104861, 6015], ticks=16)
    all4 = lines_of(rt4)
    blk = [x for x in all4 if "QB19 " in x]
    check("g32 cards: QB19 - the three cards the game tables pay read locked four ways",
          has_line(blk, "QB19 117486 lock=1 reward=1 type=11 ans=true native=false")
          and has_line(blk, "QB19 126988 lock=1 reward=1 type=11 ans=true native=false")
          and has_line(blk, "QB19 112409 lock=1 reward=1 type=11 ans=true native=false"),
          " | ".join(blk[:3]))
    check("g32 cards: QB19 - the beta card and the store card carry a bit and no bundle",
          has_line(blk, "QB19 104861 lock=1 reward=0 type=11 ans=true native=false")
          and has_line(blk, "QB19 6015 lock=1 reward=0 type=11 ans=true native=false"),
          " | ".join(blk[3:]))
    check("g32 cards: QB19 - one header naming the tables that answered, then the five cards",
          has_line(blk, "QB19 cards=3/3") and count_line(blk, "QB19 ") == 6, str(len(blk)))
    check("g32 cards: QB19 - the header sees all three tables and no table line is printed at all",
          has_line(blk, "QB19 cards=3/3") and count_line(all4, "card table ") == 0,
          " | ".join([x for x in all4 if "card table " in x or "QB19 cards=" in x][-2:]))
    check("g32 cards: QB19 - it is outside the second block and the block still closes",
          count_line(rb_lines(all4), "QB19 ") == 0 and rb_end(rb_lines(all4)) == len(rb_lines(all4)),
          "%d / %s" % (count_line(rb_lines(all4), "QB19 "), rb_end(rb_lines(all4))))
    pump(rt4, 20)
    check("g32 cards: QB19 - and prints once per vm, not once per tick",
          count_line(lines_of(rt4), "QB19 ") == 6, str(count_line(lines_of(rt4), "QB19 ")))

    rt5 = rb_rt(lua51, extra=CARD_ROWS + CARD_TYPES, after="LOAD_ALL()", slabs=[104861],
                ticks=16)
    blk2 = [x for x in lines_of(rt5) if "QB19 " in x]
    check("g32 cards: QB19 - a table id with no bit reads open beside its own reward flag",
          has_line(blk2, "QB19 117486 lock=0 reward=1 type=11 ans=false native=true"),
          " | ".join(blk2[:2]))

    rt6 = rb_rt(lua51, extra=CARD_TYPES, slabs=[117486, 104861, 6015])
    blk3 = lines_of(rt6)
    check("g32 cards: QB19 - with no card tables the five wait for a load that never comes",
          count_line(blk3, "QB19 ") == 0, " | ".join([x for x in blk3 if "QB19 " in x][:3]))

    rt7 = rb_rt(lua51, extra=CARD_ROWS_MISS + CARD_TYPES, after="LOAD_ALL()",
                slabs=[117486, 112409, 126988])
    pump(rt7, 8)
    blk4 = [x for x in lines_of(rt7) if "QB19 " in x]
    check("g32 cards: QB19 - a refused table keeps the five waiting and says why once",
          count_line(blk4, "QB19 ") == 0
          and count_line(lines_of(rt7), "card table gunsmithChallenges why=") == 1,
          " | ".join([x for x in lines_of(rt7) if "why=" in x][:2]))


def g32_qb20(lua51):
    rt = rb_rt(lua51, extra=CARD_ROWS + CARD_TYPES + QB20_ROWS, after="LOAD_ALL()",
               slabs=[117486, 126988, 112409, 104861, 6015])
    lines = lines_of(rt)
    blk = [x for x in lines if "QB20 " in x]
    check("g32 qb20: the co-op tab - children, the numeric first slot and the empty one",
          has_line(blk, "QB20 OB cat_wc_total children=3 firstNum=2 empty=1 bit=2 reward=1 open=0"
                        " num=0 den=3 pct=0 native=0.25 cum=absent"),
          " | ".join(blk[:2]))
    check("g32 qb20: the warzone tab - one child, one bit and no reward",
          has_line(blk, "QB20 BR cat_br_total children=1 firstNum=1 empty=0 bit=1 reward=1 open=0"
                        " num=0 den=1 pct=0 native=none cum=absent"),
          " | ".join([x for x in blk if "QB20 BR cat" in x]))
    check("g32 qb20: the zombies tab - two children the tables pay, both locked",
          has_line(blk, "QB20 ZM cat_zm_total children=2 firstNum=2 empty=0 bit=2 reward=2 open=0"
                        " num=0 den=2 pct=0 native=1 cum=absent"),
          " | ".join([x for x in blk if "QB20 ZM cat" in x]))
    check("g32 qb20: a child names its first loot slot and all four answers",
          has_line(blk, "QB20 OB child 70001 split1=117486 bit=1 reward=1 door=true ans=false")
          and has_line(blk, "QB20 OB child 70005 split1=6015 bit=1 reward=0 door=true ans=false")
          and has_line(blk, "QB20 BR child 70010 split1=126988 bit=1 reward=1 door=true ans=false")
          and has_line(blk, "QB20 ZM child 70020 split1=112409 bit=1 reward=1 door=true ans=false"),
          " | ".join([x for x in blk if " child " in x][:4]))
    check("g32 qb20: an empty first slot adds no bit and no reward",
          has_line(blk, "QB20 OB child 70003 split1= bit=0 reward=0 door=absent ans=absent"),
          " | ".join([x for x in blk if "70003" in x]))
    check("g32 qb20: six children across the three tabs, and the block inside its cap",
          count_line(blk, " child ") == 6 and len(rb_lines(lines)) <= 40,
          "%d / %d" % (count_line(blk, " child "), len(rb_lines(lines))))
    check("g32 qb20: the three tabs print once each and the block closes",
          count_line(blk, "QB20 OB ") == 4 and count_line(blk, "QB20 BR ") == 2
          and count_line(blk, "QB20 ZM ") == 3 and rb_end(rb_lines(lines)) == len(rb_lines(lines)),
          "%d / %d / %d" % (count_line(blk, "QB20 OB "), count_line(blk, "QB20 BR "),
                            count_line(blk, "QB20 ZM ")))
    pump(rt, 20)
    check("g32 qb20: and once per vm, not once per tick",
          count_line(lines_of(rt), "QB20 ") == len(blk), str(count_line(lines_of(rt), "QB20 ")))

    rt2 = rb_rt(lua51, extra=CARD_ROWS + CARD_TYPES + QB20_MANY, after="LOAD_ALL()",
                slabs=[104861])
    blk2 = [x for x in lines_of(rt2) if "QB20 " in x]
    check("g32 qb20: the child lines stop at twelve across the tabs",
          count_line(blk2, " child ") == 12 and not has_line(blk2, "child 70113")
          and not has_line(blk2, "child 70114"),
          " | ".join([x for x in blk2 if " child " in x][-2:]))
    check("g32 qb20: and the tab that spent them still names its own counts",
          has_line(blk2, "QB20 OB cat_many children=14 firstNum=14 empty=0 bit=14 reward=0 open=0"
                         " num=0 den=14 pct=0 native=none cum=absent"),
          " | ".join([x for x in blk2 if "cat_many" in x]))

    rt3 = rb_rt(lua51, extra=CARD_ROWS + CARD_TYPES + QB20_ROWS + QB20_CUM, after="LOAD_ALL()",
                slabs=[104861])
    blk3 = [x for x in lines_of(rt3) if "QB20 " in x]
    check("g32 qb20: the cumulated reader is called with the tab and its answer printed",
          has_line(blk3, "QB20 OB cat_wc_total children=3 firstNum=2 empty=1 bit=0 reward=1 open=2"
                         " num=2 den=3 pct=67 native=0.25 cum=0.5"),
          " | ".join([x for x in blk3 if "cat_wc_total" in x]))

    rt4 = rb_rt(lua51)
    blk4 = [x for x in lines_of(rt4) if "QB20 " in x]
    check("g32 qb20: a vm with no calling card table answers absent on all three tabs",
          count_line(blk4, "QB20 OB absent children=0 firstNum=0 empty=0 bit=0 reward=0 open=0"
                           " num=0 den=0 pct=none native=none cum=absent") == 1
          and count_line(blk4, "QB20 BR absent ") == 1
          and count_line(blk4, "QB20 ZM absent ") == 1 and not has_line(blk4, "raised"),
          " | ".join(blk4[:3]))


def card_vm(lua51, pre, ids, n, ticks=8, cards=True):
    rt = new_rt(lua51, frontend=True, src=False)
    rt.execute(pre)
    lua_slabs(rt, slabs_of(list(ids)))
    rt.execute("SET_G11(%d)" % n)
    load(rt)
    pump(rt, ticks)
    if cards:
        rt.eval("LOAD_ALL()")
    return rt


def g32_card_files(lua51):
    rt = card_vm(lua51, CARD_ROWS_RAISE + CARD_TYPES, [117486, 200020, 112409, 126988], 84)
    lines = lines_of(rt)
    calls = int(rt.eval("GETFILECALLS"))
    check("g32 files: a table that carries its own file keeps it and its getter is never called",
          calls == 0
          and rt.eval("G11('cardK')") == 3,
          "getfile=%d" % calls)
    check("g32 files: the raise behind that getter costs no table",
          rt.eval("G11('cardK')") == 3 and count_line(lines, "card table ") == 0,
          " | ".join([x for x in lines if "card " in x][:5]))
    check("g32 files: the four tables are read and no line names any of them",
          count_line(lines, "card table ") == 0 and count_line(lines, "why=") == 0
          and rt.eval("G11('gset2')[117486]") is True,
          " | ".join([x for x in lines if "card " in x][:5]))


def g32_card_path(lua51):
    path = "ae/sat_ae_autogen_reticle_challenges.csv"
    rt = card_vm(lua51, CARD_ROWS_PATH + CARD_TYPES, [117486, 200020, 112409, 126988], 85)
    lines = lines_of(rt)
    check("g32 path: a table with no handle lands on its own stringtable, and no line names it",
          count_line(lines, "card table ") == 0
          and rt.eval("COLNUM['%s'] ~= nil" % path) is True,
          " | ".join([x for x in lines if "card table" in x][:4]))
    col = rt.eval("COLNUM['%s'][1]" % path)
    check("g32 path: the path read carries that table's own loot column", col == 5, str(col))
    n = rt.eval("#COLNUM['%s']" % path)
    check("g32 path: and that one column is the whole read", n == 1, str(n))
    ans = rt.eval("ASK_L(117486)")
    check("g32 path: the set is whole and that card is locked by its bit",
          rt.eval("G11('cardK')") == 3 and ans is False, str(ans))


def g32_card_miss(lua51):
    rt = card_vm(lua51, CARD_ROWS_MISS + CARD_TYPES + READ_COUNT,
                 [117486, 200020, 112409, 126988], 86, cards=False)
    lines = lines_of(rt)
    check("g32 miss: at boot no table is named and no why is printed",
          count_line(lines, "card table ") == 0 and count_line(lines, "why=") == 0
          and rt.eval("G11('cardK')") is None,
          " | ".join([x for x in lines if "card " in x][:2]))
    check("g32 miss: a refused table answers false and names its error, type and column",
          rt.eval("LOAD_CARD('gs')") is False
          and count_line(lines_of(rt), "card table gunsmithChallenges why=gs not ready"
                                       " file=string col=5") == 1,
          " | ".join([x for x in lines_of(rt) if "why=" in x][:2]))
    check("g32 miss: and it joins nothing",
          rt.eval("G11('cardK')") is None and rt.eval("G11('gset2')") is None,
          "%s / %s" % (rt.eval("G11('cardK')"), rt.eval("G11('gset2')")))
    rt.eval("LOAD_ALL()")
    lines = lines_of(rt)
    check("g32 miss: the other two tables pay while it refuses, and it says why once",
          rt.eval("G11('cardK')") == 2 and rt.eval("ASK_L(117486)") is False
          and count_line(lines, "why=") == 1,
          "%s / %d" % (rt.eval("G11('cardK')"), count_line(lines, "why=")))
    check("g32 miss: and the refused table's ids are in no set",
          rt.eval("G11('gset2')[112409]") is None and rt.eval("G11('gset2')[126988]") is None,
          "%s / %s" % (rt.eval("G11('gset2')[112409]"), rt.eval("G11('gset2')[126988]")))

    e0 = int(rt.eval("G11('epoch')"))
    check("g32 miss: the next ask reads it again and still answers false",
          rt.eval("LOAD_CARD('gs')") is False and reads(rt, "gs") == 3
          and int(rt.eval("G11('epoch')")) == e0,
          "%d / %d" % (reads(rt, "gs"), int(rt.eval("G11('epoch')"))))
    late = rt.eval("LOAD_CARD('gs')")
    check("g32 miss: a table that answers on a later ask joins and moves the epoch",
          late is True and reads(rt, "gs") == 4 and int(rt.eval("G11('epoch')")) > e0
          and rt.eval("G11('gset2')[112409]") is True and rt.eval("ASK_L(126988)") is False,
          "%s / %d / %d" % (late, reads(rt, "gs"), int(rt.eval("G11('epoch')"))))
    check("g32 miss: and the refusal is never said twice",
          count_line(lines_of(rt), "why=") == 1,
          " | ".join([x for x in lines_of(rt) if "why=" in x][:2]))
    check("g32 miss: the two tables that answered are never read a second time",
          [reads(rt, f) for f in ("ret", "seas", "ccprestige")] == [1, 1, 2],
          str([reads(rt, f) for f in ("ret", "seas", "ccprestige")]))
    check("g32 miss: the refused table stays on its handle and never asks its path",
          reads(rt, "gs") == 4 and reads(rt, "ae/sat_gs_challenges.csv") == 0,
          "%d / %d" % (reads(rt, "gs"), reads(rt, "ae/sat_gs_challenges.csv")))


NEW_ROWS = r"""
CSV.callingCardPrestigeChallenges = { file = "ccprestige",
  cols = { id = 0, loot = 6, prestige = 14 } }
CSV.reticleChallenges = { file = "ret", cols = { id = 0, loot = 5 } }
CSV.seasonalChallenges = { file = "seas", cols = { id = 0, loot = 6 } }
CSV.gunsmithChallenges = { file = "gs", cols = { id = 0, loot = 5 } }
ROWS["ccprestige"] = { ["1"] = { id = "80001", prestige = "1" } }
ROWS["ret"] = { ["6"] = { loot = "240001|240002+240003" } }
ROWS["seas"] = { ["7"] = { loot = "240010" } }
ROWS["gs"] = { ["8"] = { loot = "240020+240021" } }
"""

NEW_TYPES = r"""
SET_TYPE(240001, 11)
SET_TYPE(240002, 11)
SET_TYPE(240003, 11)
SET_TYPE(240010, 11)
SET_TYPE(240020, 11)
SET_TYPE(240021, 11)
"""

READ_COUNT = r"""
READCOUNT = {}
ROWREADS = {}
local colrc = StringTable[xhash("tablelookupentirecolumnbynum")]
StringTable[xhash("tablelookupentirecolumnbynum")] = function(file, n)
  local k = tostring(file)
  READCOUNT[k] = (READCOUNT[k] or 0) + 1
  return colrc(file, n)
end
local rowrc = StringTable[xhash("tablereadallrows")]
StringTable[xhash("tablereadallrows")] = function(file, cols)
  local k = tostring(file)
  ROWREADS[k] = (ROWREADS[k] or 0) + 1
  return rowrc(file, cols)
end
"""

RET_FULL = r"""
GETFILECALLS = 0
COLCOLS["ae/sat_ae_autogen_reticle_challenges.csv"] = { id = 0, loot = 5 }
CSV.reticleChallenges = { cols = { id = 0, ref = 1, name = 2, desc = 3, amount = 4, loot = 5,
                                  XPReward = 6, category = 7, order = 8, children = 9,
                                  image = 10, detailDesc = 11, customSplashRef = 12,
                                  featuredLootItem = 13, gameModeMask = 14, itemRef = 15,
                                  feature = 16 },
  [xhash("GetFile")] = function(t) GETFILECALLS = GETFILECALLS + 1; error("no file", 0) end }
CSV.callingCardPrestigeChallenges = { file = "ccprestige",
  cols = { id = 0, loot = 6, prestige = 14 } }
CSV.seasonalChallenges = { file = "seas", cols = { id = 0, loot = 6 } }
CSV.gunsmithChallenges = { file = "gs", cols = { id = 0, loot = 5 } }
ROWS["ccprestige"] = { ["1"] = { id = "80001", prestige = "1" } }
ROWS["ret"] = {}
ROWS["seas"] = {}
ROWS["gs"] = {}
ROWS["ae/sat_ae_autogen_reticle_challenges.csv"] = { ["5"] = { loot = "126988" } }
"""

CARD_ROWS_LONG = r"""
LONGWHY = string.rep("y", 300)
local collw = StringTable[xhash("tablelookupentirecolumnbynum")]
StringTable[xhash("tablelookupentirecolumnbynum")] = function(file, n)
  if tostring(file) == "gs" then error("gs read refused " .. LONGWHY, 0) end
  return collw(file, n)
end
CSV.callingCardPrestigeChallenges = { file = "ccprestige",
  cols = { id = 0, loot = 6, prestige = 14 } }
CSV.reticleChallenges = { file = "ret", cols = { id = 0, loot = 5 } }
CSV.seasonalChallenges = { file = "seas", cols = { id = 0, loot = 6 } }
CSV.gunsmithChallenges = { file = "gs", cols = { id = 0, loot = 5 } }
ROWS["ccprestige"] = { ["1"] = { id = "80001", prestige = "1" } }
ROWS["ret"] = { ["1"] = { loot = "117486" } }
ROWS["seas"] = {}
ROWS["gs"] = { ["8"] = { loot = "240020" } }
"""

FCACHE_COUNT = r"""
RESOLVES = 0
local dvarold = Dvar
Dvar = setmetatable({}, { __index = function(t, k)
  if k == xhash("GetDvarString") then RESOLVES = RESOLVES + 1 end
  return dvarold[k]
end })
"""

G12_READS = r"""
R12 = 0
local get12 = Dvar[xhash("GetDvarString")]
Dvar[xhash("GetDvarString")] = function(key)
  if key == xhashdvar("zm_g12_ver") then R12 = R12 + 1 end
  return get12(key)
end
"""

CAMO_SCAN = r"""
PCAMOCALLS = 0
PRESTIGE[xhash("getmaxweaponprestigelevel")] = function(ref) return 2 end
PRESTIGE[xhash("getweaponprestigecamos")] = function(ref)
  PCAMOCALLS = PCAMOCALLS + 1
  local a = { { startPrestige = 0, startLevel = 0, targetPrestige = 1, targetLevel = 27,
                camoBundle = { lootid = 107478 } } }
  return a, {}, {}
end
WEAPON[xhash("enumerateweapons")] = function(cb) cb({ ref = "sat_pi_alcor" }) end
"""


def reads(rt, f):
    return int(rt.eval("(READCOUNT['%s'] or 0)" % f))


def g32_newtables(lua51):
    rt = card_vm(lua51, NEW_ROWS + NEW_TYPES + READ_COUNT,
                 [240001, 240003, 240010, 240020, 126988], 90)
    lines = lines_of(rt)
    check("w1 tables: each of the three lazy tables loads and joins its own rows, with no line",
          count_line(lines, "card table ") == 0
          and rt.eval("G11('cardK')") == 3
          and rt.eval("G11('gset2')[240010]") is True,
          " | ".join([x for x in lines if "card table " in x][1:]))
    check("w1 tables: the set carries every id of the three tables",
          rt.eval("G11('cardK')") == 3
          and all(rt.eval("G11('gset2')[%d]" % i) is True
                  for i in (240001, 240002, 240003, 240010, 240020, 240021)),
          str(rt.eval("G11('cardK')")))
    check("w1 tables: a bar split and a plus split in a new table both join",
          rt.eval("ASK_L(240001)") is False and rt.eval("ASK_L(240003)") is False,
          "%s / %s" % (rt.eval("ASK_L(240001)"), rt.eval("ASK_L(240003)")))
    check("w1 tables: an id from a new table with no bit stays open",
          rt.eval("ASK_L(240099)") is True, str(rt.eval("ASK_L(240099)")))

    rt2 = card_vm(lua51, RET_FULL + CARD_TYPES, [126988], 91)
    l2 = lines_of(rt2)
    path = "ae/sat_ae_autogen_reticle_challenges.csv"
    check("w1 path: the path read asks that table's own loot column and prints no line",
          count_line(l2, "card table ") == 0
          and rt2.eval("COLNUM['%s'][1]" % path) == 5,
          str(rt2.eval("COLNUM['%s'][1]" % path)))
    check("w1 path: the card it pays joins the set and its table counts as loaded",
          rt2.eval("G11('gset2')[126988]") is True and rt2.eval("G11('cardK')") == 3,
          str(rt2.eval("G11('cardK')")))
    check("w1 path: and its own getter was called once",
          int(rt2.eval("GETFILECALLS")) == 1, str(rt2.eval("GETFILECALLS")))
    check("w1 path: a table with no rows still loads, counts, and adds no id",
          rt2.eval("G11('gset2')[240020]") is None
          and rt2.eval("G11('gset2')[240010]") is None,
          str(rt2.eval("G11('cardK')")))

    rt3 = card_vm(lua51, CARD_ROWS_LONG + CARD_TYPES, [117486], 92)
    why = [x for x in lines_of(rt3) if "card table gunsmithChallenges why=" in x]
    check("w1 why: a refused table prints its whole error, not forty characters",
          len(why) == 1 and "gs read refused yyyyyyyyyy" in why[0]
          and why[0].endswith(" file=string col=5")
          and len(why[0].split("why=")[1].split(" file=")[0]) == 203,
          why[0][-40:] if why else "none")
    pump(rt3, 8)
    rt3.eval("LOAD_ALL()")
    check("w1 why: and it stays one line however often it is asked",
          count_line(lines_of(rt3), "card table gunsmithChallenges why=") == 1,
          str(count_line(lines_of(rt3), "card table gunsmithChallenges why=")))

    rt4 = card_vm(lua51, CARD_ROWS_LONG + CARD_TYPES + READ_COUNT, [117486], 93)
    pump(rt4, 20)
    rt4.eval("LOAD_ALL()")
    pump(rt4, 20)
    check("w1 read: a table that loaded is never read again, a refused one only when asked",
          reads(rt4, "ret") == 1 and reads(rt4, "seas") == 1
          and reads(rt4, "ccprestige") == 2 and reads(rt4, "gs") == 2,
          "%d / %d / %d / %d" % (reads(rt4, "ret"), reads(rt4, "seas"),
                                 reads(rt4, "ccprestige"), reads(rt4, "gs")))


def g32_speed(lua51):
    rt = new_rt(lua51, frontend=True, src=False, pre=FCACHE_COUNT)
    lua_slabs(rt, slabs_of([117486]))
    rt.execute("SET_G11(94)")
    load(rt)
    pump(rt, 1)
    base = int(rt.eval("RESOLVES"))
    for _ in range(3):
        rt.eval("ASK_L(117486)")
    rt.eval("ASK_P(117486)")
    check("w1 cache: the dvar getter is resolved once and never again",
          base <= 2 and int(rt.eval("RESOLVES")) == base,
          "%d -> %d" % (base, int(rt.eval("RESOLVES"))))

    rt2 = new_rt(lua51, frontend=True, src=False, pre=G12_READS)
    lua_slabs(rt2, slabs_of([150901]))
    rt2.execute("SET_G11(95)")
    load(rt2)
    pump(rt2, 1)
    base = int(rt2.eval("R12"))
    for _ in range(3):
        rt2.eval("ASK_L(150901)")
    check("w1 set: an absent reward payload costs at most one read a tick",
          int(rt2.eval("R12")) - base <= 1, "%d reads for three asks" % (int(rt2.eval("R12")) - base))
    pump(rt2, 8)
    after = int(rt2.eval("R12"))
    check("w1 set: and the next poll tries once more",
          after - base == 1, "%d -> %d" % (base, after))

    rt3 = new_rt(lua51, frontend=True, src=False)
    lua_slabs(rt3, slabs_of([150901]))
    rt3.execute("SET_G11(96)")
    load(rt3)
    pump(rt3, 1)
    e0 = int(rt3.eval("G11('epoch')"))
    pump(rt3, 20)
    check("w1 epoch: a quiet tick leaves it alone", int(rt3.eval("G11('epoch')")) == e0,
          "%d -> %d" % (e0, int(rt3.eval("G11('epoch')"))))
    lua_slabs(rt3, slabs_of([150902]))
    rt3.execute('SET_VER("97:33:65536")')
    pump(rt3, 8)
    e1 = int(rt3.eval("G11('epoch')"))
    check("w1 epoch: a serial change bumps it", e1 > e0, "%d -> %d" % (e0, e1))
    rt3.execute('SET_DVAR("zm_unlock_all", "1")')
    pump(rt3, 8)
    e2 = int(rt3.eval("G11('epoch')"))
    check("w1 epoch: an unlock change bumps it", e2 > e1, "%d -> %d" % (e1, e2))
    rt3.execute('SET_DVAR("zm_unlock_all", "0")')
    pump(rt3, 8)
    check("w1 epoch: and the switch going back bumps it again",
          int(rt3.eval("G11('epoch')")) > e2, "%d -> %d" % (e2, int(rt3.eval("G11('epoch')"))))

    rt4 = new_rt(lua51, frontend=True, src=False)
    lua_slabs(rt4, slabs_of([150901]))
    lua_rslabs(rt4, slabs_of([200000, 200001]))
    rt4.execute("SET_G11(98)")
    load(rt4)
    pump(rt4, 1)
    e3 = int(rt4.eval("G11('epoch')"))
    rt4.execute("SET_G12(2)")
    pump(rt4, 8)
    check("w1 epoch: the reward set load bumps it",
          int(rt4.eval("G11('epoch')")) > e3 and rt4.eval("G11('sethex')") is not None,
          "%d -> %d" % (e3, int(rt4.eval("G11('epoch')"))))

    rt5 = new_rt(lua51, frontend=True, src=False)
    rt5.execute(CAMO_SCAN)
    lua_slabs(rt5, slabs_of([150901]))
    rt5.execute("SET_G11(99)")
    rt5.execute('SET_PRESTIGE("sat_pi_alcor", 0)')
    rt5.execute('SET_LEVEL("sat_pi_alcor", 2)')
    rt5.execute("SET_CAMODATA(107478, nil)")
    rt5.execute("SET_TYPE(107478, 13)")
    load(rt5)
    pump(rt5, 1)
    rt5.eval("ASK_L(107478)")
    n0 = int(rt5.eval("PCAMOCALLS"))
    check("w1 cache: the weapon camo map is built and kept",
          n0 >= 1 and rt5.eval("G11('camomap')") is not None, str(n0))
    lua_slabs(rt5, slabs_of([150902]))
    rt5.execute('SET_VER("100:33:65536")')
    pump(rt5, 8)
    rt5.eval("ASK_L(107478)")
    check("w1 cache: and a serial change does not rebuild it",
          int(rt5.eval("PCAMOCALLS")) == n0, "%d -> %d" % (n0, int(rt5.eval("PCAMOCALLS"))))

    rt6 = new_rt(lua51, frontend=True, src=False)
    rt6.execute(r"""
PCAMOEMPTY = 0
PRESTIGE[xhash("getmaxweaponprestigelevel")] = function(ref) return 2 end
PRESTIGE[xhash("getweaponprestigecamos")] = function(ref)
  PCAMOEMPTY = PCAMOEMPTY + 1
  return {}, {}, {}
end
WEAPON[xhash("enumerateweapons")] = function(cb) cb({ ref = "sat_sh_shepherd" }) end
""")
    lua_slabs(rt6, slabs_of([150901]))
    rt6.execute("SET_G11(124)")
    rt6.execute('SET_PRESTIGE("sat_sh_shepherd", 0)')
    rt6.execute('SET_LEVEL("sat_sh_shepherd", 2)')
    rt6.execute("SET_CAMODATA(107480, 'sat_sh_shepherd')")
    rt6.execute("SET_TYPE(107480, 13)")
    load(rt6)
    pump(rt6, 1)
    c0 = int(rt6.eval("PCAMOEMPTY"))
    rt6.eval("ASK_L(107480)")
    rt6.eval("ASK_L(107480)")
    check("w1 cache: a weapon with no prestige camos has its ladder read once",
          int(rt6.eval("PCAMOEMPTY")) - c0 == 1, str(int(rt6.eval("PCAMOEMPTY")) - c0))


def g32_open(lua51):
    rt = card_vm(lua51, CARD_ROWS + CARD_TYPES + BUY_FIX + "SET_BUY(104861, { lootid = 104861 })",
                 [117486, 104861], 87)
    rt.execute("OWNED = false")
    ans = rt.eval("ASK_L(104861)")
    check("g32 open: with no open rule the door's decline is the original's answer",
          ans is False, str(ans))
    before = int(rt.eval("LCALLS"))
    rt.execute("ProgressionTuning.locks.open = function(id) return true end")
    ans, calls = rt.eval("ASK_L(104861)"), int(rt.eval("LCALLS")) - before
    check("g32 open: an open answer reads unlocked and the original is never called",
          ans is True and calls == 0, "%s / %d" % (ans, calls))
    ans = rt.eval("ASK_L(117486)")
    check("g32 open: the lock rule still wins over an open answer", ans is False, str(ans))
    rt.execute("ProgressionTuning.locks.open = function(id) return nil end")
    ans = rt.eval("ASK_L(104861)")
    check("g32 open: no opinion leaves the answer where it was", ans is False, str(ans))
    rt.execute("ProgressionTuning.locks.open = nil")
    before = int(rt.eval("LCALLS"))
    rt.eval("ASK_L(104861)")
    calls = int(rt.eval("LCALLS")) - before
    check("g32 open: an absent open rule costs one original call, as before", calls == 1, str(calls))


STORE_FIX = r"""
STORE = { Bundles = {} }
PLATFORM = true
PLATCALLS = 0
STORE.Bundles[xhash("IsLootUseableOnCurrentPlatform")] = function(c, id)
  PLATCALLS = PLATCALLS + 1
  return PLATFORM
end
function SET_PLATFORM(v) PLATFORM = v end
LOOT.itemTypes.OPERATOR = 1
LOOT.itemTypes.OPERATOR_SKIN = 8
LOOT.itemTypes.OPERATOR_EXECUTION = 9
LOOT.itemTypes.EMBLEM = 12
LOOT.itemTypes.CHARM = 16
LOOT.itemTypes.STICKER = 17
LOOT.itemTypes.SPRAYS = 22
LOOT.itemTypes.LOAD_SCREEN = 36
LOOT.itemTypes.EMOTE = 49
LOOT.itemTypes.PERK = 6
LOOT.itemTypes.EQUIPMENT = 5
LOOT.itemTypes.STREAK = 4
LOOT.itemTypes.SUPER = 3
LOOT.itemTypes.WILDCARD = 45
LOOT.itemTypes.AMMOMOD = 46
"""

STORE_LISTS = ["@cat_camos", "@cat_attachments", "@cat_reticles", "@cat_cards", "@cat_emblems",
               "@cat_operators", "@cat_loadingscreens", "@cat_finishers", "@cat_stickers",
               "@cat_charms", "@cat_sprays", "@cat_emotes"]

BUY_FIX = r"""
if type(STORE) ~= "table" then STORE = {} end
if type(STORE.Bundles) ~= "table" then STORE.Bundles = {} end
BUY, BPASS, BLCK, BMAP = {}, {}, {}, {}
BUYCALLS, BPCALLS, BCCALLS, BMCALLS, DESCCALLS = 0, 0, 0, 0, 0
function SET_BUY(id, b) BUY[tostring(id)] = b end
function SET_BP(id, v) BPASS[tostring(id)] = v end
function SET_BC(id, v) BLCK[tostring(id)] = v end
function SET_BM(id, v) BMAP[tostring(id)] = v end
function SET_BIDX(id, v) BATTLEMAP.LootIdToSectorIndex[tonumber(id)] = v end
STORE.Bundles[xhash("GetFirstBundleWithLootId")] = function(c, id)
  BUYCALLS = BUYCALLS + 1
  return BUY[tostring(id)]
end
LOOT[xhash("GetUnlockDescription")] = function(b)
  DESCCALLS = DESCCALLS + 1
  return "unlocked in the store"
end
PAGEDBATTLEPASS = {}
PAGEDBATTLEPASS[xhash("isbattlepassreward")] = function(id)
  BPCALLS = BPCALLS + 1
  return BPASS[tostring(id)] == true
end
PAGEDBATTLEPASS[xhash("isblackcellreward")] = function(id)
  BCCALLS = BCCALLS + 1
  return BLCK[tostring(id)] == true
end
BATTLEMAP = { LootIdToSectorIndex = {} }
BATTLEMAP[xhash("IsReward")] = function(c, id)
  BMCALLS = BMCALLS + 1
  return BMAP[tostring(id)] == true
end
function BUYCARDS()
  return BUYCALLS + BPCALLS + BCCALLS + BMCALLS + DESCCALLS
end
"""


def g32_store(lua51):
    card, paid, earn = 6015, 117486, 62769
    weapon, perk, plat = 200000, 200001, 200002
    ids = [card, paid, earn, weapon, perk, plat]
    rt = card_vm(lua51, CARD_ROWS + CARD_TYPES + STORE_FIX + BUY_FIX
                 + "SET_BUY(%d, { lootid = %d }) SET_BUY(%d, { lootid = %d })" % (card, card, plat, plat),
                 ids, 88)
    rt.execute("SET_TYPE(%d, 2)" % weapon)
    rt.execute("SET_TYPE(%d, 6)" % perk)
    rt.execute("SET_TYPE(%d, 11)" % earn)
    rt.execute("SET_TYPE(%d, 11)" % plat)
    before = int(rt.eval("LCALLS"))
    ans = rt.eval("ASK_L(%d)" % card)
    calls = int(rt.eval("LCALLS")) - before
    check("g32 store: a store card with a bit and a bundle reads unlocked",
          ans is True and rt.eval("ASK_P(%d)" % card) is True, str(ans))
    check("g32 store: and the client's own function is never asked for it", calls == 0, str(calls))
    check("g32 store: a card one of the game tables pays stays locked",
          rt.eval("ASK_L(%d)" % paid) is False, str(rt.eval("ASK_L(%d)" % paid)))
    before = int(rt.eval("LCALLS"))
    ans = rt.eval("ASK_L(%d)" % earn)
    check("g32 store: a card a level list earns still carries a bit and locks",
          ans is False and int(rt.eval("LCALLS")) - before == 0, str(ans))
    before = int(rt.eval("LCALLS"))
    got = (rt.eval("ASK_L(%d)" % weapon), rt.eval("ASK_L(%d)" % perk))
    check("g32 store: a weapon and a perk are left to the client too",
          got == (True, True) and int(rt.eval("LCALLS")) - before == 2, str(got))
    rt.execute("SET_PLATFORM(false)")
    before = int(rt.eval("LCALLS"))
    ans = rt.eval("ASK_L(%d)" % plat)
    check("g32 store: a platform that refuses the item leaves it to the client",
          ans is True and int(rt.eval("LCALLS")) - before == 1, str(ans))
    rt.execute("SET_PLATFORM(true)")
    before, p0 = int(rt.eval("LCALLS")), int(rt.eval("PLATCALLS"))
    ans = rt.eval("ASK_L(%d)" % plat)
    check("g32 store: and that refusal is kept for the session, with no second question",
          ans is True and int(rt.eval("LCALLS")) - before == 1
          and int(rt.eval("PLATCALLS")) == p0,
          "%s / %d / %d" % (ans, int(rt.eval("LCALLS")) - before, int(rt.eval("PLATCALLS")) - p0))
    pump(rt, 12)
    l = lines_of(rt)
    tally = [x for x in l if "store ids by type:" in x]
    check("g32 store: one line says how many store ids opened, by type",
          len(tally) == 1 and " by type: 11=" in tally[0], " | ".join(tally))
    rt.eval("ASK_L(%d)" % card)
    pump(rt, 12)
    check("g32 store: and it is printed once per vm",
          count_line(lines_of(rt), "store ids by type:") == 1,
          str(count_line(lines_of(rt), "store ids by type:")))

    rt2 = card_vm(lua51, CARD_TYPES + STORE_FIX + BUY_FIX
                  + "SET_BUY(%d, { lootid = %d })" % (card, card), [card], 89)
    before = int(rt2.eval("LCALLS"))
    ans = rt2.eval("ASK_L(%d)" % card)
    check("g32 store: a card opens even while a card table is outstanding",
          ans is True and int(rt2.eval("LCALLS")) - before == 0, str(ans))
    check("g32 store: and the card set is reported short, not whole",
          rt2.eval("G11('cardK')") is None, str(rt2.eval("G11('cardK')")))


def g32_toggle(lua51):
    card, camo, band = 117486, 131708, 107478
    ids = [card, camo, band]
    rt = new_rt(lua51, frontend=True, src=False)
    rt.execute(CARD_ROWS + CARD_TYPES + STORE_FIX)
    lua_slabs(rt, slabs_of(ids))
    lua_rslabs(rt, slabs_of([card, camo]))
    rt.execute("SET_G11(90)")
    rt.execute("SET_G12(2)")
    rt.execute("SET_TYPE(%d, 13)" % camo)
    rt.execute("SET_TYPE(%d, 13)" % band)
    rt.execute('SET_CAMODATA(%d, "sat_pi_alcor")' % band)
    rt.execute('SET_PRESTIGE("sat_pi_alcor", 0)')
    rt.execute('SET_LEVEL("sat_pi_alcor", 0)')
    rt.execute(PRESTIGE_CAMO_FN)
    load(rt)
    pump(rt, 1)
    rt.eval("LOAD_ALL()")
    l = lines_of(rt)
    want = ("unlock dvars: ammomods=- attachments=- camos=- cards=- charms=- emblems=- emotes=-"
            " equipment=- fieldupgrades=- finishers=- loadingscreens=- operators=- perks=- reticles=-"
            " scorestreaks=- sprays=- stickers=- weapons=- wildcards=-")
    check("g32 toggle: the arm line names every unlock switch and what it reads", has_line(l, want),
          " | ".join([x for x in l if "unlock dvars:" in x]))
    check("g32 toggle: a paid card and a paid camo read locked with every switch off",
          rt.eval("ASK_L(%d)" % card) is False and rt.eval("ASK_L(%d)" % camo) is False,
          "%s / %s" % (rt.eval("ASK_L(%d)" % card), rt.eval("ASK_L(%d)" % camo)))
    check("g32 toggle: and the band camo reads locked below its band",
          rt.eval("ASK_L(%d)" % band) is False, str(rt.eval("ASK_L(%d)" % band)))
    rt.execute('SET_DVAR("zm_unlock_cards", "1")')
    pump(rt, 2)
    check("g32 toggle: cards on makes a paid card read unlocked",
          rt.eval("ASK_L(%d)" % card) is True and rt.eval("ASK_P(%d)" % card) is True,
          str(rt.eval("ASK_L(%d)" % card)))
    check("g32 toggle: and the camo beside it stays locked",
          rt.eval("ASK_L(%d)" % camo) is False, str(rt.eval("ASK_L(%d)" % camo)))
    rt.execute('SET_DVAR("zm_unlock_cards", "0")')
    rt.execute('SET_DVAR("zm_unlock_camos", "1")')
    pump(rt, 2)
    check("g32 toggle: camos on makes a paid camo read unlocked",
          rt.eval("ASK_L(%d)" % camo) is True, str(rt.eval("ASK_L(%d)" % camo)))
    check("g32 toggle: and the band camo opens with its band unreached",
          rt.eval("ASK_L(%d)" % band) is True, str(rt.eval("ASK_L(%d)" % band)))
    check("g32 toggle: the card is locked again",
          rt.eval("ASK_L(%d)" % card) is False, str(rt.eval("ASK_L(%d)" % card)))
    rt.execute('SET_DVAR("zm_unlock_camos", "0")')
    pump(rt, 2)
    rt.execute("ProgressionTuning.tick = ProgressionTuning.tick + 1")
    rt.execute("RESET_READS()")
    rt.eval("ASK_L(%d)" % camo)
    one = int(rt.eval("READS()"))
    rt.execute("RESET_READS()")
    rt.eval("ASK_L(%d)" % camo)
    two = int(rt.eval("READS()"))
    check("g32 toggle: every switch is read once a tick, not once an ask",
          one - two >= 18, "%d then %d" % (one, two))


def debug_toggles(lua51):
    attach, card, weapon = 126608, 200000, 125186
    ids = [attach, card, weapon]
    rt = new_rt(lua51, frontend=True, src=False)
    lua_slabs(rt, slabs_of(ids))
    lua_rslabs(rt, slabs_of(ids))
    rt.execute("SET_TYPE(%d, 7)" % attach)
    rt.execute("SET_TYPE(%d, 11)" % card)
    rt.execute("SET_TYPE(%d, 2)" % weapon)
    rt.execute("SET_G11(120)")
    rt.execute("SET_G12(%d)" % len(ids))
    load(rt)
    pump(rt, 1)

    def doors(i):
        return rt.eval("ASK_P(%d)" % i), rt.eval("ASK_L(%d)" % i)

    check("dbg toggle: an attachment, a card and a weapon with a bit and a reward read locked",
          all(doors(i) == (False, False) for i in ids), str([doors(i) for i in ids]))

    rt.execute('SET_DVAR("zm_unlock_attachments", "1")')
    pump(rt, 8)
    check("dbg toggle: unlock attachments opens the attachment on both doors",
          doors(attach) == (True, True), str(doors(attach)))
    check("dbg toggle: and leaves a calling card with a bit and a reward locked",
          doors(card) == (False, False), str(doors(card)))
    check("dbg toggle: and leaves a weapon with a bit and a reward locked",
          doors(weapon) == (False, False), str(doors(weapon)))
    check("dbg toggle: the open side opens that attachment and nothing else",
          rt.eval("ProgressionTuning.locks.open(%d)" % attach) is True
          and rt.eval("ProgressionTuning.locks.open(%d)" % card) is False
          and rt.eval("ProgressionTuning.locks.open(%d)" % weapon) is False,
          "%s / %s" % (rt.eval("ProgressionTuning.locks.open(%d)" % attach),
                       rt.eval("ProgressionTuning.locks.open(%d)" % card)))
    check("dbg toggle: it is not the unlock everything switch, so no stand-down is logged",
          count_line(lines_of(rt), "g11 debug unlock") == 0,
          " | ".join([ln for ln in lines_of(rt) if "debug unlock" in ln]))

    rt.execute('SET_DVAR("zm_unlock_attachments", "0") SET_DVAR("zm_unlock_weapons", "1")')
    pump(rt, 8)
    check("dbg toggle: unlock weapons opens that weapon on both doors",
          doors(weapon) == (True, True), str(doors(weapon)))
    check("dbg toggle: and leaves the attachment and the card locked",
          doors(attach) == (False, False) and doors(card) == (False, False),
          str([doors(attach), doors(card)]))

    rt.execute('SET_DVAR("zm_unlock_weapons", "0") SET_DVAR("zm_unlock_all", "1")')
    pump(rt, 8)
    check("dbg toggle: unlock everything opens all three on both doors",
          all(doors(i) == (True, True) for i in ids), str([doors(i) for i in ids]))
    check("dbg toggle: and that is the one switch the door reports as a stand-down",
          count_line(lines_of(rt), "g11 debug unlock zm_unlock_all is on") == 1,
          " | ".join([ln for ln in lines_of(rt) if "debug unlock" in ln]))
    rt.execute('SET_DVAR("zm_unlock_all", "0")')
    pump(rt, 8)
    check("dbg toggle: every switch off closes all three again",
          all(doors(i) == (False, False) for i in ids), str([doors(i) for i in ids]))


def dbg_toggle_prestige(lua51):
    rt = new_rt(lua51, frontend=True, src=False)
    lua_slabs(rt, slabs_of([150900]))
    lua_rslabs(rt, slabs_of([150100]))
    rt.execute("SET_G11(51)")
    rt.execute("SET_G12(1)")
    rt.execute('SET_PRESTIGE("sat_pi_alcor", 0)')
    rt.execute('SET_LEVEL("sat_pi_alcor", 2)')
    rt.execute('SET_PREQ("sat_pi_alcor", 126608, 1)')
    rt.execute('PRESTIGE_BUNDLE(126608, "sat_pi_alcor")')
    rt.execute("SET_TYPE(126608, 7)")
    load(rt)
    pump(rt, 1)

    def doors(i):
        return rt.eval("ASK_P(%d)" % i), rt.eval("ASK_L(%d)" % i)

    check("dbg toggle: a prestige attachment reads locked with every switch off",
          doors(126608) == (False, False), str(doors(126608)))
    rt.execute('SET_DVAR("zm_unlock_attachments", "1")')
    pump(rt, 8)
    check("dbg toggle: unlock attachments opens a prestige attachment on both doors",
          doors(126608) == (True, True), str(doors(126608)))
    rt.execute('SET_DVAR("zm_unlock_attachments", "0")')
    pump(rt, 8)
    check("dbg toggle: and off again closes that prestige attachment",
          doors(126608) == (False, False), str(doors(126608)))
    rt.execute('SET_DVAR("zm_unlock_all", "1")')
    pump(rt, 8)
    check("dbg toggle: unlock everything still opens that prestige attachment",
          doors(126608) == (True, True), str(doors(126608)))


def g32_prestige_sets(lua51):
    one, three, five, plain = 80001, 80002, 80003, 80004

    def sets(pre="", player=0):
        rt = new_rt(lua51, frontend=True, src=False)
        rt.execute(PRESTIGE_SETS)
        rt.execute("SET_CS(%d, 0) SET_CS(%d, 0) SET_CS(%d, 0) SET_CS(%d, 0)" % (one, three, five, plain))
        rt.execute("SET_PPLAYER(%d)" % player)
        if pre:
            rt.execute(pre)
        load(rt)
        pump(rt, 8)
        return rt

    rt = sets(player=1)
    check("g32 sets: a set at the player's own prestige reads in progress",
          rt.eval("ASK_CS(%d)" % one) == 1, str(rt.eval("ASK_CS(%d)" % one)))
    check("g32 sets: a set above it reads inactive, not in progress",
          rt.eval("ASK_CS(%d)" % three) == 4 and rt.eval("ASK_CS(%d)" % five) == 4,
          "%s / %s" % (rt.eval("ASK_CS(%d)" % three), rt.eval("ASK_CS(%d)" % five)))
    check("g32 sets: an id that is no prestige row is answered by the client untouched",
          rt.eval("ASK_CS(%d)" % plain) == 0, str(rt.eval("ASK_CS(%d)" % plain)))
    check("g32 sets: no line names the prestige, and the sets it opens are the state's own",
          count_line(lines_of(rt), "prestige sets:") == 0
          and rt.eval("ASK_CS(%d)" % one) == 1 and rt.eval("ASK_CS(%d)" % three) == 4,
          " | ".join([x for x in lines_of(rt) if "prestige sets:" in x][:2]))
    cols = rt.eval("table.concat(COLNUM['ccprestige'], ',')")
    check("g32 sets: the map is built from the id and prestige columns alone",
          cols == "0,14", str(cols))

    rt.execute("SET_PPLAYER(5)")
    pump(rt, 1)
    check("g32 sets: every set up to a prestige 5 player reads in progress",
          [rt.eval("ASK_CS(%d)" % i) for i in (one, three, five)] == [1, 1, 1],
          str([rt.eval("ASK_CS(%d)" % i) for i in (one, three, five)]))
    rt.execute("SET_CS(%d, 3)" % three)
    check("g32 sets: a set the client has finished stays finished",
          rt.eval("ASK_CS(%d)" % three) == 3, str(rt.eval("ASK_CS(%d)" % three)))
    rt.execute("SET_CS(%d, 4)" % plain)
    check("g32 sets: an inactive state on an id of ours is not read as ours",
          rt.eval("ASK_CS(%d)" % plain) == 4, str(rt.eval("ASK_CS(%d)" % plain)))

    pump(rt, 1)
    p0 = int(rt.eval("PPCALLS"))
    for _ in range(3):
        rt.eval("ASK_CS(%d)" % one)
    check("g32 sets: the player prestige is read once a tick, not once an ask",
          int(rt.eval("PPCALLS")) - p0 == 1, str(int(rt.eval("PPCALLS")) - p0))

    rt.execute('SET_DVAR("zm_unlock_cards", "1")')
    pump(rt, 1)
    check("g32 sets: with unlock cards on the client's own state stands",
          rt.eval("ASK_CS(%d)" % one) == 0, str(rt.eval("ASK_CS(%d)" % one)))
    rt.execute('SET_DVAR("zm_unlock_cards", "0") SET_DVAR("zm_unlock_all", "1")')
    pump(rt, 1)
    check("g32 sets: and with unlock all on it stands too",
          rt.eval("ASK_CS(%d)" % one) == 0, str(rt.eval("ASK_CS(%d)" % one)))
    rt.execute('SET_DVAR("zm_unlock_all", "0")')
    pump(rt, 1)
    check("g32 sets: both off and the set is in progress again",
          rt.eval("ASK_CS(%d)" % one) == 1, str(rt.eval("ASK_CS(%d)" % one)))

    dvar = sets(pre="DROP_PPLAYER() SET_DVAR('zm_local_prestige', '3')", player=3)
    check("g32 sets: with no prestige native the dvar the hud reads answers instead",
          dvar.eval("ASK_CS(%d)" % three) == 1 and dvar.eval("ASK_CS(%d)" % five) == 4,
          "%s / %s" % (dvar.eval("ASK_CS(%d)" % three), dvar.eval("ASK_CS(%d)" % five)))
    check("g32 sets: and it prints no line at all, the dvar path proved by the answer",
          count_line(lines_of(dvar), "prestige sets:") == 0
          and dvar.eval("ASK_CS(%d)" % one) == 1,
          " | ".join([x for x in lines_of(dvar) if "prestige sets:" in x][:2]))

    late = new_rt(lua51, frontend=True, src=False)
    late.execute(PRESTIGE_SETS)
    late.execute("SET_CS(%d, 0) SET_PPLAYER(1) DROP_CS()" % one)
    load(late)
    pump(late, 4)
    check("g32 sets: a vm with no state reader arms without a word",
          not any("error" in x or "raised" in x for x in lines_of(late)),
          " | ".join([x for x in lines_of(late) if "error" in x or "raised" in x][:2]))
    late.execute("ADD_CS()")
    pump(late, 40)
    check("g32 sets: and the reader is wrapped as soon as the client offers it",
          late.eval("ASK_CS(%d)" % one) == 1, str(late.eval("ASK_CS(%d)" % one)))


def g32_ask_cost(lua51):
    camo, ret = 107478, 129198
    rt = new_rt(lua51, frontend=True, src=False)
    rt.execute(CAMO_SCAN)
    lua_slabs(rt, slabs_of([camo, ret]))
    rt.execute("SET_G11(101)")
    rt.execute("SET_TYPE(%d, 14)" % ret)
    rt.execute("SET_TYPE(%d, 13)" % camo)
    rt.execute('SET_CAMODATA(%d, "sat_pi_alcor")' % camo)
    rt.execute('SET_PRESTIGE("sat_pi_alcor", 0)')
    rt.execute('SET_LEVEL("sat_pi_alcor", 2)')
    load(rt)
    pump(rt, 1)
    rt.eval("ASK_L(%d)" % camo)
    rt.execute("RESET_READS()")
    for _ in range(3):
        rt.eval("ASK_L(%d)" % camo)
    cam = int(rt.eval("READS()"))
    check("w2 ask: three asks of one camo id in a tick cost three reads, not fifteen",
          cam <= 3, "%d reads" % cam)

    rt.eval("ASK_L(%d)" % ret)
    rt.execute("RESET_READS()")
    for _ in range(3):
        rt.eval("ASK_L(%d)" % ret)
    retr = int(rt.eval("READS()"))
    check("w2 ask: a reticle id asked three times in a tick reads no switch again",
          retr == 0, "%d reads" % retr)

    many = [160100 + i for i in range(50)]
    for i in many:
        rt.execute("SET_TYPE(%d, 14)" % i)
    lua_slabs(rt, slabs_of([camo, ret] + many))
    rt.execute('SET_VER("102:33:65536")')
    pump(rt, 8)
    rt.eval("ASK_L(%d)" % many[0])
    rt.execute("RESET_READS()")
    for i in many:
        rt.eval("ASK_L(%d)" % i)
    bulk = int(rt.eval("READS()"))
    check("w2 ask: fifty ids asked in one tick cost less than one read each", bulk < 50,
          "%d reads" % bulk)

    rt.execute("SET_TYPE(160500, 14)")
    lua_slabs(rt, slabs_of([160500]))
    rt.execute('SET_VER("103:33:65536")')
    pump(rt, 8)
    rt.eval("ASK_L(160500)")
    tc = int(rt.eval("TYPECALLS"))
    for _ in range(3):
        rt.eval("ASK_L(160500)")
    check("w2 ask: the type of an id is looked up once for three asks",
          int(rt.eval("TYPECALLS")) - tc == 0, str(int(rt.eval("TYPECALLS")) - tc))


def g32_ask_native(lua51):
    card, ret = 104861, 129198
    rt = new_rt(lua51, frontend=True, src=False)
    rt.execute(CARD_ROWS + CARD_TYPES + STORE_FIX + BUY_FIX + "SET_BUY(%d, { lootid = %d })" % (card, card))
    lua_slabs(rt, slabs_of([card, ret]))
    lua_rslabs(rt, slabs_of([ret]))
    rt.execute("SET_G11(104)")
    rt.execute("SET_G12(1)")
    rt.execute("SET_TYPE(%d, 14)" % ret)
    load(rt)
    pump(rt, 1)
    rt.eval("ASK_L(%d)" % card)
    p0 = int(rt.eval("PLATCALLS"))
    for _ in range(3):
        rt.execute("ProgressionTuning.g11.memo = nil")
        rt.eval("ASK_L(%d)" % card)
    plat = int(rt.eval("PLATCALLS"))
    check("w2 native: the platform question is asked once for an id", p0 == 1 and plat == 1,
          "%d then %d" % (p0, plat))

    d0 = int(rt.eval("DEFCALLS"))
    rt.eval("ASK_L(%d)" % ret)
    d1 = int(rt.eval("DEFCALLS"))
    for _ in range(3):
        rt.execute("ProgressionTuning.g11.memo = nil")
        rt.eval("ASK_L(%d)" % ret)
    defs = int(rt.eval("DEFCALLS"))
    check("w2 native: the default question is asked once for an id", d1 - d0 == 1 and defs == d1,
          "%d / %d then %d" % (d0, d1, defs))

    lua_slabs(rt, slabs_of([card]))
    rt.execute('SET_VER("105:33:65536")')
    pump(rt, 8)
    ans = rt.eval("ASK_L(%d)" % ret)
    check("w2 memo: a moved serial drops the answer the door kept", ans is True, str(ans))


def g32_ask_epoch(lua51):
    card = 117486
    rt = card_vm(lua51, CARD_ROWS + CARD_TYPES, [card], 106)
    first = rt.eval("ASK_L(%d)" % card)
    rt.execute('SET_DVAR("zm_unlock_cards", "1")')
    pump(rt, 1)
    on = rt.eval("ASK_L(%d)" % card)
    rt.execute('SET_DVAR("zm_unlock_cards", "0")')
    pump(rt, 1)
    off = rt.eval("ASK_L(%d)" % card)
    check("w2 memo: a changed switch drops the answer the door kept",
          first is False and on is True and off is False, "%s / %s / %s" % (first, on, off))


def g32_ask_logs(lua51):
    ids = [160001 + i for i in range(300)]
    rt = new_rt(lua51, frontend=True, src=False)
    lua_slabs(rt, slabs_of(ids))
    rt.execute("SET_G11(107)")
    for i in ids:
        rt.execute("SET_TYPE(%d, 13)" % i)
    load(rt)
    pump(rt, 1)
    for i in ids:
        rt.eval("ASK_L(%d)" % i)
    n = count_line(lines_of(rt), "names no weapon")
    check("w2 log: the no weapon line stops at twenty four a session", n == 24, str(n))


def g32_ask_cards(lua51):
    rt = card_vm(lua51, CARD_ROWS + CARD_TYPES + READ_COUNT, [117486], 108, ticks=1, cards=False)
    pump(rt, 64)
    why = count_line(lines_of(rt), "why=")
    check("w2 card: no tick reads a card table, however long the vm runs",
          [reads(rt, f) for f in ("ret", "seas", "gs")] == [0, 0, 0]
          and reads(rt, "ccprestige") == 2 and why == 0,
          "%d / %d / %d / %d / %d" % (reads(rt, "ret"), reads(rt, "seas"), reads(rt, "gs"),
                                      reads(rt, "ccprestige"), why))


BUY_IDS = r"""
SET_TYPE(130001, 11) SET_TYPE(130002, 11) SET_TYPE(130003, 11) SET_TYPE(130004, 11)
SET_TYPE(130005, 11) SET_TYPE(130006, 11) SET_TYPE(130007, 11) SET_TYPE(130008, 11)
SET_TYPE(130009, 11)
"""

BUY_SELLS = r"""
SET_BUY(130002, { lootid = 130002 })
SET_BP(130003, true)
SET_BC(130004, true)
SET_BM(130005, true)
SET_BIDX(130006, 3)
SET_DEFAULT(130007)
PLAIN_BUNDLE(130008, "jup_ar_mw3gun")
"""

BIDX_ONLY = r"""
STORE = nil
BATTLEMAP = { LootIdToSectorIndex = { [130006] = 3 } }
"""


def g32_buy(lua51):
    plain, sold, bp, bc, bm, bidx = 130001, 130002, 130003, 130004, 130005, 130006
    dflt, car, nobit = 130007, 130008, 130009
    ids = [plain, sold, bp, bc, bm, bidx, dflt, car]

    def vm(pre="", slabs=None, n=120, ticks=2):
        rt = new_rt(lua51, frontend=True, src=False)
        rt.execute(BUY_IDS)
        if pre:
            rt.execute(pre)
        lua_slabs(rt, slabs_of(slabs if slabs is not None else ids))
        rt.execute("SET_G11(%d)" % n)
        load(rt)
        pump(rt, ticks)
        return rt

    rt = vm(BUY_FIX + BUY_SELLS)
    check("g32 buy: a card with a bit and nothing selling it locks",
          rt.eval("ASK_L(%d)" % plain) is False, str(rt.eval("ASK_L(%d)" % plain)))
    check("g32 buy: the same card opens when a bundle carries it",
          rt.eval("ASK_L(%d)" % sold) is True, str(rt.eval("ASK_L(%d)" % sold)))
    check("g32 buy: a battle pass reward opens",
          rt.eval("ASK_L(%d)" % bp) is True, str(rt.eval("ASK_L(%d)" % bp)))
    check("g32 buy: a blackcell reward opens",
          rt.eval("ASK_L(%d)" % bc) is True, str(rt.eval("ASK_L(%d)" % bc)))
    check("g32 buy: a battle map reward opens",
          rt.eval("ASK_L(%d)" % bm) is True, str(rt.eval("ASK_L(%d)" % bm)))
    check("g32 buy: a battle map sector index no longer opens on its own",
          rt.eval("ASK_L(%d)" % bidx) is False, str(rt.eval("ASK_L(%d)" % bidx)))
    check("g32 buy: a card the game ships by default opens",
          rt.eval("ASK_L(%d)" % dflt) is True, str(rt.eval("ASK_L(%d)" % dflt)))
    check("g32 buy: a card carried by a foreign ref opens",
          rt.eval("ASK_L(%d)" % car) is True, str(rt.eval("ASK_L(%d)" % car)))
    check("g32 buy: a card with no bit opens",
          rt.eval("ASK_L(%d)" % nobit) is True, str(rt.eval("ASK_L(%d)" % nobit)))

    b0, p0 = int(rt.eval("BUYCALLS")), int(rt.eval("BPCALLS"))
    k0, m0, d0 = int(rt.eval("BCCALLS")), int(rt.eval("BMCALLS")), int(rt.eval("DESCCALLS"))
    for _ in range(3):
        rt.execute("ProgressionTuning.g11.memo = nil")
        rt.eval("ASK_L(%d)" % sold)
    check("g32 buy: every native is asked once for an id, not once an ask",
          (int(rt.eval("BUYCALLS")), int(rt.eval("BPCALLS")), int(rt.eval("BCCALLS")),
           int(rt.eval("BMCALLS")), int(rt.eval("DESCCALLS"))) == (b0, p0, k0, m0, d0),
          "%d/%d/%d/%d/%d" % (int(rt.eval("BUYCALLS")) - b0, int(rt.eval("BPCALLS")) - p0,
                              int(rt.eval("BCCALLS")) - k0, int(rt.eval("BMCALLS")) - m0,
                              int(rt.eval("DESCCALLS")) - d0))

    rt.execute('SET_DVAR("zm_unlock_cards", "1")')
    pump(rt, 1)
    check("g32 buy: the card switch still forces the type open",
          rt.eval("ASK_L(%d)" % plain) is True, str(rt.eval("ASK_L(%d)" % plain)))
    rt.execute('SET_DVAR("zm_unlock_cards", "0")')
    pump(rt, 1)
    check("g32 buy: and off again locks it back",
          rt.eval("ASK_L(%d)" % plain) is False, str(rt.eval("ASK_L(%d)" % plain)))

    cold = vm(BUY_FIX + BUY_SELLS, n=121)
    c0 = int(cold.eval("BUYCARDS()"))
    cold.eval("ASK_L(%d)" % sold)
    first = int(cold.eval("BUYCARDS()")) - c0
    c1 = int(cold.eval("BUYCARDS()"))
    cold.execute("ProgressionTuning.g11.memo = nil")
    cold.eval("ASK_L(%d)" % sold)
    check("g32 buy: a sold card costs five questions cold and none warm",
          first == 5 and int(cold.eval("BUYCARDS()")) == c1,
          "%d then %d" % (first, int(cold.eval("BUYCARDS()")) - c1))

    bare = vm("", n=122)
    check("g32 buy: with no probe at all a card stays locked",
          bare.eval("ASK_L(%d)" % plain) is False, str(bare.eval("ASK_L(%d)" % plain)))
    check("g32 buy: and says once which probe is missing",
          count_line(lines_of(bare),
                     "card lock: purchasable probe missing STORE.Bundles.GetFirstBundleWithLootId") == 1,
          " | ".join([x for x in lines_of(bare) if "purchasable" in x][:2]))

    only = vm(BIDX_ONLY, n=125)
    check("g32 buy: a sector table alone is no probe, so the fail closed line prints",
          only.eval("ASK_L(%d)" % bidx) is False
          and count_line(lines_of(only), "card lock: purchasable probe missing") == 1,
          " | ".join([x for x in lines_of(only) if "purchasable" in x][:2]))

    many = [130100 + i for i in range(300)]
    cap = new_rt(lua51, frontend=True, src=False)
    cap.execute("".join("SET_TYPE(%d, 11) " % i for i in many))
    cap.execute(BUY_FIX)
    cap.execute("SET_TOGGLE('pt_log', 1)")
    lua_slabs(cap, slabs_of(many))
    cap.execute("SET_G11(123)")
    load(cap)
    pump(cap, 1)
    for i in many:
        cap.eval("ASK_L(%d)" % i)
    blk = [x for x in lines_of(cap) if "card lock: " in x and "probe missing" not in x]
    check("g32 buy: the card lock line stops at forty a session",
          len(blk) == 40 and has_line(blk, "card lock: 1 id=%d type=11 buy=0" % many[0])
          and has_line(blk, "card lock: 40 id=%d type=11 buy=0" % many[39]),
          "%d lines" % len(blk))

    trig = new_rt(lua51, frontend=True, src=False)
    trig.execute(CARD_ROWS + CARD_TYPES + STORE_FIX + READ_COUNT)
    trig.execute("SET_TYPE(131708, 13) SET_TYPE(129198, 14) SET_TYPE(140001, 16) SET_TYPE(140002, 12)")
    lua_slabs(trig, slabs_of([117486, 131708, 129198, 140001, 140002]))
    trig.execute("SET_G11(124)")
    load(trig)
    trig.eval("ASK_L(117486)")
    check("g32 load: a card ask loads no reward table",
          [reads(trig, f) for f in ("ret", "seas", "gs")] == [0, 0, 0],
          str([reads(trig, f) for f in ("ret", "seas", "gs")]))
    trig.eval("ASK_L(131708)")
    check("g32 load: a camo ask loads the gunsmith table", reads(trig, "gs") == 1,
          str(reads(trig, "gs")))
    trig.eval("ASK_L(129198)")
    check("g32 load: a reticle ask loads the reticle table", reads(trig, "ret") == 1,
          str(reads(trig, "ret")))
    trig.eval("ASK_L(140001)")
    check("g32 load: a charm ask loads the seasonal table", reads(trig, "seas") == 1,
          str(reads(trig, "seas")))
    trig.eval("ASK_L(140002)")
    check("g32 load: an emblem ask finds that table already there", reads(trig, "seas") == 1,
          str(reads(trig, "seas")))


W5_CAMO = r"""
PRESTIGE[xhash("getmaxweaponprestigelevel")] = function(ref) return 2 end
PRESTIGE[xhash("getweaponprestigecamos")] = function(ref)
  local a = { { startPrestige = 0, startLevel = 0, targetPrestige = 1, targetLevel = 27,
                camoBundle = { lootid = 107478 } } }
  local b = { { startPrestige = 2, startLevel = 99, targetPrestige = 2, targetLevel = 149,
                camoBundle = { lootid = 132741 } } }
  local c = { { startPrestige = 0, startLevel = 0, targetPrestige = 1, targetLevel = 27,
                camoBundle = { lootid = 113244 } } }
  return a, b, c
end
WEAPON[xhash("enumerateweapons")] = function(cb) cb({ ref = "sat_pi_alcor" }) end
"""

W5_COUNTS = r"""
CAMOREFCALLS, PRESTIGECALLS, PRESTCALLS, LEVELCALLS = 0, 0, 0, 0
MODENOW = "zm"
Engine[xhash("GetActiveGameModeKey")] = function() return MODENOW end
function SET_MODE(v) MODENOW = v end
function MEMO(id)
  local m = G11('memo')
  if type(m) ~= "table" or type(m.lock) ~= "table" then return nil end
  return m.lock[id]
end
local w5camo = WEAPON[xhash("getcamodatabyid")]
WEAPON[xhash("getcamodatabyid")] = function(id)
  CAMOREFCALLS = CAMOREFCALLS + 1
  return w5camo(id)
end
local w5steps = PRESTIGE[xhash("getweaponprestigecamos")]
PRESTIGE[xhash("getweaponprestigecamos")] = function(ref)
  PRESTIGECALLS = PRESTIGECALLS + 1
  return w5steps(ref)
end
local w5prest = PRESTIGE[xhash("getweaponprestigelevel")]
PRESTIGE[xhash("getweaponprestigelevel")] = function(c, ref)
  PRESTCALLS = PRESTCALLS + 1
  return w5prest(c, ref)
end
local w5lvl = PROGRESSION[xhash("GetWeaponLevel")]
PROGRESSION[xhash("GetWeaponLevel")] = function(c, ref)
  LEVELCALLS = LEVELCALLS + 1
  return w5lvl(c, ref)
end
function W5()
  return TYPECALLS + DEFCALLS + PLATCALLS + CAMOREFCALLS + PRESTIGECALLS + PRESTCALLS + LEVELCALLS
end
"""


def g32_w5(lua51):
    band, flat, plain = 107478, 160200, 140701
    att, ret, card, plat = 126608, 129198, 117486, 200002
    gear, gatt, ctrl = 113244, 62769, 140702
    rt = new_rt(lua51, frontend=True, src=False)
    rt.execute(CARD_ROWS + CARD_TYPES + STORE_FIX + BUY_FIX
               + "SET_BUY(%d, { lootid = %d })" % (plat, plat) + W5_CAMO + W5_COUNTS)
    lua_slabs(rt, slabs_of([band, att, ret, card, plat]))
    rt.execute("SET_G11(110)")
    rt.execute("SET_TYPE(%d, 13)" % band)
    rt.execute("SET_TYPE(%d, 13)" % flat)
    rt.execute("SET_TYPE(%d, 13)" % gear)
    rt.execute("SET_TYPE(132741, 13)")
    rt.execute("SET_TYPE(%d, 11)" % card)
    rt.execute("SET_TYPE(%d, 11)" % plat)
    rt.execute("SET_TYPE(%d, 14)" % ret)
    rt.execute('SET_CAMODATA(%d, "sat_pi_alcor")' % band)
    rt.execute('SET_PRESTIGE("sat_pi_alcor", 0)')
    rt.execute('SET_LEVEL("sat_pi_alcor", 2)')
    for i in (att, gatt, ctrl):
        rt.execute('SET_PREQ("sat_pi_alcor", %d, 1)' % i)
        rt.execute('PRESTIGE_BUNDLE(%d, "sat_pi_alcor")' % i)
    load(rt)
    pump(rt, 1)

    c0 = int(rt.eval("CAMOREFCALLS"))
    rt.eval("ASK_L(%d)" % flat)
    check("w5 camo: the first ask of a camo with no own data reads that data once",
          int(rt.eval("CAMOREFCALLS")) - c0 == 1, str(int(rt.eval("CAMOREFCALLS")) - c0))
    for _ in range(2):
        rt.eval("ASK_L(%d)" % flat)
    check("w5 camo: and the miss is kept - three asks read it once",
          int(rt.eval("CAMOREFCALLS")) - c0 == 1, str(int(rt.eval("CAMOREFCALLS")) - c0))

    check("w5 gearn: an earned prestige reward with no bit is not closed by its own rule",
          rt.eval("ASK_L(%d)" % gatt) is True and rt.eval("ASK_L(%d)" % gear) is True,
          "%s / %s" % (rt.eval("ASK_L(%d)" % gatt), rt.eval("ASK_L(%d)" % gear)))
    check("w5 gearn: while the same two rules still close a camo and a reward that earn nothing",
          rt.eval("ASK_L(%d)" % 132741) is False and rt.eval("ASK_L(%d)" % ctrl) is False,
          "%s / %s" % (rt.eval("ASK_L(%d)" % 132741), rt.eval("ASK_L(%d)" % ctrl)))

    for i in (flat, plain, ret, card):
        rt.eval("ASK_L(%d)" % i)
    rt.execute("RESET_READS()")
    w0 = int(rt.eval("W5()"))
    for _ in range(3):
        for i in (flat, plain, ret, card):
            rt.eval("ASK_L(%d)" % i)
    check("w5 warm: three more asks of a camo, an attachment, a reticle and a card cost no call",
          int(rt.eval("W5()")) == w0, "%d -> %d" % (w0, int(rt.eval("W5()"))))
    check("w5 warm: and not one dvar read between them", int(rt.eval("READS()")) == 0,
          "%d reads" % int(rt.eval("READS()")))

    s0 = int(rt.eval("PRESTIGECALLS"))
    rt.eval("ASK_L(%d)" % band)
    check("w5 band: the weapon ladder is read once and kept",
          int(rt.eval("PRESTIGECALLS")) - s0 == 1, str(int(rt.eval("PRESTIGECALLS")) - s0))
    p0, l0 = int(rt.eval("PRESTCALLS")), int(rt.eval("LEVELCALLS"))
    rt.eval("ASK_L(%d)" % band)
    check("w5 band: a second ask reads the weapon pair and nothing else",
          int(rt.eval("PRESTIGECALLS")) - s0 == 1 and int(rt.eval("PRESTCALLS")) - p0 == 1
          and int(rt.eval("LEVELCALLS")) - l0 == 1,
          "%d / %d / %d" % (int(rt.eval("PRESTIGECALLS")) - s0, int(rt.eval("PRESTCALLS")) - p0,
                            int(rt.eval("LEVELCALLS")) - l0))
    rt.execute('SET_PRESTIGE("sat_pi_alcor", 1)')
    check("w5 band: a weapon prestige change answers on the next ask in the same tick",
          rt.eval("ASK_L(%d)" % band) is True, str(rt.eval("ASK_L(%d)" % band)))
    rt.execute('SET_PRESTIGE("sat_pi_alcor", 0)')
    check("w5 band: and back again locks it in the same tick too",
          rt.eval("ASK_L(%d)" % band) is False, str(rt.eval("ASK_L(%d)" % band)))

    for i in (ret, card, flat):
        rt.eval("ASK_L(%d)" % i)
    before = {i: rt.eval("ASK_L(%d)" % i) for i in (ret, card, flat)}
    rt.execute('SET_MODE("ob")')
    pump(rt, 1)
    check("w5 mode: a mode change drops every answer the door kept",
          rt.eval("MEMO(%d) == nil" % ret) is True and rt.eval("MEMO(%d) == nil" % card) is True,
          "%s / %s" % (rt.eval("MEMO(%d)" % ret), rt.eval("MEMO(%d)" % card)))
    check("w5 mode: and drops the camo answer the band does move",
          rt.eval("MEMO(%d) == nil" % flat) is True, str(rt.eval("MEMO(%d)" % flat)))
    check("w5 mode: the camo map and the weapon ladder go with it",
          rt.eval("G11('camomap')") is None
          and rt.eval("G11('pcamo')['sat_pi_alcor']") is None,
          "%s / %s" % (rt.eval("G11('camomap')") is not None,
                       rt.eval("G11('pcamo')['sat_pi_alcor']") is not None))
    check("w5 mode: and the ask after it answers as it did before the move",
          all(rt.eval("ASK_L(%d)" % i) == before[i] for i in (ret, card, flat)),
          " | ".join("%d %s/%s" % (i, before[i], rt.eval("ASK_L(%d)" % i)) for i in (ret, card, flat)))
    check("w5 mode: while the answer it just gave fills the memo again",
          rt.eval("MEMO(%d) ~= nil" % ret), str(rt.eval("MEMO(%d)" % ret)))

    rt.execute("SET_PLATFORM(false)")
    p1 = int(rt.eval("PLATCALLS"))
    for _ in range(3):
        rt.execute("ProgressionTuning.g11.memo = nil")
        rt.eval("ASK_L(%d)" % plat)
    check("w5 store: a refused platform id asks the platform once and keeps the no",
          int(rt.eval("PLATCALLS")) - p1 == 1, str(int(rt.eval("PLATCALLS")) - p1))

    rt.eval("ASK_L(%d)" % card)
    e1 = int(rt.eval("G11('memo').epoch"))
    lua_slabs(rt, slabs_of([band, att, ret, card, plat, 200003]))
    rt.execute('SET_VER("111:33:65536")')
    pump(rt, 20)
    rt.eval("ASK_L(%d)" % card)
    e2 = int(rt.eval("G11('memo').epoch"))
    check("w5 epoch: a moved serial drops the memo and the next ask refills it",
          e2 > e1 and e2 == int(rt.eval("G11('epoch')")), "%d -> %d" % (e1, e2))


def g32_earn_pin(lua51):
    text = LUA_TEXT[PRISON]
    m = re.search(r"local GEARN_IDS = \{(.*?)\}", text, re.S)
    ids = sorted(int(x) for x in re.findall(r"\d+", m.group(1))) if m else []
    path = os.path.join(PKG, "data", "challenges.tsv")
    rows = [ln.rstrip("\n").split("\t") for ln in open(path, encoding="utf-8")]
    lists = {r[0]: r[1] for r in rows if len(r) == 2 and r[0].startswith("@")}

    def ids_of(name):
        return set(int(t) for t in lists.get(name, "").split(",") if t.strip().isdigit())

    earn, store = set(), set()
    for name in lists:
        if name.startswith(("@lv_", "@pr_", "@rank_")):
            earn |= ids_of(name)
    for name in STORE_LISTS:
        store |= ids_of(name)
    check("g32 earn: the earn list is exactly the store ids a level prestige or rank list pays",
          ids == sorted(earn & store), "%d ids against %d" % (len(ids), len(earn & store)))




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
    check("order: the %d parts load in %s order with nothing raised" % (len(LUA_FILES), LOAD_ORDER),
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
          and count_line(l, "weekly body=") == 0,
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
    check("G1: the whole body goes out and nothing prints it",
          rl.eval("EV(1).options.bodyText") == "Z" * 60
          and count_line(lines_of(rl), "weekly body=") == 0,
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
          num(rt, "ProgressionTuning.guns['sat_me_shockbaton'].level") == 0,
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
          num(rt2, "ProgressionTuning.guns['sat_pi_alcor'].own") == 3
          and num(rt2, "ProgressionTuning.guns['sat_pi_alcor'].n") == 5
          and rt2.eval("ProgressionTuning.guns['sat_pi_alcor'].src") == "minxp"
          and num(rt2, "ProgressionTuning.guns['sat_pi_alcor'].level") == 3,
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
          a == b and num(rt3, "ProgressionTuning.guns['sat_pi_alcor'].level") == 3,
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
          rt4.eval("ProgressionTuning.guns['sat_pi_alcor'].ladder") is None
          and rt4.eval("NEVENTS()") == 0,
          " | ".join([x for x in lines_of(rt4) if "picked=" in x][:2]))
    rt4.execute('SET_LEVEL("sat_pi_alcor", 3)')
    rt4.execute('SET_PAID("v1;125186:4009:2")')
    pump(rt4, 5)
    check("A3: the next payment retries and primes - no deadlock",
          num(rt4, "ProgressionTuning.guns['sat_pi_alcor'].level") == 3
          and rt4.eval("NEVENTS()") == 0,
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
          num(rt5, "ProgressionTuning.guns['sat_reach_test'].level") == 0
          and rt5.eval("NEVENTS()") == 0,
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
          num(rt6, "ProgressionTuning.guns['sat_big_test'].own") == 3
          and num(rt6, "ProgressionTuning.guns['sat_big_test'].n") == 3
          and num(rt6, "ProgressionTuning.guns['sat_big_test'].level") == 3,
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
          num(rt, "ProgressionTuning.guns['sat_me_shockbaton'].level") == 0,
          " | ".join([x for x in l if "prime " in x][:3]))
    check("A: and the pick names the row's own cell - the per-level cost list is not a candidate at all",
          num(rt, "ProgressionTuning.guns['sat_me_shockbaton'].n") == 5
          and rt.eval("ProgressionTuning.guns['sat_me_shockbaton'].src") == "csv"
          and count_line(l, "/weapon") == 0,
          " | ".join([x for x in l if "picked=" in x][:3]))
    check("A: 260 XP draws nothing", rt.eval("NEVENTS()") == 0)
    for tot in (300, 360, 440):
        rt.execute('SET_PAID("v1;98753:%d:%d")' % (tot, tot))
        pump(rt, 8)
    check("A: 300, 360 and 440 are all still level 0 - the ten false banners are gone",
          rt.eval("NEVENTS()") == 0
          and num(rt, "ProgressionTuning.guns['sat_me_shockbaton'].level") == 0,
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
          num(rt2, "ProgressionTuning.guns['sat_pi_alcor'].level") == 2
          and num(rt2, "ProgressionTuning.guns['sat_pi_alcor'].n") == 5
          and rt2.eval("ProgressionTuning.guns['sat_pi_alcor'].src") == "minxp",
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
          rt3.eval("ProgressionTuning.guns['sat_reach_test'].ladder") is None
          and has_line(l, "no ladder answers for sat_reach_test (own 0)"),
          " | ".join([x for x in l if ("picked=" in x or "no ladder" in x)][:3]))
    check("A: and that refusal draws nothing", rt3.eval("NEVENTS()") == 0)
    rt3.execute('SET_MINXP("sat_reach_test", { 100, 200, 300 })')
    rt3.execute('SET_PAID("v1;50101:90:2")')
    pump(rt3, 8)
    check("A: the refusal is not kept - the next payment picks the ladder that now exists and primes",
          num(rt3, "ProgressionTuning.guns['sat_reach_test'].level") == 0
          and rt3.eval("NEVENTS()") == 0,
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
          rt4.eval("ProgressionTuning.guns['sat_pi_alcor'].ladder") is None
          and rt4.eval("NEVENTS()") == 0,
          " | ".join([x for x in lines_of(rt4) if "picked=" in x][:2]))
    rt4.execute('SET_LEVEL("sat_pi_alcor", 4)')
    rt4.execute('SET_PAID("v1;125186:4600:2")')
    pump(rt4, 8)
    check("A: when own catches up the pick is made and the level is primed, never announced late",
          num(rt4, "ProgressionTuning.guns['sat_pi_alcor'].level") == 4
          and rt4.eval("NEVENTS()") == 0,
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
          num(rt, "ProgressionTuning.camo.rows['sat_pi_atlas'].id") == 57201
          and num(rt, "ProgressionTuning.camo.rows['sat_pi_atlas'].n") == 3
          and num(rt, "ProgressionTuning.camo.rows['sat_pi_atlas'].th[1]") == 100
          and num(rt, "ProgressionTuning.camo.rows['sat_pi_atlas'].th[3]") == 300,
          " | ".join([x for x in l if "camo watch" in x][:2]))
    check("B: the first sighting primes silently, so a row already past a tier draws nothing",
          num(rt, "ProgressionTuning.camo.seen['57201']") == 90
          and count_line(l, "camo prime") == 0
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
    check("B: and the crossing is counted once and prints no line of its own",
          count_line(l, "camo cross id=") == 0
          and num(rt, "ProgressionTuning.camo.crossN") == 1,
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
          rt2.eval("NEVENTS()") == 0
          and num(rt2, "ProgressionTuning.camo.seen['57201']") == 150
          and count_line(lines_of(rt2), "camo prime") == 0,
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
          num(rt, "ProgressionTuning.chal.n") == 2
          and num(rt, "ProgressionTuning.chal.dailyN") == 1
          and num(rt, "ProgressionTuning.chal.weeklyN") == 1
          and num(rt, "ProgressionTuning.chal.rows[1].id") == 53310
          and num(rt, "ProgressionTuning.chal.rows[1].th[1]") == 75
          and num(rt, "ProgressionTuning.chal.seen['53310']") == 40
          and count_line(l, "chal watch") == 0,
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
          rt2.eval("NEVENTS()") == 0
          and num(rt2, "ProgressionTuning.chal.seen['53310']") == 75,
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
    check("E: in a Zombies match the watched row is the ZM row, and the multiplayer row is not",
          num(rt, "ProgressionTuning.camo.rows['sat_pi_alcor'].id") == 68970
          and not has_line(l, "68922"),
          " | ".join([x for x in l if "camo watch" in x][:2]))
    check("E: the watched row keeps the targets and the mode it was asked for",
          num(rt, "ProgressionTuning.camo.rows['sat_pi_alcor'].n") == 3
          and num(rt, "ProgressionTuning.camo.rows['sat_pi_alcor'].th[1]") == 100
          and num(rt, "ProgressionTuning.camo.rows['sat_pi_alcor'].th[3]") == 300
          and num(rt, "ProgressionTuning.camo.rows['sat_pi_alcor'].mode") == 2
          and count_line(l, "camo watch id=") == 0,
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
          not has_line(l, "camo card id=68922")
          and num(rt, "ProgressionTuning.camo.crossN") == 1,
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
          rt2.eval("SEENMODE") == 1
          and int(rt2.eval("ProgressionTuning.camo.rows['sat_pi_alcor'].id")) == 68922
          and int(rt2.eval("ProgressionTuning.camo.rows['sat_pi_alcor'].th[1]")) == 5
          and int(rt2.eval("ProgressionTuning.camo.rows['sat_pi_alcor'].th[3]")) == 20
          and int(rt2.eval("ProgressionTuning.camo.rows['sat_pi_alcor'].mode")) == 1,
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
          num(rt, "ProgressionTuning.chal.n") == 3
          and num(rt, "ProgressionTuning.chal.dailyN") == 1
          and num(rt, "ProgressionTuning.chal.weeklyN") == 2
          and count_line(l, "chal watch") == 0,
          " | ".join([x for x in l if "chal watch" in x][:2]))
    check("F: and the client is asked for the incomplete rows only",
          rt.eval("WEEKOPT") is not None and rt.eval("WEEKOPT.includeComplete") is False,
          str(rt.eval("WEEKOPT")))
    check("F: the weekly rows are watched with their own ids, kinds and targets",
          num(rt, "ProgressionTuning.chal.rows[2].id") == 60330
          and num(rt, "ProgressionTuning.chal.rows[2].kind") == 585
          and num(rt, "ProgressionTuning.chal.rows[2].th[1]") == 3
          and num(rt, "ProgressionTuning.chal.rows[3].id") == 60325,
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
          num(rt2, "ProgressionTuning.chal.n") == 2
          and num(rt2, "ProgressionTuning.chal.weeklyN") == 1
          and num(rt2, "ProgressionTuning.chal.rows[2].id") == 60330
          and num(rt2, "ProgressionTuning.chal.rows[2].th[1]") == 3,
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
COMPLETE = {}
function SET_COMPLETE(id) COMPLETE[id] = true end
Challenge[xhash("IsChallengeComplete")] = function(c, id) return COMPLETE[id] == true end
function SET_CHAL_REC(id) OC[tostring(id)] = { xp = 0, rank = 0 } end
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
          num(rt, "ProgressionTuning.chal.sweep.n") == 12
          and num(rt, "ProgressionTuning.chal.sweep.done") == 0
          and num(rt, "ProgressionTuning.chal.sweep.prog") == 12
          and rt.eval("ProgressionTuning.chal.sweep.src") == "fork"
          and count_line(l, "chal sweep") == 0,
          " | ".join([x for x in l if "chal sweep" in x][:2]))
    check("G: and it sweeps the four kinds the client names, counted per kind",
          num(rt, "ProgressionTuning.chal.sweep.kinds[1]") == 585
          and num(rt, "ProgressionTuning.chal.sweep.kinds[2]") == 590
          and num(rt, "ProgressionTuning.chal.sweep.kinds[3]") == 592
          and int(rt.eval("#ProgressionTuning.chal.sweep.kinds")) == 4,
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
          and num(rt, "ProgressionTuning.chal.crossN") == 12
          and count_line(l, "chal week cross id=") == 0
          and not has_line(l, "cards this match"),
          "%s / %s / %s" % (rt.eval("NAMED('add_message_splash_manager')"),
                            rt.eval("NAMED('completed_challenge')"),
                            num(rt, "ProgressionTuning.chal.crossN")))

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
          num(rt, "ProgressionTuning.chal.sweep.n") == 1
          and num(rt, "ProgressionTuning.chal.sweep.done") == 1
          and num(rt, "ProgressionTuning.chal.sweep.prog") == 1
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
          rt.eval("ProgressionTuning.chal.sweep.src") == "list"
          and num(rt, "ProgressionTuning.chal.sweep.n") == 2,
          " | ".join([x for x in l if "chal sweep" in x][:1]))
    rt.execute("SET_COMPLETE(70300)")
    rt.execute("DROP_WEEK_LIST()")
    pump(rt, 40)
    l = lines_of(rt)
    check("G: a weekly that disappears from that list is carded as a completion",
          has_line(l, "weekly card id=70300 row=sat_weekly_zm_list_a kind=585 target=4 value=4 route=B")
          and count_line(l, "chal week cross id=") == 0,
          " | ".join([x for x in l if "chal week cross" in x or " card id=" in x][:2]))

    rt = new_rt(lua51, src=False)
    rt.execute(PRE)
    rt.execute("DROP_FORK()")
    rt.execute("SET_WEEK_LIST(70500, '4', 'sat_weekly_zm_neg_a', 585, 1)")
    rt.execute("SET_CHAL_REC(70500)")
    rt.execute("SET_G11(220)")
    load(rt)
    pump(rt, 24)
    rt.execute("DROP_WEEK_LIST()")
    pump(rt, 32)
    l = lines_of(rt)
    check("G: a vanished weekly the game calls incomplete is not carded",
          not has_line(l, "weekly card id=70500")
          and num(rt, "ProgressionTuning.chal.crossN") == 1
          and count_line(l, "chal week cross id=") == 0
          and rt.eval("NEVENTS()") == 0,
          " | ".join([x for x in l if "chal week cross" in x or " card id=" in x][:3]))

    rt = new_rt(lua51, src=False)
    rt.execute(PRE)
    rt.execute("DROP_FORK()")
    rt.execute("SET_WEEK_LIST(70600, '4', 'sat_weekly_zm_gone_a', 585, 1)")
    rt.execute("SET_G11(221)")
    load(rt)
    pump(rt, 24)
    rt.execute("DROP_WEEK_LIST()")
    pump(rt, 32)
    l = lines_of(rt)
    check("G: a vanished weekly whose record is gone too is carded once, as unknown",
          has_line(l, "weekly card id=70600 row=sat_weekly_zm_gone_a kind=585 target=4 value=4"
                      " route=B")
          and num(rt, "ProgressionTuning.chal.crossN") == 1
          and count_line(l, "chal week cross id=") == 0,
          " | ".join([x for x in l if "chal week cross" in x or " card id=" in x][:3]))

    rt = new_rt(lua51, src=False)
    rt.execute(PRE)
    rt.execute("DROP_FORK()")
    rt.execute("Challenge[xhash('IsChallengeComplete')] = nil")
    rt.execute("SET_WEEK_LIST(70700, '4', 'sat_weekly_zm_nogate_a', 585, 1)")
    rt.execute("SET_G11(222)")
    load(rt)
    pump(rt, 24)
    rt.execute("DROP_WEEK_LIST()")
    pump(rt, 32)
    l = lines_of(rt)
    check("G: with no gate in the VM one line says so and the vanished row is carded as today",
          count_line(l, "chal week gate - no Challenge.IsChallengeComplete in this VM,"
                        " the vanished row is carded") == 1
          and has_line(l, "weekly card id=70700 row=sat_weekly_zm_nogate_a kind=585 target=4 value=4"
                          " route=B"),
          " | ".join([x for x in l if "chal week cross" in x or "chal week gate" in x][:3]))

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


def week_sticker(lua51):
    PRE = SweepStub + """
WSTORE[429] = {}
ASKS = {}
WeeklyChallenge[xhash("getweeklychallengedatabyid")] = function(id)
  ASKS[#ASKS + 1] = id
  return WROW[id]
end
"""
    rt = new_rt(lua51, src=False)
    rt.execute(PRE)
    rt.execute("SET_WEEK(52508, 429, '3', 'sat_sb_zm_freshmeat_1', 1, 1)")
    rt.execute("SET_G11(230)")
    load(rt)
    pump(rt, 24)
    l = lines_of(rt)
    check("G: the sweep asks for the sticker book kind beside the three weeklies",
          num(rt, "ProgressionTuning.chal.sweep.n") == 1
          and int(rt.eval("#ProgressionTuning.chal.sweep.kinds")) == 4
          and num(rt, "ProgressionTuning.chal.sweep.kinds[4]") == 429
          and count_line(l, "chal sweep") == 0,
          " | ".join([x for x in l if "chal sweep" in x][:2]))
    check("G: a sticker book row is never asked for a weekly row",
          rt.eval("#ASKS") == 0, str(rt.eval("#ASKS")))
    rt.execute("SET_WEEK_STATUS(429, 52508, 3, 3)")
    pump(rt, 40)
    l = lines_of(rt)
    check("G: a 429 row that flips complete is carded once on route A with its own kind",
          rt.eval("NAMED('completed_challenge')") == 1
          and int(rt.eval("LASTOF('completed_challenge').kind")) == 429
          and rt.eval("LASTOF('completed_challenge').id") == 52508
          and has_line(l, "daily card id=52508 row=- kind=429 target=3 value=3 route=A")
          and has_line(l, "chal week card id=52508 ref=- kind=429 enabled=nil isweekly=false"
                          " splash=true route=A"),
          " | ".join([x for x in l if " card id=" in x][:2]))
    check("G: and no weekly row is asked for that 429 id even after it is carded",
          rt.eval("#ASKS") == 0, str(rt.eval("#ASKS")))


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
          num(rt, "ProgressionTuning.camo.count['sat_pi_alcor'].base") == 1
          and num(rt, "ProgressionTuning.camo.count['sat_pi_alcor'].special") == 3
          and num(rt, "ProgressionTuning.camo.count['sat_pi_alcor'].mastery") == 1
          and num(rt, "ProgressionTuning.camo.count['sat_pi_alcor'].extra") == 1,
          " | ".join([x for x in l if "camo rows" in x][:2]))
    check("H: a gate row is a requirement, never a watched camo",
          not has_line(l, "camo prime id=68978") and not has_line(l, "camo card id=68978"),
          " | ".join([x for x in l if "68978" in x][:2]))
    check("H: every special and the gold task prime silently",
          rt.eval("ProgressionTuning.camo.seen['68971']") is not None
          and rt.eval("ProgressionTuning.camo.seen['68976']") is not None
          and count_line(l, "camo prime") == 0
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
          num(rt2, "ProgressionTuning.camo.count['sat_me_nashira'].base") == 1
          and num(rt2, "ProgressionTuning.camo.count['sat_me_nashira'].special") == 1
          and num(rt2, "ProgressionTuning.camo.count['sat_me_nashira'].mastery") == 2
          and num(rt2, "ProgressionTuning.camo.count['sat_me_nashira'].extra") == 0,
          " | ".join([x for x in lines_of(rt2) if "camo rows" in x][:2]))

    rt3 = new_rt(lua51, src=False)
    rt3.execute(PRE)
    rt3.execute(NASHIRA_ROWS)
    rt3.execute("SET_CAMO_PROGRESS(69098, 0)")
    rt3.execute("SET_G11(212)")
    rt3.execute("SET_PAID('v1;125186:900:1')")
    load(rt3)
    pump(rt3, 16)
    before = rt3.eval("ProgressionTuning.camo.count['sat_me_nashira']")
    rt3.execute("SET_PAID('v1;125186:900:1;126469:800:1')")
    pump(rt3, 16)
    check("H: a weapon that becomes held mid-match is enumerated then, not at load",
          before is None
          and num(rt3, "ProgressionTuning.camo.count['sat_me_nashira'].base") == 1,
          "%s | %s" % (before, rt3.eval("ProgressionTuning.camo.count['sat_me_nashira']")))

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
          and num(rt4, "ProgressionTuning.camo.count['sat_pi_alcor'].base") == 1
          and num(rt4, "ProgressionTuning.camo.count['sat_pi_alcor'].special") == 0
          and num(rt4, "ProgressionTuning.camo.count['sat_pi_alcor'].mastery") == 1
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
          and num(rt5, "ProgressionTuning.camo.count['sat_pi_alcor'].base") == 1
          and num(rt5, "ProgressionTuning.camo.count['sat_pi_alcor'].special") == 3
          and num(rt5, "ProgressionTuning.camo.count['sat_pi_alcor'].mastery") == 0
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
          num(rt, "ProgressionTuning.ret.n") == 2
          and num(rt, "ProgressionTuning.ret.nzm") == 2
          and num(rt, "ProgressionTuning.ret.kind") == 422
          and num(rt, "ProgressionTuning.ret.rows[1].id") == 66938
          and num(rt, "ProgressionTuning.ret.rows[2].id") == 56892,
          " | ".join([x for x in l if "reticle rows" in x][:1]))
    check("I: the multiplayer optic row is never watched in a Zombies match",
          rt.eval("ProgressionTuning.ret.seen[57777]") is None,
          " | ".join([x for x in l if "57777" in x][:1]))
    check("I: a reticle already past its first target primes silently",
          num(rt, "ProgressionTuning.ret.seen['66938']") == 59
          and count_line(l, "reticle prime") == 0
          and rt.eval("NEVENTS()") == 0, " | ".join([x for x in l if "reticle prime" in x][:2]))
    rt.execute("SET_CAMO_PROGRESS(66938, 200)")
    pump(rt, 40)
    l = lines_of(rt)
    check("I: a reticle tier crossing cards once, with the reticle kind and that row",
          rt.eval("NAMED('completed_challenge')") == 1
          and int(rt.eval("LASTOF('completed_challenge').kind")) == 422
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
          has_line(blk, "Q14 reticle rows n=2 zm=2 kind=422")
          and has_line(blk, "Q14 gate kind=422 id=66938 answer=true")
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
          and num(rt2, "ProgressionTuning.ret.n") == 2
          and num(rt2, "ProgressionTuning.ret.nzm") == 2
          and not has_line(l2, "progression_tuning: error"),
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
    check("I: the rows state carries kind 422 even when the name lookup answers nil",
          num(rt4, "ProgressionTuning.ret.kind") == 422
          and num(rt4, "ProgressionTuning.ret.n") == 2
          and count_line(l4, "reticle rows") == 0
          and not has_line(l4, "no reticle card this match"),
          " | ".join([x for x in l4 if "reticle rows" in x][:1]))
    rt4.execute("SET_CAMO_PROGRESS(66938, 200)")
    pump(rt4, 40)
    check("I: and a crossing cards kind 422 with the row it crossed",
          rt4.eval("NAMED('completed_challenge')") == 1
          and int(rt4.eval("LASTOF('completed_challenge').kind")) == 422
          and rt4.eval("LASTOF('completed_challenge').id") == 66938,
          "%s / %s" % (rt4.eval("NAMED('completed_challenge')"),
                       rt4.eval("LASTOF('completed_challenge').kind")))

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
          and num(rt5, "ProgressionTuning.ret.seen['66938']") == 200
          and count_line(lines_of(rt5), "reticle prime") == 0,
          " | ".join([x for x in lines_of(rt5) if "reticle" in x][:2]))

    rt6 = new_rt(lua51, src=False)
    rt6.execute(PRE)
    rt6.execute("""
SET_MODE_ROW('sat_pi_alcor', 2, 68970, {'100'})
SET_CAMO_PROGRESS(68970, 0)
local i = 1
while i <= 40 do
  SET_RET(66900 + i - 1, 'sat_ch_reticle_zm_sat_row' .. tostring(i), '100|200')
  SET_CAMO_PROGRESS(66900 + i - 1, 0)
  i = i + 1
end
SET_CAMO_PROGRESS(66938, 121)
""")
    rt6.execute("SET_G11(225)")
    rt6.execute("SET_PAID('v1;125186:900:1')")
    load(rt6)
    pump(rt6, 40)
    l6 = lines_of(rt6)
    check("I: the watch window orders by stored progress, so the one row carrying it survives the cap",
          num(rt6, "ProgressionTuning.ret.n") == 36
          and num(rt6, "ProgressionTuning.ret.rows[1].id") == 66938
          and num(rt6, "ProgressionTuning.ret.seen['66938']") == 121
          and count_line(l6, "reticle rows") == 0,
          " | ".join([x for x in l6 if "reticle" in x][:2]))
    rt6.execute("SET_CAMO_PROGRESS(66938, 200)")
    pump(rt6, 40)
    check("I: and a crossing on that row cards kind 422",
          rt6.eval("NAMED('completed_challenge')") == 1
          and int(rt6.eval("LASTOF('completed_challenge').kind")) == 422
          and rt6.eval("LASTOF('completed_challenge').id") == 66938
          and has_line(lines_of(rt6), "reticle card id=66938 row=sat_ch_reticle_zm_sat_row39 target=200"
                                     " route=A value=200 tier=2"),
          "%s / %s" % (rt6.eval("NAMED('completed_challenge')"),
                       rt6.eval("LASTOF('completed_challenge').kind")))

    rt7 = new_rt(lua51, src=False)
    rt7.execute(PRE)
    rt7.execute("""
SET_MODE_ROW('sat_pi_alcor', 2, 68970, {'100'})
SET_CAMO_PROGRESS(68970, 0)
local i = 1
while i <= 40 do
  SET_RET(66900 + i - 1, 'sat_ch_reticle_zm_sat_row' .. tostring(i), '100|200')
  i = i + 1
end
""")
    rt7.execute("SET_G11(226)")
    rt7.execute("SET_PAID('v1;125186:900:1')")
    load(rt7)
    pump(rt7, 40)
    l7 = lines_of(rt7)
    check("I: with no store record on any row the window is the id order, today's",
          num(rt7, "ProgressionTuning.ret.n") == 36
          and num(rt7, "ProgressionTuning.ret.rows[1].id") == 66900
          and count_line(l7, "reticle rows") == 0
          and not has_line(l7, "reticle prime"),
          " | ".join([x for x in l7 if "reticle rows" in x][:1]))


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
          num(rt3, "ProgressionTuning.camo.count['sat_ar_flatline'].special") == 10
          and num(rt3, "ProgressionTuning.camo.count['sat_me_nashira'].special") == 10
          and num(rt3, "ProgressionTuning.camo.count['sat_pi_alcor'].special") == 10
          and num(rt3, "ProgressionTuning.camo.extraN") == 30
          and count_line(l3, "camo rows") == 0,
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
          num(rt, "ProgressionTuning.guns['sat_pi_atlas'].level") == 0, " | ".join(l[-6:]))

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
    pump(rt2, 48)
    check("cf: a prestige camo on the 650th weapon is in the map, past the old 600 cap",
          rt2.eval("ASK_L(140810)") is False, str(rt2.eval("ASK_L(140810)")))
    check("cf: and the map says how many weapons it walked",
          has_line(lines_of(rt2), "the weapon ladders name 1 prestige camo ids over 700 weapons"),
          " | ".join([x for x in lines_of(rt2) if "prestige camo ids over" in x][:2]))

    rt3 = capped(2100)
    pump(rt3, 140)
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
    check("cf: and the rebuild that re-reads the bitmap never re-asks it",
          int(rt5.eval("BUNDLECALLS")) == 1, str(rt5.eval("BUNDLECALLS")))

    scope4 = sorted(ls)[:4]
    rt6 = new_rt(lua51, frontend=True, src=False)
    lua_slabs(rt6, slabs_of(scope4 + [160001]))
    lua_rslabs(rt6, slabs_of([scope4[1], scope4[3]]))
    rt6.execute("SET_G11(206)")
    rt6.execute("SET_G12(2)")
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
          num(rt, "ProgressionTuning.camo.rows['sat_pi_atlas'].id") == 57201
          and num(rt, "ProgressionTuning.camo.rows['sat_pi_atlas'].n") == 3,
          " | ".join([x for x in l if "camo watch" in x][:3]))


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


UTCFILLFIX = r"""
UTC_SEEN = 0
UTC_N = 0
CoD = { GetUTC = function() return 1763520000 end }
Engine[xhash("GetUTC")] = function(...)
  UTC_SEEN = UTC_SEEN + 1
  UTC_N = select("#", ...)
  return nil
end
"""


UTC_KEY_MT = r"""
CLUA = { PushXHash = function(n) return xhash(n) end }
Engine[xhash("GetUTC")] = function() return nil end
setmetatable(Engine, { __index = function(t, k)
  if type(k) == "string" then return rawget(t, xhash(k)) end
  return nil
end })
"""

UTC_KEY_OTHER = r"""
CLUA = { PushXHash = function(n) return xhash(n) end }
OTHERUTC = function() return "other" end
Engine[xhash("GetUTC")] = OTHERUTC
Engine.GetUTC = function() return nil end
"""


def utc_fill(lua51):
    """The clock fill: a nil is answered by the cod getter, a number passes through whole."""
    ra = new_rt(lua51, frontend=True, src=False)
    ra.execute(UTCFILLFIX)
    load(ra)
    la = lines_of(ra)
    check("utcfill: one arm line per vm, and the nil the original answers becomes the cod number",
          count_line(la, "progression_tuning: utc fill armed") == 1
          and count_line(la, "utc fill ") == 1
          and ra.eval('Engine[xhash("GetUTC")]()') == 1763520000
          and ra.eval("UTC_SEEN") == 1,
          "%s | %s" % (ra.eval('Engine[xhash("GetUTC")]()'),
                       " | ".join([x for x in la if "utc fill" in x][:3])))
    check("utcfill: the wrapper sits under the hash key it was found by and no plain name appears",
          ra.eval('Engine["GetUTC"]') is None and ra.eval('Engine[xhash("GetUTC")]') is not None,
          "%s / %s" % (ra.eval('Engine["GetUTC"]'), ra.eval('Engine[xhash("GetUTC")]')))
    ra.eval('Engine[xhash("GetUTC")](7, "b", nil)')
    check("utcfill: every argument reaches the original that was wrapped",
          ra.eval("UTC_N") == 3, str(ra.eval("UTC_N")))

    rb = new_rt(lua51, frontend=True, src=False)
    rb.execute('CoD = { GetUTC = function() return 7 end }')
    rb.execute('Engine[xhash("GetUTC")] = function() error("boom utc", 0) end')
    load(rb)
    check("utcfill: an original that raises is filled, and the raise never reaches the caller",
          rb.eval('Engine[xhash("GetUTC")]()') == 7,
          str(rb.eval('pcall(function() return Engine[xhash("GetUTC")]() end)')))

    rz = new_rt(lua51, frontend=True, src=False)
    rz.execute('Engine[xhash("GetUTC")] = function() return nil end')
    load(rz)
    check("utcfill: with no cod getter a nil clock is answered 0",
          rz.eval('Engine[xhash("GetUTC")]()') == 0, str(rz.eval('Engine[xhash("GetUTC")]()')))

    rs = new_rt(lua51, frontend=True, src=False)
    rs.execute('CoD = { GetUTC = function() return "soon" end }')
    rs.execute('Engine[xhash("GetUTC")] = function() return nil end')
    load(rs)
    check("utcfill: a cod answer that is not a number is answered 0",
          rs.eval('Engine[xhash("GetUTC")]()') == 0, str(rs.eval('Engine[xhash("GetUTC")]()')))

    rp = new_rt(lua51, frontend=True, src=False)
    rp.execute('CoD = { GetUTC = function() return 1 end }')
    rp.execute('Engine[xhash("GetUTC")] = function() return 5, "b", nil, "d" end')
    load(rp)
    rp.execute('UP_N = select("#", Engine[xhash("GetUTC")]())')
    rp.execute("UP_A, UP_B, UP_C, UP_D = Engine[xhash(\"GetUTC\")]()")
    check("utcfill: a number clock comes back with all four of its returns, the nil one too",
          rp.eval("UP_N") == 4 and rp.eval("UP_A") == 5 and rp.eval("UP_B") == "b"
          and rp.eval("UP_C") is None and rp.eval("UP_D") == "d",
          "%s %s %s %s %s" % (rp.eval("UP_N"), rp.eval("UP_A"), rp.eval("UP_B"),
                              rp.eval("UP_C"), rp.eval("UP_D")))
    check("utcfill: and the cod getter was never asked while the original answered",
          count_line(lines_of(rp), "utc fill armed") == 1
          and rp.eval("UP_A") == 5,
          "%s %s" % (rp.eval("UP_A"), count_line(lines_of(rp), "utc fill armed")))

    rn = new_rt(lua51, frontend=True, src=False)
    rn.execute("Engine.GetUTC = function() return nil end")
    rn.execute('CoD = { GetUTC = function() return 33 end }')
    load(rn)
    check("utcfill: a table that keeps the plain name is filled in place",
          rn.eval("Engine.GetUTC()") == 33, str(rn.eval("Engine.GetUTC()")))

    km = new_rt(lua51, frontend=True, src=False)
    km.execute(UTC_KEY_MT)
    load(km)
    check("utcfill: a plain name reached through a metatable is filled, and the pushed and hashed keys too",
          km.eval('Engine[xhash("GetUTC")]()') == 0
          and km.eval('Engine["GetUTC"]') is not None
          and km.eval('Engine[xhash("GetUTC")] == Engine.GetUTC') is True
          and count_line(lines_of(km), "utc fill armed") == 1,
          "%s / %s" % (km.eval('Engine[xhash("GetUTC")]()'),
                       km.eval('Engine[xhash("GetUTC")] == Engine.GetUTC')))

    ko = new_rt(lua51, frontend=True, src=False)
    ko.execute(UTC_KEY_OTHER)
    load(ko)
    check("utcfill: a pushed key holding another function is never overwritten",
          ko.eval('Engine[xhash("GetUTC")] == OTHERUTC') is True
          and ko.eval('Engine[xhash("GetUTC")]()') == "other"
          and ko.eval('Engine.GetUTC()') == 0,
          "%s / %s" % (ko.eval('Engine[xhash("GetUTC")]()'), ko.eval("Engine.GetUTC()")))

    kn = new_rt(lua51, frontend=True, src=False)
    kn.execute('CoD = { GetUTC = function() return 44 end }')
    kn.execute("Engine.GetUTC = function() return nil end")
    load(kn)
    check("utcfill: with no loader table the found member alone is filled and nothing raises",
          kn.eval("Engine.GetUTC()") == 44
          and count_line(lines_of(kn), "progression_tuning: utc fill armed") == 1,
          "%s" % kn.eval("Engine.GetUTC()"))

    rx = new_rt(lua51, frontend=True)
    lx = lines_of(rx)
    check("utcfill: a vm whose engine has no getter says absent once and wraps nothing",
          count_line(lx, "progression_tuning: utc fill absent") == 1
          and count_line(lx, "utc fill armed") == 0
          and rx.eval('Engine[xhash("GetUTC")]') is None,
          " | ".join([x for x in lx if "utc fill" in x][:3]))

    re = new_rt(lua51, frontend=True, src=False)
    re.execute("Engine = nil")
    re.execute(LUA_TEXT[CHALLENGES])
    check("utcfill: with no engine table at all it arms absent and raises nothing",
          count_line(lines_of(re), "progression_tuning: utc fill absent") == 1,
          " | ".join([x for x in lines_of(re) if "utc fill" in x][:3]))

    rd = new_rt(lua51, frontend=True, src=False)
    rd.execute(UTCFILLFIX)
    load(rd)
    rd.execute('F1 = Engine[xhash("GetUTC")]')
    load(rd)
    rd.execute('F2 = Engine[xhash("GetUTC")]')
    rd.execute("UTC_SEEN = 0")
    rd.execute('Engine[xhash("GetUTC")]()')
    ld = lines_of(rd)
    check("utcfill: a second chunk run wraps nothing twice - the same function, one call through",
          rd.eval("F1 == F2") is True and rd.eval("UTC_SEEN") == 1
          and count_line(ld, "utc fill armed") == 1,
          "same=%s seen=%s arms=%d" % (rd.eval("F1 == F2"), rd.eval("UTC_SEEN"),
                                       count_line(ld, "utc fill armed")))


def ch_of(rt):
    """The token channel's own string in this vm."""
    v = rt.eval('DVARS[xhashdvar("pt_tokens_ch")]')
    return None if v is None else str(v)


def options_rows(lua51):
    """The two rows the debug tab gains: their place, their labels and what the page does with them."""
    rt = new_rt(lua51, pre=OPTIONSFIX)
    tab, other = '{ 7, "debug" }', '{ "not", "the debug tab" }'
    check("opts: the rows part arms against a page holding all four members",
          rt.eval("ProgressionTuning.probes.options()") is True, " | ".join(lines_of(rt)[-3:]))
    rt.execute('W1 = OPTIONS["#x7bf7f57679e8d050"]')
    rt.execute("NRET = select('#', W1(%s, 0, 1))" % tab)
    check("opts: the list member keeps every return the page gave it", int(rt.eval("NRET")) == 2,
          str(rt.eval("NRET")))
    check("opts: the list member appends both rows to the debug tab",
          int(rt.eval("#LIST")) == 5
          and rt.eval('LIST[4][xhash("settingId")]') == "pt_token_amount"
          and rt.eval('LIST[5][xhash("settingId")]') == "pt_permanent",
          "%s rows" % rt.eval("#LIST"))
    rt.execute("W1(%s, 0, 1)" % tab)
    check("opts: and appends them once - a second build of the same list adds nothing",
          int(rt.eval("#LIST")) == 5 and count_line(lines_of(rt), "options row added") <= 1,
          "%s rows" % rt.eval("#LIST"))
    rt.execute("W1(%s, 0, 1)" % other)
    check("opts: and adds nothing to a list that is not the debug tab",
          int(rt.eval("#LIST")) == 5 and count_line(lines_of(rt), "options row added") <= 1)

    rt.execute('OPTIONS[xhash("createoptionlist")](nil, nil, LIST, false)')
    ids = [rt.eval('LIST[%d][xhash("settingId")]' % i) for i in range(1, 6)]
    check("opts: the page build moves both rows to sit directly after the anchor",
          ids == ["#x7a1b0000000000a1", "0x5a6d0000000000be", "pt_token_amount",
                  "pt_permanent", "#x2c9f0000000000d4"], " | ".join(ids))

    rt.execute('DR = OPTIONS["#xe7686f7a9907efd8"]')
    rt.execute('TROW = DR("pt_token_amount", 0)')
    rt.execute('PROW = DR("pt_permanent", 0)')
    check("opts: the dropdown row carries its own id, its six labels and its kind",
          rt.eval('TROW[xhash("settingId")]') == "pt_token_amount"
          and rt.eval('TROW[xhash("label")]') == "XP Token Amount"
          and [rt.eval('TROW[xhash("labels")][%d]' % i) for i in range(1, 7)]
          == ["0", "1", "5", "10", "25", "99"]
          and rt.eval('TROW[xhash("widgetType")]') == "Dropdown",
          str(rt.eval('TROW[xhash("labels")]')))
    check("opts: the toggle row carries its own id, its two labels and its kind",
          rt.eval('PROW[xhash("settingId")]') == "pt_permanent"
          and [rt.eval('PROW[xhash("labels")][%d]' % i) for i in range(1, 3)] == ["Off", "On"]
          and rt.eval('PROW[xhash("widgetType")]') == "ToggleButton",
          str(rt.eval('PROW[xhash("labels")]')))
    check("opts: every other id is the page's own answer",
          rt.eval('DR("#x7a1b0000000000a1", 0)[xhash("settingId")]') == "#x7a1b0000000000a1"
          and rt.eval('ProgressionTuning.tokens.csrc') == "chan")

    check("opts: the dropdown answers the 1-based index of the lowest current count",
          int(rt.eval('TROW[xhash("getter")](0)')) == 1, str(rt.eval('TROW[xhash("getter")](0)')))
    rt.execute('TROW[xhash("setter")](0, 3)')
    check("opts: and the index it is handed writes that count to every slot, on the channel",
          int(rt.eval('TROW[xhash("getter")](0)')) == 3
          and ch_of(rt) == "p=0;w=0;n=2;c=5,5,5,5,5,5,5,5;x=0", str(ch_of(rt)))
    check("opts: the toggle answers 1 while the flag is off",
          int(rt.eval('PROW[xhash("getter")](0)')) == 1)
    rt.execute('PROW[xhash("setter")](0, 2)')
    check("opts: and 2 once it is set on, with the flag on the channel",
          int(rt.eval('PROW[xhash("getter")](0)')) == 2
          and str(ch_of(rt)).endswith(";x=1"), str(ch_of(rt)))
    rt.execute('PROW[xhash("setter")](0, 1)')
    check("opts: and 1 again when it is set back to off",
          int(rt.eval('PROW[xhash("getter")](0)')) == 1
          and str(ch_of(rt)).endswith(";x=0"), str(ch_of(rt)))
    rt.execute("MenuBuilder.BuildRegisteredType('a', {})")
    rt.execute("MenuBuilder.BuildRegisteredType('a', {})")
    check("opts: every page build re-arms and leaves the wrapper it installed in place",
          rt.eval('OPTIONS["#x7bf7f57679e8d050"] == W1') is True and int(rt.eval("BUILT")) == 2,
          str(rt.eval("BUILT")))

    rm = new_rt(lua51)
    check("opts: with no page at all the part arms nothing and moves nothing",
          rm.eval("ProgressionTuning.probes.options()") is False
          and count_line(lines_of(rm), "options move raised") == 0)


def options_layers(lua51):
    """The debug page through both layers: one of every row, whether we hold the slot or sit under it."""
    dbg = ["#x3" + h for h in ("5a6d0000000000a1", "5a6d0000000000be", "5a6d0000000000aa")]
    stock = ["5a6d0000000000a1", "5a6d0000000000be", "5a6d0000000000aa"]
    dead = "3f58d23122dd68ae"
    token, perm = "pt_token_amount", "pt_permanent"
    trow, prow = token + "|XP Token Amount|Dropdown", perm + "|Enable Double XP|ToggleButton"
    da, db = "#xe7686f7a9907efd8", "#x9f6c4b08602983fb"

    def data(rt):
        return [str(rt.eval('DLBL("%s", "%s")' % (m, i))) for m in (da, db) for i in (token, perm)]

    rt = new_rt(lua51, pre=OPTIONSLAY)
    inner = str(rt.eval("K1LIST()")).split(",")
    check("opts: the inner layer puts its own rows above the stock ones and drops the dead one",
          len(inner) == 6 and [inner.count(i) for i in dbg] == [1, 1, 1]
          and all(s in inner for s in stock) and dead not in inner, " | ".join(inner))

    top = str(rt.eval("PAGELIST()")).split(",")
    check("opts: holding the slot, the rebuild above and the stock rows below are on the page once each",
          top == [dbg[0], dbg[1], token, perm, dbg[2]] + stock, " | ".join(top))
    check("opts: holding the slot, our two rows answer their own bundle",
          data(rt) == [trow, prow, trow, prow], " | ".join(data(rt)))

    rb = new_rt(lua51, pre=OPTIONSLAY)
    rb.execute("KRONOSHOOK()")
    check("opts: the page's second layer takes the slot over ours",
          rb.eval("OPTIONS[SKSECT] == KHOOKS[SKSECT]") is True
          and rb.eval("OPTIONS[SKSECT] ~= K1") is True)
    buried = str(rb.eval("PAGELIST()")).split(",")
    check("opts: under that layer, the stock rows are on the page once and our two once",
          buried == [dbg[0], dbg[1], token, perm, dbg[2]], " | ".join(buried))
    check("opts: and under that layer our two rows still answer their own bundle",
          data(rb) == [trow, prow, trow, prow], " | ".join(data(rb)))

    rb.execute("KRONOSHOOK()")
    builds = [str(rb.eval("PAGELIST()")) for _ in range(3)]
    check("opts: rebuilds and a repeat hook leave one of every row",
          [b.split(",") for b in builds] == [buried] * 3, " | ".join(builds))


def tokens_channel(lua51):
    """The token channel: what it reads, what it writes and what another vm's write does."""
    full = "p=600;w=1200;n=42;c=1,2,3,4,5,6,7,8;x=1"
    rt = new_rt(lua51, pre='SET_DVAR("pt_tokens_ch", "%s")' % full)
    check("tok: a full line is read into its five fields, counts in channel order",
          int(rt.eval("ProgressionTuning.tokens.p")) == 600
          and int(rt.eval("ProgressionTuning.tokens.w")) == 1200
          and int(rt.eval("ProgressionTuning.tokens.sn")) == 42
          and int(rt.eval("ProgressionTuning.tokens.x")) == 1
          and [int(rt.eval("ProgressionTuning.tokens.c[%d]" % i)) for i in range(1, 9)]
          == [1, 2, 3, 4, 5, 6, 7, 8]
          and rt.eval("ProgressionTuning.tokens.csrc") == "chan", str(ch_of(rt)))
    check("tok: and the part does not write over it while nothing moves",
          ch_of(rt) == full, str(ch_of(rt)))
    rt.execute("ProgressionTuning.tokens.perm(true)")
    check("tok: a write keeps every field and rises the serial",
          ch_of(rt) == "p=600;w=1200;n=43;c=1,2,3,4,5,6,7,8;x=1", str(ch_of(rt)))
    check("tok: the line the writer produces is inside the dll's own charset and size",
          re.match(r"^[a-z0-9=;,]+$", str(ch_of(rt))) is not None and len(str(ch_of(rt))) <= 512,
          str(ch_of(rt)))
    unk = "p=11;w=22;n=30;c=1,2,3,4,5,6,7,8;x=0;z=7"
    rk = new_rt(lua51, pre='SET_DVAR("pt_tokens_ch", "%s")' % unk)
    check("tok: a field this build does not parse is ignored by the read",
          int(rk.eval("ProgressionTuning.tokens.p")) == 11
          and int(rk.eval("ProgressionTuning.tokens.sn")) == 30
          and int(rk.eval("ProgressionTuning.tokens.c[1]")) == 1, str(ch_of(rk)))
    rk.execute("ProgressionTuning.tokens.perm(true)")
    check("tok: and dropped by the next write, which rebuilds the line from its own fields",
          ch_of(rk) == "p=11;w=22;n=31;c=1,2,3,4,5,6,7,8;x=1" and "z=" not in str(ch_of(rk)),
          str(ch_of(rk)))

    rseed = new_rt(lua51, pre="CLR_DVAR('pt_tokens_ch') " + TOKENREC)
    check("tok: a line with no counts seeds the eight slots from the client's own record",
          [int(rseed.eval("ProgressionTuning.tokens.c[%d]" % i)) for i in range(1, 9)]
          == [1, 2, 3, 4, 5, 6, 7, 8]
          and rseed.eval("ProgressionTuning.tokens.csrc") == "seed"
          and count_line(lines_of(rseed), "tokens P4") == 0,
          " | ".join([x for x in lines_of(rseed) if "tokens P4" in x][:3]))
    rnone = new_rt(lua51, pre="CLR_DVAR('pt_tokens_ch')")
    check("tok: with no channel and no record there is nothing to seed and nothing written",
          rnone.eval("ProgressionTuning.tokens.c") is None and ch_of(rnone) in (None, ""),
          str(ch_of(rnone)))

    foreign = "p=300;w=900;n=57;c=2,3,4,5,6,7,8,1;x=1"
    rp = new_rt(lua51, pre='SET_DVAR("pt_tokens_ch", "%s")' % full)
    pump(rp, 1)
    rp.execute('SET_DVAR("pt_tokens_ch", "%s")' % foreign)
    pump(rp, 1)
    check("tok: a serial another vm wrote is adopted on the next tick, with its counts",
          int(rp.eval("ProgressionTuning.tokens.sn")) == 57
          and int(rp.eval("ProgressionTuning.tokens.p")) == 300
          and int(rp.eval("ProgressionTuning.tokens.w")) == 900
          and int(rp.eval("ProgressionTuning.tokens.x")) == 1
          and int(rp.eval("ProgressionTuning.tokens.c[1]")) == 2
          and rp.eval("ProgressionTuning.tokens.csrc") == "chan", str(ch_of(rp)))
    pump(rp, 1)
    check("tok: and the same serial is not adopted a second time",
          int(rp.eval("ProgressionTuning.tokens.sn")) == 57, str(ch_of(rp)))

    ro = new_rt(lua51, frontend=True, src=False, pre="SET_TOGGLE('pt_on', 0)")
    ro.execute(UTCFILLFIX)
    load(ro)
    check("utcfill: the fill arms with every toggle off, because it only fills a nil",
          ro.eval('Engine[xhash("GetUTC")]()') == 1763520000
          and count_line(lines_of(ro), "progression_tuning: utc fill armed") == 1,
          str(ro.eval('Engine[xhash("GetUTC")]()')))
ARMORY_FIX = r"""
UTC = 0
GATE_CALLS = 0
PRESS_CALLS = 0
FOCUS_CALLS = 0
PRESS_RAISE = false
OC_RAISE = false
OCREC = {}
OC_ORIG = OnlineChallenges[xhash("getchallengeprogress")]
OnlineChallenges[xhash("getchallengeprogress")] = function(c, id)
  if OC_RAISE then error("client record raised") end
  local r = OCREC[tostring(id)]
  if r ~= nil then return r end
  return OC_ORIG(c, id)
end
Dvar[xhash("SetDvarString")] = function(k, v) if DVARS[k] ~= nil then DVARS[k] = v end end
GATEKEY = "#x0A6376439B2D40DC"
CoD = {}
CoD[xhash("GetUTC")] = function() return UTC end
function NODE(v) return { GetValue = function(self, c) return v end } end
function HNODE(v) return { [xhash("GetValue")] = function(self, c) return v end } end
function UDMODEL(achv, ref)
  local p = newproxy(true)
  local raw = { [xhash("armory_button_data")] = { [xhash("achievement_id")] = NODE(achv) } }
  if ref ~= nil then raw[xhash("item_ref")] = NODE(ref) end
  getmetatable(p).__index = raw
  return p
end
function TILE(achv, ref)
  local t = { armory_button_data = { achievement_id = NODE(achv) } }
  if ref ~= nil then t.item_ref = NODE(ref) end
  return t
end
function TREE()
  local src = {}
  src[xhash("frontend")] = {}
  src[xhash("frontend")][xhash("armory")] = {}
  return src
end
ARMORY = {}
ORIG = function(c, row)
  GATE_CALLS = GATE_CALLS + 1
  if not row then return false end
  local start = row.progressSchedule_start
  if start == nil or tostring(start) == "" then return true end
  return tonumber(start) < CoD[xhash("GetUTC")]()
end
ARMORY[GATEKEY] = ORIG
ARMORY[xhash("setactiveitem")] = function(menu, c)
  PRESS_CALLS = PRESS_CALLS + 1
  if PRESS_RAISE then error("client press raised") end
  return "client-ret", 7
end
ARMORY[xhash("setfocuseddatasource")] = function(c, tile) FOCUS_CALLS = FOCUS_CALLS + 1 end
_DataSources = TREE()
function SIDE() return _DataSources[xhash("frontend")][xhash("armory")] end
function SET_FOCUS(id, ref) SIDE()[xhash("armory_select_focus_item")] = NODE(TILE(id, ref)) end
function SET_ACTIVE(id, ref) SIDE()[xhash("armory_active_item")] = NODE(TILE(id, ref)) end
function SET_HNODE(id, ref) SIDE()[xhash("armory_select_focus_item")] = HNODE(TILE(id, ref)) end
function SET_UD(id, ref) SIDE()[xhash("armory_select_focus_item")] = NODE(UDMODEL(id, ref)) end
function SET_PLAIN(id, ref)
  _DataSources = { frontend = { armory = { armory_select_focus_item = NODE(TILE(id, ref)) } } }
end
function CLR_FOCUS() _DataSources = TREE() end
function EL(id, ref) return { GetDataSource = function() return TILE(id, ref) end } end
function ROW(id, start) return { id = id, progressSchedule_start = start } end
function ASK(id, start) return ARMORY[GATEKEY](0, ROW(id, start)) end
function ASK_ORIG(id, start) return ORIG(0, ROW(id, start)) end
function ASKC() return GATE_CALLS end
function SNAP()
  SNAPED = ARMORY[GATEKEY]
  SNAPP = ARMORY[xhash("setactiveitem")]
  SNAPO = OnlineChallenges[xhash("getchallengeprogress")]
end
function SAME()
  return ARMORY[GATEKEY] == SNAPED and ARMORY[xhash("setactiveitem")] == SNAPP
    and OnlineChallenges[xhash("getchallengeprogress")] == SNAPO
end
function SET_UTC(v) UTC = v end
PKEY = nil
function PADPRESS()
  local k = xhash("setactiveitem")
  local v = ARMORY[k]
  ARMORY[k] = nil
  PKEY = "#x00" .. string.sub(k, 3)
  ARMORY[PKEY] = v
end
function PRESS(el)
  local a, b = ARMORY[PKEY or xhash("setactiveitem")](el or {}, 0)
  return tostring(a) .. "," .. tostring(b)
end
function PRESS_EL(id, ref) return PRESS(EL(id, ref)) end
function PRESSCALLS() return PRESS_CALLS end
function TRYPRESS() return (pcall(ARMORY[xhash("setactiveitem")], {}, 0)) end
function PRESSERR()
  local ok, err = pcall(ARMORY[xhash("setactiveitem")], {}, 0)
  return tostring(err)
end
function HOVER(ds) return ARMORY[xhash("setfocuseddatasource")](0, { GetDataSource = function() return ds end }) end
function FOCUSED() return FOCUS_CALLS end
CRAFTLOCK = {}
CLK_CALLS = 0
CLK_RAISE = false
PurchaseMenuUtils = {}
PurchaseMenuUtils.isitemlocked = function(c, item)
  CLK_CALLS = CLK_CALLS + 1
  if CLK_RAISE then error("the game lock raised") end
  if type(item) ~= "table" or item.itemref == nil then return false end
  return CRAFTLOCK[item.itemref] == true
end
function SET_CRAFT(ref, locked) CRAFTLOCK[ref] = locked end
function CRAFT_N() return CLK_CALLS end
function CRAFT_ZERO() CLK_CALLS = 0 end
function CRAFT_RAISE(v) CLK_RAISE = v end
function CRAFT_LOCK() return PurchaseMenuUtils.isitemlocked or PurchaseMenuUtils[xhash("isitemlocked")] end
function CRAFT_ASK(ref) return CRAFT_LOCK()(0, { itemref = ref }) end
function CRAFT_HASHED()
  local k = xhash("isitemlocked")
  PurchaseMenuUtils[k] = PurchaseMenuUtils.isitemlocked
  PurchaseMenuUtils.isitemlocked = nil
end
function CRAFT_SNAP() CRAFTW = CRAFT_LOCK() end
function CRAFT_SAME() return CRAFT_LOCK() == CRAFTW end
function CRAFT_DROP() PurchaseMenuUtils = nil end
function OC_PUT(id, rec) OCREC[tostring(id)] = rec end
function OC_ASK(id) return OnlineChallenges[xhash("getchallengeprogress")](0, id) end
function OC_TRY(id) return (pcall(OnlineChallenges[xhash("getchallengeprogress")], 0, id)) end
function OC_ERR(id)
  local ok, err = pcall(OnlineChallenges[xhash("getchallengeprogress")], 0, id)
  return tostring(err)
end
function OC_LAST(id)
  local r = OC_ASK(id)
  if type(r) ~= "table" or type(r.progress) ~= "table" then return "none" end
  return tostring(r.progress.last_activation)
end
function OC_CLIENT_LAST(id)
  local r = OCREC[tostring(id)]
  if type(r) ~= "table" or type(r.progress) ~= "table" then return "none" end
  return tostring(r.progress.last_activation)
end
function OC_DEFAULTS(id)
  local r = OC_ASK(id)
  if type(r) ~= "table" or type(r.progress) ~= "table" then return "none" end
  return tostring(r.progress.default)
end
function OC_ID(id)
  local r = OC_ASK(id)
  if type(r) ~= "table" then return "none" end
  return tostring(r.id)
end
function OC_OWN(id) return OC_ASK(id) == OCREC[tostring(id)] end
function CH() return DVARS[xhashdvar("pt_armory_ch")] end
function CH_ABSENT() DVARS[xhashdvar("pt_armory_ch")] = nil end
function PICK() return rawget(_G, "ProgressionTuning").probes.armory() end
OWNEDN = 0
PROXY_LOOT = {}
PROXY_LOOT[xhash("IsOwned")] = function(c, id) OWNEDN = OWNEDN + 1; return 1 end
function OWNED_GET()
  local t = PROXY_LOOT
  if type(t) ~= "table" then return nil end
  local f = t[xhash("IsOwned")]
  if type(f) == "function" then return f end
  return t.IsOwned
end
function OWNED(id) return OWNED_GET()(0, id) end
function OWNED_N() return OWNEDN end
function OWNED_ZERO() OWNEDN = 0 end
function OWNED_SNAP() OW1 = OWNED_GET() end
function OWNED_SAME() return OWNED_GET() == OW1 end
function OWNED_PLAIN()
  PROXY_LOOT = {}
  PROXY_LOOT.IsOwned = function(c, id) OWNEDN = OWNEDN + 1; return 1 end
end
function OWNED_BOTH()
  PROXY_LOOT = {}
  PROXY_LOOT[xhash("IsOwned")] = function(c, id) OWNEDN = OWNEDN + 1; return 1 end
  PROXY_LOOT.IsOwned = function(c, id) return 99 end
end
function OWNED_PLAIN_ASK(id) return PROXY_LOOT.IsOwned(0, id) end
function OWNED_RAISE(v)
  PROXY_LOOT[xhash("IsOwned")] = function(c, id)
    if v then error("the ownership getter raised") end
    return 1
  end
end
function OWNED_DROP() PROXY_LOOT = nil end
function DOORSTUB()
  rawget(_G, "ProgressionTuning").locks = {
    answer = function(id) return false end,
    open = function(id) return false end,
  }
end
function OWNSPROBE(ids)
  for i = 1, #ids do
    if ids[i] and 0 < PROXY_LOOT[xhash("IsOwned")](0, ids[i]) then return true end
  end
  return false
end
ITEMID = {}
BPID = {}
BPRAISE = false
BPN = 0
function SET_ITEMID(ref, id) ITEMID[ref] = id end
function SET_BPID(ref, ids) BPID[ref] = ids end
function BP_RAISE(v) BPRAISE = v end
function BP_N() return BPN end
function BP_ZERO() BPN = 0 end
function DROP_BP() PROGRESSION[xhash("ownsBlueprintOfWeapon")] = nil end
function DROP_ID() LOOT[xhash("getitemid")] = nil end
LOOT[xhash("getitemid")] = function(ref) return ITEMID[ref] end
PROGRESSION[xhash("ownsBlueprintOfWeapon")] = function(c, ref)
  BPN = BPN + 1
  if BPRAISE then error("the blueprint test raised") end
  local ids = BPID[ref]
  if ids == nil then return false end
  local f = PROXY_LOOT[xhash("IsOwned")]
  for i = 1, #ids do
    if f ~= nil and 0 < f(c, ids[i]) then return true end
  end
  return false
end
BP_ORIG = PROGRESSION[xhash("ownsBlueprintOfWeapon")]
function OBW_SLOT()
  local f = PROGRESSION[xhash("ownsBlueprintOfWeapon")]
  if type(f) == "function" then return f end
  return PROGRESSION.ownsBlueprintOfWeapon
end
function OBW(ref) return OBW_SLOT()(0, ref) end
function OBW_ORIG(ref) return BP_ORIG(0, ref) end
function OBW_SNAP() OBW1 = OBW_SLOT() end
function OBW_SAME() return OBW_SLOT() == OBW1 end
function OBW_PLAIN()
  local f = PROGRESSION[xhash("ownsBlueprintOfWeapon")]
  PROGRESSION.ownsBlueprintOfWeapon = f
  PROGRESSION[xhash("ownsBlueprintOfWeapon")] = nil
end
"""

ARMORY_RAISE = r"""
GATEKEY = "#x0A6376439B2D40DC"
CALLS = 0
ARMORY = {}
ARMORY[GATEKEY] = function(c, row)
  CALLS = CALLS + 1
  error("gate blew up")
end
function ROW(id, start) return { id = id, progressSchedule_start = start } end
function ASK(id, start) return ARMORY[GATEKEY](0, ROW(id, start)) end
function TRYOK(id, start) return (pcall(ARMORY[GATEKEY], 0, ROW(id, start))) end
function TRYERR(id, start)
  local ok, err = pcall(ARMORY[GATEKEY], 0, ROW(id, start))
  return tostring(err)
end
function ASKC() return CALLS end
"""


def lock_word():
    """The arm line's lock field: alphabetical order arms the part before the door exists."""
    return "missing" if LOAD_ORDER == "alphabetical" else "wrapped"


def armory_line(lines):
    return [ln for ln in lines if "armory armed" in ln]


def armory_gate(lua51):
    rt = new_rt(lua51, frontend=True, pre=ARMORY_FIX)
    l = lines_of(rt)
    check("armory: the schedule gate is wrapped and the one arm line names the count",
          armory_line(l) == ["progression_tuning: armory armed v12 vm=menu gate=wrapped pick=wrapped "
                             "answer=wrapped lock=%s own=wrapped vars=147+309 craft=n/a "
                             "card=missing rows=76 pick=0 q=0" % lock_word()],
          " | ".join(armory_line(l)))
    hook = rt.eval("rawget(_G, 'ProgressionTuning').hooks.armory")
    check("armory: it arms on its own lui timer and main registers no hook for it",
          "GetRoot" in LUA_TEXT[ARMORY] and "onComplete" in LUA_TEXT[ARMORY]
          and "S.hooks.armory" not in SRC and "armory" not in LUA_TEXT[MAIN]
          and hook is None, "hook=%s" % str(hook))
    check("armory: the client's own gate refuses the row - a future stamp over a zero clock",
          rt.eval("ASK_ORIG(69316, '1793811600')") is False
          and int(rt.eval("ASKC()")) == 1, str(rt.eval("ASKC()")))
    check("armory: the wrapped gate answers released for that same row",
          rt.eval("ASK(69316, '1793811600')") is True)
    check("armory: and answers released for the last of the 76 as well",
          rt.eval("ASK(71374, '1793811600')") is True)
    other = rt.eval("ASK(54499, '1793811600')")
    blank = rt.eval("ASK(54499, '')")
    check("armory: a row outside the 76 keeps the client's own answer",
          other is False and blank is True, "%s / %s" % (other, blank))
    check("armory: the original is asked once per delegated row and never for ours",
          int(rt.eval("ASKC()")) == 3, str(rt.eval("ASKC()")))

    rt.execute("SNAP()")
    before = len(lines_of(rt))
    load(rt)
    l2 = lines_of(rt)
    check("armory: loading the file twice wraps nothing twice and says nothing again",
          rt.eval("SAME()") is True and len(l2) == before
          and len(armory_line(l2)) == 1, " | ".join(armory_line(l2)))
    calls = int(rt.eval("ASKC()"))
    rt.execute("ASK(54499, '1793811600')")
    check("armory: and a delegated row still reaches the original exactly once",
          int(rt.eval("ASKC()")) - calls == 1, str(int(rt.eval("ASKC()")) - calls))

    rt2 = new_rt(lua51, frontend=True, pre=ARMORY_RAISE)
    check("armory: an armory row is answered even where the client's gate raises",
          rt2.eval("ASK(69316, '1')") is True)
    check("armory: a raising gate on any other row gives the client's own refusal, not an error",
          rt2.eval("TRYOK(54499, '1')") is True and rt2.eval("ASK(54499, '1')") is False,
          "%s / %s" % (rt2.eval("TRYOK(54499, '1')"), rt2.eval("ASK(54499, '1')")))

    # the match vm: the same gate and answer, and the pick the hook left in the channel
    rt3 = new_rt(lua51, frontend=False, pre=ARMORY_FIX + "\nSET_DVAR('pt_armory_ch', 'a=69318')")
    l3 = lines_of(rt3)
    check("armory: a match vm arms on the same gate and answer and says which vm it is",
          armory_line(l3) == ["progression_tuning: armory armed v12 vm=match gate=wrapped pick=wrapped "
                              "answer=wrapped lock=%s own=wrapped vars=147+309 craft=wrapped "
                              "card=missing rows=76 pick=69318 q=0" % lock_word()],
          " | ".join(armory_line(l3)))
    check("armory: and the game's own in-match card gets the pick the seed carries",
          rt3.eval("ASK(69316, '1793811600')") is True
          and rt3.eval("OC_LAST(52813)") == "69318",
          "%s %s" % (rt3.eval("ASK(69316, '1793811600')"), rt3.eval("OC_LAST(52813)")))

    # a match vm with no nameable press: the gate and the answer are enough to arm
    rt3b = new_rt(lua51, frontend=False, src=False,
                  pre=ARMORY_FIX + "\nARMORY[xhash('setactiveitem')] = nil\n"
                                   "SET_DVAR('pt_armory_ch', 'a=69320')")
    rt3b.execute(LUA_TEXT[ARMORY])
    check("armory: a match vm with no press arms on the gate and the answer alone",
          armory_line(lines_of(rt3b)) == ["progression_tuning: armory armed v12 vm=match gate=wrapped "
                                          "pick=missing answer=wrapped lock=missing own=wrapped "
                                          "vars=147+309 craft=wrapped card=missing rows=76 pick=69320 q=0"]
          and rt3b.eval("OC_LAST(52813)") == "69320"
          and int(rt3b.eval("QUEUED()")) == 1,
          " | ".join(armory_line(lines_of(rt3b)) + [str(rt3b.eval("QUEUED()"))]))
    rt3b.execute("DOORSTUB()")
    pump(rt3b, 1)
    check("armory: and it keeps its own watch once the door is in, the late line said once",
          int(rt3b.eval("QUEUED()")) == 1
          and [ln for ln in lines_of(rt3b) if "armory late " in ln]
          == ["progression_tuning: armory late lock"],
          " | ".join(lines_of(rt3b)[-3:]))

    rt4 = new_rt(lua51, frontend=True)
    l4 = lines_of(rt4)
    check("armory: with no ARMORY table at all nothing is wrapped and nothing is said",
          not armory_line(l4), " | ".join(armory_line(l4)))
    rt4.execute(ARMORY_FIX)
    pump(rt4, 4)
    l5 = lines_of(rt4)
    check("armory: the tick picks the gate up when the table turns up late",
          rt4.eval("ASK(69316, '1793811600')") is True
          and armory_line(l5) == ["progression_tuning: armory armed v12 vm=menu gate=wrapped pick=wrapped "
                                  "answer=wrapped lock=wrapped own=wrapped vars=147+309 craft=n/a "
                                  "card=missing rows=76 pick=0 q=0"],
          " | ".join(armory_line(l5)))
    pump(rt4, 8)
    check("armory: and the arm line stays one line",
          len(armory_line(lines_of(rt4))) == 1, " | ".join(armory_line(lines_of(rt4))))

    rt5 = new_rt(lua51, frontend=True)
    rt5.execute("ARMORY = {}")
    pump(rt5, 480)
    l6 = lines_of(rt5)
    check("armory: an armory table with no gate gives up quietly after the tries run out",
          armory_line(l6) == ["progression_tuning: armory armed v12 vm=menu gate=missing pick=missing "
                              "answer=wrapped lock=wrapped own=missing vars=147+309 craft=n/a "
                              "card=missing rows=76 pick=0 q=0"],
          " | ".join(armory_line(l6)))
    check("armory: its own watch still ticks once the tries run out, main's timer stands too",
          int(rt5.eval("QUEUED()")) == 2, str(rt5.eval("QUEUED()")))

    rt6 = new_rt(lua51, frontend=True, src=False)
    rt6.execute(ARMORY_FIX)
    rt6.execute(LUA_TEXT[ARMORY])
    l7 = lines_of(rt6)
    check("armory: the part arms in a vm with no main part in it at all",
          armory_line(l7) == ["progression_tuning: armory armed v12 vm=menu gate=wrapped pick=wrapped "
                              "answer=wrapped lock=missing own=wrapped vars=147+309 craft=n/a "
                              "card=missing rows=76 pick=0 q=0"]
          and rt6.eval("ASK(69316, '1793811600')") is True
          and rt6.eval("rawget(_G, 'ProgressionTuning').hooks.armory") is None,
          " | ".join(armory_line(l7)))


def pick_lines(lines):
    return [ln for ln in lines if "armory pick" in ln]


def armory_pick(lua51):
    """C31 a4: the call names the row first, the hashed tree answers when it does not."""
    rt = new_rt(lua51, frontend=True, pre=ARMORY_FIX + "\nSET_DVAR('pt_armory_ch', '')")
    rt.execute("SET_FOCUS(69320, 'sat_pi_alcor')")
    got = rt.eval("PRESS()")
    calls = int(rt.eval("PRESSCALLS()"))
    check("armory pick: the clients own press runs first and its values come back unchanged",
          got == "client-ret,7" and calls == 1, "%s calls=%d" % (got, calls))
    check("armory pick: the press names its row and the ref that came with it",
          pick_lines(lines_of(rt)) == ["progression_tuning: armory pick 69320 (sat_pi_alcor)"],
          " | ".join(pick_lines(lines_of(rt))))
    check("armory pick: 52813 answers the pick with a copied record, its id and a default",
          rt.eval("OC_LAST(52813)") == "69320" and rt.eval("OC_ID(52813)") == "52813"
          and rt.eval("OC_DEFAULTS(52813)") == "0", "%s %s %s" % (rt.eval("OC_LAST(52813)"),
                                                                 rt.eval("OC_ID(52813)"),
                                                                 rt.eval("OC_DEFAULTS(52813)")))
    check("armory pick: the channel carries the row for the hook half",
          rt.eval("CH()") == "a=69320", str(rt.eval("CH()")))
    rt.execute("PRESS()")
    check("armory pick: the same pick again is one line and the same answer",
          len(pick_lines(lines_of(rt))) == 1 and rt.eval("OC_LAST(52813)") == "69320",
          " | ".join(pick_lines(lines_of(rt))))
    rt.execute("SET_FOCUS(69318); PRESS()")
    check("armory pick: a second pick moves it and the answer follows",
          rt.eval("OC_LAST(52813)") == "69318" and len(pick_lines(lines_of(rt))) == 2
          and rt.eval("CH()") == "a=69318", " | ".join(pick_lines(lines_of(rt))))

    rt.execute("OC_PUT(52813, { id = 52813, progress = { xp = 12, default = 0, last_activation = 0 } })")
    check("armory pick: a zero activation is answered from a copy, the clients table untouched",
          rt.eval("OC_LAST(52813)") == "69318" and rt.eval("OC_OWN(52813)") is False
          and rt.eval("OC_CLIENT_LAST(52813)") == "0",
          "%s own=%s client=%s" % (rt.eval("OC_LAST(52813)"), rt.eval("OC_OWN(52813)"),
                                   rt.eval("OC_CLIENT_LAST(52813)")))
    rt.execute("OC_PUT(52813, { id = 52813, progress = { last_activation = 69316 } })")
    check("armory pick: a record the client already activated passes through untouched",
          rt.eval("OC_LAST(52813)") == "69316" and rt.eval("OC_OWN(52813)") is True,
          "%s own=%s" % (rt.eval("OC_LAST(52813)"), rt.eval("OC_OWN(52813)")))
    rt.execute("OC_PUT(54499, { id = 54499, progress = { last_activation = 69316 } })")
    check("armory pick: every other id is the clients own answer",
          rt.eval("OC_OWN(54499)") is True and rt.eval("OC_LAST(54499)") == "69316",
          "%s own=%s" % (rt.eval("OC_LAST(54499)"), rt.eval("OC_OWN(54499)")))

    # a press that is not one of the 76
    ro = new_rt(lua51, frontend=True, pre=ARMORY_FIX)
    ro.execute("SET_FOCUS(54499, 'sat_pi_alcor'); PRESS()")
    check("armory pick: a press outside the 76 is not recorded and says one line",
          not pick_lines(lines_of(ro))
          and count_line(lines_of(ro), "armory press no row - ") == 1
          and ro.eval("OC_LAST(52813)") == "none",
          " | ".join(lines_of(ro)[-3:]))
    ro.execute("PRESS()")
    check("armory pick: and the no route line stays one line",
          count_line(lines_of(ro), "armory press no row - ") == 1,
          " | ".join(lines_of(ro)[-2:]))

    # the tile the press carries is read before any datasource
    rp = new_rt(lua51, frontend=True, pre=ARMORY_FIX)
    rp.execute("SET_FOCUS(69318, 'sat_ar_emu'); PRESS_EL(69320, 'sat_pi_alcor')")
    check("armory pick: the element the press carries names the row before the datasource",
          rp.eval("OC_LAST(52813)") == "69320"
          and pick_lines(lines_of(rp)) == ["progression_tuning: armory pick 69320 (sat_pi_alcor)"],
          " | ".join(pick_lines(lines_of(rp)) + lines_of(rp)[-2:]))
    re_el = new_rt(lua51, frontend=True, pre=ARMORY_FIX)
    re_el.execute("CLR_FOCUS(); PRESS_EL(69324, 'sat_ar_emu')")
    check("armory pick: and it names one row with no datasource tree behind it",
          re_el.eval("OC_LAST(52813)") == "69324"
          and re_el.eval("rawget(_G, '_DataSources').frontend") is None,
          str(re_el.eval("OC_LAST(52813)")))
    rn_node = new_rt(lua51, frontend=True, pre=ARMORY_FIX)
    rn_node.execute("SET_HNODE(69326, 'sat_ar_emu'); PRESS()")
    check("armory pick: a node whose GetValue sits under its hash still answers",
          rn_node.eval("OC_LAST(52813)") == "69326"
          and pick_lines(lines_of(rn_node)) == ["progression_tuning: armory pick 69326 (sat_ar_emu)"],
          " | ".join(pick_lines(lines_of(rn_node)) + lines_of(rn_node)[-2:]))
    ru = new_rt(lua51, frontend=True, pre=ARMORY_FIX)
    ru.execute("SET_UD(69328, 'sat_ar_emu'); PRESS()")
    check("armory pick: a model that answers only through its index still names the row",
          ru.eval("OC_LAST(52813)") == "69328"
          and pick_lines(lines_of(ru)) == ["progression_tuning: armory pick 69328 (sat_ar_emu)"],
          " | ".join(pick_lines(lines_of(ru)) + lines_of(ru)[-2:]))

    # the tree keyed by plain names, which the client does not do
    rpl = new_rt(lua51, frontend=True, pre=ARMORY_FIX)
    rpl.execute("SET_PLAIN(69320, 'sat_pi_alcor'); PRESS()")
    diag = [ln for ln in lines_of(rpl) if "armory press no row - " in ln]
    check("armory pick: a plain named tree resolves nothing, so the hash route is the one read",
          not pick_lines(lines_of(rpl)) and rpl.eval("OC_LAST(52813)") == "none"
          and len(diag) == 1, " | ".join(diag or pick_lines(lines_of(rpl))))
    check("armory pick: the one diagnostic names the routes walked and the argument types",
          len(diag) == 1 and "el focus active args=table nil number" in diag[0],
          " | ".join(diag))

    # the active tile answers when the focus item does not
    ra = new_rt(lua51, frontend=True, pre=ARMORY_FIX)
    ra.execute("SET_ACTIVE(69318); PRESS()")
    check("armory pick: with no focus value the active tile names the row",
          ra.eval("OC_LAST(52813)") == "69318", str(ra.eval("OC_LAST(52813)")))

    # the last tile the client focused
    rh = new_rt(lua51, frontend=True, pre=ARMORY_FIX)
    rh.execute("HOVER(TILE(69324, 'sat_ar_emu')); PRESS()")
    check("armory pick: the last focused tile is the fallback and is not kept",
          int(rh.eval("FOCUSED()")) == 1 and rh.eval("OC_LAST(52813)") == "69324"
          and pick_lines(lines_of(rh)) == ["progression_tuning: armory pick 69324 (sat_ar_emu)"],
          " | ".join(pick_lines(lines_of(rh))))

    # a press with no datasource at all
    rn = new_rt(lua51, frontend=True, pre=ARMORY_FIX)
    rn.execute("PRESS()")
    check("armory pick: a press with nothing to read records nothing",
          not pick_lines(lines_of(rn)) and rn.eval("OC_LAST(52813)") == "none"
          and count_line(lines_of(rn), "armory press no row - el focus active args=table nil number") == 1,
          " | ".join(lines_of(rn)[-2:]))

    # the dvar the hook has not made yet
    rd = new_rt(lua51, frontend=True, pre=ARMORY_FIX + "\nCH_ABSENT()")
    rd.execute("SET_FOCUS(69320); PRESS()")
    check("armory pick: an absent channel is a silent no op and the pick still answers",
          rd.eval("CH()") is None and rd.eval("OC_LAST(52813)") == "69320"
          and count_line(lines_of(rd), "attempt to") == 0,
          "%s / %s" % (rd.eval("CH()"), rd.eval("OC_LAST(52813)")))
    rq = new_rt(lua51, frontend=True,
                pre=ARMORY_FIX + "\nDvar[xhash('SetDvarString')] = nil\nCH_ABSENT()")
    rq.execute("SET_FOCUS(69320); PRESS()")
    check("armory pick: no setter in this vm is the same silent no op",
          rq.eval("CH()") is None and rq.eval("OC_LAST(52813)") == "69320"
          and not [ln for ln in lines_of(rq) if "not recorded" in ln],
          " | ".join(lines_of(rq)[-2:]))

    # the pick the hook left in the channel
    rs = new_rt(lua51, frontend=True, pre=ARMORY_FIX + "\nSET_DVAR('pt_armory_ch', 'a=69318')")
    check("armory pick: a pick already in the channel is adopted at arm",
          pick_lines(lines_of(rs)) == ["progression_tuning: armory pick 69318"]
          and rs.eval("OC_LAST(52813)") == "69318"
          and armory_line(lines_of(rs)) == ["progression_tuning: armory armed v12 vm=menu gate=wrapped "
                                            "pick=wrapped answer=wrapped lock=%s own=wrapped "
                                            "vars=147+309 craft=n/a "
                                            "card=missing rows=76 pick=69318 q=0" % lock_word()],
          " | ".join(lines_of(rs)))
    rw = new_rt(lua51, frontend=True, pre=ARMORY_FIX + "\nSET_DVAR('pt_armory_ch', 'a=12345')")
    check("armory pick: a channel value outside the 76 is not adopted",
          pick_lines(lines_of(rw)) == [] and rw.eval("OC_LAST(52813)") == "none",
          " | ".join(pick_lines(lines_of(rw))))

    # the clients own raises
    rr = new_rt(lua51, frontend=True, pre=ARMORY_FIX)
    rr.execute("OC_RAISE = true")
    check("armory pick: a raising record is a safe nil where the client would have raised",
          rr.eval("OC_TRY(52813)") is True and str(rr.eval("OC_ERR(52813)")) == "nil"
          and rr.eval("OC_TRY(54499)") is True and str(rr.eval("OC_ERR(54499)")) == "nil",
          "%s / %s" % (rr.eval("OC_ERR(52813)"), rr.eval("OC_ERR(54499)")))
    rr.execute("OC_RAISE = false; PRESS_RAISE = true")
    check("armory pick: a raising press is swallowed and records nothing",
          rr.eval("TRYPRESS()") is True and str(rr.eval("PRESSERR()")) == "nil"
          and not pick_lines(lines_of(rr)),
          str(rr.eval("PRESSERR()")))

    # loading the file twice
    rl = new_rt(lua51, frontend=True, pre=ARMORY_FIX)
    rl.execute("SNAP(); SET_FOCUS(69320); PRESS()")
    before = len(lines_of(rl))
    load(rl)
    check("armory pick: loading the file twice wraps nothing twice and says nothing again",
          rl.eval("SAME()") is True and len(lines_of(rl)) == before
          and len(armory_line(lines_of(rl))) == 1 and len(pick_lines(lines_of(rl))) == 1,
          " | ".join(lines_of(rl)[-3:]))

    # a press the client keeps under a padded hash
    rp2 = new_rt(lua51, frontend=True, pre=ARMORY_FIX + "\nPADPRESS()")
    rp2.execute("SET_FOCUS(69320); PRESS()")
    check("armory pick: a press under a padded hash is found and wrapped",
          rp2.eval("OC_LAST(52813)") == "69320"
          and count_line(lines_of(rp2), "lock=%s own=wrapped vars=147+309 craft=n/a "
                                       "card=missing rows=76 pick=" % lock_word()) == 1,
          " | ".join(lines_of(rp2)[-2:]))

    # a match vm
    rm = new_rt(lua51, frontend=False, pre=ARMORY_FIX)
    rm.execute("SET_FOCUS(69320); PRESS()")
    lm = armory_line(lines_of(rm))
    check("armory pick: a match vm records the press it sees and answers 52813 there",
          rm.eval("PRESS()") == "client-ret,7"
          and pick_lines(lines_of(rm)) == ["progression_tuning: armory pick 69320"]
          and rm.eval("OC_LAST(52813)") == "69320"
          and len(lm) == 1 and "vm=match" in lm[0],
          " | ".join(lm + lines_of(rm)[-2:]))


ARMORY_QUEUE = r"""
Challenge = { [xhash("IsChallengeComplete")] = function(c, id) return id == 69316 end }
ARMORY[xhash("getcachedarmoryachievements")] = function()
  return { { id = "69320" }, { id = 69316 }, { id = "69318" }, { id = 54499 }, { id = 69324 } }
end
"""

ARMORY_QUEUE_NOC = r"""
ARMORY[xhash("getcachedarmoryachievements")] = function()
  return { { id = "69320" }, { id = 69316 }, { id = "69318" } }
end
"""


def armory_queue(lua51):
    """step P: the channel carries a queue, the seed adopts one and a press keeps it."""
    # an empty channel is not a line: the queue waits for the hook's line or a press
    rq = new_rt(lua51, frontend=True, pre=ARMORY_FIX + ARMORY_QUEUE + "\nSET_DVAR('pt_armory_ch', '')")
    check("armory queue: nothing is written into a channel before the hook put a line in it",
          rq.eval("CH()") == "", str(rq.eval("CH()")))
    check("armory queue: the arm line names the pick it has and how many ids the queue holds",
          armory_line(lines_of(rq)) == ["progression_tuning: armory armed v12 vm=menu gate=wrapped pick=wrapped "
                                        "answer=wrapped lock=%s own=wrapped vars=147+309 craft=n/a "
                                        "card=missing rows=76 pick=0 q=3" % lock_word()],
          " | ".join(armory_line(lines_of(rq))))
    rq.execute("SET_FOCUS(69318); PRESS()")
    check("armory queue: a press writes a= and the page's own list as its q= in order, finished rows dropped",
          rq.eval("CH()") == "a=69318;q=69320,69318,69324", str(rq.eval("CH()")))
    rq.execute("SET_FOCUS(69324); PRESS()")
    check("armory queue: and a second press keeps the same queue",
          rq.eval("CH()") == "a=69324;q=69320,69318,69324", str(rq.eval("CH()")))
    check("armory queue: the page's list is not written again on a press",
          count_line(lines_of(rq), "armory pick 69324") == 1 and len(pick_lines(lines_of(rq))) == 2,
          " | ".join(pick_lines(lines_of(rq))))

    # a channel line the hook left: the seed adopts the row and the queue, and a press keeps it
    rs = new_rt(lua51, frontend=True, pre=ARMORY_FIX + "\nSET_DVAR('pt_armory_ch', 'a=69320;q=69318,69316')")
    check("armory queue: a merged line in the channel seeds the row and the queue",
          rs.eval("CH()") == "a=69320;q=69318,69316"
          and armory_line(lines_of(rs)) == ["progression_tuning: armory armed v12 vm=menu gate=wrapped pick=wrapped "
                                            "answer=wrapped lock=%s own=wrapped vars=147+309 craft=n/a "
                                            "card=missing rows=76 pick=69320 q=2" % lock_word()],
          " | ".join(armory_line(lines_of(rs)) + pick_lines(lines_of(rs))))
    rs.execute("SET_FOCUS(69324); PRESS()")
    check("armory queue: the press keeps the queue the seed took",
          rs.eval("CH()") == "a=69324;q=69318,69316", str(rs.eval("CH()")))

    # a row outside the 76 is not a pick, but the queue it came with is still the queue
    rw = new_rt(lua51, frontend=True, pre=ARMORY_FIX + "\nSET_DVAR('pt_armory_ch', 'a=12345;q=69316')")
    rw.execute("SET_FOCUS(69320); PRESS()")
    check("armory queue: a channel row outside the 76 is not adopted, its queue is",
          not [ln for ln in pick_lines(lines_of(rw)) if ln.endswith("armory pick 12345")]
          and rw.eval("CH()") == "a=69320;q=69316", str(rw.eval("CH()")))

    # no completion reader in this vm: the list is taken whole rather than not at all
    rn = new_rt(lua51, frontend=True, pre=ARMORY_FIX + ARMORY_QUEUE_NOC + "\nSET_DVAR('pt_armory_ch', '')")
    check("armory queue: an empty channel takes no queue from the page either",
          rn.eval("CH()") == "", str(rn.eval("CH()")))
    rn.execute("SET_FOCUS(69320); PRESS()")
    check("armory queue: with no completion reader the page's list is taken as it stands",
          rn.eval("CH()") == "a=69320;q=69320,69316,69318", str(rn.eval("CH()")))


def armory_seed(lua51):
    """C88 a2: the pick is taken whenever the hook's line turns up, and no write runs before it."""
    # a: the arm lands before the hook has registered the channel
    ra = new_rt(lua51, frontend=True, src=False)
    ra.execute(ARMORY_FIX)
    ra.execute(LUA_TEXT[ARMORY])
    check("armory seed: an arm with no channel takes nothing and writes nothing",
          ra.eval("CH()") is None and not pick_lines(lines_of(ra))
          and int(ra.eval("QUEUED()")) == 1,
          "%s / %s" % (ra.eval("CH()"), " | ".join(lines_of(ra))))
    pump(ra, 3)
    check("armory seed: three ticks with no channel still take nothing",
          ra.eval("CH()") is None and not pick_lines(lines_of(ra)),
          " | ".join(lines_of(ra)))
    ra.execute("SET_DVAR('pt_armory_ch', 'a=75671')")
    pump(ra, 1)
    check("armory seed: the line the hook registers late is adopted on the next tick",
          pick_lines(lines_of(ra)) == ["progression_tuning: armory pick 75671 (seeded late)"]
          and ra.eval("OC_LAST(52813)") == "75671",
          " | ".join(pick_lines(lines_of(ra)) + [str(ra.eval("OC_LAST(52813)"))]))
    check("armory seed: and the seed leaves the hook's own line as it found it",
          ra.eval("CH()") == "a=75671", str(ra.eval("CH()")))
    ra.execute("DOORSTUB()")
    pump(ra, 5)
    check("armory seed: the pick is said once and the watch keeps ticking once the door is in",
          len(pick_lines(lines_of(ra))) == 1 and int(ra.eval("QUEUED()")) == 1,
          "%d lines / %s queued" % (len(pick_lines(lines_of(ra))), ra.eval("QUEUED()")))

    # b: an empty channel is not a line, so only a press writes
    rb = new_rt(lua51, frontend=True, src=False)
    rb.execute(ARMORY_FIX + "\nSET_DVAR('pt_armory_ch', '')")
    rb.execute(LUA_TEXT[ARMORY])
    check("armory seed: an empty channel takes no arm write",
          rb.eval("CH()") == "" and not pick_lines(lines_of(rb)), str(rb.eval("CH()")))
    rb.execute("SET_FOCUS(69320); PRESS()")
    check("armory seed: a press writes its row into that channel",
          rb.eval("CH()") == "a=69320", str(rb.eval("CH()")))
    check("armory seed: and the press is the one line it says",
          pick_lines(lines_of(rb)) == ["progression_tuning: armory pick 69320"],
          " | ".join(pick_lines(lines_of(rb))))

    # c: the channel the hook filled before the part read it
    rc = new_rt(lua51, frontend=True, src=False)
    rc.execute(ARMORY_FIX + "\nSET_DVAR('pt_armory_ch', 'a=69318')")
    rc.execute(LUA_TEXT[ARMORY])
    check("armory seed: a channel filled before the arm is adopted at the arm, as before",
          pick_lines(lines_of(rc)) == ["progression_tuning: armory pick 69318"]
          and rc.eval("OC_LAST(52813)") == "69318" and rc.eval("CH()") == "a=69318"
          and int(rc.eval("QUEUED()")) == 1,
          " | ".join(lines_of(rc)))

    # d: the answer asks before any tick has run
    rd = new_rt(lua51, frontend=True, src=False)
    rd.execute(ARMORY_FIX)
    rd.execute(LUA_TEXT[ARMORY])
    rd.execute("SET_DVAR('pt_armory_ch', 'a=69318')")
    check("armory seed: the answer seeds the pick itself when no tick has run",
          rd.eval("OC_LAST(52813)") == "69318"
          and pick_lines(lines_of(rd)) == ["progression_tuning: armory pick 69318 (seeded late)"],
          " | ".join(pick_lines(lines_of(rd)) + [str(rd.eval("OC_LAST(52813)"))]))
    pump(rd, 1)
    check("armory seed: the timer waits for the door the answer cannot give it",
          int(rd.eval("QUEUED()")) == 1 and len(pick_lines(lines_of(rd))) == 1,
          "%s queued" % str(rd.eval("QUEUED()")))
    rd.execute("DOORSTUB()")
    pump(rd, 1)
    check("armory seed: and the watch stands once the door is in and the pick is seeded",
          int(rd.eval("QUEUED()")) == 1 and len(pick_lines(lines_of(rd))) == 1
          and [ln for ln in lines_of(rd) if "armory late " in ln]
          == ["progression_tuning: armory late lock"],
          "%s queued | %s" % (str(rd.eval("QUEUED()")), " | ".join(lines_of(rd)[-2:])))


def armory_advance(lua51):
    """v9: a hook advance of the pick in the channel is adopted on the next tick."""
    rt = new_rt(lua51, frontend=False,
                pre=ARMORY_FIX + "\nSET_DVAR('pt_armory_ch', 'a=69318;q=69320,69324')")
    pump(rt, 1)
    check("armory advance: the pick the hook left is the one the arm took",
          rt.eval("OC_LAST(52813)") == "69318" and len(pick_lines(lines_of(rt))) == 1,
          "%s / %s" % (rt.eval("OC_LAST(52813)"), " | ".join(pick_lines(lines_of(rt)))))
    rt.execute("SET_DVAR('pt_armory_ch', 'a=69320;q=69320,69324')")
    check("armory advance: before the tick the answer still names the old pick",
          rt.eval("OC_LAST(52813)") == "69318", str(rt.eval("OC_LAST(52813)")))
    pump(rt, 1)
    check("armory advance: the hook's changed a is adopted on the next tick and said once",
          rt.eval("OC_LAST(52813)") == "69320"
          and [ln for ln in pick_lines(lines_of(rt)) if ln.endswith("(advanced)")]
          == ["progression_tuning: armory pick 69320 (advanced)"],
          " | ".join(pick_lines(lines_of(rt))))
    pump(rt, 3)
    check("armory advance: an unchanged line costs nothing and says nothing",
          len(pick_lines(lines_of(rt))) == 2, " | ".join(pick_lines(lines_of(rt))))
    rt.execute("SET_FOCUS(69324); PRESS()")
    check("armory advance: a press writes its row over the hook's line",
          rt.eval("CH()") == "a=69324;q=69320,69324" and rt.eval("OC_LAST(52813)") == "69324",
          "%s / %s" % (rt.eval("CH()"), rt.eval("OC_LAST(52813)")))
    rt.execute("SET_DVAR('pt_armory_ch', 'a=69316;q=69320,69324')")
    pump(rt, 1)
    check("armory advance: a later hook advance is adopted again",
          rt.eval("OC_LAST(52813)") == "69316"
          and count_line(lines_of(rt), "(advanced)") == 2,
          " | ".join(pick_lines(lines_of(rt))))

    # a press in the same window outranks the hook line
    rp = new_rt(lua51, frontend=False, pre=ARMORY_FIX + "\nSET_DVAR('pt_armory_ch', 'a=69318')")
    pump(rp, 1)
    rp.execute("SET_DVAR('pt_armory_ch', 'a=69320')")
    rp.execute("SET_FOCUS(69324); PRESS()")
    pump(rp, 1)
    check("armory advance: a press after the hook write keeps the row it pressed",
          rp.eval("OC_LAST(52813)") == "69324" and count_line(lines_of(rp), "(advanced)") == 0,
          "%s / %s" % (rp.eval("OC_LAST(52813)"), " | ".join(pick_lines(lines_of(rp)))))

    # the same with no setter, so the press cannot write its own line
    rs = new_rt(lua51, frontend=False, pre=ARMORY_FIX + "\nSET_DVAR('pt_armory_ch', 'a=69318')")
    pump(rs, 1)
    rs.execute("Dvar[xhash('SetDvarString')] = nil")
    rs.execute("SET_DVAR('pt_armory_ch', 'a=69320')")
    rs.execute("SET_FOCUS(69324); PRESS()")
    pump(rs, 1)
    check("armory advance: a press whose own write failed still outranks the hook line",
          rs.eval("OC_LAST(52813)") == "69324" and rs.eval("CH()") == "a=69320"
          and count_line(lines_of(rs), "(advanced)") == 0,
          "%s / %s" % (rs.eval("OC_LAST(52813)"), rs.eval("CH()")))

    # a line outside the 76 and a line of our own are not advances
    rw = new_rt(lua51, frontend=False, pre=ARMORY_FIX + "\nSET_DVAR('pt_armory_ch', 'a=69318')")
    pump(rw, 1)
    rw.execute("SET_DVAR('pt_armory_ch', 'a=54499')")
    pump(rw, 1)
    check("armory advance: a changed a outside the 76 is left where the hook put it",
          rw.eval("OC_LAST(52813)") == "69318" and count_line(lines_of(rw), "(advanced)") == 0,
          "%s / %s" % (rw.eval("OC_LAST(52813)"), " | ".join(pick_lines(lines_of(rw)))))
    rw.execute("SET_FOCUS(69320); PRESS()")
    pump(rw, 3)
    check("armory advance: the part's own write is never taken as an advance",
          rw.eval("OC_LAST(52813)") == "69320" and count_line(lines_of(rw), "(advanced)") == 0,
          " | ".join(pick_lines(lines_of(rw))))

    if LOAD_ORDER == "harness":
        for order in ("harness", "alphabetical", "reversed"):
            r = new_rt(lua51, frontend=False, src=False,
                       pre=ARMORY_FIX + "\nSET_DVAR('pt_armory_ch', 'a=69318;q=69320,69324')")
            for n in LOAD_ORDERS[order]:
                r.execute(LUA_TEXT[n])
            pump(r, 1)
            r.execute("SET_DVAR('pt_armory_ch', 'a=69320;q=69320,69324')")
            pump(r, 1)
            check("armory advance: %s order adopts the hook's a on the next tick" % order,
                  r.eval("OC_LAST(52813)") == "69320"
                  and count_line(lines_of(r), "(advanced)") == 1,
                  " | ".join(pick_lines(lines_of(r))))


ACARDROWS = r"""
ACMROW = {}
Challenge[xhash("IsChallengeComplete")] = function(c, id) return ACMROW[tostring(id)] == true end
function CARD_SET(row) ACMROW[tostring(row)] = true end
function CARD_CLR(row) ACMROW[tostring(row)] = nil end
function CARD_N() return NAMED("completed_challenge") end
"""

CARD_FIX = ACARDROWS + r"""
CARDK = 0
Challenge[xhash("GetAEKindID")] = function(n)
  if n == "ae_kind_armory" or n == xhash("ae_kind_armory") then CARDK = CARDK + 1; return 368 end
  return 0
end
function CARD_KIND() local e = LASTOF("completed_challenge"); return tostring(e and e.kind) end
function CARD_ID() local e = LASTOF("completed_challenge"); return tostring(e and e.id) end
function CARD_PL() local e = LASTOF("completed_challenge"); return tostring(e and type(e.progress)) end
"""

# the game's common item entry, its wrong picture and the gun own one
PICT_FIX = r"""
COMMON_ITEM = {}
CIMG = {}
CIMGN = 0
function SET_CIMG(id, v) CIMG[tostring(id)] = v end
function SET_REF(id, ref) LOOTREF[tostring(id)] = ref end
COMMON_ITEM[xhash("GetItemSpawnEntryImageByID")] = function(id)
  CIMGN = CIMGN + 1
  local v = CIMG[tostring(id)]
  if v ~= nil then return v end
  return nil
end
WEAPON[xhash("getbwimage")] = function(ref) return "bw_" .. tostring(ref) end
function ENTRY(id) return COMMON_ITEM[xhash("GetItemSpawnEntryImageByID")](id) end
function CARD_KEYS()
  local e = LASTOF("completed_challenge")
  if e == nil then return "" end
  local t = {}
  for k in pairs(e) do t[#t + 1] = tostring(k) end
  table.sort(t)
  return table.concat(t, ",")
end
"""

# the spawn entry title the client answers and the gun own name the part puts in its place
NAME_FIX = r"""
NTITLE = {}
GNAME = {}
NCALLS = 0
function SET_TITLE(id, v) NTITLE[tostring(id)] = v end
function SET_GNAME(ref, v) GNAME[ref] = v end
LOOT[xhash("getitemnamebyid")] = function(id, mark)
  NCALLS = NCALLS + 1
  local v = NTITLE[tostring(id)]
  if v ~= nil then return v end
  return "ITEM " .. tostring(id)
end
WEAPON[xhash("getweapondataforref")] = function(ref)
  local n = GNAME[ref]
  if n == nil then return nil end
  return { name = n }
end
function ASK_NAME(id, mark) return LOOT[xhash("getitemnamebyid")](id, mark) end
function NAME_CALLS() return NCALLS end
function NAME_KEEP() NWRAP = LOOT[xhash("getitemnamebyid")] end
function NAME_SAME() return NWRAP == LOOT[xhash("getitemnamebyid")] end
"""


def armory_card(lua51):
    """v10: a row that finishes in the match draws the game's own armory card, v11: it names the gun."""
    rt = new_rt(lua51, frontend=False, pre=ARMORY_FIX + CARD_FIX)
    pump(rt, 2)
    check("armory card: the arm line names the card path this vm can take",
          " card=ok " in armory_line(lines_of(rt))[0], " | ".join(armory_line(lines_of(rt))))
    check("armory card: a row that was open at the arm draws nothing",
          int(rt.eval("CARD_N()")) == 0, str(rt.eval("CARD_N()")))
    rt.execute("CLEAR(); CARD_SET(69316)")
    pump(rt, 1)
    check("armory card: the row that just finished draws one card with its own id and kind",
          int(rt.eval("CARD_N()")) == 1 and rt.eval("CARD_KIND()") == "368"
          and rt.eval("CARD_ID()") == "69316" and rt.eval("CARD_PL()") == "table",
          "%s / %s / %s" % (rt.eval("CARD_N()"), rt.eval("CARD_KIND()"), rt.eval("CARD_ID()")))
    check("armory card: the card line names the row, the kind and the row's loot",
          count_line(lines_of(rt), "armory card 69316 kind=368 loot=126468") == 1,
          " | ".join([ln for ln in lines_of(rt) if "armory card" in ln]))
    pump(rt, 3)
    check("armory card: one card per row, never one a tick",
          int(rt.eval("CARD_N()")) == 1 and count_line(lines_of(rt), "armory card ") == 1,
          "%s / %d lines" % (rt.eval("CARD_N()"), count_line(lines_of(rt), "armory card ")))
    rt.execute("CARD_SET(69318)")
    pump(rt, 1)
    check("armory card: a second row that finishes draws its own card",
          int(rt.eval("CARD_N()")) == 2 and int(rt.eval("CARD_ID()")) == 69318,
          "%s / %s" % (rt.eval("CARD_N()"), rt.eval("CARD_ID()")))
    rt.execute("CARD_CLR(69318)")
    pump(rt, 1)
    rt.execute("CARD_SET(69318)")
    pump(rt, 1)
    check("armory card: a row already carded is never carded twice in one session",
          int(rt.eval("CARD_N()")) == 2, str(rt.eval("CARD_N()")))

    # a row complete at the arm is never carded
    ra = new_rt(lua51, frontend=False, pre=ARMORY_FIX + CARD_FIX + "\nCARD_SET(69318)")
    pump(ra, 3)
    check("armory card: a row complete at the arm draws nothing",
          int(ra.eval("CARD_N()")) == 0, str(ra.eval("CARD_N()")))
    ra.execute("CARD_CLR(69318)")
    pump(ra, 1)
    ra.execute("CARD_SET(69318)")
    pump(ra, 1)
    check("armory card: and it stays silent when that row turns complete later",
          int(ra.eval("CARD_N()")) == 0, str(ra.eval("CARD_N()")))

    # a root that raises is swallowed
    rr = new_rt(lua51, frontend=False, pre=ARMORY_FIX + CARD_FIX)
    pump(rr, 1)
    rr.execute("LUI[xhash('UIRoot')][xhash('ProcessEvent')] = function() error('the root raised') end")
    rr.execute("CARD_SET(69320)")
    pump(rr, 1)
    check("armory card: a raising root is swallowed and said once",
          count_line(lines_of(rr), "attempt to") == 0
          and count_line(lines_of(rr), "armory card 69320 refused") == 1,
          " | ".join([ln for ln in lines_of(rr) if "armory card" in ln or "attempt to" in ln]))
    fired = int(pump(rr, 2))
    check("armory card: and the watch keeps ticking after the refusal",
          fired == 2 and int(rr.eval("QUEUED()")) == 2,
          "%d ticks / %s queued" % (fired, rr.eval("QUEUED()")))

    # a vm with no kind says missing and draws nothing
    rn = new_rt(lua51, frontend=False, pre=ARMORY_FIX + ACARDROWS)
    pump(rn, 1)
    rn.execute("CLEAR(); CARD_SET(69316)")
    pump(rn, 1)
    check("armory card: a vm with no kind says missing on the arm line and draws nothing",
          " card=missing " in armory_line(lines_of(rn))[0]
          and int(rn.eval("CARD_N()")) == 0
          and count_line(lines_of(rn), "armory card ") == 0,
          " | ".join(armory_line(lines_of(rn))))

    # the widget reads the row id: name and picture both come from its own loot
    wpn = [it for it in items76() if it[3] == 1]
    rk = new_rt(lua51, frontend=False, pre=ARMORY_FIX + CARD_FIX + PICT_FIX)
    rk.execute("SET_REF(142465, 'sat_sm_civet')")
    rk.execute("SET_CIMG(142465, 'sat_icon_weapon_sat_sm_orca_material')")
    rk.execute("SET_REF(125052, 'sat_acc_sight')")
    rk.execute("SET_CIMG(125052, 'sat_icon_weapon_sat_acc_sight_material')")
    rk.execute("SET_REF(126337, 'sat_fieldupgrade_a')")
    rk.execute("SET_CIMG(126337, 'sat_icon_weapon_sat_fieldupgrade_b_material')")
    rk.execute("SET_REF(200000, 'sat_foreign')")
    rk.execute("SET_CIMG(200000, 'sat_icon_foreign')")
    check("armory card: before any card the spawn entry names another smg for the vmp row",
          rk.eval("ENTRY(142465)") == "sat_icon_weapon_sat_sm_orca_material",
          str(rk.eval("ENTRY(142465)")))
    pump(rk, 1)
    for row in (75671, 66895, 69330):
        rk.execute("CLEAR(); CARD_SET(%d)" % row)
        pump(rk, 1)
        check("armory card: row %d carries exactly name, controller, kind, id and progress" % row,
              rk.eval("CARD_KEYS()") == "controller,id,kind,name,progress"
              and rk.eval("CARD_ID()") == str(row) and rk.eval("CARD_KIND()") == "368"
              and int(rk.eval("LASTOF('completed_challenge').controller")) == 0
              and rk.eval("CARD_PL()") == "table",
              "%s / %s / %s" % (rk.eval("CARD_ID()"), rk.eval("CARD_KIND()"), rk.eval("CARD_KEYS()")))
    check("armory card: the vmp row's picture is the gun own one, not the entry's other smg",
          rk.eval("ENTRY(142465)") == "bw_sat_sm_civet", str(rk.eval("ENTRY(142465)")))
    check("armory card: an attachment and a field upgrade keep the entry's own art",
          rk.eval("ENTRY(125052)") == "sat_icon_weapon_sat_acc_sight_material"
          and rk.eval("ENTRY(126337)") == "sat_icon_weapon_sat_fieldupgrade_b_material",
          "%s / %s" % (rk.eval("ENTRY(125052)"), rk.eval("ENTRY(126337)")))
    check("armory card: an id outside the 76 keeps the entry's own answer",
          rk.eval("ENTRY(200000)") == "sat_icon_foreign", str(rk.eval("ENTRY(200000)")))
    check("armory card: the picture wrap says one line for the %d weapon loots" % len(wpn),
          count_line(lines_of(rk), "armory picture wrapped for %d weapon loots" % len(wpn)) == 1,
          " | ".join([ln for ln in lines_of(rk) if "picture" in ln]))

    # the name line: the spawn entry title for eight of the 34, the gun own name for all of them
    bad = [(125262, "sat_sm_bear", "&#sat_weapon/sat_sm_bear"),
           (119843, "sat_sm_gecko", "&#sat_weapon/sat_sm_gecko"),
           (116617, "sat_sm_bengal", "&#sat_weapon/sat_sm_bengal"),
           (98043, "sat_sm_hyena", "&#sat_weapon/sat_sm_hyena"),
           (133344, "sat_sm_marmot", "&#SAT_WEAPON/SAT_SM_MARMOT"),
           (119845, "sat_dm_solomon", "&#sat_weapon/sat_dm_solomon"),
           (97917, "sat_lm_typhon", "&#sat_weapon/sat_lm_typhon"),
           (131330, "sat_ar_kiwi", "&#SAT_WEAPON/SAT_AR_KIWI")]
    rw = new_rt(lua51, frontend=False, pre=ARMORY_FIX + CARD_FIX + PICT_FIX + NAME_FIX)
    for loot, ref, key in bad:
        rw.execute("SET_REF(%d, '%s'); SET_TITLE(%d, 'SUB MACHINE GUN'); SET_GNAME('%s', '%s')"
                   % (loot, ref, loot, ref, key))
    rw.execute("SET_REF(126468, 'sat_ar_finch')"
               "; SET_TITLE(126468, 'L:&#sat_weapon/sat_ar_finch')"
               "; SET_GNAME('sat_ar_finch', '&#sat_weapon/sat_ar_finch')")
    rw.execute("SET_TITLE(200000, 'FOREIGN ITEM')")
    check("armory card: before a card the hyena row's loot answers the smg class title",
          rw.eval("ASK_NAME(98043)") == "SUB MACHINE GUN", str(rw.eval("ASK_NAME(98043)")))
    pump(rw, 1)
    rw.execute("CLEAR(); CARD_SET(62979)")
    pump(rw, 1)
    check("armory card: a card for the hyena row wraps the name and still draws the card",
          int(rw.eval("CARD_N()")) == 1 and int(rw.eval("CARD_ID()")) == 62979,
          "%s / %s" % (rw.eval("CARD_N()"), rw.eval("CARD_ID()")))
    for loot, ref, key in bad:
        check("armory card: loot %d answers its own gun name, with and without the mark" % loot,
              rw.eval("ASK_NAME(%d)" % loot) == "L:" + key
              and rw.eval("ASK_NAME(%d, true)" % loot) == "L:" + key,
              "%s / %s" % (rw.eval("ASK_NAME(%d)" % loot), rw.eval("ASK_NAME(%d, true)" % loot)))
    check("armory card: a loot whose title was already the gun own keeps that same name",
          rw.eval("ASK_NAME(126468)") == "L:&#sat_weapon/sat_ar_finch",
          str(rw.eval("ASK_NAME(126468)")))
    check("armory card: an id outside the 34 keeps the client's own answer",
          rw.eval("ASK_NAME(200000)") == "FOREIGN ITEM", str(rw.eval("ASK_NAME(200000)")))
    check("armory card: the name wrap says one line for the %d weapon loots" % len(wpn),
          count_line(lines_of(rw), "armory name wrapped for %d weapon loots" % len(wpn)) == 1,
          " | ".join([ln for ln in lines_of(rw) if "name wrapped" in ln]))
    rw.execute("NAME_KEEP()")
    rw.execute("CLEAR(); CARD_SET(69318)")
    pump(rw, 1)
    check("armory card: a second card leaves the wrapped name in place and says nothing more",
          rw.eval("NAME_SAME()") is True
          and count_line(lines_of(rw), "armory name wrapped") == 1,
          "%s / %d lines" % (rw.eval("NAME_SAME()"),
                             count_line(lines_of(rw), "armory name wrapped")))

    # a loot with no ref and no gun data keeps the entry's own title and is never blank
    rd = new_rt(lua51, frontend=False, pre=ARMORY_FIX + CARD_FIX + PICT_FIX + NAME_FIX)
    rd.execute("SET_TITLE(116617, 'SUB MACHINE GUN')")
    pump(rd, 1)
    rd.execute("CLEAR(); CARD_SET(64768)")
    pump(rd, 1)
    check("armory card: a loot the gun data cannot name keeps the entry's own title, never blank",
          rd.eval("ASK_NAME(116617)") == "SUB MACHINE GUN"
          and count_line(lines_of(rd), "armory name wrapped") == 1,
          "%s / %d lines" % (rd.eval("ASK_NAME(116617)"),
                             count_line(lines_of(rd), "armory name wrapped")))

    # the menu vm never wraps the name
    rmw = new_rt(lua51, frontend=True, pre=ARMORY_FIX + NAME_FIX)
    rmw.execute("SET_TITLE(98043, 'SUB MACHINE GUN')")
    pump(rmw, 2)
    check("armory card: a menu vm keeps the entry's own title and wraps no name",
          rmw.eval("ASK_NAME(98043)") == "SUB MACHINE GUN"
          and count_line(lines_of(rmw), "armory name") == 0,
          "%s / %d lines" % (rmw.eval("ASK_NAME(98043)"),
                             count_line(lines_of(rmw), "armory name")))

    # a vm without the common item table still draws the card
    rnc = new_rt(lua51, frontend=False, pre=ARMORY_FIX + CARD_FIX)
    pump(rnc, 1)
    rnc.execute("CLEAR(); CARD_SET(75671)")
    pump(rnc, 1)
    check("armory card: a vm with no common item entry draws the card and names no picture",
          int(rnc.eval("CARD_N()")) == 1 and count_line(lines_of(rnc), "armory picture") == 0,
          "%s / %d lines" % (rnc.eval("CARD_N()"), count_line(lines_of(rnc), "armory picture")))

    if LOAD_ORDER == "harness":
        for order in ("harness", "alphabetical", "reversed"):
            r = new_rt(lua51, frontend=False, src=False,
                       pre=ARMORY_FIX + CARD_FIX + PICT_FIX + NAME_FIX
                       + "\nSET_DVAR('pt_armory_ch', 'a=69318')"
                       + "\nSET_REF(126468, 'sat_ar_finch')"
                       + "\nSET_TITLE(126468, 'SUB MACHINE GUN')"
                       + "\nSET_GNAME('sat_ar_finch', '&#sat_weapon/sat_ar_finch')"
                       + "\nSET_CIMG(126468, 'sat_icon_weapon_sat_ar_eagle_material')")
            for n in LOAD_ORDERS[order]:
                r.execute(LUA_TEXT[n])
            pump(r, 1)
            r.execute("CLEAR(); CARD_SET(69316)")
            pump(r, 1)
            check("armory card: %s order draws the one card for the finished row" % order,
                  int(r.eval("CARD_N()")) == 1 and r.eval("CARD_KIND()") == "368"
                  and r.eval("CARD_ID()") == "69316",
                  "%s / %s" % (r.eval("CARD_N()"), r.eval("CARD_ID()")))
            check("armory card: %s order swaps the row's picture for the gun own one" % order,
                  r.eval("ENTRY(126468)") == "bw_sat_ar_finch", str(r.eval("ENTRY(126468)")))
            check("armory card: %s order swaps the smg class title for the gun own name" % order,
                  r.eval("ASK_NAME(126468)") == "L:&#sat_weapon/sat_ar_finch"
                  and count_line(lines_of(r), "armory name wrapped") == 1,
                  "%s / %d lines" % (r.eval("ASK_NAME(126468)"),
                                     count_line(lines_of(r), "armory name wrapped")))


LOCKFIX = r"""
LKROWS = {}
LKCALLS = 0
LKRAISE = false
Challenge[xhash("IsChallengeComplete")] = function(c, row)
  LKCALLS = LKCALLS + 1
  if LKRAISE then error("the completion reader raised") end
  return LKROWS[tostring(row)] == true
end
function LK_DONE(row) LKROWS[tostring(row)] = true end
function LK_OPEN(row) LKROWS[tostring(row)] = nil end
function LK_N() return LKCALLS end
function LK_ZERO() LKCALLS = 0 end
function DROP_COMPLETE() Challenge[xhash("IsChallengeComplete")] = nil end
function ANS(id) return rawget(_G, "ProgressionTuning").locks.answer(id) end
function OPN(id) return rawget(_G, "ProgressionTuning").locks.open(id) end
function SNAP2()
  local s = rawget(_G, "ProgressionTuning")
  S2A, S2O = s.locks.answer, s.locks.open
end
function SAME2()
  local s = rawget(_G, "ProgressionTuning")
  return s.locks.answer == S2A and s.locks.open == S2O
end
function REBUILD()
  rawget(_G, "ProgressionTuning").locks = {
    answer = function(id) return false end,
    open = function(id) return false end,
  }
end
BPGATE = 0
local function BP_ANSWER(c, id)
  if BPGATE ~= 0 and id == BPGATE then return false end
  return true
end
PROGRESSION[xhash("isunlockedwithid")] = BP_ANSWER
LOOT[xhash("isunlockedwithid")] = BP_ANSWER
"""

# the builds getter the armory part wraps: it lists an entry only when the door says unlocked
LISTFIX = r"""
GM_IDS = {}
GM_SEEN = {}
GM_OPTS = nil
GM_CALLS = 0
GM_RAISE = false
GM_NEST = 0
GM_TWO = false
WEAPON.getmodifications = function(c, opt)
  GM_CALLS = GM_CALLS + 1
  GM_OPTS = opt
  if GM_RAISE then error("the builds getter raised") end
  if GM_NEST > 0 then
    GM_NEST = GM_NEST - 1
    WEAPON.getmodifications(0, { excludeBaseWeapons = true, forceLoot = true,
      byWeapons = { ['sat_sm_civet'] = true } })
  end
  local out = {}
  local f = LOOT[xhash("isunlockedwithid")]
  for i = 1, #GM_IDS do
    local id = GM_IDS[i]
    local owned = f ~= nil and f(c, id) == true
    GM_SEEN[id] = owned
    if owned or (opt ~= nil and opt.checkOwnership == false) then
      out[#out + 1] = { lootID = id }
    end
  end
  if GM_TWO then return out, "second" end
  return out
end
function GM_SET(list) GM_IDS = list end
function GM_CLEAR() GM_SEEN = {} end
function GM_SAW(id) return GM_SEEN[id] end
function GM_N() return GM_CALLS end
function GM_ZERO() GM_CALLS = 0 end
function GM_RAISE_ON(v) GM_RAISE = v end
function GM_NEST_ON(v) GM_NEST = v end
function GM_TWO_ON(v) GM_TWO = v end
function GM_LAST() return GM_OPTS end
function GM_KEPT()
  local o = GM_OPTS
  if o == nil then return "none" end
  return tostring(o.forceLoot) .. "/" .. tostring(o.excludeBaseWeapons)
end
function GM_COUNT(opt) return #WEAPON.getmodifications(0, opt) end
function GM_TRY(opt)
  local ok, v = pcall(WEAPON.getmodifications, 0, opt)
  if not ok then return "raised" end
  if type(v) ~= "table" then return tostring(v) end
  return tostring(#v)
end
function GM_BOTH(opt)
  local ok, a, b = pcall(WEAPON.getmodifications, 0, opt)
  if not ok then return "raised" end
  return tostring(type(a)) .. "/" .. tostring(b)
end
GMREF = "sat_sm_civet"
BPS = { sat_sm_civet = { { lootid = 151472 }, { lootid = 153766 }, { lootid = 151503 } } }
BUNDLES = { [153766] = true }
Engine.GetWeaponBlueprints = function(ref) return BPS[ref] or {} end
if type(GL_HACK) ~= "table" then GL_HACK = {} end
GL_HACK.getweaponmpref = function(ref) return ref end
if type(STORE) ~= "table" then STORE = {} end
if type(STORE.Bundles) ~= "table" then STORE.Bundles = {} end
STORE.Bundles[xhash("GetFirstBundleWithLootId")] = function(c, id)
  if BUNDLES[id] then return "bundle" .. tostring(id) end
  return nil
end
"""

# the option shapes the client passes that must not open the window
BUILDS = "{ excludeBaseWeapons = true, forceLoot = true, byWeapons = { ['sat_sm_civet'] = true } }"
ALL_LIST = ("{ checkOwnership = false, forceCustom = false, excludeBaseWeapons = true, forceLoot = true, "
            "byWeapons = { ['sat_sm_civet'] = true } }")
LISTREF = "sat_sm_civet"
SHAPES = [
    ("shop", "{ includeBundleItems = true, onlyIncludeUnownedItem = true, byWeapons = { ['sat_sm_civet'] = true } }"),
    ("blackcell", "{ onlyIncludeBlackCellEvolvingReward = true, onlyIncludeUnownedItem = true, "
                  "excludeBaseWeapons = true, byWeapons = { ['sat_sm_civet'] = true } }"),
    ("bundle store", "{ exclusiveBundleItems = true, forceLoot = true, excludeBaseWeapons = true, "
                     "byWeapons = { ['sat_sm_civet'] = true } }"),
    ("counters", ALL_LIST),
    ("armory grid", "{ excludeBaseWeapons = true, includeBundleItems = true, "
                    "byWeapons = { ['sat_sm_civet'] = true } }"),
    ("custom", "{ forceCustom = true, byWeapons = { ['sat_sm_civet'] = true } }"),
]

# the three items the user reported, plus one of each other kind, plus two that are not ours
LOCK_IDS = [142465, 140458, 119853, 126337, 129239]
LOCK_OTHER = [126608, 200000]
LOCK_KINDS = {142465: 2, 140458: 7, 119853: 7, 126337: 7, 129239: 7, 126608: 7, 200000: 11}

# the per-weapon versions of the 76 (docs\ARMORY-LOCK-AUDIT.md 2.2, 3.2): the 1911's own two muzzles and two
# optics, its six blueprints, and one blueprint of a gun outside the 76 (the Hades' Shiny, 100249)
VAR_ATTACH = [126626, 140475, 125070, 126906]
VAR_ATTACH_ROW = {126626: 64771, 140475: 71381, 125070: 66895, 126906: 66895}
VAR_BLUEPRINT = [130444, 132228, 140232, 143881, 145335, 140106]
VAR_BLUEPRINT_ROW = 69320
# the blueprint of a gun outside the 76 and the gun itself
VAR_FOREIGN = 100249
FOREIGN_BASE = 88943


def items76():
    """The armory part's own item table as (loot, row, cost, kind)."""
    m = re.search(r"local ITEMS = \{\n(.*?)\n\}\n", LUA_TEXT[ARMORY], re.S)
    out = []
    for ln in (m.group(1) if m else "").split("\n"):
        t = re.findall(r"\d+", ln)
        if len(t) == 4:
            out.append(tuple(int(x) for x in t))
    return out


def vars_table():
    """The armory part's own version table as (row, [ids]), in file order."""
    m = re.search(r"local VARS = \{\n(.*?)\n\}\n", LUA_TEXT[ARMORY], re.S)
    out = []
    for ln in (m.group(1) if m else "").split("\n"):
        t = re.findall(r"\d+", ln)
        if len(t) >= 2:
            out.append((int(t[0]), [int(x) for x in t[1:]]))
    return out


def vars_map():
    """Every version id -> the row it inherits."""
    return {vid: row for row, ids in vars_table() for vid in ids}


def blueprints():
    """Every version id under a weapon row, the ids a builds list must keep showing."""
    kind = {row: k for _loot, row, _cost, k in items76()}
    return sorted(vid for vid, row in vars_map().items() if kind[row] == 1)


def attachment_versions():
    """Every version id under an attachment row."""
    kind = {row: k for _loot, row, _cost, k in items76()}
    return sorted(vid for vid, row in vars_map().items() if kind[row] == 2)


def bp_map():
    """Every blueprint id the armory sells and its gun, plus the one outside the 76."""
    kind = {row: (loot, k) for loot, row, _cost, k in items76()}
    out = {}
    for vid, row in vars_map().items():
        loot, k = kind[row]
        if k == 1:
            out[vid] = loot
    out[VAR_FOREIGN] = FOREIGN_BASE
    return out


def bp_setup():
    """The base each blueprint answers to, and the switch shut to start with."""
    out = " ".join("SET_BLUEPRINT(%d, %d)" % (v, b) for v, b in sorted(bp_map().items()))
    return out + '\nSET_DVAR("zm_unlock_blueprints", "0")'


def lock_rt(lua51, pre="", frontend=True, extra=()):
    """A door with the client's own payload, its defaults and our part over it."""
    every = [it[0] for it in items76()] + LOCK_OTHER + [VAR_FOREIGN] + list(extra)
    rt = new_rt(lua51, frontend=frontend, src=False,
                pre=ARMORY_FIX + "\n" + LOCKFIX + "\n" + bp_setup() + "\n" + pre)
    lua_slabs(rt, slabs_of(every))
    lua_rslabs(rt, slabs_of(every))
    rt.execute("SET_G11(77)")
    rt.execute("SET_G12(%d)" % len(every))
    for it in items76():
        rt.execute("SET_DEFAULT(%d)" % it[0])
    for i, t in LOCK_KINDS.items():
        rt.execute("SET_TYPE(%d, %d)" % (i, t))
    return rt


def list_rt(lua51, pre="", frontend=True, extra=()):
    """The same door, plus the builds getter the window is counted on."""
    return lock_rt(lua51, pre=LISTFIX + "\n" + pre, frontend=frontend, extra=extra)


def list_lines(lines):
    """The temporary check block's lines - the block is gone, so this must always be empty."""
    return [ln for ln in lines if "armory check " in ln]


def armory_lock(lua51):
    """C87 a3: the armory row is the only unlock path for the 76 items."""
    items = items76()
    check("armory lock: the item table is the scope's 76 and names the user's three",
          len(items) == 76 and {142465, 140458, 119853} <= set(i[0] for i in items)
          and len(set(i[1] for i in items)) == 76,
          "%d items" % len(items))

    # the gap: the door alone opens all five through the client's own default table
    door = lock_rt(lua51)
    for n in LOAD_ORDERS["harness"]:
        if n != ARMORY:
            door.execute(LUA_TEXT[n])
    pump(door, 1)
    gap = [(i, door.eval("ASK_P(%d)" % i), door.eval("ASK_L(%d)" % i)) for i in LOCK_IDS]
    check("armory lock: the door alone opens every one of them on the default table",
          all(p is True and l is True for _i, p, l in gap), str(gap))
    vgap = [(i, door.eval("ASK_P(%d)" % i), door.eval("ASK_L(%d)" % i)) for i in VAR_ATTACH]
    check("armory lock: and opens the 1911's four attachment versions too",
          all(p is True and l is True for _i, p, l in vgap), str(vgap[:4]))
    check("armory lock: while its six blueprints stay shut to the switch alone",
          all(door.eval("ASK_P(%d)" % i) is False for i in VAR_BLUEPRINT),
          str([door.eval("ASK_P(%d)" % i) for i in VAR_BLUEPRINT]))
    check("armory lock: and keeps an id outside the 76 locked on both doors",
          door.eval("ASK_P(126608)") is False and door.eval("ASK_L(126608)") is False
          and door.eval("ASK_P(200000)") is False,
          "%s / %s" % (door.eval("ASK_P(126608)"), door.eval("ASK_L(126608)")))
    other_ans = (door.eval("ANS(126608)"), door.eval("OPN(126608)"),
                 door.eval("ANS(200000)"), door.eval("OPN(200000)"))
    check("armory lock: a vm with no armory part in it says no arm line at all",
          armory_line(lines_of(door)) == [], " | ".join(armory_line(lines_of(door))))

    rt = lock_rt(lua51)
    load(rt)
    pump(rt, 1)
    check("armory lock: the arm line names the door side this part wrapped",
          len(armory_line(lines_of(rt))) == 1
          and ("lock=%s" % lock_word()) in armory_line(lines_of(rt))[0],
          " | ".join(armory_line(lines_of(rt))))
    held = [(i, rt.eval("ASK_P(%d)" % i), rt.eval("ASK_L(%d)" % i)) for i in LOCK_IDS]
    check("armory lock: those five read locked once their own row is read on both doors",
          all(p is False and l is False for _i, p, l in held), str(held))
    check("armory lock: an id outside the 76 keeps the doors own answer, id for id",
          (rt.eval("ANS(126608)"), rt.eval("OPN(126608)"),
           rt.eval("ANS(200000)"), rt.eval("OPN(200000)")) == other_ans
          and rt.eval("ASK_P(126608)") is False and rt.eval("ASK_P(200000)") is False,
          str((rt.eval("ANS(126608)"), rt.eval("OPN(126608)"))))
    check("armory lock: the answer side says locked and the open side says nothing for them",
          rt.eval("ANS(142465)") is True and rt.eval("OPN(142465)") is False
          and rt.eval("ANS(119853)") is True and rt.eval("OPN(119853)") is False,
          "%s / %s" % (rt.eval("ANS(142465)"), rt.eval("OPN(142465)")))

    # the row's own completion is enough, and only for the row that finished
    rt.execute("LK_DONE(75671)")
    pump(rt, 1)
    check("armory lock: a finished row opens its item on both doors",
          rt.eval("ASK_P(142465)") is True and rt.eval("ASK_L(142465)") is True
          and rt.eval("ANS(142465)") is False and rt.eval("OPN(142465)") is True,
          "%s / %s" % (rt.eval("ASK_P(142465)"), rt.eval("ASK_L(142465)")))
    check("armory lock: and leaves the other four locked",
          all(rt.eval("ASK_P(%d)" % i) is False for i in (140458, 119853, 126337, 129239)),
          str([rt.eval("ASK_P(%d)" % i) for i in (140458, 119853, 126337, 129239)]))
    rt.execute("LK_OPEN(75671)")
    pump(rt, 1)
    check("armory lock: and the lock comes back when that row is not done again",
          rt.eval("ASK_P(142465)") is False, str(rt.eval("ASK_P(142465)")))

    # a switch per kind, and the one switch over all of them
    rt.execute('SET_DVAR("zm_unlock_weapons", "1")')
    pump(rt, 1)
    check("armory lock: the weapon switch opens the weapon alone",
          rt.eval("ASK_P(142465)") is True and rt.eval("ASK_L(142465)") is True
          and all(rt.eval("ASK_P(%d)" % i) is False for i in (140458, 119853, 126337, 129239)),
          "%s / %s" % (rt.eval("ASK_P(142465)"), rt.eval("ASK_P(140458)")))
    rt.execute('SET_DVAR("zm_unlock_weapons", "0") SET_DVAR("zm_unlock_attachments", "1")')
    pump(rt, 1)
    check("armory lock: the attachment switch opens both attachments and nothing else",
          rt.eval("ASK_L(140458)") is True and rt.eval("ASK_L(119853)") is True
          and rt.eval("ASK_P(142465)") is False and rt.eval("ASK_P(126337)") is False
          and rt.eval("ASK_P(129239)") is False,
          str([rt.eval("ASK_P(%d)" % i) for i in (142465, 126337, 129239)]))
    rt.execute('SET_DVAR("zm_unlock_attachments", "0") SET_DVAR("zm_unlock_fieldupgrades", "1")')
    pump(rt, 1)
    check("armory lock: the field upgrade switch opens the field upgrade",
          rt.eval("ASK_P(126337)") is True and rt.eval("ASK_P(119853)") is False,
          "%s / %s" % (rt.eval("ASK_P(126337)"), rt.eval("ASK_P(119853)")))
    rt.execute('SET_DVAR("zm_unlock_fieldupgrades", "0") SET_DVAR("zm_unlock_scorestreaks", "1")')
    pump(rt, 1)
    check("armory lock: the scorestreak switch opens the scorestreak",
          rt.eval("ASK_P(129239)") is True and rt.eval("ASK_P(126337)") is False,
          "%s / %s" % (rt.eval("ASK_P(129239)"), rt.eval("ASK_P(126337)")))
    rt.execute('SET_DVAR("zm_unlock_scorestreaks", "0") SET_DVAR("zm_unlock_all", "1")')
    pump(rt, 1)
    check("armory lock: unlock everything opens all 76 on both doors",
          all(rt.eval("ASK_P(%d)" % i[0]) is True and rt.eval("ASK_L(%d)" % i[0]) is True
              for i in items),
          str([rt.eval("ASK_P(%d)" % i[0]) for i in items if rt.eval("ASK_P(%d)" % i[0]) is not True]))
    check("armory lock: and the switch that is on stands down every term of our rule",
          rt.eval("ANS(142465)") is False and rt.eval("OPN(142465)") is True,
          "%s / %s" % (rt.eval("ANS(142465)"), rt.eval("OPN(142465)")))
    rt.execute('SET_DVAR("zm_unlock_all", "0")')
    pump(rt, 12)
    check("armory lock: every switch off closes all 76 again",
          all(rt.eval("ASK_P(%d)" % i[0]) is False for i in items),
          str([rt.eval("ASK_P(%d)" % i[0]) for i in items if rt.eval("ASK_P(%d)" % i[0]) is not False]))

    # the versions of those items: 147 attachment ids and 309 weapon ids, each under its own row
    table = vars_table()
    vmap = vars_map()
    kinds = {it[1]: it[3] for it in items}
    attach_ids = [v for v, r in vmap.items() if kinds.get(r) == 2]
    weapon_ids = [v for v, r in vmap.items() if kinds.get(r) == 1]
    check("armory lock: the version table is 39 rows and 456 ids, none of them a base id",
          len(table) == 39 and len(vmap) == 456 and all(r in kinds for r, _ in table)
          and not (set(vmap) & set(i[0] for i in items)),
          "%d rows / %d ids" % (len(table), len(vmap)))
    check("armory lock: 147 of them sit under an attachment row and 309 under a weapon row",
          len(attach_ids) == 147 and len(weapon_ids) == 309,
          "%d / %d" % (len(attach_ids), len(weapon_ids)))
    check("armory lock: the table names the 1911's own four versions and its six blueprints",
          all(vmap.get(i) == r for i, r in VAR_ATTACH_ROW.items())
          and all(vmap.get(i) == VAR_BLUEPRINT_ROW for i in VAR_BLUEPRINT)
          and VAR_FOREIGN not in vmap,
          str([(i, vmap.get(i)) for i in VAR_ATTACH + VAR_BLUEPRINT]))

    # an attachment version answers to its row and to the attachment switch
    held = [(i, rt.eval("ASK_P(%d)" % i), rt.eval("ASK_L(%d)" % i)) for i in VAR_ATTACH]
    check("armory lock: the 1911's two muzzles and two optics read locked on both doors",
          all(p is False and l is False for _i, p, l in held), str(held))
    check("armory lock: a version's answer side says locked and its open side says nothing",
          rt.eval("ANS(126626)") is True and rt.eval("OPN(126626)") is False,
          "%s / %s" % (rt.eval("ANS(126626)"), rt.eval("OPN(126626)")))
    rt.execute("LK_DONE(64771)")
    pump(rt, 1)
    check("armory lock: the hybrid row done opens the redwell on both doors",
          rt.eval("ASK_P(126626)") is True and rt.eval("ASK_L(126626)") is True
          and rt.eval("ANS(126626)") is False and rt.eval("OPN(126626)") is True,
          "%s / %s" % (rt.eval("ASK_P(126626)"), rt.eval("ASK_L(126626)")))
    check("armory lock: and leaves the brake and the optics shut",
          all(rt.eval("ASK_P(%d)" % i) is False for i in (140475, 125070, 126906)),
          str([rt.eval("ASK_P(%d)" % i) for i in (140475, 125070, 126906)]))
    rt.execute("LK_OPEN(64771) LK_DONE(71381) LK_DONE(66895)")
    pump(rt, 1)
    check("armory lock: each row opens its own versions and no other row's",
          rt.eval("ASK_P(126626)") is False and rt.eval("ASK_P(140475)") is True
          and rt.eval("ASK_P(125070)") is True and rt.eval("ASK_P(126906)") is True,
          str([(i, rt.eval("ASK_P(%d)" % i)) for i in VAR_ATTACH]))
    rt.execute("LK_OPEN(71381) LK_OPEN(66895)")
    pump(rt, 1)
    rt.execute('SET_DVAR("zm_unlock_attachments", "1")')
    pump(rt, 1)
    check("armory lock: the attachment switch opens every version of every attachment",
          all(rt.eval("ASK_P(%d)" % i) is True and rt.eval("ASK_L(%d)" % i) is True for i in VAR_ATTACH),
          str([rt.eval("ASK_P(%d)" % i) for i in VAR_ATTACH]))
    rt.execute('SET_DVAR("zm_unlock_attachments", "0") SET_DVAR("zm_unlock_weapons", "1")')
    pump(rt, 1)
    check("armory lock: the weapon switch does not open a version of an attachment",
          all(rt.eval("ASK_P(%d)" % i) is False for i in VAR_ATTACH),
          str([rt.eval("ASK_P(%d)" % i) for i in VAR_ATTACH]))

    # a blueprint needs its gun open and the blueprint switch on
    rt.execute('SET_DVAR("zm_unlock_weapons", "0") SET_DVAR("zm_unlock_attachments", "1")')
    pump(rt, 1)
    check("armory lock: the attachment switch does not open a blueprint of an armory gun",
          all(rt.eval("ASK_P(%d)" % i) is False for i in VAR_BLUEPRINT),
          str([rt.eval("ASK_P(%d)" % i) for i in VAR_BLUEPRINT]))
    rt.execute('SET_DVAR("zm_unlock_attachments", "0") SET_DVAR("zm_unlock_blueprints", "1")')
    pump(rt, 1)
    held = [(i, rt.eval("ASK_P(%d)" % i), rt.eval("ASK_L(%d)" % i)) for i in VAR_BLUEPRINT]
    check("armory lock: the blueprint switch alone leaves them shut while the gun is locked",
          all(p is False and l is False for _i, p, l in held), str(held))
    rt.execute("LK_DONE(69320)")
    pump(rt, 1)
    check("armory lock: the 1911's own row done opens all six with the switch on",
          all(rt.eval("ASK_P(%d)" % i) is True and rt.eval("ASK_L(%d)" % i) is True for i in VAR_BLUEPRINT),
          str([rt.eval("ASK_P(%d)" % i) for i in VAR_BLUEPRINT]))
    rt.execute('SET_DVAR("zm_unlock_blueprints", "0")')
    pump(rt, 1)
    check("armory lock: and the switch off shuts them again with the gun open",
          all(rt.eval("ASK_P(%d)" % i) is False for i in VAR_BLUEPRINT),
          str([rt.eval("ASK_P(%d)" % i) for i in VAR_BLUEPRINT]))
    rt.execute("LK_OPEN(69320)")
    pump(rt, 1)
    rt.execute('SET_DVAR("zm_unlock_weapons", "1")')
    pump(rt, 1)
    check("armory lock: the weapon switch opens the gun and leaves the blueprints shut",
          rt.eval("ASK_P(125186)") is True
          and all(rt.eval("ASK_P(%d)" % i) is False for i in VAR_BLUEPRINT),
          "%s / %s" % (rt.eval("ASK_P(125186)"), rt.eval("ASK_P(%d)" % VAR_BLUEPRINT[0])))
    rt.execute('SET_DVAR("zm_unlock_blueprints", "1")')
    pump(rt, 1)
    check("armory lock: the blueprints follow once their own switch is on too",
          all(rt.eval("ASK_P(%d)" % i) is True for i in VAR_BLUEPRINT),
          str([rt.eval("ASK_P(%d)" % i) for i in VAR_BLUEPRINT]))
    rt.execute('SET_DVAR("zm_unlock_blueprints", "0") SET_DVAR("zm_unlock_weapons", "0")')
    pump(rt, 1)

    # a version is a table lookup: no completion pass of its own
    pump(rt, 1)
    rt.eval("ASK_P(126626)")
    rt.execute("LK_ZERO()")
    for i in VAR_ATTACH + VAR_BLUEPRINT:
        rt.eval("ASK_P(%d)" % i)
        rt.eval("ASK_L(%d)" % i)
    check("armory lock: ten versions asked twice cost no completion read of their own",
          int(rt.eval("LK_N()")) == 0, str(rt.eval("LK_N()")))

    # one completion pass per tick, not one per ask
    pump(rt, 1)
    rt.execute("LK_ZERO()")
    for i in LOCK_IDS:
        rt.eval("ASK_P(%d)" % i)
    first = int(rt.eval("LK_N()"))
    for i in LOCK_IDS:
        rt.eval("ASK_L(%d)" % i)
    second = int(rt.eval("LK_N()"))
    pump(rt, 1)
    rt.eval("ASK_P(142465)")
    third = int(rt.eval("LK_N()"))
    check("armory lock: the 76 rows are read once a tick, not once an ask",
          first == 76 and second == 76 and third > 76,
          "%d / %d / %d" % (first, second, third))

    # a vm with no completion reader falls back to the record's own progress
    rp = lock_rt(lua51, pre="DROP_COMPLETE()\nSET_OC(75671, 250000, 0)")
    rp.execute("SET_OC(64771, 149999, 0) SET_OC(71381, 150000, 0)")
    load(rp)
    pump(rp, 1)
    check("armory lock: with no completion reader the record's own progress decides",
          rp.eval("ASK_P(142465)") is True and rp.eval("ASK_L(140458)") is True
          and rp.eval("ASK_L(119853)") is False,
          "%s / %s" % (rp.eval("ASK_L(140458)"), rp.eval("ASK_L(119853)")))
    rp.execute("SET_OC(64771, 150000, 0) SET_OC(71381, 149999, 0)")
    pump(rp, 1)
    check("armory lock: one xp short is short and one xp at the cost is done",
          rp.eval("ASK_L(119853)") is True and rp.eval("ASK_L(140458)") is False,
          "%s / %s" % (rp.eval("ASK_L(119853)"), rp.eval("ASK_L(140458)")))

    # a completion reader that raises leaves the items shut and says nothing
    rr = lock_rt(lua51)
    rr.execute("LKRAISE = true")
    load(rr)
    pump(rr, 1)
    check("armory lock: a raising completion reader keeps the items locked",
          rr.eval("ASK_P(142465)") is False and rr.eval("ASK_L(119853)") is False
          and not [ln for ln in lines_of(rr) if "attempt to" in ln],
          " | ".join([ln for ln in lines_of(rr) if "attempt to" in ln][:2]))

    # loading the file twice wraps nothing twice
    rt.execute("SNAP2()")
    before = len(lines_of(rt))
    rt.execute(LUA_TEXT[ARMORY])
    check("armory lock: loading the part again keeps one wrapper on each rule",
          rt.eval("SAME2()") is True and len(lines_of(rt)) == before
          and rt.eval("ASK_P(142465)") is False,
          " | ".join(lines_of(rt)[before:]))

    # a door that is rebuilt is wrapped again on the next tick
    rt.execute("REBUILD()")
    open_now = rt.eval("ASK_P(142465)")
    pump(rt, 1)
    check("armory lock: a rebuilt door is wrapped again on the next tick",
          open_now is True and rt.eval("ASK_P(142465)") is False
          and rt.eval("ANS(142465)") is True,
          "%s / %s" % (open_now, rt.eval("ASK_P(142465)")))

    # the three load orders end in the same answer
    if LOAD_ORDER == "harness":
        for order in ("harness", "alphabetical", "reversed"):
            r = lock_rt(lua51)
            for n in LOAD_ORDERS[order]:
                r.execute(LUA_TEXT[n])
            pump(r, 1)
            check("armory lock: %s order leaves all 76 locked and the door asking us" % order,
                  all(r.eval("ASK_P(%d)" % i[0]) is False for i in items)
                  and r.eval("ANS(142465)") is True
                  and r.eval("ANS(126608)") is True
                  and r.eval("ASK_P(126608)") is False,
                  "%s / %s" % (r.eval("ASK_P(142465)"), r.eval("ANS(126608)")))

        # the arm lands before the door exists and the pick is already seeded at the arm (C87 a4's own
        # failure: v4 never retried because seed had falsified the timer's guard)
        ra = lock_rt(lua51)
        ra.execute("SET_DVAR('pt_armory_ch', 'a=75671')")
        for n in LOAD_ORDERS["alphabetical"]:
            ra.execute(LUA_TEXT[n])
        first = armory_line(lines_of(ra))
        check("armory lock: armory before the door says lock=missing and names the seeded pick",
              len(first) == 1 and " lock=missing " in first[0] and " pick=75671 " in first[0]
              and " own=wrapped " in first[0],
              " | ".join(first))
        pump(ra, 1)
        late = [ln for ln in lines_of(ra) if "armory late " in ln]
        check("armory lock: one tick later the door is ours even with the pick seeded at the arm",
              ra.eval("ANS(142465)") is True and ra.eval("ASK_P(142465)") is False
              and late == ["progression_tuning: armory late lock"],
              " | ".join(late + [str(ra.eval("ASK_P(142465)"))]))
        pump(ra, 3)
        check("armory lock: and the late line is said once, not once a tick",
              [ln for ln in lines_of(ra) if "armory late " in ln] == late
              and ra.eval("ASK_P(142465)") is False,
              " | ".join(lines_of(ra)[-3:]))


CRAFT_REFS = ("radiation_blast", "smart_gun", "sniper_drone", "skybreak")


def craft_asks(rt):
    """The four armory streaks and the answer the table gets for each."""
    return [(r, rt.eval("CRAFT_ASK('%s')" % r)) for r in CRAFT_REFS]


def armory_craft(lua51):
    """the crafting table greys out the streaks the armory sells until they are earned."""
    rt = lock_rt(lua51, frontend=False)
    load(rt)
    pump(rt, 1)
    line = armory_line(lines_of(rt))
    check("craft: a match vm wraps the table lock and the arm line says which vm and which side",
          len(line) == 1 and line[0].startswith("progression_tuning: armory armed v12 vm=match ")
          and " vars=147+309 " in line[0] and " craft=wrapped " in line[0]
          and " own=wrapped " in line[0] and " obw=" not in line[0],
          " | ".join(line))
    check("craft: the four streaks the armory sells read locked at the table",
          all(v is True for _r, v in craft_asks(rt)), str(craft_asks(rt)))
    check("craft: an item that is not one of ours keeps the game's own answer",
          rt.eval("SET_CRAFT('equip_armorplate', true)") is None
          and rt.eval("SET_CRAFT('rcxd', false)") is None
          and rt.eval("CRAFT_ASK('equip_armorplate')") is True
          and rt.eval("CRAFT_ASK('rcxd')") is False
          and rt.eval("CRAFT_ASK('toma_strike')") is False,
          "%s / %s" % (rt.eval("CRAFT_ASK('equip_armorplate')"), rt.eval("CRAFT_ASK('rcxd')")))

    # its own row done opens its own streak and leaves the other three shut
    rt.execute("LK_DONE(69328)")
    pump(rt, 1)
    check("craft: the ion core opens once its own row is done",
          rt.eval("CRAFT_ASK('radiation_blast')") is False
          and rt.eval("CRAFT_ASK('smart_gun')") is True,
          "%s / %s" % (rt.eval("CRAFT_ASK('radiation_blast')"), rt.eval("CRAFT_ASK('smart_gun')")))
    rt.execute("LK_OPEN(69328)")
    pump(rt, 1)
    check("craft: and shuts again when that row is not done",
          rt.eval("CRAFT_ASK('radiation_blast')") is True, str(rt.eval("CRAFT_ASK('radiation_blast')")))

    # the switch, then the switch over all four
    rt.execute('SET_DVAR("zm_unlock_scorestreaks", "1")')
    pump(rt, 1)
    check("craft: the scorestreak switch opens all four at the table",
          all(v is False for _r, v in craft_asks(rt)), str(craft_asks(rt)))
    rt.execute('SET_DVAR("zm_unlock_scorestreaks", "0") SET_DVAR("zm_unlock_all", "1")')
    pump(rt, 1)
    check("craft: unlock everything opens all four at the table",
          all(v is False for _r, v in craft_asks(rt)), str(craft_asks(rt)))
    rt.execute('SET_DVAR("zm_unlock_all", "0")')
    pump(rt, 1)
    check("craft: with every switch off they read locked again",
          all(v is True for _r, v in craft_asks(rt)), str(craft_asks(rt)))

    # the game's own lock is still asked once for every item, ours or not
    rt.execute("CRAFT_ZERO()")
    rt.eval("CRAFT_ASK('radiation_blast')")
    rt.eval("CRAFT_ASK('equip_armorplate')")
    check("craft: the game's own lock is asked once for each ask and never doubled",
          int(rt.eval("CRAFT_N()")) == 2, str(rt.eval("CRAFT_N()")))

    # the tick keeps coming back to the same wrapper
    rt.execute("CRAFT_SNAP()")
    pump(rt, 3)
    check("craft: three more ticks keep one wrapper on the table",
          rt.eval("CRAFT_SAME()") is True and rt.eval("CRAFT_ASK('radiation_blast')") is True,
          str(rt.eval("CRAFT_SAME()")))

    # the hashed slot, the way the client stores members
    rh = lock_rt(lua51, frontend=False, pre="CRAFT_HASHED()")
    load(rh)
    pump(rh, 1)
    check("craft: a table that keeps the lock under its hash is wrapped too",
          rh.eval("CRAFT_ASK('radiation_blast')") is True
          and rh.eval("CRAFT_ASK('rcxd')") is False
          and " craft=wrapped " in armory_line(lines_of(rh))[0],
          " | ".join(armory_line(lines_of(rh))))

    # a raising original: our refs answer our rule, everything else stays shut
    rr = lock_rt(lua51, frontend=False, pre="CRAFT_RAISE(true)")
    load(rr)
    pump(rr, 1)
    check("craft: a raising game lock answers locked and never an error",
          rr.eval("CRAFT_ASK('radiation_blast')") is True and rr.eval("CRAFT_ASK('rcxd')") is True
          and count_line(lines_of(rr), "attempt to") == 0
          and count_line(lines_of(rr), "armory craft lock raised") == 1,
          " | ".join([ln for ln in lines_of(rr) if "craft lock" in ln or "attempt to" in ln][:3]))
    rr.execute("LK_DONE(69328)")
    pump(rr, 1)
    check("craft: and an earned streak still opens under that raise",
          rr.eval("CRAFT_ASK('radiation_blast')") is False,
          str(rr.eval("CRAFT_ASK('radiation_blast')")))

    # a menu vm leaves the table alone
    rm = lock_rt(lua51)
    load(rm)
    pump(rm, 1)
    check("craft: a menu vm says n a and leaves the table lock alone",
          " craft=n/a " in armory_line(lines_of(rm))[0]
          and rm.eval("CRAFT_ASK('radiation_blast')") is False
          and int(rm.eval("CRAFT_N()")) == 1,
          "%s / %s" % (" craft=n/a " in armory_line(lines_of(rm))[0], rm.eval("CRAFT_N()")))

    # no table at all in a match vm
    rn = lock_rt(lua51, frontend=False, pre="CRAFT_DROP()")
    load(rn)
    pump(rn, 1)
    check("craft: a match vm with no table says missing and wraps nothing",
          " craft=missing " in armory_line(lines_of(rn))[0], " | ".join(armory_line(lines_of(rn))))

    # the three load orders end in the same locked table
    if LOAD_ORDER == "harness":
        for order in ("harness", "alphabetical", "reversed"):
            r = lock_rt(lua51, frontend=False)
            for n in LOAD_ORDERS[order]:
                r.execute(LUA_TEXT[n])
            pump(r, 1)
            check("craft: %s order locks the ion core and leaves the rest alone" % order,
                  r.eval("CRAFT_ASK('radiation_blast')") is True
                  and r.eval("CRAFT_ASK('rcxd')") is False
                  and " craft=wrapped " in armory_line(lines_of(r))[0],
                  "%s / %s" % (r.eval("CRAFT_ASK('radiation_blast')"), r.eval("CRAFT_ASK('rcxd')")))


def armory_own(lua51):
    """C87 a5: the client's ownership getter answers not owned for our ids until earned."""
    rt = lock_rt(lua51)
    load(rt)
    pump(rt, 1)
    line = armory_line(lines_of(rt))
    check("armory own: the ownership getter is wrapped at the arm and the line says so",
          len(line) == 1 and " own=wrapped " in line[0], " | ".join(line))
    check("armory own: the five the user reported answer not owned",
          all(rt.eval("OWNED(%d)" % i) == 0 for i in LOCK_IDS),
          str([rt.eval("OWNED(%d)" % i) for i in LOCK_IDS]))
    rt.execute("OWNED_ZERO()")
    rt.eval("OWNED(142465)")
    check("armory own: our own ids never reach the client's getter",
          int(rt.eval("OWNED_N()")) == 0, str(rt.eval("OWNED_N()")))
    check("armory own: an id outside the 76 is the client's own answer, asked once",
          rt.eval("OWNED(126608)") == 1 and int(rt.eval("OWNED_N()")) == 1,
          "%s / %s" % (rt.eval("OWNED(126608)"), rt.eval("OWNED_N()")))
    rt.execute("OWNED_SNAP()")
    rt.execute(LUA_TEXT[ARMORY])
    check("armory own: loading the part again keeps one wrapper on the getter",
          rt.eval("OWNED_SAME()") is True and rt.eval("OWNED(142465)") == 0,
          str(rt.eval("OWNED_SAME()")))

    # the versions under a row: the attachment versions answer not owned, the blueprints are the clients own
    check("armory own: the 1911's six blueprints are the client's own answer, owned",
          all(rt.eval("OWNED(%d)" % i) == 1 for i in VAR_BLUEPRINT),
          str([rt.eval("OWNED(%d)" % i) for i in VAR_BLUEPRINT]))
    rt.execute("OWNED_ZERO()")
    check("armory own: and a blueprint ask reaches the client's getter",
          rt.eval("OWNED(%d)" % VAR_BLUEPRINT[0]) == 1 and int(rt.eval("OWNED_N()")) == 1,
          "%s / %s" % (rt.eval("OWNED(%d)" % VAR_BLUEPRINT[0]), rt.eval("OWNED_N()")))
    check("armory own: its four attachment versions answer not owned",
          all(rt.eval("OWNED(%d)" % i) == 0 for i in VAR_ATTACH),
          str([rt.eval("OWNED(%d)" % i) for i in VAR_ATTACH]))
    rt.execute("OWNED_ZERO()")
    check("armory own: and an attachment version never reaches the client's getter",
          rt.eval("OWNED(%d)" % VAR_ATTACH[0]) == 0 and int(rt.eval("OWNED_N()")) == 0,
          "%s / %s" % (rt.eval("OWNED(%d)" % VAR_ATTACH[0]), rt.eval("OWNED_N()")))
    check("armory own: a blueprint of a gun outside the 76 is the client's own answer",
          rt.eval("OWNED(%d)" % VAR_FOREIGN) == 1, str(rt.eval("OWNED(%d)" % VAR_FOREIGN)))

    rt.execute("LK_DONE(69320)")
    pump(rt, 1)
    check("armory own: the 1911's row done hands its id back and leaves the brake shut",
          rt.eval("OWNED(125186)") == 1
          and all(rt.eval("OWNED(%d)" % i) == 0 for i in (140458, 119853)),
          "%s / %s" % (rt.eval("OWNED(125186)"), rt.eval("OWNED(140458)")))
    rt.execute("LK_OPEN(69320)")
    pump(rt, 1)
    check("armory own: and takes the id back when that row is not done again, the blueprints stay owned",
          rt.eval("OWNED(125186)") == 0
          and all(rt.eval("OWNED(%d)" % i) == 1 for i in VAR_BLUEPRINT),
          "%s / %s" % (rt.eval("OWNED(125186)"), rt.eval("OWNED(%d)" % VAR_BLUEPRINT[0])))

    # the switches, the same ones the lock reads
    rt.execute('SET_DVAR("zm_unlock_weapons", "1")')
    pump(rt, 1)
    check("armory own: the weapon switch hands every weapon id back",
          rt.eval("OWNED(142465)") == 1
          and all(rt.eval("OWNED(%d)" % i) == 1 for i in VAR_BLUEPRINT)
          and rt.eval("OWNED(140458)") == 0,
          "%s / %s" % (rt.eval("OWNED(142465)"), rt.eval("OWNED(140458)")))
    rt.execute('SET_DVAR("zm_unlock_weapons", "0") SET_DVAR("zm_unlock_attachments", "1")')
    pump(rt, 1)
    check("armory own: the attachment switch hands both attachments back and no weapon",
          rt.eval("OWNED(140458)") == 1 and rt.eval("OWNED(119853)") == 1
          and rt.eval("OWNED(142465)") == 0 and rt.eval("OWNED(126337)") == 0,
          str([rt.eval("OWNED(%d)" % i) for i in (140458, 119853, 142465, 126337)]))
    rt.execute('SET_DVAR("zm_unlock_attachments", "0") SET_DVAR("zm_unlock_all", "1")')
    pump(rt, 1)
    check("armory own: unlock everything hands all 76 back on the getter too",
          all(rt.eval("OWNED(%d)" % i[0]) == 1 for i in items76()),
          str([rt.eval("OWNED(%d)" % i[0]) for i in items76() if rt.eval("OWNED(%d)" % i[0]) != 1]))
    rt.execute('SET_DVAR("zm_unlock_all", "0")')
    pump(rt, 1)
    check("armory own: and every switch off answers not owned again",
          all(rt.eval("OWNED(%d)" % i[0]) == 0 for i in items76()),
          str([rt.eval("OWNED(%d)" % i[0]) for i in items76() if rt.eval("OWNED(%d)" % i[0]) != 0]))

    # a version is the same table lookup the lock does, so no completion pass of its own
    tmp = LOCK_IDS + VAR_ATTACH + VAR_BLUEPRINT
    rt.eval("OWNED(%d)" % tmp[0])
    rt.execute("LK_ZERO()")
    for i in tmp:
        rt.eval("OWNED(%d)" % i)
    check("armory own: fifteen asks cost no completion read of their own",
          int(rt.eval("LK_N()")) == 0, str(rt.eval("LK_N()")))

    # a table that keeps the getter under its plain name, and a table rebuilt after the arm
    rh = lock_rt(lua51, pre="OWNED_PLAIN()")
    load(rh)
    pump(rh, 1)
    check("armory own: a getter the table keeps under its plain name is wrapped too",
          rh.eval("OWNED(142465)") == 0 and rh.eval("OWNED(126608)") == 1
          and " own=wrapped " in armory_line(lines_of(rh))[0],
          " | ".join(armory_line(lines_of(rh))))
    rh.execute("OWNED_PLAIN()")
    pump(rh, 1)
    check("armory own: a getter table rebuilt under a new key is wrapped on the next tick",
          rh.eval("OWNED(142465)") == 0 and rh.eval("OWNED(126608)") == 1,
          "%s / %s" % (rh.eval("OWNED(142465)"), rh.eval("OWNED(126608)")))

    # both spellings in one table: the hashed slot is the one the client's pin sits in and reads
    r2 = lock_rt(lua51, pre="OWNED_BOTH()")
    load(r2)
    pump(r2, 1)
    check("armory own: with both slots in the table the hashed one is the one wrapped",
          r2.eval("OWNED(142465)") == 0 and r2.eval("OWNED(126608)") == 1
          and r2.eval("OWNED_PLAIN_ASK(142465)") == 99,
          "%s / %s / %s" % (r2.eval("OWNED(142465)"), r2.eval("OWNED(126608)"),
                            r2.eval("OWNED_PLAIN_ASK(142465)")))

    # a getter that raises, and a vm without one
    rr = lock_rt(lua51, pre="OWNED_RAISE(true)")
    load(rr)
    pump(rr, 1)
    check("armory own: a raising getter never rethrows - not owned is the safe answer",
          rr.eval("OWNED(142465)") == 0 and rr.eval("OWNED(126608)") == 0
          and count_line(lines_of(rr), "attempt to") == 0,
          "%s / %s" % (rr.eval("OWNED(142465)"), rr.eval("OWNED(126608)")))
    rn = lock_rt(lua51, pre="OWNED_DROP()")
    load(rn)
    check("armory own: a vm with no getter says own=missing and wraps nothing",
          " own=missing " in armory_line(lines_of(rn))[0],
          " | ".join(armory_line(lines_of(rn))))

    # the match vm reads the same table
    rm = lock_rt(lua51, frontend=False)
    load(rm)
    pump(rm, 1)
    check("armory own: a match vm wraps the getter and answers not owned there too",
          " own=wrapped " in armory_line(lines_of(rm))[0] and rm.eval("OWNED(142465)") == 0
          and rm.eval("OWNED(126608)") == 1,
          " | ".join(armory_line(lines_of(rm))))

    # the three load orders end in the same ownership answer
    if LOAD_ORDER == "harness":
        for order in ("harness", "alphabetical", "reversed"):
            r = lock_rt(lua51)
            for n in LOAD_ORDERS[order]:
                r.execute(LUA_TEXT[n])
            pump(r, 1)
            check("armory own: %s order answers not owned for ours and owned for the rest" % order,
                  r.eval("OWNED(142465)") == 0 and r.eval("OWNED(%d)" % VAR_FOREIGN) == 1
                  and r.eval("OWNED(126608)") == 1,
                  "%s / %s" % (r.eval("OWNED(142465)"), r.eval("OWNED(126608)")))


GUN_REF = "sat_pi_alcor"
FOREIGN_REF = "sat_lm_hades"


def bp_rt(lua51, pre=""):
    """A door with the client's own blueprint test and our part over it."""
    bp = ",".join(str(i) for i in VAR_BLUEPRINT)
    head = ("SET_ITEMID('%s', 125186) SET_BPID('%s', {%s})\n"
            "SET_ITEMID('%s', %d) SET_BPID('%s', {%d})\n"
            "SET_BPID('sat_lm_typhon', {%d})\n" % (GUN_REF, GUN_REF, bp,
                                                  FOREIGN_REF, FOREIGN_BASE, FOREIGN_REF, VAR_FOREIGN,
                                                  VAR_FOREIGN))
    return lock_rt(lua51, pre=head + pre)


def blueprint_own(lua51):
    """C87 a6: the door's blueprint test answers not owned while the gun is locked."""
    rt = bp_rt(lua51)
    load(rt)
    pump(rt, 1)
    line = armory_line(lines_of(rt))
    check("blueprint test: the armory part names no blueprint test of its own",
          len(line) == 1 and " obw=" not in line[0] and " bpwin=" not in line[0], " | ".join(line))
    check("blueprint test: the client's own test would hand the armory gun to the picker",
          rt.eval("OBW_ORIG('%s')" % GUN_REF) is True and rt.eval("OBW('%s')" % GUN_REF) is False,
          "%s / %s" % (rt.eval("OBW_ORIG('%s')" % GUN_REF), rt.eval("OBW('%s')" % GUN_REF)))
    check("blueprint test: an armory gun reads not owned while its row is incomplete",
          rt.eval("OBW('%s')" % GUN_REF) is False, str(rt.eval("OBW('%s')" % GUN_REF)))
    check("blueprint test: and a gun outside the 76 keeps the client's own answer",
          rt.eval("OBW('%s')" % FOREIGN_REF) is True, str(rt.eval("OBW('%s')" % FOREIGN_REF)))
    rt.execute("BP_ZERO()")
    check("blueprint test: a ref the loot table does not name is delegated",
          rt.eval("OBW('sat_zz_nothing')") is False and rt.eval("BP_N()") == 1, str(rt.eval("BP_N()")))

    # the row is the only key, and the switches the same ones the door reads
    rt.execute("LK_DONE(69320)")
    pump(rt, 1)
    check("blueprint test: the 1911's row done opens it",
          rt.eval("OBW('%s')" % GUN_REF) is True, str(rt.eval("OBW('%s')" % GUN_REF)))
    rt.execute("LK_OPEN(69320)")
    pump(rt, 1)
    check("blueprint test: and shuts it again when that row is not done",
          rt.eval("OBW('%s')" % GUN_REF) is False, str(rt.eval("OBW('%s')" % GUN_REF)))
    rt.execute('SET_DVAR("zm_unlock_weapons", "1")')
    pump(rt, 1)
    check("blueprint test: the weapon switch opens it",
          rt.eval("OBW('%s')" % GUN_REF) is True, str(rt.eval("OBW('%s')" % GUN_REF)))
    rt.execute('SET_DVAR("zm_unlock_weapons", "0") SET_DVAR("zm_unlock_all", "1")')
    pump(rt, 1)
    check("blueprint test: unlock everything opens it",
          rt.eval("OBW('%s')" % GUN_REF) is True, str(rt.eval("OBW('%s')" % GUN_REF)))
    rt.execute('SET_DVAR("zm_unlock_all", "0")')
    pump(rt, 1)

    # the row stays locked with an owned blueprint under it
    check("blueprint test: the gun stays shut with an owned blueprint under it",
          rt.eval("OWNED(%d)" % VAR_BLUEPRINT[0]) == 1
          and rt.eval("ASK_P(%d)" % VAR_BLUEPRINT[0]) is False
          and rt.eval("OBW('%s')" % GUN_REF) is False,
          "%s / %s / %s" % (rt.eval("OWNED(%d)" % VAR_BLUEPRINT[0]),
                            rt.eval("ASK_P(%d)" % VAR_BLUEPRINT[0]),
                            rt.eval("OBW('%s')" % GUN_REF)))

    # one wrapper a vm, and the plain spelling
    rt.execute("OBW_SNAP()")
    pump(rt, 2)
    check("blueprint test: two more ticks keep one wrapper on the client's test",
          rt.eval("OBW_SAME()") is True and rt.eval("OBW('%s')" % GUN_REF) is False,
          str(rt.eval("OBW_SAME()")))
    rp = bp_rt(lua51, pre="OBW_PLAIN()")
    load(rp)
    pump(rp, 1)
    check("blueprint test: a test the table keeps under its plain name is wrapped too",
          rp.eval("OBW('%s')" % GUN_REF) is False, str(rp.eval("OBW('%s')" % GUN_REF)))

    # a raising test and a table without one
    rr = bp_rt(lua51, pre="BP_RAISE(true)")
    load(rr)
    pump(rr, 1)
    check("blueprint test: a raising client test answers not owned and never rethrows",
          rr.eval("OBW('%s')" % GUN_REF) is False and rr.eval("OBW('%s')" % FOREIGN_REF) is False
          and count_line(lines_of(rr), "attempt to") == 0,
          "%s / %s" % (rr.eval("OBW('%s')" % GUN_REF), rr.eval("OBW('%s')" % FOREIGN_REF)))
    rn = bp_rt(lua51, pre="DROP_BP()")
    load(rn)
    pump(rn, 1)
    check("blueprint test: a vm with no client test wraps nothing and still arms",
          rn.eval("OBW_SLOT()") is None and len(armory_line(lines_of(rn))) == 1
          and count_line(lines_of(rn), "attempt to") == 0,
          " | ".join(armory_line(lines_of(rn))))

    # a menu vm and the three load orders
    rm = bp_rt(lua51)
    load(rm)
    pump(rm, 1)
    check("blueprint test: the menu vm wraps the same member",
          rm.eval("OBW('%s')" % GUN_REF) is False, str(rm.eval("OBW('%s')" % GUN_REF)))
    if LOAD_ORDER == "harness":
        for order in ("harness", "alphabetical", "reversed"):
            r = bp_rt(lua51)
            for n in LOAD_ORDERS[order]:
                r.execute(LUA_TEXT[n])
            pump(r, 1)
            check("blueprint test: %s order answers not owned for the armory gun" % order,
                  r.eval("OBW('%s')" % GUN_REF) is False and r.eval("OBW('%s')" % FOREIGN_REF) is True,
                  "%s / %s" % (r.eval("OBW('%s')" % GUN_REF), r.eval("OBW('%s')" % FOREIGN_REF)))


def blueprint_list(lua51):
    """C87 a4 v12: the builds window lists every blueprint id, in any lock state."""
    bp, att = blueprints(), attachment_versions()
    check("blueprint list: the table splits into 309 weapon ids and 147 attachment ones, none shared",
          len(bp) == 309 and len(att) == 147 and not (set(bp) & set(att)),
          "%d / %d" % (len(bp), len(att)))
    check("blueprint list: the armory part is v12 and the window has moved to the lock door",
          'local VERSION = "v12"' in LUA_TEXT[ARMORY]
          and "LISTING" not in LUA_TEXT[ARMORY] and "BPID" not in LUA_TEXT[ARMORY]
          and "getmodifications" not in LUA_TEXT[ARMORY]
          and LUA_TEXT[PRISON].count('"getmodifications"') == 1
          and LUA_TEXT[ARMORY].count('"getitemnamebyid"') == 1
          and LUA_TEXT[ARMORY].count('"getweapondataforref"') == 1,
          "v12 pins")

    rt = list_rt(lua51)
    rt.execute("GM_SET({151472, 153766, 142465, %d})" % VAR_FOREIGN)
    load(rt)
    pump(rt, 1)
    check("blueprint list: outside the window every blueprint of the 76 reads locked",
          all(rt.eval("ASK_P(%d)" % i) is False for i in bp)
          and all(rt.eval("ASK_L(%d)" % i) is False for i in bp),
          str([i for i in bp if rt.eval("ASK_P(%d)" % i) is not False][:4]))
    check("blueprint list: and so does a blueprint of a gun outside the 76",
          rt.eval("ASK_P(%d)" % VAR_FOREIGN) is False and rt.eval("ASK_L(%d)" % VAR_FOREIGN) is False,
          "%s / %s" % (rt.eval("ASK_P(%d)" % VAR_FOREIGN), rt.eval("ASK_L(%d)" % VAR_FOREIGN)))
    rt.execute("OWNED_ZERO()")
    check("blueprint list: a blueprint id is the client's own answer again",
          rt.eval("OWNED(151472)") == 1 and int(rt.eval("OWNED_N()")) == 1
          and rt.eval("OWNED(142465)") == 0,
          "%s / %s" % (rt.eval("OWNED(151472)"), rt.eval("OWNED_N()")))
    check("blueprint list: the 76 base ids and the 147 attachment versions stay not owned",
          all(rt.eval("OWNED(%d)" % i[0]) == 0 for i in items76())
          and all(rt.eval("OWNED(%d)" % i) == 0 for i in att),
          str([i[0] for i in items76() if rt.eval("OWNED(%d)" % i[0]) != 0][:4]))

    # the builds call is the only thing that opens the window, and only while it runs
    rt.execute("GM_CLEAR()")
    check("blueprint list: a builds call lists every blueprint and never the base id",
          int(rt.eval("GM_COUNT(%s)" % BUILDS)) == 3
          and rt.eval("GM_SAW(151472)") is True and rt.eval("GM_SAW(153766)") is True
          and rt.eval("GM_SAW(%d)" % VAR_FOREIGN) is True
          and rt.eval("GM_SAW(142465)") is False,
          str(rt.eval("GM_COUNT(%s)" % BUILDS)))
    check("blueprint list: and the window is shut the moment that call returns",
          rt.eval("ASK_P(151472)") is False and rt.eval("ASK_L(151472)") is False,
          "%s / %s" % (rt.eval("ASK_P(151472)"), rt.eval("ASK_L(151472)")))
    rt.execute("GM_CLEAR()")
    check("blueprint list: the all list counts every id and opens no window",
          int(rt.eval("GM_COUNT(%s)" % ALL_LIST)) == 4 and rt.eval("GM_SAW(151472)") is False,
          "%s / %s" % (rt.eval("GM_COUNT(%s)" % ALL_LIST), rt.eval("GM_SAW(151472)")))
    bad = []
    for name, opt in SHAPES:
        rt.execute("GM_CLEAR()")
        rt.eval("GM_COUNT(%s)" % opt)
        if rt.eval("GM_SAW(151472)") is not False:
            bad.append((name, rt.eval("GM_SAW(151472)")))
    check("blueprint list: no other option shape opens the window", bad == [], str(bad))
    rt.eval("GM_COUNT(%s)" % BUILDS)
    check("blueprint list: the option table reaches the client untouched",
          rt.eval("GM_KEPT()") == "true/true", str(rt.eval("GM_KEPT()")))

    # an error and a nested call both leave the counter where they found it
    rt.execute("GM_RAISE_ON(true)")
    check("blueprint list: a getter that raises hands back an empty list and never rethrows",
          rt.eval("GM_TRY(%s)" % BUILDS) == "0" and count_line(lines_of(rt), "attempt to") == 0,
          str(rt.eval("GM_TRY(%s)" % BUILDS)))
    check("blueprint list: and the counter is back at zero after the error",
          rt.eval("ASK_P(151472)") is False and rt.eval("ASK_L(151472)") is False,
          "%s / %s" % (rt.eval("ASK_P(151472)"), rt.eval("ASK_L(151472)")))
    rt.execute("GM_RAISE_ON(false)")
    check("blueprint list: the same call works again once the getter answers",
          int(rt.eval("GM_COUNT(%s)" % BUILDS)) == 3 and rt.eval("ASK_P(151472)") is False,
          str(rt.eval("GM_COUNT(%s)" % BUILDS)))
    rt.execute("GM_NEST_ON(1)")
    check("blueprint list: a nested builds call keeps the window open for the outer one",
          int(rt.eval("GM_COUNT(%s)" % BUILDS)) == 3, str(rt.eval("GM_COUNT(%s)" % BUILDS)))
    rt.execute("GM_NEST_ON(0)")
    check("blueprint list: and the counter is still zero after the nested pair",
          rt.eval("ASK_P(151472)") is False, str(rt.eval("ASK_P(151472)")))
    rt.execute("GM_TWO_ON(true)")
    check("blueprint list: every value the client returned comes back through the wrapper",
          rt.eval("GM_BOTH(%s)" % BUILDS) == "table/second", str(rt.eval("GM_BOTH(%s)" % BUILDS)))
    rt.execute("GM_TWO_ON(false)")

    # a match vm wraps no builds getter at all
    rm = list_rt(lua51, frontend=False)
    rm.execute("GM_SET({151472, 153766})")
    load(rm)
    pump(rm, 1)
    check("blueprint list: a match vm wraps no builds getter",
          int(rm.eval("GM_COUNT(%s)" % BUILDS)) == 0 and rm.eval("ASK_P(151472)") is False,
          str(rm.eval("GM_COUNT(%s)" % BUILDS)))

    # the temporary check block is gone from the part and from this replay
    check("blueprint list: the temporary check block and its reads are gone",
          "armory check" not in LUA_TEXT[ARMORY] and "chk_" not in LUA_TEXT[ARMORY]
          and "check_lines" not in LUA_TEXT[ARMORY] and "LIST_ORIG" not in LUA_TEXT[ARMORY]
          and '"sat_sm_civet"' not in LUA_TEXT[ARMORY]
          and not list_lines(lines_of(rt)),
          " | ".join(list_lines(lines_of(rt))))

    # the rule itself, in every state a blueprint can be in
    blueprint_rule(lua51)


def blueprint_rule(lua51):
    """The user's rule: listed always, unlocked only when the gun is open and the switch is on."""
    states = [("off", "0"), ("on", "1")]
    for name, extra, base in (("open", (), True), ("locked", (FOREIGN_BASE,), False)):
        rt = list_rt(lua51, extra=extra)
        rt.execute("GM_SET({%d, %d})" % (VAR_FOREIGN, FOREIGN_BASE))
        load(rt)
        pump(rt, 1)
        bad = []
        for swname, sw in states:
            for allname, allon in states:
                rt.execute('SET_DVAR("zm_unlock_blueprints", "%s") SET_DVAR("zm_unlock_all", "%s")'
                           % (sw, allon))
                pump(rt, 12)
                want = allon == "1" or (base and sw == "1")
                got = (rt.eval("ASK_P(%d)" % VAR_FOREIGN) is True
                       and rt.eval("ASK_L(%d)" % VAR_FOREIGN) is True)
                rt.execute("GM_CLEAR()")
                rt.eval("GM_COUNT(%s)" % BUILDS)
                listed = rt.eval("GM_SAW(%d)" % VAR_FOREIGN) is True
                if got != want or not listed:
                    bad.append((swname, allname, got, want, listed))
        check("blueprint rule: a gun outside the 76 with its gun %s follows the switch and lists" % name,
              bad == [], str(bad))

    # an armory gun: its own row opens the gun, and the switch still gates the blueprint
    rt = list_rt(lua51)
    rt.execute("GM_SET({%d, 125186})" % VAR_BLUEPRINT[0])
    load(rt)
    pump(rt, 1)
    bad = []
    for bname in ("locked", "open"):
        rt.execute("LK_DONE(69320)" if bname == "open" else "LK_OPEN(69320)")
        pump(rt, 1)
        for swname, sw in states:
            for allname, allon in states:
                rt.execute('SET_DVAR("zm_unlock_blueprints", "%s") SET_DVAR("zm_unlock_all", "%s")'
                           % (sw, allon))
                pump(rt, 12)
                want = allon == "1" or (bname == "open" and sw == "1")
                got = (rt.eval("ASK_P(%d)" % VAR_BLUEPRINT[0]) is True
                       and rt.eval("ASK_L(%d)" % VAR_BLUEPRINT[0]) is True)
                rt.execute("GM_CLEAR()")
                rt.eval("GM_COUNT(%s)" % BUILDS)
                listed = rt.eval("GM_SAW(%d)" % VAR_BLUEPRINT[0]) is True
                if got != want or not listed:
                    bad.append((bname, swname, allname, got, want, listed))
    check("blueprint rule: an armory gun's blueprints follow its row and the switch and list",
          bad == [], str(bad))

    # the gun row never opens on a blueprint alone
    rm = list_rt(lua51)
    rm.execute("SET_ITEMID('%s', %d) SET_BPID('%s', {%d})" % (FOREIGN_REF, FOREIGN_BASE,
                                                              FOREIGN_REF, VAR_FOREIGN))
    load(rm)
    pump(rm, 1)
    check("blueprint rule: with its gun open an owned blueprint is the client's own answer",
          rm.eval("OBW_ORIG('%s')" % FOREIGN_REF) is True
          and rm.eval("OBW('%s')" % FOREIGN_REF) is True,
          "%s / %s" % (rm.eval("OBW_ORIG('%s')" % FOREIGN_REF), rm.eval("OBW('%s')" % FOREIGN_REF)))
    rl = list_rt(lua51, extra=(FOREIGN_BASE,))
    rl.execute("SET_ITEMID('%s', %d) SET_BPID('%s', {%d})" % (FOREIGN_REF, FOREIGN_BASE,
                                                              FOREIGN_REF, VAR_FOREIGN))
    load(rl)
    pump(rl, 1)
    check("blueprint rule: and an owned blueprint never opens a locked gun",
          rl.eval("OBW_ORIG('%s')" % FOREIGN_REF) is True
          and rl.eval("OBW('%s')" % FOREIGN_REF) is False,
          "%s / %s" % (rl.eval("OBW_ORIG('%s')" % FOREIGN_REF), rl.eval("OBW('%s')" % FOREIGN_REF)))

    # an id that is no blueprint is left alone
    rn = list_rt(lua51)
    load(rn)
    pump(rn, 1)
    before = (rn.eval("ANS(200000)"), rn.eval("OPN(200000)"), rn.eval("ASK_P(200000)"))
    rn.execute('SET_DVAR("zm_unlock_blueprints", "1")')
    pump(rn, 1)
    check("blueprint rule: a non blueprint id answers exactly as it did",
          (rn.eval("ANS(200000)"), rn.eval("OPN(200000)"), rn.eval("ASK_P(200000)")) == before,
          "%s vs %s" % (str(before), str((rn.eval("ANS(200000)"), rn.eval("OPN(200000)")))))

    # no base getter means no base gate, and one line says so
    rg = list_rt(lua51, pre="DROP_BASE()")
    load(rg)
    pump(rg, 1)
    check("blueprint rule: with no base getter the switch alone decides and the part says so",
          has_line(lines_of(rg), "blueprint lock: no WEAPON.getbaseweaponlootidfromblueprint")
          and rg.eval("ASK_P(%d)" % VAR_FOREIGN) is False,
          " | ".join([ln for ln in lines_of(rg) if "blueprint" in ln][:2]))

    # the three load orders end in the same answer
    if LOAD_ORDER == "harness":
        for order in ("harness", "alphabetical", "reversed"):
            r = list_rt(lua51)
            r.execute('SET_DVAR("zm_unlock_blueprints", "1")')
            for n in LOAD_ORDERS[order]:
                r.execute(LUA_TEXT[n])
            pump(r, 1)
            check("blueprint rule: %s order opens the blueprint once the switch is on" % order,
                  r.eval("ASK_P(%d)" % VAR_FOREIGN) is True
                  and r.eval("ASK_P(%d)" % FOREIGN_BASE) is True,
                  "%s / %s" % (r.eval("ASK_P(%d)" % VAR_FOREIGN), r.eval("ASK_P(%d)" % FOREIGN_BASE)))


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
            g12_door(lua51, ls)
            s1_reticle(lua51, ls)
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
            week_sticker(lua51)
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
            diag_qb_gate(lua51)
            diag_qb_weeklies(lua51)
            diag_qb_kinds(lua51)
            diag_qb_owned(lua51)
            diag_qb_ladder(lua51)
            diag_qb_sources(lua51)
            diag_qb_dvar(lua51)
            diag_qb_reticle(lua51)
            diag_qb_rewards(lua51)
            g32_cards(lua51)
            g32_qb20(lua51)
            g32_card_files(lua51)
            g32_card_path(lua51)
            g32_card_miss(lua51)
            g32_newtables(lua51)
            g32_speed(lua51)
            g32_open(lua51)
            g32_store(lua51)
            g32_toggle(lua51)
            debug_toggles(lua51)
            dbg_toggle_prestige(lua51)
            g32_prestige_sets(lua51)
            g32_ask_cost(lua51)
            g32_ask_native(lua51)
            g32_ask_epoch(lua51)
            g32_ask_logs(lua51)
            g32_ask_cards(lua51)
            g32_buy(lua51)
            g32_w5(lua51)
            g32_earn_pin(lua51)
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
            utc_fill(lua51)
            options_rows(lua51)
            options_layers(lua51)
            tokens_channel(lua51)
            armory_gate(lua51)
            armory_pick(lua51)
            armory_queue(lua51)
            armory_seed(lua51)
            armory_advance(lua51)
            armory_card(lua51)
            armory_lock(lua51)
            armory_craft(lua51)
            armory_own(lua51)
            blueprint_own(lua51)
            blueprint_list(lua51)

        for order in LOAD_ORDERS:
            LOAD_ORDER = order
            info("replay: the %d parts load in %s order" % (len(LUA_FILES), order))
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
    for path in ([MODJSON] + [os.path.join(LUA_DIR, n) for n in TEXT_FILES]
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







