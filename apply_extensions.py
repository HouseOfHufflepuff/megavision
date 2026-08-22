"""
ONE-TIME WORK -- apply each team's real negotiated extensions (from the
"Megavision (new thread)" Gmail thread, Aug 17-21 2026) to team_player_wages,
using the Rulez tab's real formulas:
  - Kept player: 1 forward year -> +50% for a new year; 2 forward years ->
    +30% of the last year for a 3rd. Can chain (1->2->3) if a team asked
    for 3 years on a player who only had 1.
  - Drafted player: flat +10% of the 26/27 base per additional year (not
    compounding -- see HUF's Rutter/Mac Allister correction), up to 3 years.

Run:
    python3 apply_extensions.py
"""
from datetime import datetime, timezone

from db import connect
from merge_contracts_onetime import name_match, season_next

now = datetime.now(timezone.utc).isoformat()


def get_player_row_name(cur, code, requested_name):
    """Resolve a name from the email against whatever's actually stored for
    this team in team_player_wages (fuzzy, handles typos/formatting diffs)."""
    names = [r[0] for r in cur.execute(
        "SELECT DISTINCT player_name FROM team_player_wages WHERE team_code=?", (code,)
    ).fetchall()]
    matches = [n for n in names if name_match(n, requested_name)]
    if len(matches) == 1:
        return matches[0]
    if len(matches) > 1:
        print(f"  AMBIGUOUS '{requested_name}' in {code}: {matches} -- skipped")
        return None
    print(f"  NOT FOUND '{requested_name}' in {code} -- skipped")
    return None


def forward_rows(cur, code, player):
    return cur.execute(
        "SELECT season, wage FROM team_player_wages WHERE team_code=? AND player_name=? AND season>='26/27' ORDER BY season",
        (code, player),
    ).fetchall()


def insert(cur, code, player, category, season, wage, source):
    cur.execute(
        "INSERT INTO team_player_wages (team_code, player_name, category, season, wage, source, updated_at) "
        "VALUES (?,?,?,?,?,?,?) ON CONFLICT(team_code, player_name, season) DO UPDATE SET "
        "wage=excluded.wage, source=excluded.source, category=excluded.category, updated_at=excluded.updated_at",
        (code, player, category, season, round(wage, 3), source, now),
    )


def extend_kept(cur, code, requested_name, category, target_years):
    player = get_player_row_name(cur, code, requested_name)
    if not player:
        return
    fwd = forward_rows(cur, code, player)
    if not fwd:
        print(f"  {player} ({code}): no forward wage on record, can't extend -- skipped")
        return
    years = len(fwd)
    last_season, last_wage = fwd[-1]
    while years < target_years:
        pct = 1.50 if years == 1 else 1.30
        src = "extension_50pct" if years == 1 else "extension_30pct"
        new_wage = last_wage * pct
        new_season = season_next(last_season)
        insert(cur, code, player, category, new_season, new_wage, src)
        print(f"  {player} ({code}): +{new_season}=${new_wage:.2f} ({src})")
        last_season, last_wage = new_season, new_wage
        years += 1


def extend_drafted(cur, code, requested_name, target_years):
    player = get_player_row_name(cur, code, requested_name)
    if not player:
        return
    fwd = forward_rows(cur, code, player)
    if not fwd:
        print(f"  {player} ({code}): no forward wage on record, can't extend -- skipped")
        return
    base_season, base_wage = fwd[0]
    years = len(fwd)
    last_season = fwd[-1][0]
    n = years
    while n < target_years:
        n += 1
        new_wage = base_wage * (1 + 0.10 * (n - 1))
        new_season = season_next(last_season)
        insert(cur, code, player, "drafted", new_season, new_wage, "extension_10pct_flat")
        print(f"  {player} ({code}): +{new_season}=${new_wage:.2f} (extension_10pct_flat)")
        last_season = new_season


def drop_season(cur, code, requested_name, season):
    player = get_player_row_name(cur, code, requested_name)
    if not player:
        return
    cur.execute("DELETE FROM team_player_wages WHERE team_code=? AND player_name=? AND season=?", (code, player, season))
    print(f"  {player} ({code}): dropped {season}")


def cut_player(cur, code, requested_name):
    player = get_player_row_name(cur, code, requested_name)
    if not player:
        return
    cur.execute("DELETE FROM team_player_wages WHERE team_code=? AND player_name=?", (code, player))
    print(f"  {player} ({code}): cut, all wage rows removed")


def main():
    conn = connect()
    cur = conn.cursor()

    print("=== HUF ===")
    for p in ["Georginio Rutter", "Antoine Semenyo", "Morgan Gibbs-White", "Yankuba Minteh", "Alexis Mac Allister"]:
        cat = "drafted" if p in ("Georginio Rutter", "Alexis Mac Allister") else "kept"
        (extend_drafted if cat == "drafted" else extend_kept)(cur, "HUF", p, *(([3]) if cat == "drafted" else ("kept", 3)))
    for p, cat in [("Jack Grealish", "kept"), ("Gabriel Martinelli", "drafted"), ("Sandro Tonali", "kept")]:
        (extend_drafted(cur, "HUF", p, 2) if cat == "drafted" else extend_kept(cur, "HUF", p, "kept", 2))
    extend_kept(cur, "HUF", "William Saliba", "youth_legend", 3)

    print("=== NAC ===")
    for p in ["Metata", "Yoane Wissa", "Dejan Kulusevski", "Enzo Le Fee", "Tyrick Mitchell"]:
        extend_kept(cur, "NAC", p, "kept", 2)
    for p in ["Rayan", "Emiliano Buendia", "Nordi Mukiele"]:
        extend_drafted(cur, "NAC", p, 3)
    extend_kept(cur, "NAC", "Cole Palmer", "youth_legend", 3)
    cut_player(cur, "NAC", "Curtis Jones")

    print("=== REN ===")
    for p in ["Richarlison", "Bruno Fernandes", "Riccardo Calafiori", "Marcus Tavernier", "Jeremie Frimong", "Milos Kerkez"]:
        extend_kept(cur, "REN", p, "kept", 3)
    for p in ["Pedro Neto", "Pascal Gross"]:
        extend_drafted(cur, "REN", p, 3)

    print("=== DU ===")
    for p in ["Alexander Isak", "Igor Thiago", "Marcos Senesi", "Malo Gusto", "Alex Iwobi"]:
        extend_kept(cur, "DU", p, "kept", 3)
    for p in ["Boubacar Kamara", "Kaoru Mitoma", "Oscar Bobb", "Maxence Lacroix"]:
        extend_drafted(cur, "DU", p, 3)

    print("=== ASS ===")
    for p in ["Josko Gvardiol", "Bazoumana Touré"]:
        extend_drafted(cur, "ASS", p, 3)
    for p, cat in [("Liam Delap", "youth_players"), ("Kiernan Dewsbury-Hall", "kept"), ("Erling Haaland", "youth_legend"),
                   ("Justin Kluivert", "kept"), ("Benjamin Sesko", "youth_players"), ("Carlos Alcaraz", "kept")]:
        player = get_player_row_name(cur, "ASS", p)
        if player:
            cur_years = len(forward_rows(cur, "ASS", player))
            extend_kept(cur, "ASS", p, cat, cur_years + 1)
    cut_player(cur, "ASS", "Cristian Romero")
    drop_season(cur, "ASS", "Daniel James", "27/28")

    print("=== QFC ===")
    for p in ["Hugo Ektike", "Eberechi Eze", "Martin Zubimendi", "Jeremy Doku", "Piero Hincaipe", "Jurrien Timber"]:
        extend_kept(cur, "QFC", p, "kept", 3)
    for p in ["Mohammed Kudus", "Abdukodir Khusanov", "Jeremy Jacquet"]:
        extend_drafted(cur, "QFC", p, 3)
    drop_season(cur, "QFC", "Dominic Solanke", "27/28")
    cut_player(cur, "QFC", "Jacob Ramsey")
    cut_player(cur, "QFC", "Rico Lewis")

    print("=== CRG ===")
    extend_drafted(cur, "CRG", "Reece James", 3)
    extend_drafted(cur, "CRG", "Matty Cash", 2)
    for p in ["Enzo", "Guimaraes", "Szoboszloi", "Van Hecke", "Mbeumo", "Evanilson"]:
        extend_kept(cur, "CRG", p, "kept", 3)
    extend_kept(cur, "CRG", "Declan Rice", "youth_legend", 3)

    # --- post-hoc patches: names the initial pass couldn't resolve ---
    print("=== patches ===")
    # NAC: Le Fee / Mitchell had only a sunk 24/25 wage on record (no 26/27
    # base to extend from) -- backfill their real 26/27 from the keeper
    # sheet's own y1 column before extending to the requested 2 years.
    insert(cur, "NAC", "Tyrick Mitchell", "kept", "26/27", 6.655, "cut_em_sheet")
    insert(cur, "NAC", "Enzo Le Fee", "kept", "26/27", 4.4, "cut_em_sheet")
    extend_kept(cur, "NAC", "Tyrick Mitchell", "kept", 2)
    extend_kept(cur, "NAC", "Enzo Le Fee", "kept", 2)

    # QFC: stored name carried a stray trailing position-code token
    # ("Jeremy Doku M") that the fuzzy matcher can't see past -- rename in
    # place, then extend normally.
    cur.execute("UPDATE team_player_wages SET player_name='Jeremy Doku' WHERE team_code='QFC' AND player_name='Jeremy Doku M'")
    extend_kept(cur, "QFC", "Jeremy Doku", "kept", 3)

    # REN: email's "F-Wright" is Haji Wright (drafted, fpl_price baseline).
    extend_drafted(cur, "REN", "Haji Wright", 3)

    print("=== POW (last plan Sam sent -- never got a final confirm, applying as-is per instruction) ===")
    for p in ["Chris Richards", "Harvey Barnes", "Matheus Cunha", "Brian Brobbey", "Omari Hutchinson"]:
        extend_drafted(cur, "POW", p, 3)
    for p in ["Rayan Ait Nouri", "Maxim DeCuyper", "Youri Tilemans", "Jaidon Anthony"]:
        extend_kept(cur, "POW", p, "kept", 3)
    cut_player(cur, "POW", "Djed Spence")  # "Djed Spence is gone as well" -- left the team

    conn.commit()
    conn.close()


if __name__ == "__main__":
    main()
