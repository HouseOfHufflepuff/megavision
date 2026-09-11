"""
Weekly roster-management run across all 12 teams: WRITE mode (real Fantrax
transactions) for the 4 subscribed teams (roster_manager.SUBSCRIBED), READ
mode (report only, nothing touched) for the other 8 -- then one combined
email to each group.

Run:
    python3 run_weekly_roster_management.py [week]
"""
import sys
from datetime import datetime, timezone

import common
import fantrax_live as fl
import roster_manager as rm
import sync_fpl_stats as fpl
from db import connect

now = datetime.now(timezone.utc).isoformat()


def run(week=None):
    sess = fl._session()
    week = rm.target_week(week, sess)
    sr = rm.is_sr_week(week)
    print(f"GW{week} -- {'Sr' if sr else 'Jr'} week")

    elements = fpl.fetch_elements()
    lookup = fpl.build_lookup(elements)
    wb = common.fetch_live_workbook()
    youth_by_code = common.fetch_youth(wb)
    conn = connect()

    managed_sections = []
    suggested_sections = []

    for code in rm.ALL_TEAMS:
        write = code in rm.SUBSCRIBED
        print(f"\n=== {code} ({'WRITE' if write else 'read-only'}) ===")
        result = rm.build_plan(conn, sess, youth_by_code, elements, lookup, code, week, sr)
        moves = rm.diff_moves(result)
        print(rm.render_report(result, moves))

        if write:
            log = rm.apply_moves(sess, result, moves)
            for entry in log:
                print("  ", entry)
            failures = [l for l in log if not l[3]]
            if failures:
                print(f"  ** {len(failures)} failed transaction(s) for {code} -- see log above **")

            sr_picks = [p for players in result["plan"].values() for p in players]
            picks_by_name = {p["name"]: p for p in sr_picks}
            for m in moves:
                if m["action"] != "add":
                    continue
                p = picks_by_name.get(m["name"])
                if p and p.get("is_youth_candidate"):
                    conn.execute(
                        "INSERT OR IGNORE INTO youth_starts (team_code, player_name, gameweek, updated_at) VALUES (?,?,?,?)",
                        (code, m["name"], week, now),
                    )
            conn.commit()

            body = rm.build_email_body(result, moves, conn, sess, executed=True)
            managed_sections.append((code, body))
        else:
            body = rm.build_email_body(result, moves, conn, sess, executed=False)
            suggested_sections.append((code, body))

    conn.close()
    return week, managed_sections, suggested_sections


def compose_managed_email(week, sections):
    subject = f"[AI] MEGAVISION Roster Management — GW{week} — HUF / TTS / BPB / NAC"
    parts = [
        "Ran roster management for the 4 subscribed teams ahead of this week's games. "
        "Real Fantrax moves were made where listed below -- one section per team.",
        "=" * 70,
    ]
    for code, body in sections:
        parts.append(f"\n########## {rm.TEAM_FULL_NAME.get(code, code)} ({code}) ##########\n")
        parts.append(body)
        parts.append("\n" + "=" * 70)
    return subject, "\n".join(parts)


def compose_suggested_email(week, sections):
    subject = f"[AI] MEGAVISION Roster Suggestions — GW{week} — 8 teams (opt-in available)"
    parts = [
        "Ran the same roster-management analysis for your team, read-only -- nothing was "
        "changed on Fantrax. Here's what it would do and why, one section per team.",
        "=" * 70,
    ]
    for code, body in sections:
        parts.append(f"\n########## {rm.TEAM_FULL_NAME.get(code, code)} ({code}) ##########\n")
        parts.append(body)
        parts.append("\n" + "=" * 70)
    parts.append(
        "\nWant these moves made automatically each week like HUF/TTS/BPB/NAC? "
        "Reply all to the MEGAVISION AI thread to opt in."
    )
    return subject, "\n".join(parts)


if __name__ == "__main__":
    week_arg = int(sys.argv[1]) if len(sys.argv) > 1 else None
    week, managed, suggested = run(week_arg)
    print("\n\n" + "#" * 70)
    print("MANAGED EMAIL SUBJECT/BODY")
    print("#" * 70)
    subj, body = compose_managed_email(week, managed)
    print(subj)
    print(body)
    print("\n\n" + "#" * 70)
    print("SUGGESTED EMAIL SUBJECT/BODY")
    print("#" * 70)
    subj2, body2 = compose_suggested_email(week, suggested)
    print(subj2)
    print(body2)
