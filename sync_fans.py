"""
Computes and stores one GW's worth of fan interest, attendance, and ticket
revenue for every real (12-team) matchup that week, using the algorithm in
fans_algo.py. Stored week over week in mega.db's gw_fans table, same
pattern as sync_best11.py.

Run:
    python3 sync_fans.py 2

Depends on sync_best11.py already having been run for a week at or before
the target week (uses the latest available Best 11 as the Top XI input).
"""
import sys
from datetime import datetime, timezone

import fans_algo as fa
import fantrax_live as fl
from common import (
    TEAMS, fetch_live_workbook, fetch_stadiums, fetch_trophy_room, tally_trophies,
)
from db import connect


def sync_week(week):
    conn = connect()
    cur = conn.cursor()
    now = datetime.now(timezone.utc).isoformat()

    wb = fetch_live_workbook()
    capacities = {code: v["capacity"] or 0 for code, v in fetch_stadiums(wb).items()}

    comps, seasons = fetch_trophy_room(wb)
    trophy_tally = tally_trophies(comps, seasons)
    current_titles = cur.execute("SELECT competition, team_code FROM titles WHERE season='26/27'").fetchall()
    for comp, code in current_titles:
        if comp in trophy_tally.get(code, {}):
            trophy_tally[code][comp] += 1
    trophy_counts = {code: sum(v.values()) for code, v in trophy_tally.items()}
    max_trophies = max(trophy_counts.values()) if trophy_counts else 0

    sess = fl._session()
    standings = fl.fetch_all_standings(sess)
    rank_by_code = fa.rank_by_code_from_standings(standings)

    best11_week = cur.execute("SELECT MAX(week) FROM best11 WHERE week<=?", (week,)).fetchone()[0]
    topxi_counts = {code: 0 for code, _, _ in TEAMS}
    mbp_code, mbp_fpts = None, -1
    if best11_week is not None:
        for pos, rank, name, club, code, fpts in cur.execute(
            "SELECT pos, slot_rank, player_name, real_club, team_code, fpts FROM best11 WHERE week=?", (best11_week,)
        ):
            if code:
                topxi_counts[code] += 1
                if fpts > mbp_fpts:
                    mbp_fpts, mbp_code = fpts, code

    base_scores = {}
    breakdowns = {}
    for code, _, _ in TEAMS:
        b = fa.base_score(code, rank_by_code.get(code), topxi_counts.get(code, 0),
                           trophy_counts.get(code, 0), max_trophies)
        mbp_v = fa.mbp_bonus(code, mbp_code)
        b["mbp"] = mbp_v
        b["total"] = round(b["total"] + mbp_v, 2)
        breakdowns[code] = b
        base_scores[code] = b["total"]

    total_capacity = sum(capacities.values())
    fanbase = fa.team_fanbase(base_scores, total_capacity)

    games = [g for g in fl.fetch_schedule(sess) if g["week"] == week]
    ticket_price = 0.0 if week in fa.NON_REGULAR_SEASON_WEEKS else fa.REGULAR_SEASON_TICKET_PRICE

    cur.execute("DELETE FROM gw_fans WHERE week=?", (week,))
    results = []
    for g in games:
        home, away = g["home"], g["away"]
        game = fa.compute_game_fans(home, away, fanbase, capacities, rank_by_code)
        gate = game["attendance"] * ticket_price
        home_rev, away_rev = gate * fa.HOME_GATE_SHARE, gate * (1 - fa.HOME_GATE_SHARE)
        for code, opp, is_home, interest, rev in (
            (home, away, True, game["home_interest"], home_rev),
            (away, home, False, game["away_interest"], away_rev),
        ):
            cur.execute(
                "INSERT INTO gw_fans (week, team_code, opponent, is_home, base_score, fanbase, interest, "
                "attendance, ticket_revenue, bonuses, updated_at) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                (week, code, opp, int(is_home), base_scores.get(code), fanbase.get(code), interest,
                 game["attendance"] if is_home else None, rev, ", ".join(game["bonuses"]), now),
            )
        results.append({"home": home, "away": away, **game, "gate": gate, "home_rev": home_rev, "away_rev": away_rev})

    conn.commit()
    conn.close()
    return results, breakdowns, rank_by_code, fanbase


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 sync_fans.py WEEK")
        sys.exit(1)
    week = int(sys.argv[1])
    results, breakdowns, rank_by_code, fanbase = sync_week(week)
    print(f"GW{week} fans (ticket price ${0.0 if week in fa.NON_REGULAR_SEASON_WEEKS else fa.REGULAR_SEASON_TICKET_PRICE:.2f}):\n")
    for g in sorted(results, key=lambda r: -r["attendance"]):
        tag = " *** SOLD OUT ***" if g["sold_out"] else ""
        bonuses = f" [{', '.join(g['bonuses'])}]" if g["bonuses"] else ""
        print(f"  {g['home']:4} vs {g['away']:4}  interest={g['combined_interest']:.0f}  "
              f"cap={g['capacity']:.0f}  attendance={g['attendance']:.0f}{tag}  "
              f"gate=${g['gate']:.2f} (H ${g['home_rev']:.2f} / A ${g['away_rev']:.2f}){bonuses}")
    print("\nBase score breakdown (standings/topxi/trophy/momentum/mbp -> total, fanbase):")
    for code in sorted(breakdowns, key=lambda c: rank_by_code.get(c, 99)):
        b = breakdowns[code]
        print(f"  {code:4} rank={rank_by_code.get(code, '—'):>2}  "
              f"{b['standings']:5.1f} + {b['topxi']:5.1f} + {b['trophy']:5.1f} + {b['momentum']:5.1f} + {b['mbp']:4.1f} "
              f"= {b['total']:6.1f}  fanbase={fanbase.get(code, 0):.0f}")
