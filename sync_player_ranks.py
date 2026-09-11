"""
Builds the MEGAVISION Rank dataset: every 2026/27 EPL player, cross-referenced
across three live sources for one gameweek --

  - Fantrax (fantrax_live.py): the PRIMARY source of who's a current EPL
    player and at which club/position -- live and roster-accurate.
  - FC 26 ratings (fc26_ratings.py): age, height, weight, overall, pace,
    potential. Community CSV mirror, all leagues. Matched to the Fantrax
    player by NAME ONLY, ignoring the CSV's own club field entirely -- it
    lags real transfers (e.g. still listed a player at his OLD club weeks
    after a real move), so requiring it to match Fantrax's live club was
    silently dropping anyone the CSV hadn't caught up on yet. Position
    (via FC26_POS_TO_BUCKET) is used only to disambiguate when a surname
    matches more than one FC26 player, never to filter by club.
  - fantasyfootballscout.co.uk/team-news (ffs_scrape.py): predicted
    starting XI, Out list, fitness Doubts (with %), and a keyword read of
    the club's news blurb for a positive/negative mention flag.

Player identity is matched by folded last name (see _fold below) --
good enough at this scale, not airtight; a genuine ambiguous case (two
same-surname, same-position players) would misattribute. No global
player-ID space ties these sources together, so this is the best
available join key. Fixed 2026-09-11 to drop the FC26-club filter after
it silently excluded a just-transferred player (Christos Tzolis, still
tagged to his old club in the CSV) from getting any rank score at all.

Run:
    python3 sync_player_ranks.py [week]

`week` is the displayed GW number (defaults to the earliest week in the
Fantrax schedule -- see matchday_email.py's identical convention).
"""
import json
import sys
import unicodedata
import urllib.request
from datetime import datetime, timezone

import fantrax_live as fl
import fc26_ratings as fc26
import ffs_scrape
import sync_fpl_stats as fpl
from db import connect

LIVE_EVENT_URL = "https://fantasy.premierleague.com/api/event/{event}/live/"

now = datetime.now(timezone.utc).isoformat()

# EA FC's own position tokens -> our GK/D/M/F buckets, used only to
# disambiguate when a surname matches more than one FC 26 player -- never
# to filter by club (the CSV's club field lags real transfers).
FC26_POS_TO_BUCKET = {
    "GK": "GK",
    "CB": "D", "LB": "D", "RB": "D", "LWB": "D", "RWB": "D",
    "CDM": "M", "CM": "M", "CAM": "M", "LM": "M", "RM": "M",
    "LW": "F", "RW": "F", "CF": "F", "ST": "F",
}

FALLBACK_OVERALL = 50.0  # neutral middle-of-the-pack rating for a live Fantrax player with no FC26 match at all


def _fold(s):
    return unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode("ascii").lower().strip()


def fc26_bucket(positions_str):
    for tok in (positions_str or "").split(","):
        b = FC26_POS_TO_BUCKET.get(tok.strip())
        if b:
            return b
    return None


def build_fc26_index(players):
    """folded last-name token -> [fc26 rows]. Indexed under every token in
    last_names (handles mononyms) so a Fantrax player's own last name
    matches however FC26 recorded them."""
    idx = {}
    for p in players:
        for token in p["last_names"]:
            idx.setdefault(token, []).append(p)
    return idx


def match_fc26(fantrax_name, fantrax_pos, fc26_idx):
    """Fantrax is the live/current source of truth for identity (name,
    club, position) -- FC26 is matched to it by name only, disambiguated
    by position when a surname is shared, never by club (see module
    docstring for why matching on club silently dropped real players)."""
    last = _fold(fantrax_name.split()[-1])
    candidates = fc26_idx.get(last, [])
    if not candidates:
        return None
    if len(candidates) == 1:
        return candidates[0]
    same_pos = [c for c in candidates if fc26_bucket(c["positions"]) == fantrax_pos]
    if len(same_pos) == 1:
        return same_pos[0]
    pool = same_pos or candidates
    # still ambiguous -- best-effort: highest-rated candidate, so a random
    # lower-league same-surname player doesn't win over the real EPL one.
    return max(pool, key=lambda c: c["overall"])


def fetch_minutes_last_week(week):
    """{element_id: {"minutes":.., "starts":..}} from FPL's own live event
    data for the real gameweek before this one. Mega's own week numbering
    runs one ahead of FPL's real event numbering -- Mega GW1 was the cup
    week (Community Shield/Super Cup/FA Cup), not a real PL round -- so
    "last week" for Mega week W is FPL event W-2. Confirmed by cross-
    checking FPL's bootstrap-static `events` (event 3 marked finished/
    is_current while Mega was on GW4, event 4 marked is_next while Mega
    was on GW5)."""
    fpl_event = week - 2
    if fpl_event < 1:
        return {}
    req = urllib.request.Request(LIVE_EVENT_URL.format(event=fpl_event), headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception:
        return {}
    return {e["id"]: {"minutes": e["stats"]["minutes"], "starts": e["stats"]["starts"]} for e in data.get("elements", [])}


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

    print("Fetching full Fantrax player pool (owned + free agents, all 4 positions) -- primary source of who's a current EPL player...", file=sys.stderr)
    fantrax_pool = fl.fetch_full_player_pool(sess)
    print(f"  {len(fantrax_pool)} Fantrax player rows.", file=sys.stderr)

    print("Fetching FC 26 ratings (all leagues -- matched to Fantrax by name only, not club)...", file=sys.stderr)
    fc26_players = fc26.fetch_all_players()
    fc26_idx = build_fc26_index(fc26_players)
    print(f"  {len(fc26_players)} FC26 players worldwide, indexed by surname.", file=sys.stderr)

    print("Scraping fantasyfootballscout.co.uk/team-news...", file=sys.stderr)
    ffs_data = ffs_scrape.fetch_and_parse()
    ffs_idx = build_ffs_index(ffs_data)

    if week is None:
        games_by_week = {}
        for g in fl.fetch_schedule(sess):
            games_by_week.setdefault(g["week"], []).append(g)
        week = min(games_by_week)
    print(f"Building for gameweek {week}...", file=sys.stderr)

    print("Fetching FPL live minutes for last week...", file=sys.stderr)
    minutes_by_id = fetch_minutes_last_week(week)
    fpl_elements = fpl.fetch_elements()
    fpl_lookup = fpl.build_lookup(fpl_elements)
    print(f"  {len(minutes_by_id)} players with minutes data from FPL event {week - 2}.", file=sys.stderr)

    conn = connect()
    cur = conn.cursor()
    n_players, n_gw, n_no_fc26 = 0, 0, 0

    for fx in fantrax_pool:
        name, club_code, position = fx["name"], fx["club"], fx["pos"]
        p = match_fc26(name, position, fc26_idx)
        if p is None:
            n_no_fc26 += 1

        cur.execute(
            "INSERT INTO epl_players (player_name, real_club, age, height_cm, weight_kg, fc26_overall, "
            "fc26_speed, fc26_potential, fantrax_position, fantrax_ros_pct, updated_at) VALUES (?,?,?,?,?,?,?,?,?,?,?) "
            "ON CONFLICT(player_name, real_club) DO UPDATE SET age=excluded.age, height_cm=excluded.height_cm, "
            "weight_kg=excluded.weight_kg, fc26_overall=excluded.fc26_overall, fc26_speed=excluded.fc26_speed, "
            "fc26_potential=excluded.fc26_potential, fantrax_position=excluded.fantrax_position, "
            "fantrax_ros_pct=excluded.fantrax_ros_pct, updated_at=excluded.updated_at",
            (name, club_code,
             _int(p.get("age")) if p else None, _int(p.get("height_cm")) if p else None, _int(p.get("weight_kg")) if p else None,
             p["overall"] if p else FALLBACK_OVERALL, _float(p.get("pace")) if p else None, p["potential"] if p else None,
             position, fx["ros_pct"], now),
        )
        n_players += 1

        injuries = "; ".join(fx["injuries"]) if fx["injuries"] else ""
        started_last_week = 1 if fx["games_started"] >= 1 else 0
        score = fx["fpts"]

        club_ffs = ffs_idx.get(club_code, {"names": {}, "news": ""})
        last = _fold(name.split()[-1])
        ffs_flag = club_ffs["names"].get(last)
        ffs_start = 1 if ffs_flag == "lineup" else 0
        ffs_doubt = 1 if ffs_flag == "doubt" else 0
        ffs_negative = 1 if ffs_flag in ("out", "doubt") else 0
        pos_mention, neg_mention = ffs_scrape.classify_mentions(name, club_ffs["news"])
        ffs_positive = 1 if pos_mention and not ffs_negative else 0
        ffs_negative = 1 if ffs_negative or neg_mention else 0

        name_parts = name.split()
        fpl_el = fpl.match(fpl_lookup, name_parts[-1], name_parts[0][:1] if name_parts else None, club_code)
        minutes_last_week = minutes_by_id.get(fpl_el["id"], {}).get("minutes") if fpl_el else None

        cur.execute(
            "INSERT INTO player_gameweek (player_name, real_club, gameweek, score, injury_status, "
            "started_last_week, ffs_start, ffs_positive_mention, ffs_negative_mention, ffs_doubt, "
            "minutes_last_week, updated_at) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?,?) ON CONFLICT(player_name, real_club, gameweek) DO UPDATE SET "
            "score=excluded.score, injury_status=excluded.injury_status, started_last_week=excluded.started_last_week, "
            "ffs_start=excluded.ffs_start, ffs_positive_mention=excluded.ffs_positive_mention, "
            "ffs_negative_mention=excluded.ffs_negative_mention, ffs_doubt=excluded.ffs_doubt, "
            "minutes_last_week=excluded.minutes_last_week, updated_at=excluded.updated_at",
            (name, club_code, week, score, injuries, started_last_week,
             ffs_start, ffs_positive, ffs_negative, ffs_doubt, minutes_last_week, now),
        )
        n_gw += 1

    conn.commit()
    conn.close()
    print(f"Done: {n_players} epl_players rows, {n_gw} player_gameweek rows for GW{week} "
          f"({n_no_fc26} with no FC26 match -- given fallback overall {FALLBACK_OVERALL}).")
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
