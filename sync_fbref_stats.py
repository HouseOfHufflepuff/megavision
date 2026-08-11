"""
THE SCRIPT TO RUN YOURSELF: fetches 2025/26 FBref stats (Big 5 European
Leagues), caches them into mega.db, then regenerates and republishes the
site pages that show them (team pages' Scouting tab + draft.html).

    python3 sync_fbref_stats.py

This has to run from your own machine, not the sandbox this site's other
scripts run in -- fbref.com blocks that sandbox outright (HTTP 403,
Cloudflare bot check, confirmed directly). If it 403s for you too, FBref
is blocking your IP as well and there's no scraping fix for that; see
fbref_stats.py's docstring for the Kaggle-dataset fallback.

This does NOT commit or push. After it finishes, review the regenerated
*.html files and run your usual git add/commit/push when you're happy
with them.
"""
import subprocess
import sys
from datetime import datetime, timezone

from db import connect
from fbref_stats import fetch_all_players


def main():
    try:
        players = fetch_all_players()
    except Exception as e:
        print(f"\nFBref fetch failed: {e}", file=sys.stderr)
        print("If this is a 403, FBref is blocking this machine too -- see the Kaggle "
              "fallback noted in fbref_stats.py's docstring.", file=sys.stderr)
        sys.exit(1)

    conn = connect()
    cur = conn.cursor()
    now = datetime.now(timezone.utc).isoformat()
    written = 0
    for p in players:
        if not p.get("player"):
            continue
        last = p["player"].split()[-1]
        cur.execute(
            """INSERT INTO fbref_players
               (player_name, last_name, club, games, games_started, goals, assists,
                goals_per90, goals_assists_per90, xg_per90, sca_per90, gca_per90,
                tackles, clearances, passes_completed, updated_at)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
               ON CONFLICT(player_name, club) DO UPDATE SET
                 last_name=excluded.last_name, games=excluded.games, games_started=excluded.games_started,
                 goals=excluded.goals, assists=excluded.assists, goals_per90=excluded.goals_per90,
                 goals_assists_per90=excluded.goals_assists_per90, xg_per90=excluded.xg_per90,
                 sca_per90=excluded.sca_per90, gca_per90=excluded.gca_per90, tackles=excluded.tackles,
                 clearances=excluded.clearances, passes_completed=excluded.passes_completed,
                 updated_at=excluded.updated_at""",
            (p["player"], last, p.get("club"), p["games"], p["games_started"], p["goals"], p["assists"],
             p["goals_per90"], p["goals_assists_per90"], p["xg_per90"], p["sca_per90"], p["gca_per90"],
             p["tackles"], p["clearances"], p["passes_completed"], now),
        )
        written += 1
    conn.commit()
    conn.close()
    print(f"\nCached {written} FBref player-season rows to mega.db.")

    print("\nRegenerating team pages + financials...")
    subprocess.run([sys.executable, "update_rosters.py"], check=True)
    print("\nRegenerating draft board...")
    subprocess.run([sys.executable, "build_draft.py"], check=True)

    print("\nDone. Review the changed *.html files, then commit + push as usual to publish.")


if __name__ == "__main__":
    main()
