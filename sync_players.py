"""
Upsert the team_players table from the live spreadsheet.

Run:
    python3 sync_players.py

Always fetches the sheet live over HTTP (same as the site's build scripts) --
no cached xlsx, no stored intermediate file. Splits the sheet's single messy
'Player' column into player_name / real_club / note via player_clean.py,
cross-checked against the sheet's own Pos column.
"""
import sys
from datetime import datetime, timezone

from common import TEAMS, fetch_live_workbook, find_team_sheet
from player_clean import clean_player
from db import connect


def parse_roster(ws):
    rows = list(ws.iter_rows(min_row=1, max_row=40, values_only=True))
    header_idx = None
    for i, r in enumerate(rows):
        if r[1] == "Player" and r[2] == "Pos":
            header_idx = i
            break
    if header_idx is None:
        return None
    year_labels = [rows[header_idx][3], rows[header_idx][4], rows[header_idx][5]]
    players = []
    for r in rows[header_idx + 1:]:
        if r[0] == "Total":
            break
        if r[1] is None:
            continue
        players.append({
            "slot": r[0],
            "raw": r[1],
            "pos": r[2],
            "y1": r[3], "y2": r[4], "y3": r[5],
            "buyout": r[6],
        })
    return year_labels, players


def main():
    print("Fetching live spreadsheet...")
    wb = fetch_live_workbook()
    now = datetime.now(timezone.utc).isoformat()

    conn = connect()
    cur = conn.cursor()

    total_players = 0
    total_review = 0

    for code, name, owners in TEAMS:
        cur.execute(
            "INSERT INTO teams(code, full_name, owner_display) VALUES (?,?,?) "
            "ON CONFLICT(code) DO UPDATE SET full_name=excluded.full_name, owner_display=excluded.owner_display",
            (code, name, ", ".join(owners)),
        )

        sheet_name = find_team_sheet(wb, code)
        if sheet_name is None:
            print(f"WARN: no tab for {code}, skipping", file=sys.stderr)
            continue
        parsed = parse_roster(wb[sheet_name])
        if parsed is None:
            print(f"WARN: no roster header found for {code}, skipping", file=sys.stderr)
            continue
        year_labels, players = parsed
        y1_label, y2_label, y3_label = year_labels

        for p in players:
            cleaned = clean_player(p["raw"], p["pos"])
            total_players += 1
            if cleaned["needs_review"]:
                total_review += 1
            cur.execute(
                """
                INSERT INTO team_players (
                    team_code, roster_slot, player_name_raw, player_name, position,
                    real_club, note, needs_review, is_placeholder_gk, resolved_via_override,
                    salary_year1_label, salary_year1, salary_year2_label, salary_year2,
                    salary_year3_label, salary_year3, buyout, updated_at
                ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                ON CONFLICT(team_code, player_name_raw) DO UPDATE SET
                    roster_slot=excluded.roster_slot,
                    player_name=excluded.player_name,
                    position=excluded.position,
                    real_club=excluded.real_club,
                    note=excluded.note,
                    needs_review=excluded.needs_review,
                    is_placeholder_gk=excluded.is_placeholder_gk,
                    resolved_via_override=excluded.resolved_via_override,
                    salary_year1_label=excluded.salary_year1_label,
                    salary_year1=excluded.salary_year1,
                    salary_year2_label=excluded.salary_year2_label,
                    salary_year2=excluded.salary_year2,
                    salary_year3_label=excluded.salary_year3_label,
                    salary_year3=excluded.salary_year3,
                    buyout=excluded.buyout,
                    updated_at=excluded.updated_at
                """,
                (
                    code, p["slot"], str(p["raw"]), cleaned["player_name"], p["pos"],
                    cleaned["real_club"], cleaned["note"],
                    int(cleaned["needs_review"]), int(cleaned["is_placeholder_gk"]),
                    int(cleaned["resolved_via_override"]),
                    y1_label, p["y1"], y2_label, p["y2"], y3_label, p["y3"], p["buyout"],
                    now,
                ),
            )

    conn.commit()
    conn.close()
    print(f"Upserted {total_players} players ({total_review} flagged needs_review).")


if __name__ == "__main__":
    main()
