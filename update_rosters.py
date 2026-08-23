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
import json
import subprocess
import sys

from common import (
    TEAMS, head, foot, hero_logo, fetch_live_workbook, EXPORT_URL, fetch_trophy_room,
    tally_trophies, COMP_ABBR, fetch_fans, owner_short, POSITION_ORDER,
    position_sort_key, fetch_youth, fetch_all_season_labels,
    fetch_season_salary_totals, fetch_standings_reference,
    fetch_firm_legacy, compute_fan_formula, fetch_stadiums, club_full_name,
)
from player_clean import clean_player
import db
import sync_fpl_stats as fpl
import transfer as trx

FPL_MIN_PRICE = 4.0  # FPL's own price floor -- used as a fallback for unmatched players

CURRENT_SALARY_SEASON = "25/26"

STATUS_COLOR = {
    "Promoted": "var(--mv-gold)",
    "Released": "var(--mv-ink-dim)",
    "Frozen": "var(--mv-crimson)",
    "Active": "var(--mv-ink)",
}

TROPHY_ACCENTS = ["var(--mv-gold)", "var(--mv-blue)", "var(--mv-violet)", "var(--mv-pink)", "var(--mv-crimson)"]

# league formation: 3-4-3 (+ 1 GK), field order top (attack) to bottom (GK)
FORMATION = [("F", 3), ("M", 4), ("D", 3), ("GK", 1)]

parser = argparse.ArgumentParser()
parser.add_argument("--push", action="store_true")
args = parser.parse_args()


def money(v):
    if v is None:
        return "—"
    if isinstance(v, (int, float)):
        return f"${v:,.2f}"
    return str(v)


def eur(v):
    if not isinstance(v, (int, float)):
        return "—"
    if v >= 1_000_000:
        return f"€{v / 1_000_000:,.1f}M"
    if v >= 1_000:
        return f"€{v / 1_000:,.0f}K"
    return f"€{v:,.0f}"


def num1(v):
    return f"{v:.1f}" if isinstance(v, (int, float)) else "—"


def numi(v):
    return f"{v:,.0f}" if isinstance(v, (int, float)) else "—"


def finance_season_header(season):
    if season == CURRENT_SEASON:
        return f'<span style="color:var(--mv-gold)">{season}</span>'
    return season


# Row ranges for each box within a team's column block on the "CUT EM IF YA
# GOT EM" tab -- the single source of truth for who's actually on the 26/27
# roster. "Into Draft Pool" is deliberately excluded: those players simply
# aren't in any of these three boxes, so they're excluded from the site by
# construction, not by a name-matching guess.
KEEP_BOX_ROWS = {
    "kept": (22, 29),
    "youth_legend": (31, 31),
    "youth_players": (34, 40),
}
CATEGORY_LABEL = {"kept": "Kept", "youth_legend": "Youth Legend", "youth_players": "Youth Player", "drafted": "Drafted '27"}
CATEGORY_BADGE_COLOR = {"kept": "var(--mv-ink-muted)", "youth_legend": "var(--mv-gold)", "youth_players": "var(--mv-blue)", "drafted": "var(--mv-violet)"}


def find_keeper_block_col(label_row, code):
    # the sheet labels this team's block "RNE"; every other code matches TEAMS directly
    sheet_code = "RNE" if code == "REN" else code
    for i, v in enumerate(label_row):
        if v == sheet_code:
            return i
    return None


def parse_keeper_roster(wb, code):
    """This team's actual 26/27 roster: Kept Contracts + Youth Legend of the
    Club + Youth Players, straight from the CUT EM IF YA GOT EM tab. Each
    player carries which box they came from (category) and their 26/27 +
    27/28 salary, which is all that tab tracks (no buyout/3rd-year column
    here -- that lives on each team's own roster tab, which this
    intentionally does NOT read from anymore, since that tab still lists
    players who were actually cut)."""
    ws = wb["CUT EM IF YA GOT EM"]
    rows = list(ws.iter_rows(min_row=1, max_row=101, values_only=True))
    label_row = rows[4]
    col = find_keeper_block_col(label_row, code)
    if col is None:
        return None

    roster = []
    for category, (start, end) in KEEP_BOX_ROWS.items():
        for r in range(start, end + 1):
            row = rows[r - 1]
            if not row[col]:
                continue
            y1 = row[col + 2] if isinstance(row[col + 2], (int, float)) else None
            y2 = row[col + 3] if isinstance(row[col + 3], (int, float)) else None
            pos = (row[col + 1] or "").strip().upper()
            if pos == "G":
                pos = "GK"
            roster.append({
                "player": row[col],
                "pos": pos,
                "category": category,
                "y1": y1,
                "y2": y2,
                "current_salary": y1 or 0,
            })
    return roster


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
    # the REAL regular-season schedule for our 12 teams, straight off
    # Fantrax's own getLeagueInfo -- NOT the Google Sheet's "League
    # Schedule" tab, whose home/away is simply wrong (confirmed against
    # this same endpoint: 3 of 6 week-1 fixtures had home/away flipped).
    # Never source the schedule from the sheet again. Fantrax's scoring
    # period 1 is entirely Juniors-squad games (none of our 12 real teams);
    # our teams' real season starts at period 2, displayed as "GW 1" (see
    # fantrax_live.fetch_schedule -- displayed week = Fantrax period - 1).
    schedule_games = fantrax_live.fetch_schedule(_fx_sess)
except Exception as e:
    print(f"WARN: live Fantrax fetch failed ({e}); depth charts fall back to salary order, "
          f"Fan Formula/teams-table ratings will be omitted", file=sys.stderr)
    fantrax_standings, fantrax_rosters, top_xi, mbp, fan_formula = {}, {}, [], None, {}
    schedule_games = []

REGULAR_SEASON_WEEKS = 35  # Fantrax periods 2-36 displayed as GW 1-35 (period 1 is Juniors-only)
games_by_team = {code: [] for code, _, _ in TEAMS}
for g in schedule_games:
    if g["home"] in games_by_team:
        games_by_team[g["home"]].append(g)
    if g["away"] in games_by_team:
        games_by_team[g["away"]].append(g)
for _code in games_by_team:
    games_by_team[_code].sort(key=lambda g: g["week"])
print(f"Loaded {len(schedule_games)} real regular-season games across {len(games_by_team)} teams from Fantrax.")


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

# 26/27 hasn't kicked off yet -- every team starts 0, same as the 0-0-0
# record already shown on each team page; Fantrax's live standings still
# reflect the prior season, not a real record for the new one.
team_wins = {code: 0 for code, _, _ in TEAMS}

# EA FC 26 ratings + 2025/26 FPL performance stats, read from mega.db
# (populated by the separate sync_fc26_ratings.py / sync_fpl_stats.py
# scripts -- run those periodically, not fetched live on every site
# build). last name (lower) -> record.
global_fc26_lookup = {}
global_stats_lookup = {}
try:
    import db as _db
    _conn = _db.connect()
    for _pname, _rating in _conn.execute(
        "SELECT player_name, fc26_rating FROM team_players WHERE fc26_rating IS NOT NULL"
    ):
        if _pname:
            global_fc26_lookup[_pname.split()[-1].lower()] = _rating
    for _row in _conn.execute(
        "SELECT player_name, fc26_rating, fc26_potential, fc26_value_eur, "
        "fpl_starts, fpl_goals, fpl_assists, fpl_minutes, fpl_tackles, fpl_cbi, fpl_xg "
        "FROM team_players WHERE fc26_rating IS NOT NULL OR fpl_minutes IS NOT NULL"
    ):
        _pname = _row[0]
        if _pname:
            global_stats_lookup[_pname.split()[-1].lower()] = {
                "fc26": _row[1], "fc26_pot": _row[2], "fc26_value": _row[3],
                "fpl_starts": _row[4], "fpl_goals": _row[5], "fpl_assists": _row[6],
                "fpl_minutes": _row[7], "fpl_tackles": _row[8], "fpl_cbi": _row[9], "fpl_xg": _row[10],
            }
    _conn.close()
    print(f"Loaded {len(global_fc26_lookup)} FC 26 ratings and {len(global_stats_lookup)} scouting "
          f"records from mega.db (run sync_fc26_ratings.py / sync_fpl_stats.py to refresh).")
except Exception as e:
    print(f"WARN: could not read FC 26/FPL stats from mega.db ({e}); "
          f"ratings will fall back to live Fantrax fantasy points", file=sys.stderr)

# Real money: team_player_wages (mega.db) is the source of truth for
# salary now -- built by merge_contracts_onetime.py + the per-team
# extend_contracts_*.py scripts, real multi-year contracts (25/26 through
# however many years a player's been extended), not a live re-derivation.
# Live FPL price is now only a fallback for any team/player that hasn't
# been through that merge yet.
print("Fetching live FPL prices (fallback for anyone not yet in team_player_wages)...")
_fpl_elements = fpl.fetch_elements()
_fpl_lookup = fpl.build_lookup(_fpl_elements)


def fpl_price(player_name, club=None):
    if not player_name:
        return FPL_MIN_PRICE
    tokens = player_name.split()
    last = tokens[-1]
    first_initial = tokens[0][0] if tokens else None
    e = fpl.match(_fpl_lookup, last, first_initial, club)
    return e["now_cost"] / 10 if e else FPL_MIN_PRICE


_wages_conn = db.connect()
_wages_by_team = {}
for _team_code, _pname, _season, _wage in _wages_conn.execute(
    "SELECT team_code, player_name, season, wage FROM team_player_wages"
):
    try:
        _wage = float(str(_wage).replace(",", "."))
    except (TypeError, ValueError):
        print(f"WARN: bad wage value {_wage!r} for {_team_code}/{_pname}/{_season}, skipping", file=sys.stderr)
        continue
    _wages_by_team.setdefault(_team_code, {}).setdefault(_pname, {})[_season] = _wage
_wages_conn.close()
print(f"Loaded real contract wages for {sum(len(v) for v in _wages_by_team.values())} players from team_player_wages.")

_all_transfers = trx.all_transfers()
print(f"Loaded {len(_all_transfers)} transfer{'s' if len(_all_transfers) != 1 else ''} from transfers.")

ALL_SEASONS = ["25/26", "26/27", "27/28", "28/29"]
CURRENT_SEASON = "26/27"


def player_wages(code, player_name, club=None):
    """{season: wage} for this player, real contract data if we have it
    (team_player_wages), else a single-season fallback at live FPL price."""
    team_wages = _wages_by_team.get(code, {})
    if player_name in team_wages:
        return team_wages[player_name]
    return {CURRENT_SEASON: fpl_price(player_name, club)}


# the actual 26/27 draft results (one-time historical fact, see
# data/draft_picks_2627.json's header note for how it was generated) --
# only the 12 junior teams drafted, since senior rosters were already full
# from keepers and their turns were passed every round.
_drafted_by_code = {}
with open("data/draft_picks_2627.json") as _f:
    for _d in json.load(_f):
        _drafted_by_code.setdefault(_d["code"], []).append(_d)
print(f"Loaded {sum(len(v) for v in _drafted_by_code.values())} drafted picks from data/draft_picks_2627.json.")

updated = []
financial_rows = []

for code, name, owners in TEAMS:
    roster = parse_keeper_roster(wb, code)
    if roster is None:
        print(f"WARN: no CUT EM IF YA GOT EM block for {code}, skipping", file=sys.stderr)
        continue

    # add this year's actual draft picks (junior team, real Fantrax results)
    # onto the parent senior team's roster -- these are real players with a
    # real salary now, not the historical/informational Youth Draft History
    for _d in _drafted_by_code.get(code, []):
        pos = (_d["pos"] or "").strip().upper()
        if pos == "G":
            pos = "GK"
        roster.append({
            "player": _d["name"], "pos": pos, "category": "drafted",
            "y1": None, "y2": None, "current_salary": 0,
            "clean_name": _d["name"], "club_full": club_full_name(_d["club"]),
            "_drafted_club": _d["club"],
        })

    roster_size = len(roster)

    stadium_info = stadiums.get(code, {})
    stadium_name = stadium_info.get("stadium") or ""
    cap = stadium_info.get("capacity")
    capacity_str = f"{cap:,.0f}" if isinstance(cap, (int, float)) else str(cap or "—")

    def category_badge(p):
        cat = p["category"]
        if cat == "kept":
            return ""
        color = CATEGORY_BADGE_COLOR[cat]
        return (f'<span class="mv-badge" style="background:transparent;border:1px solid {color};'
                f'color:{color};font-size:9px;padding:1px 6px;margin-left:6px;">{CATEGORY_LABEL[cat]}</span>')

    def player_label(p):
        return (p["clean_name"] or p["player"]) + category_badge(p)

    # ---- scrub the raw "R Dias - D MCI" sheet field into its own columns:
    # clean name, club, live Fantrax fantasy points, EA FC 26 rating -- all
    # matched by cleaned last name ----
    team_fpts = fpts_lookup(code)
    for p in roster:
        if p["category"] == "drafted":
            # already-clean name/club straight from Fantrax draft results,
            # not the sheet's messy "Name - Pos Club" format -- clean_player()
            # would mis-parse it
            club_for_price = p.pop("_drafted_club", None)
        else:
            cleaned = clean_player(p["player"], p["pos"])
            p["clean_name"] = cleaned["player_name"]
            p["club_full"] = club_full_name(cleaned["real_club"])
            club_for_price = cleaned["real_club"]
        last = (p["clean_name"] or "").split()[-1].lower() if p["clean_name"] else ""
        p["fpts"] = team_fpts.get(last)
        # real contract wages -- team_player_wages if we have it (real,
        # possibly multi-year), else a single-season live FPL price fallback
        wages = player_wages(code, p["clean_name"], club_for_price)
        p["wages"] = wages
        # fall back to the earliest *forward* season on record (never 25/26,
        # which is historical/sunk -- a player with no forward salary, e.g.
        # dropped down to $0 this year, should show $0, not their old
        # historical value)
        _forward = {s: w for s, w in wages.items() if s >= CURRENT_SEASON}
        p["current_salary"] = wages.get(CURRENT_SEASON) if CURRENT_SEASON in wages else (min(_forward.items())[1] if _forward else 0)
        p["fc26"] = global_fc26_lookup.get(last)
        stats = global_stats_lookup.get(last) or {}
        p["fc26_pot"] = stats.get("fc26_pot")
        p["fc26_value"] = stats.get("fc26_value")
        p["fpl_starts"] = stats.get("fpl_starts")
        p["fpl_goals"] = stats.get("fpl_goals")
        p["fpl_assists"] = stats.get("fpl_assists")
        p["fpl_minutes"] = stats.get("fpl_minutes")
        p["fpl_tackles"] = stats.get("fpl_tackles")
        p["fpl_cbi"] = stats.get("fpl_cbi")
        p["fpl_xg"] = stats.get("fpl_xg")
        mins = p["fpl_minutes"]
        if isinstance(mins, (int, float)) and mins > 0:
            p["g_per90"] = (p["fpl_goals"] or 0) * 90 / mins
            p["ga_per90"] = ((p["fpl_goals"] or 0) + (p["fpl_assists"] or 0)) * 90 / mins
            p["xg_per90"] = (p["fpl_xg"] or 0) * 90 / mins
        else:
            p["g_per90"] = p["ga_per90"] = p["xg_per90"] = None

    # payroll: every player on the roster counts, salary is now each
    # player's real FPL price (set above), computed only after that's done
    total_payroll = sum(p["current_salary"] for p in roster)
    pos_counts = {}
    for p in roster:
        pos_counts[p["pos"]] = pos_counts.get(p["pos"], 0) + 1
    season_net = -total_payroll  # no games/revenue yet this season

    _matched_fpts = [p["fpts"] for p in roster if isinstance(p["fpts"], (int, float))]
    avg_fpts = (sum(_matched_fpts) / len(_matched_fpts)) if _matched_fpts else None
    _matched_fc26 = [p["fc26"] for p in roster if isinstance(p["fc26"], (int, float))]
    avg_fc26 = (sum(_matched_fc26) / len(_matched_fc26)) if _matched_fc26 else None

    # group by position (GK, D, M, F, then anything else), salary desc within group
    grouped = sorted(roster, key=lambda p: (position_sort_key(p["pos"]), -p["current_salary"]))

    def fc26_plain(p):
        return f'{p["fc26"]:,.0f}' if isinstance(p["fc26"], (int, float)) else "—"

    def fpts_plain(p):
        return f'{p["fpts"]:,.1f}' if isinstance(p["fpts"], (int, float)) else "—"

    def sort_val(v):
        return v if isinstance(v, (int, float)) else -1

    roster_rows = []
    for p in grouped:
        roster_rows.append(
            f'<tr><td>{player_label(p)}</td><td class="dim">{p["club_full"] or "—"}</td><td>{p["pos"]}</td>'
            f'<td style="color:{CATEGORY_BADGE_COLOR[p["category"]]};">{CATEGORY_LABEL[p["category"]]}</td>'
            f'<td data-sort="{sort_val(p["fc26"])}" style="color:var(--mv-gold);font-weight:700;">{fc26_plain(p)}</td>'
            f'<td data-sort="{sort_val(p["fpts"])}" class="dim">{fpts_plain(p)}</td>'
            f'<td data-sort="{p["current_salary"]}"><strong style="color:var(--mv-gold)">{money(p["current_salary"])}</strong></td></tr>'
        )

    # position-count summary row -- <tfoot>, so it's excluded from sorting
    ordered_pos = [p for p in POSITION_ORDER if p in pos_counts] + \
                  [p for p in pos_counts if p not in POSITION_ORDER]
    counts_line = "  &middot;  ".join(f"{pos_counts[p]} {p}" for p in ordered_pos)
    roster_total_row = f'<tr><td colspan="7">{roster_size} total &middot; {counts_line}</td></tr>'

    # ---- finances: the same roster, one column per forward season that
    # anyone on this roster actually has a real contract year for (25/26
    # never shown -- it's already sunk) ----
    team_transfers = [t for t in _all_transfers if t["from_team"] == code or t["to_team"] == code]
    finance_seasons = [s for s in ("26/27", "27/28", "28/29")
                        if any(s in p["wages"] for p in roster) or any(t["season"] == s for t in team_transfers)]
    finance_rows = []
    for p in grouped:
        cells = "".join(
            f'<td data-sort="{sort_val(p["wages"].get(season))}">'
            + (f'<strong style="color:var(--mv-gold)">{money(p["wages"][season])}</strong>' if season in p["wages"] else "—")
            + "</td>"
            for season in finance_seasons
        )
        finance_rows.append(
            f'<tr><td>{player_label(p)}</td><td class="dim">{p["club_full"] or "—"}</td><td>{p["pos"]}</td>'
            f'<td style="color:{CATEGORY_BADGE_COLOR[p["category"]]};">{CATEGORY_LABEL[p["category"]]}</td>'
            f'{cells}</tr>'
        )
    # transfer fees as their own line item -- a cost for the buyer only.
    # Selling isn't tracked as revenue yet (that's part of the not-yet-built
    # revenue system), so the seller shows nothing here.
    for t in team_transfers:
        if t["to_team"] != code:
            continue
        cells = "".join(
            f'<td data-sort="{t["amount"] if season == t["season"] else 0}">'
            + (f'<strong style="color:var(--mv-crimson)">{money(t["amount"])}</strong>' if season == t["season"] else "—")
            + "</td>"
            for season in finance_seasons
        )
        finance_rows.append(
            f'<tr><td colspan="4" class="dim">Transfer Fee &mdash; Signed {t["player_name"]} from {t["from_team"]}</td>{cells}</tr>'
        )
    finance_season_totals = [
        sum(p["wages"].get(season, 0) for p in roster)
        + trx.team_transfer_net(code, season, _all_transfers)
        for season in finance_seasons
    ]
    finance_total_row = (
        f'<tr><td colspan="4">{roster_size} total &middot; {counts_line}</td>'
        + "".join(f'<td>{money(t)}</td>' for t in finance_season_totals)
        + "</tr>"
    )

    # ---- GW: this team's real regular-season matchups straight off
    # Fantrax's own schedule (36 scoring periods; 37-38 are playoffs -- see
    # fantrax_live.fetch_schedule). The Google Sheet's "League Schedule" tab
    # is NOT used for this -- its home/away is simply wrong (confirmed
    # against Fantrax itself: 3 of 6 week-1 fixtures were flipped). Weekly
    # salary is season payroll spread evenly across the 36 real regular-
    # season weeks. Fans/Ticket Revenue/P&L are left blank -- there's no
    # real revenue model wired up yet, so showing a number there would be
    # fabricated. Transfer fees are season-level, not weekly, so they get
    # their own row at the bottom that feeds the season cost total. ----
    weekly_salary = total_payroll / REGULAR_SEASON_WEEKS if total_payroll else 0
    gw_rows = []
    for g in games_by_team.get(code, []):
        is_home = g["home"] == code
        home_label = f'<strong style="color:var(--mv-gold)">{g["home"]}</strong>' if is_home else g["home"]
        away_label = f'<strong style="color:var(--mv-gold)">{g["away"]}</strong>' if not is_home else g["away"]
        gw_rows.append(
            f'<tr><td data-sort="{g["week"]}">{g["week"]}</td>'
            f'<td data-sort="{weekly_salary}">{money(weekly_salary)}</td>'
            f'<td>{home_label}</td><td>{away_label}</td>'
            f'<td class="dim" data-sort="0">&mdash;</td>'
            f'<td class="dim" data-sort="0">&mdash;</td>'
            f'<td class="dim" data-sort="0">&mdash;</td></tr>'
        )
    gw_salary_total = weekly_salary * len(gw_rows)
    gw_transfer_cost = trx.team_transfer_net(code, "26/27", _all_transfers)
    gw_season_cost = gw_salary_total + gw_transfer_cost
    gw_total_row = (
        f'<tr><td colspan="6">{len(gw_rows)}-game salary total</td>'
        f'<td><strong style="color:var(--mv-crimson)">{money(-gw_salary_total)}</strong></td></tr>'
        f'<tr><td colspan="6" class="dim">Transfers (in/out)</td><td>{money(-gw_transfer_cost)}</td></tr>'
        f'<tr><td colspan="6"><strong>26/27 Season Cost</strong></td>'
        f'<td><strong style="color:var(--mv-crimson)">{money(-gw_season_cost)}</strong></td></tr>'
    )

    # ---- scouting: EA FC 26 ratings + 2025/26 Premier League performance
    # (from mega.db -- see sync_fc26_ratings.py / sync_fpl_stats.py) ----
    scouting_rows = []
    for p in grouped:
        scouting_rows.append(
            f'<tr><td>{player_label(p)}</td><td class="dim">{p["club_full"] or "—"}</td><td>{p["pos"]}</td>'
            f'<td data-sort="{sort_val(p["fc26"])}" style="color:var(--mv-gold);">{numi(p["fc26"])}</td>'
            f'<td data-sort="{sort_val(p["fc26_pot"])}">{numi(p["fc26_pot"])}</td>'
            f'<td data-sort="{sort_val(p["fc26_value"])}">{eur(p["fc26_value"])}</td>'
            f'<td data-sort="{sort_val(p["fpl_starts"])}">{numi(p["fpl_starts"])}</td>'
            f'<td data-sort="{sort_val(p["fpl_goals"])}">{numi(p["fpl_goals"])}</td>'
            f'<td data-sort="{sort_val(p["fpl_assists"])}">{numi(p["fpl_assists"])}</td>'
            f'<td data-sort="{sort_val(p["g_per90"])}">{num1(p["g_per90"])}</td>'
            f'<td data-sort="{sort_val(p["ga_per90"])}">{num1(p["ga_per90"])}</td>'
            f'<td data-sort="{sort_val(p["xg_per90"])}">{num1(p["xg_per90"])}</td>'
            f'<td data-sort="{sort_val(p["fpl_tackles"])}">{numi(p["fpl_tackles"])}</td>'
            f'<td data-sort="{sort_val(p["fpl_cbi"])}">{numi(p["fpl_cbi"])}</td></tr>'
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

    # box fill order for a row of N boxes: middle first, then outward --
    # e.g. 3 boxes -> [center, left, right]; 4 boxes -> [inner two, then outer two]
    CENTER_OUT_ORDER = {1: [0], 3: [1, 0, 2], 4: [1, 2, 0, 3]}

    def distribute_center_out(players, need):
        order = CENTER_OUT_ORDER.get(need, list(range(need)))
        boxes = [[] for _ in range(need)]
        for i, p in enumerate(players):
            boxes[order[i % need]].append(p)
        return boxes

    def render_box(pos, box_players):
        if not box_players:
            return f'<div class="mv-slot empty"><div class="pos">{pos}</div><div class="player">&mdash;</div></div>'
        rows = "".join(
            f'<div class="mv-box-player"><span class="player">{player_label(p)}</span>'
            f'<span class="rating">{rating_label(p)}</span>'
            f'<span class="rating" style="color:var(--mv-gold);">{money(p["current_salary"])}</span></div>'
            for p in box_players
        )
        return f'<div class="mv-slot"><div class="pos">{pos}</div>{rows}</div>'

    # ---- depth chart: real 3-4-3 formation. Each row is `need` boxes for
    # that position; every player at that position (not just starters) is
    # distributed across the row's boxes, best rating first, filling the
    # middle box before working outward, so a deep position piles up in the
    # middle rather than only ever showing one name per box ----
    pitch_rows = []
    for pos, need in FORMATION:
        players = by_pos.get(pos, [])
        boxes = distribute_center_out(players, need)
        row_html = "".join(render_box(pos, box) for box in boxes)
        pitch_rows.append(f'<div class="mv-pitch-row">{row_html}</div>')
    depth_html = "".join(pitch_rows)

    # ---- youth draft history: all-time, purely informational -- these are
    # NOT the same as the "Youth Legend"/"Youth Player" categories above
    # (which are the subset currently kept and counted in payroll); this is
    # every player the team has ever drafted, shown for reference, never
    # counted toward salary ----
    youth = youth_by_code.get(code, [])

    # ---- youth: rating (EA FC 26, falling back to live Fantrax fpts),
    # matched league-wide since a youth player may not be on this team's own
    # active Fantrax roster ----
    for y in youth:
        cleaned = clean_player(y["player"], y["pos"])
        last = (cleaned["player_name"] or "").split()[-1].lower() if cleaned["player_name"] else ""
        y["fc26"] = global_fc26_lookup.get(last)
        y["fpts"] = global_fpts_lookup.get(last)
    _matched_youth_fc26 = [y["fc26"] for y in youth if isinstance(y["fc26"], (int, float))]
    avg_youth_fc26 = (sum(_matched_youth_fc26) / len(_matched_youth_fc26)) if _matched_youth_fc26 else None

    def rating_plain_label(fc26):
        return f'{fc26:,.0f}' if isinstance(fc26, (int, float)) else '—'

    # ---- youth draft history: ONE table, all-time, sorted most recent
    # draft first. This is a historical record (informational only, salary
    # doesn't count here) -- the currently-kept youth players with real
    # salary are already in the main roster table above, tagged "Youth
    # Legend"/"Youth Player" ----
    # fetch_youth() already returns most-recent-first straight off the sheet
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
        youth_section = f"""<div class="mv-table-scroll">
        <table class="mv-table mv-sortable" id="youth-table-{code}">
          <thead><tr>
            <th data-sort-type="text">Draft</th><th data-sort-type="text">Player</th><th data-sort-type="text">Pos</th>
            <th data-sort-type="num">Age</th><th data-sort-type="text">Club</th><th data-sort-type="num">Rating</th>
            <th data-sort-type="text">Status</th>
          </tr></thead>
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
      <div class="sub">{owner_short(owners)} &middot; {stadium_name} (Capacity {capacity_str})</div>
    </div>

    <div class="mv-stat-grid">
      <div class="mv-stat"><div class="label">Record</div><div class="value">0-0-0</div></div>
      <div class="mv-stat"><div class="label">Points</div><div class="value">0</div></div>
      <div class="mv-stat"><div class="label">League Rank</div><div class="value">&mdash;</div></div>
      <div class="mv-stat"><div class="label">Roster Size</div><div class="value">{roster_size}</div></div>
      <div class="mv-stat"><div class="label">Total Payroll</div><div class="value">{money(total_payroll)}</div></div>
      <div class="mv-stat"><div class="label">Season Net</div><div class="value">{money(season_net)}</div></div>
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
        <button class="mv-tab" onclick="mvShowTab(this,'roster-{code}')">Roster</button>
        <button class="mv-tab" onclick="mvShowTab(this,'depth-{code}')">Depth Chart</button>
        <button class="mv-tab active" onclick="mvShowTab(this,'finances-{code}')">Finances</button>
        <button class="mv-tab" onclick="mvShowTab(this,'scouting-{code}')">Scouting</button>
      </div>
      <div style="font-size:11px;color:var(--mv-ink-muted);margin-bottom:14px;">
        Roster is Kept Contracts + Youth Legend + Youth Players from the league's keeper sheet, plus this
        year's actual draft picks &mdash;
        <span style="color:{CATEGORY_BADGE_COLOR["youth_legend"]};">Youth Legend</span>,
        <span style="color:{CATEGORY_BADGE_COLOR["youth_players"]};">Youth Player</span>, and
        <span style="color:{CATEGORY_BADGE_COLOR["drafted"]};">Drafted '27</span> tags mark each.
        Salary is each player's real contract wage (multi-year where extended, per the Rulez contract
        rules) where we've verified it, live FPL price as a fallback otherwise.
        Depth Chart is ranked by EA FC 26 overall rating (Fantrax fantasy points as fallback/tiebreak).
      </div>

      <div id="roster-{code}" class="mv-tab-panel">
        <div class="sub">{roster_size} players for 26/27 &middot; FC 26 rating, live Fantrax points, real FPL salary &middot; click a column to sort</div>
        <div class="mv-table-scroll">
          <table class="mv-table mv-sortable" id="roster-table-{code}">
            <thead><tr>
              <th data-sort-type="text">Player</th>
              <th data-sort-type="text">Club</th>
              <th data-sort-type="text">Pos</th>
              <th data-sort-type="text">Category</th>
              <th data-sort-type="num">FC 26 Rating</th>
              <th data-sort-type="num">Total Pts</th>
              <th data-sort-type="num">Current Salary</th>
            </tr></thead>
            <tbody>
              {"".join(roster_rows)}
            </tbody>
            <tfoot>{roster_total_row}</tfoot>
          </table>
        </div>
      </div>

      <div id="depth-{code}" class="mv-tab-panel">
        <div class="sub">3-4-3 formation &middot; every player at each position, filled center-out, best to worst by EA FC 26 rating &middot; rating and current salary shown per player</div>
        <div class="mv-pitch">
          {depth_html}
        </div>
      </div>

      <div id="finances-{code}" class="mv-tab-panel active">
        <div class="mv-subtabs">
          <div class="mv-tabs" style="margin-bottom:12px;">
            <button class="mv-tab active" onclick="mvShowSubTab(this,'gw-{code}')">GW</button>
            <button class="mv-tab" onclick="mvShowSubTab(this,'contracts-{code}')">Contracts</button>
          </div>

          <div id="gw-{code}" class="mv-tab-panel active">
            <div class="sub">Real regular-season matchups straight off Fantrax (36 scoring periods) &middot; Salary is season payroll
              spread evenly across those 36 weeks &middot; Fans/Ticket Revenue/P&amp;L left blank until a real revenue model exists &middot; click a column to sort</div>
            <div class="mv-table-scroll">
              <table class="mv-table mv-sortable" id="gw-table-{code}">
                <thead><tr>
                  <th data-sort-type="num">GW</th>
                  <th data-sort-type="num">Salary</th>
                  <th data-sort-type="text">Home</th>
                  <th data-sort-type="text">Away</th>
                  <th data-sort-type="num">Fans</th>
                  <th data-sort-type="num">Ticket Revenue</th>
                  <th data-sort-type="num">P&amp;L</th>
                </tr></thead>
                <tbody>
                  {"".join(gw_rows)}
                </tbody>
                <tfoot>{gw_total_row}</tfoot>
              </table>
            </div>
          </div>

          <div id="contracts-{code}" class="mv-tab-panel">
            <div class="sub">Real contract wages by year plus any transfer fees, team totals then player-by-player &middot; click a column to sort</div>
            <div class="mv-stat-grid" style="grid-template-columns:repeat(auto-fit, minmax(120px,1fr));margin-bottom:18px;">
              {"".join(
                  f'<div class="mv-stat"><div class="label">{season} Cost</div><div class="value" style="font-size:18px;">{money(tot)}</div></div>'
                  for season, tot in zip(finance_seasons, finance_season_totals)
              )}
            </div>
            <div class="mv-table-scroll">
              <table class="mv-table mv-sortable" id="finances-table-{code}">
                <thead><tr>
                  <th data-sort-type="text">Player</th>
                  <th data-sort-type="text">Club</th>
                  <th data-sort-type="text">Pos</th>
                  <th data-sort-type="text">Category</th>
                  {"".join(f'<th data-sort-type="num">{finance_season_header(s)}</th>' for s in finance_seasons)}
                </tr></thead>
                <tbody>
                  {"".join(finance_rows)}
                </tbody>
                <tfoot>{finance_total_row}</tfoot>
              </table>
            </div>
          </div>
        </div>
      </div>

      <div id="scouting-{code}" class="mv-tab-panel">
        <div class="sub">EA Sports FC 26 ratings (all leagues) + 2025/26 Premier League season totals &middot; click a column to sort</div>
        <div style="font-size:11px;color:var(--mv-ink-muted);margin-bottom:10px;">
          Sourced from a live FC 26 ratings feed and the official Fantasy Premier League API &mdash;
          not FBref (fbref.com blocks automated access). "Starts" is starts, not total appearances;
          "CBI" is clearances+blocks+interceptions combined, not pure clearances; SCA/90, GCA/90, and
          pass-completion counts aren't available from either source and are omitted rather than
          guessed. A dash means no match was found (different name spelling, or the player didn't
          play in the Premier League last season).
        </div>
        <div class="mv-table-scroll">
          <table class="mv-table mv-sortable" id="scouting-table-{code}">
            <thead><tr>
              <th data-sort-type="text">Player</th>
              <th data-sort-type="text">Club</th>
              <th data-sort-type="text">Pos</th>
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
            </tr></thead>
            <tbody>
              {"".join(scouting_rows)}
            </tbody>
          </table>
        </div>
      </div>
    </section>

    <section class="card mv-card">
      <h2 class="mv-chrome-text">Youth Draft History</h2>
      <div class="sub">{len(youth)} player{"s" if len(youth) != 1 else ""} drafted all-time &middot; informational only, does not count toward payroll</div>
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
        "avg_youth_fc26": avg_youth_fc26,
        "avg_fpts": avg_fpts,
        "wins": team_wins.get(code),
        "capacity": stadiums.get(code, {}).get("capacity"),
        "stadium": stadiums.get(code, {}).get("stadium"),
        "season_costs": {
            s: sum(p["wages"].get(s, 0) for p in roster) + trx.team_transfer_net(code, s, _all_transfers)
            for s in ("26/27", "27/28", "28/29")
        },
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
    f'<td data-sort="{r["avg_youth_fc26"] if isinstance(r["avg_youth_fc26"], (int, float)) else -1}">{fmt_num(r["avg_youth_fc26"], 1)}</td>'
    f'<td data-sort="{r["season_costs"]["26/27"]}">{money(r["season_costs"]["26/27"])}</td>'
    f'<td data-sort="{r["season_costs"]["27/28"]}">{money(r["season_costs"]["27/28"])}</td>'
    f'<td data-sort="{r["season_costs"]["28/29"]}">{money(r["season_costs"]["28/29"])}</td>'
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
              <th data-sort-type="num">Avg Youth Rating &#9650;&#9660;</th>
              <th data-sort-type="num">26/27 Cost &#9650;&#9660;</th>
              <th data-sort-type="num">27/28 Cost &#9650;&#9660;</th>
              <th data-sort-type="num">28/29 Cost &#9650;&#9660;</th>
            </tr>
          </thead>
          <tbody>
            {teams_table_rows}
          </tbody>
        </table>
      </div>
      <p style="font-size:11px;color:var(--mv-ink-muted);margin-top:10px;">
        &ldquo;Avg FC 26 Rating&rdquo; is each team's average EA Sports FC 26 overall rating across matched
        roster players; &ldquo;Avg Youth Rating&rdquo; is the same across all-time drafted youth players
        (source: a community CSV mirror of the FC 26 database on GitHub, since EA's own site, sofifa.com,
        and futwiz.com all explicitly disallow ClaudeBot in robots.txt). Run
        <code>sync_fc26_ratings.py</code> to refresh the ratings in the local database this reads from.
        Cost columns are each team's real contract wages plus net transfer fees for that season, same
        figures as <a href="financials.html" style="color:inherit;">Financials</a>. Wins reset to 0 --
        26/27 hasn't kicked off yet.
      </p>
    </section>
""" + foot()

with open("teams.html", "w") as f:
    f.write(teams_html)
print("Updated teams.html")

# ---------------- financials.html / index.html (site default is now
# Financials -- see head()'s NAV_LINKS): two tabs, GW (default) and Season.
# GW is every team's real regular-season schedule straight off Fantrax (36
# scoring periods; NOT the Google Sheet's League Schedule tab, whose
# home/away is wrong -- see fantrax_live.fetch_schedule) -- one row per team
# per game they actually play, with weekly salary (season payroll / 36,
# same math as each team's own GW tab). Revenue/P&L are left blank for now:
# there's no real ticket/fan revenue model wired up site-wide yet. Season is
# the existing 3-forward-season cost table (real contract wages + transfer
# fees), unchanged. ----------------
financial_rows_sorted = sorted(financial_rows, key=lambda r: -(r["season_costs"]["26/27"] or 0))

financials_rows_html = "\n            ".join(
    f'<tr>'
    f'<td><a href="team-{r["code"].lower()}.html" style="color:inherit;text-decoration:none;font-weight:600;">{r["name"]}</a></td>'
    f'<td class="dim">{r["owner"]}</td>'
    f'<td><strong style="color:var(--mv-gold)">{money(r["season_costs"]["26/27"])}</strong></td>'
    f'<td>{money(r["season_costs"]["27/28"])}</td>'
    f'<td>{money(r["season_costs"]["28/29"])}</td>'
    f'<td>{r["trophies"]}</td>'
    f'</tr>'
    for r in financial_rows_sorted
)

financials_totals = {
    s: sum(r["season_costs"][s] for r in financial_rows_sorted) for s in ("26/27", "27/28", "28/29")
}

weekly_salary_by_code = {r["code"]: (r["cost"] / REGULAR_SEASON_WEEKS if r["cost"] else 0) for r in financial_rows}
team_name_by_code = {r["code"]: r["name"] for r in financial_rows}

gw_all_rows = []
for _code in sorted(games_by_team):
    for g in games_by_team[_code]:
        is_home = g["home"] == _code
        gw_all_rows.append({
            "week": g["week"], "code": _code, "is_home": is_home,
            "opp": g["away"] if is_home else g["home"],
            "salary": weekly_salary_by_code.get(_code, 0),
        })
gw_all_rows.sort(key=lambda r: (r["week"], r["code"]))

gw_all_rows_html = "\n            ".join(
    f'<tr>'
    f'<td data-sort="{r["week"]}">{r["week"]}</td>'
    f'<td><a href="team-{r["code"].lower()}.html" style="color:inherit;text-decoration:none;font-weight:600;">{team_name_by_code.get(r["code"], r["code"])}</a></td>'
    f'<td>{"Home" if r["is_home"] else "Away"}</td>'
    f'<td class="dim">{team_name_by_code.get(r["opp"], r["opp"])}</td>'
    f'<td data-sort="{r["salary"]}">{money(r["salary"])}</td>'
    f'<td class="dim" data-sort="0">&mdash;</td>'
    f'<td class="dim" data-sort="0">&mdash;</td>'
    f'</tr>'
    for r in gw_all_rows
)

financials_body = f"""
    <div class="mv-page-header">
      <h1 class="mv-chrome-text">Financials</h1>
      <div class="sub">Every team's regular-season schedule and costs &mdash; 26/27 forward</div>
    </div>

    <section class="card mv-card">
      <div class="mv-subtabs">
        <div class="mv-tabs" style="margin-bottom:12px;">
          <button class="mv-tab active" onclick="mvShowSubTab(this,'gw-league')">GW</button>
          <button class="mv-tab" onclick="mvShowSubTab(this,'season-league')">Season</button>
        </div>

        <div id="gw-league" class="mv-tab-panel active">
          <div class="sub">Real regular-season schedule straight off Fantrax (36 scoring periods), every team &middot; Salary is
            season payroll spread evenly across those 36 weeks &middot; Revenue/P&amp;L left blank until the revenue model is built &middot; click a column to sort</div>
          <div class="mv-table-scroll">
            <table class="mv-table mv-sortable" id="gw-table-league">
              <thead><tr>
                <th data-sort-type="num">GW</th>
                <th data-sort-type="text">Team</th>
                <th data-sort-type="text">Home/Away</th>
                <th data-sort-type="text">Opponent</th>
                <th data-sort-type="num">Salary</th>
                <th data-sort-type="num">Revenue</th>
                <th data-sort-type="num">P&amp;L</th>
              </tr></thead>
              <tbody>
                {gw_all_rows_html}
              </tbody>
            </table>
          </div>
        </div>

        <div id="season-league" class="mv-tab-panel">
          <div class="sub">Cost per team, all 3 forward seasons &mdash; sum of each player's real contract wage (Kept + Youth + this year's draft picks) plus net transfer fees paid that season</div>
          <div class="mv-table-scroll">
            <table class="mv-table">
              <thead><tr><th>Team</th><th>Owner</th><th>26/27</th><th>27/28</th><th>28/29</th><th># Trophies</th></tr></thead>
              <tbody>
                {financials_rows_html}
              </tbody>
              <tfoot>
                <tr>
                  <td colspan="2">League Total</td>
                  <td><strong style="color:var(--mv-gold)">{money(financials_totals["26/27"])}</strong></td>
                  <td>{money(financials_totals["27/28"])}</td>
                  <td>{money(financials_totals["28/29"])}</td>
                  <td></td>
                </tr>
              </tfoot>
            </table>
          </div>
        </div>
      </div>
    </section>
"""

for _fname, _title in (("index.html", "Home"), ("financials.html", "Financials")):
    with open(_fname, "w") as f:
        f.write(head(_title, "index.html") + hero_logo() + financials_body + foot())
    print(f"Updated {_fname}")

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
