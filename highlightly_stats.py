"""Senior-team stats (25/26 season + career) for the youth-draft pool from the Highlightly football API.

Key lives in .env (HIGHLIGHTLY_API_KEY, gitignored). Free plan = 100 requests/day, so this is resumable:
every response is cached in data/highlightly_cache.json and the run stops when the daily quota is nearly gone.
Re-run it tomorrow and it carries on where it stopped.

    python3 highlightly_stats.py [pool_scored.json]      # default /tmp/stats/pool_scored.json
"""
import json, os, re, sys, unicodedata, urllib.parse, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HERE, "data", "highlightly_cache.json")
OUT = os.path.join(HERE, "data", "youth_senior_stats.json")
BASE = "https://soccer.highlightly.net"
LAST, CURRENT = {"25/26", "2025"}, {"26/27", "2026"}
YOUTH = re.compile(r"\b(U\d{2}|II|B|Futures|NXT|Castilla|Jong|Youth|Academy|Reserves?|Primavera|Atl[eè]tic|Las Palmas Atl[eé]tico|Young Violets)\b", re.I)
GENERIC = {"fc", "cf", "club", "football", "afc", "sc", "sv", "vfl", "vfb", "fk", "bk", "ik", "if", "ss", "ac", "as",
           "sk", "kv", "kvc", "krc", "rsc", "kaa", "de", "the", "of", "clube", "calcio", "sad", "ud"}


def key():
    for line in open(os.path.join(HERE, ".env")):
        if line.startswith("HIGHLIGHTLY_API_KEY="):
            return line.split("=", 1)[1].strip()
    sys.exit("HIGHLIGHTLY_API_KEY missing from .env")


def fold(s):
    s = unicodedata.normalize("NFKD", s or "")
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"[^a-z \-']", "", s.lower().replace("-", " ")).strip()


def toks(s, generic=()):
    s = re.sub(r"nuremberg", "nurnberg", fold(s))
    return {t for t in s.split() if len(t) > 1 and t not in generic}


class Api:
    def __init__(self):
        self.k, self.remaining = key(), None

    def get(self, path):
        req = urllib.request.Request(BASE + path, headers={"x-rapidapi-key": self.k, "User-Agent": "megabot/1.0"})
        with urllib.request.urlopen(req, timeout=40) as r:
            self.remaining = int(r.headers.get("x-ratelimit-requests-remaining", self.remaining or 0))
            return json.load(r)


def pick_candidate(player, cands):
    """Best name match among search hits; None if nothing plausible."""
    mine = toks(player["name"])
    last = fold(player["name"]).split()[-1]
    first = fold(player["name"]).split()[0]
    best = None
    for c in cands:
        theirs = toks(c.get("fullName") or "") | toks(c.get("name") or "")
        if last not in theirs and not (mine & theirs - {first}):
            continue
        score = len(mine & theirs) + (2 if first in theirs or first[0] in {t[0] for t in theirs} else 0)
        if best is None or score > best[0]:
            best = (score, c)
    return best[1] if best else None


def senior_rows(stats):
    return [r for r in stats.get("perCompetition", []) if not YOUTH.search(r.get("club") or "")]


def summarise(player, stats):
    rows = senior_rows(stats)
    def tot(rs):
        return {"gp": sum(r["gamesPlayed"] or 0 for r in rs), "g": sum(r["goals"] or 0 for r in rs),
                "a": sum(r["assists"] or 0 for r in rs), "min": sum(r["minutesPlayed"] or 0 for r in rs)}
    last = [r for r in rows if r["season"] in LAST]
    cur = [r for r in rows if r["season"] in CURRENT]
    ct = toks(player["club"], GENERIC)
    seen = {c for r in last + cur for c in toks(r["club"], GENERIC)}
    by_club = {}
    for r in last:
        by_club[r["club"]] = by_club.get(r["club"], 0) + (r["gamesPlayed"] or 0)
    notes = ", ".join(f"{c} {n}" for c, n in sorted(by_club.items(), key=lambda x: -x[1]))
    return {"last_season": tot(last), "current_season": tot(cur), "career": tot(rows),
            "games_by_club_25_26": by_club, "notes": notes,
            "clubs_25_26": sorted({r["club"] for r in last}), "club_verified": bool(ct & seen),
            "competitions_25_26": sorted({f'{r["league"].strip()} ({r["club"]})' for r in last})}


def main():
    pool = json.load(open(sys.argv[1] if len(sys.argv) > 1 else "/tmp/stats/pool_scored.json"))
    cache = json.load(open(CACHE)) if os.path.exists(CACHE) else {"search": {}, "stats": {}}
    api = Api()
    # priority: top-100 players TM couldn't cover -> rest of top 100 -> remaining n/a pool
    top = pool[:100]
    order = [p for p in top if p["stat"] == "n/a"] + [p for p in top if p["stat"] != "n/a"] + \
            [p for p in pool[100:] if p["stat"] == "n/a"]
    out = json.load(open(OUT)) if os.path.exists(OUT) else {}
    for p in order:
        k = p["name"]
        if k in out:
            continue
        if api.remaining is not None and api.remaining <= 2:
            break
        if k not in cache["search"]:
            q = " ".join([fold(k).split()[0], fold(k).split()[-1]])
            cache["search"][k] = api.get("/players?" + urllib.parse.urlencode({"name": q, "limit": 20}))["data"]
            json.dump(cache, open(CACHE, "w"))
        cand = pick_candidate(p, cache["search"][k])
        if not cand:
            out[k] = {"status": "no_search_match"}
            continue
        if str(cand["id"]) not in cache["stats"]:
            if api.remaining is not None and api.remaining <= 2:
                break
            cache["stats"][str(cand["id"])] = api.get(f"/players/{cand['id']}/statistics")[0]
            json.dump(cache, open(CACHE, "w"))
        out[k] = {"status": "ok", "hl_id": cand["id"], "hl_name": cand.get("fullName") or cand["name"],
                  **summarise(p, cache["stats"][str(cand["id"])])}
        json.dump(out, open(OUT, "w"), indent=1)
    json.dump(out, open(OUT, "w"), indent=1)
    print(f"done: {sum(1 for v in out.values() if v['status']=='ok')} players with stats, "
          f"{sum(1 for v in out.values() if v['status']!='ok')} unmatched, requests left today: {api.remaining}")


if __name__ == "__main__":
    main()
