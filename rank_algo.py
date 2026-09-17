"""
The MEGAVISION Rank algorithm: a 0-100 per-player, per-gameweek projection
score. See sync_megavision_rank.py for the pipeline that calls this against
real data; this module is pure functions, no I/O, so the formula can be
unit-tested/tuned on its own.

Design v2 (2026-09-17, per Jer -- replaced v1's additive-bonus +
z-score-bell-curve + multiplicative-gate design): a STRAIGHT weighted
percentage blend, no layers. Every factor is first converted to its own
0-100 sub-score, then combined with a fixed weight -- the final number is
literally readable as "this much talent, this much recent form, this much
start-certainty," nothing hidden in a bell curve or a multiplicative gate.

Factors and weights (sum to 100%):
    10%  FC26 overall rating
    35%  Season fantasy points total (Fantrax, cumulative)
    10%  Last real gameweek's fantasy total (FPL total_points -- Fantrax's
         own API has no per-gameweek player-scoring endpoint, confirmed by
         testing; see sync_player_ranks.fetch_minutes_last_week)
    5%   Last real gameweek's minutes played
    5%   Team strength -- own club's real EPL standings position
    5%   Opponent weakness -- opponent's real EPL standings position, reversed
    20%  fantasyfootballscout.co.uk predicted-XI/doubt/out read
    10%  rotowire.com depth-chart read

See compute_rank() for the exact combination.
"""

RANK_WEIGHTS = {
    "fc26": 0.10,
    "season_fpts": 0.35,
    "last_game_fpts": 0.10,
    "last_game_minutes": 0.05,
    "team_strength": 0.05,
    "opponent_weakness": 0.05,
    "ffs": 0.20,
    "roto": 0.10,
}
assert abs(sum(RANK_WEIGHTS.values()) - 1.0) < 1e-9, "RANK_WEIGHTS must sum to 100%"

EPL_CLUB_COUNT = 20  # for standings-position normalization: 1 = top of the table, 20 = bottom

# Kept for the club-level Matchups display (build_rank.py), which is a
# separate FC26-quality-based metric from the standings-based
# team_strength/opponent_weakness rank factors above -- not part of the
# player Rank formula itself.
TEAM_STRENGTH_WEIGHT = 0.4
MATCHUP_OPPONENT_WEIGHT = 0.5
HOME_BONUS = 3.0
AWAY_PENALTY = 3.0


def _minmax(value, lo, hi):
    """value scaled into [0,100] given the pool's [lo,hi] range. Falls back
    to a neutral 50 when there's no real range to scale against (missing
    data, or every player in the group tied)."""
    if value is None or lo is None or hi is None or hi <= lo:
        return 50.0
    return max(0.0, min(100.0, 100.0 * (value - lo) / (hi - lo)))


def fc26_subscore(fc26_overall):
    return max(0.0, min(100.0, fc26_overall if fc26_overall is not None else 0.0))


def season_fpts_subscore(season_fpts, position_min, position_max):
    """Min-max normalized WITHIN the player's own Fantrax position group --
    a GK's season point total and a forward's aren't on the same scale
    under Fantrax's own scoring rules, so comparing them league-wide would
    be apples to oranges."""
    return _minmax(season_fpts, position_min, position_max)


def last_game_fpts_subscore(last_game_fpts, position_min, position_max):
    return _minmax(last_game_fpts, position_min, position_max)


def last_game_minutes_subscore(minutes):
    if minutes is None:
        return 0.0
    return max(0.0, min(100.0, minutes / 90.0 * 100.0))


def team_strength_subscore(own_position):
    """Real EPL standings position (1=top, 20=bottom) -> 0-100, top club
    of the table scores 100."""
    if own_position is None:
        return 50.0
    return max(0.0, min(100.0, 100.0 * (EPL_CLUB_COUNT - own_position) / (EPL_CLUB_COUNT - 1)))


def opponent_weakness_subscore(opponent_position):
    """The mirror of team_strength_subscore -- a bottom-of-the-table
    opponent (position 20) scores 100 (a very favorable matchup); a
    league-leading opponent (position 1) scores 0."""
    if opponent_position is None:
        return 50.0
    return max(0.0, min(100.0, 100.0 * (opponent_position - 1) / (EPL_CLUB_COUNT - 1)))


# fantasyfootballscout.co.uk sub-score -- the exact same tiers the old (v1)
# multiplicative start-certainty gate used, just expressed directly on the
# 0-100 scale instead of as a 0-1 multiplier:
#   FFS's own structured Out list              -> 15
#   Not in FFS's predicted XI                   -> 45
#   In FFS's predicted XI, but a fitness doubt  -> 75
#   Clean, undoubted FFS predicted XI slot      -> 100
FFS_OUT_SCORE = 15.0
FFS_NOT_STARTING_SCORE = 45.0
FFS_DOUBTFUL_SCORE = 75.0
FFS_CLEAN_START_SCORE = 100.0


def ffs_subscore(ffs_start, ffs_doubt, is_out):
    """is_out: FFS's own structured Out list (see sync_player_ranks.py's
    ffs_out) -- a real curated call, not a guess."""
    if is_out:
        return FFS_OUT_SCORE
    if not ffs_start:
        return FFS_NOT_STARTING_SCORE
    if ffs_doubt:
        return FFS_DOUBTFUL_SCORE
    return FFS_CLEAN_START_SCORE


# rotowire.com sub-score -- derived the same way as the FFS one, off the
# club's own positional depth chart: rank 1 (first-choice at that slot) is
# the strongest signal a static depth chart can give, tapering off by rank,
# with RotoWire's own inline injury/suspension tags overriding the rank
# entirely when present (an OUT/SUS tag means the depth-chart rank is
# stale; a GTD tag means "picked, but a fitness call" -- mirrors FFS's own
# doubt tier exactly):
#   OUT or SUS tag                        -> 15  (mirrors FFS's Out tier)
#   GTD tag                                -> 75  (mirrors FFS's doubt tier)
#   Depth rank 1 (first-choice)            -> 100
#   Depth rank 2                           -> 60
#   Depth rank 3                           -> 35
#   Depth rank 4th-choice or lower         -> 20
#   Not on the club's depth chart at all   -> 45  (mirrors FFS's not-starting tier)
ROTO_OUT_TAGS = {"OUT", "SUS"}
ROTO_DOUBT_TAGS = {"GTD"}
ROTO_OUT_SCORE = 15.0
ROTO_DOUBT_SCORE = 75.0
ROTO_BY_DEPTH_RANK = {1: 100.0, 2: 60.0, 3: 35.0}
ROTO_DEPTH_RANK_DEFAULT_SCORE = 20.0
ROTO_UNLISTED_SCORE = 45.0


def roto_subscore(depth_rank, inj_tag):
    if inj_tag in ROTO_OUT_TAGS:
        return ROTO_OUT_SCORE
    if inj_tag in ROTO_DOUBT_TAGS:
        return ROTO_DOUBT_SCORE
    if depth_rank is None:
        return ROTO_UNLISTED_SCORE
    return ROTO_BY_DEPTH_RANK.get(depth_rank, ROTO_DEPTH_RANK_DEFAULT_SCORE)


def compute_rank(p):
    """p: one player's dict of already-resolved inputs -- fc26_overall,
    season_fpts, position_fpts_min/max, last_game_fpts,
    position_last_game_fpts_min/max, last_game_minutes, own_position,
    opponent_position, ffs_start, ffs_doubt, is_out, roto_depth_rank,
    roto_inj_tag (see compute_ranks/sync_megavision_rank.py for how these
    get resolved from real data). Returns the final 0-100 MEGAVISION Rank:
    a straight weighted sum of 8 independently-normalized 0-100 sub-scores.
    No bell curve, no gate -- every factor contributes exactly its stated
    percentage of the final number."""
    subscores = {
        "fc26": fc26_subscore(p["fc26_overall"]),
        "season_fpts": season_fpts_subscore(p["season_fpts"], p["position_fpts_min"], p["position_fpts_max"]),
        "last_game_fpts": last_game_fpts_subscore(
            p["last_game_fpts"], p["position_last_game_fpts_min"], p["position_last_game_fpts_max"]
        ),
        "last_game_minutes": last_game_minutes_subscore(p["last_game_minutes"]),
        "team_strength": team_strength_subscore(p["own_position"]),
        "opponent_weakness": opponent_weakness_subscore(p["opponent_position"]),
        "ffs": ffs_subscore(p["ffs_start"], p["ffs_doubt"], p["is_out"]),
        "roto": roto_subscore(p["roto_depth_rank"], p["roto_inj_tag"]),
    }
    total = sum(subscores[k] * RANK_WEIGHTS[k] for k in RANK_WEIGHTS)
    return round(max(1.0, min(100.0, total)), 1)


def compute_ranks(players):
    """players: list of dicts, each shaped per compute_rank(). Returns a
    parallel list of final 0-100 scores."""
    return [compute_rank(p) for p in players]


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


