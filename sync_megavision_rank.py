"""
Computes the MEGAVISION Rank (see rank_algo.py) for every player already
loaded into epl_players/player_gameweek by sync_player_ranks.py, and writes
it back into player_gameweek.megavision_rank.

Run:
    python3 sync_player_ranks.py     # populate/refresh the raw data first
    python3 sync_megavision_rank.py [week]
"""
import sys
import unicodedata

import ffs_scrape
import rank_algo
from db import connect


def _fold(s):
    return unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode("ascii").lower().strip()


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

    # club_avg_fc26: mean overall of every tracked player at that club
    club_totals = {}
    for r in rows:
        club_totals.setdefault(r["real_club"], []).append(r["fc26_overall"])
    club_avg_fc26 = {c: sum(v) / len(v) for c, v in club_totals.items()}
    league_avg_fc26 = sum(club_avg_fc26.values()) / len(club_avg_fc26)

    # position_avg_score: mean current-week score by position (missing scores excluded)
    pos_scores = {}
    for r in rows:
        if r["score"] is not None:
            pos_scores.setdefault(r["fantrax_position"], []).append(r["score"])
    position_avg_score = {p: sum(v) / len(v) for p, v in pos_scores.items()}

    print("Scraping opponent/home-away from fantasyfootballscout.co.uk/team-news...", file=sys.stderr)
    ffs_data = ffs_scrape.fetch_and_parse()
    opponent_club = {club: info["opponent_name"] for club, info in ffs_data.items()}
    is_home_by_club = {club: info["is_home"] for club, info in ffs_data.items()}

    inputs = []
    for r in rows:
        club = r["real_club"]
        opp_name = opponent_club.get(club)
        opp_avg = None
        if opp_name:
            opp_folded = _fold(opp_name)
            for c2 in club_avg_fc26:
                if _fold(_club_display_name(c2)) == opp_folded:
                    opp_avg = club_avg_fc26[c2]
                    break
        is_out = bool(r["injury_status"]) or bool(r["ffs_negative_mention"] and not r["ffs_doubt"])
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

    conn = connect()
    cur = conn.cursor()
    for r, rank in zip(rows, ranks):
        cur.execute(
            "UPDATE player_gameweek SET megavision_rank=? WHERE player_name=? AND real_club=? AND gameweek=?",
            (rank, r["player_name"], r["real_club"], week),
        )
    conn.commit()
    conn.close()

    top = sorted(zip(rows, ranks), key=lambda x: -x[1])[:5]
    print(f"Done. Top 5: " + ", ".join(f"{r['player_name']} ({rank})" for r, rank in top))
    return week


CLUB_DISPLAY_NAMES = {
    "ARS": "Arsenal", "AVL": "Aston Villa", "BOU": "AFC Bournemouth", "BRE": "Brentford",
    "BHA": "Brighton and Hove Albion", "CHE": "Chelsea", "COV": "Coventry City",
    "CRY": "Crystal Palace", "EVE": "Everton", "FUL": "Fulham", "HUL": "Hull City",
    "IPS": "Ipswich Town", "LEE": "Leeds United", "LIV": "Liverpool", "MCI": "Manchester City",
    "MUN": "Manchester United", "NEW": "Newcastle United", "NOT": "Nottingham Forest",
    "SUN": "Sunderland", "TOT": "Tottenham Hotspur",
}


def _club_display_name(code):
    return CLUB_DISPLAY_NAMES.get(code, code)


if __name__ == "__main__":
    week_arg = int(sys.argv[1]) if len(sys.argv) > 1 else None
    sync(week_arg)
