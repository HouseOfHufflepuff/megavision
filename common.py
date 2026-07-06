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


def find_team_sheet(wb, code):
    """Team tabs occasionally get renamed in the live sheet (e.g. 'FAV' ->
    'FAV-Updated'). Try an exact match first, then fall back to any sheet
    name starting with the code, instead of silently dropping the team."""
    if code in wb.sheetnames:
        return code
    for name in wb.sheetnames:
        if name.upper().startswith(code.upper()):
            return name
    return None


def fetch_stadiums(wb):
    """code -> {stadium, capacity}, from row 1 of each team tab."""
    stadiums = {}
    for code, _, _ in TEAMS:
        sheet_name = find_team_sheet(wb, code)
        if sheet_name is None:
            continue
        row0 = next(wb[sheet_name].iter_rows(min_row=1, max_row=1, values_only=True))
        stadiums[code] = {"stadium": row0[1] or "", "capacity": row0[6]}
    return stadiums


def fetch_youth(wb):
    """code -> list of youth-drafted players (all-time), most recent first,
    straight from the 'Youth' tab. Columns: Year, Team, Player, Pos,
    Age, Current Owner Team, Currently Playing, Original Team,
    Fantrax Eligible, Promoted, Youth Rights Released, Contract Frozen."""
    ws = wb["Youth"]
    rows = list(ws.iter_rows(min_row=2, max_row=1167, values_only=True))
    valid_codes = {code for code, _, _ in TEAMS}
    youth_by_code = {code: [] for code in valid_codes}
    for row in rows:
        if not row or row[1] not in valid_codes or not row[2]:
            continue
        code = row[1]
        promoted = str(row[9] or "").strip().upper() == "Y"
        released = str(row[10] or "").strip().upper() == "Y"
        frozen = str(row[11] or "").strip().upper() == "Y"
        if promoted:
            status = "Promoted"
        elif released:
            status = "Released"
        elif frozen:
            status = "Frozen"
        else:
            status = "Active"
        youth_by_code[code].append({
            "year": row[0],
            "player": row[2],
            "pos": row[3] or "",
            "age": row[4],
            "club": row[6] or row[5] or row[7] or "",
            "status": status,
        })
    return youth_by_code


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

# Historical Trophy Room winner names don't always match a team's current
# full name exactly (renames, abbreviations) -- map every variant seen to a code.
TEAM_ALIASES = {
    "5th Ave Argyle": "FAV",
    "5th Avenue Argyle": "FAV",
    "Battersea Power Bottoms": "POW",
    "Battersea Power": "POW",
    "CRG McGovern": "CRG",
    "Divided United": "DU",
    "House of Hufflepuff": "HUF",
    "MS 08th": "MS8",
    "MS 08th FC": "MS8",
    "MS08": "MS8",
    "NFC Andover City": "NAC",
    "Andover City": "NAC",
    "Quidpool FC": "QFC",
    "Real News": "REN",
    "The Bookhouse Boys": "BHB",
    "Bookhouse Boys": "BHB",
    "Thottenham Thotspur": "TTS",
    "What The FC": "WTF",
    "Wholeassed United FC": "ASS",
}


def resolve_team_code(name):
    if not name:
        return None
    return TEAM_ALIASES.get(name.strip())


def tally_trophies(comps, seasons):
    """code -> {comp: count}, built from Trophy Room season rows."""
    tally = {code: {c: 0 for c in comps} for code, _, _ in TEAMS}
    for row in seasons:
        for i, comp in enumerate(comps):
            winner = row[i + 1]
            code = resolve_team_code(winner)
            if code:
                tally[code][comp] += 1
    return tally


# Short labels so trophy tiles never wrap to 3 lines
COMP_ABBR = {
    "Premium Title": "Premium",
    "Champions League": "Champions Lg",
    "Europa League": "Europa Lg",
    "Mega FA Cup": "FA Cup",
    "Citadel Cup": "Citadel Cup",
    "Mega Community Shield": "Comm. Shield",
    "Mega Super Cup": "Super Cup",
}


def fetch_fans(wb):
    """code -> current fan count, from the Standings tab (not every team
    always has a row there -- missing means 0/unknown, shown as '—')."""
    ws = wb["Standings"]
    rows = list(ws.iter_rows(min_row=1, max_row=15, values_only=True))
    header_idx = None
    for i, row in enumerate(rows):
        if row and row[1] == "Team":
            header_idx = i
            break
    fans = {}
    if header_idx is None:
        return fans
    for row in rows[header_idx + 1:]:
        if not row or not row[1]:
            break
        code = resolve_team_code(row[1])
        if code:
            fans[code] = row[12]
    return fans


def owner_short(owners):
    """'Jeremy Ahrens' -> 'Jeremy A.'; extra owners noted as '+N'."""
    first = owners[0].strip()
    parts = first.split()
    if len(parts) >= 2:
        short = f"{parts[0]} {parts[-1][0]}."
    else:
        short = first
    if len(owners) > 1:
        short += f" +{len(owners) - 1}"
    return short


POSITION_ORDER = ["GK", "D", "M", "F"]


def position_sort_key(pos):
    pos = (pos or "").upper()
    try:
        return POSITION_ORDER.index(pos)
    except ValueError:
        return len(POSITION_ORDER)


NAV_LINKS = [
    ("index.html", "Home"),
    ("teams.html", "Teams"),
    ("financials.html", "Financials"),
]


def head(title, active):
    """No logo in the nav anywhere -- it's a big hero image at the top of
    every page's content instead (see hero_logo())."""
    nav_items = []
    for href, label in NAV_LINKS:
        cls = ' class="active"' if href == active else ""
        nav_items.append(f'<a href="{href}"{cls}>{label}</a>')
    nav_links = "\n      ".join(nav_items)
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
    <div class="mv-nav-links">
      {nav_links}
    </div>
  </nav>
  <div class="wrap">
"""


def hero_logo():
    """Big logo, same treatment as index.html, for the top of every other page."""
    return """    <div style="text-align:center;margin-bottom:36px;">
      <img src="logo-trim.png" alt="MEGAVISION" class="mv-glow" style="width:100%;max-width:640px;height:auto;">
    </div>
"""


def foot():
    updated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    return f"""  </div>
  <footer class="mv-footer">MEGAVISION &middot; Mega League Archive &middot; <a href="style-guide.html">Style Guide</a> &middot; Updated {updated_at}</footer>
  <script>
    function mvShowTab(btn, panelId) {{
      var tabs = btn.parentElement.querySelectorAll('.mv-tab');
      var panels = btn.closest('.mv-card').querySelectorAll('.mv-tab-panel');
      tabs.forEach(function(t) {{ t.classList.remove('active'); }});
      panels.forEach(function(p) {{ p.classList.remove('active'); }});
      btn.classList.add('active');
      document.getElementById(panelId).classList.add('active');
    }}
  </script>
</body>
</html>
"""


# kept for any old callers; prefer foot() so the timestamp is current
FOOT = foot()
