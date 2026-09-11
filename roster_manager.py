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
        "SELECT g.megavision_rank FROM epl_players p JOIN player_gameweek g "
        "ON g.player_name=p.player_name AND g.real_club=p.real_club "
        "WHERE p.player_name=? AND g.gameweek=?", (name, week),
    ).fetchone()
    return row[0] if row else None


def fetch_categories(conn, code):
    return dict(conn.execute(
        "SELECT player_name, category FROM team_player_wages WHERE team_code=? AND season='26/27'", (code,)
    ).fetchall())


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
        rank = fetch_rank(conn, f'{el["first_name"]} {el["second_name"]}', week)
        out.append({
            "name": f'{el["first_name"]} {el["second_name"]}', "sheet_name": r["player"],
            "pos": pos, "club": el.get("club_short"), "age": age, "rank": rank,
            "starts": fetch_start_count(conn, code, f'{el["first_name"]} {el["second_name"]}'),
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
        pool_by_pos.setdefault(p["pos"], []).append({
            "name": p["name"], "pos": p["pos"], "rank": fetch_rank(conn, p["name"], week),
            "category": categories.get(p["name"], "?"), "scorerId": p["scorerId"],
            "on_active": p in active_roster, "is_youth_candidate": False,
        })
    for c in youth_candidates:
        pool_by_pos.setdefault(c["pos"], []).append({
            "name": c["name"], "pos": c["pos"], "rank": c["rank"], "category": "unpromoted_youth",
            "scorerId": None, "on_active": False, "is_youth_candidate": True,
            "starts": c["starts"], "club": c["club"], "age": c["age"],
        })

    slots_needed = {}
    for p in active_roster:
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


def render_report(result, moves):
    code, week, sr = result["code"], result["week"], result["sr"]
    lines = [f'=== {TEAM_FULL_NAME.get(code, code)} ({code}) -- GW{week}, {"Sr" if sr else "Jr"} week ===']
    adds = [m for m in moves if m["action"] == "add"]
    drops = [m for m in moves if m["action"] == "drop"]
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
    week_args = [a for a in args if not a.startswith("--")]
    week_arg = int(week_args[0]) if week_args else None

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

    conn = connect()
    for code in SUBSCRIBED:
        result = build_plan(conn, sess, youth_by_code, elements, lookup, code, week, sr)
        moves = diff_moves(result)
        print(render_report(result, moves))
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
