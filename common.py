# Shared nav/head/foot template + team roster used by build_site.py and update_rosters.py

import io
import urllib.request
from datetime import datetime, timezone

import openpyxl

SHEET_ID = "1l-BG5on67L9beLArTMShJiVZgJOL3CUed3rbuwZKBL0"
EXPORT_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=xlsx"


def fetch_live_workbook():
    """Always live: the sheet is shared 'anyone with the link can view', so
    this is a plain unauthenticated HTTP GET, straight into memory. Never
    write the export to disk, never cache it between runs."""
    req = urllib.request.Request(EXPORT_URL, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = resp.read()
    return openpyxl.load_workbook(io.BytesIO(data), data_only=True)


def fetch_trophy_room(wb):
    ws = wb["Trophy Room"]
    all_rows = list(ws.iter_rows(min_row=1, max_row=60, values_only=True))
    header_idx = None
    for i, row in enumerate(all_rows):
        if row and row[1] == "Premium Title":
            header_idx = i
            break
    comps = [c for c in all_rows[header_idx][1:8] if c]
    seasons = []
    for row in all_rows[header_idx + 1:]:
        if row[0] == "Money":
            break
        if row[0]:
            seasons.append(list(row))
    return comps, seasons

# code, full name, owners
TEAMS = [
    ("FAV", "5th Ave Argyle", ["Jack Weatherman"]),
    ("POW", "Battersea Power Bottoms", ["Sam Rufer", "Joe Effertz"]),
    ("CRG", "CRG McGovern", ["Casey McGovern", "Ryan McGovern", "Grady McGovern", "Jadyn McGovern"]),
    ("DU", "Divided United", ["Chris Gauron"]),
    ("HUF", "House of Hufflepuff", ["Jeremy Ahrens"]),
    ("MS8", "MS 08th", ["Raul Templonuevo"]),
    ("NAC", "NFC Andover City", ["Kris Lien"]),
    ("QFC", "Quidpool FC", ["Erik Johnson"]),
    ("REN", "Real News", ["Reid Foster"]),
    ("BHB", "The Bookhouse Boys", ["Matt O'Laughlin"]),
    ("TTS", "Thottenham Thotspur", ["Kevin O'Laughlin"]),
    ("WTF", "What The FC", ["Erik Olson"]),
    ("ASS", "Wholeassed United FC", ["Kirk Walton", "Dan Hinrichs"]),
]

NAV_LINKS = [
    ("index.html", "Home"),
    ("teams.html", "Teams"),
    ("financials.html", "Financials"),
]


def head(title, active, nav_logo=True):
    nav_items = []
    for href, label in NAV_LINKS:
        cls = ' class="active"' if href == active else ""
        nav_items.append(f'<a href="{href}"{cls}>{label}</a>')
    nav_links = "\n      ".join(nav_items)
    brand = (
        '<a href="index.html" class="mv-nav-brand"><img src="logo.png" alt="MEGAVISION"></a>'
        if nav_logo else '<div class="mv-nav-brand"></div>'
    )
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title} — MEGAVISION</title>
<link rel="icon" type="image/png" sizes="32x32" href="favicon-32.png">
<link rel="icon" type="image/png" sizes="16x16" href="favicon-16.png">
<link rel="apple-touch-icon" href="apple-touch-icon.png">
<link rel="stylesheet" href="palette.css">
<link rel="stylesheet" href="dashboard.css">
</head>
<body>
  <nav class="mv-nav">
    {brand}
    <div class="mv-nav-links">
      {nav_links}
    </div>
  </nav>
  <div class="wrap">
"""


def foot():
    updated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    return f"""  </div>
  <footer class="mv-footer">MEGAVISION &middot; Mega League Archive &middot; <a href="style-guide.html">Style Guide</a> &middot; Updated {updated_at}</footer>
</body>
</html>
"""


# kept for any old callers; prefer foot() so the timestamp is current
FOOT = foot()
