import json

d = json.load(open("_trophy_seasons.json"))
comps = d["comps"]
seasons = d["seasons"]  # most recent first

total_titles = sum(1 for s in seasons for v in s[1:8] if v)
reigning = seasons[0][1] or "—"

rows_html = []
for i, s in enumerate(seasons):
    is_latest = i == 0
    cells = []
    for ci, comp in enumerate(comps):
        val = s[ci + 1] or "—"
        cls = "empty" if val == "—" else ("champ" if comp == "Premium Title" else "")
        prefix = "🏆 " if comp == "Premium Title" and val != "—" else ""
        cells.append(f'<td class="{cls}">{prefix}{val}</td>')
    row_class = "latest" if is_latest else ""
    rows_html.append(f'<tr class="{row_class}"><td class="season">{s[0]}</td>{"".join(cells)}</tr>')

headers_html = "".join(f"<th>{c}</th>" for c in comps)
rows_joined = "\n          ".join(rows_html)

html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>MEGAVISION — Mega Fantasy League</title>
<style>
  :root {{
    --bg: #0a0a10;
    --panel: #13131b;
    --panel-2: #191922;
    --border: #26262f;
    --ink: #f2f1f7;
    --ink-muted: #8f8ca3;
    --gold: #f0b429;
    --violet: #9b6bff;
    --pink: #ff4fa3;
    --blue: #4fc3ff;
  }}
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0;
    background: radial-gradient(circle at 50% -10%, #1b1430 0%, var(--bg) 55%);
    color: var(--ink);
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
    -webkit-font-smoothing: antialiased;
  }}
  .wrap {{
    max-width: 980px;
    margin: 0 auto;
    padding: 48px 20px 80px;
  }}
  header {{
    text-align: center;
    margin-bottom: 40px;
  }}
  header img {{
    max-width: 380px;
    width: 70%;
    height: auto;
    filter: drop-shadow(0 0 40px rgba(155, 107, 255, 0.35));
  }}
  header p {{
    color: var(--ink-muted);
    font-size: 15px;
    letter-spacing: 0.04em;
    margin-top: 4px;
  }}
  .stats {{
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 14px;
    margin-bottom: 48px;
  }}
  .stat {{
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 18px 12px;
    text-align: center;
  }}
  .stat .label {{
    font-size: 11px;
    letter-spacing: 0.08em;
    color: var(--ink-muted);
    text-transform: uppercase;
    margin-bottom: 6px;
  }}
  .stat .value {{
    font-size: 26px;
    font-weight: 700;
    background: linear-gradient(90deg, var(--violet), var(--pink));
    -webkit-background-clip: text;
    background-clip: text;
    color: transparent;
  }}
  section.card {{
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 28px;
  }}
  section.card h2 {{
    margin: 0 0 4px;
    font-size: 20px;
  }}
  section.card .sub {{
    color: var(--ink-muted);
    font-size: 13px;
    margin-bottom: 20px;
  }}
  .table-scroll {{
    overflow-x: auto;
  }}
  table {{
    width: 100%;
    border-collapse: collapse;
    font-size: 13.5px;
    white-space: nowrap;
  }}
  thead th {{
    text-align: left;
    padding: 10px 12px;
    color: var(--ink-muted);
    font-size: 11px;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    border-bottom: 2px solid var(--border);
  }}
  thead th:first-child {{ border-bottom-color: var(--gold); }}
  tbody td {{
    padding: 10px 12px;
    border-bottom: 1px solid var(--border);
  }}
  tbody td.season {{
    font-weight: 700;
    color: var(--ink);
  }}
  tbody td.champ {{
    color: var(--gold);
    font-weight: 600;
  }}
  tbody td.empty {{
    color: #4a4854;
  }}
  tbody tr.latest {{
    background: rgba(240, 180, 41, 0.07);
  }}
  tbody tr:hover {{
    background: var(--panel-2);
  }}
  footer {{
    text-align: center;
    color: var(--ink-muted);
    font-size: 12px;
    margin-top: 32px;
  }}
</style>
</head>
<body>
  <div class="wrap">
    <header>
      <img src="logo.png" alt="MEGAVISION">
      <p>MEGA FANTASY SOCCER LEAGUE &nbsp;·&nbsp; EST. 2014</p>
    </header>

    <div class="stats">
      <div class="stat">
        <div class="label">Seasons Played</div>
        <div class="value">{len(seasons)}</div>
      </div>
      <div class="stat">
        <div class="label">Titles Awarded</div>
        <div class="value">{total_titles}</div>
      </div>
      <div class="stat">
        <div class="label">Reigning Champion</div>
        <div class="value" style="font-size:18px;">{reigning}</div>
      </div>
    </div>

    <section class="card">
      <h2>Hall of Champions</h2>
      <div class="sub">Every title the league has ever awarded, season by season</div>
      <div class="table-scroll">
        <table>
          <thead><tr><th>Season</th>{headers_html}</tr></thead>
          <tbody>
          {rows_joined}
          </tbody>
        </table>
      </div>
    </section>

    <footer>MEGAVISION &middot; Mega League Archive</footer>
  </div>
</body>
</html>
"""

with open("index.html", "w") as f:
    f.write(html)

print("wrote index.html,", len(html), "bytes")
