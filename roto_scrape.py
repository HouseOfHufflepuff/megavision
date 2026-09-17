"""
Scrapes rotowire.com's Premier League depth charts for a second, independent
"who's actually going to start" signal -- a plain positional ranking per
club (1 = first-choice, 2 = backup, ...), plus RotoWire's own inline
injury tags (GTD/OUT) on top of each name. No JS rendering needed, the
whole page is server-rendered.

Added 2026-09-17 per Jer: blend this in at a fixed 20% weight alongside the
existing FFS-based start signal (see rank_algo.ROTO_WEIGHT), so a single
source's mistake or blind spot doesn't fully decide a player's gate.

Run standalone to sanity-check:
    python3 roto_scrape.py
"""
import re
import urllib.request

DEPTH_CHARTS_URL = "https://www.rotowire.com/soccer/premier-league-depth-charts-1/"

# RotoWire's own team names -> our FPL-style 3-letter club codes.
ROTO_TEAM_TO_CLUB = {
    "afc bournemouth": "BOU", "arsenal": "ARS", "aston villa": "AVL",
    "brentford": "BRE", "brighton & hove albion": "BHA", "chelsea": "CHE",
    "coventry city": "COV", "crystal palace": "CRY", "everton": "EVE",
    "fulham": "FUL", "hull city": "HUL", "ipswich town": "IPS",
    "leeds united": "LEE", "liverpool": "LIV", "manchester city": "MCI",
    "manchester united": "MUN", "newcastle united": "NEW",
    "nottingham forest": "NOT", "sunderland": "SUN", "tottenham hotspur": "TOT",
}

TEAM_BLOCK_RE = re.compile(
    r'depth-charts__team-name">([^<]+)</div>.*?(?=<div class="depth-charts__block">|$)', re.S
)
POS_BLOCK_RE = re.compile(
    r'<div class="depth-charts__pos-head">([^<]+)</div>\s*<ul class="depth-charts__pos-list">(.*?)</ul>', re.S
)
PLAYER_ITEM_RE = re.compile(
    r'<li>\s*<a href="/soccer/player/[^"]*">(.*?)</a>(?:\s*<span class="depth-charts__inj">([^<]+)</span>)?\s*</li>',
    re.S,
)
NAME_SPAN_RE = re.compile(r'<span class="hide-until-xs">([^<]*)</span><span class="hide-xs-up">[^<]*</span>\s*([^<]*)')

POS_HEAD_TO_CODE = {"Goalkeeper": "GK", "Defender": "D", "Midfielder": "M", "Forward": "F"}


def _clean_name(raw):
    m = NAME_SPAN_RE.search(raw)
    if not m:
        return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", raw)).strip()
    first, last = m.group(1).strip(), m.group(2).strip()
    return f"{first} {last}".strip()


def fetch_depth_charts_html():
    req = urllib.request.Request(DEPTH_CHARTS_URL, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8")


def parse_depth_charts(html):
    """club_code -> {pos_code: [{"name", "depth_rank" (1-based), "inj_tag"}]}"""
    out = {}
    for m in TEAM_BLOCK_RE.finditer(html):
        team_name, block = m.group(1).strip(), m.group(0)
        club = ROTO_TEAM_TO_CLUB.get(team_name.lower())
        if not club:
            continue
        positions = {}
        for pos_m in POS_BLOCK_RE.finditer(block):
            pos_head, list_html = pos_m.group(1).strip(), pos_m.group(2)
            pos_code = POS_HEAD_TO_CODE.get(pos_head)
            if not pos_code:
                continue
            players = []
            for i, item_m in enumerate(PLAYER_ITEM_RE.finditer(list_html), start=1):
                name = _clean_name(item_m.group(1))
                inj_tag = item_m.group(2)
                if name:
                    players.append({"name": name, "depth_rank": i, "inj_tag": inj_tag})
            positions[pos_code] = players
        out[club] = positions
    return out


def build_index(depth_charts):
    """club_code -> {folded_surname: {"depth_rank", "inj_tag"}} -- flat,
    matched the same way FFS/FPL names are matched elsewhere in this repo."""
    import sync_fpl_stats as fpl
    idx = {}
    for club, positions in depth_charts.items():
        names = {}
        for pos_code, players in positions.items():
            for p in players:
                last = fpl._fold(p["name"].split()[-1])
                names[last] = {"depth_rank": p["depth_rank"], "inj_tag": p["inj_tag"]}
        idx[club] = names
    return idx


def fetch_and_parse():
    return parse_depth_charts(fetch_depth_charts_html())


if __name__ == "__main__":
    charts = fetch_and_parse()
    for club, positions in sorted(charts.items()):
        print(f"=== {club} ===")
        for pos_code in ("GK", "D", "M", "F"):
            players = positions.get(pos_code, [])
            names = ", ".join(f'{p["depth_rank"]}.{p["name"]}' + (f'[{p["inj_tag"]}]' if p["inj_tag"] else "") for p in players)
            print(f"  {pos_code}: {names}")
