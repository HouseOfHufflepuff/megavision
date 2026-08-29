"""
The MEGAVISION Rank algorithm: a 0-100 per-player, per-gameweek projection
score. See sync_megavision_rank.py for the pipeline that calls this against
real data; this module is pure functions, no I/O, so the formula can be
unit-tested/tuned on its own.

Design (first pass, v1):

  1. RAW COMPOSITE -- FC 26 overall (talent) plus three context bonuses:
     team strength (players on stacked squads get more service), matchup
     (a weak upcoming opponent, small home boost), and current-season form
     (already outproducing the position average). Each bonus is scaled
     small relative to overall (5-15 pts of overall) so talent stays the
     dominant signal -- context nudges the order, it doesn't invert it.

  2. BELL CURVE -- the raw composite, standardized (z-score) across every
     player in the pool that gameweek, then mapped onto a 0-100 scale
     centered at 50. This is what makes it "a distribution": most players
     cluster in the middle, and reaching the 90s requires being several
     standard deviations above the field, not just having a good number.

  3. START-CERTAINTY GATE -- applied AFTER the bell curve, multiplicative.
     A gate of 1.0 needs a clean, undoubted FFS starting XI slot -- this is
     the mechanism that makes "guaranteed start" a hard precondition for
     the top of the board, per the brief: the single highest talent+matchup
     score in the league still can't crack 100 while there's any doubt
     about them actually playing.
"""

TEAM_STRENGTH_WEIGHT = 0.4
MATCHUP_OPPONENT_WEIGHT = 0.5
HOME_BONUS = 3.0
AWAY_PENALTY = 3.0
FORM_WEIGHT = 0.5

BELL_CENTER = 50.0
BELL_SPREAD = 15.0  # points per standard deviation

GATE_CLEAN_START = 1.00
GATE_DOUBTFUL_START = 0.75
GATE_NOT_STARTING = 0.45
GATE_OUT = 0.15


def raw_composite(fc26_overall, club_avg_fc26, league_avg_fc26,
                   opponent_avg_fc26, is_home, player_score, position_avg_score):
    """One player's pre-normalization score. All the _avg_ inputs are
    already computed across the pool by the caller (see sync_megavision_rank.py)."""
    team_strength_bonus = (club_avg_fc26 - league_avg_fc26) * TEAM_STRENGTH_WEIGHT
    matchup_bonus = (league_avg_fc26 - opponent_avg_fc26) * MATCHUP_OPPONENT_WEIGHT if opponent_avg_fc26 is not None else 0.0
    if is_home is True:
        matchup_bonus += HOME_BONUS
    elif is_home is False:
        matchup_bonus -= AWAY_PENALTY
    form_bonus = (player_score - position_avg_score) * FORM_WEIGHT if player_score is not None and position_avg_score is not None else 0.0
    return fc26_overall + team_strength_bonus + matchup_bonus + form_bonus


def bell_curve(raw_values):
    """[raw] -> [0-100 bell-shaped score], mean/stdev computed across the
    whole list. Population stdev (not sample) -- we have the entire pool,
    not a sample of it."""
    n = len(raw_values)
    if n == 0:
        return []
    mean = sum(raw_values) / n
    variance = sum((v - mean) ** 2 for v in raw_values) / n
    stdev = variance ** 0.5
    if stdev == 0:
        return [BELL_CENTER for _ in raw_values]
    return [max(1.0, min(100.0, BELL_CENTER + BELL_SPREAD * (v - mean) / stdev)) for v in raw_values]


def start_gate(ffs_start, ffs_doubt, is_out):
    """is_out: explicit injury/unavailability (Fantrax injury_status set
    with an "Out"/"Inactive" tone, or FFS's Out list) -- distinct from
    ffs_doubt (a live fitness-test %, could still play)."""
    if is_out:
        return GATE_OUT
    if not ffs_start:
        return GATE_NOT_STARTING
    if ffs_doubt:
        return GATE_DOUBTFUL_START
    return GATE_CLEAN_START


def matchup_factor(club_avg_fc26, league_avg_fc26, opponent_avg_fc26, is_home):
    """The same matchup term used inside raw_composite, exposed standalone
    so a team's "how favorable is this fixture" number can be shown on its
    own (Matchups tab) without recomputing a whole player's composite."""
    bonus = (league_avg_fc26 - opponent_avg_fc26) * MATCHUP_OPPONENT_WEIGHT if opponent_avg_fc26 is not None else 0.0
    if is_home is True:
        bonus += HOME_BONUS
    elif is_home is False:
        bonus -= AWAY_PENALTY
    return round(bonus, 1)


LIKELIHOOD_START_MULT = 5.0
LIKELIHOOD_DOUBT_MULT = 2.5
LIKELIHOOD_BENCH_MULT = 1.0
LIKELIHOOD_OUT_MULT = 0.1
LIKELIHOOD_SHARPNESS = 8.0  # divisor on fc26_overall before exponentiating; lower = sharper separation by talent


def start_likelihoods(group):
    """group: [{fc26_overall, ffs_start, ffs_doubt, is_out}, ...] -- every
    player at one position on one real club's squad. Returns a parallel
    list of 0-100 floats that sums to exactly 100: a softmax over FC 26
    overall, scaled hard for a confirmed FFS starter and down hard for a
    doubt/out. This estimates XI-selection odds, not minutes or points --
    a nailed-on starter should land near 100 within their own position
    group even if a rival squad's backup at the same slot rates higher on
    raw talent alone."""
    if not group:
        return []
    weights = []
    for p in group:
        if p["is_out"]:
            mult = LIKELIHOOD_OUT_MULT
        elif p["ffs_start"] and not p["ffs_doubt"]:
            mult = LIKELIHOOD_START_MULT
        elif p["ffs_start"] and p["ffs_doubt"]:
            mult = LIKELIHOOD_DOUBT_MULT
        else:
            mult = LIKELIHOOD_BENCH_MULT
        weights.append(pow(2.718281828, (p["fc26_overall"] or 50) / LIKELIHOOD_SHARPNESS) * mult)
    total = sum(weights)
    if total == 0:
        return [round(100.0 / len(group), 1)] * len(group)
    pcts = [round(w / total * 100, 1) for w in weights]
    drift = round(100.0 - sum(pcts), 1)
    if pcts:
        pcts[pcts.index(max(pcts))] += drift  # force an exact 100.0 sum through rounding
    return pcts


def compute_ranks(players):
    """players: list of dicts, each with raw_composite inputs already
    resolved to keys: fc26_overall, club_avg_fc26, league_avg_fc26,
    opponent_avg_fc26, is_home, score, position_avg_score, ffs_start,
    ffs_doubt, is_out. Returns a parallel list of final 0-100 scores."""
    raws = [
        raw_composite(
            p["fc26_overall"], p["club_avg_fc26"], p["league_avg_fc26"],
            p["opponent_avg_fc26"], p["is_home"], p["score"], p["position_avg_score"],
        )
        for p in players
    ]
    bells = bell_curve(raws)
    gates = [start_gate(p["ffs_start"], p["ffs_doubt"], p["is_out"]) for p in players]
    return [round(max(1.0, min(100.0, b * g)), 1) for b, g in zip(bells, gates)]
