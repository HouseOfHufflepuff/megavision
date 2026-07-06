"""
Repeatable roster + financials sync for the 13 MEGAVISION team pages.

Run it. That's it:

    python3 update_rosters.py            # fetch live, regenerate the 13 pages
    python3 update_rosters.py --push     # also git commit + push

Every run fetches the spreadsheet live over plain HTTP (it's shared "anyone
with the link can view", so no login/credential is needed) straight into
memory and parses it from there. Nothing is written to disk except the
regenerated team-<code>.html files. No caching, no temp files, no stored
copy of the spreadsheet, ever.
"""
import argparse
import subprocess
import sys

from common import TEAMS, head, foot, fetch_live_workbook, EXPORT_URL, fetch_trophy_room, tally_trophies

# 25/26 is over; only players actually signed for 26/27 count as current roster.
# Match by the literal column label, not position, since some teams' sheets
# (e.g. CRG) are still labeled a year behind (24/25-25/26-26/27 instead of
# 25/26-26/27-27/28) -- the label tells us which column is really 26/27.
CURRENT_SEASON_LABEL = "26/27"

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
TROPHY_ACCENTS = ["var(--mv-gold)", "var(--mv-blue)", "var(--mv-violet)", "var(--mv-pink)", "var(--mv-crimson)"]
trophy_color = {c: TROPHY_ACCENTS[i % len(TROPHY_ACCENTS)] for i, c in enumerate(comps)}

updated = []
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
    pos_summary = " &middot; ".join(f"{v} {k}" for k, v in sorted(pos_counts.items()) if k)
    season_net = -total_payroll  # no games/revenue yet this season

    y1_label, y2_label, y3_label = data["year_labels"]
    col_labels = [3, 4, 5]
    current_idx = col_labels.index(data["current_col"])
    year_th = [y1_label, y2_label, y3_label]
    year_th[current_idx] = f'<span style="color:var(--mv-gold)">{year_th[current_idx]}</span>'

    cap = data["capacity"]
    capacity_str = f"{cap:,.0f}" if isinstance(cap, (int, float)) else str(cap or "—")

    roster_rows = []
    for p in sorted(roster, key=lambda p: -p["current_salary"]):
        cells = [money(p["y1"]), money(p["y2"]), money(p["y3"])]
        cells[current_idx] = f'<strong style="color:var(--mv-gold)">{cells[current_idx]}</strong>'
        roster_rows.append(
            f'<tr><td>{p["player"]}</td><td>{p["pos"]}</td>'
            f'<td>{cells[0]}</td><td>{cells[1]}</td><td>{cells[2]}</td>'
            f'<td class="dim">{money(p["buyout"])}</td></tr>'
        )

    team_trophies = trophy_tally.get(code, {})
    total_trophies = sum(team_trophies.values())
    trophy_tiles = "\n      ".join(
        f'<div class="mv-stat"><div class="label">{c}</div>'
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
      <h2 class="mv-chrome-text">Roster</h2>
      <div class="sub">{roster_size} players signed for 26/27 &middot; {pos_summary} &middot; no games played yet this season</div>
      <div class="mv-table-scroll">
        <table class="mv-table">
          <thead><tr><th>Player</th><th>Pos</th><th>{year_th[0]}</th><th>{year_th[1]}</th><th>{year_th[2]}</th><th>BuyOut</th></tr></thead>
          <tbody>
            {"".join(roster_rows)}
          </tbody>
        </table>
      </div>
    </section>

    <p style="margin-top:24px;"><a href="teams.html" style="color:var(--mv-ink-muted);font-size:13px;">&larr; Back to all teams</a></p>
""" + foot()

    with open(f"team-{slug}.html", "w") as f:
        f.write(page)
    updated.append((code, roster_size, total_payroll))

print(f"Updated {len(updated)} team pages:")
for code, size, payroll in updated:
    print(f"  {code}: {size} players, ${payroll:,.2f} payroll")

if args.push:
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
