import json

d = json.load(open("_trophy_seasons.json"))
comps = d["comps"]
seasons = d["seasons"]

total_titles = sum(1 for s in seasons for v in s[1:8] if v)
reigning = seasons[0][1] or "—"

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


def head(title, active):
    links = [
        ("index.html", "Home"),
        ("teams.html", "Teams"),
        ("financials.html", "Financials"),
        ("style-guide.html", "Style Guide"),
    ]
    nav_items = []
    for href, label in links:
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

# ---------------- index.html ----------------
rows_html = []
for i, s in enumerate(seasons):
    cells = []
    for ci, comp in enumerate(comps):
        val = s[ci + 1] or "—"
        cls = "dim" if val == "—" else ("champ" if comp == "Premium Title" else "")
        style = ' style="color:var(--mv-gold);font-weight:600;"' if cls == "champ" else ""
        cells.append(f'<td class="{cls}"{style}>{val}</td>')
    row_style = ' style="background:rgba(255,209,102,0.06);"' if i == 0 else ""
    rows_html.append(f'<tr{row_style}><td style="font-weight:700;">{s[0]}</td>{"".join(cells)}</tr>')

headers_html = "".join(f"<th>{c}</th>" for c in comps)
rows_joined = "\n            ".join(rows_html)

index_html = head("Home", "index.html") + f"""
    <header style="text-align:center;margin-bottom:36px;">
      <img src="logo.png" alt="MEGAVISION" class="mv-glow" style="width:120px;height:auto;opacity:0.92;">
      <p style="color:var(--mv-ink-muted);font-size:14px;letter-spacing:0.04em;margin-top:10px;">MEGA FANTASY SOCCER LEAGUE &nbsp;·&nbsp; EST. 2014</p>
    </header>

    <div class="mv-stat-grid">
      <div class="mv-stat"><div class="label">Seasons Played</div><div class="value mv-spark-text">{len(seasons)}</div></div>
      <div class="mv-stat"><div class="label">Titles Awarded</div><div class="value mv-spark-text">{total_titles}</div></div>
      <div class="mv-stat"><div class="label">Reigning Champion</div><div class="value mv-spark-text" style="font-size:17px;">{reigning}</div></div>
    </div>

    <section class="card mv-card">
      <h2 class="mv-chrome-text">Hall of Champions</h2>
      <div class="sub">Every title the league has ever awarded, season by season</div>
      <div class="mv-table-scroll">
        <table class="mv-table">
          <thead><tr><th>Season</th>{headers_html}</tr></thead>
          <tbody>
            {rows_joined}
          </tbody>
        </table>
      </div>
    </section>
""" + FOOT

with open("index.html", "w") as f:
    f.write(index_html)

# ---------------- teams.html ----------------
team_cards = []
for code, name, owners in TEAMS:
    slug = code.lower()
    team_cards.append(f"""      <a class="mv-team-card" href="team-{slug}.html">
        <div class="code">{code}</div>
        <div class="name">{name}</div>
        <div class="owners">{", ".join(owners)}</div>
        <div class="go">View Team &rarr;</div>
      </a>""")

teams_html = head("Teams", "teams.html") + f"""
    <div class="mv-page-header">
      <h1 class="mv-chrome-text">Teams</h1>
      <div class="sub">All {len(TEAMS)} franchises competing this season</div>
    </div>
    <div class="mv-team-grid">
{chr(10).join(team_cards)}
    </div>
""" + FOOT

with open("teams.html", "w") as f:
    f.write(teams_html)

# ---------------- team-<code>.html (shell pages) ----------------
for code, name, owners in TEAMS:
    slug = code.lower()
    page = head(name, "teams.html") + f"""
    <div class="mv-page-header">
      <h1 class="mv-chrome-text">{name}<span class="mv-badge">{code}</span></h1>
      <div class="sub">{", ".join(owners)}</div>
    </div>

    <div class="mv-stat-grid">
      <div class="mv-stat"><div class="label">Record</div><div class="value">0-0-0</div></div>
      <div class="mv-stat"><div class="label">Points</div><div class="value">0</div></div>
      <div class="mv-stat"><div class="label">League Rank</div><div class="value">&mdash;</div></div>
      <div class="mv-stat"><div class="label">Season Net</div><div class="value">$0.00</div></div>
    </div>

    <section class="card mv-card">
      <h2 class="mv-chrome-text">Roster</h2>
      <div class="sub">No games played yet this season</div>
      <div class="mv-empty">
        <div class="big">Roster not yet loaded</div>
        Check back once the season kicks off.
      </div>
    </section>

    <p style="margin-top:24px;"><a href="teams.html" style="color:var(--mv-ink-muted);font-size:13px;">&larr; Back to all teams</a></p>
""" + FOOT
    with open(f"team-{slug}.html", "w") as f:
        f.write(page)

# ---------------- financials.html ----------------
rollup_cards = "\n      ".join(
    f'<div class="mv-stat"><div class="label">{name}</div><div class="value">$0.00</div></div>'
    for _, name, _ in sorted(TEAMS, key=lambda t: t[1])
)

financials_html = head("Financials", "financials.html") + f"""
    <div class="mv-page-header">
      <h1 class="mv-chrome-text">Financials</h1>
      <div class="sub">Season net by team, followed by game-by-game detail. No games have been played yet this season.</div>
    </div>

    <div class="mv-stat-grid" style="grid-template-columns:repeat(auto-fit, minmax(160px,1fr));">
      {rollup_cards}
    </div>

    <section class="card mv-card">
      <h2 class="mv-chrome-text">Game Log</h2>
      <div class="sub">Modeled on the league schedule &mdash; week, matchup, stadium, attendance, gate receipts</div>
      <div class="mv-table-scroll">
        <table class="mv-table">
          <thead>
            <tr><th>Week</th><th>Home</th><th>Away</th><th>Stadium</th><th>Attendance</th><th>Gate Receipts</th></tr>
          </thead>
        </table>
      </div>
      <div class="mv-empty">
        <div class="big">No games played yet this season</div>
        Game-by-game financials will appear here once Week 1 kicks off.
      </div>
    </section>
""" + FOOT

with open("financials.html", "w") as f:
    f.write(financials_html)

print("done")
