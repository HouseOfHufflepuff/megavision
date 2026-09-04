"""
Computes and stores one GW's worth of fan interest, attendance, and ticket
revenue for every real (12-team) matchup that week, using the real
formula in fans_algo.py (Rulez 2.2). Stored week over week in mega.db's
gw_fans table, same pattern as sync_best11.py.

Run:
    python3 sync_fans.py 2

Depends on sync_best11.py already having been run for a week at or before
the target week (uses the latest available Best 11 for Top XI fans).
"""
import sys
from datetime import datetime, timezone

import fans_algo as fa
import fantrax_live as fl
from common import TEAMS, fetch_stadiums
from db import connect


def sync_week(week):
    conn = connect()
    cur = conn.cursor()
    now = datetime.now(timezone.utc).isoformat()

    capacities = {code: v["capacity"] or 0 for code, v in fetch_stadiums().items()}

    title_rows = cur.execute("SELECT competition, team_code FROM titles WHERE season='26/27'").fetchall()
    legacy_fans = {code: fa.legacy_fan_value(code, title_rows) for code, _, _ in TEAMS}

    sess = fl._session()
    standings = fl.fetch_all_standings(sess)
    league_record_rank = fa.league_record_rank_by_code(standings)
    scoring_rank = fa.scoring_rank_by_code(standings)

    best11_week = cur.execute("SELECT MAX(week) FROM best11 WHERE week<=?", (week,)).fetchone()[0]
    topxi_fans = {code: 0.0 for code, _, _ in TEAMS}
    if best11_week is not None:
        for pos, slot_rank, name, club, code, fpts in cur.execute(
            "SELECT pos, slot_rank, player_name, real_club, team_code, fpts FROM best11 WHERE week=?", (best11_week,)
        ):
            if not code:
                continue
            is_top = pos in ("F", "M", "D") and slot_rank == 1
            topxi_fans[code] = topxi_fans.get(code, 0.0) + (fa.TOPXI_TOP_FANS if is_top else fa.TOPXI_REST_FANS)

    breakdowns = {}
    fanbase = {}
    for code, _, _ in TEAMS:
        b = fa.team_fan_count(league_record_rank.get(code), scoring_rank.get(code),
                               topxi_fans.get(code, 0.0), legacy_fans.get(code, 0))
        breakdowns[code] = b
        fanbase[code] = b["total"]

    games = [g for g in fl.fetch_schedule(sess) if g["week"] == week]
    ticket_price = 0.0 if week in fa.NON_REGULAR_SEASON_WEEKS else fa.REGULAR_SEASON_TICKET_PRICE

    cur.execute("DELETE FROM gw_fans WHERE week=?", (week,))
    results = []
    for g in games:
        home, away = g["home"], g["away"]
        game = fa.compute_game_fans(home, away, fanbase, capacities, league_record_rank)
        gate = game["attendance"] * ticket_price
        home_rev, away_rev = gate * fa.HOME_GATE_SHARE, gate * (1 - fa.HOME_GATE_SHARE)
        for code, opp, is_home, interest, rev in (
            (home, away, True, game["home_interest"], home_rev),
            (away, home, False, game["away_interest"], away_rev),
        ):
            cur.execute(
                "INSERT INTO gw_fans (week, team_code, opponent, is_home, base_score, fanbase, interest, "
                "attendance, ticket_revenue, bonuses, updated_at) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                (week, code, opp, int(is_home), fanbase.get(code), fanbase.get(code), interest,
                 game["attendance"], rev, ", ".join(game["bonuses"]), now),
            )
        results.append({"home": home, "away": away, **game, "gate": gate, "home_rev": home_rev, "away_rev": away_rev})

    conn.commit()
    conn.close()
    return results, breakdowns, league_record_rank, fanbase


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 sync_fans.py WEEK")
        sys.exit(1)
    week = int(sys.argv[1])
    results, breakdowns, league_record_rank, fanbase = sync_week(week)
    print(f"GW{week} fans (ticket price ${0.0 if week in fa.NON_REGULAR_SEASON_WEEKS else fa.REGULAR_SEASON_TICKET_PRICE:.2f}):\n")
    for g in sorted(results, key=lambda r: -r["attendance"]):
        tag = " *** SOLD OUT ***" if g["sold_out"] else ""
        bonuses = f" [{', '.join(g['bonuses'])}]" if g["bonuses"] else ""
        print(f"  {g['home']:4} vs {g['away']:4}  interest={g['combined_interest']:.0f}  "
              f"cap={g['capacity']:.0f}  attendance={g['attendance']:.0f}{tag}  "
              f"gate=${g['gate']:.2f} (H ${g['home_rev']:.2f} / A ${g['away_rev']:.2f}){bonuses}")
    print("\nReal fan count breakdown (league record + scoring standing + top XI + legacy -> total):")
    for code in sorted(breakdowns, key=lambda c: -breakdowns[c]["total"]):
        b = breakdowns[code]
        print(f"  {code:4} {b['league_record']:5.0f} + {b['scoring_standing']:5.0f} + {b['topxi']:5.1f} + {b['legacy']:4.0f} "
              f"= {b['total']:6.1f} fans")
