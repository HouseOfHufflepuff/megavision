"""
The weekly MEGAVISION update: syncs real results for the week that just
finished, rebuilds the whole site off that, then preps MEGAVISION Rank for
the upcoming week. This is the site/data half of the weekly cycle --
roster management (real Fantrax moves) is deliberately a separate script
(run_weekly_roster_management.py), since that one makes real transactions
and shouldn't fire as a side effect of a routine site refresh.

Pipeline, in order:
    1. sync_best11.py <played week>    -- top-owned scorers league-wide
    2. sync_fans.py <played week>      -- fan interest, attendance, ticket revenue
    3. update_rosters.py               -- rebuilds every page off the DB
                                           (standings, finances, fan cards,
                                           roster/contract pages, team pages)
    4. sync_player_ranks.py <next week>   -- FC26 + Fantrax + FFS team-news
    5. sync_megavision_rank.py <next week> -- 0-100 Rank + start likelihood
    6. build_rank.py                    -- rebuilds rank.html

Week detection reuses roster_manager's (already-fixed) logic: a week only
counts as played once it has a real, nonzero score -- not just because a
Gameweek table exists (Fantrax pre-populates next week's table with 0-0
placeholders before it's played).

Run:
    python3 weekly_update.py            # auto-detect played/next week
    python3 weekly_update.py 4          # force played week = 4 (next = 5)
"""
import subprocess
import sys

import fantrax_live as fl
import roster_manager as rm


def run(cmd):
    print(f"\n$ {' '.join(cmd)}")
    result = subprocess.run(cmd)
    if result.returncode != 0:
        raise SystemExit(f"FAILED: {' '.join(cmd)} (exit {result.returncode})")


def main():
    sess = fl._session()
    if len(sys.argv) > 1:
        played_week = int(sys.argv[1])
        next_week = played_week + 1
    else:
        next_week = rm.target_week(None, sess)
        played_week = next_week - 1

    print(f"Played week: GW{played_week}  |  Prepping: GW{next_week}")

    if played_week >= 1:
        run(["python3", "sync_best11.py", str(played_week)])
        run(["python3", "sync_fans.py", str(played_week)])

    run(["python3", "update_rosters.py"])

    run(["python3", "sync_player_ranks.py", str(next_week)])
    run(["python3", "sync_megavision_rank.py", str(next_week)])
    run(["python3", "build_rank.py"])

    print(f"\nDone. Site rebuilt for GW{played_week} results, GW{next_week} rank ready.")
    print("Not run automatically (separate, deliberate step): python3 run_weekly_roster_management.py")


if __name__ == "__main__":
    main()
