"""
Rulez page -- the full 26/27 rulebook, as published by the commissioner in
the "official" Google Doc (season structure, financials, rosters,
transactions, youth, scoring). Static content, not live-fetched; re-run
this and edit the content below whenever the doc changes.

Source: https://docs.google.com/document/d/1Ct7ctNSsruBosoQq48PblnJFhRj19-K58968KuECblo

Run:
    python3 build_rulez.py
"""
from common import head, foot, hero_logo

SOURCE_DOC_URL = "https://docs.google.com/document/d/1Ct7ctNSsruBosoQq48PblnJFhRj19-K58968KuECblo/edit"


def card(title, body, accent=None):
    border = f' style="border-left:4px solid {accent};"' if accent else ""
    return f'<section class="card mv-card"{border}><h2 class="mv-chrome-text" style="margin-top:0;">{title}</h2>{body}</section>'


def ul(items):
    return '<ul style="line-height:1.8;padding-left:20px;margin:0;">' + "".join(f"<li>{i}</li>" for i in items) + "</ul>"


def ol(items):
    return '<ol style="line-height:1.8;padding-left:20px;margin:0;">' + "".join(f"<li>{i}</li>" for i in items) + "</ol>"


def h3(text):
    return f'<h3 class="dim" style="font-size:14px;text-transform:uppercase;letter-spacing:0.04em;margin:18px 0 6px;">{text}</h3>'


def build():
    # ---------------- 1. Season Structure ----------------
    season = card("1. Season Structure and Competitions", f"""
      {ul([
        "<strong>Season Play</strong>: 12-team double round robin, runs roughly inside EPL gameweeks 2-30. Takes precedence for scheduling -- ideally weekend games where teams are rested and most likely to play starters.",
        "<strong>FA Cup</strong>: 4-round tournament, runs inside gameweeks 1-36. Prioritized during awkward scheduling weeks (midweek games, short rest). Week 1's Super Cup and Community Shield teams get a Round 1 bye; the remaining 8 teams are randomized into Round 1.",
        "<strong>Citadel Cup</strong>: 4-round tournament, sits between weeks 2-25 (ideally two sets of back-to-back EPL games). Round 1 is pool play -- four pools of three teams, seeded by standings at the time. Top 2 scorers per pool advance to Round 2, cross-pool: 1A v 2D, 1B v 2C, 1C v 2A, 1D v 2B.",
        "<strong>Champions League</strong>: top 4 League standings qualify, expected around week 31-36. 2-legged semifinal (cumulative points advance), 1-week final.",
        "<strong>Europa League</strong>: teams 5-8 qualify, expected around week 31-36. 2-week quarterfinal, CL semifinal losers join for the semifinal, 1-week final. Semifinal and final are both 2-week, cumulative-points-advance rounds.",
        "<strong>Super Cup</strong>: typically Week 1 -- winner of the previous year's Champions League vs. winner of the previous year's Europa League.",
        "<strong>Community Shield</strong>: typically Week 1 -- winner of the previous year's League vs. winner of the previous year's FA Cup.",
      ])}
    """)

    # ---------------- 2. Financials ----------------
    financials = card("2. Financials", f"""
      {h3("2.1 Pool Funding")}
      {ul([
        "Salaries are the bulk of pool funding -- teams pay salaries for 17 outfield players + 1 Team GK across the 22 league weeks; each team likely contributes $100-$250 via salaries.",
        "Teams pay $50 to expand their stadium by 50 seats -- more seats means a bigger share of ticket revenue (below).",
        "Every transfer with a money component includes a 10% league cut.",
        "$10 Federation Fee helps fund cup payouts.",
        "$15 bounty for a 2nd youth pick.",
        "$6 per injury replacement pickup during the season.",
        "Contracts of players cut from a roster.",
        "Loan fees ($6 from each club).",
      ])}
      {h3("2.2 Revenue Back From the Pool to Teams")}
      <div style="margin-bottom:10px;"><strong>Ticket Sales</strong></div>
      {ul([
        "80% of ticket sales go to the home team, 20% to the away team.",
        "Tickets sold = the sum of home and away fans for the two teams, capped by the home team's stadium capacity.",
        "Tickets are $0.04 each.",
        "CL and Europa games count as ticketed games; the higher seed hosts.",
      ])}
      <div style="margin:14px 0 6px;"><strong>Fans, per team, calculated as:</strong></div>
      <div class="mv-table-scroll" style="margin-bottom:10px;">
        <table class="mv-table">
          <thead><tr><th>League Record Standing</th><th>Fans</th><th>Overall Scoring Standing</th><th>Fans</th></tr></thead>
          <tbody>
            {"".join(f'<tr><td>{rank}</td><td>{fans}</td><td>{srank if srank else "&mdash;"}</td><td>{sfans if sfans else "&mdash;"}</td></tr>' for rank, fans, srank, sfans in [
                ("1st", 200, "1st", 100), ("2nd", 160, "2nd", 80), ("3rd", 140, "3rd", 70), ("4th", 120, "4th", 60),
                ("5th", 90, "5th", 50), ("6th", 80, "6th", 45), ("7th", 70, "7th", 40), ("8th", 60, "8th", 35),
                ("9th", 50, "", ""), ("10th", 40, "", ""), ("11th", 30, "", ""), ("12th", 20, "", ""),
            ])}
          </tbody>
        </table>
      </div>
      {ul([
        "<strong>Legacy</strong>: 10 fans per League or CL title in the last 3 years; 5 fans per Europa, FA Cup, or Citadel Cup title in the last 3 years; 1 fan per Super Cup or Community Shield in the last 3 years. All-time: 5 fans per League/CL title ever, 2 fans per Europa/FA Cup/Citadel Cup title ever.",
        "<strong>Top XI</strong>: 30 fans each for the single top F, top M, top D; the rest of the Top XI (2 more F, 3 more M, 3 more D, 1 GK) is worth 10 fans each.",
        "Total fan pool is about 1,900 fans/week league-wide, with some dilution assumed for sold-out stadiums.",
      ])}
      {h3("Other Payouts")}
      {ul([
        "Transfers out of the EPL: the team receives &#8531; of the transfer fee (in GBP) as real dollars from the league fund.",
        "FA Cup: $40 winner, $20 runner-up.",
        "Citadel Cup: $20 winner, $10 runner-up (plus any sponsorship).",
        "Community Shield and Super Cup: $5 to the winner.",
      ])}
      {h3("Mega Fund (whatever's left in the pool)")}
      {ul([
        "60% to the <strong>TV Bonus</strong> by final standing: 1st 40%, 2nd 20%, 3rd 10%, 4th 8%, 5th 7%, 6th 5%, 7th 4%, 8th 3%, 9th 1%, 10th 1%, 11th 1%, 12th 0%.",
        "40% to <strong>postseason payouts</strong>: 50% CL winner, 20% CL loser, 20% Europa winner, 10% Europa loser.",
      ])}
    """, accent="var(--mv-gold)")

    # ---------------- 3. Rosters ----------------
    rosters = card("3. Rosters", f"""
      {ul([
        "Counted scores = top GK + 10 highest-scoring outfield players.",
        "Active roster needs 15 players: a Team GK (2 goalkeepers pooled) plus 3 per position (D, M, F). Team Goalies automatically use whichever of your 2 GKs scored higher that week, regardless of who you started.",
        "Teams roster 17 contracts total -- 15 starters + 2 bench outfield spots.",
      ])}
      {h3("Roster-Size Exceptions")}
      {ul([
        "<strong>Youth Player</strong>: any unpromoted youth player you hold rights to is selectable if on an EPL roster, provided they're 23 or younger at August 1. Limited to 4 league games/year without triggering a promotion; unlimited Cup/playoff games.",
        "<strong>Youth Player Loan (in)</strong>: a youth player (23 or younger) loaned in from another team adds a roster spot and can play unrestricted. Each team can take on only one loaned youth player.",
        "<strong>Injury Replacement (IRP)</strong>: $6 to pick up a free agent when a rostered player is ruled out for multiple games; roster them until the next FA window. If the injured player returns, drop the IRP unless it can shift to another injured player (no extra fee for that).",
      ])}
    """)

    # ---------------- 4. Transactions ----------------
    acquisition = card("4.1 Player Acquisition", f"""
      <p style="color:var(--mv-ink-muted);line-height:1.7;">A team fills its 17 contracts through any combination of these paths.</p>
      {h3("(1) Kept Players")}
      {ul([
        "Max 9 multi-year contracts under normal conditions -- at any point, 9 of 17 players can be expected back next year.",
        "Multi-year contracts: max 5 per position, min 1 per position. Okay: 5F/3M/1D or 4F/1M/1D. Not okay: 6F/2M/1D or 5F/4M/0D.",
        "<strong>Legend of the Club</strong>: a former youth player, promoted, now 24+ on August 1 -- one per team, doesn't count against the 9.",
        "<strong>Promoted Youth, 23 or younger</strong>: doesn't count against the 9.",
        "<strong>Loaned Player</strong>: one loaned-in player per year doesn't count against the 9 (as if they \"return\" to their original team once the 9 are measured). If a loan is cancelled early, the benefit is voided.",
        "Extensions allowed any time before the 3rd FA window: +50% for a 2nd year on a 1-year deal, +30% for a 3rd year on a 2-year deal.",
      ])}
      {h3("(2) Drafted Player")}
      {ul([
        "Season starts with a 6-9 round draft (commissioner judgment), reverse order of prior standings, not snake. Commissioner may allow extra post-draft free-agent pickups treated as draft picks if roster spots remain.",
        "Starting salary = real FPL salary in GBP.",
        "May be extended +10% for Year 2 and Year 3 any time before the 1st EPL game. After that, still extendable through the 3rd FA window but at the higher kept-player rate (+50% Y2, +30% Y3).",
      ])}
      {h3("(3) Free Agent Pickups")}
      <div style="margin-bottom:6px;">Three FA windows: <strong>1st</strong> after the summer window closes (~9/1), <strong>2nd</strong> during the November international break, <strong>3rd</strong> after the January window closes.</div>
      {ul([
        "1st &amp; 2nd windows: open bidding, $4 starting bid, $1 increments to $10, $2 increments $10-20, $5 increments $20-40, $10 increments after $40. High bid wins and becomes the guaranteed salary; can be surrendered back at no cost. Extendable at +50% Y2 / +30% Y3.",
        "3rd window: same bid ladder but starts at $6; the winning bid is credited to the league as a fee, the player can't be extended, and they're a flat $4 salary (de minimis cost for the ~5 remaining games).",
      ])}
      {h3("(4) Transfers")}
      {ul([
        "Three transfer windows: July 1 through the end of the 1st FA window, during the 2nd FA window, and during the 3rd FA window.",
        "Any cash in a transfer is taxed 10% to the league.",
        "Transfers can include players, cash, youth rights, draft/youth pick swaps, conditional payouts, or options on future players/rights.",
        "Any player option included in a transfer must be protected by one of the 9 multi-year slots; the option-holder can seek a release from the other owner if desired.",
        "Players acquired via transfer can be extended +10% up to 3 years, same terms as drafted players.",
      ])}
      {h3("(5) Loans")}
      {ul([
        "For the remaining season only; loaned players must already be on a multi-year contract.",
        "While on loan, the contract doesn't count against either team's 9-limit -- but it does count against the receiving team's 17 OF max, and they pay the salary.",
        "Buyback provisions can end a loan early, exercisable only during transfer windows; an early-cancelled loan puts the contract back against the parent club's 9-limit.",
        "Each team pays a $6 league fee per loan (on top of the 10% cash tax). Max 2 loaned out, max 2 loaned in, per team.",
        "If a loaned player transfers out of the EPL, the parent team gets any league compensation; half of any cash in that deal returns to the team that had them on loan.",
      ])}
      {h3("(6) Youth Promotion")}
      {ul([
        "Promotion grants a 3-year contract: Y1 $4, Y2 $4, Y3 $4.40.",
        "Youth players can play 4 league games without promotion, unlimited Cup/Euro games; a 5th league start requires promotion.",
        "Any unpromoted youth player 24+ on August 1 on an EPL roster must be promoted or released by the Youth Draft (October international break) -- applies only once they're actually in the EPL. A promoted-at-24+ player can be used as a Legend of the Club, otherwise needs one of the 9 multi-year slots.",
      ])}
      {h3("(7) Youth Loan")}
      {ul([
        "A team may loan out a youth player they hold rights to; the receiving team gets unrestricted use and it doesn't count against their 17 OF max.",
        "One loaned out, one loaned in, per team. $6 league fee plus the standard 10% cash tax. Player must be 23 or younger on August 1.",
      ])}
      {h3("(8) Injury Replacement Player (IRP)")}
      {ul([
        "$6 for a free-agent replacement once a player has missed a real match or is clearly ruled out for the next one.",
        "Can't be picked up during an FA window or during a scoring window for that set of games. First-come-first-served via the AI thread.",
        "When the injured player returns, drop the IRP the next week (or reassign it to another currently-injured player at no extra cost). All IRPs must be dropped at the start of any FA window; re-picking one up afterward costs another $6. Max 2 IRPs at a time, regardless of how many players are actually injured.",
      ])}
    """)

    divestiture = card("4.2 Player Divestiture", f"""
      {ul(["Contract Expiration", "Cut", "Transfer", "Loan", "Player Transferred out of EPL", "Team Relegated"])}
      {h3("Buy-Outs")}
      {ul([
        "1-year deal, no extension: $1 buyout.",
        "Last year of contract: 100% of that year's remaining salary.",
        "Cut with 2 years left: 100% current year + 50% of year 2.",
        "Cut with 3 years left: 100% current year + 50% of year 2 + 25% of year 3.",
        "Offseason buy-outs (before the league year starts): 50% of the upcoming contract year, 25% of the year after.",
      ])}
      {h3("Contracted Player on a Relegated Team")}
      {ul(["Player is cut from the roster; contract and all dollars owed are voided."])}
      {h3("Relegated Player Sold to an Active EPL Team")}
      {ul([
        "If sold prior to the end of the EPL summer transfer window: keep on current contract, or cut at no cost.",
        "No fee for a relegated-team player transferred to another EPL team, but still cuttable at no cost.",
        "Must return to the EPL during the first EPL transfer window in September.",
      ])}
    """)

    # ---------------- 5. Youth Academy ----------------
    youth = card("5. Youth Academy System", f"""
      {h3("Youth Player Draft")}
      {ul([
        "Held during the October international break.",
        "Draft order is reverse order of Mega standings at the time.",
        "One non-owned league player per team; a 2nd costs a $15 bounty.",
        "Eligible: under age 20 at the start of the EPL season, not on a current Mega roster.",
      ])}
      {h3("Loss of Protected Homegrown Status")}
      {ul(["A promoted youth player loses protected Homegrown status once they turn 24 at the start of the Mega season."])}
    """, accent="var(--mv-blue)")

    # ---------------- 6. Scoring ----------------
    tiebreakers = f"""
      {h3("Tie Breakers for Playoff Games (Title)")}
      {ol(["Goals Scored", "Assists", "Total accurate passes"])}
    """
    scoring_rows = [
        ("Game Started", "1", "1", "1", "1"), ("Game Played", "1", "1", "1", "1"),
        ("PK Save", "4", "", "", ""), ("Save", "1 per 2", "", "", ""),
        ("Clean Sheet", "5", "4", "2", "1"), ("Red Card", "-3", "-3", "-3", "-3"),
        ("Yellow Card", "-0.5", "-0.5", "-0.5", "-0.5"),
        ("Accurate Crosses", "", "0.5 per 3", "0.5 per 3", "0.5 per 3"),
        ("Accurate Passes", "", "0.5 per 25", "0.5 per 25", "0.5 per 25"),
        ("Assist from shot off post", "", "2", "2", "2"),
        ("Assist off Rebound", "", "2", "2", "2"),
        ("Assist from Own Goal", "", "2", "2", "2"),
        ("Second (Hockey) Assist", "", "1", "1", "1"),
        ("Assist", "", "4", "4", "4"),
        ("Big Chance Created", "", "1", "1", "1"),
        ("Ball Recovery", "", "0.5 per 6", "0.5 per 6", "0.5 per 3"),
        ("Duels Won", "", "0.5 per 6", "0.5 per 6", "0.5 per 6"),
        ("Fouls Suffered", "", "0.5 per 3", "0.5 per 3", "0.5 per 3"),
        ("Goals Against", "-1 per 2", "-1 per 2", "-1 per 3", ""),
        ("Goals Scored", "", "8", "8", "8"),
        ("Interception in the Box", "", "0.5 per 2", "0.5 per 2", "0.5 per 2"),
        ("Interceptions", "", "0.5 per 3", "0.5 per 3", "0.5 per 3"),
        ("Long Ball Accurate", "", "0.5 per 3", "0.5 per 3", "0.5 per 3"),
        ("Own Goal", "", "-5", "-5", "-5"),
        ("Passing Comp %", "", "0.5 for >80%", "0.5 for >80%", "0.5 for >80%"),
        ("Penalty committed", "", "-1", "-1", "-1"),
        ("Penalty Drawn", "", "2", "2", "2"),
        ("Penalty Kick Goal", "", "6", "6", "6"),
        ("Penalty Miss", "", "-2", "-2", "-2"),
        ("Successful final 3rd pass", "", "0.5 per 15", "0.5 per 15", "0.5 per 15"),
        ("Shots on target", "", "0.5 per 3", "0.5 per 3", "0.5 per 3"),
        ("Successful Dribble", "", "0.5 per 3", "0.5 per 3", "0.5 per 3"),
        ("Effective Clearance", "", "0.5 per 3", "0.5 per 3", "0.5 per 3"),
        ("Key Passes", "", "0.5 per 3", "0.5 per 3", "0.5 per 3"),
        ("Tackles won - Last Man", "", "0.5", "0.5", "0.5"),
        ("Tackles Won + Blocked Shots", "", "0.5 per 3", "0.5 per 3", "0.5 per 3"),
    ]
    scoring_table = f"""
      <div class="mv-table-scroll">
        <table class="mv-table mv-sortable">
          <thead><tr><th data-sort-type="text">Scoring</th><th>GK</th><th>D</th><th>M</th><th>F</th></tr></thead>
          <tbody>
            {"".join(f'<tr><td>{name}</td><td>{gk or "&mdash;"}</td><td>{d or "&mdash;"}</td><td>{m or "&mdash;"}</td><td>{f or "&mdash;"}</td></tr>' for name, gk, d, m, f in scoring_rows)}
          </tbody>
        </table>
      </div>
    """
    scoring = card("6. Scoring", tiebreakers + h3("Fantasy Scoring by Position") + scoring_table)

    html = head("Rulez", "rulez.html") + hero_logo() + f"""
    <div class="mv-page-header">
      <h1 class="mv-chrome-text">Rulez</h1>
      <div class="sub">The full 26/27 rulebook &mdash; season structure, financials, rosters, transactions, youth, and scoring &middot;
        <a href="{SOURCE_DOC_URL}" target="_blank" rel="noopener" style="color:inherit;">source doc</a></div>
    </div>
    {season}
    {financials}
    {rosters}
    {acquisition}
    {divestiture}
    {youth}
    {scoring}
""" + foot()

    with open("rulez.html", "w") as f:
        f.write(html)
    print("Updated rulez.html")


if __name__ == "__main__":
    build()
