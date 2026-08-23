"""
Reusable script for recording a player transfer fee between two teams and
querying its financial impact. update_rosters.py imports team_transfers()
to fold these into each team's Finances tab and financials.html.

Record a transfer:
    python3 transfer.py "Antoine Semenyo" FAV HUF 200 26/27 2026-08-01

from_team is the seller (receives the fee, a credit); to_team is the buyer
(pays the fee, a cost) for the given season. Run update_rosters.py afterward
to rebuild the site with the new figures.
"""
import sys
from datetime import datetime, timezone

from db import connect


def record_transfer(player_name, from_team, to_team, amount, season, transfer_date=None):
    conn = connect()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO transfers (player_name, from_team, to_team, amount, season, transfer_date, created_at) "
        "VALUES (?,?,?,?,?,?,?)",
        (player_name, from_team, to_team, float(amount), season, transfer_date,
         datetime.now(timezone.utc).isoformat()),
    )
    conn.commit()
    conn.close()


def all_transfers():
    """Every recorded transfer, for update_rosters.py to fold in per team."""
    conn = connect()
    rows = conn.execute(
        "SELECT player_name, from_team, to_team, amount, season, transfer_date FROM transfers "
        "ORDER BY season, transfer_date"
    ).fetchall()
    conn.close()
    return [
        {"player_name": r[0], "from_team": r[1], "to_team": r[2], "amount": r[3],
         "season": r[4], "transfer_date": r[5]}
        for r in rows
    ]


# Rulez tab, row 121: "Transfer fee is paid 90% to seller, and 10% to
# league pot."
SELLER_SHARE = 0.90
LEAGUE_CUT = 0.10


def team_transfer_net(code, season, transfers=None):
    """Transfer fee cost on `code` for `season`: the full fee they paid
    buying players (the buyer pays 100% regardless of how it's split on
    the receiving end)."""
    transfers = transfers if transfers is not None else all_transfers()
    return sum(t["amount"] for t in transfers if t["to_team"] == code and t["season"] == season)


def team_transfer_revenue(code, season, transfers=None):
    """Transfer revenue on `code` for `season`: their 90% cut of fees for
    players they sold."""
    transfers = transfers if transfers is not None else all_transfers()
    return sum(t["amount"] * SELLER_SHARE for t in transfers if t["from_team"] == code and t["season"] == season)


def league_pot_transfer_levy(transfers=None, season=None):
    """The league's 10% cut of every transfer fee -- a one-time addition to
    the league pot when the transfer happens, not a per-week flow."""
    transfers = transfers if transfers is not None else all_transfers()
    return sum(t["amount"] * LEAGUE_CUT for t in transfers if season is None or t["season"] == season)


if __name__ == "__main__":
    if len(sys.argv) != 7:
        print("Usage: python3 transfer.py PLAYER FROM_TEAM TO_TEAM AMOUNT SEASON DATE")
        sys.exit(1)
    _, player, frm, to, amount, season, date = sys.argv
    record_transfer(player, frm, to, amount, season, date)
    print(f"Recorded: {player} {frm} -> {to} for ${float(amount):.2f} ({season}, {date})")
