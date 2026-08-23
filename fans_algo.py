"""
The Fan Interest algorithm (v2, redoing the placeholder 80%-of-capacity
assumption from the first Fans tab pass). Two layers:

  1. BASE SCORE (season-level, recomputed every GW): how popular is this
     team overall, right now -- a blend of standings, Top 11 ownership,
     trophies, MBP, and current win/loss momentum. This is each team's
     season-long "brand strength," independent of who they're playing.

  2. MATCHUP FANS (per-fixture, this week only): base score converts into
     an actual fan-count number (see fanbase_for_teams), then home + away
     combine and get boosted for a big occasion (derby, title-race clash,
     bottom-team drama, upset buzz) before being capped at the host
     stadium's capacity. Overflow -- interested fans beyond what the
     stadium can hold -- is simply lost demand for that game, not
     redistributed elsewhere (the simple choice; redistributing overflow
     to other same-week games was considered and rejected for now, see
     README notes in the Fans tab).

Every weight below is a judgment call, not a league-decided rule (only the
five INPUT signals -- standings, Top 11, MBP, trophies, and the two
matchup situations named -- came from the user; the numeric weights and
the two extra signals (momentum, upset buzz) are this script's own call,
clearly labeled as such wherever they're displayed).
"""

# ---- rivalries: HUF-CRG, POW-TTS, BHB-FAV were specified directly; the
# other 6 teams are paired up here as a first guess (thematic, not
# geographic/historical -- there's no real-world basis to draw on) ----
RIVALRIES = [
    frozenset({"HUF", "CRG"}),
    frozenset({"POW", "TTS"}),
    frozenset({"BHB", "FAV"}),
    frozenset({"REN", "WTF"}),   # "Real News" vs "What The FC" -- newsroom rivalry
    frozenset({"QFC", "ASS"}),   # Quidpool vs Wholeassed -- the crude-name derby
    frozenset({"DU", "NAC"}),    # the remaining pair
]

# ---- base score weights (season-level, out of 100 max) ----
STANDINGS_WEIGHT = 45   # HIGH, per instruction
TOPXI_WEIGHT = 25       # MEDIUM, per instruction
TROPHY_WEIGHT = 15      # LOW, per instruction
MBP_WEIGHT = 5          # VERY LOW, per instruction
MOMENTUM_WEIGHT = 10    # LOW-MEDIUM -- our own addition, rewards SHORT-term
                         # form distinctly from the slower-moving standings
                         # component. 0 until real win/loss results exist.

# ---- matchup bonuses (multiplicative, applied to this week's combined
# home+away fan interest before the stadium cap) ----
RIVALRY_BONUS = 0.35     # HIGH, per instruction
TOP1V2_BONUS = 0.08      # VERY LOW, per instruction ("battle between 1 & 2")
BOTTOM_TEAM_BONUS = 0.08  # VERY LOW, per instruction ("...& bottom team")
UPSET_BUZZ_BONUS = 0.12   # LOW -- our own addition: residual buzz the week
                           # after a big upset. 0 until real results exist.

# GW1 is Community Shield/Super Cup/FA Cup play, not a regular-season game
# -- no salary draw, no regular ticket price. Shared with update_rosters.py
# and sync_fans.py so there's one source of truth.
NON_REGULAR_SEASON_WEEKS = {1}
REGULAR_SEASON_TICKET_PRICE = 0.05
HOME_GATE_SHARE = 0.80  # League Schedule tab's own param cell (80/20 home/away)

# ---- total league fanbase: static anchor, dynamic allocation. We know
# total stadium capacity (a real, stable number) -- the total fan pool is
# defined as a multiple of it, so the "how big is the whole pie" question
# has a stable, real-world-grounded anchor. All the week-to-week and
# season-to-season MOVEMENT then happens in each team's SHARE of that pool
# (driven by the dynamic base score), not in an arbitrarily wobbling total
# -- a wobbling total would just add noise without rewarding anything,
# whereas a fixed pool with dynamic shares directly rewards a team's
# results with a bigger slice. FANBASE_MULTIPLIER itself was picked
# empirically against GW1's real fixtures/base scores: 0.35 gives most
# games in the 55-100% capacity range with occasional sellouts on the
# strongest combined-interest matchups, rather than either everything or
# nothing selling out -- that's the "small stadiums usually full, big
# stadiums occasionally sell out for a big match" feel being asked for.
# Could be made dynamic later too (e.g. tied to aggregate league scoring
# or total prior-week attendance, so a genuinely exciting season grows the
# whole pie) -- noted as a future direction, not built now: there's only
# one real week of signal (GW1) so far to calibrate a trend against.
FANBASE_MULTIPLIER = 0.35


def rank_by_code_from_standings(standings):
    """standings: fantrax_live.fetch_all_standings()'s output (24 rows, Sr +
    Jr). Jr folds into Sr, and only Jr has real signal right now (Sr teams
    are still all tied at rank 13, 0-0-0) -- take whichever entry per code
    has the higher fpts_for, works automatically once Sr teams have real
    results too. Returns {code: rank 1-12}, re-ranked from whichever source
    was picked per team (mixing Jr ranks 1-12 with tied Sr rank 13 isn't a
    clean ordering on its own)."""
    fpts_by_code = {}
    for row in standings:
        if not row["code"]:
            continue
        if row["code"] not in fpts_by_code or row["fpts_for"] > fpts_by_code[row["code"]]:
            fpts_by_code[row["code"]] = row["fpts_for"]
    ordered = sorted(fpts_by_code, key=lambda c: -fpts_by_code[c])
    return {code: i + 1 for i, code in enumerate(ordered)}


def base_score(code, standings_rank, topxi_count, trophy_count, max_trophy_count,
                win_streak=0, loss_streak=0):
    """0-100ish. standings_rank is 1 = best. topxi_count is how many of the
    11 Best-11 slots this team owns (0-11). win_streak/loss_streak default
    0 (no real results yet -- see MOMENTUM_WEIGHT)."""
    standings_v = ((13 - standings_rank) / 12) * STANDINGS_WEIGHT if standings_rank else 0
    topxi_v = (topxi_count / 11) * TOPXI_WEIGHT
    trophy_v = (trophy_count / max_trophy_count) * TROPHY_WEIGHT if max_trophy_count else 0
    momentum_v = min(win_streak, 5) / 5 * MOMENTUM_WEIGHT - min(loss_streak, 5) / 5 * MOMENTUM_WEIGHT
    return {
        "standings": round(standings_v, 2), "topxi": round(topxi_v, 2),
        "trophy": round(trophy_v, 2), "momentum": round(momentum_v, 2),
        "total": round(standings_v + topxi_v + trophy_v + momentum_v, 2),
    }


def mbp_bonus(code, mbp_code):
    return MBP_WEIGHT if code == mbp_code else 0.0


def team_fanbase(base_scores_with_mbp, total_capacity):
    """base_scores_with_mbp: {code: base_total_including_mbp}. Returns
    {code: fanbase} -- each team's share of the static total pool."""
    total_pool = total_capacity * FANBASE_MULTIPLIER
    grand_total = sum(base_scores_with_mbp.values()) or 1
    return {code: total_pool * (v / grand_total) for code, v in base_scores_with_mbp.items()}


def matchup_bonuses(home, away, standings_rank_by_code, upset_last_week=None):
    """Returns (multiplier, [reasons]) for this specific fixture."""
    mult = 1.0
    reasons = []
    if frozenset({home, away}) in RIVALRIES:
        mult += RIVALRY_BONUS
        reasons.append(f"Derby Day (+{RIVALRY_BONUS:.0%})")
    ranks = standings_rank_by_code
    if ranks.get(home) in (1, 2) and ranks.get(away) in (1, 2) and ranks.get(home) != ranks.get(away):
        mult += TOP1V2_BONUS
        reasons.append(f"#1 vs #2 clash (+{TOP1V2_BONUS:.0%})")
    max_rank = max(ranks.values()) if ranks else None
    if max_rank and (ranks.get(home) == max_rank or ranks.get(away) == max_rank):
        mult += BOTTOM_TEAM_BONUS
        reasons.append(f"Bottom-of-the-table drama (+{BOTTOM_TEAM_BONUS:.0%})")
    upset_last_week = upset_last_week or set()
    if home in upset_last_week or away in upset_last_week:
        mult += UPSET_BUZZ_BONUS
        reasons.append(f"Upset buzz (+{UPSET_BUZZ_BONUS:.0%})")
    return mult, reasons


def compute_game_fans(home, away, fanbase_by_code, capacity_by_code, standings_rank_by_code, upset_last_week=None):
    """One game's attendance: combine home + away fan interest, apply this
    week's matchup bonuses, cap at the host stadium's capacity. Overflow
    (interest beyond capacity) is discarded, not redistributed -- see the
    module docstring."""
    mult, reasons = matchup_bonuses(home, away, standings_rank_by_code, upset_last_week)
    home_interest = fanbase_by_code.get(home, 0) * mult
    away_interest = fanbase_by_code.get(away, 0) * mult
    combined = home_interest + away_interest
    capacity = capacity_by_code.get(home) or 0
    attendance = min(combined, capacity)
    sold_out = combined > capacity
    return {
        "home_interest": home_interest, "away_interest": away_interest,
        "combined_interest": combined, "capacity": capacity,
        "attendance": attendance, "sold_out": sold_out,
        "overflow": max(0, combined - capacity), "multiplier": mult, "bonuses": reasons,
    }
