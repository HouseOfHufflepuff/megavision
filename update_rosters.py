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
import re
import subprocess
import sys

from common import (
    TEAMS, head, foot, hero_logo, fetch_live_workbook, EXPORT_URL, fetch_trophy_room,
    tally_trophies, COMP_ABBR, fetch_fans, owner_short, POSITION_ORDER,
    position_sort_key, fetch_youth, find_team_sheet, fetch_all_season_labels,
    fetch_season_salary_totals, fetch_league_schedule_games, fetch_standings_reference,
    fetch_firm_legacy, compute_fan_formula, fetch_stadiums,
)
from player_clean import clean_player

CURRENT_SALARY_SEASON = "25/26"

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
stadiums = fetch_stadiums(wb)
rank_bonus, points_bonus_table = fetch_standings_reference(wb)
firm_legacy = fetch_firm_legacy(wb)

# Live Fantrax fantasy points, used to rank the depth chart within each
# position and as the "rating" column on teams.html. (EA FC 26 ratings were
# the original plan, but EA's own site, sofifa.com, and futwiz.com all
# explicitly disallow ClaudeBot in robots.txt -- sofifa names it directly on
# the exact player-page pattern -- so that source is off the table. Real live
# Fantrax scoring is used instead.) Also feeds the Fan Formula below.
print("Fetching live Fantrax rosters (for depth-chart ranking + Fan Formula)...")
try:
    import fantrax_live
    _fx_sess = fantrax_live._session()
    fantrax_standings = fantrax_live.fetch_standings(_fx_sess)
    fantrax_rosters = fantrax_live.fetch_all_rosters(_fx_sess)
    top_xi, mbp = fantrax_live.compute_top_xi(fantrax_rosters)
    fan_formula = compute_fan_formula(rank_bonus, points_bonus_table, firm_legacy, fantrax_standings, top_xi, mbp)
except Exception as e:
    print(f"WARN: live Fantrax fetch failed ({e}); depth charts fall back to salary order, "
          f"Fan Formula/teams-table ratings will be omitted", file=sys.stderr)
    fantrax_standings, fantrax_rosters, top_xi, mbp, fan_formula = {}, {}, [], None, {}


def fpts_lookup(code):
    """last-name (lowercase) -> fantasy points, for this team's live Fantrax
    roster. Matched against the sheet's raw player field via clean_player()
    since the two sources spell/format names differently."""
    roster = fantrax_rosters.get(code, [])
    return {p["name"].split()[-1].lower(): p["fpts"] for p in roster}


# Global (all-teams) last-name -> fpts, for matching YOUTH players, who
# often aren't on their own Mega team's active Fantrax roster (unpromoted
# prospects, loans, etc.) but may show up on any of the 13 live rosters.
global_fpts_lookup = {}
for _roster in fantrax_rosters.values():
    for _p in _roster:
        global_fpts_lookup[_p["name"].split()[-1].lower()] = _p["fpts"]

team_wins = {}
for _code, _s in fantrax_standings.items():
    try:
        team_wins[_code] = int(_s["record"].split("-")[0])
    except (ValueError, IndexError, AttributeError):
        team_wins[_code] = None

# EA FC 26 overall ratings, read from mega.db (populated by the separate
# sync_fc26_ratings.py script -- run that periodically, it's not fetched
# live on every site build). last name (lower) -> rating.
global_fc26_lookup = {}
try:
    import db as _db
    _conn = _db.connect()
    for _pname, _rating in _conn.execute(
        "SELECT player_name, fc26_rating FROM team_players WHERE fc26_rating IS NOT NULL"
    ):
        if _pname:
            global_fc26_lookup[_pname.split()[-1].lower()] = _rating
    _conn.close()
    print(f"Loaded {len(global_fc26_lookup)} FC 26 ratings from mega.db "
          f"(run sync_fc26_ratings.py to refresh).")
except Exception as e:
    print(f"WARN: could not read FC 26 ratings from mega.db ({e}); "
          f"ratings will fall back to live Fantrax fantasy points", file=sys.stderr)

updated = []
financial_rows = []

for code, name, owners in TEAMS:
    sheet_name = find_team_sheet(wb, code)
    if sheet_name is None:
        print(f"WARN: no tab for {code}, skipping", file=sys.stderr)
        continue
    if sheet_name != code:
        print(f"NOTE: {code} tab is now named '{sheet_name}' in the live sheet", file=sys.stderr)
    data = parse_team_tab(wb[sheet_name], code)
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
    # salary summed by contract year, across the WHOLE roster (not just the
    # current-season column) -- players not signed for a given year contribute 0
    year_totals = [
        sum(p[key] for p in roster if isinstance(p[key], (int, float)))
        for key in ("y1", "y2", "y3")
    ]
    col_labels = [3, 4, 5]
    current_idx = col_labels.index(data["current_col"])
    year_th = [y1_label, y2_label, y3_label]
    year_th[current_idx] = f'<span style="color:var(--mv-gold)">{year_th[current_idx]}</span>'

    cap = data["capacity"]
    capacity_str = f"{cap:,.0f}" if isinstance(cap, (int, float)) else str(cap or "—")

    # ---- youth cross-reference: flag roster/depth players this team drafted ----
    youth = youth_by_code.get(code, [])
    youth_last_names = {
        parts[-1].lower()
        for y in youth
        for parts in [y["player"].replace(".", " ").split()]
        if parts and len(parts[-1]) >= 3
    }

    def is_youth_product(player_field):
        core = player_field.split(" - ")[0]
        tokens = set(re.split(r"[^a-zA-Z]+", core.lower())) - {""}
        return bool(tokens & youth_last_names)

    YOUTH_MARK = '<span title="Youth product" style="display:inline-block;width:8px;height:8px;border-radius:50%;background:var(--mv-blue);margin-right:5px;"></span>'

    def player_label(p):
        return (YOUTH_MARK if is_youth_product(p["player"]) else "") + p["player"]

    # ---- live Fantrax fantasy points + FC 26 rating per player, matched by
    # cleaned last name ----
    team_fpts = fpts_lookup(code)
    for p in roster:
        cleaned = clean_player(p["player"], p["pos"])
        last = (cleaned["player_name"] or "").split()[-1].lower() if cleaned["player_name"] else ""
        p["fpts"] = team_fpts.get(last)
        p["fc26"] = global_fc26_lookup.get(last)
    _matched_fpts = [p["fpts"] for p in roster if isinstance(p["fpts"], (int, float))]
    avg_fpts = (sum(_matched_fpts) / len(_matched_fpts)) if _matched_fpts else None
    _matched_fc26 = [p["fc26"] for p in roster if isinstance(p["fc26"], (int, float))]
    avg_fc26 = (sum(_matched_fc26) / len(_matched_fc26)) if _matched_fc26 else None

    # group by position (GK, D, M, F, then anything else), salary desc within group
    grouped = sorted(roster, key=lambda p: (position_sort_key(p["pos"]), -p["current_salary"]))

    roster_rows = []
    for p in grouped:
        cells = [money(p["y1"]), money(p["y2"]), money(p["y3"])]
        cells[current_idx] = f'<strong style="color:var(--mv-gold)">{cells[current_idx]}</strong>'
        roster_rows.append(
            f'<tr><td>{player_label(p)}</td><td>{p["pos"]}</td>'
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

    # ---- depth chart: 3-4-3, ranked by EA FC 26 overall rating within each
    # position (falls back to live Fantrax fantasy points, then salary, for
    # players with no FC 26 match) ----
    depth_sorted = sorted(
        roster,
        key=lambda p: (position_sort_key(p["pos"]), -(p["fc26"] or -1), -(p["fpts"] or -1), -p["current_salary"]),
    )
    by_pos = {pos: [p for p in depth_sorted if p["pos"] == pos] for pos, _ in FORMATION}

    def rating_label(p):
        return f'{p["fc26"]:,.0f} OVR' if isinstance(p["fc26"], (int, float)) else "— OVR"

    def fpts_label(p):
        return f'{p["fpts"]:,.1f} pts' if isinstance(p["fpts"], (int, float)) else "— pts"

    pitch_rows = []
    for pos, need in FORMATION:
        slots = []
        players = by_pos.get(pos, [])
        for i in range(need):
            if i < len(players):
                p = players[i]
                slots.append(
                    f'<div class="mv-slot"><div class="pos">{pos}</div>'
                    f'<div class="player">{player_label(p)}</div>'
                    f'<div class="salary" style="color:var(--mv-gold);font-weight:700;">{rating_label(p)}</div>'
                    f'<div class="salary dim">{fpts_label(p)}</div>'
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
            f'<div class="player">{player_label(p)}</div>'
            f'<div class="salary" style="color:var(--mv-gold);font-weight:700;">{rating_label(p)}</div>'
            f'<div class="salary dim">{fpts_label(p)}</div>'
            f'<div class="salary">{money(p["current_salary"])}</div></div>'
            for p in bench
        )
        depth_groups.append(
            f'<div class="mv-depth-group"><div class="heading">{pos} Depth</div>'
            f'<div class="mv-pitch-row" style="justify-content:flex-start;">{items}</div></div>'
        )
    depth_html = "".join(depth_groups) or '<div class="mv-empty">No depth beyond the starting 3-4-3.</div>'

    # ---- youth: rating (EA FC 26, falling back to live Fantrax fpts),
    # matched league-wide since a youth player may not be on this team's own
    # active Fantrax roster ----
    for y in youth:
        cleaned = clean_player(y["player"], y["pos"])
        last = (cleaned["player_name"] or "").split()[-1].lower() if cleaned["player_name"] else ""
        y["fc26"] = global_fc26_lookup.get(last)
        y["fpts"] = global_fpts_lookup.get(last)

    # ---- youth depth chart, now folded directly into the Youth section: ----
    # every player this team has ever drafted, grouped by position, ranked
    # by live rating within each group (all-time, not just current roster) ----
    youth_by_pos = {}
    for y in youth:
        youth_by_pos.setdefault(y["pos"].upper(), []).append(y)
    youth_pos_order = [p for p in POSITION_ORDER if p in youth_by_pos] + \
                       [p for p in youth_by_pos if p not in POSITION_ORDER]

    def rating_pts_label(fc26, fpts):
        primary = f'{fc26:,.0f} OVR' if isinstance(fc26, (int, float)) else '— OVR'
        secondary = f'{fpts:,.1f} pts' if isinstance(fpts, (int, float)) else '— pts'
        return primary, secondary

    def rating_plain_label(fc26):
        return f'{fc26:,.0f}' if isinstance(fc26, (int, float)) else '—'

    youth_pitch_groups = []
    for pos in youth_pos_order:
        players = sorted(
            youth_by_pos[pos],
            key=lambda y: (-(y["fc26"] if isinstance(y["fc26"], (int, float)) else -1),
                            -(y["fpts"] if isinstance(y["fpts"], (int, float)) else -1)),
        )
        items = "".join(
            f'<div class="mv-slot"><div class="pos">{pos}</div>'
            f'<div class="player">{y["player"]}</div>'
            f'<div class="salary" style="color:var(--mv-gold);font-weight:700;">{rating_pts_label(y["fc26"], y["fpts"])[0]}</div>'
            f'<div class="salary dim">{rating_pts_label(y["fc26"], y["fpts"])[1]}</div>'
            f'<div class="salary" style="color:{STATUS_COLOR[y["status"]]};">{y["status"]}</div></div>'
            for y in players
        )
        youth_pitch_groups.append(
            f'<div class="mv-depth-group"><div class="heading">{pos} &middot; {len(players)} &middot; ranked by rating</div>'
            f'<div class="mv-pitch-row" style="justify-content:flex-start;">{items}</div></div>'
        )
    youth_depth_html = "".join(youth_pitch_groups) or '<div class="mv-empty">No youth players drafted yet.</div>'

    # ---- youth table (the cross-reference set was already built above) ----
    youth_rows = "".join(
        f'<tr><td class="dim">{y["year"]}</td><td>{y["player"]}</td><td>{y["pos"]}</td>'
        f'<td>{y["age"] if y["age"] is not None else "—"}</td><td>{y["club"]}</td>'
        f'<td>{rating_plain_label(y["fc26"])}</td>'
        f'<td style="color:{STATUS_COLOR[y["status"]]};font-weight:600;">{y["status"]}</td></tr>'
        for y in youth
    )
    if not youth:
        youth_section = '<div class="mv-empty">No youth players drafted yet.</div>'
    else:
        youth_section = f"""<div class="mv-depth-group-wrap">{youth_depth_html}</div>
      <div class="mv-table-scroll" style="margin-top:18px;">
        <table class="mv-table">
          <thead><tr><th>Draft</th><th>Player</th><th>Pos</th><th>Age</th><th>Club</th><th>Rating</th><th>Status</th></tr></thead>
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
    page = head(name, "teams.html") + hero_logo() + f"""
    <div class="mv-page-header">
      <h1 class="mv-chrome-text">{name}<span class="mv-badge">{code}</span></h1>
      <div class="sub">{owner_short(owners)} &middot; {data["stadium"]} (Capacity {capacity_str})</div>
    </div>

    <div class="mv-stat-grid">
      <div class="mv-stat"><div class="label">Record</div><div class="value">0-0-0</div></div>
      <div class="mv-stat"><div class="label">Points</div><div class="value">0</div></div>
      <div class="mv-stat"><div class="label">League Rank</div><div class="value">&mdash;</div></div>
      <div class="mv-stat"><div class="label">Roster Size</div><div class="value">{roster_size}</div></div>
      <div class="mv-stat"><div class="label">Total Payroll</div><div class="value">{money(total_payroll)}</div></div>
      <div class="mv-stat"><div class="label">Season Net</div><div class="value">{money(season_net)}</div></div>
    </div>

    <div class="mv-stat-grid" style="grid-template-columns:repeat(auto-fit, minmax(120px,1fr));margin-top:10px;">
      {"".join(
          f'<div class="mv-stat"><div class="label">{lbl} Payroll</div><div class="value" style="font-size:18px;">{money(tot)}</div></div>'
          for lbl, tot in zip((y1_label, y2_label, y3_label), year_totals) if lbl
      )}
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
      <div style="font-size:11px;color:var(--mv-ink-muted);margin-bottom:14px;display:flex;align-items:center;gap:6px;">
        <span style="display:inline-block;width:8px;height:8px;border-radius:50%;background:var(--mv-blue);"></span>
        this team's own youth draft product &middot; Depth Chart is ranked by EA FC 26 overall rating (Fantrax fantasy points as fallback/tiebreak)
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
        <div class="sub">League formation 3-4-3, ranked by EA FC 26 overall rating at each position</div>
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
        "fans": fan_formula.get(code, {}).get("total", fans_by_code.get(code)),
        "trophies": total_trophies,
        "avg_fc26": avg_fc26,
        "avg_fpts": avg_fpts,
        "wins": team_wins.get(code),
        "capacity": stadiums.get(code, {}).get("capacity"),
        "stadium": stadiums.get(code, {}).get("stadium"),
    })

print(f"Updated {len(updated)} team pages:")
for code, size, payroll in updated:
    print(f"  {code}: {size} players, ${payroll:,.2f} payroll")

# ---------------- teams.html: sortable table ----------------
def fmt_num(v, decimals=0):
    return f"{v:,.{decimals}f}" if isinstance(v, (int, float)) else "—"

teams_table_rows = "\n            ".join(
    f'<tr>'
    f'<td data-sort="{r["name"]}"><a href="team-{r["code"].lower()}.html" style="color:inherit;text-decoration:none;font-weight:600;">{r["name"]}</a> '
    f'<span class="dim">{r["code"]}</span></td>'
    f'<td class="dim">{r["owner"]}</td>'
    f'<td data-sort="{r["fans"] if isinstance(r["fans"], (int, float)) else -1}">{fmt_num(r["fans"])}</td>'
    f'<td data-sort="{r["capacity"] if isinstance(r["capacity"], (int, float)) else -1}">{fmt_num(r["capacity"])}</td>'
    f'<td data-sort="{r["wins"] if isinstance(r["wins"], (int, float)) else -1}">{fmt_num(r["wins"])}</td>'
    f'<td data-sort="{r["trophies"]}">{r["trophies"]}</td>'
    f'<td data-sort="{r["avg_fc26"] if isinstance(r["avg_fc26"], (int, float)) else -1}">{fmt_num(r["avg_fc26"], 1)}</td>'
    f'</tr>'
    for r in financial_rows
)

teams_html = head("Teams", "teams.html") + hero_logo() + f"""
    <div class="mv-page-header">
      <h1 class="mv-chrome-text">Teams</h1>
      <div class="sub">All {len(TEAMS)} franchises &middot; click a column to sort &middot; Rating is each roster's average EA FC 26 overall rating</div>
    </div>

    <section class="card mv-card">
      <div class="mv-table-scroll">
        <table class="mv-table mv-sortable" id="teamsTable">
          <thead>
            <tr>
              <th data-sort-type="text">Team</th>
              <th>Owner</th>
              <th data-sort-type="num">Fans &#9650;&#9660;</th>
              <th data-sort-type="num">Capacity &#9650;&#9660;</th>
              <th data-sort-type="num">Wins &#9650;&#9660;</th>
              <th data-sort-type="num"># Trophies &#9650;&#9660;</th>
              <th data-sort-type="num">Avg FC 26 Rating &#9650;&#9660;</th>
            </tr>
          </thead>
          <tbody>
            {teams_table_rows}
          </tbody>
        </table>
      </div>
      <p style="font-size:11px;color:var(--mv-ink-muted);margin-top:10px;">
        &ldquo;Avg FC 26 Rating&rdquo; is each team's average EA Sports FC 26 overall rating across matched
        roster players (source: a community CSV mirror of the FC 26 database on GitHub, since EA's own site,
        sofifa.com, and futwiz.com all explicitly disallow ClaudeBot in robots.txt). Run
        <code>sync_fc26_ratings.py</code> to refresh the ratings in the local database this reads from.
      </p>
    </section>

    <script>
      (function() {{
        var table = document.getElementById('teamsTable');
        var headers = table.querySelectorAll('th');
        var tbody = table.querySelector('tbody');
        headers.forEach(function(th, idx) {{
          th.style.cursor = 'pointer';
          var dir = 1;
          th.addEventListener('click', function() {{
            var rows = Array.from(tbody.querySelectorAll('tr'));
            var type = th.dataset.sortType;
            rows.sort(function(a, b) {{
              var av = a.children[idx].dataset.sort || a.children[idx].textContent.trim();
              var bv = b.children[idx].dataset.sort || b.children[idx].textContent.trim();
              if (type === 'num') {{ av = parseFloat(av); bv = parseFloat(bv); }}
              if (av < bv) return -1 * dir;
              if (av > bv) return 1 * dir;
              return 0;
            }});
            dir *= -1;
            rows.forEach(function(r) {{ tbody.appendChild(r); }});
          }});
        }});
      }})();
    </script>
""" + foot()

with open("teams.html", "w") as f:
    f.write(teams_html)
print("Updated teams.html")

# ---------------- financials.html ----------------
team_meta = {r["code"]: r for r in financial_rows}  # code -> {name, owner, trophies, ...}

season_labels = fetch_all_season_labels(wb)
salary_by_season = {label: fetch_season_salary_totals(wb, label) for label in season_labels}
games = fetch_league_schedule_games(wb)  # weeks 1-22, 25/26 season
# rank_bonus / firm_legacy / fantrax_standings / top_xi / mbp / fan_formula
# were already fetched near the top of the script (shared with the depth
# chart and the new teams.html table).

# per-team game aggregates for the 25/26 summary (derived from `games`, not tracked separately)
games_by_team = {code: [] for code, _, _ in TEAMS}
for g in games:
    games_by_team[g["home"]].append((g, "home"))
    games_by_team[g["away"]].append((g, "away"))


def fmt_fans(v):
    return f"{v:,.0f}" if isinstance(v, (int, float)) else "—"


def season_summary_rows(label):
    salaries = salary_by_season.get(label, {})
    rows = []
    for code, _, _ in TEAMS:
        meta = team_meta.get(code)
        if meta is None:
            continue
        team_games = games_by_team.get(code, []) if label == CURRENT_SALARY_SEASON else []
        gp = len(team_games)
        revenue = sum(g["home_rev"] if side == "home" else g["away_rev"] for g, side in team_games)
        season_payroll = salaries.get(code)
        cost = (season_payroll / 22 * gp) if isinstance(season_payroll, (int, float)) and gp else season_payroll
        fans = fan_formula.get(code, {}).get("total") if label == CURRENT_SALARY_SEASON else fans_by_code.get(code)
        rows.append({
            "code": code, "name": meta["name"], "owner": meta["owner"], "trophies": meta["trophies"],
            "games": gp, "cost": cost, "revenue": revenue if gp else None, "fans": fans,
        })
    rows.sort(key=lambda r: -(r["cost"] or 0))
    return rows


def render_summary_table(label, rows, show_games_col):
    header = "<th>Team</th><th>Owner</th>"
    if show_games_col:
        header += "<th>GP</th><th>Cost</th><th>Revenue</th><th>Net</th><th>Fans</th><th># Trophies</th>"
    else:
        header += f"<th>{label} Salary Cost</th><th># Trophies</th>"
    body_rows = []
    for r in rows:
        cells = (
            f'<td><a href="team-{r["code"].lower()}.html" style="color:inherit;text-decoration:none;font-weight:600;">{r["name"]}</a></td>'
            f'<td class="dim">{r["owner"]}</td>'
        )
        if show_games_col:
            net = (r["revenue"] - r["cost"]) if isinstance(r["revenue"], (int, float)) and isinstance(r["cost"], (int, float)) else None
            cells += (
                f'<td>{r["games"]}</td><td>{money(r["cost"])}</td><td>{money(r["revenue"])}</td>'
                f'<td>{money(net)}</td><td>{fmt_fans(r["fans"])}</td><td>{r["trophies"]}</td>'
            )
        else:
            cells += f'<td>{money(r["cost"])}</td><td>{r["trophies"]}</td>'
        body_rows.append(f"<tr>{cells}</tr>")
    return f"""<table class="mv-table">
          <thead><tr>{header}</tr></thead>
          <tbody>
            {"\n            ".join(body_rows)}
          </tbody>
        </table>"""


def render_games_table(label):
    if label != CURRENT_SALARY_SEASON:
        return ""
    body_rows = []
    for g in sorted(games, key=lambda g: (g["week"], g["home"])):
        cap = f'{g["capacity"]:,.0f}' if isinstance(g["capacity"], (int, float)) else "—"
        body_rows.append(
            f'<tr><td>{g["week"]}</td>'
            f'<td><a href="team-{g["home"].lower()}.html" style="color:inherit;font-weight:600;">{g["home"]}</a></td>'
            f'<td><a href="team-{g["away"].lower()}.html" style="color:inherit;font-weight:600;">{g["away"]}</a></td>'
            f'<td class="dim">{g["stadium"] or "—"}</td>'
            f'<td>{cap}</td>'
            f'<td>{fmt_fans(g["home_int"])} / {fmt_fans(g["away_int"])}</td>'
            f'<td>{fmt_fans(g["attendance"])}</td>'
            f'<td>{money(g["gate_receipts"])}</td>'
            f'<td>{money(g["home_rev"])}</td>'
            f'<td>{money(g["away_rev"])}</td></tr>'
        )
    return f"""
    <section class="card mv-card">
      <h2 class="mv-chrome-text">{label} Game Log</h2>
      <div class="sub">Every fixture from the league schedule &mdash; fan interest, attendance (capacity-capped), gate receipts, and the 80/20 home/away revenue split</div>
      <div class="mv-table-scroll">
        <table class="mv-table">
          <thead><tr><th>Wk</th><th>Home</th><th>Away</th><th>Stadium</th><th>Capacity</th><th>Fan Int (H/A)</th><th>Attendance</th><th>Gate Receipts</th><th>Home Rev</th><th>Away Rev</th></tr></thead>
          <tbody>
            {"\n            ".join(body_rows)}
          </tbody>
        </table>
      </div>
    </section>"""


def render_fan_formula_section(label):
    if label != CURRENT_SALARY_SEASON or not fan_formula:
        return ""
    breakdown_rows = "\n            ".join(
        f'<tr><td><a href="team-{code.lower()}.html" style="color:inherit;font-weight:600;">{code}</a></td>'
        f'<td>{f["standings"]:,.0f}</td><td>{f["firm_legacy"]:,.0f}</td>'
        f'<td>{f["top_xi"]:,.0f} <span class="dim">({f["xi_count"]})</span></td>'
        f'<td>{f["mbp"]:,.0f}</td><td>{f["points_bonus"]:,.0f}</td>'
        f'<td style="font-weight:700;color:var(--mv-gold);">{f["total"]:,.0f}</td></tr>'
        for code, f in sorted(fan_formula.items(), key=lambda kv: -kv[1]["total"])
    )
    xi_rows = "\n            ".join(
        f'<tr><td>{p["pos"]}</td><td>{p["name"]}</td>'
        f'<td><a href="team-{p["code"].lower()}.html" style="color:inherit;font-weight:600;">{p["code"]}</a></td>'
        f'<td>{p["fpts"]:,.1f}</td></tr>'
        for p in top_xi
    )
    mbp_line = f'{mbp["name"]} ({mbp["code"]}, {mbp["fpts"]:,.1f} pts)' if mbp else "—"
    return f"""
    <section class="card mv-card">
      <h2 class="mv-chrome-text">The Fan Formula</h2>
      <div class="sub">How each team's final {CURRENT_SALARY_SEASON} fan count is built, live from the league sheet and Fantrax</div>
      <p style="font-size:13px;line-height:1.7;color:var(--mv-ink-muted);">
        <b style="color:var(--mv-ink);">Fans = Standings + Firm&amp;Legacy + Top&nbsp;XI + MBP + Points&nbsp;Bonus</b><br>
        &middot; <b>Standings</b>: tiered by live Fantrax rank (1st = 220 fans down to 12th = 25)<br>
        &middot; <b>Firm + Legacy</b>: career/trophy legacy value, from the league sheet<br>
        &middot; <b>Top XI</b>: 20 fans per player a team owns in the league's real live Top XI (1 GK / 3 D / 4 M / 3 F, ranked by actual Fantrax fantasy points)<br>
        &middot; <b>MBP</b>: 50 fans for owning the single highest-scoring player in the league &mdash; currently <b style="color:var(--mv-ink);">{mbp_line}</b><br>
        &middot; <b>Points Bonus</b>: fixed bonus for the top 5 teams by season points, from the league sheet
      </p>
      <div class="mv-table-scroll">
        <table class="mv-table">
          <thead><tr><th>Team</th><th>Standings</th><th>Legacy</th><th>Top XI (#)</th><th>MBP</th><th>Points Bonus</th><th>Total Fans</th></tr></thead>
          <tbody>
            {breakdown_rows}
          </tbody>
        </table>
      </div>

      <h3 class="mv-chrome-text" style="font-size:16px;margin-top:24px;">Live Starting XI</h3>
      <div class="sub">The actual top-scoring owned players league-wide, right now</div>
      <div class="mv-table-scroll">
        <table class="mv-table">
          <thead><tr><th>Pos</th><th>Player</th><th>Team</th><th>Fantasy Pts</th></tr></thead>
          <tbody>
            {xi_rows}
          </tbody>
        </table>
      </div>
    </section>"""


season_options = "\n      ".join(
    f'<option value="{label}"{" selected" if label == CURRENT_SALARY_SEASON else ""}>{label}</option>'
    for label in season_labels
)

season_blocks = []
for label in season_labels:
    show_games = label == CURRENT_SALARY_SEASON
    rows = season_summary_rows(label)
    note = (
        f"Cost and revenue for {label}, derived from every game played this season."
        if show_games else
        f"{label} hasn't been played yet &mdash; salary cost only, no games or revenue to show."
    )
    display = "block" if label == CURRENT_SALARY_SEASON else "none"
    season_blocks.append(f"""
    <div class="season-block" data-season="{label}" style="display:{display};">
      <div class="sub" style="margin-bottom:10px;">{note}</div>
      <section class="card mv-card">
        <div class="mv-table-scroll">
          {render_summary_table(label, rows, show_games)}
        </div>
      </section>
      {render_games_table(label)}
      {render_fan_formula_section(label)}
    </div>""")

financials_html = head("Financials", "financials.html") + hero_logo() + f"""
    <div class="mv-page-header">
      <h1 class="mv-chrome-text">Financials</h1>
      <div class="sub">Pick a season &mdash; cost, revenue, fans, and (for {CURRENT_SALARY_SEASON}) the full game-by-game log.</div>
    </div>

    <div style="text-align:center;margin-bottom:20px;">
      <label for="seasonSelect" style="font-size:13px;color:var(--mv-ink-muted);margin-right:8px;">Season</label>
      <select id="seasonSelect" style="background:var(--mv-black-3);color:var(--mv-ink);border:1px solid var(--mv-border);border-radius:6px;padding:6px 10px;font-size:14px;">
      {season_options}
      </select>
    </div>

    {"".join(season_blocks)}

    <script>
      document.getElementById('seasonSelect').addEventListener('change', function() {{
        var season = this.value;
        document.querySelectorAll('.season-block').forEach(function(el) {{
          el.style.display = (el.dataset.season === season) ? 'block' : 'none';
        }});
      }});
    </script>
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
