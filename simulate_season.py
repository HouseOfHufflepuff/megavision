"""
Full-season financial simulation, using the real fans_algo.py formula (now
live on the site, matching Rulez section 2 directly) -- not a separate
approximation. Read-only -- never touches mega.db.

Fixes from the first version of this script, per commissioner feedback:
  - TV Bonus is a PAYOUT, never negative. Mega Fund is floored at $0 before
    computing TV Bonus/postseason -- if tickets+cups ever outrun pool
    inflow, that's a funding shortfall the league needs to cover with more
    real inflow sources, not a bill sent to teams disguised as a "bonus."
  - Models a minimum $100 of "other league fees" (stadium expansion,
    Federation Fee, youth-pick bounty, IRP pickups, cut-contract
    forfeitures, loan fees -- all real Rulez 2.1 pool inflows this sim
    does not track individually) as a flat pool inflow, per instruction.
    This is a placeholder aggregate, not derived from the (possibly
    outdated) rules doc -- the real per-fee amounts need to come from the
    commissioner, not be reverse-engineered from a document that may no
    longer be current.

Run:
    python3 simulate_season.py [seed]
"""
import random
import sys

import fans_algo as fa
import fantrax_live as fl
from common import TEAMS, fetch_stadiums

LEAGUE_WEEKS = 22  # Rulez 2.1 -- flag to the commissioner: confirmed the salary math should
                    # divide by 22, but unclear if the real schedule itself should also be
                    # only 22 weeks (Fantrax currently has 35 configured) -- see report.

CS_SC_PAYOUT = 5.0  # Community Shield / Super Cup, each -- fixed on-site 2026-09-03 (was $10/$5)
FA_CUP_PAYOUT = (40.0, 20.0)
CITADEL_CUP_PAYOUT = (20.0, 10.0)
REALIZED_TRANSFER_LEVY = 23.0  # from the real transfers table, 26/27 season to date
MIN_OTHER_LEAGUE_FEES = 100.0  # placeholder aggregate -- see module docstring

TV_BONUS_PCT = [0.40, 0.20, 0.10, 0.08, 0.07, 0.05, 0.04, 0.03, 0.01, 0.01, 0.01, 0.00]


def round_robin_schedule(codes, rounds=2):
    """Standard circle method -- n-1 weeks per single round robin, doubled
    for a return leg (home/away flipped) to hit 22 weeks with 12 teams."""
    n = len(codes)
    fixed = codes[0]
    rest = codes[1:]
    weeks = []
    for _ in range(n - 1):
        pairs = list(zip([fixed] + rest[:n // 2 - 1], rest[n // 2 - 1:][::-1]))
        weeks.append(pairs)
        rest = [rest[-1]] + rest[:-1]
    full = []
    for r in range(rounds):
        for wk in weeks:
            full.append([(h, a) for h, a in wk] if r % 2 == 0 else [(a, h) for h, a in wk])
    return full


def simulate(seed=None):
    rng = random.Random(seed)
    sess = fl._session()
    standings = fl.fetch_all_standings(sess)
    strength = {}
    for row in standings:
        if row["code"] and (row["code"] not in strength or row["fpts_for"] > strength[row["code"]]):
            strength[row["code"]] = row["fpts_for"] or 60.0
    codes = [c for c, _, _ in TEAMS]
    for c in codes:
        strength.setdefault(c, 60.0)

    stadiums = fetch_stadiums()
    capacity = {c: stadiums.get(c, {}).get("capacity") or 400 for c in codes}

    schedule = round_robin_schedule(codes, rounds=2)
    assert len(schedule) == LEAGUE_WEEKS, f"expected {LEAGUE_WEEKS} weeks, got {len(schedule)}"

    record_pts = {c: 0 for c in codes}
    cum_score = {c: 0.0 for c in codes}
    pool_out = 0.0
    team_ticket_rev = {c: 0.0 for c in codes}
    team_topxi_fans_total = {c: 0.0 for c in codes}

    # legacy fans: this season's known titles only (see fans_algo docstring
    # on the "last 3 years" simplification)
    legacy_fans = {c: 0 for c in codes}
    legacy_fans["QFC"] = fa.LEGACY_FANS_3YR["Mega Community Shield"]
    legacy_fans["BHB"] = fa.LEGACY_FANS_3YR["Mega Super Cup"]

    for week in schedule:
        week_scores = {c: max(20.0, rng.gauss(strength[c], 16.0)) for c in codes}
        for c in codes:
            cum_score[c] += week_scores[c]
        for home, away in week:
            if week_scores[home] > week_scores[away]:
                record_pts[home] += 3
            elif week_scores[home] < week_scores[away]:
                record_pts[away] += 3
            else:
                record_pts[home] += 1
                record_pts[away] += 1

        record_rank = {c: i + 1 for i, c in enumerate(sorted(codes, key=lambda c: -record_pts[c]))}
        scoring_rank = {c: i + 1 for i, c in enumerate(sorted(codes, key=lambda c: -cum_score[c]))}

        total_score = sum(week_scores.values())
        topxi_fans = {c: (fa.TOPXI_TOP_FANS * 3 + fa.TOPXI_REST_FANS * 8) * (week_scores[c] / total_score) for c in codes}
        for c in codes:
            team_topxi_fans_total[c] += topxi_fans[c]

        team_fans = {
            c: fa.team_fan_count(record_rank[c], scoring_rank[c], topxi_fans[c], legacy_fans[c])["total"]
            for c in codes
        }

        for home, away in week:
            tickets = min(team_fans[home] + team_fans[away], capacity[home])
            gate = tickets * fa.REGULAR_SEASON_TICKET_PRICE
            team_ticket_rev[home] += gate * fa.HOME_GATE_SHARE
            team_ticket_rev[away] += gate * (1 - fa.HOME_GATE_SHARE)
            pool_out += gate

    final_record_rank = sorted(codes, key=lambda c: -record_pts[c])

    def bracket_winner_runnerup(field):
        cur = list(field)
        last_beaten = None
        while len(cur) > 1:
            nxt = []
            for i in range(0, len(cur), 2):
                a, b = cur[i], cur[i + 1]
                sa, sb = rng.gauss(strength[a], 16), rng.gauss(strength[b], 16)
                w, loser = (a, b) if sa >= sb else (b, a)
                nxt.append(w)
                if len(cur) == 2:
                    last_beaten = loser
            cur = nxt
        return cur[0], last_beaten

    fa_winner, fa_runnerup = bracket_winner_runnerup(final_record_rank[:8])
    cit_winner, cit_runnerup = bracket_winner_runnerup(final_record_rank[4:12])

    cup_payouts = {c: 0.0 for c in codes}
    cup_payouts[fa_winner] += FA_CUP_PAYOUT[0]
    cup_payouts[fa_runnerup] += FA_CUP_PAYOUT[1]
    cup_payouts[cit_winner] += CITADEL_CUP_PAYOUT[0]
    cup_payouts[cit_runnerup] += CITADEL_CUP_PAYOUT[1]
    cup_payouts["QFC"] += CS_SC_PAYOUT
    cup_payouts["BHB"] += CS_SC_PAYOUT
    pool_out += FA_CUP_PAYOUT[0] + FA_CUP_PAYOUT[1] + CITADEL_CUP_PAYOUT[0] + CITADEL_CUP_PAYOUT[1] + CS_SC_PAYOUT * 2

    cl_field = final_record_rank[:4]
    s1, s2, s3, s4 = cl_field
    sf1 = s1 if rng.gauss(strength[s1], 16) >= rng.gauss(strength[s4], 16) else s4
    sf2 = s2 if rng.gauss(strength[s2], 16) >= rng.gauss(strength[s3], 16) else s3
    cl_winner = sf1 if rng.gauss(strength[sf1], 16) >= rng.gauss(strength[sf2], 16) else sf2
    cl_loser = sf2 if cl_winner == sf1 else sf1
    eu1, eu2 = final_record_rank[4], final_record_rank[5]
    eu_winner = eu1 if rng.gauss(strength[eu1], 16) >= rng.gauss(strength[eu2], 16) else eu2
    eu_loser = eu2 if eu_winner == eu1 else eu1

    return {
        "codes": codes, "strength": strength, "capacity": capacity,
        "record_pts": record_pts, "cum_score": cum_score, "final_record_rank": final_record_rank,
        "team_ticket_rev": team_ticket_rev, "cup_payouts": cup_payouts, "pool_out_tickets_cups": pool_out,
        "cl_winner": cl_winner, "cl_loser": cl_loser, "eu_winner": eu_winner, "eu_loser": eu_loser,
        "fa_winner": fa_winner, "fa_runnerup": fa_runnerup, "cit_winner": cit_winner, "cit_runnerup": cit_runnerup,
    }


def real_salary_totals():
    from db import connect
    conn = connect()
    out = {r[0]: r[1] for r in conn.execute(
        "SELECT team_code, ROUND(SUM(wage),2) FROM team_player_wages WHERE season='26/27' GROUP BY team_code"
    )}
    conn.close()
    return out


def real_transfer_levies_by_buyer():
    from db import connect
    conn = connect()
    out = {}
    for to_team, amount in conn.execute("SELECT to_team, amount FROM transfers"):
        out[to_team] = out.get(to_team, 0.0) + amount * 0.10
    conn.close()
    return out


def report(seed=None):
    sim = simulate(seed)
    codes = sim["codes"]
    salary = real_salary_totals()
    levies = real_transfer_levies_by_buyer()

    salary_total = sum(salary.get(c, 0) or 0 for c in codes)
    pool_in = salary_total + REALIZED_TRANSFER_LEVY + MIN_OTHER_LEAGUE_FEES
    pool_out_tickets_cups = sim["pool_out_tickets_cups"]
    mega_fund_raw = pool_in - pool_out_tickets_cups
    mega_fund = max(0.0, mega_fund_raw)
    shortfall = min(0.0, mega_fund_raw)

    final_rank = sim["final_record_rank"]
    tv_bonus = {c: mega_fund * 0.60 * TV_BONUS_PCT[final_rank.index(c)] for c in codes}
    postseason_pool = mega_fund * 0.40
    postseason = {c: 0.0 for c in codes}
    postseason[sim["cl_winner"]] += postseason_pool * 0.50
    postseason[sim["cl_loser"]] += postseason_pool * 0.20
    postseason[sim["eu_winner"]] += postseason_pool * 0.20
    postseason[sim["eu_loser"]] += postseason_pool * 0.10

    # other league fees: modeled as a flat per-team share, since there's no
    # real per-team tracking of stadium/IRP/loan/cut fees yet (see docstring)
    other_fee_share = MIN_OTHER_LEAGUE_FEES / len(codes)

    print(f"=== SIMULATED {LEAGUE_WEEKS}-WEEK SEASON (seed={seed}) -- real fan formula ===\n")
    print("Final League Record standing (simulated):")
    for i, c in enumerate(final_rank, 1):
        print(f"  {i:2}. {c:4}  {sim['record_pts'][c]:3} pts   scoring-total {sim['cum_score'][c]:7.1f}")

    print(f"\nFA Cup: {sim['fa_winner']} def. {sim['fa_runnerup']} (${FA_CUP_PAYOUT[0]:.0f}/${FA_CUP_PAYOUT[1]:.0f})")
    print(f"Citadel Cup: {sim['cit_winner']} def. {sim['cit_runnerup']} (${CITADEL_CUP_PAYOUT[0]:.0f}/${CITADEL_CUP_PAYOUT[1]:.0f})")
    print(f"Community Shield: QFC (${CS_SC_PAYOUT:.0f})   Super Cup: BHB (${CS_SC_PAYOUT:.0f})")
    print(f"Champions League: {sim['cl_winner']} def. {sim['cl_loser']} in the final")
    print(f"Europa: {sim['eu_winner']} def. {sim['eu_loser']}")

    print(f"\n=== POOL ===")
    print(f"  IN  -- salaries ${salary_total:.2f} + transfer levy ${REALIZED_TRANSFER_LEVY:.2f} "
          f"+ other league fees (min ${MIN_OTHER_LEAGUE_FEES:.2f}, placeholder) = ${pool_in:.2f}")
    print(f"  OUT -- tickets + cups (paid during season) = ${pool_out_tickets_cups:.2f}")
    if shortfall < 0:
        print(f"  SHORTFALL before flooring: ${shortfall:.2f} -- pool would have gone negative; floored to $0 for payout purposes.")
    print(f"  MEGA FUND (leftover, floored at $0, 100% redistributed) = ${mega_fund:.2f}")
    print(f"     -> TV Bonus pool (60%) = ${mega_fund*0.60:.2f}   Postseason pool (40%) = ${postseason_pool:.2f}")

    print(f"\n=== FULL SEASON FINANCIAL PICTURE, PER TEAM ===")
    print(f"{'Team':4} {'Salary(out)':>11} {'OtherFees':>9} {'Levy(out)':>9} {'Tickets(in)':>11} {'Cups(in)':>9} {'TV Bonus':>9} {'Postseason':>10} {'NET':>9}")
    grand_net = 0.0
    for c in codes:
        sal = salary.get(c, 0) or 0
        lev = levies.get(c, 0.0)
        tix = sim["team_ticket_rev"][c]
        cup = sim["cup_payouts"][c]
        tv = tv_bonus[c]
        post = postseason[c]
        net = -sal - other_fee_share - lev + tix + cup + tv + post
        grand_net += net
        print(f"{c:4} {-sal:11.2f} {-other_fee_share:9.2f} {-lev:9.2f} {tix:11.2f} {cup:9.2f} {tv:9.2f} {post:10.2f} {net:9.2f}")

    print(f"\nSum of every team's NET P&L across the season: ${grand_net:.2f}  (should be ~$0.00 -- closed pool, nothing created or destroyed)")
    print(f"TV Bonus range: ${min(tv_bonus.values()):.2f} to ${max(tv_bonus.values()):.2f} -- all non-negative: {all(v >= 0 for v in tv_bonus.values())}")


if __name__ == "__main__":
    seed = int(sys.argv[1]) if len(sys.argv) > 1 else 42
    report(seed)
