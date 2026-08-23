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

# "908prhw8mdor759p" (the old value here) is "Mega 25-26 Fantasy Soccer Lg"
# -- LAST season, not this one. It was used for this entire site by mistake
# (schedule AND standings/rosters/Fan Formula all pulled from the wrong
# league) until caught and corrected. "9rv5verjmrz6rjuo" is the real
# "Mega 26-27 Fantasy Soccer Lg" (2026-08-21 to 2027-05-30) -- confirmed
# directly against https://www.fantrax.com/fantasy/league/9rv5verjmrz6rjuo
LEAGUE_ID = "9rv5verjmrz6rjuo"

# our team code -> Fantrax team ID, cross-referenced by team NAME against
# this league's own getLeagueInfo (team IDs are a completely different
# format/value from the old 25-26 league, not reusable). This league also
# has 12 "Juniors" reserve-squad teams (e.g. "HUFF Juniors") which are
# intentionally NOT in this map -- they're a separate bracket, not one of
# our 12 real teams, and Fantrax's own scoring period 1 is entirely
# Juniors-vs-Juniors games (see fetch_schedule).
FANTRAX_TEAM_ID = {
    "FAV": "23hm85gemrz6rjx5",
    "POW": "d01w4imsmrz6rjx5",
    "CRG": "4dgc8wkkmrz6rjx5",
    "DU": "2y4shiaemrz6rjx5",
    "HUF": "c2qvgb1omrz6rjx5",
    "NAC": "rb3j7yppmrz6rjx5",
    "QFC": "npzdfihcmrz6rjx5",
    "REN": "pf3vvmrcmrz6rjx5",
    "BHB": "y6h220iwmrz6rjx5",
    "TTS": "smzr62sgmrz6rjx5",
    "WTF": "8toaz9ikmrz6rjx5",
    "ASS": "kc8p9g8gmrz6rjx5",
}

# this league's 12 "Juniors" reserve-squad teams, one per real team, each
# its own separate Fantrax roster -- NOT a naming pattern off FANTRAX_TEAM_ID
# (e.g. "5th Ave Juniors" vs "5th Ave Argyle", "THOT Juniors" vs
# "Thottenham Thotspur"), so hardcoded by hand from getLeagueInfo's
# teamInfo, same as FANTRAX_TEAM_ID. For Best 11 purposes a Jr-owned player
# counts as owned by the Sr team -- see ALL_TEAM_ID_TO_CODE.
JUNIOR_TEAM_ID = {
    "FAV": "ejw2j4f3mrz6rjx5",
    "POW": "84c87qbdmrz6rjx5",
    "CRG": "rfot8g91mrz6rjx5",
    "DU": "7lc80yhamrz6rjx5",
    "HUF": "797y7t21mrz6rjx5",
    "NAC": "iv6z1sxgmrz6rjx4",
    "QFC": "9oyrf4i2mrz6rjx5",
    "REN": "7zzbwoaamrz6rjx5",
    "BHB": "lbngvz1imrz6rjx5",
    "TTS": "tp4p1lgamrz6rjx5",
    "WTF": "by2nv4otmrz6rjx5",
    "ASS": "yetxuljxmrz6rjx5",
}

# every Fantrax team id (Sr + Jr) -> our 12 codes, Jr treated as owned by Sr
ALL_TEAM_ID_TO_CODE = {v: k for k, v in FANTRAX_TEAM_ID.items()}
ALL_TEAM_ID_TO_CODE.update({v: k for k, v in JUNIOR_TEAM_ID.items()})

POSITION_MAP = {"701": "F", "702": "M", "703": "D", "704": "GK"}
POS_GROUP = {"F": "POS_701", "M": "POS_702", "D": "POS_703", "GK": "POS_704"}

# league formation for "Top XI"/"Best 11": 1 GK, 3 D, 4 M, 3 F (per the
# Rulez tab: "Starting formation is GK + top 10 outfield scorers")
FORMATION_SLOTS = {"GK": 1, "D": 3, "M": 4, "F": 3}


def fetch_position_leaders(sess, pos, limit=10):
    """Top-scoring owned (ALL_TAKEN) players at `pos` ("GK"/"D"/"M"/"F"),
    ranked by fantasy points, straight off Fantrax's own player-stats page
    (the same data as
    fantasy/league/<id>/players;statusOrTeamFilter=ALL_TAKEN;positionOrGroup=POS_xxx)
    -- NOT reconstructed from roster pulls, so it matches exactly what's on
    that page. Each entry: name, real_club, team_code (Jr rosters folded
    into their Sr code), fpts."""
    body = {"msgs": [{"method": "getPlayerStats", "data": {
        "leagueId": LEAGUE_ID, "view": "STATS", "statusOrTeamFilter": "ALL_TAKEN",
        "positionOrGroup": POS_GROUP[pos], "maxResultsPerPage": limit, "pageNumber": 1,
    }}]}
    resp = sess.post("https://www.fantrax.com/fxpa/req", params={"leagueId": LEAGUE_ID}, json=body, timeout=30)
    resp.raise_for_status()
    data = resp.json()["responses"][0]["data"]
    out = []
    for row in data["statsTable"][:limit]:
        scorer = row["scorer"]
        team_cell = row["cells"][1]
        code = ALL_TEAM_ID_TO_CODE.get(team_cell.get("teamId"))
        try:
            fpts = float(row["cells"][6]["content"])
        except (KeyError, IndexError, TypeError, ValueError):
            fpts = 0.0
        out.append({
            "name": scorer["name"], "real_club": scorer.get("teamShortName", ""),
            "team_code": code, "team_owner_raw": team_cell.get("toolTip"), "fpts": fpts,
        })
    return out


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


def fetch_all_standings(sess):
    """The full 24-row standings (all 12 Sr teams + all 12 Jr teams),
    unfiltered, straight off getStandings. Right now the Sr teams haven't
    played a real scored matchup yet (still 0-0-0/rank 13, tied) -- only
    the Jr bracket's period-1 games have real results -- so the meaningful
    "top 12" on the standings page today is the Jr teams. Each row is
    tagged with our resolved code (Jr folds into its Sr code, same as
    fetch_position_leaders) so callers can use whichever has real signal."""
    resp = sess.get("https://www.fantrax.com/fxea/general/getStandings", params={"leagueId": LEAGUE_ID}, timeout=20)
    resp.raise_for_status()
    out = []
    for row in resp.json():
        out.append({
            "team_name": row["teamName"],
            "team_id": row["teamId"],
            "code": ALL_TEAM_ID_TO_CODE.get(row["teamId"]),
            "is_junior": row["teamId"] in JUNIOR_TEAM_ID.values(),
            "rank": row["rank"],
            "record": row["points"],
            "fpts_for": row["totalPointsFor"],
            "win_pct": row["winPercentage"],
        })
    out.sort(key=lambda r: r["rank"])
    return out


# getLeagueInfo's playoffs.lastRegularSeasonPeriod == 36; periods 37-38 are
# playoffs (TBD matchups until the regular season finishes, excluded).
# Fantrax scoring period 1 is entirely Juniors-vs-Juniors games (0 of our 12
# real teams play in it -- confirmed and QA'd with the user); our 12 teams'
# real season starts at Fantrax period 2, which we display as "GW 1" -- so
# every displayed week number is the Fantrax period minus 1.
REGULAR_SEASON_PERIODS = range(2, 37)


def fetch_schedule(sess, periods=REGULAR_SEASON_PERIODS):
    """Real regular-season matchups for our 12 teams, straight from
    Fantrax's own scoring-period schedule (getLeagueInfo's "matchups") --
    NOT the Google Sheet's "League Schedule" tab, which was confirmed wrong
    (flipped home/away) and must never be used as a schedule source again.
    Public endpoint, no auth needed. Each entry: week (Fantrax period - 1,
    i.e. displayed GW number), home code, away code."""
    resp = sess.get("https://www.fantrax.com/fxea/general/getLeagueInfo", params={"leagueId": LEAGUE_ID}, timeout=20)
    resp.raise_for_status()
    id_to_code = {v: k for k, v in FANTRAX_TEAM_ID.items()}
    games = []
    for period in resp.json()["matchups"]:
        fantrax_period = period["period"]
        if fantrax_period not in periods:
            continue
        week = fantrax_period - 1
        for m in period["matchupList"]:
            home, away = m.get("home", {}), m.get("away", {})
            if home.get("TBD") or away.get("TBD"):
                continue
            home_code = id_to_code.get(home.get("id"))
            away_code = id_to_code.get(away.get("id"))
            if home_code and away_code:
                games.append({"week": week, "home": home_code, "away": away_code})
    return games


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
