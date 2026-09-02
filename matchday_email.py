"""
Builds the weekly "matchday" preview email: this week's fixtures, last
week's scores, predicted scores, fan/capacity/revenue for each game, each
team's hot player, and any injured player on either roster.

Data sources: live Fantrax (schedule, standings, rosters/fpts, injury
icons), the live Google Sheet (stadium names/capacity, via common.py --
see the project note on retiring this dependency), and mega.db (titles,
best11, for the Fan Formula inputs shared with sync_fans.py).

Run:
    python3 matchday_email.py [week]

`week` is the displayed GW number (defaults to the next unplayed week found
in the Fantrax schedule). Prints the plain-text email body to stdout --
review before sending, this script never sends anything itself.
"""
import sys
from datetime import datetime, timezone

import fantrax_live as fl
import fans_algo as fa
from common import TEAMS, fetch_live_workbook, fetch_stadiums, fetch_trophy_room, tally_trophies
from db import connect

TEAM_FULL_NAME = {code: name for code, name, _ in TEAMS}
FORMATION_SLOTS = fl.FORMATION_SLOTS  # {"GK":1,"D":3,"M":4,"F":3}


def next_unplayed_week(games_by_week):
    """First week in the schedule -- Fantrax carries no per-game result in
    this feed, so "next" is just the earliest week present (today's actual
    matches haven't been played yet the very first time this runs each
    season; for a mid-season run this would need real result data, not
    built here since only week 1 exists so far)."""
    return min(games_by_week)


def team_predicted_score(roster):
    """Sum of the team's own best-XI (by the league's real GK+3D+4M+3F
    formation) fpts so far this season -- the closest same-shape estimate
    of what a team scores that we have real data for. Simple and explicit,
    not a hidden model: this is each team's own top scorers, not luck."""
    total = 0.0
    picked = []
    for pos, slots in FORMATION_SLOTS.items():
        candidates = sorted((p for p in roster if p["pos"] == pos), key=lambda p: -p["fpts"])
        for p in candidates[:slots]:
            total += p["fpts"]
            picked.append(p)
    return round(total, 1), picked


def hot_player(roster):
    scored = [p for p in roster if p["fpts"] > 0]
    if not scored:
        return None
    return max(scored, key=lambda p: p["fpts"])


def build(week=None):
    sess = fl._session()

    print("Fetching Fantrax schedule...", file=sys.stderr)
    all_games = fl.fetch_schedule(sess)
    games_by_week = {}
    for g in all_games:
        games_by_week.setdefault(g["week"], []).append(g)
    if week is None:
        week = next_unplayed_week(games_by_week)
    this_week_games = games_by_week.get(week, [])
    if not this_week_games:
        raise SystemExit(f"No scheduled games found for week {week}")

    print("Fetching live standings (last week's / season-to-date scores)...", file=sys.stderr)
    standings = fl.fetch_all_standings(sess)
    rank_by_code = fa.rank_by_code_from_standings(standings)
    fpts_by_code = {}
    for row in standings:
        if row["code"] and (row["code"] not in fpts_by_code or row["fpts_for"] > fpts_by_code[row["code"]]):
            fpts_by_code[row["code"]] = row["fpts_for"]

    print("Fetching all 12 rosters (membership + injuries)...", file=sys.stderr)
    rosters = {code: fl.fetch_full_roster(sess, team_id) for code, team_id in fl.FANTRAX_TEAM_ID.items()}

    print("Fetching real player-level fpts (roster-relative fpts reads 0 right after the Sr/Jr swap)...", file=sys.stderr)
    player_points = fl.fetch_all_player_points(sess)
    for roster in rosters.values():
        for p in roster:
            p["fpts"] = player_points.get(p["name"], p["fpts"])

    print("Fetching stadiums from the live sheet...", file=sys.stderr)
    wb = fetch_live_workbook()
    stadiums = fetch_stadiums(wb)

    print("Computing real fan counts (League Record + Scoring standing + Top XI + Legacy)...", file=sys.stderr)
    conn = connect()
    cur = conn.cursor()
    title_rows = cur.execute("SELECT competition, team_code FROM titles WHERE season='26/27'").fetchall()
    legacy_fans = {code: fa.legacy_fan_value(code, title_rows) for code, _, _ in TEAMS}
    scoring_rank = fa.scoring_rank_by_code(standings)

    best11_week = cur.execute("SELECT MAX(week) FROM best11 WHERE week<=?", (week,)).fetchone()[0]
    topxi_fans = {code: 0.0 for code, _, _ in TEAMS}
    mbp_code, mbp_fpts = None, -1
    if best11_week is not None:
        rows_by_pos = {}
        for pos, slot_rank, name, club, code, fpts in cur.execute(
            "SELECT pos, slot_rank, player_name, real_club, team_code, fpts FROM best11 WHERE week=? ORDER BY pos, slot_rank", (best11_week,)
        ):
            rows_by_pos.setdefault(pos, []).append((code, fpts))
            if fpts > mbp_fpts:
                mbp_fpts, mbp_code = fpts, code
        for pos, rows in rows_by_pos.items():
            for i, (code, fpts) in enumerate(rows):
                if not code:
                    continue
                is_top = pos in ("F", "M", "D") and i == 0
                topxi_fans[code] = topxi_fans.get(code, 0.0) + (fa.TOPXI_TOP_FANS if is_top else fa.TOPXI_REST_FANS)
    conn.close()

    breakdowns = {}
    fanbase = {}
    for code, _, _ in TEAMS:
        b = fa.team_fan_count(rank_by_code.get(code), scoring_rank.get(code), topxi_fans.get(code, 0.0), legacy_fans.get(code, 0))
        breakdowns[code] = b
        fanbase[code] = b["total"]

    capacities = {code: v["capacity"] or 0 for code, v in stadiums.items()}
    ticket_price = 0.0 if week in fa.NON_REGULAR_SEASON_WEEKS else fa.REGULAR_SEASON_TICKET_PRICE

    print("Building matchup previews...", file=sys.stderr)
    previews = []
    for g in this_week_games:
        home, away = g["home"], g["away"]
        game = fa.compute_game_fans(home, away, fanbase, capacities, rank_by_code)
        gate = game["attendance"] * ticket_price
        home_rev, away_rev = gate * fa.HOME_GATE_SHARE, gate * (1 - fa.HOME_GATE_SHARE)

        home_roster, away_roster = rosters[home], rosters[away]
        home_pred, home_picked = team_predicted_score(home_roster)
        away_pred, away_picked = team_predicted_score(away_roster)

        home_injured = [p for p in home_picked if p["injuries"]]
        away_injured = [p for p in away_picked if p["injuries"]]

        previews.append({
            "home": home, "away": away,
            "home_full": TEAM_FULL_NAME.get(home, home), "away_full": TEAM_FULL_NAME.get(away, away),
            "stadium": stadiums.get(home, {}).get("stadium") or "TBD",
            "capacity": capacities.get(home, 0),
            "home_last_wk": fpts_by_code.get(home, 0.0), "away_last_wk": fpts_by_code.get(away, 0.0),
            "home_pred": home_pred, "away_pred": away_pred,
            "home_hot": hot_player(home_roster), "away_hot": hot_player(away_roster),
            "attendance": game["attendance"], "capacity_pct": (game["attendance"] / game["capacity"] * 100) if game["capacity"] else 0,
            "sold_out": game["sold_out"], "bonuses": game["bonuses"],
            "gate": gate, "home_rev": home_rev, "away_rev": away_rev,
            "home_injured": home_injured, "away_injured": away_injured,
            "home_fanbase": fanbase.get(home, 0), "away_fanbase": fanbase.get(away, 0),
        })

    return week, previews, ticket_price


def money(v):
    return f"${v:,.2f}"


def render_email(week, previews, ticket_price):
    lines = []
    lines.append(f"MEGAVISION MATCHDAY PREVIEW -- Week {week}")
    lines.append(f"Ticket price this week: {money(ticket_price)}" if ticket_price else "Non-ticketed week (Community Shield/Super Cup rules)")
    lines.append("")
    lines.append(f"{len(previews)} games this week. Here's the breakdown, park to pitch.")
    lines.append("")

    for p in previews:
        lines.append("=" * 60)
        lines.append(f"{p['away_full']} ({p['away']}) at {p['home_full']} ({p['home']})")
        lines.append(f"{p['stadium']} -- capacity {p['capacity']:,.0f}")
        lines.append("")
        lines.append(f"Last week: {p['home']} {p['home_last_wk']:.1f} pts -- {p['away']} {p['away_last_wk']:.1f} pts")
        winner = p['home'] if p['home_pred'] > p['away_pred'] else (p['away'] if p['away_pred'] > p['home_pred'] else None)
        lines.append(f"Predicted: {p['home']} {p['home_pred']:.1f} -- {p['away']} {p['away_pred']:.1f}"
                      + (f"  (edge: {winner})" if winner else "  (dead even)"))
        lines.append("")

        for side, code, hot in (("Home", p["home"], p["home_hot"]), ("Away", p["away"], p["away_hot"])):
            if hot:
                lines.append(f"{side} hot player ({code}): {hot['name']} ({hot['pos']}, {hot['club']}) -- {hot['fpts']:.1f} pts so far")
            else:
                lines.append(f"{side} hot player ({code}): no scoring data yet")
        lines.append("")

        injured_all = [(p["home"], x) for x in p["home_injured"]] + [(p["away"], x) for x in p["away_injured"]]
        if injured_all:
            lines.append("Injury watch (rostered in the projected best XI):")
            for code, x in injured_all:
                lines.append(f"  {code} -- {x['name']} ({x['pos']}): {'; '.join(x['injuries'])}")
        else:
            lines.append("Injury watch: clean bill of health for both projected XIs.")
        lines.append("")

        sellout = " -- SOLD OUT" if p["sold_out"] else ""
        lines.append(f"Fans: {p['home']} fanbase {p['home_fanbase']:,.0f} / {p['away']} fanbase {p['away_fanbase']:,.0f}")
        lines.append(f"Attendance: {p['attendance']:,.0f} ({p['capacity_pct']:.0f}% of capacity){sellout}")
        if p["bonuses"]:
            lines.append(f"Occasion: {', '.join(p['bonuses'])}")
        if p["gate"] > 0:
            lines.append(f"Gate revenue: {money(p['gate'])} total -- {p['home']} {money(p['home_rev'])} / {p['away']} {money(p['away_rev'])}")
        lines.append("")

    lines.append("=" * 60)
    lines.append(f"Generated {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')} -- scores are each team's own best-XI fpts total "
                  "so far this season, not a betting line. Fan/attendance/revenue figures are the site's own Fan Formula model, not final until the "
                  "games are actually played.")
    return "\n".join(lines)


if __name__ == "__main__":
    week_arg = int(sys.argv[1]) if len(sys.argv) > 1 else None
    week, previews, ticket_price = build(week_arg)
    print(render_email(week, previews, ticket_price))
