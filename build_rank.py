"""
Renders rank.html from the epl_players / player_gameweek / epl_club_gameweek
tables -- MEGAVISION Rank: a Matchups tab (every EPL fixture this gameweek,
records, matchup factor, full depth chart with start likelihood %), a Best
11 tab rendered as an actual pitch formation, and F/M/D/GK tabs ordered by
the MEGAVISION Rank score (see rank_algo.py).

Run:
    python3 sync_player_ranks.py       # populate/refresh raw data
    python3 sync_megavision_rank.py    # compute the 0-100 score + likelihoods
    python3 build_rank.py
"""
import unicodedata
from datetime import datetime, timezone

from common import head, foot, hero_logo, club_full_name, SITE_URL
from db import connect


def _fold(s):
    return unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode("ascii").lower().strip()

POSITIONS = [("F", "Forwards"), ("M", "Midfielders"), ("D", "Defenders"), ("GK", "Goalkeepers")]
FORMATION = [("F", 3), ("M", 4), ("D", 3), ("GK", 1)]  # top of the pitch down, per the brief


def fetch_rows(cur, week):
    cur.execute(
        "SELECT p.player_name, p.real_club, p.fantrax_position, p.age, p.height_cm, p.weight_kg, "
        "p.fc26_overall, p.fc26_speed, p.fc26_potential, p.fantrax_ros_pct, "
        "g.score, g.injury_status, g.started_last_week, g.ffs_start, g.ffs_positive_mention, "
        "g.ffs_negative_mention, g.ffs_doubt, g.megavision_rank, g.start_likelihood "
        "FROM epl_players p JOIN player_gameweek g ON g.player_name=p.player_name AND g.real_club=p.real_club "
        "WHERE g.gameweek=? AND p.fantrax_position IS NOT NULL",
        (week,),
    )
    cols = [d[0] for d in cur.description]
    return [dict(zip(cols, row)) for row in cur.fetchall()]


def fetch_clubs(cur, week):
    cur.execute(
        "SELECT real_club, opponent, is_home, played, win, draw, loss, league_position, "
        "club_avg_fc26, matchup_factor FROM epl_club_gameweek WHERE gameweek=?",
        (week,),
    )
    cols = [d[0] for d in cur.description]
    return {row[0]: dict(zip(cols, row)) for row in cur.fetchall()}


def badge(text, color):
    return f'<span class="mv-badge" style="border:1px solid {color};color:{color};font-size:9px;padding:1px 6px;margin-left:4px;">{text}</span>'


def flags(r):
    out = []
    if r["ffs_doubt"]:
        out.append(badge("Doubt", "var(--mv-gold)"))
    if r["ffs_negative_mention"] and not r["ffs_doubt"]:
        out.append(badge("Negative", "var(--mv-crimson)"))
    if r["ffs_positive_mention"]:
        out.append(badge("Positive", "var(--mv-blue)"))
    if r["injury_status"]:
        out.append(badge("Injured", "var(--mv-crimson)"))
    return "".join(out)


def rank_color(rank):
    if rank is None:
        return "var(--mv-ink-muted)"
    if rank >= 80:
        return "var(--mv-gold)"
    if rank >= 60:
        return "var(--mv-blue)"
    if rank >= 40:
        return "var(--mv-ink)"
    return "var(--mv-ink-muted)"


def player_row(rank_num, r):
    ovr = f'{r["fc26_overall"]:.0f}' if r["fc26_overall"] is not None else "—"
    speed = f'{r["fc26_speed"]:.0f}' if r["fc26_speed"] is not None else "—"
    ros = f'{r["fantrax_ros_pct"]:.0f}%' if r["fantrax_ros_pct"] is not None else "—"
    score = f'{r["score"]:.1f}' if r["score"] is not None else "—"
    started = "Yes" if r["started_last_week"] else "No"
    mv = r["megavision_rank"]
    mv_str = f'{mv:.1f}' if mv is not None else "—"
    start_pct = f'{r["start_likelihood"]:.0f}%' if r["start_likelihood"] is not None else "—"
    return (
        f'<tr><td data-sort="{rank_num}">{rank_num}</td>'
        f'<td>{r["player_name"]}{flags(r)}</td>'
        f'<td class="dim">{r["real_club"] or "—"}</td>'
        f'<td data-sort="{mv or -1}"><strong style="color:{rank_color(mv)};font-size:14px;">{mv_str}</strong></td>'
        f'<td data-sort="{r["start_likelihood"] or 0}">{start_pct}</td>'
        f'<td data-sort="{r["fc26_overall"] or -1}">{ovr}</td>'
        f'<td data-sort="{r["fc26_speed"] or -1}">{speed}</td>'
        f'<td data-sort="{r["fantrax_ros_pct"] or -1}">{ros}</td>'
        f'<td data-sort="{r["score"] or -1}">{score}</td>'
        f'<td data-sort="{r["started_last_week"] or 0}">{started}</td>'
        f'</tr>'
    )


TABLE_HEADER = (
    '<tr><th data-sort-type="num">#</th><th data-sort-type="text">Player</th><th>Club</th>'
    '<th data-sort-type="num">MEGAVISION Rank</th><th data-sort-type="num">Start%</th>'
    '<th data-sort-type="num">FC26 OVR</th><th data-sort-type="num">FC26 Speed</th><th data-sort-type="num">ROS%</th>'
    '<th data-sort-type="num">GW Score</th><th data-sort-type="num">Started Last Wk</th></tr>'
)


def table(rows, panel_id, active=False):
    body = "".join(player_row(i + 1, r) for i, r in enumerate(rows))
    cls = "mv-tab-panel active" if active else "mv-tab-panel"
    return f"""<div id="{panel_id}" class="{cls}">
      <div class="mv-table-scroll"><table class="mv-table mv-sortable">
        <thead>{TABLE_HEADER}</thead><tbody>{body}</tbody>
      </table></div>
    </div>"""


def pitch_slot(r):
    mv = r["megavision_rank"]
    mv_str = f'{mv:.1f}' if mv is not None else "—"
    return (
        f'<div class="mv-slot">'
        f'<div class="pos">{r["fantrax_position"]}</div>'
        f'<div class="player">{r["player_name"]}</div>'
        f'<div class="dim" style="font-size:11px;">{r["real_club"] or ""}</div>'
        f'<div class="salary" style="color:{rank_color(mv)};">{mv_str}</div>'
        f'</div>'
    )


def pitch_view(best11_by_pos):
    rows_html = []
    for pos, _ in FORMATION:
        slots = "".join(pitch_slot(r) for r in best11_by_pos[pos])
        rows_html.append(f'<div class="mv-pitch-row">{slots}</div>')
    return f'<div class="mv-pitch">{"".join(rows_html)}</div>'


def rank_tier(rank):
    if rank is None:
        return "tier-low"
    if rank >= 80:
        return "tier-elite"
    if rank >= 60:
        return "tier-good"
    if rank >= 40:
        return "tier-mid"
    return "tier-low"


def matchup_player(r):
    mv = r["megavision_rank"]
    mv_str = f'{mv:.0f}' if mv is not None else "—"
    start_pct = f'{r["start_likelihood"]:.0f}%' if r["start_likelihood"] is not None else "—"
    return (
        f'<div class="mv-matchup-player">'
        f'<span class="name">{r["player_name"]}{flags(r)}</span>'
        f'<span class="pct">{start_pct}</span>'
        f'<span class="mv-rank-chip {rank_tier(mv)}">{mv_str}</span>'
        f'</div>'
    )


def record_str(club_info):
    if not club_info or club_info.get("played") is None:
        return "0-0-0"
    return f'{club_info["win"]}-{club_info["draw"]}-{club_info["loss"]}'


def matchup_card(home, away, players_by_club, clubs):
    home_info, away_info = clubs.get(home, {}), clubs.get(away, {})
    home_mf, away_mf = home_info.get("matchup_factor"), away_info.get("matchup_factor")

    def mf_str(mf):
        if mf is None:
            return "—"
        sign = "+" if mf > 0 else ""
        color = "var(--mv-blue)" if mf > 0 else ("var(--mv-crimson)" if mf < 0 else "var(--mv-ink-muted)")
        return f'<span class="mf" style="color:{color};">{sign}{mf:.1f}</span>'

    home_pos, away_pos = {}, {}
    for r in players_by_club.get(home, []):
        home_pos.setdefault(r["fantrax_position"], []).append(r)
    for r in players_by_club.get(away, []):
        away_pos.setdefault(r["fantrax_position"], []).append(r)

    pos_rows = []
    for pos, _ in FORMATION:
        away_players = sorted(away_pos.get(pos, []), key=lambda r: -(r["start_likelihood"] or 0))
        home_players = sorted(home_pos.get(pos, []), key=lambda r: -(r["start_likelihood"] or 0))
        pos_rows.append(f"""<div class="mv-matchup-pos-row">
          <div class="mv-matchup-side away">{''.join(matchup_player(r) for r in away_players)}</div>
          <div class="mv-pos-pill pos-{pos}">{pos}</div>
          <div class="mv-matchup-side home">{''.join(matchup_player(r) for r in home_players)}</div>
        </div>""")

    return f"""<div class="mv-matchup-card">
      <div class="mv-matchup-head">
        <div class="mv-matchup-team away">
          <div class="name">{club_full_name(away)}</div>
          <div class="meta">{away} &middot; {record_str(away_info)} &middot; away &middot; {mf_str(away_mf)}</div>
        </div>
        <div class="mv-matchup-vs">AT</div>
        <div class="mv-matchup-team home">
          <div class="name">{club_full_name(home)}</div>
          <div class="meta">{home} &middot; {record_str(home_info)} &middot; home &middot; {mf_str(home_mf)}</div>
        </div>
      </div>
      {''.join(pos_rows)}
    </div>"""


def build_matchups_panel(rows, clubs, active=False):
    players_by_club = {}
    for r in rows:
        players_by_club.setdefault(r["real_club"], []).append(r)

    paired = set()
    cards = []
    for club, info in sorted(clubs.items()):
        if club in paired or not info.get("opponent"):
            continue
        # resolve opponent name -> code by matching against every other club's display name
        opp_code = None
        for c2 in clubs:
            if c2 != club and _fold(club_full_name(c2)) == _fold(info["opponent"]):
                opp_code = c2
                break
        if not opp_code or opp_code in paired:
            continue
        home = club if info.get("is_home") else opp_code
        away = opp_code if info.get("is_home") else club
        cards.append(matchup_card(home, away, players_by_club, clubs))
        paired.add(club)
        paired.add(opp_code)

    cls = "mv-tab-panel active" if active else "mv-tab-panel"
    return f'<div id="matchups" class="{cls}"><div class="mv-matchup-grid">{"".join(cards)}</div></div>'


def build(week=None):
    conn = connect()
    cur = conn.cursor()
    if week is None:
        week = cur.execute("SELECT MAX(gameweek) FROM player_gameweek").fetchone()[0]
    rows = fetch_rows(cur, week)
    clubs = fetch_clubs(cur, week)
    conn.close()

    by_pos = {pos: sorted(
        (r for r in rows if r["fantrax_position"] == pos),
        key=lambda r: -(r["megavision_rank"] or 0),
    ) for pos, _ in POSITIONS}

    tabs = ['<button class="mv-tab active" onclick="mvShowTab(this,\'matchups\')">Matchups</button>',
            '<button class="mv-tab" onclick="mvShowTab(this,\'best-11\')">Best 11</button>']
    for pos, label in POSITIONS:
        tabs.append(f'<button class="mv-tab" onclick="mvShowTab(this,\'pos-{pos}\')">{label}</button>')

    best11_by_pos = {}
    used = set()
    for pos, slots in FORMATION:
        picks = [r for r in by_pos[pos] if r["ffs_start"] and r["player_name"] not in used][:slots]
        for r in picks:
            used.add(r["player_name"])
        best11_by_pos[pos] = picks

    all_best11 = [r for pos, _ in FORMATION for r in best11_by_pos[pos]]
    avg_mv = sum(r["megavision_rank"] or 0 for r in all_best11) / len(all_best11) if all_best11 else 0
    best11_panel = f"""<div id="best-11" class="mv-tab-panel">
      <div class="sub" style="margin-bottom:10px;">3 F / 4 M / 3 D / 1 GK, highest MEGAVISION Rank among this gameweek's projected starters &middot;
        average rank {avg_mv:.1f}</div>
      {pitch_view(best11_by_pos)}
    </div>"""

    panels = [build_matchups_panel(rows, clubs, active=True), best11_panel]
    for i, (pos, label) in enumerate(POSITIONS):
        panels.append(table(by_pos[pos], f"pos-{pos}"))

    published_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    iso_now = datetime.now(timezone.utc).isoformat()

    rank_description = (
        f"Free fantasy football player rankings for GW{week}: every EPL player scored 0-100 by MEGAVISION Rank, "
        "combining FC 26 ratings, team strength, matchup difficulty, and real starting-lineup probability. "
        "Live depth charts, start-likelihood percentages, and a Best 11 for every position."
    )
    rank_keywords = (
        "fantasy football rankings, fantasy soccer rankings, EPL player rankings, fantasy Premier League rankings, "
        "FPL rankings, fantasy football projections, start sit fantasy soccer, weekly fantasy football projections, "
        "fantasy football best 11, fantasy football depth chart, agentic fantasy sports data"
    )
    rank_structured_data = {
        "@context": "https://schema.org",
        "@type": "Dataset",
        "name": f"MEGAVISION Rank — GW{week} EPL Fantasy Football Player Rankings",
        "description": rank_description,
        "keywords": [k.strip() for k in rank_keywords.split(",")],
        "url": f"{SITE_URL}/rank.html",
        "dateModified": iso_now,
        "isAccessibleForFree": True,
        "creator": {"@type": "Organization", "name": "MEGAVISION"},
        "variableMeasured": ["MEGAVISION Rank (0-100)", "Start Likelihood (%)", "FC 26 Overall", "Matchup Factor"],
    }

    html = head(
        "Rank", "rank.html", wide=True,
        description=rank_description, keywords=rank_keywords,
        structured_data=rank_structured_data,
    ) + hero_logo() + f"""
    <div class="mv-page-header">
      <h1 class="mv-chrome-text">Rank</h1>
      <div class="sub">MEGAVISION Rank for GW{week} &middot; {len(rows)} EPL players tracked &middot; Published {published_at}</div>
    </div>

    <section class="card mv-card">
      <h2 class="mv-chrome-text" style="margin-top:0;">MEGAVISION Rank</h2>
      <div class="sub" style="margin-bottom:14px;">0-100 projection score: FC 26 talent, team strength, this week's matchup, and current form,
        standardized into a bell curve, then gated by FFS's projected starting XI -- a doubtful or non-starting player can't reach the top
        regardless of talent. Start% is each player's estimated odds of being in their club's XI (sums to 100% within a position group). v1, weights still being tuned.</div>
      <div class="mv-tabs">{''.join(tabs)}</div>
      {''.join(panels)}
    </section>
    """ + foot()

    with open("rank.html", "w") as f:
        f.write(html)
    print(f"Updated rank.html -- GW{week}, {len(rows)} players")


if __name__ == "__main__":
    build()
