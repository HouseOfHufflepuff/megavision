"""
Upsert 2025/26 Premier League season totals (minutes, starts, goals,
assists, tackles, clearances+blocks+interceptions, xG) into mega.db's
team_players table, from the official Fantasy Premier League API --
no auth, no scraping, no bot-blocking.

Deliberately NOT sourced from FBref: fbref.com returns HTTP 403 to every
fetch (Cloudflare bot check), and no current free bulk mirror of its
25/26 advanced tables (SCA/GCA, pure clearances, pass completions) could
be found -- see the "known gaps" note below. The FPL API is the closest
free, reliable, no-auth substitute; its own stat definitions are used
as-is (e.g. "clearances_blocks_interceptions" is a combined stat, not
FBref's narrower "Clr").

Known gaps vs. what FBref itself would offer, left out rather than
faked: SCA/90, GCA/90, successful/completed passes, and any player who
spent 2025/26 outside the Premier League (this API only tracks the PL).

Run:
    python3 sync_players.py        # roster current first
    python3 sync_fpl_stats.py
"""
import json
import unicodedata
import urllib.request
from datetime import datetime, timezone

from db import connect

BOOTSTRAP_URL = "https://fantasy.premierleague.com/api/bootstrap-static/"
SUMMARY_URL = "https://fantasy.premierleague.com/api/element-summary/{id}/"
SEASON = "2025/26"


def _fold(s):
    return unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode("ascii").lower()


def _get_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def fetch_elements():
    data = _get_json(BOOTSTRAP_URL)
    return data["elements"]


def build_lookup(elements):
    """Keyed by last-name token (lower, folded) -- matches how callers look
    players up (player_name.split()[-1]), so a compound surname like "van
    Dijk" has to be indexed under "dijk", not the whole string."""
    lookup = {}
    for e in elements:
        tokens = {e["second_name"].split()[-1] if e["second_name"] else "", e["web_name"]}
        for token in tokens:
            if token:
                lookup.setdefault(_fold(token), []).append(e)
    return lookup


def match(lookup, last_name, first_initial=None):
    candidates = lookup.get(_fold(last_name))
    if not candidates:
        return None
    # de-dupe (same element can be indexed under both second_name and web_name)
    seen = {}
    for c in candidates:
        seen[c["id"]] = c
    candidates = list(seen.values())
    if len(candidates) == 1:
        return candidates[0]
    if first_initial:
        narrowed = [c for c in candidates if _fold(c["first_name"][:1]) == _fold(first_initial)]
        if len(narrowed) == 1:
            return narrowed[0]
    return None


def fetch_season_totals(element_id):
    """2025/26 season row from this player's history_past, or None."""
    data = _get_json(SUMMARY_URL.format(id=element_id))
    for row in data.get("history_past", []):
        if row.get("season_name") == SEASON:
            return row
    return None


def main():
    print("Fetching FPL player list...")
    elements = fetch_elements()
    lookup = build_lookup(elements)
    print(f"Got {len(elements)} Premier League players.")

    conn = connect()
    cur = conn.cursor()
    rows = cur.execute("SELECT id, player_name FROM team_players WHERE player_name IS NOT NULL").fetchall()

    now = datetime.now(timezone.utc).isoformat()
    matched = 0
    no_season_data = 0
    unmatched = 0
    for row_id, player_name in rows:
        tokens = player_name.split()
        last = tokens[-1]
        first_initial = tokens[0][0] if tokens else None
        e = match(lookup, last, first_initial)
        if e is None:
            unmatched += 1
            continue
        totals = fetch_season_totals(e["id"])
        if totals is None:
            no_season_data += 1
            continue
        matched += 1
        cur.execute(
            "UPDATE team_players SET fpl_starts = ?, fpl_goals = ?, fpl_assists = ?, fpl_minutes = ?, "
            "fpl_tackles = ?, fpl_cbi = ?, fpl_xg = ?, fpl_stats_updated_at = ? WHERE id = ?",
            (
                totals["starts"], totals["goals_scored"], totals["assists"], totals["minutes"],
                totals["tackles"], totals["clearances_blocks_interceptions"],
                float(totals["expected_goals"]), now, row_id,
            ),
        )
    conn.commit()
    conn.close()
    print(f"Matched {matched} players with 2025/26 PL data. {no_season_data} matched a PL player but had no "
          f"2025/26 season row (likely played elsewhere that season). {unmatched} not found in the PL at all "
          f"(spent 2025/26 outside the Premier League, or a naming mismatch).")


if __name__ == "__main__":
    main()
