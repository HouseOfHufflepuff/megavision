"""
Rulez page -- the 26/27 offseason calendar and contract/loan rules, as
communicated by the commissioner. Static content (a rules memo, not
live-fetched data); re-run this and edit the content below whenever the
rules get updated or the Rulez tab gets its planned redraft.

Run:
    python3 build_rulez.py
"""
from common import head, foot, hero_logo

DATES = [
    {
        "date": "Thursday, August 20",
        "items": [
            "Rosters must be 17 outfield players + 1 GK, with a maximum of 9 players on multi-year "
            "contracts (Youth Legend and Promoted Youth aged 23 or younger as of August 1 are excluded "
            "from that 9-player cap).",
            "Window closes to extend drafted players &mdash; extensions available at +10% for 3 years.",
            "Team-to-team transfers allowed during this window; extensions can be done at +10%.",
            "Contract years can be dropped on existing contracts at any point up to this date.",
            "Drafted players can be cut for $1 up to this date.",
            "Teams below 17 outfield players may pick up fillers at their FPL contract amount, as long "
            "as the player is on the same real-world team they were on at draft day.",
            "Stadium expansions should be completed by this date.",
        ],
    },
    {
        "date": "Thursday, September 3",
        "items": [
            "Likely date for the Free Agent Auction.",
            "If a team extends any free agent at 50%/30% terms while already holding 9 multi-year "
            "contracts, a player must be cut or transferred to stay under the cap.",
        ],
    },
    {
        "date": "Thursday, October 8 <span class=\"dim\" style=\"font-weight:400;\">(International Youth Day)</span>",
        "items": [
            "Any unpromoted youth player on an EPL roster who turns 24 or older by August 1 must be "
            "given a contract by this date, or the team releases their rights. A list of affected "
            "players will be published separately.",
            "Proposed deadline for year-long youth loans: a youth player aged 23 or younger can be "
            "loaned for the year, with the receiving team free to use them without restriction. "
            "Loan-for-loan swaps of similar players are a common structure for this.",
            "The Youth Draft should conclude by this date.",
        ],
    },
]

LOAN_OPTIONS = [
    ("Loans count against the loaning team's cap",
     "A loaned player still counts toward the 9-contract limit of the team sending them out. This "
     "makes taking a player on loan more attractive to the receiving team, since they get a top player "
     "without spending one of their own 9 slots."),
    ("Loans count against the receiving team's cap",
     "The team taking a player on loan (on a multi-year deal) has it count against their own 9-contract "
     "limit. The loaning team gets a temporary boost, entering the new year with 10 kept multi-year "
     "contracts (though they'll still need to get back to 9 the following season). This increases the "
     "incentive to loan a player out and raises the bar for who's worth taking on loan."),
    ("Two free loan slots per team",
     "Each team can loan out up to two players on multi-year deals, and while those loans are active, "
     "the contracts don't count against either team's 9-player limit. This would meaningfully increase "
     "loan activity, since two teams could effectively \"stash\" each other's multi-year keepers without "
     "either side losing a roster slot. If adopted, a league loan fee (on top of the existing 10% league "
     "cut on money changing hands) has been proposed to help offset lost cut/unsettled-contract revenue."),
]


def build():
    date_sections = "\n".join(
        f"""
    <section class="card mv-card">
      <h2 class="mv-chrome-text" style="margin-top:0;">{d["date"]}</h2>
      <ul style="line-height:1.8;padding-left:20px;margin:0;">
        {"".join(f'<li>{item}</li>' for item in d["items"])}
      </ul>
    </section>"""
        for d in DATES
    )

    loan_items = "\n        ".join(
        f'<li style="margin-bottom:14px;"><strong>{title}.</strong> {body}</li>'
        for title, body in LOAN_OPTIONS
    )

    html = head("Rulez", "rulez.html") + hero_logo() + f"""
    <div class="mv-page-header">
      <h1 class="mv-chrome-text">Rulez</h1>
      <div class="sub">26/27 offseason calendar &mdash; contract, transfer, loan, and draft deadlines</div>
    </div>
    {date_sections}

    <section class="card mv-card" style="border-left:4px solid var(--mv-violet);">
      <div class="mv-badge" style="background:transparent;border:1px solid var(--mv-violet);color:var(--mv-violet);margin-bottom:10px;">Proposed &mdash; Under Review</div>
      <h2 class="mv-chrome-text" style="margin-top:0;">Multi-Year Contract Limit vs. Loans</h2>
      <p style="color:var(--mv-ink-muted);line-height:1.7;">
        The new 9-multi-year-contract cap creates friction for loans, which have traditionally involved
        players already on multi-year deals &mdash; burning one of only 9 slots to loan someone out reduces
        the incentive unless the player or compensation is exceptional. Three options are on the table:
      </p>
      <ol style="line-height:1.7;padding-left:20px;">
        {loan_items}
      </ol>
    </section>

    <section class="card mv-card">
      <div style="color:var(--mv-ink-muted);font-size:13px;">
        A full redraft of the Rulez tab is planned before August 21, to be proposed to the league for review.
      </div>
    </section>
""" + foot()

    with open("rulez.html", "w") as f:
        f.write(html)
    print("Updated rulez.html")


if __name__ == "__main__":
    build()
