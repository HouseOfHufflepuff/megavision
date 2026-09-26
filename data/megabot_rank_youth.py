import csv, gzip, re, json, collections, unicodedata, statistics, sys
from datetime import date

# ---------- 1. rebuild the FULL eligible pool (same filters as the top-100 build) ----------
src = open("/tmp/build_final_dob.py").read()
src = src.split("rows = sorted(by_lastkey.values()")[0]          # stop before the top-100 cut
ns = {}
exec(compile(src, "pool", "exec"), ns)
by_lastkey, fc_match, last_key, nxgn, fold = ns["by_lastkey"], ns["fc_match"], ns["last_key"], ns["nxgn"], ns["fold"]

# goal.com NXGN 2026 rank = position in the hardcoded list (1..50)
gc_rank = {}
for i, nm in enumerate(nxgn, 1):
    m = fc_match(nm)
    if m:
        k = last_key(m["long_name"] or m["short_name"])
        if k in by_lastkey: gc_rank[k] = i
pool = []
for k, v in by_lastkey.items():
    if v["pot"] is None: continue
    v = dict(v); v["key"] = k; v["gc_rank"] = gc_rank.get(k)
    pool.append(v)
print("pool size:", len(pool), "| with goal.com rank:", sum(1 for p in pool if p["gc_rank"]))

# ---------- 2. Transfermarkt 25/26 stats ----------
def toks(s): return {t for t in fold(s).replace("-", " ").split() if len(t) > 2}
comps = {r["competition_id"]: r for r in csv.DictReader(gzip.open("competitions.csv.gz", "rt", encoding="utf-8"))}
club_comps = {k for k, v in comps.items() if v["type"] != "national_team_competition"}
COVERED_LEAGUES = {"ES1","IT1","GB1","L1","PO1","NL1","TR1","FR1","UKR1","BE1","RU1","SC1","GR1","DK1"}  # full 25/26 league coverage in TM dataset
by_dob = collections.defaultdict(list)
for p in csv.DictReader(gzip.open("players.csv.gz", "rt", encoding="utf-8")):
    d = (p["date_of_birth"] or "")[:10]
    if d >= "2006-10-02": by_dob[d].append(p)

def find(c):
    ct = toks(c["name"]); best = None
    for p in by_dob.get(c["dob"].isoformat(), []):
        pt = toks(p["name"]); ov = len(ct & pt)
        last = fold(p["name"]).replace("-", " ").split()[-1] if fold(p["name"]) else ""
        if ov >= 1 and (last in ct or ov >= 2) and (best is None or ov > best[0]): best = (ov, p)
    return best[1] if best else None

pid2idx = {}
for i, c in enumerate(pool):
    p = find(c); c["tm"] = p
    if p: pid2idx[p["player_id"]] = i
agg = collections.defaultdict(lambda: {"g": 0, "a": 0, "gp": 0, "by": collections.Counter()})
for a in csv.DictReader(gzip.open("appearances.csv.gz", "rt", encoding="utf-8")):
    if a["player_id"] in pid2idx and "2025-07-01" <= a["date"] < "2026-07-01" and a["competition_id"] in club_comps:
        s = agg[a["player_id"]]
        if int(a["minutes_played"] or 0) > 0: s["gp"] += 1; s["by"][a["player_club_id"]] += 1
        s["g"] += int(a["goals"] or 0); s["a"] += int(a["assists"] or 0)

club_dom = {r["club_id"]: r["domestic_competition_id"] for r in csv.DictReader(gzip.open("clubs.csv.gz", "rt", encoding="utf-8"))}
moves = collections.defaultdict(list)          # player_id -> transfers/loans inside the 25/26 season window
for t in csv.DictReader(gzip.open("transfers.csv.gz", "rt", encoding="utf-8")):
    if t["player_id"] in pid2idx and "2025-07-01" <= t["transfer_date"] <= "2026-06-30":
        moves[t["player_id"]].append(t)
GENERIC = {"fc","cf","club","football","afc","sc","sv","vfl","vfb","fk","bk","ik","if","ss","ac","as","sk","kv","kvc","krc","rsc","kaa","de","the","of","clube","calcio","sad","ud","1"}
YOUTH = re.compile(r"\b(U\d{2}|II|B|Futures|NXT|Castilla|Jong|Youth|Academy|Reserves?)\b|Castilla", re.I)
def ctoks(s): return {t for t in fold(s).replace("-", " ").split() if t not in GENERIC and len(t) > 1}
def same_club(a, b):
    A, B = ctoks(a), ctoks(b)
    return bool(A & B) or any(x[:4] == y[:4] for x in A for y in B if len(x) >= 4 and len(y) >= 4)
for c in pool:
    p = c["tm"]; c["why"] = ""
    if not p: c["stat"] = "n/a"; c["why"] = "no TM match"; c["gp"] = c["g"] = c["a"] = None
    else:
        dom = p.get("current_club_domestic_competition_id")
        s = agg.get(p["player_id"])
        def ok_side(cid, name):    # covered league, or an academy/reserve side of a club (ignored); anything else = uncovered senior club
            return club_dom.get(cid) in COVERED_LEAGUES or bool(YOUTH.search(name or ""))
        stayed = all(ok_side(t["from_club_id"], t["from_club_name"]) and ok_side(t["to_club_id"], t["to_club_name"]) for t in moves.get(p["player_id"], []))
        if dom not in COVERED_LEAGUES: c["stat"] = "n/a"; c["why"] = "league not covered"
        elif not same_club(c["club"], p["current_club_name"]): c["stat"] = "n/a"; c["why"] = "loan/club mismatch"
        elif not stayed: c["stat"] = "n/a"; c["why"] = "moved from/to uncovered league"
        else: c["stat"] = "TM" if s else "TM-zero"
        if c["stat"] == "n/a": c["gp"] = c["g"] = c["a"] = None
        else: c["gp"], c["g"], c["a"] = (s["gp"], s["g"], s["a"]) if s else (0, 0, 0)
    c["ga"] = None if c["g"] is None else c["g"] + c["a"]

HL = json.load(open("/Users/houseofhufflepuff/Development/mega/megavision/data/youth_senior_stats.json"))
HLC = json.load(open("/Users/houseofhufflepuff/Development/mega/megavision/data/highlightly_cache.json"))["stats"]
club_name = {r["club_id"]: r["name"] for r in csv.DictReader(gzip.open("clubs.csv.gz", "rt", encoding="utf-8"))}

# ---- strength-of-games tiers (Jer's spec): 0 EPL | 1 Bundesliga, La Liga, Ligue 1 | 2 other European pro | 4 non-European pro | 5 youth
TIER_PTS = {0: 100, 1: 80, 2: 60, 4: 20, 5: 0}          # linear: 100 - 20*tier
SOG_CAP = 4000                                             # 40 EPL games (40 x 100) = full marks
def tm_tier(dom): return 0 if dom == "GB1" else 1 if dom in ("ES1", "L1", "FR1") else 2
YOUTH_HL = re.compile(r"\b(U\d{2}|II|B|Futures|NXT|Castilla|Jong|Youth|Academy|Reserves?|Primavera|Young Violets)\b|Atl[eè]tic\b|Las Palmas Atl[eé]tico", re.I)
EURO = re.compile(r"2\. Bundesliga|Championship|LaLiga2|Serie [ABC]|Liga Portugal|Eredivisie|Pro League|Allsvenskan|Eliteserien|Ekstraklasa|HNL|Super ?liga|Premier Liga|League of Ireland|Liga 3|Segunda|Regionalliga|S[uü]per Lig|Super League|Ligue 2|League (One|Two)|Premiership|Jupiler|Bundesliga|Premier League|LaLiga|Ligue 1|2\. Liga|Superliga|Oberliga", re.I)
NONEURO = re.compile(r"Torneo|Liga ?Pro|Primera Divisi[oó]n|Liga 1|Dimayor|A-League|Brasileiro|MLS|Liga MX|Copa LPF", re.I)
unclassified = set()
def hl_tier(club, rows):
    if YOUTH_HL.search(club): return 5
    nat = [r for r in rows if r["type"] == "national league"]
    cups = {r["league"].strip() for r in rows if r["type"] == "national cup"}
    lg = max(nat, key=lambda r: r["gamesPlayed"] or 0)["league"].strip() if nat else ""
    if lg == "Premier League" and cups & {"FA Cup", "EFL Cup"}: return 0
    if lg == "Bundesliga": return 1 if "DFB-Pokal" in cups else 2
    if lg == "LaLiga" or lg.startswith("Ligue 1"): return 1
    if NONEURO.search(lg) and not re.match(r"Ligue 1", lg): return 4
    if EURO.search(lg): return 2
    unclassified.add((club, lg)); return 2

for c in pool:
    c["notes"] = ""; c["career"] = None; c["by_team"] = None
    h = HL.get(c["name"])
    if c["stat"] in ("TM", "TM-zero"):
        s = agg.get(c["tm"]["player_id"])
        c["by_team"] = [(club_name.get(k, k), n, tm_tier(club_dom.get(k))) for k, n in s["by"].most_common()] if s else []
    elif h and h["status"] == "ok" and h["club_verified"]:
        l = h["last_season"]
        c["stat"] = "HL"; c["gp"], c["g"], c["a"] = l["gp"], l["g"], l["a"]; c["ga"] = l["g"] + l["a"]; c["career"] = h["career"]
        byclub = collections.defaultdict(list)
        for r in HLC[str(h["hl_id"])]["perCompetition"]:
            if r["season"] in ("25/26", "2025"): byclub[r["club"]].append(r)
        c["by_team"] = []
        for club, rows in byclub.items():
            n = sum(r["gamesPlayed"] or 0 for r in rows); t = hl_tier(club, rows)
            if n > 0 or t != 5: c["by_team"].append((club, n, t))
        c["by_team"].sort(key=lambda x: -x[1])
    elif h:
        c["why"] = "HL profile unverified/unmatched"
    if c["by_team"] is not None:
        c["notes"] = ", ".join(f"{cl} {n} (T{t})" for cl, n, t in c["by_team"])
        c["sog_raw"] = sum(n * TIER_PTS[t] for _, n, t in c["by_team"])
    else:
        c["sog_raw"] = None
if unclassified: print("UNCLASSIFIED leagues (defaulted to tier 2):", sorted(unclassified))
print("stat coverage:", collections.Counter(c["stat"] for c in pool)); print(collections.Counter(c["why"] for c in pool if c["stat"]=="n/a"))

# ---------- 3. MegaBot Rank ----------
W = dict(pot=.40, ovr=.25, sog=.15, ga=.10, gc=.05, spd=.05)
GP_CAP, GA_CAP = 40, 15                       # games / G+A that earn a full 100
def mm(vals, x):                               # min-max over the pool
    lo, hi = min(vals), max(vals); return 100 * (x - lo) / (hi - lo) if hi > lo else 0
pots = [c["pot"] for c in pool]; ovrs = [c["ovr"] for c in pool]
spds = [c["pace"] for c in pool if c["pace"] is not None]
known_sog = [min(c["sog_raw"], SOG_CAP) / SOG_CAP * 100 for c in pool if c["sog_raw"] is not None]
known_ga = [min(c["ga"], GA_CAP) / GA_CAP * 100 for c in pool if c["ga"] is not None]
med_sog, med_ga, med_spd = statistics.median(known_sog), statistics.median(known_ga), statistics.median(spds)
for c in pool:
    c["s_pot"] = mm(pots, c["pot"]); c["s_ovr"] = mm(ovrs, c["ovr"])
    c["s_gc"] = (51 - c["gc_rank"]) / 50 * 100 if c["gc_rank"] else 0
    c["s_spd"] = mm(spds, c["pace"]) if c["pace"] is not None else mm(spds, med_spd)
    c["s_sog"] = min(c["sog_raw"], SOG_CAP) / SOG_CAP * 100 if c["sog_raw"] is not None else med_sog
    c["s_ga"] = min(c["ga"], GA_CAP) / GA_CAP * 100 if c["ga"] is not None else med_ga
    c["score"] = (W["pot"]*c["s_pot"] + W["ovr"]*c["s_ovr"] + W["sog"]*c["s_sog"] + W["ga"]*c["s_ga"]
                  + W["gc"]*c["s_gc"] + W["spd"]*c["s_spd"])
pool.sort(key=lambda c: -c["score"])
# old (pot-only) rank for comparison
old = {c["key"]: i for i, c in enumerate(sorted(pool, key=lambda c: (-c["pot"], -c["ovr"])), 1)}

with open("megabot_rank_youth_2026.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["megabot_rank","prev_rank_pot_only","name","dob","team","league","position","megabot_score","strength_of_games_score","fc_pot","fc_ovr","goalcom_nxgn_rank","speed","games_25_26","goals_25_26","assists_25_26","g_plus_a_25_26","stats_source","career_senior_gp","career_senior_g","career_senior_a","notes_games_by_team_25_26"])
    for i, c in enumerate(pool[:100], 1):
        w.writerow([i, old[c["key"]] if old[c["key"]] <= 100 else ">100", c["name"], c["dob"].isoformat(), c["club"], c["league"], c["pos"],
                    round(c["score"], 1), round(c["s_sog"], 1), int(c["pot"]), int(c["ovr"]), c["gc_rank"] or "", int(c["pace"]) if c["pace"] is not None else "",
                    "" if c["gp"] is None else c["gp"], "" if c["g"] is None else c["g"], "" if c["a"] is None else c["a"],
                    "" if c["ga"] is None else c["ga"], c["stat"],
                    *(("", "", "") if not c["career"] else (c["career"]["gp"], c["career"]["g"], c["career"]["a"])), c["notes"]])
json.dump([{k: (v.isoformat() if isinstance(v, date) else v) for k, v in c.items() if k not in ("tm","sources")} for c in pool], open("pool_scored.json", "w"), default=str)
print("medians used for unknown stats -> SoG", round(med_sog,1), "G+A", round(med_ga,1))

if "--debug" in sys.argv:
    n = 0
    for c in pool:
        if c["why"].startswith("moved") and n < 30:
            n += 1
            print(c["name"][:26], "|", c["club"], "|", [(t["transfer_date"], t["from_club_name"], t["to_club_name"], club_dom.get(t["from_club_id"]), club_dom.get(t["to_club_id"])) for t in moves[c["tm"]["player_id"]]])
