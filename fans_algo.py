"""
The Fan Interest / ticket revenue algorithm -- rewritten 2026-09-03 to
match the real Rulez formula (section 2.2, Revenue Back From the Pool) as
directly as the data allows, replacing the original placeholder (a
weighted 0-100 "base score" blend that was this script's own invention,
never actually specified by the league). Two layers:

  1. REAL FAN COUNT (season-level, recomputed every GW) -- a literal sum,
     not a weighted score:
       - League Record standing fans (200/160/140/120/90/80/70/60/50/40/30/20
         for 1st-12th, by real win/loss/draw record)
       - Overall Scoring standing fans (100/80/70/60/50/45/40/35, top 8
         only, by cumulative season fantasy points -- a DIFFERENT ranking
         than League Record; a team can score a lot and still lose close
         matchups, or vice versa)
       - Top XI fans (30 each for the single top-scoring F/M/D that week,
         10 each for the other 8 Best-11 slots)
       - Legacy fans (title history -- see legacy_fan_value)
     This produces each team's actual fan count directly -- no arbitrary
     pool-share multiplier needed anymore (the old FANBASE_MULTIPLIER is
     gone; a team's fan count no longer depends on what anyone else's is).

  2. MATCHUP DAY (per-fixture, this week only): the two teams' real fan
     counts combine and get boosted for a big occasion (derby, title-race
     clash, bottom-team drama, upset buzz) before being capped at the host
     stadium's capacity. This layer is NOT in the documented rules --
     it's this project's own flavor addition from early on (derby
     rivalries, "go on a heater" momentum), kept because it doesn't touch
     the real fan-count math, only which week's game feels biggest. Says
     so plainly wherever it's displayed. Flagged to the commissioner as an
     open question: keep it, or strip it down to the literal ruleset?

Per-team legacy titles and Top XI results are DB-backed (best11, titles
tables) -- computed by the caller (sync_fans.py) and passed in here, same
separation as before.
"""

# ---- rivalries: all 6 pairs specified directly by the user ----
RIVALRIES = [
    frozenset({"HUF", "CRG"}),
    frozenset({"BHB", "DU"}),
    frozenset({"QFC", "FAV"}),
    frozenset({"TTS", "REN"}),
    frozenset({"WTF", "NAC"}),
    frozenset({"POW", "ASS"}),
]

RIVAL_OF = {}
for _pair in RIVALRIES:
    _a, _b = tuple(_pair)
    RIVAL_OF[_a] = _b
    RIVAL_OF[_b] = _a

# ---- real fan-count tables (Rulez 2.2) ----
LEAGUE_RECORD_FANS = [200, 160, 140, 120, 90, 80, 70, 60, 50, 40, 30, 20]  # 1st..12th
SCORING_STANDING_FANS = [100, 80, 70, 60, 50, 45, 40, 35]  # 1st..8th only, 9th-12th get 0
TOPXI_TOP_FANS = 30   # per top-scoring F, top-scoring M, top-scoring D that week
TOPXI_REST_FANS = 10  # per each of the other 8 Best-11 slots (GK + 2F + 3M + 2D)

# Legacy: title-history fans. The doc's exact wording is "10 fans per
# League or CL title in the last 3 years; 5 fans per Europa/FA Cup/Citadel
# Cup title in the last 3 years; 1 fan per Super Cup/Community Shield in
# the last 3 years. All-time: 5 fans per League/CL title ever, 2 fans per
# Europa/FA Cup/Citadel Cup title ever." Only one season (26/27) of title
# history exists right now, so every real title on record trivially
# qualifies as "last 3 years" -- the all-time tier can't yet produce a
# different number than the 3-year tier and isn't separately modeled.
# Revisit once multi-season title history exists.
LEGACY_FANS_3YR = {
    "Premium Title": 10, "Champions League": 10, "Europa League": 5,
    "Mega FA Cup": 5, "Citadel Cup": 5, "Mega Super Cup": 1, "Mega Community Shield": 1,
}

# ---- matchup-day bonuses (multiplicative, applied to this week's combined
# home+away fan count before the stadium cap) -- our own flavor layer, not
# in the documented rules, see module docstring ----
RIVALRY_BONUS = 0.35
TOP1V2_BONUS = 0.08
BOTTOM_TEAM_BONUS = 0.08
UPSET_BUZZ_BONUS = 0.12

# Mega's Community Shield/Super Cup (real-world EPL GW1, Juniors-vs-Juniors)
# is the only non-regular-season week, and it never gets a displayed GW
# number at all (see fantrax_live.REGULAR_SEASON_PERIODS) -- so nothing in
# the actual displayed schedule is exempt from salary/ticket pricing.
NON_REGULAR_SEASON_WEEKS = set()
REGULAR_SEASON_TICKET_PRICE = 0.04  # Rulez 2.2 -- was $0.05, wrong
HOME_GATE_SHARE = 0.80


def _pick_real_row_per_code(standings):
    """Which Sr/Jr row represents each code right now -- whichever has the
    higher fpts_for (real signal can currently sit on either roster)."""
    best = {}
    for row in standings:
        if not row["code"]:
            continue
        if row["code"] not in best or row["fpts_for"] > best[row["code"]]["fpts_for"]:
            best[row["code"]] = row
    return best


def league_record_rank_by_code(standings):
    """Real win/loss/draw record standing, 1-12 -- Fantrax's own rank
    field, re-ranked to 1-12 across whichever row represents each code."""
    rows = _pick_real_row_per_code(standings)
    ordered = sorted(rows, key=lambda c: rows[c]["rank"])
    return {code: i + 1 for i, code in enumerate(ordered)}


def scoring_rank_by_code(standings):
    """Overall cumulative fantasy-points standing, 1-12 -- a DIFFERENT
    ranking than league record (see module docstring)."""
    rows = _pick_real_row_per_code(standings)
    ordered = sorted(rows, key=lambda c: -rows[c]["fpts_for"])
    return {code: i + 1 for i, code in enumerate(ordered)}


# kept as an alias -- matchup_bonuses/RIVAL logic wants a competitive
# standings rank, which is League Record, not Scoring
rank_by_code_from_standings = league_record_rank_by_code


def legacy_fan_value(team_code, title_rows):
    """title_rows: iterable of (competition, team_code) for every title on
    record. Sums LEGACY_FANS_3YR for every title this team actually won --
    see the table's docstring for the all-time-tier caveat."""
    return sum(LEGACY_FANS_3YR.get(comp, 0) for comp, code in title_rows if code == team_code)


def team_fan_count(league_record_rank, scoring_rank, topxi_fans, legacy_fans):
    """The real per-team fan count -- league_record_rank/scoring_rank are
    1-12 (or None); topxi_fans/legacy_fans are pre-computed by the caller
    from best11/titles. Returns a breakdown dict, 'total' is this team's
    actual fan count (not a share of anything -- this IS the number)."""
    league_record_v = LEAGUE_RECORD_FANS[league_record_rank - 1] if league_record_rank and 1 <= league_record_rank <= 12 else 0
    scoring_v = SCORING_STANDING_FANS[scoring_rank - 1] if scoring_rank and 1 <= scoring_rank <= 8 else 0
    total = league_record_v + scoring_v + topxi_fans + legacy_fans
    return {
        "league_record": league_record_v, "scoring_standing": scoring_v,
        "topxi": round(topxi_fans, 1), "legacy": legacy_fans, "total": round(total, 1),
    }


def matchup_bonuses(home, away, standings_rank_by_code, upset_last_week=None):
    """Returns (multiplier, [reasons]) for this specific fixture. Flavor
    layer, not in the documented rules -- see module docstring."""
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
    """One game's attendance: combine home + away real fan counts, apply
    this week's matchup bonuses, cap at the host stadium's capacity.
    Overflow (interest beyond capacity) is discarded, not redistributed."""
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
