"""
Repeatable roster + financials sync for all 13 MEGAVISION team pages plus
financials.html.

Run it. That's it:

    python3 update_rosters.py            # fetch live, regenerate the pages
    python3 update_rosters.py --push     # also git commit + push

Every run fetches the spreadsheet live over plain HTTP (it's shared "anyone
with the link can view", so no login/credential is needed) straight into
memory and parses it from there. Nothing is written to disk except the
regenerated *.html files. No caching, no temp files, no stored copy of the
spreadsheet, ever.
"""
import argparse
import subprocess
import sys

from common import (
    TEAMS, head, foot, fetch_live_workbook, EXPORT_URL, fetch_trophy_room,
    tally_trophies, COMP_ABBR, fetch_fans, owner_short, POSITION_ORDER,
    position_sort_key, fetch_youth,
)

STATUS_COLOR = {
    "Promoted": "var(--mv-gold)",
    "Released": "var(--mv-ink-dim)",
    "Frozen": "var(--mv-crimson)",
    "Active": "var(--mv-ink)",
}

# 25/26 is over; only players actually signed for 26/27 count as current roster.
# Match by the literal column label, not position, since some teams' sheets
# (e.g. CRG) are still labeled a year behind (24/25-25/26-26/27 instead of
# 25/26-26/27-27/28) -- the label tells us which column is really 26/27.
CURRENT_SEASON_LABEL = "26/27"

TROPHY_ACCENTS = ["var(--mv-gold)", "var(--mv-blue)", "var(--mv-violet)", "var(--mv-pink)", "var(--mv-crimson)"]

# league formation: 3-4-3 (+ 1 GK), field order top (attack) to bottom (GK)
FORMATION = [("F", 3), ("M", 4), ("D", 3), ("GK", 1)]

parser = argparse.ArgumentParser()
parser.add_argument("--push", action="store_true")
args = parser.parse_args()


def parse_team_tab(ws, code):
    rows = list(ws.iter_rows(min_row=1, max_row=40, values_only=True))
    stadium_name = rows[0][1] or ""
    capacity = rows[0][6]

    header_idx = None
    for i, r in enumerate(rows):
        if r[1] == "Player" and r[2] == "Pos":
            header_idx = i
            break
    if header_idx is None:
        return None

    year_labels = [rows[header_idx][3], rows[header_idx][4], rows[header_idx][5]]
    year_cols = [3, 4, 5]  # column indices in each row matching year_labels

    if CURRENT_SEASON_LABEL in year_labels:
        current_col = year_cols[year_labels.index(CURRENT_SEASON_LABEL)]
    else:
        print(f"WARN: {code} has no column labeled {CURRENT_SEASON_LABEL} "
              f"(got {year_labels}), falling back to the 2nd year column", file=sys.stderr)
        current_col = year_cols[1]

    roster = []
    for r in rows[header_idx + 1:]:
        if r[0] == "Total":
            break
        if r[1] is None:
            continue
        current_salary = r[current_col]
        if not isinstance(current_salary, (int, float)):
            continue  # not signed for 26/27, 25/26 is over -- drop them
        roster.append({
            "player": r[1],
            "pos": r[2] or "",
            "y1": r[3],
            "y2": r[4],
            "y3": r[5],
            "buyout": r[6],
            "current_salary": current_salary,
        })

    return {
        "stadium": stadium_name,
        "capacity": capacity,
        "year_labels": year_labels,
        "current_col": current_col,
        "roster": roster,
    }


def money(v):
    if v is None:
        return "—"
    if isinstance(v, (int, float)):
        return f"${v:,.2f}"
    return str(v)


print(f"Fetching live spreadsheet from {EXPORT_URL} ...")
wb = fetch_live_workbook()
print("Fetched. Parsing team tabs...")

comps, seasons = fetch_trophy_room(wb)
trophy_tally = tally_trophies(comps, seasons)
trophy_color = {c: TROPHY_ACCENTS[i % len(TROPHY_ACCENTS)] for i, c in enumerate(comps)}
fans_by_code = fetch_fans(wb)
youth_by_code = fetch_youth(wb)

updated = []
financial_rows = []

for code, name, owners in TEAMS:
    if code not in wb.sheetnames:
        print(f"WARN: no tab for {code}, skipping", file=sys.stderr)
        continue
    data = parse_team_tab(wb[code], code)
    if data is None:
        print(f"WARN: could not find roster header for {code}, skipping", file=sys.stderr)
        continue

    roster = data["roster"]
    roster_size = len(roster)
    total_payroll = sum(p["current_salary"] for p in roster)
    pos_counts = {}
    for p in roster:
        pos_counts[p["pos"]] = pos_counts.get(p["pos"], 0) + 1
    season_net = -total_payroll  # no games/revenue yet this season

    y1_label, y2_label, y3_label = data["year_labels"]
    col_labels = [3, 4, 5]
    current_idx = col_labels.index(data["current_col"])
    year_th = [y1_label, y2_label, y3_label]
    year_th[current_idx] = f'<span style="color:var(--mv-gold)">{year_th[current_idx]}</span>'

    cap = data["capacity"]
    capacity_str = f"{cap:,.0f}" if isinstance(cap, (int, float)) else str(cap or "—")

    # group by position (GK, D, M, F, then anything else), salary desc within group
    grouped = sorted(roster, key=lambda p: (position_sort_key(p["pos"]), -p["current_salary"]))

    roster_rows = []
    for p in grouped:
        cells = [money(p["y1"]), money(p["y2"]), money(p["y3"])]
        cells[current_idx] = f'<strong style="color:var(--mv-gold)">{cells[current_idx]}</strong>'
        roster_rows.append(
            f'<tr><td>{p["player"]}</td><td>{p["pos"]}</td>'
            f'<td>{cells[0]}</td><td>{cells[1]}</td><td>{cells[2]}</td>'
            f'<td class="dim">{money(p["buyout"])}</td></tr>'
        )

    # position-count summary row at the bottom of the table
    ordered_pos = [p for p in POSITION_ORDER if p in pos_counts] + \
                  [p for p in pos_counts if p not in POSITION_ORDER]
    counts_line = "  &middot;  ".join(f"{pos_counts[p]} {p}" for p in ordered_pos)
    roster_rows.append(
        f'<tr style="background:var(--mv-black-3);font-weight:700;">'
        f'<td colspan="6">{roster_size} total &middot; {counts_line}</td></tr>'
    )

    # ---- depth chart: 3-4-3, ranked by salary within each position ----
    by_pos = {pos: [p for p in grouped if p["pos"] == pos] for pos, _ in FORMATION}
    pitch_rows = []
    for pos, need in FORMATION:
        slots = []
        players = by_pos.get(pos, [])
        for i in range(need):
            if i < len(players):
                p = players[i]
                slots.append(
                    f'<div class="mv-slot"><div class="pos">{pos}</div>'
                    f'<div class="player">{p["player"]}</div>'
                    f'<div class="salary">{money(p["current_salary"])}</div></div>'
                )
            else:
                slots.append(f'<div class="mv-slot empty"><div class="pos">{pos}</div><div class="player">&mdash;</div></div>')
        pitch_rows.append(f'<div class="mv-pitch-row">{"".join(slots)}</div>')

    depth_groups = []
    for pos, need in FORMATION:
        bench = by_pos.get(pos, [])[need:]
        if not bench:
            continue
        items = "".join(
            f'<div class="mv-slot"><div class="pos">{pos}</div>'
            f'<div class="player">{p["player"]}</div>'
            f'<div class="salary">{money(p["current_salary"])}</div></div>'
            for p in bench
        )
        depth_groups.append(
            f'<div class="mv-depth-group"><div class="heading">{pos} Depth</div>'
            f'<div class="mv-pitch-row" style="justify-content:flex-start;">{items}</div></div>'
        )
    depth_html = "".join(depth_groups) or '<div class="mv-empty">No depth beyond the starting 3-4-3.</div>'

    # ---- youth ----
    youth = youth_by_code.get(code, [])
    youth_rows = "".join(
        f'<tr><td class="dim">{y["year"]}</td><td>{y["player"]}</td><td>{y["pos"]}</td>'
        f'<td>{y["age"] if y["age"] is not None else "—"}</td><td>{y["club"]}</td>'
        f'<td style="color:{STATUS_COLOR[y["status"]]};font-weight:600;">{y["status"]}</td></tr>'
        for y in youth
    )
    if not youth:
        youth_section = '<div class="mv-empty">No youth players drafted yet.</div>'
    else:
        youth_section = f"""<div class="mv-table-scroll">
        <table class="mv-table">
          <thead><tr><th>Draft</th><th>Player</th><th>Pos</th><th>Age</th><th>Club</th><th>Status</th></tr></thead>
          <tbody>{youth_rows}</tbody>
        </table>
      </div>"""

    team_trophies = trophy_tally.get(code, {})
    total_trophies = sum(team_trophies.values())
    trophy_tiles = "\n      ".join(
        f'<div class="mv-stat"><div class="label">{COMP_ABBR.get(c, c)}</div>'
        f'<div class="value" style="color:{trophy_color[c]};">{team_trophies.get(c, 0)}</div></div>'
        for c in comps
    )

    slug = code.lower()
    page = head(name, "teams.html") + f"""
    <div class="mv-page-header">
      <h1 class="mv-chrome-text">{name}<span class="mv-badge">{code}</span></h1>
      <div class="sub">{", ".join(owners)} &middot; {data["stadium"]} (Capacity {capacity_str})</div>
    </div>

    <div class="mv-stat-grid">
      <div class="mv-stat"><div class="label">Record</div><div class="value">0-0-0</div></div>
      <div class="mv-stat"><div class="label">Points</div><div class="value">0</div></div>
      <div class="mv-stat"><div class="label">League Rank</div><div class="value">&mdash;</div></div>
      <div class="mv-stat"><div class="label">Roster Size</div><div class="value">{roster_size}</div></div>
      <div class="mv-stat"><div class="label">Total Payroll</div><div class="value">{money(total_payroll)}</div></div>
      <div class="mv-stat"><div class="label">Season Net</div><div class="value">{money(season_net)}</div></div>
    </div>

    <section class="card mv-card">
      <h2 class="mv-chrome-text">Trophy Case</h2>
      <div class="sub">{total_trophies} title{"s" if total_trophies != 1 else ""} all-time</div>
      <div class="mv-stat-grid" style="grid-template-columns:repeat(auto-fit, minmax(120px,1fr));">
      {trophy_tiles}
      </div>
    </section>

    <section class="card mv-card">
      <div class="mv-tabs">
        <button class="mv-tab active" onclick="mvShowTab(this,'roster-{code}')">Roster</button>
        <button class="mv-tab" onclick="mvShowTab(this,'depth-{code}')">Depth Chart</button>
      </div>

      <div id="roster-{code}" class="mv-tab-panel active">
        <div class="sub">{roster_size} players signed for 26/27, grouped by position &middot; no games played yet this season</div>
        <div class="mv-table-scroll">
          <table class="mv-table">
            <thead><tr><th>Player</th><th>Pos</th><th>{year_th[0]}</th><th>{year_th[1]}</th><th>{year_th[2]}</th><th>BuyOut</th></tr></thead>
            <tbody>
              {"".join(roster_rows)}
            </tbody>
          </table>
        </div>
      </div>

      <div id="depth-{code}" class="mv-tab-panel">
        <div class="sub">League formation 3-4-3, ranked by salary at each position</div>
        <div class="mv-pitch">
          {"".join(pitch_rows)}
        </div>
        {depth_html}
      </div>
    </section>

    <section class="card mv-card">
      <h2 class="mv-chrome-text">Youth</h2>
      <div class="sub">{len(youth)} player{"s" if len(youth) != 1 else ""} drafted all-time</div>
      {youth_section}
    </section>

    <p style="margin-top:24px;"><a href="teams.html" style="color:var(--mv-ink-muted);font-size:13px;">&larr; Back to all teams</a></p>
""" + foot()

    with open(f"team-{slug}.html", "w") as f:
        f.write(page)
    updated.append((code, roster_size, total_payroll))
    financial_rows.append({
        "code": code,
        "name": name,
        "owner": owner_short(owners),
        "cost": total_payroll,
        "revenue": 0.0,
        "fans": fans_by_code.get(code),
        "trophies": total_trophies,
    })

print(f"Updated {len(updated)} team pages:")
for code, size, payroll in updated:
    print(f"  {code}: {size} players, ${payroll:,.2f} payroll")

# ---------------- financials.html ----------------
financial_rows.sort(key=lambda r: -r["cost"])

def fmt_fans(v):
    return f"{v:,.0f}" if isinstance(v, (int, float)) else "—"

fin_table_rows = "\n            ".join(
    f'<tr><td><a href="team-{r["code"].lower()}.html" style="color:inherit;text-decoration:none;font-weight:600;">{r["name"]}</a></td>'
    f'<td class="dim">{r["owner"]}</td>'
    f'<td>{money(r["cost"])}</td>'
    f'<td>{money(r["revenue"])}</td>'
    f'<td>{fmt_fans(r["fans"])}</td>'
    f'<td>{r["trophies"]}</td></tr>'
    for r in financial_rows
)

financials_html = head("Financials", "financials.html") + f"""
    <div class="mv-page-header">
      <h1 class="mv-chrome-text">Financials</h1>
      <div class="sub">Cost and revenue by team for 26/27, followed by game-by-game detail. No games have been played yet this season.</div>
    </div>

    <section class="card mv-card">
      <div class="mv-table-scroll">
        <table class="mv-table">
          <thead><tr><th>Team</th><th>Owner</th><th>Cost</th><th>Revenue</th><th>Fans</th><th># Trophies</th></tr></thead>
          <tbody>
            {fin_table_rows}
          </tbody>
        </table>
      </div>
    </section>

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
""" + foot()

with open("financials.html", "w") as f:
    f.write(financials_html)
print("Updated financials.html")

if args.push:
    files = [f"team-{c.lower()}.html" for c, _, _ in updated] + ["financials.html"]
    subprocess.run(["git", "add"] + files, check=True)
    result = subprocess.run(["git", "diff", "--cached", "--quiet"])
    if result.returncode == 0:
        print("No changes to publish.")
    else:
        subprocess.run(
            ["git", "-c", "user.email=ahrens@gmail.com", "-c", "user.name=Jeremy Ahrens",
             "commit", "-q", "-m", "Update team rosters and financials from spreadsheet"],
            check=True,
        )
        subprocess.run(["git", "push", "-q"], check=True)
        print("Pushed to GitHub Pages.")
