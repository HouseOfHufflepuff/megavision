"""
Builds the MEGAVISION Rank dataset: every 2026/27 EPL player, cross-referenced
across three live sources for one gameweek --

  - FC 26 ratings (fc26_ratings.py): age, height, weight, overall, pace,
    potential. Community CSV mirror, all leagues -- filtered here to this
    season's real 20 EPL clubs (the CSV's own "Premier League" league_name
    tag is unreliable: it also catches Ukraine's Premier League, and still
    lists last season's relegated clubs).
  - Fantrax (fantrax_live.py): position, % rostered across Fantrax
    leagues, this gameweek's fantasy points, games started, injury status.
  - fantasyfootballscout.co.uk/team-news (ffs_scrape.py): predicted
    starting XI, Out list, fitness Doubts (with %), and a keyword read of
    the club's news blurb for a positive/negative mention flag.

Player identity across all three is matched by folded last name + real
club (see _fold/_club_code below) -- good enough at this scale, not
airtight; a genuine ambiguous case (two same-surname players at the same
club) would misattribute. No global player-ID space ties these sources
together, so this is the best available join key.

Run:
    python3 sync_player_ranks.py [week]

`week` is the displayed GW number (defaults to the earliest week in the
Fantrax schedule -- see matchday_email.py's identical convention).
"""
import sys
import unicodedata
from datetime import datetime, timezone

import fantrax_live as fl
import fc26_ratings as fc26
import ffs_scrape
from db import connect

now = datetime.now(timezone.utc).isoformat()

# This season's real 20 EPL clubs (FFS's own team-news dropdown, confirmed
# against ffs_scrape.FFS_CODE_TO_CLUB) -> the FC 26 CSV's exact club_name
# string, since the CSV's own "Premier League" tag over-matches (also
# tags Ukraine's Premier League, and lags a season on relegation).
CLUB_NAME_TO_CODE = {
    "afc bournemouth": "BOU", "arsenal": "ARS", "aston villa": "AVL",
    "brentford": "BRE", "brighton & hove albion": "BHA", "chelsea": "CHE",
    "coventry city": "COV", "crystal palace": "CRY", "everton": "EVE",
    "fulham fc": "FUL", "hull city": "HUL", "ipswich town": "IPS",
    "leeds united": "LEE", "liverpool": "LIV", "manchester city": "MCI",
    "manchester united": "MUN", "newcastle united": "NEW",
    "nottingham forest": "NOT", "sunderland": "SUN", "tottenham hotspur": "TOT",
}

# EA FC's own position tokens -> our GK/D/M/F buckets, used as a fallback
# when a player has no Fantrax match (so the Rank page can still place
# every FC 26 player somewhere).
FC26_POS_TO_BUCKET = {
    "GK": "GK",
    "CB": "D", "LB": "D", "RB": "D", "LWB": "D", "RWB": "D",
    "CDM": "M", "CM": "M", "CAM": "M", "LM": "M", "RM": "M",
    "LW": "F", "RW": "F", "CF": "F", "ST": "F",
}


def _fold(s):
    return unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode("ascii").lower().strip()


def fc26_bucket(positions_str):
    for tok in (positions_str or "").split(","):
        b = FC26_POS_TO_BUCKET.get(tok.strip())
        if b:
            return b
    return None


def build_fantrax_index(pool):
    """folded last name -> [pool entries], for matching against FC 26."""
    idx = {}
    for p in pool:
        last = _fold(p["name"].split()[-1])
        idx.setdefault(last, []).append(p)
    return idx


def match_fantrax(fc26_row, fantrax_idx):
    last = _fold((fc26_row["short_name"] or fc26_row["full_name"]).split()[-1])
    candidates = fantrax_idx.get(last, [])
    if not candidates:
        return None
    if len(candidates) == 1:
        return candidates[0]
    club_code = CLUB_NAME_TO_CODE.get(_fold(fc26_row["club"]))
    same_club = [c for c in candidates if c["club"] == club_code]
    return same_club[0] if same_club else candidates[0]


def build_ffs_index(ffs_data):
    """club code -> {folded_name: 'lineup'|'out'|'doubt'}, plus raw news text."""
    idx = {}
    for club, info in ffs_data.items():
        names = {}
        for n in info["lineup"]:
            names[_fold(n.split()[-1])] = "lineup"
        for n in info["out"]:
            names[_fold(n.split()[-1])] = "out"
        for n, _pct in info["doubts"]:
            names[_fold(n.split()[-1])] = "doubt"
        idx[club] = {"names": names, "news": info["news"]}
    return idx


def sync(week=None):
    sess = fl._session()

    print("Fetching FC 26 ratings (all leagues, filtering to this season's 20 EPL clubs)...", file=sys.stderr)
    fc26_players = [p for p in fc26.fetch_all_players() if _fold(p["club"]) in CLUB_NAME_TO_CODE]
    print(f"  {len(fc26_players)} EPL players in FC 26 data.", file=sys.stderr)

    print("Fetching full Fantrax player pool (owned + free agents, all 4 positions)...", file=sys.stderr)
    fantrax_pool = fl.fetch_full_player_pool(sess)
    fantrax_idx = build_fantrax_index(fantrax_pool)
    print(f"  {len(fantrax_pool)} Fantrax player rows.", file=sys.stderr)

    print("Scraping fantasyfootballscout.co.uk/team-news...", file=sys.stderr)
    ffs_data = ffs_scrape.fetch_and_parse()
    ffs_idx = build_ffs_index(ffs_data)

    if week is None:
        games_by_week = {}
        for g in fl.fetch_schedule(sess):
            games_by_week.setdefault(g["week"], []).append(g)
        week = min(games_by_week)
    print(f"Building for gameweek {week}...", file=sys.stderr)

    conn = connect()
    cur = conn.cursor()
    n_players, n_gw = 0, 0

    for p in fc26_players:
        club_code = CLUB_NAME_TO_CODE[_fold(p["club"])]
        fx = match_fantrax(p, fantrax_idx)
        name = fx["name"] if fx else p["short_name"] or p["full_name"]
        position = fx["pos"] if fx else fc26_bucket(p["positions"])

        cur.execute(
            "INSERT INTO epl_players (player_name, real_club, age, height_cm, weight_kg, fc26_overall, "
            "fc26_speed, fc26_potential, fantrax_position, fantrax_ros_pct, updated_at) VALUES (?,?,?,?,?,?,?,?,?,?,?) "
            "ON CONFLICT(player_name, real_club) DO UPDATE SET age=excluded.age, height_cm=excluded.height_cm, "
            "weight_kg=excluded.weight_kg, fc26_overall=excluded.fc26_overall, fc26_speed=excluded.fc26_speed, "
            "fc26_potential=excluded.fc26_potential, fantrax_position=excluded.fantrax_position, "
            "fantrax_ros_pct=excluded.fantrax_ros_pct, updated_at=excluded.updated_at",
            (name, club_code, _int(p.get("age")), _int(p.get("height_cm")), _int(p.get("weight_kg")),
             p["overall"], _float(p.get("pace")), p["potential"],
             position, fx["ros_pct"] if fx else None, now),
        )
        n_players += 1

        injuries = "; ".join(fx["injuries"]) if fx and fx["injuries"] else ""
        started_last_week = 1 if fx and fx["games_started"] >= 1 else 0
        score = fx["fpts"] if fx else None

        club_ffs = ffs_idx.get(club_code, {"names": {}, "news": ""})
        last = _fold(name.split()[-1])
        ffs_flag = club_ffs["names"].get(last)
        ffs_start = 1 if ffs_flag == "lineup" else 0
        ffs_doubt = 1 if ffs_flag == "doubt" else 0
        ffs_negative = 1 if ffs_flag in ("out", "doubt") else 0
        pos_mention, neg_mention = ffs_scrape.classify_mentions(name, club_ffs["news"])
        ffs_positive = 1 if pos_mention and not ffs_negative else 0
        ffs_negative = 1 if ffs_negative or neg_mention else 0

        cur.execute(
            "INSERT INTO player_gameweek (player_name, real_club, gameweek, score, injury_status, "
            "started_last_week, ffs_start, ffs_positive_mention, ffs_negative_mention, ffs_doubt, updated_at) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?) ON CONFLICT(player_name, real_club, gameweek) DO UPDATE SET "
            "score=excluded.score, injury_status=excluded.injury_status, started_last_week=excluded.started_last_week, "
            "ffs_start=excluded.ffs_start, ffs_positive_mention=excluded.ffs_positive_mention, "
            "ffs_negative_mention=excluded.ffs_negative_mention, ffs_doubt=excluded.ffs_doubt, updated_at=excluded.updated_at",
            (name, club_code, week, score, injuries, started_last_week,
             ffs_start, ffs_positive, ffs_negative, ffs_doubt, now),
        )
        n_gw += 1

    conn.commit()
    conn.close()
    print(f"Done: {n_players} epl_players rows, {n_gw} player_gameweek rows for GW{week}.")
    return week


def _int(v):
    try:
        return int(float(v))
    except (TypeError, ValueError):
        return None


def _float(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


if __name__ == "__main__":
    week_arg = int(sys.argv[1]) if len(sys.argv) > 1 else None
    sync(week_arg)
