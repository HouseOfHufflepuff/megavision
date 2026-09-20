"""
Weekly roster manager for the subscribed teams: HUF, TTS, POW (Battersea
Power Bottoms / "BPB"), NAC.

For a given gameweek, decides whether the league is playing Sr (regular
season) or Jr (cup) rosters that week, then builds the best legal lineup
for each subscribed team's ACTIVE sub-team (Sr or Jr, whichever the week
calls for) using MEGAVISION Rank -- pulling in real held-rights unpromoted
youth as a candidate too, gated behind an escalating bar (YOUTH_ESCALATION_PCT,
currently 20% per real start already used -- 0 starts even, 1 start 20%
better, 2 starts 40%, etc., no hard cap) and Rulez 4.1(6)'s promotion trigger
at PROMOTION_TRIGGER_STARTS real starts (tracked in the youth_starts table --
see db.py; that table starts empty, so any youth already mid-count before
this tool existed will undercount until reconciled by hand).

Week-type detection: `week not in fans_algo.NON_REGULAR_SEASON_WEEKS` ==
Sr. That set is currently EMPTY in this codebase (a pre-existing gap this
script inherits rather than silently patches over) -- so every week reads
as Sr right now. If a real cup week needs Jr rosters, populate that set
first (fans_algo.py) rather than hacking around it here.

"Best lineup" means: for each position, keep the number of slots the
active roster currently has at that position, and fill them with the
highest MEGAVISION-Rank-scored eligible players drawn from BOTH this
team's Sr and Jr rosters combined, plus any real held-rights unpromoted
youth (Youth sheet, Active status, 23-or-younger at 8/1, currently on an
EPL roster) not already on either. This assumes the CURRENT position
counts are already a legal shape -- it optimizes who fills the shape, not
the shape itself.

Modes:
    python3 roster_manager.py [week]                    read-only QA report (default)
    python3 roster_manager.py [week] --write             execute the moves on Fantrax for real
    python3 roster_manager.py [week] --write --email      also email each team what changed and why

`week` defaults to the next real-world-unplayed gameweek in the Fantrax
schedule.
"""
import json
import re
import sys
import unicodedata
from datetime import date, datetime, timezone

import common
import fantrax_live as fl
import fans_algo as fa
import rank_algo
import sync_fantrax_keepers as sfk
import sync_fpl_stats as fpl
from db import connect

now = datetime.now(timezone.utc).isoformat()

SUBSCRIBED_DEFAULT = ["HUF", "TTS", "POW", "NAC"]  # fallback only -- fetch_managed_teams() is the real source of truth (managed_teams table)
TEAM_FULL_NAME = {
    "FAV": "5th Ave Argyle", "POW": "Battersea Power Bottoms", "CRG": "CRG McGovern",
    "DU": "Divided United", "HUF": "House of Hufflepuff", "NAC": "NFC Andover City",
    "QFC": "Quidpool FC", "REN": "Real News", "BHB": "The Bookhouse Boys",
    "TTS": "Thottenham Thotspur", "WTF": "What The FC", "ASS": "Wholeassed United FC",
}
TEAM_OWNER_EMAILS = {
    "FAV": ["jweathermanjr@gmail.com"],
    "POW": ["samrufer@gmail.com", "jeffertz@gmail.com"],
    "CRG": ["caseymcgovern@gmail.com"],
    "DU": ["chrisgauron@gmail.com"],
    "HUF": ["ahrens@gmail.com"],
    "NAC": ["tuffer11@gmail.com"],
    "QFC": ["erikjohnsonmn@gmail.com"],
    "REN": ["reidfoster80@gmail.com"],
    "BHB": ["molaughlin@gmail.com"],
    "TTS": ["kolaughlin@gmail.com"],
    "WTF": ["erikaeolson@gmail.com"],
    "ASS": ["kirkwalton@gmail.com", "dan.hinrichs@gmail.com"],
}
ALL_TEAMS = list(TEAM_FULL_NAME.keys())


def fetch_managed_teams(conn=None):
    """Team codes opted into automated roster management, from the
    managed_teams DB table -- the real source of truth (replaced the old
    hardcoded SUBSCRIBED list 2026-09-17). Falls back to
    SUBSCRIBED_DEFAULT if the table is empty (shouldn't happen once
    seeded, but a script relying on this shouldn't silently manage zero
    teams because of a migration gap)."""
    own_conn = conn is None
    if own_conn:
        conn = connect()
    rows = [r[0] for r in conn.execute("SELECT team_code FROM managed_teams ORDER BY team_code").fetchall()]
    if own_conn:
        conn.close()
    return rows or list(SUBSCRIBED_DEFAULT)

YOUTH_CUTOFF = date(2026, 8, 1)  # Rulez: 23 or younger at Aug 1 to be a selectable Youth Player

# Escalating-bar youth rule, replacing the old flat 25%-better gate AND the
# old hard 4-start cap (per Jer 2026-09-17): a youth must beat the weakest
# alternative by (their own current start count * 20%) to start again --
# 0 starts even, 1 start 20% better, 2 starts 40%, 3 starts 60%, 4 starts
# 80%. No hard stop; the bar just keeps climbing. Applies to EVERY week's
# decision, continuing starters included, not just brand-new candidates.
YOUTH_ESCALATION_PCT = 0.20

# A youth who reaches this many real starts is flagged for a mandatory
# promotion decision -- not a hard block (the escalating bar above already
# makes a 5th+ start steadily harder on its own), just a loud notice the
# owner needs to see and act on.
PROMOTION_TRIGGER_STARTS = 5

# Cross-position comparison floor (per Jer 2026-09-18): a youth-eligible D
# can now clear the escalating bar against the weakest established player
# at M or F too, not just fellow D's -- "like for like" was more
# restrictive than the Rulez require. The only constraint is that D, M,
# and F each keep at least this many active players after any such swap.
MIN_ACTIVE_PER_OUTFIELD_POS = 3


CLUB_ALIASES = {
    "arsenal": "ARS", "aston villa": "AVL", "bournemouth": "BOU", "brentford": "BRE",
    "brighton": "BHA", "chelsea": "CHE", "coventry city": "COV", "coventry": "COV",
    "crystal palace": "CRY", "everton": "EVE", "fulham": "FUL", "hull city": "HUL",
    "hull": "HUL", "ipswich": "IPS", "ipswich town": "IPS", "leeds": "LEE",
    "leeds united": "LEE", "liverpool": "LIV", "man city": "MCI", "manchester city": "MCI",
    "man united": "MUN", "man utd": "MUN", "manchester united": "MUN", "newcastle": "NEW",
    "nottingham": "NFO", "nottingham forest": "NFO", "nott'm forest": "NFO",
    "tottenham": "TOT", "spurs": "TOT", "sunderland": "SUN",
}


def _fold(s):
    return unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode("ascii").lower().strip()


def clean_name(name):
    n = re.sub(r"\([^)]*\)", "", name)
    n = re.sub(r'["“][^"”]*["”]', "", n)
    return re.sub(r"\s+", " ", n).strip()


def normalize_club(raw):
    return CLUB_ALIASES.get(raw.strip().lower()) if raw else None


def age_on_cutoff(bd):
    y, m, d = (int(x) for x in bd.split("-"))
    born = date(y, m, d)
    return YOUTH_CUTOFF.year - born.year - ((YOUTH_CUTOFF.month, YOUTH_CUTOFF.day) < (born.month, born.day))


def candidates_for(lookup, last_name):
    cands = lookup.get(fpl._fold(last_name)) or []
    seen = {}
    for c in cands:
        seen[c["id"]] = c
    return list(seen.values())


def confident_match(cands, first_name):
    exact = [c for c in cands if fpl._fold(c["first_name"]) == fpl._fold(first_name)]
    return exact[0] if len(exact) == 1 else None


def is_sr_week(week):
    return week not in fa.NON_REGULAR_SEASON_WEEKS


def _week_is_played(sess, w):
    """A week's Gameweek table exists in Fantrax's schedule data before
    it's actually played -- pre-populated with every score at a flat 0.0
    placeholder -- so "played" can only mean at least one real, nonzero
    score shows up in it, never just "the table exists." Real bug caught
    2026-09-11: checking only "does fetch_gameweek_scores return anything"
    treated that placeholder table as a finished week, skipping straight
    to the week after the real current one."""
    games = fl.fetch_gameweek_scores(sess, w)
    return bool(games) and any(g["home_score"] or g["away_score"] for g in games)


def target_week(explicit, sess):
    """Next week after the last one with real, confirmed results.
    Deliberately NOT "the first week with no table at all" -- Fantrax's
    getStandings only keeps a rolling window of past Gameweek tables, so
    an old, already-played week can come back completely empty once
    enough weeks have passed (caught 2026-09-11: GW2 had real scores
    early this season but returned 0 games once GW3-5 existed, which
    would have made target_week wrongly report week 2 as still
    unplayed). Scanning for the highest played week and adding 1 sidesteps
    that ambiguity -- it only ever reads "has this appeared with a real
    score," never "is this table present at all.\""""
    if explicit:
        return explicit
    games_by_week = {}
    for g in fl.fetch_schedule(sess):
        games_by_week.setdefault(g["week"], []).append(g)
    last_played = max((w for w in games_by_week if _week_is_played(sess, w)), default=min(games_by_week) - 1)
    return last_played + 1


def fetch_rank(conn, name, week):
    row = conn.execute(
        "SELECT g.megavision_rank, g.start_likelihood, g.ffs_start, g.ffs_doubt, g.injury_status "
        "FROM epl_players p JOIN player_gameweek g "
        "ON g.player_name=p.player_name AND g.real_club=p.real_club "
        "WHERE p.player_name=? AND g.gameweek=?", (name, week),
    ).fetchone()
    if not row:
        return None, None, None
    rank, likelihood, ffs_start, ffs_doubt, injury = row
    tag = "OUT" if injury and "out" in injury.lower() else ("DOUBT" if ffs_doubt else ("START" if ffs_start else "BENCH"))
    return rank, likelihood, tag


def fetch_prev_rank(conn, name, week):
    """Last gameweek's MEGAVISION Rank for this player, or None if it
    wasn't recorded. Caller subtracts from the current rank to get the
    +/- (see build_rank.py's identical +/- Last Wk column) -- kept as a
    separate lookup rather than doing the subtraction here since callers
    already have the current rank in hand and it avoids a second query."""
    row = conn.execute(
        "SELECT g.megavision_rank FROM epl_players p JOIN player_gameweek g "
        "ON g.player_name=p.player_name AND g.real_club=p.real_club "
        "WHERE p.player_name=? AND g.gameweek=?", (name, week - 1),
    ).fetchone()
    return row[0] if row else None


def get_opponent(sess, code, week):
    """(opponent_code, is_home) for this team's real fixture this week, or
    (None, None) if no game found (a bye or a cup-bracket week)."""
    for g in fl.fetch_schedule(sess):
        if g["week"] != week:
            continue
        if g["home"] == code:
            return g["away"], True
        if g["away"] == code:
            return g["home"], False
    return None, None


def predicted_score(roster):
    """Sum of the best-XI (league's real GK+3D+4M+3F shape) by each
    player's own real fpts-to-date -- same methodology as
    matchday_email.py's team_predicted_score, reimplemented here to avoid
    a cross-import (matchday_email.py isn't built to be imported, it's a
    standalone report script). Not a betting line -- each team's own top
    scorers so far, the closest same-shape estimate we have real data for."""
    formation = {"GK": 1, "D": 3, "M": 4, "F": 3}
    total = 0.0
    for pos, slots in formation.items():
        candidates = sorted((p for p in roster if p["pos"] == pos), key=lambda p: -(p.get("fpts") or 0))
        total += sum(p.get("fpts") or 0 for p in candidates[:slots])
    return round(total, 1)


def fetch_categories(conn, code):
    return dict(conn.execute(
        "SELECT player_name, category FROM team_player_wages WHERE team_code=? AND season='26/27'", (code,)
    ).fetchall())


def fetch_age(conn, name, lookup=None):
    """Real age on the Rulez Aug-1 youth cutoff -- NOT epl_players.age, which
    is FC26's own age field (as of FC26's roster-freeze date, a totally
    different reference point). Found 2026-09-17: this silently misclassified
    Georginio Rutter (born 2002-04-20, real cutoff age 24) as a 23-or-under
    youth candidate because FC26 still had him at 23. Computed live from
    FPL's real birth_date via age_on_cutoff() whenever a confident name match
    is available; falls back to the stale DB column only when it isn't."""
    if lookup is not None:
        clean = clean_name(name)
        parts = clean.split()
        if parts:
            cands = candidates_for(lookup, parts[-1])
            el = confident_match(cands, parts[0]) if cands else None
            if el and el.get("birth_date"):
                return age_on_cutoff(el["birth_date"])
    row = conn.execute("SELECT age FROM epl_players WHERE player_name=?", (name,)).fetchone()
    return row[0] if row and row[0] is not None else None


# A player counts as "youth" for the 25%-better gate if they're 23 or
# younger AND don't already have a real multi-year/committed contract on
# this team -- age alone isn't enough (Tzolis and Elliott are both 23/22
# but already promoted with real 3-year deals; that decision's made, this
# gate is about NOT yet spending a start on someone unproven). Broadened
# 2026-09-11 per Jer: this was previously only checking the narrow Rulez
# "held rights, never rostered" case and missed Bergvall/Tel/Kostoulas --
# all young single-year "drafted" picks already sitting on the Jr roster,
# which is exactly the kind of unproven player this gate exists for.
COMMITTED_CATEGORIES = {"kept", "youth_players", "youth_legend", "irp"}


def is_youth(age, category):
    return age is not None and age <= 23 and category not in COMMITTED_CATEGORIES


def fetch_youth_override(conn, code, name):
    """Explicit owner correction of Youth Player status, checked before the
    age/category heuristic -- see db.py's youth_status_overrides for why
    this exists (Christos Tzolis: real age 24, committed 3-year contract
    per team_player_wages, but the owner says he's a Youth Player anyway).
    Returns True/False if an override exists, None otherwise."""
    row = conn.execute(
        "SELECT is_youth FROM youth_status_overrides WHERE team_code=? AND player_name=?", (code, name)
    ).fetchone()
    return bool(row[0]) if row else None


def is_youth_for(conn, code, name, age, category):
    override = fetch_youth_override(conn, code, name)
    return override if override is not None else is_youth(age, category)


def fetch_start_count(conn, code, name):
    return conn.execute(
        "SELECT COUNT(*) FROM youth_starts WHERE team_code=? AND player_name=?", (code, name)
    ).fetchone()[0]


def fetch_youth_candidates(conn, youth_by_code, elements, lookup, code, week, existing_names):
    """Real held-rights unpromoted youth for this team: Active on the Youth
    sheet, 23-or-younger at 8/1, currently on an EPL roster (live FPL
    cross-match, not the sheet's own possibly-stale club field), not
    already on either the Sr or Jr roster."""
    out = []
    for r in youth_by_code.get(code, []):
        if r["status"] != "Active":
            continue
        clean = clean_name(r["player"])
        if clean in existing_names:
            continue
        parts = clean.split()
        if not parts:
            continue
        last, first = parts[-1], parts[0]
        cands = candidates_for(lookup, last)
        if not cands:
            continue
        el = confident_match(cands, first)
        if el is None or not el.get("birth_date"):
            continue
        age = age_on_cutoff(el["birth_date"])
        if age > 23:
            continue
        pos = (r["pos"] or "").strip()
        if pos not in ("GK", "D", "M", "F"):
            continue
        full_name = f'{el["first_name"]} {el["second_name"]}'
        rank, likelihood, tag = fetch_rank(conn, full_name, week)
        out.append({
            "name": full_name, "sheet_name": r["player"],
            "pos": pos, "club": el.get("club_short"), "age": age, "rank": rank,
            "likelihood": likelihood, "tag": tag,
            "starts": fetch_start_count(conn, code, full_name),
        })
    return out


def _flag_promotion(notes, pos, yc, new_start_count):
    if new_start_count >= PROMOTION_TRIGGER_STARTS:
        notes.append(
            f'  {pos}: *** {yc["name"]} reaches {new_start_count} real starts this week -- PROMOTED. '
            f'Owner decision needed: give him a real contract, or drop him. ***'
        )


def _fill_position_group(pool_by_pos, slots_needed, positions, min_per_pos=None):
    """Fill `positions` (["GK"], or ["D","M","F"] together) applying the
    escalating youth-start bar. When min_per_pos is set, a youth-eligible
    player at one position in the group can displace the globally weakest
    established player at ANY position in the group -- not just their own
    -- as long as that position keeps at least min_per_pos players
    afterward. Without min_per_pos (e.g. GK, a group of one), comparison
    stays strictly within the position, same as before. Returns
    (picked_by_pos, notes)."""
    picked_by_pos = {}
    for pos in positions:
        pool = pool_by_pos.get(pos, [])
        established = sorted(
            (p for p in pool if not p["is_youth_eligible"]),
            key=lambda p: p["rank"] if p["rank"] is not None else -1, reverse=True,
        )
        picked_by_pos[pos] = established[:slots_needed.get(pos, 0)]

    youth_pool = sorted(
        (p for pos in positions for p in pool_by_pos.get(pos, []) if p["is_youth_eligible"]),
        key=lambda p: p["rank"] if p["rank"] is not None else -1, reverse=True,
    )

    notes = []
    for yc in youth_pool:
        pos = yc["pos"]
        if yc["rank"] is None:
            notes.append(f'  {pos}: skip {yc["name"]} (held youth rights) -- no MEGAVISION Rank data available')
            continue
        starts = yc.get("starts", 0)
        required_pct = starts * YOUTH_ESCALATION_PCT

        # Room for another slot outright at their own position -- fill it
        # directly, no swap needed (e.g. GK's fixed 2-slot rule with one
        # of the two goalkeepers being youth-eligible, or a position that
        # doesn't have enough established players to fill its own count).
        if len(picked_by_pos[pos]) < slots_needed.get(pos, 0):
            picked_by_pos[pos].append(yc)
            notes.append(f'  {pos}: {yc["name"]} added -- open slot, no alternative to compare against')
            _flag_promotion(notes, pos, yc, starts + 1)
            continue

        if min_per_pos is not None:
            # Cross-position pool: every currently-picked player across the
            # whole group, EXCLUDING anyone whose own position is already
            # at the floor (displacing them would break the min-per-position
            # rule for that position).
            candidates = [p for p2 in positions if len(picked_by_pos[p2]) > min_per_pos for p in picked_by_pos[p2]]
        else:
            candidates = picked_by_pos[pos]

        if not candidates:
            notes.append(
                f'  {pos}: skip {yc["name"]} -- no eligible alternative to displace without dropping a '
                f'position below {min_per_pos}'
            )
            continue

        weakest = min(candidates, key=lambda p: p["rank"] if p["rank"] is not None else -1)
        weakest_rank = weakest["rank"] if weakest["rank"] is not None else 0
        bar = weakest_rank * (1.0 + required_pct)
        if yc["rank"] >= bar and yc["rank"] > weakest_rank:
            picked_by_pos[weakest["pos"]].remove(weakest)
            picked_by_pos[pos].append(yc)
            cross_note = f' (a {weakest["pos"]})' if weakest["pos"] != pos else ""
            notes.append(
                f'  {pos}: {yc["name"]} ({yc["rank"]:.1f}, {starts} prior starts) clears the {required_pct:.0%} bar over '
                f'{weakest["name"]}{cross_note} ({weakest_rank:.1f}, bar was {bar:.1f}) -- start {starts + 1}'
            )
            _flag_promotion(notes, pos, yc, starts + 1)
        else:
            yc_rank_display = f'{yc["rank"]:.1f}' if yc["rank"] is not None else "0.0"
            notes.append(
                f'  {pos}: {yc["name"]} ({yc_rank_display}, {starts} prior starts) does NOT clear the '
                f'{required_pct:.0%} bar over {weakest["name"]} ({weakest_rank:.1f}, needed {bar:.1f}) -- stays off'
            )
    return picked_by_pos, notes


def build_plan(conn, sess, youth_by_code, elements, lookup, code, week, sr):
    sr_id, jr_id = fl.FANTRAX_TEAM_ID[code], fl.JUNIOR_TEAM_ID[code]
    active_id = sr_id if sr else jr_id
    other_id = jr_id if sr else sr_id

    active_roster = fl.fetch_full_roster(sess, active_id)
    other_roster = fl.fetch_full_roster(sess, other_id)
    categories = fetch_categories(conn, code)

    existing_names = {p["name"] for p in active_roster} | {p["name"] for p in other_roster}
    youth_candidates = fetch_youth_candidates(conn, youth_by_code, elements, lookup, code, week, existing_names)

    pool_by_pos = {"GK": [], "D": [], "M": [], "F": []}
    for p in active_roster + other_roster:
        rank, likelihood, tag = fetch_rank(conn, p["name"], week)
        age = fetch_age(conn, p["name"], lookup)
        category = categories.get(p["name"], "?")
        youth_eligible = is_youth_for(conn, code, p["name"], age, category)
        on_active = p in active_roster
        pool_by_pos.setdefault(p["pos"], []).append({
            "name": p["name"], "pos": p["pos"], "rank": rank, "likelihood": likelihood, "tag": tag,
            "category": category, "scorerId": p["scorerId"], "age": age,
            "on_active": on_active, "source": "active" if on_active else "other",
            # is_youth_candidate: subject to the 25%-better gate -- only
            # meaningful for a NEW selection decision, so it's False once
            # already active (that call's already been made). is_youth_eligible
            # stays True regardless of active status -- used for the 4-start
            # cap and the full youth-status listing, which both need to see
            # an already-active youth too, not just new candidates.
            "is_youth_candidate": youth_eligible and not on_active,
            "is_youth_eligible": youth_eligible,
            "starts": fetch_start_count(conn, code, p["name"]) if youth_eligible else 0,
        })
    for c in youth_candidates:
        pool_by_pos.setdefault(c["pos"], []).append({
            "name": c["name"], "pos": c["pos"], "rank": c["rank"], "likelihood": c["likelihood"], "tag": c["tag"],
            "category": "unpromoted_youth",
            "scorerId": None, "on_active": False, "source": "held_rights",
            "is_youth_candidate": True, "is_youth_eligible": True,
            "starts": c["starts"], "club": c["club"], "age": c["age"],
        })

    # Both goalkeepers always ride together on whichever team (Sr/Jr) is
    # active this week -- there's no competitive GK slot in this league,
    # Rulez auto-uses whichever of the two scored higher. Every other
    # position keeps the active roster's current slot count.
    slots_needed = {"GK": 2}
    for p in active_roster:
        if p["pos"] != "GK":
            slots_needed[p["pos"]] = slots_needed.get(p["pos"], 0) + 1

    plan = {}
    notes = []
    # GK stays its own isolated group -- no cross-position comparison (per
    # Jer 2026-09-18: D/M/F can compare across each other, GK wasn't
    # mentioned and has its own "both always ride together" rule anyway).
    gk_plan, gk_notes = _fill_position_group(pool_by_pos, slots_needed, ["GK"])
    plan.update(gk_plan)
    notes.extend(gk_notes)

    # D/M/F share one combined comparison pool (per Jer 2026-09-18): a
    # youth-eligible D can now clear the escalating bar against the
    # weakest established player at ANY of D/M/F, not just fellow
    # defenders, as long as that position keeps at least
    # MIN_ACTIVE_PER_OUTFIELD_POS players afterward. Previously every
    # position was scored strictly "like for like" (a D only ever
    # competed against other D's), which was more restrictive than the
    # Rulez actually require.
    dmf_plan, dmf_notes = _fill_position_group(
        pool_by_pos, slots_needed, ["D", "M", "F"], min_per_pos=MIN_ACTIVE_PER_OUTFIELD_POS
    )
    plan.update(dmf_plan)
    notes.extend(dmf_notes)

    return {
        "code": code, "week": week, "sr": sr, "active_id": active_id, "other_id": other_id,
        "active_roster": active_roster, "other_roster": other_roster, "plan": plan, "notes": notes,
        "pool_by_pos": pool_by_pos,
    }


def diff_moves(result):
    """[{action: 'keep'|'add'|'drop', name, pos, from}] describing what has
    to change on Fantrax to go from the current active roster to the plan."""
    active_names = {p["name"] for p in result["active_roster"]}
    other_by_name = {p["name"]: p for p in result["other_roster"]}
    plan_names = {p["name"] for players in result["plan"].values() for p in players}

    moves = []
    for pos, players in result["plan"].items():
        for p in players:
            if p["name"] in active_names:
                moves.append({"action": "keep", "name": p["name"], "pos": pos})
            elif p["name"] in other_by_name:
                moves.append({"action": "add", "name": p["name"], "pos": pos, "from": "other roster (Sr/Jr swap)"})
            else:
                moves.append({"action": "add", "name": p["name"], "pos": pos, "from": "held youth rights (new pickup)"})
    for p in result["active_roster"]:
        if p["name"] not in plan_names:
            moves.append({"action": "drop", "name": p["name"], "pos": p["pos"]})
    return moves


def render_report(result, moves, detailed=False):
    code, week, sr = result["code"], result["week"], result["sr"]
    lines = [f'=== {TEAM_FULL_NAME.get(code, code)} ({code}) -- GW{week}, {"Sr" if sr else "Jr"} week ===']
    adds = [m for m in moves if m["action"] == "add"]
    drops = [m for m in moves if m["action"] == "drop"]

    if detailed:
        picked_names = {p["name"] for players in result["plan"].values() for p in players}
        for pos in ("GK", "D", "M", "F"):
            pool = result["pool_by_pos"].get(pos, [])
            if not pool:
                continue
            lines.append(f"  --- {pos} ---")
            ordered = sorted(pool, key=lambda p: p["rank"] if p["rank"] is not None else -1, reverse=True)
            for p in ordered:
                rank_s = f'{p["rank"]:.1f}' if p["rank"] is not None else "  no data"
                like_s = f'{p["likelihood"]:.1f}%' if p.get("likelihood") is not None else "n/a"
                tag = p.get("tag") or ""
                pick_mark = "PICKED" if p["name"] in picked_names else "      "
                cat = p.get("category", "")
                age_s = f'age {p["age"]}' if p.get("age") is not None else "age ?"
                youth_s = " [YOUTH]" if p["is_youth_eligible"] else ""
                starts_s = f'  ({p["starts"]} starts)' if p["is_youth_eligible"] else ""
                lines.append(
                    f'    [{pick_mark}] {p["name"]:26s} rank={rank_s:>7s}  likelihood={like_s:>6s}  {tag:5s}  '
                    f'{p["source"]:11s} {cat:16s} {age_s}{youth_s}{starts_s}'
                )

    lines.append("  -- moves --")
    if not adds and not drops:
        lines.append("  No changes -- current active roster is already the best legal lineup available.")
    for m in adds:
        lines.append(f'  ADD  {m["name"]} ({m["pos"]}) <- {m["from"]}')
    for m in drops:
        lines.append(f'  DROP {m["name"]} ({m["pos"]})')
    if result["notes"]:
        lines.append("  -- youth-gate detail --")
        lines.extend(result["notes"])
    return "\n".join(lines)


def commissioner_trade(sess, team_a, team_b, out_scorer_id, in_scorer_id, week):
    """A commissioner-mode Sr<->Jr swap that takes effect for the CURRENT
    period immediately -- unlike createClaimDropCommissioner (do_drop/
    do_claim below), which Fantrax always defers to the NEXT period no
    matter what params are sent (confirmed 2026-09-11 via repeated direct
    testing: explicit period overrides, admin mode, fresh untouched
    players -- all deferred). The real mechanism, reverse-engineered
    2026-09-11 from Fantrax's own legacy trade.go page source (not the
    documented /fxpa/req API): POST JSON to /fxa/createTrade with a
    'transactions' map of "SC,{scorerId},{fromTeamId},{toTeamId},{sortKey}"
    strings, a txDateTime string ('YYYY-MM-DD HH:MM:SS', any moment inside
    the current period), and period as a plain string. Verified live:
    executes immediately against the current, already-started roster
    period -- not queued for next period like drop/claim."""
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    params = {
        "transactions": {
            "1": f"SC,{out_scorer_id},{team_a},{team_b},0",
            "2": f"SC,{in_scorer_id},{team_b},{team_a},1",
        },
        "txDateTime": now_str,
        "period": str(week),
        "adminMode": True, "future": True, "override": False, "msg": "",
        "fantasyTeamId": team_a,
    }
    resp = sess.post("https://www.fantrax.com/fxa/createTrade", params={"leagueId": fl.LEAGUE_ID},
                      data=json.dumps(params), headers={"Content-Type": "application/json"}, timeout=20)
    d = resp.json()
    code = d.get("code") or d.get("exception", {}).get("code") or "ERROR"
    msg = d.get("genericMessage") or d.get("exception", {}).get("message")
    return code == "EXECUTED", msg


def apply_moves(sess, result, moves):
    """Pairs each drop with an "other roster" add as a commissioner_trade
    (immediate, current-period effect). A brand-new held-youth-rights
    pickup has no scorerId on either of this team's own rosters (never
    been on any Mega roster at all), so it can't be paired into a trade --
    that case still needs a live free-agent claim, which Fantrax DOES
    defer to next period (no trade counterpart exists to swap against);
    logged as a clear limitation rather than guessed at."""
    active_id, other_id = result["active_id"], result["other_id"]
    other_by_scorer = {p["name"]: p["scorerId"] for p in result["other_roster"]}
    active_by_scorer = {p["name"]: p["scorerId"] for p in result["active_roster"]}
    log = []

    drops = [m for m in moves if m["action"] == "drop"]
    adds_from_other = [m for m in moves if m["action"] == "add" and m["from"].startswith("other roster")]
    adds_new = [m for m in moves if m["action"] == "add" and not m["from"].startswith("other roster")]

    for drop_m, add_m in zip(drops, adds_from_other):
        out_sid = active_by_scorer.get(drop_m["name"])
        in_sid = other_by_scorer.get(add_m["name"])
        if not out_sid or not in_sid:
            log.append(("trade", result["code"], f'{drop_m["name"]} <-> {add_m["name"]}', False, "missing scorerId"))
            continue
        ok, msg = commissioner_trade(sess, active_id, other_id, out_sid, in_sid, result["week"])
        log.append(("trade", result["code"], f'{drop_m["name"]} <-> {add_m["name"]}', ok, msg))

    leftover_drops = drops[len(adds_from_other):]
    for drop_m in leftover_drops:
        sid = active_by_scorer.get(drop_m["name"])
        ok, err = sfk.do_drop(sess, active_id, sid) if sid else (False, "no scorerId")
        log.append(("drop", result["code"], drop_m["name"], ok, err))

    for add_m in adds_new:
        log.append(("claim", result["code"], add_m["name"], False,
                     "no scorerId -- new held-youth-rights pickup needs a live free-agent claim, "
                     "which Fantrax defers to next period (no trade path exists for it)"))
    return log


def render_rosters(result, conn):
    code = result["code"]
    lines = [f'=== {TEAM_FULL_NAME.get(code, code)} ({code}) -- current live Fantrax rosters ===']
    for label, roster in (("Sr", result["active_roster"] if result["sr"] else result["other_roster"]),
                            ("Jr", result["other_roster"] if result["sr"] else result["active_roster"])):
        lines.append(f'  --- {label} roster ({len(roster)} players) ---')
        by_pos = {}
        for p in roster:
            by_pos.setdefault(p["pos"], []).append(p)
        for pos in ("GK", "D", "M", "F"):
            for p in sorted(by_pos.get(pos, []), key=lambda x: x["name"]):
                rank, likelihood, tag = fetch_rank(conn, p["name"], result["week"])
                age = fetch_age(conn, p["name"])
                rank_s = f'{rank:.1f}' if rank is not None else "no data"
                lines.append(f'    {pos:3s} {p["name"]:26s} age {age if age is not None else "?":<4} rank={rank_s:>7s}  {tag or ""}')
    return "\n".join(lines)


def score_sheet(result, conn, executed=True):
    """Final Sr lineup and Jr roster (after this week's plan), each row:
    rank, +/- vs last week, start likelihood. This is the exact table
    format shown for QA -- also embedded in the team email so owners see
    the same numbers. Headers say "PROPOSED ..." for a read-only,
    not-yet-executed report and just "... LINEUP/ROSTER" once it's
    actually been run for real (executed=True, the default -- matches
    build_email_body's own default)."""
    sr_picks = [p for players in result["plan"].values() for p in players]
    sr_names = {p["name"] for p in sr_picks}
    combined = result["active_roster"] + result["other_roster"]
    jr_players = [p for p in combined if p["name"] not in sr_names]

    def rows_for(players_with_rank):
        out = []
        for pos in ("GK", "D", "M", "F"):
            for p in sorted([x for x in players_with_rank if x["pos"] == pos], key=lambda x: -(x["rank"] or -1)):
                out.append(p)
        return out

    def render(title, players):
        lines = [title, f'{"Pos":4s}{"Player":27s}{"Rank":>7s}{"+/-":>8s}{"Start%":>8s}']
        for p in players:
            rank_s = f'{p["rank"]:.1f}' if p.get("rank") is not None else "no data"
            delta = p.get("delta")
            delta_s = f'{delta:+.1f}' if delta is not None else "n/a"
            like_s = f'{p["likelihood"]:.1f}%' if p.get("likelihood") is not None else "n/a"
            lines.append(f'{p["pos"]:4s}{p["name"]:27s}{rank_s:>7s}{delta_s:>8s}{like_s:>8s}')
        return "\n".join(lines)

    sr_rows = rows_for(sr_picks)  # already carry rank/likelihood from build_plan's pool entries
    for p in sr_rows:
        prev = fetch_prev_rank(conn, p["name"], result["week"])
        p["delta"] = (p["rank"] - prev) if (p["rank"] is not None and prev is not None) else None

    jr_rows = []
    for p in jr_players:
        rank, likelihood, _tag = fetch_rank(conn, p["name"], result["week"])
        prev = fetch_prev_rank(conn, p["name"], result["week"])
        delta = (rank - prev) if (rank is not None and prev is not None) else None
        jr_rows.append({"name": p["name"], "pos": p["pos"], "rank": rank, "likelihood": likelihood, "delta": delta})
    jr_rows = rows_for(jr_rows)

    prefix = "" if executed else "PROPOSED "
    return (
        render(f'{prefix}SR LINEUP ({"Sr" if result["sr"] else "Jr"} week)', sr_rows)
        + "\n\n" + render(f"{prefix}JR (YOUTH) ROSTER", jr_rows)
    )


METHODOLOGY = """\
=== How MEGAVISION Rank is calculated (rank_algo.py) ===

1. RAW COMPOSITE = FC26 overall rating, plus three small context bonuses:
     + team strength:   (this club's avg FC26 overall - league avg) * 0.4
     + matchup:         (league avg FC26 - this week's opponent avg FC26) * 0.5
                         + 3.0 if home, - 3.0 if away
     + current form:    (this player's score so far - position average) * 0.5
   Each bonus is small relative to overall (talent stays the dominant signal).

2. BELL CURVE -- the raw composite is standardized (z-score) across every
   player in the pool that gameweek, then mapped onto 0-100 centered at 50.
   Most players cluster in the middle; the 90s require being several
   standard deviations above the field, not just "a good number."

3. START-CERTAINTY GATE -- multiplies the bell-curve score:
     x1.00 if fantasyfootballscout.co.uk has them a clean, undoubted starter
     x0.75 if they're starting but FFS has a fitness doubt
     x0.45 if FFS doesn't have them starting at all
     x0.15 if they're outright ruled out
   This is why a nailed-on average player can outrank a star with any
   doubt attached -- start certainty is a hard gate, not just a nudge.

START LIKELIHOOD is a separate number (not part of Rank): within each real
club's own position group, an exponential weighting of FC26 overall,
multiplied x5 for a clean FFS start, x2.5 for a doubtful start, x1 for
bench, x0.1 for out -- then normalized to sum to 100% across that position
group at that one real club. It estimates "will they actually play," not
"how good are they if they do."

YOUTH GATE (roster_manager.py, not rank_algo's own score) -- separate from
the two above: a player 23-or-younger without a real multi-year contract
can only be newly added to the active lineup if their Rank clears 25%
above the weakest player they'd replace, and stops being eligible after 4
tracked starts until promoted.
"""


FUN_OPENERS = {
    "many": "MegaBot's been in the lab all night. Buckle up, there's a lot happening:",
    "some": "A couple of moving parts this week -- here's the case for each:",
    "none": "Quiet week on the transaction front -- sometimes the best move is no move:",
}


def _pool_lookup(result):
    """name -> pool entry, across every position bucket -- for pulling a
    rank/likelihood/starts number back up when rendering a move line."""
    out = {}
    for players in result["pool_by_pos"].values():
        for p in players:
            out[p["name"]] = p
    return out


def move_rationale_line(m, pool_by_name):
    """One IN/OUT line with the real rank behind it, not just a bare name --
    the whole point of "why are we making this move" is the number, not
    the vibes."""
    p = pool_by_name.get(m["name"], {})
    rank = p.get("rank")
    rank_s = f'{rank:.1f}' if rank is not None else "no data"
    tag = p.get("tag") or ""
    if m["action"] == "add":
        arrow = "IN "
        src = m["from"]
        return f'  {arrow} {m["name"]:24s} ({m["pos"]})  rank {rank_s:>6s}  {tag:6s}  -- {src}'
    else:
        return f'  OUT {m["name"]:24s} ({m["pos"]})  rank {rank_s:>6s}  {tag:6s}'


def all_youth_status(result, conn):
    """Every youth-eligible player (broadened is_youth() rule: 23-or-
    younger, no committed multi-year contract) currently sitting on EITHER
    of this team's two Fantrax rosters -- not just the ones involved in
    this week's decision. An owner planning ahead needs the whole bench,
    not just what moved."""
    seen = {}
    for players in result["pool_by_pos"].values():
        for p in players:
            if p.get("is_youth_eligible") and p["source"] in ("active", "other"):
                seen[p["name"]] = p
    rows = []
    for name, p in seen.items():
        starts = fetch_start_count(conn, result["code"], name)
        rows.append({
            "name": name, "pos": p["pos"], "where": "Sr" if (p["on_active"] == result["sr"]) else "Jr",
            "starts": starts, "capped": starts >= PROMOTION_TRIGGER_STARTS,
            "next_bar": starts * YOUTH_ESCALATION_PCT,
        })
    rows.sort(key=lambda r: (-r["starts"], r["pos"], r["name"]))
    return rows


SPONSOR_URL = "https://houseofhufflepuff.github.io/two-halves/"
SPONSOR_TAGLINES = [
    "Official MEGAVISION Sponsor: Two Halves -- a rescue robot built to fit through a standard doorway. See it -> {url}",
    "This week's chaos is brought to you by Two Halves. Yes, the robot. Especially the robot. -> {url}",
    "Before you rage-refresh your roster again, go meet Two Halves -- the split-chassis rescue bot MEGAVISION is proud to call a sponsor. -> {url}",
    "MEGAVISION runs on fan formulas, salary caps, and now: a bipedal rescue robot. Meet our sponsor -> {url}",
    "Two Halves: split chassis, rescue laser, fits through a standard doorway. Also, our sponsor. -> {url}",
]


def sponsor_cta():
    import random
    return random.choice(SPONSOR_TAGLINES).format(url=SPONSOR_URL)


def build_email_body(result, moves, conn, sess, executed=True):
    code = result["code"]
    week = result["week"]
    verb = "made" if executed else "would make (opt in to have these run for real -- see footer)"
    pool_by_name = _pool_lookup(result)

    adds = [m for m in moves if m["action"] == "add"]
    drops = [m for m in moves if m["action"] == "drop"]
    opener_key = "many" if len(adds) + len(drops) >= 3 else ("some" if adds or drops else "none")

    lines = [FUN_OPENERS[opener_key], "",
             f'MegaBot ran roster management for {TEAM_FULL_NAME.get(code, code)} ahead of GW{week} '
             f'({"Sr" if result["sr"] else "Jr"} week). Here\'s what it {verb}, and why:', ""]

    if not adds and not drops:
        lines.append("No changes -- your active roster was already the best legal lineup by MEGAVISION Rank.")
    for m in adds:
        lines.append(move_rationale_line(m, pool_by_name))
    for m in drops:
        lines.append(move_rationale_line(m, pool_by_name))

    if result["notes"]:
        lines.append("")
        lines.append(f"Youth-selection detail (Rulez 4.1(6), escalating bar: starts x {YOUTH_ESCALATION_PCT:.0%} better needed):")
        lines.extend(result["notes"])

    # Every youth on EITHER roster, not just ones touched this week -- the
    # owner needs the whole picture, and a PROMOTED player needs a decision
    # whether or not anything moved this week.
    youth_rows = all_youth_status(result, conn)
    if youth_rows:
        lines.append("")
        lines.append(f"Youth on your rosters (Sr + Jr) -- real starts, and the bar to start again ({YOUTH_ESCALATION_PCT:.0%}/start):")
        for r in youth_rows:
            flag = f"  *** PROMOTED at {r['starts']} starts -- needs a real contract decision ***" if r["capped"] else ""
            next_bar_s = "even" if r["starts"] == 0 else f"{r['next_bar']:.0%} better"
            lines.append(f'  {r["name"]:24s} ({r["pos"]}, {r["where"]})  {r["starts"]} starts, next start needs {next_bar_s}{flag}')

    lines.append("")
    lines.append(score_sheet(result, conn, executed=executed))

    # Predicted score vs this week's real opponent, using each side's own
    # best-XI by real fpts-to-date (see predicted_score()) -- not a rank
    # score, a fantasy-points estimate, so the two sides are comparable.
    sr_picks = [p for players in result["plan"].values() for p in players]
    opp_code, is_home = get_opponent(sess, code, week)
    if opp_code:
        # sr_picks (post-move) don't carry the real fpts field -- look it
        # up from the pre-move rosters, which is where fpts actually lives.
        fpts_by_name = {p["name"]: p.get("fpts", 0) for p in result["active_roster"] + result["other_roster"]}
        my_roster_for_pred = [{"pos": p["pos"], "fpts": fpts_by_name.get(p["name"], 0)} for p in sr_picks]
        my_pred = predicted_score(my_roster_for_pred)
        opp_sr_id = fl.FANTRAX_TEAM_ID.get(opp_code) if result["sr"] else fl.JUNIOR_TEAM_ID.get(opp_code)
        opp_roster = fl.fetch_full_roster(sess, opp_sr_id) if opp_sr_id else []
        opp_pred = predicted_score(opp_roster)
        outcome = "WIN" if my_pred > opp_pred else ("LOSS" if my_pred < opp_pred else "DRAW")
        lines.append("")
        lines.append(f'Predicted score vs {TEAM_FULL_NAME.get(opp_code, opp_code)} ({"home" if is_home else "away"}): '
                     f'{my_pred:.1f} - {opp_pred:.1f} -- projected {outcome}')
        lines.append("(best-XI by each side's own real fpts-to-date, not a betting line)")

    lines.append("")
    lines.append(sponsor_cta())
    lines.append("")
    lines.append("-- MegaBot")
    return "\n".join(lines)


def main():
    args = sys.argv[1:]
    write = "--write" in args
    send_email = "--email" in args
    detailed = "--detail" in args or "--detailed" in args
    team_filter = None
    positional = []
    for a in args:
        if a.startswith("--"):
            continue
        if a.upper() in ALL_TEAMS:
            team_filter = a.upper()
        else:
            positional.append(a)
    teams = [team_filter] if team_filter else fetch_managed_teams()
    week_arg = int(positional[0]) if positional else None

    sess = fl._session()
    week = target_week(week_arg, sess)
    sr = is_sr_week(week)
    print(f"Target week: GW{week} -- {'Sr (regular season)' if sr else 'Jr (cup)'} week "
          f"(NON_REGULAR_SEASON_WEEKS={sorted(fa.NON_REGULAR_SEASON_WEEKS)})")
    print(f"Mode: {'WRITE (real Fantrax transactions)' if write else 'READ-ONLY (QA report, no changes made)'}")
    print()

    print("Fetching live FPL player list (for youth candidate identity/age)...", file=sys.stderr)
    elements = fpl.fetch_elements()
    lookup = fpl.build_lookup(elements)
    print("Fetching Youth sheet...", file=sys.stderr)
    wb = common.fetch_live_workbook()
    youth_by_code = common.fetch_youth(wb)

    if detailed:
        print(METHODOLOGY)

    conn = connect()
    for code in teams:
        result = build_plan(conn, sess, youth_by_code, elements, lookup, code, week, sr)
        moves = diff_moves(result)
        if detailed:
            print(render_rosters(result, conn))
            print()
        print(render_report(result, moves, detailed=detailed))
        print()

        if write:
            log = apply_moves(sess, result, moves)
            for entry in log:
                print("  ", entry)
            # Log a start for EVERY youth-eligible player who ends up on the
            # Sr plan this week, not just ones newly added -- a continuing
            # youth who stays on Sr week over week must keep accumulating
            # starts too, or the 4-free-starts cap silently undercounts him
            # (real bug found 2026-09-17: Tzolis/Tel had real starts in
            # weeks the old "only log at add time" logic never recorded).
            sr_picks = [p for players in result["plan"].values() for p in players]
            for p in sr_picks:
                if p.get("is_youth_eligible"):
                    conn.execute(
                        "INSERT OR IGNORE INTO youth_starts (team_code, player_name, gameweek, updated_at) VALUES (?,?,?,?)",
                        (code, p["name"], week, now),
                    )
            conn.commit()
            if send_email:
                body = build_email_body(result, moves)
                print(f"  [would send email to {TEAM_OWNER_EMAILS.get(code)}]")
                # actual send left to the caller -- see megavision_send_helpers
                # patterns used elsewhere in this repo; not wired here since
                # write mode has never been run yet.
    conn.close()


if __name__ == "__main__":
    main()
