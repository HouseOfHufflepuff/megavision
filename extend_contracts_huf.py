"""
ONE-TIME WORK -- apply the commissioner's actual HUF contract extensions
to team_player_wages, per the Rulez tab's real formulas:
  - Kept player, 1 remaining forward year -> extend at +50% for a new year
  - Kept player, 2 remaining forward years -> extend at +30% of the last
    year for a 3rd
  - Drafted/purchased player -> +10% per year, up to 3 years max

"Remaining forward years" = seasons on record at/after 26/27 (25/26 is
always historical/sunk at this point, never counted).

Run:
    python3 extend_contracts_huf.py
"""
from datetime import datetime, timezone

from db import connect

CODE = "HUF"
now = datetime.now(timezone.utc).isoformat()


def add_year(cur, player, category, season, wage, source):
    cur.execute(
        "INSERT INTO team_player_wages (team_code, player_name, category, season, wage, source, updated_at) "
        "VALUES (?,?,?,?,?,?,?) "
        "ON CONFLICT(team_code, player_name, season) DO UPDATE SET wage=excluded.wage, source=excluded.source, updated_at=excluded.updated_at",
        (CODE, player, category, season, round(wage, 3), source, now),
    )


def drop_year(cur, player, season):
    cur.execute("DELETE FROM team_player_wages WHERE team_code=? AND player_name=? AND season=?", (CODE, player, season))


def main():
    conn = connect()
    cur = conn.cursor()

    # kept players: 2 forward years (26/27, 27/28) on record -> extend to 3 at +30%
    for player, category in [
        ("Antoine Semenyo", "kept"), ("Morgan Gibbs", "kept"),
        ("Yankuba Minteh", "kept"), ("Sandro Tonali", "kept"),
        ("William Saliba", "youth_legend"),
    ]:
        last = cur.execute(
            "SELECT wage FROM team_player_wages WHERE team_code=? AND player_name=? AND season='27/28'",
            (CODE, player),
        ).fetchone()
        assert last, f"expected a 27/28 base for {player}"
        add_year(cur, player, category, "28/29", last[0] * 1.30, "extension_30pct")

    # Jack Grealish: 1 forward year (26/27) only -> extend to 2 at +50%
    base = cur.execute(
        "SELECT wage FROM team_player_wages WHERE team_code=? AND player_name='Jack Grealish' AND season='26/27'",
        (CODE,),
    ).fetchone()
    assert base
    add_year(cur, "Jack Grealish", "kept", "27/28", base[0] * 1.50, "extension_50pct")

    # Virgil van Dijk: already at 2 forward years (26/27, 27/28) -- target is
    # 2 years, no change needed

    # drafted players extended to 3 years: 26/27 base, +10%/yr compounding
    for player in ("Georginio Rutter", "Alexis Mac Allister"):
        base = cur.execute(
            "SELECT wage FROM team_player_wages WHERE team_code=? AND player_name=? AND season='26/27'",
            (CODE, player),
        ).fetchone()
        assert base, player
        y2 = base[0] * 1.10
        y3 = y2 * 1.10
        add_year(cur, player, "drafted", "27/28", y2, "extension_10pct")
        add_year(cur, player, "drafted", "28/29", y3, "extension_10pct")

    # drafted player extended to 2 years: +10%
    base = cur.execute(
        "SELECT wage FROM team_player_wages WHERE team_code=? AND player_name='Gabriel Martinelli' AND season='26/27'",
        (CODE,),
    ).fetchone()
    assert base
    add_year(cur, "Gabriel Martinelli", "drafted", "27/28", base[0] * 1.10, "extension_10pct")

    # already-1-year drafted players staying at 1 year: no change --
    # Sven Botman, Brennan Johnson, James Hill, Djordje Petrovic,
    # James Maddison, Ruben Dias

    # explicit removals per instruction
    drop_year(cur, "Beto", "26/27")           # Beto: remove his 26/27 salary
    drop_year(cur, "Harvey Elliott", "27/28")  # Harvey Elliott: drop to 1 forward year (26/27 only)

    conn.commit()

    print("HUF wages after extensions:\n")
    rows = cur.execute(
        "SELECT player_name, category, season, wage, source FROM team_player_wages WHERE team_code=? ORDER BY player_name, season",
        (CODE,),
    ).fetchall()
    for r in rows:
        print(" ", r)
    conn.close()


if __name__ == "__main__":
    main()
