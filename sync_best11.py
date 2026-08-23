"""
Best 11: the top-owned fantasy scorers league-wide at each position, straight
off Fantrax's own player-stats pages (ALL_TAKEN, ranked by fantasy points) --
1 GK, 3 D, 4 M, 3 F, same formation as the Rulez tab's Top XI. Stored week
over week in mega.db's best11 table so history isn't lost as new weeks run.

Run for a given week:
    python3 sync_best11.py 1
"""
import sys
from datetime import datetime, timezone

import fantrax_live as fl
from db import connect


def sync_week(week):
    sess = fl._session()
    now = datetime.now(timezone.utc).isoformat()
    conn = connect()
    cur = conn.cursor()
    cur.execute("DELETE FROM best11 WHERE week=?", (week,))

    results = {}
    for pos, need in fl.FORMATION_SLOTS.items():
        leaders = fl.fetch_position_leaders(sess, pos, limit=need)
        results[pos] = leaders
        for rank, p in enumerate(leaders, start=1):
            cur.execute(
                "INSERT INTO best11 (week, pos, slot_rank, player_name, real_club, team_code, fpts, updated_at) "
                "VALUES (?,?,?,?,?,?,?,?)",
                (week, pos, rank, p["name"], p["real_club"], p["team_code"], p["fpts"], now),
            )
    conn.commit()
    conn.close()
    return results


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 sync_best11.py WEEK")
        sys.exit(1)
    week = int(sys.argv[1])
    results = sync_week(week)
    print(f"Best 11 for GW{week}:")
    for pos in ("GK", "D", "M", "F"):
        print(f"  {pos}:")
        for p in results[pos]:
            print(f"    {p['name']:25} {p['real_club']:4} {p['team_code'] or '???':5} {p['fpts']:.1f} pts"
                  + ("" if p["team_code"] else f"  (unmapped team: {p['team_owner_raw']!r})"))
