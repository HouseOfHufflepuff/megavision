"""
Repeatable roster + financials sync for the 13 MEGAVISION team pages.

Reads the roster/contract table out of each team tab in the master
spreadsheet (already exported to ../data/ss.xlsx) and regenerates
team-<code>.html for all 13 teams with current data.

Run:
    python3 update_rosters.py

Requires ../data/ss.xlsx to be present and reasonably fresh. That file is
a straight export of the Google Sheet and isn't something this script can
refresh itself (no standalone Google credential) -- ask Claude to
"refresh the spreadsheet data" first if you want the latest numbers, then
run this script, then git add/commit/push (or just ask Claude to do the
whole cycle).
"""
import subprocess
import sys
from pathlib import Path

import openpyxl

from common import TEAMS, head, FOOT

SS_PATH = Path("../data/ss.xlsx")

if not SS_PATH.exists():
    print(f"ERROR: {SS_PATH} not found. Fetch a fresh export of the spreadsheet first.", file=sys.stderr)
    sys.exit(1)


def parse_team_tab(ws):
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

    roster = []
    for r in rows[header_idx + 1:]:
        if r[0] == "Total":
            break
        if r[1] is None:
            continue
        roster.append({
            "player": r[1],
            "pos": r[2] or "",
            "y1": r[3],
            "y2": r[4],
            "y3": r[5],
            "buyout": r[6],
        })

    return {
        "stadium": stadium_name,
        "capacity": capacity,
        "year_labels": year_labels,
        "roster": roster,
    }


def money(v):
    if v is None:
        return "—"
    if isinstance(v, (int, float)):
        return f"${v:,.2f}"
    return str(v)


wb = openpyxl.load_workbook(str(SS_PATH), data_only=True)

updated = []
for code, name, owners in TEAMS:
    if code not in wb.sheetnames:
        print(f"WARN: no tab for {code}, skipping", file=sys.stderr)
        continue
    data = parse_team_tab(wb[code])
    if data is None:
        print(f"WARN: could not find roster header for {code}, skipping", file=sys.stderr)
        continue

    roster = data["roster"]
    roster_size = len(roster)
    total_payroll = sum(p["y1"] for p in roster if isinstance(p["y1"], (int, float)))
    pos_counts = {}
    for p in roster:
        pos_counts[p["pos"]] = pos_counts.get(p["pos"], 0) + 1
    pos_summary = " &middot; ".join(f"{v} {k}" for k, v in sorted(pos_counts.items()) if k)
    season_net = -total_payroll  # no games/revenue yet this season

    y1_label, y2_label, y3_label = data["year_labels"]
    cap = data["capacity"]
    capacity_str = f"{cap:,.0f}" if isinstance(cap, (int, float)) else str(cap or "—")
    roster_rows = []
    def sort_key(p):
        return -p["y1"] if isinstance(p["y1"], (int, float)) else 0

    for p in sorted(roster, key=sort_key):
        roster_rows.append(
            f'<tr><td>{p["player"]}</td><td>{p["pos"]}</td>'
            f'<td>{money(p["y1"])}</td><td>{money(p["y2"])}</td><td>{money(p["y3"])}</td>'
            f'<td class="dim">{money(p["buyout"])}</td></tr>'
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
      <h2 class="mv-chrome-text">Roster</h2>
      <div class="sub">{roster_size} players &middot; {pos_summary} &middot; no games played yet this season</div>
      <div class="mv-table-scroll">
        <table class="mv-table">
          <thead><tr><th>Player</th><th>Pos</th><th>{y1_label}</th><th>{y2_label}</th><th>{y3_label}</th><th>BuyOut</th></tr></thead>
          <tbody>
            {"".join(roster_rows)}
          </tbody>
        </table>
      </div>
    </section>

    <p style="margin-top:24px;"><a href="teams.html" style="color:var(--mv-ink-muted);font-size:13px;">&larr; Back to all teams</a></p>
""" + FOOT

    with open(f"team-{slug}.html", "w") as f:
        f.write(page)
    updated.append((code, roster_size, total_payroll))

print(f"Updated {len(updated)} team pages:")
for code, size, payroll in updated:
    print(f"  {code}: {size} players, ${payroll:,.2f} payroll")

if "--push" in sys.argv:
    files = [f"team-{c.lower()}.html" for c, _, _ in updated]
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
