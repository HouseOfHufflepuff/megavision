"""
Upsert live EA Sports FC 26 overall ratings into mega.db's team_players
table, matched by player name (which db.py already stores cleaned via
player_clean.clean_player, run by sync_players.py).

Run it periodically -- ratings shift with EA's live squad updates:

    python3 sync_players.py        # make sure the roster is current first
    python3 sync_fc26_ratings.py

Always fetches live (see fc26_ratings.py). Nothing about the CSV is cached
to disk; only the matched rating value is written to mega.db.
"""
from datetime import datetime, timezone

from db import connect
from fc26_ratings import fetch_epl_players, build_lookup, match


def main():
    print("Fetching live FC 26 ratings...")
    players = fetch_epl_players()
    lookup = build_lookup(players)
    print(f"Got {len(players)} Premier League players.")

    conn = connect()
    cur = conn.cursor()
    rows = cur.execute("SELECT id, player_name FROM team_players WHERE player_name IS NOT NULL").fetchall()

    now = datetime.now(timezone.utc).isoformat()
    matched = 0
    ambiguous = 0
    unmatched = 0
    for row_id, player_name in rows:
        tokens = player_name.split()
        last = tokens[-1]
        first_initial = tokens[0][0] if tokens else None
        rating = match(lookup, last, first_initial)
        if rating is None:
            if last.lower() in lookup:
                ambiguous += 1
            else:
                unmatched += 1
            continue
        matched += 1
        cur.execute(
            "UPDATE team_players SET fc26_rating = ?, fc26_rating_updated_at = ? WHERE id = ?",
            (rating, now, row_id),
        )
    conn.commit()
    conn.close()
    print(f"Matched {matched} players. {ambiguous} ambiguous (shared surname, couldn't disambiguate), "
          f"{unmatched} not found in the FC 26 EPL list (not in the game, or a naming mismatch).")


if __name__ == "__main__":
    main()
