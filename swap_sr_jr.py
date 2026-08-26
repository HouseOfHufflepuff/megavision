"""
One-time swap: for every one of the 12 franchises, move the entire Jr
(reserve) Fantrax roster onto the Sr team and the entire old Sr roster onto
Jr. Real commissioner-mode Fantrax transactions, executed immediately.

Why: Jr rosters are the valid, full rosters right now; Sr rosters are what
actually plays next week's matchups. Run once, per Jer's instruction
2026-08-26.

Run:
    python3 swap_sr_jr.py
"""
import time

import fantrax_live as fl
import sync_fantrax_keepers as sfk

INJURY_TYPE_IDS = {"1", "30", "7"}  # game-time decision / out / inactive -- not "9" (news note)


def fetch_full_roster(sess, team_id):
    """[{scorerId, name, pos, club, injuries: [tooltip,...]}] -- every
    player currently on this Fantrax roster, no stat/period filtering."""
    data = fl._post(sess, "getTeamRosterInfo", teamId=team_id, view="SIMPLE")
    out = []
    for table in data.get("tables", []):
        for row in table.get("rows", []):
            scorer = row.get("scorer") or {}
            sid = scorer.get("scorerId")
            pos_id = row.get("posId")
            if not sid or pos_id not in fl.POSITION_MAP:
                continue
            injuries = [
                icon["tooltip"] for icon in (scorer.get("icons") or [])
                if icon.get("typeId") in INJURY_TYPE_IDS
            ]
            out.append({
                "scorerId": sid, "name": scorer.get("name", "?"),
                "pos": fl.POSITION_MAP[pos_id], "club": scorer.get("teamShortName", ""),
                "injuries": injuries,
            })
    return out


def drop_all(sess, team_id, roster, log):
    for p in roster:
        ok, err = sfk.do_drop(sess, team_id, p["scorerId"])
        log.append(("drop", team_id, p["name"], ok, err))
        if not ok:
            print(f"    FAIL drop {p['name']}: {err}")
        time.sleep(0.4)


def claim_all(sess, team_id, roster, log):
    for p in roster:
        info, err = sfk.get_claim_defaults(sess, team_id, p["scorerId"])
        if err or not info:
            log.append(("claim", team_id, p["name"], False, err or "no claim info"))
            print(f"    FAIL claim-info {p['name']}: {err}")
            continue
        ok, cerr = sfk.do_claim(sess, team_id, p["scorerId"], info)
        log.append(("claim", team_id, p["name"], ok, cerr))
        if not ok:
            print(f"    FAIL claim {p['name']}: {cerr}")
        time.sleep(0.4)


def main():
    sess = fl._session()
    log = []
    injury_report = {}  # code -> [ {name, club, injuries} ] now on Sr

    for code in fl.FANTRAX_TEAM_ID:
        sr_id = fl.FANTRAX_TEAM_ID[code]
        jr_id = fl.JUNIOR_TEAM_ID[code]
        print(f"=== {code} ===")

        sr_roster = fetch_full_roster(sess, sr_id)
        jr_roster = fetch_full_roster(sess, jr_id)
        print(f"  Sr: {len(sr_roster)} players, Jr: {len(jr_roster)} players")

        print("  dropping both rosters...")
        drop_all(sess, sr_id, sr_roster, log)
        drop_all(sess, jr_id, jr_roster, log)

        print("  claiming Jr roster onto Sr...")
        claim_all(sess, sr_id, jr_roster, log)
        print("  claiming old Sr roster onto Jr...")
        claim_all(sess, jr_id, sr_roster, log)

        injured = [p for p in jr_roster if p["injuries"]]
        if injured:
            injury_report[code] = injured

    failures = [l for l in log if not l[3]]
    print(f"\nDONE. {len(log)} transactions, {len(failures)} failures.")
    if failures:
        print("Failures:")
        for action, team_id, name, ok, err in failures:
            code = fl.ALL_TEAM_ID_TO_CODE.get(team_id, team_id)
            print(f"  {action} {code} {name}: {err}")

    print("\nInjury flags on new Sr rosters:")
    for code, players in injury_report.items():
        for p in players:
            print(f"  {code}: {p['name']} ({p['club']}) -- {'; '.join(p['injuries'])}")

    return log, injury_report


if __name__ == "__main__":
    main()
