"""
Live Fantrax data for the Mega league -- standings and per-player fantasy
points for every team's roster, pulled straight from Fantrax's internal API
using the browser's own logged-in session (via browser_cookie3, same
approach used for Google Sheets access). Nothing is cached to disk; every
call hits Fantrax fresh.

Used to compute the real "Fan Formula" (see common.py's
compute_fan_formula): the Standings component needs Fantrax's live rank,
and the Top XI / MBP components need real per-player fantasy points across
every team's roster.
"""
import browser_cookie3
import requests

LEAGUE_ID = "908prhw8mdor759p"

# our team code -> Fantrax team ID (cross-referenced from the league's team
# list against common.TEAMS' full names). MS8 has no active Fantrax roster
# this season and is intentionally absent from the live standings/rosters.
FANTRAX_TEAM_ID = {
    "FAV": "74on3adpmdor759y",
    "POW": "qam5ix35mdor759y",
    "CRG": "gfok7ugjmdor759z",
    "DU": "vj8nas52mdor759y",
    "HUF": "we776an2mdor759y",
    "NAC": "we9keiwymdor759z",
    "QFC": "8cl8c9hpmdor759z",
    "REN": "jpso47vbmdor759z",
    "BHB": "df1rsbsgmdor759z",
    "TTS": "7m7d48t0mdor759y",
    "WTF": "3p800smqmdor759y",
    "ASS": "pcowjo87mdor759z",
}

POSITION_MAP = {"701": "F", "702": "M", "703": "D", "704": "GK"}

# league formation for "Top XI": 1 GK, 3 D, 4 M, 3 F (per the Rulez tab)
FORMATION_SLOTS = {"GK": 1, "D": 3, "M": 4, "F": 3}


def _session():
    cj = browser_cookie3.chrome(domain_name="fantrax.com")
    sess = requests.Session()
    sess.cookies.update(cj)
    sess.headers.update({"User-Agent": "Mozilla/5.0"})
    return sess


def _post(sess, method, **data):
    body = {"msgs": [{"method": method, "data": {"leagueId": LEAGUE_ID, **data}}]}
    resp = sess.post("https://www.fantrax.com/fxpa/req", params={"leagueId": LEAGUE_ID}, json=body, timeout=20)
    resp.raise_for_status()
    return resp.json()["responses"][0]["data"]


def fetch_standings(sess):
    """code -> {rank, record, points, win_pct}. Public endpoint, no auth needed."""
    resp = sess.get("https://www.fantrax.com/fxea/general/getStandings", params={"leagueId": LEAGUE_ID}, timeout=20)
    resp.raise_for_status()
    by_team_id = {row["teamId"]: row for row in resp.json()}
    out = {}
    for code, team_id in FANTRAX_TEAM_ID.items():
        row = by_team_id.get(team_id)
        if row:
            out[code] = {
                "rank": row["rank"],
                "record": row["points"],
                "fpts_for": row["totalPointsFor"],
                "win_pct": row["winPercentage"],
            }
    return out


def fetch_roster(sess, team_id):
    """List of {name, pos, fpts} for every rostered player (active + reserve)."""
    data = _post(sess, "getTeamRosterInfo", teamId=team_id, view="STATS")
    players = []
    for table in data.get("tables", []):
        header = table["header"]["cells"]
        score_idx = next((i for i, h in enumerate(header) if h.get("sortKey") == "SCORE"), None)
        for row in table["rows"]:
            pos_id = row.get("posId")
            scorer = row.get("scorer")
            if pos_id not in POSITION_MAP or not scorer:
                continue
            cells = row.get("cells", [])
            fpts = 0.0
            if score_idx is not None and score_idx < len(cells):
                try:
                    fpts = float(cells[score_idx]["content"])
                except (TypeError, ValueError, KeyError):
                    fpts = 0.0
            players.append({"name": scorer.get("name", "?"), "pos": POSITION_MAP[pos_id], "fpts": fpts})
    return players


def fetch_all_rosters(sess):
    """code -> list of {name, pos, fpts}."""
    return {code: fetch_roster(sess, team_id) for code, team_id in FANTRAX_TEAM_ID.items()}


def compute_top_xi(rosters_by_code):
    """Pool every owned player league-wide, take the top-scoring 1 GK / 3 D
    / 4 M / 3 F by fantasy points. Returns (top_xi, mbp) where top_xi is a
    list of {name, pos, code, fpts} (11 entries) and mbp is the single
    highest-scoring owned player league-wide (name, code, fpts)."""
    pool = []
    for code, roster in rosters_by_code.items():
        for p in roster:
            pool.append({**p, "code": code})

    top_xi = []
    for pos, slots in FORMATION_SLOTS.items():
        candidates = sorted((p for p in pool if p["pos"] == pos), key=lambda p: -p["fpts"])
        top_xi.extend(candidates[:slots])

    mbp = max(pool, key=lambda p: p["fpts"]) if pool else None
    return top_xi, mbp


if __name__ == "__main__":
    sess = _session()
    print("Fetching live Fantrax standings...")
    standings = fetch_standings(sess)
    for code, s in sorted(standings.items(), key=lambda kv: kv[1]["rank"]):
        print(f"  {code:5} rank {s['rank']:2}  {s['record']:10}  {s['fpts_for']:8.1f} pts")

    print("\nFetching all 12 live rosters (this takes a few seconds)...")
    rosters = fetch_all_rosters(sess)
    for code, roster in rosters.items():
        print(f"  {code}: {len(roster)} scored players")

    top_xi, mbp = compute_top_xi(rosters)
    print("\nLive Top XI (1 GK / 3 D / 4 M / 3 F by fantasy points):")
    for p in top_xi:
        print(f"  {p['pos']:2} {p['name']:25} {p['code']:5} {p['fpts']:7.1f}")
    print(f"\nMBP (most valuable owned player): {mbp['name']} ({mbp['code']}) {mbp['fpts']:.1f} pts")
