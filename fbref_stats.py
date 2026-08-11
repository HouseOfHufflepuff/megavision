"""
FBref 2025/26 season stats (Big 5 European Leagues combined pages), for
every outfield stat MEGAVISION wants: games, games started, goals,
assists, goals/90, goals+assists/90, xG/90, SCA/90, GCA/90, tackles,
clearances, completed ("successful") passes.

WHY THIS ISN'T FETCHED FROM THE MAIN SITE-BUILD MACHINE: fbref.com
returns HTTP 403 to every request from that environment (Cloudflare bot
check) -- confirmed directly, not assumed. There's a decent chance that's
an IP/environment reputation thing rather than a blanket block, so this
is built to be run from an ordinary machine (yours) instead. If you get
403s here too, FBref is blocking your IP as well and there's no scraping
fix for that -- the only clean path left is Kaggle's mirrored dataset
(https://www.kaggle.com/datasets/hubertsidorowicz/football-players-stats-2025-2026),
which needs a (free) Kaggle API token.

Also worth knowing: FBref reportedly had to pull some advanced tables
(SCA/GCA among them) after an OPTA request as of Jan 2026. If those
specific fields come back empty, that's the site, not a bug here.

Nothing here is guessed or invented: every field is read from FBref's
own `data-stat` attributes (the stable machine-readable key on each
<td>/<th>, independent of visible column headers), and any field this
script can't find gets reported as missing rather than silently zeroed.
"""
import re
import unicodedata
import urllib.request
from html.parser import HTMLParser

BIG5_BASE = "https://fbref.com/en/comps/Big5"
URLS = {
    "standard": f"{BIG5_BASE}/stats/players/Big-5-European-Leagues-Stats",
    "passing": f"{BIG5_BASE}/passing/players/Big-5-European-Leagues-Stats",
    "defense": f"{BIG5_BASE}/defense/players/Big-5-European-Leagues-Stats",
    "gca": f"{BIG5_BASE}/gca/players/Big-5-European-Leagues-Stats",
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
}


def _fold(s):
    return unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode("ascii").lower()


def fetch_html(url):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=30) as resp:
        if resp.status != 200:
            raise RuntimeError(f"{url} -> HTTP {resp.status}")
        return resp.read().decode("utf-8")


class _RowParser(HTMLParser):
    """Pulls one FBref stats table into a list of {data-stat: value} dicts,
    keyed off each cell's data-stat attribute -- FBref's own stable,
    machine-readable key, not the human-visible column header."""

    def __init__(self):
        super().__init__()
        self.rows = []
        self._row = None
        self._cell_key = None
        self._cell_text = []
        self._depth = 0

    def handle_starttag(self, tag, attrs):
        d = dict(attrs)
        if tag == "tr":
            self._row = {}
        elif tag in ("td", "th") and self._row is not None:
            self._cell_key = d.get("data-stat")
            self._cell_text = []
            self._depth += 1

    def handle_data(self, data):
        if self._cell_key is not None:
            self._cell_text.append(data)

    def handle_endtag(self, tag):
        if tag in ("td", "th") and self._cell_key is not None:
            self._row[self._cell_key] = "".join(self._cell_text).strip()
            self._cell_key = None
        elif tag == "tr" and self._row is not None:
            if self._row.get("player") and self._row.get("player") != "Player":
                self.rows.append(self._row)
            self._row = None


def parse_table(html, table_id_hint):
    """FBref wraps most stat tables in HTML comments to defeat naive
    scrapers -- so this un-comments everything before parsing, then finds
    the specific table by id substring."""
    uncommented = re.sub(r"<!--|-->", "", html)
    # isolate just the <table id="...{hint}..."> ... </table> block
    m = re.search(rf'<table[^>]*id="[^"]*{re.escape(table_id_hint)}[^"]*"[^>]*>.*?</table>', uncommented, re.S)
    if not m:
        return []
    p = _RowParser()
    p.feed(m.group(0))
    return p.rows


def _num(row, *keys):
    for k in keys:
        v = row.get(k)
        if v not in (None, ""):
            try:
                return float(v.replace(",", ""))
            except ValueError:
                continue
    return None


def fetch_category(category, table_id_hint):
    html = fetch_html(URLS[category])
    rows = parse_table(html, table_id_hint)
    if not rows:
        available = set()
        for m in re.finditer(r'<table[^>]*id="([^"]+)"', re.sub(r"<!--|-->", "", html)):
            available.add(m.group(1))
        raise RuntimeError(
            f"Couldn't find a table matching '{table_id_hint}' on {URLS[category]}. "
            f"Table ids actually present: {sorted(available) or '(none -- page may not have loaded real content)'}"
        )
    return rows


def fetch_all_players():
    """Merge Standard + Passing + Defense + GCA into one record per
    (player, team). Missing fields stay None rather than being guessed."""
    print("Fetching FBref standard stats...")
    standard = fetch_category("standard", "stats_standard")
    print(f"  {len(standard)} rows")
    print("Fetching FBref passing stats...")
    passing = fetch_category("passing", "stats_passing")
    print(f"  {len(passing)} rows")
    print("Fetching FBref defensive actions...")
    defense = fetch_category("defense", "stats_defense")
    print(f"  {len(defense)} rows")
    print("Fetching FBref goal & shot creation...")
    gca = fetch_category("gca", "stats_gca")
    print(f"  {len(gca)} rows")

    merged = {}
    for row in standard:
        key = (row.get("player"), row.get("team"))
        games = _num(row, "games")
        starts = _num(row, "games_starts")
        goals = _num(row, "goals")
        assists = _num(row, "assists")
        minutes = _num(row, "minutes")
        xg = _num(row, "xg")
        g90 = _num(row, "goals_per90")
        ga90 = _num(row, "goals_assists_per90")
        xg90 = _num(row, "xg_per90")
        if g90 is None and goals is not None and minutes:
            g90 = goals * 90 / minutes
        if ga90 is None and goals is not None and assists is not None and minutes:
            ga90 = (goals + assists) * 90 / minutes
        if xg90 is None and xg is not None and minutes:
            xg90 = xg * 90 / minutes
        merged[key] = {
            "player": row.get("player"), "club": row.get("team"),
            "games": games, "games_started": starts, "goals": goals, "assists": assists,
            "goals_per90": g90, "goals_assists_per90": ga90, "xg_per90": xg90,
            "sca_per90": None, "gca_per90": None, "tackles": None,
            "clearances": None, "passes_completed": None,
        }

    def _fold_key(row):
        return (row.get("player"), row.get("team"))

    for row in passing:
        rec = merged.get(_fold_key(row))
        if rec:
            rec["passes_completed"] = _num(row, "passes_completed")

    for row in defense:
        rec = merged.get(_fold_key(row))
        if rec:
            rec["tackles"] = _num(row, "tackles")
            rec["clearances"] = _num(row, "clearances")

    for row in gca:
        rec = merged.get(_fold_key(row))
        if rec:
            rec["sca_per90"] = _num(row, "sca_per90")
            rec["gca_per90"] = _num(row, "gca_per90")

    return list(merged.values())


def build_lookup(players):
    lookup = {}
    for p in players:
        name = p.get("player") or ""
        if not name:
            continue
        last = name.split()[-1]
        lookup.setdefault(_fold(last), []).append(p)
    return lookup


def match(lookup, last_name, first_initial=None, club_hint=None):
    candidates = lookup.get(_fold(last_name))
    if not candidates:
        return None
    if len(candidates) == 1:
        return candidates[0]
    if first_initial:
        narrowed = [c for c in candidates if _fold((c.get("player") or "")[:1]) == _fold(first_initial)]
        if narrowed:
            candidates = narrowed
        if len(candidates) == 1:
            return candidates[0]
    if club_hint:
        narrowed = [c for c in candidates
                    if _fold(club_hint) in _fold(c.get("club") or "") or _fold(c.get("club") or "") in _fold(club_hint)]
        if len(narrowed) == 1:
            return narrowed[0]
    return None


if __name__ == "__main__":
    players = fetch_all_players()
    print(f"\n{len(players)} total player-season records merged.")
    have_sca = sum(1 for p in players if p["sca_per90"] is not None)
    have_clr = sum(1 for p in players if p["clearances"] is not None)
    print(f"{have_sca} have SCA/90, {have_clr} have clearances (0 of either means FBref may have pulled those tables).")
