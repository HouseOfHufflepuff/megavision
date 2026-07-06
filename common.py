# Shared nav/head/foot template + team roster used by build_site.py and update_rosters.py

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


def head(title, active):
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
    <a href="index.html" class="mv-nav-brand"><img src="logo.png" alt="MEGAVISION"></a>
    <div class="mv-nav-links">
      {nav_links}
    </div>
  </nav>
  <div class="wrap">
"""


FOOT = """  </div>
  <footer class="mv-footer">MEGAVISION &middot; Mega League Archive &middot; <a href="style-guide.html">Style Guide</a></footer>
</body>
</html>
"""
