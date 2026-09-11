"""
Weekly roster manager for the subscribed teams: HUF, TTS, POW (Battersea
Power Bottoms / "BPB"), NAC.

For a given gameweek, decides whether the league is playing Sr (regular
season) or Jr (cup) rosters that week, then builds the best legal lineup
for each subscribed team's ACTIVE sub-team (Sr or Jr, whichever the week
calls for) using MEGAVISION Rank -- pulling in real held-rights unpromoted
youth as a candidate too, gated behind rank_algo.YOUTH_START_RANK_MULTIPLIER
(currently 25% better than the alternative they'd replace) and the Rulez
4.1(6) 4-free-starts-before-promotion cap (tracked in the youth_starts
table -- see db.py; that table starts empty, so any youth already mid-count
before this tool existed will undercount until reconciled by hand).

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

SUBSCRIBED = ["HUF", "TTS", "POW", "NAC"]
TEAM_FULL_NAME = {"HUF": "House of Hufflepuff", "TTS": "Thottenham Thotspur",
                   "POW": "Battersea Power Bottoms", "NAC": "NFC Andover City"}
TEAM_OWNER_EMAILS = {
    "HUF": ["ahrens@gmail.com"],
    "TTS": ["kolaughlin@gmail.com"],
    "POW": ["samrufer@gmail.com", "jeffertz@gmail.com"],
    "NAC": ["tuffer11@gmail.com"],
}

YOUTH_CUTOFF = date(2026, 8, 1)  # Rulez: 23 or younger at Aug 1 to be a selectable Youth Player
YOUTH_FREE_STARTS = rank_algo.YOUTH_FREE_STARTS
YOUTH_MULT = rank_algo.YOUTH_START_RANK_MULTIPLIER

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


def target_week(explicit, sess):
    if explicit:
        return explicit
    games_by_week = {}
    for g in fl.fetch_schedule(sess):
        games_by_week.setdefault(g["week"], []).append(g)
    for w in sorted(games_by_week):
        if not fl.fetch_gameweek_scores(sess, w):
            return w
    return min(games_by_week)


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


def fetch_categories(conn, code):
    return dict(conn.execute(
        "SELECT player_name, category FROM team_player_wages WHERE team_code=? AND season='26/27'", (code,)
    ).fetchall())


def fetch_age(conn, name):
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
        age = fetch_age(conn, p["name"])
        category = categories.get(p["name"], "?")
        pool_by_pos.setdefault(p["pos"], []).append({
            "name": p["name"], "pos": p["pos"], "rank": rank, "likelihood": likelihood, "tag": tag,
            "category": category, "scorerId": p["scorerId"], "age": age,
            "on_active": p in active_roster, "source": "active" if p in active_roster else "other",
            # already on the active roster -> not a NEW start decision, don't re-gate them each week
            "is_youth_candidate": is_youth(age, category) and p not in active_roster,
            "starts": fetch_start_count(conn, code, p["name"]) if is_youth(age, category) else 0,
        })
    for c in youth_candidates:
        pool_by_pos.setdefault(c["pos"], []).append({
            "name": c["name"], "pos": c["pos"], "rank": c["rank"], "likelihood": c["likelihood"], "tag": c["tag"],
            "category": "unpromoted_youth",
            "scorerId": None, "on_active": False, "source": "held_rights", "is_youth_candidate": True,
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
    for pos, n in slots_needed.items():
        pool = pool_by_pos.get(pos, [])
        established = sorted(
            (p for p in pool if not p["is_youth_candidate"]),
            key=lambda p: p["rank"] if p["rank"] is not None else -1, reverse=True,
        )
        picked = established[:n]

        for yc in [p for p in pool if p["is_youth_candidate"]]:
            if yc["rank"] is None:
                notes.append(f'  {pos}: skip {yc["name"]} (held youth rights) -- no MEGAVISION Rank data available')
                continue
            if yc.get("starts", 0) >= YOUTH_FREE_STARTS:
                notes.append(f'  {pos}: skip {yc["name"]} -- already at {yc["starts"]}/{YOUTH_FREE_STARTS} free starts, must be promoted first, not just started')
                continue
            if not picked:
                picked.append(yc)
                notes.append(f'  {pos}: {yc["name"]} added -- empty slot, no alternative to compare against')
                continue
            weakest = min(picked, key=lambda p: p["rank"] if p["rank"] is not None else -1)
            weakest_rank = weakest["rank"] if weakest["rank"] is not None else 0
            bar = weakest_rank * YOUTH_MULT
            if yc["rank"] >= bar and yc["rank"] > weakest_rank:
                picked.remove(weakest)
                picked.append(yc)
                notes.append(
                    f'  {pos}: {yc["name"]} ({yc["rank"]:.1f}) clears the {YOUTH_MULT:.0%} bar over '
                    f'{weakest["name"]} ({weakest_rank:.1f}, bar was {bar:.1f}) -- start {yc.get("starts",0)+1}/{YOUTH_FREE_STARTS}'
                )
            else:
                yc_rank_display = f'{yc["rank"]:.1f}' if yc["rank"] is not None else "0.0"
                notes.append(
                    f'  {pos}: {yc["name"]} ({yc_rank_display}) does NOT clear the '
                    f'{YOUTH_MULT:.0%} bar over {weakest["name"]} ({weakest_rank:.1f}, needed {bar:.1f}) -- stays off'
                )
        plan[pos] = picked

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
                youth_s = " [YOUTH]" if p["is_youth_candidate"] else ""
                starts_s = f'  ({p["starts"]}/{YOUTH_FREE_STARTS} starts)' if p["is_youth_candidate"] else ""
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


def apply_moves(sess, result, moves):
    """NOTE: write mode has never been run -- this is unexercised. A
    brand-new held-youth-rights pickup has no scorerId in our own data
    (never been on any Mega roster), so that case needs a live free-agent
    pool lookup (fl.fetch_full_player_pool) before it can be claimed;
    logged as a clear failure here rather than guessed at."""
    active_id, other_id = result["active_id"], result["other_id"]
    other_by_scorer = {p["name"]: p["scorerId"] for p in result["other_roster"]}
    active_by_scorer = {p["name"]: p["scorerId"] for p in result["active_roster"]}
    log = []
    for m in moves:
        if m["action"] == "drop":
            sid = active_by_scorer.get(m["name"])
            ok, err = sfk.do_drop(sess, active_id, sid) if sid else (False, "no scorerId")
            log.append(("drop", result["code"], m["name"], ok, err))
        elif m["action"] == "add":
            claim_sid = other_by_scorer.get(m["name"]) if m["from"].startswith("other roster") else None
            if m["from"].startswith("other roster") and claim_sid:
                ok, err = sfk.do_drop(sess, other_id, claim_sid)
                log.append(("drop-from-other", result["code"], m["name"], ok, err))
            if not claim_sid:
                log.append(("claim", result["code"], m["name"], False,
                             "no scorerId -- new held-youth-rights pickup needs a live free-agent pool lookup, not implemented"))
                continue
            info, err = sfk.get_claim_defaults(sess, active_id, claim_sid)
            if err or not info:
                log.append(("claim", result["code"], m["name"], False, err or "no claim info"))
                continue
            ok, cerr = sfk.do_claim(sess, active_id, claim_sid, info)
            log.append(("claim", result["code"], m["name"], ok, cerr))
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


def build_email_body(result, moves):
    code = result["code"]
    lines = [f'MegaBot ran roster management for {TEAM_FULL_NAME.get(code, code)} ahead of GW{result["week"]} '
             f'({"Sr" if result["sr"] else "Jr"} week). Here\'s what changed and why:', ""]
    adds = [m for m in moves if m["action"] == "add"]
    drops = [m for m in moves if m["action"] == "drop"]
    if not adds and not drops:
        lines.append("No changes -- your active roster was already the best legal lineup by MEGAVISION Rank.")
    for m in adds:
        lines.append(f'IN:  {m["name"]} ({m["pos"]}) -- {m["from"]}')
    for m in drops:
        lines.append(f'OUT: {m["name"]} ({m["pos"]})')
    if result["notes"]:
        lines.append("")
        lines.append("Youth-selection detail (Rulez 4.1(6), 25%-better gate):")
        lines.extend(result["notes"])
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
        if a.upper() in SUBSCRIBED:
            team_filter = a.upper()
        else:
            positional.append(a)
    teams = [team_filter] if team_filter else SUBSCRIBED
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
            for m in moves:
                if m["action"] == "add" and m["from"].startswith("held youth rights"):
                    conn.execute(
                        "INSERT OR IGNORE INTO youth_starts (team_code, player_name, gameweek, updated_at) VALUES (?,?,?,?)",
                        (code, m["name"], week, now),
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
