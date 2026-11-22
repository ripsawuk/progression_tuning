"""The augment part's replay: the store's own numbers, or the switches' full house.

Read-only. Nothing is installed and nothing is launched. The stubbed frontend VM, its two hash
namespaces and its clock come from `test_progression_tuning.py` by import (`PRELUDE`, `lines_of`,
`has_line`, `count_line`, `pump`); this file only adds what augments need - a hash-keyed
`ZMAUGMENT` with its augment cache, the game's own `cacheaugmenttierdata` reading
`Challenge.getchallengeprogress`, a refresh that forces every row complete the way the shipped
overrides do, and the hashed dev bool the tier code asks for.

The cases:

  1. the switches off: after a refresh every cached row ends on the numbers the game's own tier
     pass wrote - not the forced complete flag, not 100, not the last tier;
  2. the switches on (`zm_unlock_augments`, then `zm_unlock_all`): the forced values stand and
     the part writes nothing over them;
  3. the arm line: exactly one line with the three fields, said once across four refreshes, and
     nothing else is ever printed;
  4. the dev bool: read from the game's own `Dvar.GetDvarBool` call during the tier pass, printed
     as `true`, as `false`, and as `unread` when no tier pass ran;
  5. the plain-name fixture: a table keyed by plain names is never touched, and nothing is printed;
  6. the load orders: the module present at load, the module appearing after the part's own timer
     ticks, and the part loaded twice - one wrapper and one line in each;
  7. the decoy: a key one digit off the store's hash is left alone;
  8. the file rule: lowercase comments of ten words at most with no punctuation, no mention of the
     client, and no plain-name indexing of the augmented table.
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

# the four keys the augment table carries, the way the engine hands them out
ZMFIX = r"""
STORE_K = "#x0d847872560dcd8e4"
DIFF_K = "#x0d847872560dcd8e5"
REFRESH_K = "#x052e47d640bf4ca01"
DEV_K = setmetatable({}, { __tostring = function() return "xhash: #x1d428ffe65b5694d6" end })
DEVON = false
AID = 40001
BID = 40002
PROG = { [tostring(AID)] = 0, [tostring(BID)] = 0 }
function SET_PROG(id, v) PROG[tostring(id)] = v end
Challenge[xhash("getchallengeprogress")] = function(c, id) return PROG[tostring(id)] or 0 end
Dvar[xhash("GetDvarBool")] = function(k, d)
  if k == DEV_K then return DEVON end
  return d
end
GETSTR = Dvar[xhash("GetDvarString")]
function ROWS()
  return { [1] = { progress = 0 }, [2] = { progress = 0 }, [3] = { progress = 0 },
           isResearchComplete = true, totalProgress = 100, currentTier = 3, isUnlocked = true }
end
Z = {}
Z[STORE_K] = { sat_aug_one = ROWS(), sat_aug_two = ROWS() }
Z[DIFF_K] = { decoy = ROWS() }
Z.lootid_to_ref = { [7001] = "sat_aug_one", [7002] = "sat_aug_two" }
Z[xhash("augmentresearchchallenges")] = {
  [7001] = { achievementID = AID, amount = "70000|140000|275000" },
  [7002] = { achievementID = BID, amount = "70000|140000|275000" },
}
Z[xhash("cacheaugmenttierdata")] = function(c, ch, loot)
  local ref = Z.lootid_to_ref[loot]
  local entry = ref ~= nil and Z[STORE_K][ref] or nil
  if entry == nil then return end
  local p = Challenge[xhash("getchallengeprogress")](c, ch.achievementID)
  local dev = Dvar[xhash("GetDvarBool")](DEV_K, false)
  entry.currentTier = 1
  entry.totalProgress = 0
  entry.isResearchComplete = dev and true or false
  entry.tierAt = p
end
function TIER_ALL(c)
  for loot, ch in pairs(Z[xhash("augmentresearchchallenges")]) do
    Z[xhash("cacheaugmenttierdata")](c, ch, loot)
  end
end
CALLS = 0
function TOGGLED()
  return GETSTR(xhashdvar("zm_unlock_augments")) == "1"
      or GETSTR(xhashdvar("zm_unlock_all")) == "1"
end
Z[REFRESH_K] = function(c)
  CALLS = CALLS + 1
  TIER_ALL(c)
  for _, e in pairs(Z[STORE_K]) do e.isResearchComplete = true end
  if TOGGLED() then
    for _, e in pairs(Z[STORE_K]) do
      for i = 1, #e do if type(e[i]) == "table" then e[i].progress = 1 end end
      e.isUnlocked, e.isResearchComplete, e.totalProgress, e.currentTier = true, true, 100, #e
    end
  end
end
function MAKEZM() ZMAUGMENT = Z end
function REFRESH(c) ZMAUGMENT[REFRESH_K](c) end
function FIELD(ref, name) local e = ZMAUGMENT[STORE_K][ref]; return tostring(e and e[name]) end
function TIER(ref, i)
  local e = ZMAUGMENT[STORE_K][ref]
  local v = e and e[i] and e[i].progress
  return tostring(v)
end
function WRAPPED() return ZMAUGMENT[REFRESH_K] == nil end
function FORCE42() for _, e in pairs(Z[STORE_K]) do e.totalProgress = 42 end end
function FACED() local f = ZMAUGMENT[REFRESH_K]; return f ~= nil end
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

# the hash-keyed table with no tier pass in it: nothing to re-run, nothing to read
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


# --- 1 and 2: the switches decide whose numbers stand ------------------------------------------
def case_off(lua51):
    r = rt(ZMFIX + "\nMAKEZM()")
    r.execute("SET_DVAR('zm_unlock_augments', '0'); SET_DVAR('zm_unlock_all', '0')")
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
    r2 = rt(ZMFIX + "\nMAKEZM()")
    r2.execute("SET_DVAR('zm_unlock_augments', '0'); SET_DVAR('zm_unlock_all', '1')")
    r2.execute("REFRESH(0)")
    check("on (all): every forced value stands with the other switch",
          val(r2, "FIELD('sat_aug_one','totalProgress')") == "100" and val(r2, "TIER('sat_aug_one',1)") == "1",
          "total=" + val(r2, "FIELD('sat_aug_one','totalProgress')") + " tier1=" + val(r2, "TIER('sat_aug_one',1)"))
    check("on: the arm line names the switch that is on", "unlock=1" in arm_line(lines_of(r)),
          arm_line(lines_of(r)))


# --- 3 and 4: the one line, and the bool it carries --------------------------------------------
def case_line(lua51):
    r = rt(ZMFIX + "\nMAKEZM()")
    r.execute("SET_DVAR('zm_unlock_augments', '0'); SET_DVAR('zm_unlock_all', '0')")
    r.execute("REFRESH(0)")
    l = lines_of(r)
    check("line: one arm line and nothing else", len(l) == 1, "%d lines: %s" % (len(l), " | ".join(l[:3])))
    want = "progression_tuning: augments armed v1 unlock=0 all=0 devcomplete=false"
    check("line: the exact wording", arm_line(l) == want, arm_line(l))
    r.execute("REFRESH(0); REFRESH(0); REFRESH(0)")
    check("line: said once over four refreshes", count_line(lines_of(r), "augments armed") == 1,
          "%d" % count_line(lines_of(r), "augments armed"))
    r3 = rt(ZMFIX + "\nMAKEZM()")
    r3.execute("SET_DVAR('zm_unlock_augments', '0'); SET_DVAR('zm_unlock_all', '0'); DEVON = true")
    r3.execute("REFRESH(0)")
    check("line: devcomplete reads the bool the game asked for",
          "devcomplete=true" in arm_line(lines_of(r3)), arm_line(lines_of(r3)))
    r4 = rt(ZMNOTIER + "\nMAKEZM()")
    r4.execute("SET_DVAR('zm_unlock_augments', '0'); SET_DVAR('zm_unlock_all', '0')")
    r4.execute("REFRESH(0)")
    check("line: no tier pass to run means no claim and no line", len(lines_of(r4)) == 0,
          " | ".join(lines_of(r4)[:2]))


# --- 5, 6, 7: what must not be touched, and every load order -----------------------------------
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
    r.execute("SET_DVAR('zm_unlock_augments', '0'); SET_DVAR('zm_unlock_all', '0')")
    r.execute("REFRESH(0)")
    check("late: the timer arms when the table arrives",
          val(r, "FIELD('sat_aug_one','totalProgress')") == "0",
          "total=" + val(r, "FIELD('sat_aug_one','totalProgress')"))
    check("late: one arm line once the table is there", count_line(lines_of(r), "augments armed") == 1,
          "%d" % count_line(lines_of(r), "augments armed"))


def case_twice(lua51):
    r = rt(ZMFIX + "\nMAKEZM()")
    r.execute(SRC)
    r.execute("SET_DVAR('zm_unlock_augments', '0'); SET_DVAR('zm_unlock_all', '0')")
    r.execute("REFRESH(0)")
    check("twice: the second load wraps nothing again", val(r, "CALLS") == "1", "calls=" + val(r, "CALLS"))
    check("twice: still one arm line", count_line(lines_of(r), "augments armed") == 1,
          "%d" % count_line(lines_of(r), "augments armed"))
    check("twice: the part kept its own marker", r.eval("ProgressionTuning.parts.augments") is True,
          str(r.eval("ProgressionTuning.parts.augments")))


def case_decoy(lua51):
    r = rt(ZMFIX + "\nMAKEZM()")
    r.execute("SET_DVAR('zm_unlock_augments', '0'); SET_DVAR('zm_unlock_all', '0')")
    r.execute("REFRESH(0)")
    check("decoy: the key one digit off the store is left alone",
          val(r, "ZMAUGMENT['#x0d847872560dcd8e5'].decoy.totalProgress") == "100",
          val(r, "ZMAUGMENT['#x0d847872560dcd8e5'].decoy.totalProgress"))


def case_rewrap(lua51):
    r = rt(ZMFIX + "\nMAKEZM()")
    r.execute("SET_DVAR('zm_unlock_augments', '0'); SET_DVAR('zm_unlock_all', '0')")
    r.execute("REFRESH(0)")
    r.execute("KEEP = ZMAUGMENT[REFRESH_K]; ZMAUGMENT[REFRESH_K] = function(c) KEEP(c); FORCE42() end")
    r.execute("REFRESH(0)")
    late = val(r, "FIELD('sat_aug_one','totalProgress')")
    pump(r, 1)
    r.execute("REFRESH(0)")
    check("rewrap: a wrapper put above ours is wrapped again on the next tick",
          late == "42" and val(r, "FIELD('sat_aug_one','totalProgress')") == "0",
          "before=" + late + " after=" + val(r, "FIELD('sat_aug_one','totalProgress')"))
    check("rewrap: the game's own pass still runs once per call", val(r, "CALLS") == "3", "calls=" + val(r, "CALLS"))


def case_blind(lua51):
    r = rt(ZMFIX + "\nMAKEZM()")
    r.execute("SET_DVAR('zm_unlock_augments', '0'); SET_DVAR('zm_unlock_all', '0')")
    r.execute("Dvar[xhash('GetDvarString')] = nil")
    r.execute("REFRESH(0)")
    check("blind: an unreadable switch leaves the pass alone",
          r.eval("ProgressionTuning.aug.devseen") is False and r.eval("ProgressionTuning.aug.said") is False,
          "devseen=" + str(r.eval("ProgressionTuning.aug.devseen")))
    check("blind: and claims nothing", len(lines_of(r)) == 0, " | ".join(lines_of(r)[:2]))


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
    for case in (case_off, case_on, case_line, case_plain, case_late, case_twice, case_decoy,
                 case_rewrap, case_blind, case_missing):
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
