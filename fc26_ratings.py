"""
EA Sports FC 26 player ratings (overall, potential, transfer value), live,
across all leagues -- players move clubs/leagues, so ratings are looked up
wherever a player currently is, not restricted to the Premier League.

Not sourced from EA's own site or sofifa.com/futwiz.com directly -- all
three explicitly disallow ClaudeBot in robots.txt. Instead this pulls a
community-maintained CSV mirror on GitHub (ismailoksuz/EAFC26-DataHub,
sourced from a public Kaggle dataset) that carries the same sofifa player
IDs and images (verified: player 206517 = Jack Grealish, overall 80,
matching https://sofifa.com/player/206517/260044/ exactly). GitHub raw
content has no such bot restriction.

Always fetched live over plain HTTP -- nothing cached to disk here.
"""
import csv
import io
import unicodedata
import urllib.request

CSV_URL = "https://raw.githubusercontent.com/ismailoksuz/EAFC26-DataHub/main/data/players.csv"


def _fold(s):
    """Strip accents/diacritics for matching: 'Konaté' -> 'konate'."""
    return unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode("ascii").lower()


def fetch_all_players():
    """List of {last_names, full_name, overall, potential, value_eur, club,
    positions} for every player in the live FC 26 dataset, any league --
    players move clubs/leagues (loans, transfers), so this isn't filtered
    to the Premier League."""
    req = urllib.request.Request(CSV_URL, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = resp.read().decode("utf-8")
    reader = csv.DictReader(io.StringIO(data))
    players = []
    for row in reader:
        full_name = row.get("long_name") or row.get("short_name") or ""
        if not full_name:
            continue
        try:
            overall = float(row["overall"])
        except (KeyError, ValueError):
            continue
        try:
            potential = float(row["potential"])
        except (KeyError, ValueError):
            potential = None
        try:
            value_eur = float(row["value_eur"])
        except (KeyError, ValueError):
            value_eur = None
        short_name = row.get("short_name", "") or ""
        players.append({
            # both the full legal surname AND the short/known name's last
            # token -- Brazilian/Portuguese players in particular go by a
            # mononym (e.g. "Joelinton") that shares no surname with their
            # long_name ("Joelinton Cassio Apolinario de Lira")
            "last_names": {_fold(t) for t in (full_name.split()[-1], short_name.split()[-1] if short_name else "") if t},
            "full_name": full_name,
            "short_name": short_name,
            "overall": overall,
            "potential": potential,
            "value_eur": value_eur,
            "club": row.get("club_name", ""),
            "positions": row.get("player_positions", ""),
        })
    return players


def build_lookup(players):
    """last name (lower) -> list of candidate player dicts."""
    lookup = {}
    for p in players:
        for last_name in p["last_names"]:
            lookup.setdefault(last_name, []).append(p)
    return lookup


def match(lookup, last_name, first_initial=None):
    """Resolve a last name to a single player dict, disambiguating
    same-surname players by first initial when there's more than one
    candidate. Returns None if there's no match or it's still ambiguous."""
    candidates = lookup.get(_fold(last_name))
    if not candidates:
        return None
    if len(candidates) == 1:
        return candidates[0]
    if first_initial:
        narrowed = [c for c in candidates if _fold(c["short_name"].strip()[:1]) == _fold(first_initial)
                    or _fold(c["full_name"].strip()[:1]) == _fold(first_initial)]
        if len(narrowed) == 1:
            return narrowed[0]
    return None  # still ambiguous


if __name__ == "__main__":
    print(f"Fetching live FC 26 ratings from {CSV_URL} ...")
    players = fetch_all_players()
    print(f"Got {len(players)} players across all leagues.")
    lookup = build_lookup(players)
    dupes = {k: len(v) for k, v in lookup.items() if len(v) > 1}
    print(f"{len(dupes)} surnames shared by more than one player (need first-initial disambiguation).")
    grealish = match(lookup, "grealish")
    print(f"Sanity check -- Grealish overall: {grealish['overall'] if grealish else None} (sofifa.com/player/206517 shows 80)")
