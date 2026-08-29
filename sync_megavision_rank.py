"""
Computes the MEGAVISION Rank (see rank_algo.py) for every player already
loaded into epl_players/player_gameweek by sync_player_ranks.py: the 0-100
megavision_rank score, the start_likelihood % (sums to 100 within a club's
position group), and one epl_club_gameweek row per real club (opponent,
home/away, real-world record, and the club-level matchup factor).

Run:
    python3 sync_player_ranks.py     # populate/refresh the raw data first
    python3 sync_megavision_rank.py [week]
"""
import json
import sys
import unicodedata
import urllib.request
from datetime import datetime, timezone

import ffs_scrape
import rank_algo
from db import connect

now = datetime.now(timezone.utc).isoformat()

BOOTSTRAP_URL = "https://fantasy.premierleague.com/api/bootstrap-static/"

CLUB_DISPLAY_NAMES = {
    "ARS": "Arsenal", "AVL": "Aston Villa", "BOU": "AFC Bournemouth", "BRE": "Brentford",
    "BHA": "Brighton and Hove Albion", "CHE": "Chelsea", "COV": "Coventry City",
    "CRY": "Crystal Palace", "EVE": "Everton", "FUL": "Fulham", "HUL": "Hull City",
    "IPS": "Ipswich Town", "LEE": "Leeds United", "LIV": "Liverpool", "MCI": "Manchester City",
    "MUN": "Manchester United", "NEW": "Newcastle United", "NOT": "Nottingham Forest",
    "SUN": "Sunderland", "TOT": "Tottenham Hotspur",
}


def _fold(s):
    return unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode("ascii").lower().strip()


def _club_display_name(code):
    return CLUB_DISPLAY_NAMES.get(code, code)


def fetch_club_records():
    """FPL's own bootstrap-static teams array has played/win/draw/loss/
    position for every real EPL club, keyed by its own short_name -- which
    already matches our 3-letter club codes exactly."""
    req = urllib.request.Request(BOOTSTRAP_URL, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read())
    return {
        t["short_name"]: {"played": t["played"], "win": t["win"], "draw": t["draw"],
                           "loss": t["loss"], "position": t["position"]}
        for t in data["teams"]
    }


def sync(week=None):
    conn = connect()
    cur = conn.cursor()
    if week is None:
        week = cur.execute("SELECT MAX(gameweek) FROM player_gameweek").fetchone()[0]

    cur.execute(
        "SELECT p.player_name, p.real_club, p.fantrax_position, p.fc26_overall, "
        "g.score, g.injury_status, g.ffs_start, g.ffs_doubt, g.ffs_negative_mention "
        "FROM epl_players p JOIN player_gameweek g ON g.player_name=p.player_name AND g.real_club=p.real_club "
        "WHERE g.gameweek=? AND p.fc26_overall IS NOT NULL",
        (week,),
    )
    cols = [d[0] for d in cur.description]
    rows = [dict(zip(cols, r)) for r in cur.fetchall()]
    conn.close()

    if not rows:
        raise SystemExit(f"No player_gameweek rows for week {week} -- run sync_player_ranks.py first")

    print(f"Computing MEGAVISION Rank for {len(rows)} players, GW{week}...", file=sys.stderr)

    club_totals = {}
    for r in rows:
        club_totals.setdefault(r["real_club"], []).append(r["fc26_overall"])
    club_avg_fc26 = {c: sum(v) / len(v) for c, v in club_totals.items()}
    league_avg_fc26 = sum(club_avg_fc26.values()) / len(club_avg_fc26)

    pos_scores = {}
    for r in rows:
        if r["score"] is not None:
            pos_scores.setdefault(r["fantrax_position"], []).append(r["score"])
    position_avg_score = {p: sum(v) / len(v) for p, v in pos_scores.items()}

    print("Scraping opponent/home-away from fantasyfootballscout.co.uk/team-news...", file=sys.stderr)
    ffs_data = ffs_scrape.fetch_and_parse()
    opponent_club = {club: info["opponent_name"] for club, info in ffs_data.items()}
    is_home_by_club = {club: info["is_home"] for club, info in ffs_data.items()}

    print("Fetching real EPL club records from the FPL API...", file=sys.stderr)
    club_records = fetch_club_records()

    def opponent_avg(club):
        opp_name = opponent_club.get(club)
        if not opp_name:
            return None
        opp_folded = _fold(opp_name)
        for c2 in club_avg_fc26:
            if _fold(_club_display_name(c2)) == opp_folded:
                return club_avg_fc26[c2]
        return None

    inputs = []
    is_out_by_row = []
    for r in rows:
        club = r["real_club"]
        opp_avg = opponent_avg(club)
        is_out = bool(r["injury_status"]) or bool(r["ffs_negative_mention"] and not r["ffs_doubt"])
        is_out_by_row.append(is_out)
        inputs.append({
            "fc26_overall": r["fc26_overall"],
            "club_avg_fc26": club_avg_fc26.get(club, league_avg_fc26),
            "league_avg_fc26": league_avg_fc26,
            "opponent_avg_fc26": opp_avg,
            "is_home": is_home_by_club.get(club),
            "score": r["score"],
            "position_avg_score": position_avg_score.get(r["fantrax_position"]),
            "ffs_start": r["ffs_start"],
            "ffs_doubt": r["ffs_doubt"],
            "is_out": is_out,
        })

    ranks = rank_algo.compute_ranks(inputs)

    # start_likelihood: softmax within each (club, position) group
    groups = {}
    for i, r in enumerate(rows):
        key = (r["real_club"], r["fantrax_position"])
        groups.setdefault(key, []).append(i)
    likelihoods = [None] * len(rows)
    for key, idxs in groups.items():
        group_players = [
            {"fc26_overall": rows[i]["fc26_overall"], "ffs_start": rows[i]["ffs_start"],
             "ffs_doubt": rows[i]["ffs_doubt"], "is_out": is_out_by_row[i]}
            for i in idxs
        ]
        for i, pct in zip(idxs, rank_algo.start_likelihoods(group_players)):
            likelihoods[i] = pct

    conn = connect()
    cur = conn.cursor()
    for r, rank, likelihood in zip(rows, ranks, likelihoods):
        cur.execute(
            "UPDATE player_gameweek SET megavision_rank=?, start_likelihood=? "
            "WHERE player_name=? AND real_club=? AND gameweek=?",
            (rank, likelihood, r["player_name"], r["real_club"], week),
        )

    for club, avg in club_avg_fc26.items():
        rec = club_records.get(club, {})
        mf = rank_algo.matchup_factor(avg, league_avg_fc26, opponent_avg(club), is_home_by_club.get(club))
        cur.execute(
            "INSERT INTO epl_club_gameweek (real_club, gameweek, opponent, is_home, played, win, draw, loss, "
            "league_position, club_avg_fc26, matchup_factor, updated_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?) "
            "ON CONFLICT(real_club, gameweek) DO UPDATE SET opponent=excluded.opponent, is_home=excluded.is_home, "
            "played=excluded.played, win=excluded.win, draw=excluded.draw, loss=excluded.loss, "
            "league_position=excluded.league_position, club_avg_fc26=excluded.club_avg_fc26, "
            "matchup_factor=excluded.matchup_factor, updated_at=excluded.updated_at",
            (club, week, opponent_club.get(club), is_home_by_club.get(club),
             rec.get("played"), rec.get("win"), rec.get("draw"), rec.get("loss"), rec.get("position"),
             round(avg, 1), mf, now),
        )

    conn.commit()
    conn.close()

    top = sorted(zip(rows, ranks), key=lambda x: -x[1])[:5]
    print("Done. Top 5: " + ", ".join(f"{r['player_name']} ({rank})" for r, rank in top))
    return week


if __name__ == "__main__":
    week_arg = int(sys.argv[1]) if len(sys.argv) > 1 else None
    sync(week_arg)
