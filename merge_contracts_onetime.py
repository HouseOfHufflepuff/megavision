"""
ONE-TIME WORK -- not a repeatable sync script. Run once, QA the result,
done. If we like it we'll decide separately whether/how to make this
repeatable.

Builds team_player_wages: the real, multi-year wage ledger per player,
per season, and makes it the source of truth for financial calculations
going forward (replacing team_players.salary_year1/2/3, which is stale
and was never wired to the live site's displayed salary anyway).

The merge, precisely:
  1. "Correct roster" = what's live on the website right now: parse_keeper_roster()
     (Kept + Youth Legend + Youth Player from CUT EM IF YA GOT EM) plus this
     year's real draft picks (data/draft_picks_2627.json).
  2. Youth Legend / Youth Player only get a wage row if the Youth tab marks
     them "Promoted" -- unpromoted youth don't have a real salary yet, so
     per instruction they're left out entirely.
  3. For Kept + promoted-youth players, look up their real 3-year contract
     (25/26, 26/27, 27/28) in mega.db's existing team_players table (already
     correctly sourced from each team's own sheet tab by sync_players.py).
     Matched by last-name + first-token-prefix, NOT exact string equality --
     e.g. sheet tab has "Morgan Gibbs" (a clean_player() truncation bug on
     the hyphenated "Gibbs-White"), the live roster correctly has "Morgan
     Gibbs-White". A plain name match misses this pair.
  4. If a currently-kept player has NO match in team_players at all (e.g.
     "A. Semenyo" for HUF -- never in any per-team tab), fall back to the
     2-year y1/y2 already on the live roster (CUT EM IF YA GOT EM), tagged
     source='cut_em_sheet' instead of 'team_tab' so it's visibly a weaker source.
  5. team_players rows for THIS team that DON'T match anyone on the live
     roster are players who were actually cut -- deliberately excluded.
  6. Drafted players get one season (26/27) at their real live FPL price.
     KNOWN GAP: some drafted players may have been extended into multi-year
     deals during the Aug 20 window; there's no data source wired up yet to
     detect that, so every drafted player is written as a single-year deal.
     Flagged here rather than guessed.
"""
import unicodedata
from datetime import datetime, timezone

from common import TEAMS, fetch_live_workbook, fetch_youth
from db import connect
from player_clean import clean_player
import sync_fpl_stats as fpl
import json

# copied from update_rosters.py's parse_keeper_roster() rather than
# imported, so this script doesn't trigger that module's expensive
# top-level fetch-and-regenerate-every-page side effect
KEEP_BOX_ROWS = {"kept": (22, 29), "youth_legend": (31, 31), "youth_players": (34, 40)}


def find_keeper_block_col(label_row, code):
    sheet_code = "RNE" if code == "REN" else code
    for i, v in enumerate(label_row):
        if v == sheet_code:
            return i
    return None


def parse_keeper_roster(wb, code):
    ws = wb["CUT EM IF YA GOT EM"]
    rows = list(ws.iter_rows(min_row=1, max_row=101, values_only=True))
    label_row = rows[4]
    col = find_keeper_block_col(label_row, code)
    if col is None:
        return None
    roster = []
    for category, (start, end) in KEEP_BOX_ROWS.items():
        for r in range(start, end + 1):
            row = rows[r - 1]
            if not row[col]:
                continue
            y1 = row[col + 2] if isinstance(row[col + 2], (int, float)) else None
            y2 = row[col + 3] if isinstance(row[col + 3], (int, float)) else None
            pos = (row[col + 1] or "").strip().upper()
            if pos == "G":
                pos = "GK"
            raw = row[col]
            cleaned = clean_player(raw, pos)
            display_name = cleaned["player_name"] or raw
            roster.append({
                "player": display_name, "player_raw": raw, "pos": pos,
                "category": category, "y1": y1, "y2": y2,
            })
    return roster


def _fold(s):
    return unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode("ascii").lower()


def name_match(a, b):
    """True if a and b are plausibly the same player. Handles both the
    clean_player() hyphenated-surname truncation bug (one last name a
    prefix of the other) and abbreviated-first-name sheet entries like
    "P. Porro" vs. "Pedro Porro" (compare first initial, not full token)."""
    if not a or not b:
        return False
    ta, tb = _fold(a).split(), _fold(b).split()
    if not ta or not tb:
        return False
    if ta == tb:
        return True
    if ta[0][0] != tb[0][0]:  # first initial must match
        return False
    la, lb = ta[-1], tb[-1]
    return la == lb or la.startswith(lb) or lb.startswith(la)


def main():
    wb = fetch_live_workbook()
    youth_by_code = fetch_youth(wb)
    with open("data/draft_picks_2627.json") as f:
        drafted_all = json.load(f)
    drafted_by_code = {}
    for d in drafted_all:
        drafted_by_code.setdefault(d["code"], []).append(d)

    print("Fetching live FPL prices for drafted players...")
    fpl_elements = fpl.fetch_elements()
    fpl_lookup = fpl.build_lookup(fpl_elements)

    conn = connect()
    cur = conn.cursor()
    cur.execute("DELETE FROM team_player_wages")  # one-time full rebuild

    now = datetime.now(timezone.utc).isoformat()
    report = {}  # code -> list of row dicts, for the HUF display / QA

    for code, name, owners in TEAMS:
        roster = parse_keeper_roster(wb, code)
        if roster is None:
            continue
        team_tab_rows = cur.execute(
            "SELECT player_name, salary_year1_label, salary_year1, salary_year2_label, salary_year2, "
            "salary_year3_label, salary_year3 FROM team_players WHERE team_code=? AND player_name IS NOT NULL",
            (code,),
        ).fetchall()

        youth_status = {y["player"]: y["status"] for y in youth_by_code.get(code, [])}

        rows_for_team = []
        for p in roster:
            player = p["player"]
            cat = p["category"]
            if cat in ("youth_legend", "youth_players"):
                status = None
                for yname, ystatus in youth_status.items():
                    if name_match(yname, player):
                        status = ystatus
                        break
                if status != "Promoted":
                    continue  # not promoted -- no real salary, leave out per instruction

            match = next((r for r in team_tab_rows if name_match(r[0], player)), None)
            if match:
                # positional season labels, not the stored label text -- at
                # least REN's rows have salary_year3_label wrongly copied as
                # "26/27" instead of "27/28" (a pre-existing bug from the old
                # sync script), so the stored label can't be trusted
                _, l1, s1, l2, s2, l3, s3 = match
                for label, wage in (("25/26", s1), ("26/27", s2), ("27/28", s3)):
                    if wage is not None:
                        rows_for_team.append((code, player, cat, label, wage, "team_tab"))
            else:
                for label, wage in (("26/27", p.get("y1")), ("27/28", p.get("y2"))):
                    if wage is not None:
                        rows_for_team.append((code, player, cat, label, wage, "cut_em_sheet"))

        for d in drafted_by_code.get(code, []):
            tokens = d["name"].split()
            last, first_initial = tokens[-1], (tokens[0][0] if tokens else None)
            e = fpl.match(fpl_lookup, last, first_initial, d.get("club"))
            wage = e["now_cost"] / 10 if e else 4.0
            rows_for_team.append((code, d["name"], "drafted", "26/27", wage, "fpl_price"))

        for row in rows_for_team:
            cur.execute(
                "INSERT INTO team_player_wages (team_code, player_name, category, season, wage, source, updated_at) "
                "VALUES (?,?,?,?,?,?,?)",
                (*row, now),
            )
        report[code] = rows_for_team

    conn.commit()

    total_rows = sum(len(v) for v in report.values())
    print(f"\nWrote {total_rows} wage rows across {len(report)} teams to team_player_wages.\n")

    print("=" * 100)
    print("HUF (House of Hufflepuff, senior + junior combined) -- QA view")
    print("=" * 100)
    huf_rows = report.get("HUF", [])
    by_player = {}
    for code, player, cat, season, wage, source in huf_rows:
        by_player.setdefault((player, cat), {})[season] = (wage, source)
    for (player, cat), seasons in sorted(by_player.items(), key=lambda kv: kv[0][0]):
        parts = []
        for season in ("25/26", "26/27", "27/28"):
            if season in seasons:
                wage, source = seasons[season]
                flag = "" if source == "team_tab" else f"[{source}]"
                parts.append(f"{season}=${wage:.2f}{flag}")
        print(f"  {player:28} {cat:14} {'  '.join(parts)}")

    conn.close()


if __name__ == "__main__":
    main()
