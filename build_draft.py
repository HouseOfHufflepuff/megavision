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

from common import head, foot, hero_logo

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


def build():
    players = fetch_draft_pool()
    # ADP ascending, with blanks ("-") sinking to the bottom
    players.sort(key=lambda p: float(num_or_sentinel(p["adp"], "999999")))

    rows_html = "\n            ".join(
        f'<tr>'
        f'<td>{p["name"]}</td>'
        f'<td>{p["pos"]}</td>'
        f'<td class="dim">{p["club"]}</td>'
        f'<td data-sort="{num_or_sentinel(p["age"])}">{p["age"]}</td>'
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
      <div class="sub">{len(players)} players eligible for the 26/27 senior draft &mdash; not currently on any Fantrax roster. Click a column header to sort.</div>
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
