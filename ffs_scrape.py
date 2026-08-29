"""
Scrapes fantasyfootballscout.co.uk/team-news for every EPL club's predicted
XI, injury "Out" list, fitness "Doubts" (with %), and the free-text "Latest
News" blurb -- straight HTML (no JS rendering needed, confirmed: the whole
page is server-rendered, no API call to reverse-engineer). No bs4 in this
environment, so parsed with regex against the page's stable WordPress
markup -- fragile to a template redesign, but there's no cheaper honest way
to get real per-club predicted lineups.

Run standalone to sanity-check:
    python3 ffs_scrape.py
"""
import re
import urllib.request

TEAM_NEWS_URL = "https://www.fantasyfootballscout.co.uk/team-news"

# FFS's own team-code slugs -> our FPL-style 3-letter club codes (used
# throughout the rest of this project). Only real mismatch is Forest.
FFS_CODE_TO_CLUB = {
    "ars": "ARS", "avl": "AVL", "bou": "BOU", "bre": "BRE", "bha": "BHA",
    "che": "CHE", "cov": "COV", "cry": "CRY", "eve": "EVE", "ful": "FUL",
    "hul": "HUL", "ips": "IPS", "lee": "LEE", "liv": "LIV", "mci": "MCI",
    "mun": "MUN", "new": "NEW", "nfo": "NOT", "sun": "SUN", "tot": "TOT",
}

POSITIVE_WORDS = (
    "return", "returns", "returned", "back in training", "available",
    "boost", "fit", "impressing", "impressed", "contention", "start",
    "starts", "starting", "nailed", "in form", "back to fitness",
)
NEGATIVE_WORDS = (
    "doubt", "doubtful", "out", "injury", "injured", "miss", "misses",
    "missing", "blow", "concern", "concerned", "setback", "knock",
    "withdrawn", "limped", "substituted", "ruled out", "sidelined",
)

ITEM_RE = re.compile(r'<li class="team-news-item" data-team-code="(\w+)">(.*?)</li>\s*(?=<li class="team-news-item"|$)', re.S)
LINEUP_RE = re.compile(r'<div class="scout-picks(.*?)</div>\s*<ul class="story-parts">', re.S)
PLAYER_NAME_RE = re.compile(r'<span class="player-name[^"]*">([^<]+)</span>')
OUT_RE = re.compile(r'<strong>Out:</strong>(.*?)</li>\s*<li class="headers">\s*<strong>Doubts', re.S)
DOUBTS_RE = re.compile(r'<strong>Doubts:</strong>(.*?)</li>\s*<li class="headers">\s*<strong>Banned', re.S)
LIST_ITEM_RE = re.compile(r'<li>\s*([^<]+?)\s*(?:<span class="doubt-percent">(\d+)%</span>)?\s*</li>', re.S)
NEWS_RE = re.compile(r'<strong>Latest News:\s*</strong>(.*?)</p>', re.S)
TAG_RE = re.compile(r'<[^>]+>')


def _clean(s):
    return TAG_RE.sub("", s).replace("&#39;", "'").replace("&amp;", "&").replace("&#8217;", "’").strip()


def fetch_team_news_html():
    req = urllib.request.Request(TEAM_NEWS_URL, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8")


def parse_team_news(html):
    """club_code -> {lineup: [names], out: [names], doubts: [(name, pct)], news: str}"""
    out = {}
    for m in ITEM_RE.finditer(html):
        ffs_code, block = m.group(1), m.group(2)
        club = FFS_CODE_TO_CLUB.get(ffs_code)
        if not club:
            continue

        lineup_m = LINEUP_RE.search(block)
        lineup = [n.strip() for n in PLAYER_NAME_RE.findall(lineup_m.group(1))] if lineup_m else []

        out_m = OUT_RE.search(block)
        out_list = [_clean(n) for n, _ in LIST_ITEM_RE.findall(out_m.group(1))] if out_m else []
        out_list = [n for n in out_list if n]

        doubts_m = DOUBTS_RE.search(block)
        doubts = []
        if doubts_m:
            for name, pct in LIST_ITEM_RE.findall(doubts_m.group(1)):
                name = _clean(name)
                if name:
                    doubts.append((name, int(pct) if pct else None))

        news_m = NEWS_RE.search(block)
        news = _clean(news_m.group(1)) if news_m else ""

        out[club] = {"lineup": lineup, "out": out_list, "doubts": doubts, "news": news}
    return out


def classify_mentions(name, news_text):
    """(positive, negative) booleans -- crude keyword scan of the club's
    news blurb in the sentence(s) that actually mention this player by
    surname. No real sentiment model here, just a same-sentence keyword
    check against POSITIVE_WORDS/NEGATIVE_WORDS -- good enough to flag
    "worth a look" vs "steer clear", not a nuanced read."""
    if not news_text or not name:
        return False, False
    last = name.split()[-1].lower()
    sentences = re.split(r'(?<=[.!?])\s+', news_text)
    pos, neg = False, False
    for sent in sentences:
        if last in sent.lower():
            low = sent.lower()
            if any(w in low for w in POSITIVE_WORDS):
                pos = True
            if any(w in low for w in NEGATIVE_WORDS):
                neg = True
    return pos, neg


def fetch_and_parse():
    return parse_team_news(fetch_team_news_html())


if __name__ == "__main__":
    data = fetch_and_parse()
    for club, info in data.items():
        print(f"{club}: {len(info['lineup'])} predicted starters, {len(info['out'])} out, {len(info['doubts'])} doubts")
        print("  lineup:", ", ".join(info["lineup"]))
        if info["out"]:
            print("  out:", ", ".join(info["out"]))
        if info["doubts"]:
            print("  doubts:", ", ".join(f"{n} ({p}%)" if p else n for n, p in info["doubts"]))
