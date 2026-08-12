"""
26/27 Junior Division draft grades -- a one-time recap of the actual live
draft (only the 12 junior teams drafted; senior rosters were already full
from keepers and their picks were passed every round).

The underlying numbers (data/draft_grades_2627.json) were computed once,
right after the draft, from:
  - Fantrax's own draftPicksOrdered (the real pick-by-pick results)
  - a weighted composite rank over the full 549-player draft-eligible pool:
    FC26 overall (30%), 25/26 fantasy points (30%), 25/26 goals (15%),
    ADP inverted -- lower is better (15%), age inverted -- younger is
    better (10%), each min-max normalized 0-100 first.
  - "value" per pick = actual overall pick number minus that player's
    composite-rank position. Positive = got a good player later than the
    consensus said you had to (a steal); negative = paid an early pick for
    a player the model rated well below that slot (a reach).
  - team grades are the 12 teams' average pick value, sorted and mapped
    straight onto A through F so the grades are actually spread out
    instead of clustering.
  - player tiers (Star / Starting XI / Rotation) are composite-score bands
    across the 108 actual picks: Star >=55, Starting XI 35-54, Rotation <35.

Regenerating this page means re-running the whole draft-grading pipeline
(pulling live Fantrax draft results + FC26 + FPL data and recomputing
composite ranks) -- there isn't a single idempotent script for that yet
since it was built interactively; the commentary below is specific to this
one draft and wouldn't make sense to auto-regenerate anyway. If a future
draft needs the same treatment, treat this file as the template.

Run:
    python3 build_draft_grades.py
"""
import json

from common import head, foot, hero_logo

GRADE_COLOR = {
    "A": "var(--mv-gold)", "A-": "var(--mv-gold)",
    "B+": "var(--mv-blue)", "B": "var(--mv-blue)", "B-": "var(--mv-blue)",
    "C+": "var(--mv-violet)", "C": "var(--mv-violet)", "C-": "var(--mv-violet)",
    "D+": "var(--mv-pink)", "D": "var(--mv-pink)", "D-": "var(--mv-pink)",
    "F": "var(--mv-crimson)",
}
TIER_COLOR = {"Star": "var(--mv-gold)", "Starting XI": "var(--mv-blue)", "Rotation": "var(--mv-ink-muted)"}

# ---- hand-written commentary, specific to this draft ----
COMMENTARY = {
    "Power Juniors": {
        "color": "Disciplined, no wasted reaches -- Cunha, Brobbey and Barnes all landed at or better than "
                 "expected, and nothing in the back half blew up the board. The model's cleanest draft in the "
                 "league: nobody made fireworks, nobody torched a pick either.",
        "best_note": "Landed a proven double-digit-goal wide player in round 3 when the model had him rated as "
                      "a top-25 player overall &mdash; he just fell further than he had any business falling.",
        "worst_note": "A round-4 pick on a stat line that reads like a dead wifi signal &mdash; zero goals, zero "
                       "assists on record, and a bench role at Ipswich. Fun name, empty page.",
        "proj": {"goals": 9, "assists": 3, "cs": None,
                  "note": "Projected off a 0.3 G/90 rate across a fuller ~30-start workload than the 19 he got in 25/26."},
    },
    "Divided United Juniors": {
        "color": "A weird shape &mdash; burned an early pick badly, then more or less nailed everything after "
                 "it, closing with four straight picks that all graded as positive value. A draft that started "
                 "in the shower and ended on the podium.",
        "best_note": "A Villa engine-room starter, still on the board in round 8. That's pure last-picks-of-the-draft theft.",
        "worst_note": "A round-2 pick off the back of a name that used to mean something &mdash; zero goal "
                       "involvements, a season mostly spent in a walking boot or a transfer saga, and a reach "
                       "that cost this team a real round.",
        "proj": {"goals": 3, "assists": 5, "cs": None,
                  "note": "Projected off a 0.1 G/90, 0.3 G+A/90 rate over a healthier ~26-start season than the 17 he managed in 25/26."},
    },
    "NFCA Juniors": {
        "color": "Front-loaded with the draft's youngest player at pick 3, then closed with the single best "
                 "value pick anybody made in rounds 7-9. The middle rounds sagged, but the top and bottom of "
                 "this board were genuinely sharp.",
        "best_note": "A 33-start Brighton starting centre-back, sitting there in round 9 like nobody remembered defenders exist.",
        "worst_note": "A round-5 pick on a fringe Sunderland squad name with 85.5 fantasy points to his entire "
                       "season and a per-90 goal rate that rounds to \"please stop.\"",
        "proj": {"goals": 1, "assists": 2, "cs": 11,
                  "note": "Projected off a full 34-start season for a reliable Brighton centre-back; clean sheets estimated off Brighton's typical mid-table defensive record."},
    },
    "WTF Juniors": {
        "color": "The steady-hand draft. Calvert-Lewin, Tarkowski and Stach at the top all landed near or above "
                 "expectation, and even the one real reach barely dented an otherwise sensible board.",
        "best_note": "A 34-year-old still scoring at a strong per-90 clip whenever fit &mdash; a classic "
                      "buy-low-on-name-recognition pick that actually worked.",
        "worst_note": "The second-to-last pick of the draft on a Brentford afterthought with 49 fantasy points "
                       "on the year, whose main job is filling a bench slot.",
        "proj": {"goals": 6, "assists": 1, "cs": None,
                  "note": "Projected off a 0.3 G/90 rate scaled to ~22 starts, roughly double his injury-hit 25/26 workload."},
    },
    "THOT Juniors": {
        "color": "Leaned hard into star power early (O'Reilly, Van de Ven) and paid for it in the middle rounds "
                 "&mdash; Igor Jesus and Kevin were both real reaches this draft never fully recovered from.",
        "best_note": "An ever-present Bournemouth left-back with 38 starts, still producing chances at a rate "
                      "nobody in round 6 has any business getting.",
        "worst_note": "The second-to-last pick of the entire draft on a Sunderland wide man with 17.5 fantasy "
                       "points to his name all season &mdash; that's closer to a scouting report than a fantasy asset.",
        "proj": {"goals": 1, "assists": 7, "cs": 10,
                  "note": "Projected off a 0.2 G+A/90 rate across a similar 36-start workload to his ever-present 25/26; clean sheets estimated off Bournemouth's solid defensive record."},
    },
    "5th Ave Juniors": {
        "color": "Erratic. Harry Wilson and Wieffer were both legitimate value, but Victor Muñoz and Antonio "
                 "Silva in the same five-round stretch dragged the whole board back to the middle of the pack.",
        "best_note": "A genuine Brighton first-team midfielder, still sitting there in round 7.",
        "worst_note": "A round-6 pick on a Bournemouth defender the model can't even find an FC26 rating for "
                       "&mdash; that's not a \"deep sleeper,\" that's drafting a rumor.",
        "proj": {"goals": 3, "assists": 6, "cs": 11,
                  "note": "Projected off a 0.1 G/90, 0.3 G+A/90 rate scaled up to a fuller ~30-start season; clean sheets estimated off Brighton's typical defensive record."},
    },
    "Quidpool Juniors FC": {
        "color": "Kudus and Thiaw at the top were fine value, but Jeremy Jacquet and Marco Palestra back-to-back "
                 "in rounds 4-5 turned a promising start into a shrug.",
        "best_note": "No per-90 data to lean on, but a real 138-point season buried in round 7 is a legitimate find regardless.",
        "worst_note": "A round-5 pick on a 21-year-old Chelsea fringe defender with 32 fantasy points, whose "
                       "role mostly consists of standing near the first team.",
        "proj": {"goals": 3, "assists": 4, "cs": None,
                  "note": "No 25/26 per-90 data available (limited recorded minutes) -- this is a squad-role estimate, not a rate projection."},
    },
    "Wholeassed Junior Mules": {
        "color": "Boom-or-bust, defined by three picks: Gvardiol and Xhaka were sound, the round-8 pick was a "
                 "legitimate coup, and a round-5 swing nearly sank the whole board.",
        "best_note": "The reigning Ballon d'Or midfielder, sitting there in round 8 purely because of an "
                      "injury-shortened year. If he's right, this is the single best value pick anybody made.",
        "worst_note": "A round-5 pick on a 20-year-old Newcastle academy forward with 31.5 points on the season "
                       "and, as far as the model can tell, no realistic path to relevance this year.",
        "proj": {"goals": 4, "assists": 7, "cs": None,
                  "note": "No 25/26 per-90 data available (injury-shortened season) -- projected off pre-injury career norms for a fully healthy season, not a rate extrapolation."},
    },
    "HUFF Juniors": {
        "color": "A draft that peaked at the very last pick. Mac Allister in round 1 was fine value, but "
                 "Martinelli and Ruben Dias both went earlier than they should have, and it took until the "
                 "literal final pick to land this draft's single biggest value score.",
        "best_note": "The last pick of the entire draft, and it graded as the best value score of anybody's "
                      "whole board &mdash; a starting Newcastle centre-back who fell all nine rounds.",
        "worst_note": "A round-8 pick on a Palace forward with 20 points and a season that never got going "
                       "&mdash; a pick that reads like it was made from muscle memory of his Forest days.",
        "proj": {"goals": 1, "assists": 3, "cs": 15,
                  "note": "Projected off a 0.1 G+A/90 rate scaled to a fuller ~30-start season; clean sheets estimated off Newcastle's imposing defensive record."},
    },
    "CRG Juniors": {
        "color": "Reece James in round 2 was sharp and the round-6 pick was a genuine find, but Daizen Maeda in "
                 "round 1 and Joao Gomes in round 3 were both reaches this draft never built momentum past.",
        "best_note": "An ever-present Villa full-back with 34 starts, still sitting there in round 6.",
        "worst_note": "The literal very last pick of the draft on a Coventry teenager with zero fantasy points "
                       "on the season &mdash; a pick that exists purely because the clock ran out.",
        "proj": {"goals": 3, "assists": 3, "cs": 13,
                  "note": "Projected off a 0.1 G/90, 0.2 G+A/90 rate across a similar 34-start workload; clean sheets estimated off Aston Villa's solid European-chasing defensive record."},
    },
    "BHB Juniors": {
        "color": "Woltemade and the round-5 goalkeeper pick were genuinely good value, but this draft is really "
                 "defined by three separate deep-bench flameouts that turned a promising start into a "
                 "bottom-three finish.",
        "best_note": "A Manchester City #1 with 34 starts and elite pedigree, with no business lasting to round 5.",
        "worst_note": "A round-6 pick on a Manchester United fringe midfielder with 35 fantasy points and, per "
                       "the model, no FC26 rating to speak of &mdash; a name pick, nothing more.",
        "proj": {"goals": None, "assists": None, "cs": 17,
                  "note": "Goalkeeper -- clean sheets estimated off Manchester City's typical defensive dominance; goals/assists not applicable."},
    },
    "Real Juniors": {
        "color": "The worst draft in the league, and it isn't close. One pick graded as clean value &mdash; the "
                 "rest of this board, especially the back half, produced the two single worst individual picks "
                 "anybody made all day.",
        "best_note": "A 35-year-old still scoring at an elite per-90 rate whenever he actually plays &mdash; a genuinely savvy veteran grab.",
        "worst_note": "A round-5 pick on a Chelsea reserve goalkeeper with zero senior minutes to his name, "
                       "taken a full 448 spots ahead of where the model would ever have gone near him. This "
                       "wasn't a reach. This was a typo that got submitted.",
        "proj": {"goals": 11, "assists": 2, "cs": None,
                  "note": "Projected off an elite 0.5 G/90 rate, age-managed down to ~24 starts rather than his 26 in 25/26."},
    },
}

BULL_CASE = {
    "name": "Rayan", "team": "NFCA Juniors", "pick": "Round 1, Pick 3",
    "text": (
        "The model can't even find him an FC26 rating -- too new, too unproven by EA's own database. "
        "The real-world numbers say something completely different. 183.5 fantasy points on the season is "
        "the 5th-highest total of ANY player drafted, including plenty of established Premier League regulars "
        "picked well behind him. Five goals and two assists in just 13 starts is a 0.4 G/90, 0.6 G+A/90 rate "
        "that a lot of full-time strikers would sign for. And an ADP of 22.6 shows the wider market already "
        "treats him as an early-round asset, not a lottery ticket. This is the classic \"the algorithm hasn't "
        "caught up to the highlight reel\" pick -- a 20-year-old already outproducing his role off the bench. "
        "Give him a nailed-on starting workload in 26/27 and the ceiling here isn't a bench piece, it's a "
        "breakout season."
    ),
}

METHOD_NOTE = (
    "Only the 12 junior teams actually drafted -- senior rosters were already set from keepers, so their "
    "picks were passed every round. \"Value\" per pick is the actual overall pick number minus where a "
    "weighted composite score (FC26 overall 30%, 25/26 fantasy points 30%, 25/26 goals 15%, ADP 15%, age "
    "10%, younger better) ranked that player among all 549 draft-eligible players. Positive value means a "
    "team got a good player later than consensus said they had to; negative means they paid an early pick "
    "for a player the model rated well below that slot."
)


def money_or_dash(v, suffix=""):
    return f"{v:g}{suffix}" if v is not None else "&mdash;"


def pick_row_html(p):
    age = p.get("age")
    ovr = p.get("ovr")
    fpts = p.get("fpts")
    value = p.get("value")
    value_color = "var(--mv-gold)" if (value or 0) >= 0 else "var(--mv-crimson)"
    value_text = f"{value:+d}" if value is not None else "&mdash;"
    return (
        f'<tr><td>{p["round"]}</td><td>{p["name"]}</td><td class="dim">{p.get("pos") or "&mdash;"}</td>'
        f'<td class="dim">{p.get("club") or "&mdash;"}</td>'
        f'<td data-sort="{age if age is not None else -1}">{money_or_dash(age)}</td>'
        f'<td data-sort="{ovr if ovr is not None else -1}">{money_or_dash(ovr)}</td>'
        f'<td data-sort="{fpts if fpts is not None else -1}">{money_or_dash(fpts)}</td>'
        f'<td style="color:{TIER_COLOR[p["tier"]]};font-weight:600;">{p["tier"]}</td>'
        f'<td data-sort="{value if value is not None else -9999}" style="color:{value_color};">{value_text}</td></tr>'
    )


def build():
    teams = json.load(open("data/draft_grades_2627.json"))

    team_cards = []
    for t in teams:
        c = COMMENTARY[t["team"]]
        grade = t["grade"]
        color = GRADE_COLOR[grade]
        best, worst = t["best"], t["worst"]
        proj = c["proj"]

        pick_rows = "\n              ".join(pick_row_html(p) for p in t["picks"])

        proj_line = ""
        if proj["cs"] is not None and proj["goals"] is None:
            proj_line = f'<strong>{proj["cs"]}</strong> projected clean sheets in 26/27'
        elif proj["cs"] is not None:
            proj_line = f'<strong>{proj["goals"]}</strong> goals, <strong>{proj["assists"]}</strong> assists, <strong>{proj["cs"]}</strong> clean sheets projected for 26/27'
        else:
            proj_line = f'<strong>{proj["goals"]}</strong> goals, <strong>{proj["assists"]}</strong> assists projected for 26/27'

        team_cards.append(f"""
    <section class="card mv-card" style="border-left:4px solid {color};">
      <div style="display:flex;align-items:baseline;justify-content:space-between;flex-wrap:wrap;gap:12px;margin-bottom:10px;">
        <h2 class="mv-chrome-text" style="margin:0;">{t["team"]}</h2>
        <div style="font-size:32px;font-weight:800;color:{color};">{grade}</div>
      </div>
      <p style="color:var(--mv-ink-muted);line-height:1.6;">{c["color"]}</p>

      <div class="mv-stat-grid" style="grid-template-columns:repeat(auto-fit, minmax(260px,1fr));margin:18px 0;">
        <div class="mv-stat" style="border-color:var(--mv-gold);">
          <div class="label">Best Pick &mdash; {best["name"]} (R{best["round"]}, {best.get("pos") or ""} {best.get("club") or ""})</div>
          <div class="value" style="font-size:15px;font-weight:400;line-height:1.5;">{c["best_note"]}</div>
          <div style="margin-top:8px;font-size:13px;color:var(--mv-ink-muted);">{proj_line}<br><span style="font-size:11px;">{proj["note"]}</span></div>
        </div>
        <div class="mv-stat" style="border-color:var(--mv-crimson);">
          <div class="label">Worst Pick &mdash; {worst["name"]} (R{worst["round"]}, {worst.get("pos") or ""} {worst.get("club") or ""})</div>
          <div class="value" style="font-size:15px;font-weight:400;line-height:1.5;">{c["worst_note"]}</div>
        </div>
      </div>

      <div class="mv-table-scroll">
        <table class="mv-table mv-sortable">
          <thead><tr>
            <th data-sort-type="num">Rd</th><th data-sort-type="text">Player</th><th data-sort-type="text">Pos</th>
            <th data-sort-type="text">Club</th><th data-sort-type="num">Age</th><th data-sort-type="num">FC26</th>
            <th data-sort-type="num">FPts</th><th data-sort-type="text">Tier</th><th data-sort-type="num">Value</th>
          </tr></thead>
          <tbody>
              {pick_rows}
          </tbody>
        </table>
      </div>
    </section>""")

    html = head("Draft Grades", "draft-grades.html") + hero_logo() + f"""
    <div class="mv-page-header">
      <h1 class="mv-chrome-text">26/27 Draft Grades</h1>
      <div class="sub">Every junior team's actual live draft, graded pick by pick against a weighted expected-value model.</div>
    </div>

    <section class="card mv-card">
      <div style="font-size:12px;color:var(--mv-ink-muted);line-height:1.6;">{METHOD_NOTE}</div>
    </section>

    <section class="card mv-card" style="border-left:4px solid var(--mv-violet);">
      <h2 class="mv-chrome-text" style="margin-top:0;">Bull Case: {BULL_CASE["name"]}</h2>
      <div class="sub" style="margin-bottom:12px;">Youngest player picked in the whole draft &mdash; {BULL_CASE["team"]}, {BULL_CASE["pick"]}</div>
      <p style="line-height:1.7;">{BULL_CASE["text"]}</p>
    </section>

    {"".join(team_cards)}

    <p style="margin-top:24px;"><a href="teams.html" style="color:var(--mv-ink-muted);font-size:13px;">&larr; Back to all teams</a></p>
""" + foot()

    with open("draft-grades.html", "w") as f:
        f.write(html)
    print("Updated draft-grades.html")


if __name__ == "__main__":
    build()
