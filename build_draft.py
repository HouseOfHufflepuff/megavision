"""
Draft board: every player eligible to be drafted in the 26/27 senior draft
(i.e. not currently on any Fantrax roster in the league), pulled live from
Fantrax. Regenerates draft.html.

    python3 build_draft.py

Nothing is cached -- every run hits Fantrax fresh via the same
browser-cookie session fantrax_live.py already uses.
"""
import browser_cookie3
import requests

from common import head, foot, hero_logo, CLUB_NAMES
from fc26_ratings import fetch_all_players, build_lookup, match
import sync_fpl_stats as fpl

LEAGUE_ID = "9rv5verjmrz6rjuo"


def fetch_draft_pool():
    cj = browser_cookie3.chrome(domain_name="fantrax.com")
    sess = requests.Session()
    sess.cookies.update(cj)
    sess.headers.update({"User-Agent": "Mozilla/5.0"})

    body = {"msgs": [{"method": "getPlayerStats", "data": {
        "leagueId": LEAGUE_ID,
        "view": "STATS",
        "statusOrTeamFilter": "ALL_AVAILABLE",
        "maxResultsPerPage": 1000,
        "pageNumber": 1,
    }}]}
    resp = sess.post("https://www.fantrax.com/fxpa/req", params={"leagueId": LEAGUE_ID}, json=body, timeout=30)
    data = resp.json()["responses"][0]["data"]

    players = []
    for row in data["statsTable"]:
        scorer = row["scorer"]
        cells = row["cells"]
        cell = lambda i: cells[i]["content"] if i < len(cells) else ""
        pos = scorer.get("posShortNames", "")
        if pos == "G":
            pos = "GK"
        players.append({
            "name": scorer["name"],
            "pos": pos,
            "club": scorer.get("teamShortName", ""),
            "age": cell(2),
            "fpts": cell(5),
            "fpg": cell(6),
            "adp": cell(8),
            "rostered": cell(9),
        })
    return players


def num_or_sentinel(s, sentinel="-1"):
    s = (s or "").strip().replace("%", "")
    if not s or s == "-":
        return sentinel
    try:
        float(s)
        return s
    except ValueError:
        return sentinel


def eur(v):
    if not isinstance(v, (int, float)):
        return "—"
    if v >= 1_000_000:
        return f"€{v / 1_000_000:,.1f}M"
    if v >= 1_000:
        return f"€{v / 1_000:,.0f}K"
    return f"€{v:,.0f}"


def attach_fc26(players):
    print("Fetching live FC 26 ratings...")
    fc26_players = fetch_all_players()
    lookup = build_lookup(fc26_players)
    matched = 0
    for p in players:
        tokens = p["name"].split()
        last = tokens[-1]
        first_initial = tokens[0][0] if tokens else None
        club_hint = CLUB_NAMES.get(p["club"])
        m = match(lookup, last, first_initial, club_hint)
        if m is None:
            p["fc26"] = p["fc26_pot"] = p["fc26_value"] = None
            continue
        matched += 1
        p["fc26"] = m["overall"]
        p["fc26_pot"] = m["potential"]
        p["fc26_value"] = m["value_eur"]
    print(f"Matched {matched}/{len(players)} players to FC 26 ratings.")


def attach_fpl_stats(players):
    """2025/26 Premier League season totals from the official FPL API --
    the free-agent pool is entirely Premier League players, so coverage
    here should be much higher than the all-leagues roster pages."""
    print("Fetching FPL player list...")
    elements = fpl.fetch_elements()
    lookup = fpl.build_lookup(elements)
    matched = 0
    no_season = 0
    for i, p in enumerate(players, 1):
        tokens = p["name"].split()
        last = tokens[-1]
        first_initial = tokens[0][0] if tokens else None
        e = fpl.match(lookup, last, first_initial)
        for k in ("starts", "goals", "assists", "minutes", "tackles", "cbi", "xg"):
            p[f"fpl_{k}"] = None
        if e is None:
            continue
        totals = fpl.fetch_season_totals(e["id"])
        if totals is None:
            no_season += 1
            continue
        matched += 1
        p["fpl_starts"] = totals["starts"]
        p["fpl_goals"] = totals["goals_scored"]
        p["fpl_assists"] = totals["assists"]
        p["fpl_minutes"] = totals["minutes"]
        p["fpl_tackles"] = totals["tackles"]
        p["fpl_cbi"] = totals["clearances_blocks_interceptions"]
        p["fpl_xg"] = float(totals["expected_goals"])
        mins = p["fpl_minutes"]
        if mins:
            p["g_per90"] = p["fpl_goals"] * 90 / mins
            p["ga_per90"] = (p["fpl_goals"] + p["fpl_assists"]) * 90 / mins
            p["xg_per90"] = p["fpl_xg"] * 90 / mins
        if i % 100 == 0:
            print(f"  ...{i}/{len(players)}")
    print(f"Matched {matched}/{len(players)} players to 2025/26 FPL stats ({no_season} matched but had no 2025/26 season row).")


def build():
    players = fetch_draft_pool()
    attach_fc26(players)
    attach_fpl_stats(players)
    for p in players:
        p.setdefault("g_per90"); p.setdefault("ga_per90"); p.setdefault("xg_per90")
    # ADP ascending, with blanks ("-") sinking to the bottom
    players.sort(key=lambda p: float(num_or_sentinel(p["adp"], "999999")))

    def n(v, decimals=0):
        return f"{v:,.{decimals}f}" if isinstance(v, (int, float)) else "—"

    def sv(v):
        return v if isinstance(v, (int, float)) else -1

    rows_html = "\n            ".join(
        f'<tr>'
        f'<td>{p["name"]}</td>'
        f'<td>{p["pos"]}</td>'
        f'<td class="dim">{p["club"]}</td>'
        f'<td data-sort="{num_or_sentinel(p["age"])}">{p["age"]}</td>'
        f'<td data-sort="{sv(p["fc26"])}" style="color:var(--mv-gold);">{n(p["fc26"])}</td>'
        f'<td data-sort="{sv(p["fc26_pot"])}">{n(p["fc26_pot"])}</td>'
        f'<td data-sort="{sv(p["fc26_value"])}">{eur(p["fc26_value"])}</td>'
        f'<td data-sort="{sv(p["fpl_starts"])}">{n(p["fpl_starts"])}</td>'
        f'<td data-sort="{sv(p["fpl_goals"])}">{n(p["fpl_goals"])}</td>'
        f'<td data-sort="{sv(p["fpl_assists"])}">{n(p["fpl_assists"])}</td>'
        f'<td data-sort="{sv(p["g_per90"])}">{n(p["g_per90"], 1)}</td>'
        f'<td data-sort="{sv(p["ga_per90"])}">{n(p["ga_per90"], 1)}</td>'
        f'<td data-sort="{sv(p["xg_per90"])}">{n(p["xg_per90"], 1)}</td>'
        f'<td data-sort="{sv(p["fpl_tackles"])}">{n(p["fpl_tackles"])}</td>'
        f'<td data-sort="{sv(p["fpl_cbi"])}">{n(p["fpl_cbi"])}</td>'
        f'<td data-sort="{num_or_sentinel(p["fpts"])}">{p["fpts"]}</td>'
        f'<td data-sort="{num_or_sentinel(p["fpg"])}">{p["fpg"]}</td>'
        f'<td data-sort="{num_or_sentinel(p["adp"], "999999")}">{p["adp"]}</td>'
        f'<td data-sort="{num_or_sentinel(p["rostered"])}">{p["rostered"]}</td>'
        f'</tr>'
        for p in players
    )

    html = head("Draft Board", "draft.html") + hero_logo() + f"""
    <div class="mv-page-header">
      <h1 class="mv-chrome-text">Draft Board</h1>
      <div class="sub">{len(players)} players eligible for the 26/27 senior draft &mdash; not currently on any Fantrax roster. FC26 ratings cover all leagues; 25/26 performance is from the official Fantasy Premier League API (SCA/90, GCA/90, clearances and pass completions aren't available from any free source and are omitted rather than faked -- fbref.com blocks all automated access). Click a column header to sort.</div>
    </div>

    <section class="card mv-card">
      <div class="mv-table-scroll">
        <table class="mv-table mv-sortable">
          <thead>
            <tr>
              <th data-sort-type="text">Player</th>
              <th data-sort-type="text">Pos</th>
              <th data-sort-type="text">Club</th>
              <th data-sort-type="num">Age</th>
              <th data-sort-type="num">FC26 OVR</th>
              <th data-sort-type="num">FC26 POT</th>
              <th data-sort-type="num">FC26 Value</th>
              <th data-sort-type="num">25/26 Starts</th>
              <th data-sort-type="num">25/26 Goals</th>
              <th data-sort-type="num">25/26 Assists</th>
              <th data-sort-type="num">G/90</th>
              <th data-sort-type="num">G+A/90</th>
              <th data-sort-type="num">xG/90</th>
              <th data-sort-type="num">Tackles</th>
              <th data-sort-type="num">CBI</th>
              <th data-sort-type="num">FPts</th>
              <th data-sort-type="num">FP/G</th>
              <th data-sort-type="num">ADP</th>
              <th data-sort-type="num">% Ros</th>
            </tr>
          </thead>
          <tbody>
            {rows_html}
          </tbody>
        </table>
      </div>
    </section>
""" + foot()

    with open("draft.html", "w") as f:
        f.write(html)
    print(f"Updated draft.html ({len(players)} players)")


if __name__ == "__main__":
    build()
