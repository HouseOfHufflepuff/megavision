from common import TEAMS, head, foot, hero_logo, fetch_live_workbook, fetch_trophy_room, resolve_team_code, fetch_stadiums

print("Fetching live spreadsheet...")
wb = fetch_live_workbook()
comps, seasons = fetch_trophy_room(wb)
stadiums = fetch_stadiums(wb)
print(f"Fetched. {len(seasons)} seasons of trophy history.")

total_titles = sum(1 for s in seasons for v in s[1:8] if v)
reigning = seasons[0][1] or "—"
reigning_code = resolve_team_code(reigning)

# poppy per-competition accents, cycling the guide's 5 named accents
ACCENTS = ["var(--mv-gold)", "var(--mv-blue)", "var(--mv-violet)", "var(--mv-pink)", "var(--mv-crimson)"]
comp_color = {comp: ACCENTS[i % len(ACCENTS)] for i, comp in enumerate(comps)}


def winner_cell(val, comp):
    if val == "—" or not val:
        return '<td class="dim">—</td>'
    code = resolve_team_code(val)
    color = comp_color[comp]
    label = f'<a href="team-{code.lower()}.html" style="color:{color};text-decoration:none;">{val}</a>' if code else f'<span style="color:{color};">{val}</span>'
    return f'<td style="font-weight:600;">{label}</td>'


# ---------------- index.html ----------------
rows_html = []
for i, s in enumerate(seasons):
    cells = [winner_cell(s[ci + 1] or "—", comp) for ci, comp in enumerate(comps)]
    row_style = ' style="background:rgba(255,209,102,0.06);"' if i == 0 else ""
    rows_html.append(f'<tr{row_style}><td style="font-weight:700;">{s[0]}</td>{"".join(cells)}</tr>')

headers_html = "".join(f'<th style="color:{comp_color[c]};">{c}</th>' for c in comps)
rows_joined = "\n            ".join(rows_html)

reigning_html = (
    f'<a href="team-{reigning_code.lower()}.html" style="color:inherit;text-decoration:none;">{reigning}</a>'
    if reigning_code else reigning
)

index_html = head("Home", "index.html") + f"""
    <header style="text-align:center;margin-bottom:36px;">
      <img src="logo-trim.png" alt="MEGAVISION" class="mv-glow" style="width:100%;max-width:640px;height:auto;">
      <p style="color:var(--mv-ink-muted);font-size:14px;letter-spacing:0.04em;margin-top:10px;">MEGA FANTASY SOCCER LEAGUE &nbsp;·&nbsp; EST. 2014</p>
    </header>

    <div class="mv-stat-grid">
      <div class="mv-stat"><div class="label">Seasons Played</div><div class="value mv-spark-text">{len(seasons)}</div></div>
      <div class="mv-stat"><div class="label">Titles Awarded</div><div class="value mv-spark-text">{total_titles}</div></div>
      <div class="mv-stat"><div class="label">Reigning Champion</div><div class="value mv-spark-text" style="font-size:17px;">{reigning_html}</div></div>
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

    <p style="text-align:center;margin-top:8px;">
      <a href="teams.html" style="color:var(--mv-violet);font-weight:600;font-size:14px;text-decoration:none;">View All {len(TEAMS)} Teams &rarr;</a>
    </p>
""" + foot()

with open("index.html", "w") as f:
    f.write(index_html)

# ---------------- teams.html ----------------
team_cards = []
for code, name, owners in TEAMS:
    slug = code.lower()
    stad = stadiums.get(code, {})
    cap = stad.get("capacity")
    cap_str = f"{cap:,.0f}" if isinstance(cap, (int, float)) else "—"
    stadium_line = f'{stad.get("stadium", "—")} &middot; Capacity {cap_str}'
    team_cards.append(f"""      <a class="mv-team-card" href="team-{slug}.html">
        <div class="code">{code}</div>
        <div class="name">{name}</div>
        <div class="owners">{", ".join(owners)}</div>
        <div class="owners" style="margin-top:4px;">{stadium_line}</div>
        <div class="go">View Team &rarr;</div>
      </a>""")

teams_html = head("Teams", "teams.html") + hero_logo() + f"""
    <div class="mv-page-header">
      <h1 class="mv-chrome-text">Teams</h1>
      <div class="sub">All {len(TEAMS)} franchises competing this season</div>
    </div>
    <div class="mv-team-grid">
{chr(10).join(team_cards)}
    </div>
""" + foot()

with open("teams.html", "w") as f:
    f.write(teams_html)

# financials.html is owned by update_rosters.py now (needs per-team payroll,
# fan, and trophy data that only that script computes) -- run that after this.

print("done: index.html, teams.html (run update_rosters.py for financials.html + team pages)")
