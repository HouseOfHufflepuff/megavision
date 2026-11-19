"""
Weekly matchday preview: this week's fixtures, fans and gates, MEGAVISION
Rank XIs, anyone Out who would start, and a pick.

POLYSCI is the league sponsor. CTA button only (no lower banner PNG --
Gmail). The only link is the X profile. Prints the body. Never sends.

Run:
    python3 matchday_email.py 9
    python3 matchday_email.py 9 --html /tmp/gw9-preview.html
"""
import argparse
import html
import json
import re
import sys
import unicodedata
from pathlib import Path

import email_brand
import fantrax_live as fl
import fans_algo as fa
from common import TEAMS, fetch_stadiums
from db import connect

TEAM_FULL_NAME = {code: name for code, name, _ in TEAMS}
FORMATION_SLOTS = fl.FORMATION_SLOTS
CITY_XI_META = Path("/Users/houseofhufflepuff/Development/polysci/epl/output/mci_vs_bha_2026-10-31_starting11_meta.json")
CITY_XI_VIDEO = Path("/Users/houseofhufflepuff/Development/polysci/epl/output/mci_vs_bha_2026-10-31_starting11.mp4")


def num(value):
    value = float(value)
    if value.is_integer():
        return str(int(value))
    return f"{value:.2f}".rstrip("0").rstrip(".")


def money(value):
    return f"${float(value):.2f}"


PARTICLES = {"van", "von", "de", "del", "da", "dos", "das", "di", "le", "la"}


def norm_name(name):
    return unicodedata.normalize("NFKD", name or "").encode("ascii", "ignore").decode().lower()


def last_name(name):
    parts = (name or "").split()
    return parts[-1] if parts else ""


def short_name(name):
    parts = [p for p in (name or "").split() if p]
    if len(parts) >= 2 and parts[-2].lower().rstrip(".") in PARTICLES:
        return f"{parts[-2]} {parts[-1]}"
    return parts[-1] if parts else name or ""


def inj_short(player):
    inj = (player.get("inj") or "").split(" - ")[0].strip()
    return inj or "Out"


def load_ranks(week):
    conn = connect()
    rows = conn.execute(
        "SELECT p.player_name, p.real_club, p.fantrax_position, g.megavision_rank, "
        "g.ffs_out, g.ffs_start, g.ffs_doubt, g.start_likelihood, g.injury_status, g.score "
        "FROM epl_players p JOIN player_gameweek g ON g.player_name=p.player_name AND g.real_club=p.real_club "
        "WHERE g.gameweek=?",
        (week,),
    ).fetchall()
    conn.close()
    by_name = {}
    for name, club, pos, mv, ffs_out, ffs_start, ffs_doubt, pct, inj, score in rows:
        by_name[name.lower()] = {
            "name": name, "club": club, "pos": pos, "mv": mv or 0.0,
            "out": bool(ffs_out), "start": bool(ffs_start), "doubt": bool(ffs_doubt),
            "pct": pct, "inj": inj or "", "fpts": score or 0.0,
        }
    return by_name


def attach_rank(player, ranks):
    row = ranks.get(player["name"].lower())
    if not row:
        last = last_name(player["name"]).lower()
        hits = [v for v in ranks.values() if last_name(v["name"]).lower() == last]
        row = hits[0] if len(hits) == 1 else None
    if not row:
        return {**player, "mv": 0.0, "out": False, "start": False, "doubt": False, "inj": "", "club_real": player.get("club")}
    return {**player, **row, "club_real": row["club"]}


def projected_xi(roster, ranks):
    enriched = [attach_rank(p, ranks) for p in roster]
    xi = []
    for pos, slots in FORMATION_SLOTS.items():
        cands = sorted((p for p in enriched if p["pos"] == pos), key=lambda p: -p["mv"])
        xi.extend(cands[:slots])
    return xi


def fanbases(week, standings):
    conn = connect()
    title_rows = conn.execute("SELECT competition, team_code FROM titles WHERE season='26/27'").fetchall()
    best11_week = conn.execute("SELECT MAX(week) FROM best11 WHERE week<=?", (week,)).fetchone()[0]
    topxi = {code: 0.0 for code, _, _ in TEAMS}
    if best11_week is not None:
        rows_by_pos = {}
        for pos, slot_rank, name, club, code, fpts in conn.execute(
            "SELECT pos, slot_rank, player_name, real_club, team_code, fpts FROM best11 WHERE week=? ORDER BY pos, slot_rank",
            (best11_week,),
        ):
            rows_by_pos.setdefault(pos, []).append((code, fpts))
        for pos, rows in rows_by_pos.items():
            for i, (code, fpts) in enumerate(rows):
                if not code:
                    continue
                is_top = pos in ("F", "M", "D") and i == 0
                topxi[code] = topxi.get(code, 0.0) + (fa.TOPXI_TOP_FANS if is_top else fa.TOPXI_REST_FANS)
    conn.close()
    rank_by_code = fa.rank_by_code_from_standings(standings)
    scoring = fa.scoring_rank_by_code(standings)
    legacy = {code: fa.legacy_fan_value(code, title_rows) for code, _, _ in TEAMS}
    fanbase = {}
    for code, _, _ in TEAMS:
        b = fa.team_fan_count(rank_by_code.get(code), scoring.get(code), topxi.get(code, 0.0), legacy.get(code, 0))
        fanbase[code] = b["total"]
    return fanbase, rank_by_code


def find_owner(rosters, name):
    key = norm_name(name)
    last = norm_name(last_name(name))
    exact = []
    last_hits = []
    for code, roster in rosters.items():
        for p in roster:
            if norm_name(p["name"]) == key:
                exact.append((code, p["name"]))
            elif norm_name(last_name(p["name"])) == last:
                last_hits.append((code, p["name"]))
    if exact:
        return exact[0]
    if len(last_hits) == 1:
        return last_hits[0]
    return None, None


def city_owners(rosters, starters):
    owned = []
    for starter in starters:
        code, mega_name = find_owner(rosters, starter["name"])
        if code:
            owned.append({**starter, "mega": code, "mega_name": mega_name})
    return owned


def build(week=None):
    sess = fl._session()
    print("Fantrax schedule...", file=sys.stderr)
    all_games = fl.fetch_schedule(sess)
    games_by_week = {}
    for g in all_games:
        games_by_week.setdefault(g["week"], []).append(g)
    if week is None:
        scored = {g["week"] for g in games_by_week}
        # next week after the latest Gameweek table is handled by the caller
        week = max(games_by_week)
    this_week = games_by_week.get(week, [])
    if not this_week:
        raise SystemExit(f"No scheduled games for week {week}")

    print("Standings and rosters...", file=sys.stderr)
    standings = fl.fetch_all_standings(sess)
    senior = [r for r in standings if not r["is_junior"]]
    rosters = {code: fl.fetch_full_roster(sess, team_id) for code, team_id in fl.FANTRAX_TEAM_ID.items()}
    ranks = load_ranks(week)
    fanbase, rank_by_code = fanbases(week, standings)
    stadiums = fetch_stadiums()
    capacities = {code: v["capacity"] or 0 for code, v in stadiums.items()}
    ticket_price = 0.0 if week in fa.NON_REGULAR_SEASON_WEEKS else fa.REGULAR_SEASON_TICKET_PRICE

    previews = []
    for g in this_week:
        home, away = g["home"], g["away"]
        game = fa.compute_game_fans(home, away, fanbase, capacities, rank_by_code)
        gate = game["attendance"] * ticket_price
        home_xi = projected_xi(rosters[home], ranks)
        away_xi = projected_xi(rosters[away], ranks)
        home_sum = round(sum(p["mv"] for p in home_xi), 1)
        away_sum = round(sum(p["mv"] for p in away_xi), 1)
        pick = home if home_sum > away_sum else (away if away_sum > home_sum else None)
        previews.append({
            "home": home, "away": away,
            "home_full": TEAM_FULL_NAME.get(home, home), "away_full": TEAM_FULL_NAME.get(away, away),
            "stadium": stadiums.get(home, {}).get("stadium") or home,
            "capacity": capacities.get(home, 0),
            "home_fans": fanbase.get(home, 0), "away_fans": fanbase.get(away, 0),
            "attendance": game["attendance"], "gate": gate, "bonuses": game["bonuses"],
            "sold_out": game["sold_out"],
            "home_xi": home_xi, "away_xi": away_xi,
            "home_sum": home_sum, "away_sum": away_sum, "pick": pick,
            "home_record": next((r["record"] for r in senior if r["code"] == home), ""),
            "away_record": next((r["record"] for r in senior if r["code"] == away), ""),
            "home_rank": next((r["rank"] for r in senior if r["code"] == home), None),
            "away_rank": next((r["rank"] for r in senior if r["code"] == away), None),
            "home_out": [p for p in home_xi if p["out"]],
            "away_out": [p for p in away_xi if p["out"]],
            "home_doubt": [p for p in home_xi if p["doubt"] and not p["out"]],
            "away_doubt": [p for p in away_xi if p["doubt"] and not p["out"]],
        })

    city_meta = json.loads(CITY_XI_META.read_text()) if CITY_XI_META.exists() else {}
    city_owned = city_owners(rosters, city_meta.get("starters") or [])
    dunk_code, dunk_name = find_owner(rosters, "Lewis Dunk")
    semenyo_code, semenyo_name = find_owner(rosters, "Antoine Semenyo")
    return {
        "week": week,
        "previews": previews,
        "senior": senior,
        "ticket_price": ticket_price,
        "league_gate": sum(p["gate"] for p in previews),
        "city_meta": city_meta,
        "city_owned": city_owned,
        "dunk": {"code": dunk_code, "name": dunk_name},
        "semenyo": {"code": semenyo_code, "name": semenyo_name},
    }


def flag_bits(preview):
    bits = []
    for code, players in ((preview["home"], preview["home_out"]), (preview["away"], preview["away_out"])):
        for player in players:
            bits.append(
                f"{player['name']} is out ({inj_short(player)}). The rank still has him starting. Leave him on the bench."
            )
    for code, players in ((preview["home"], preview["home_doubt"]), (preview["away"], preview["away_doubt"])):
        for player in players:
            bits.append(f"{code}: {short_name(player['name'])} is a doubt.")
    return bits


def city_in_game(preview, owned):
    names = []
    for row in owned:
        if row["mega"] in (preview["home"], preview["away"]):
            names.append(f"{short_name(row['name'])} ({row['mega']})")
    return names


def game_story(preview, owned, league_best):
    away, home = preview["away"], preview["home"]
    sold = " Sold out." if preview["sold_out"] else ""
    bits = [
        f"{preview['away_full']} at {preview['home_full']}.",
        f"{away} are {preview['away_record']}, #{preview['away_rank']}. "
        f"{home} are {preview['home_record']}, #{preview['home_rank']}.",
        f"{num(preview['away_fans'])} fans make the trip. {num(preview['home_fans'])} are already there. "
        f"{num(preview['attendance'])} in {preview['stadium']}. Gate {money(preview['gate'])}.{sold}",
    ]
    if preview["bonuses"]:
        bits.append(preview["bonuses"][0].split(" (")[0] + ".")
    away_top = max(preview["away_xi"], key=lambda x: x["mv"])
    home_top = max(preview["home_xi"], key=lambda x: x["mv"])
    bits.append(
        f"{short_name(away_top['name'])} leads {away} at {away_top['mv']:.1f}. "
        f"{short_name(home_top['name'])} leads {home} at {home_top['mv']:.1f}."
    )
    if league_best and league_best["name"] in {home_top["name"], away_top["name"]}:
        holder = home if home_top["name"] == league_best["name"] else away
        bits.append(f"{short_name(league_best['name'])} is the top rank in the league, and he plays for {holder}.")
    bits.extend(flag_bits(preview))
    if preview["pick"]:
        winner, loser = (home, away) if preview["pick"] == home else (away, home)
        wsum = preview["home_sum"] if winner == home else preview["away_sum"]
        lsum = preview["away_sum"] if winner == home else preview["home_sum"]
        bits.append(f"Pick {winner}. Rank XI {num(wsum)} to {num(lsum)}.")
    else:
        bits.append(
            f"Level. Rank XI {away} {num(preview['away_sum'])}, {home} {num(preview['home_sum'])}."
        )
    return " ".join(bits)


def city_paragraph(data):
    city = data["city_meta"]
    if not city:
        return ""
    conclusion = city.get("conclusion") or city.get("comment") or ""
    conclusion = re.sub(r"@\w+", "", conclusion).strip()
    if conclusion and not conclusion.endswith("."):
        conclusion += "."
    owners = [f"{short_name(row['name'])} ({row['mega']})" for row in data["city_owned"]]
    owned_names = {norm_name(row["name"]) for row in data["city_owned"]}
    unowned = [
        short_name(s["name"])
        for s in (city.get("starters") or [])
        if norm_name(s["name"]) not in owned_names
    ]
    kick = city.get("kickoff_uk") or "15:00"
    venue = city.get("venue") or "the Etihad"
    bits = [
        f"Manchester City vs Brighton, Saturday {kick} UK, {venue}. {conclusion}"
    ]
    if owners:
        bits.append("In Mega: " + ", ".join(owners) + ".")
    if unowned:
        verb = "are" if len(unowned) > 1 else "is"
        bits.append(f"{', '.join(unowned)} {verb} the coin flip, and nobody in Mega has him.")
    dunk = data.get("dunk") or {}
    if dunk.get("code"):
        bits.append(f"Dunk is {dunk['code']}. They do not share a Mega pitch this week.")
    semenyo = data.get("semenyo") or {}
    if semenyo.get("code"):
        bits.append(f"Semenyo is Out for City. He is on {semenyo['code']}, and he is not in that projected XI.")
    bits.append("The clip is attached.")
    return " ".join(bits)


def render_email(data):
    week = data["week"]
    previews = data["previews"]
    leader = next(r for r in data["senior"] if r["rank"] == 1)
    first_v_second = next((p for p in previews if {p["home_rank"], p["away_rank"]} == {1, 2}), None)
    outs = []
    for preview in previews:
        for code, players in ((preview["home"], preview["home_out"]), (preview["away"], preview["away_out"])):
            for player in players:
                outs.append((code, player))
    pool = [player for preview in previews for player in preview["home_xi"] + preview["away_xi"]]
    league_best = max(pool, key=lambda x: x["mv"]) if pool else None
    headline = f"GW{week}. {leader['code']} are {leader['record']}, first."
    if first_v_second:
        headline = (
            f"GW{week}. {first_v_second['away_full']} at {first_v_second['home_full']}. First against second."
        )
    lede = (
        f"Six games. The league gate is {money(data['league_gate'])}. "
        f"{leader['code']} are {leader['record']} and first."
    )
    if outs:
        who = ", ".join(f"{code} has {player['name']} Out in the XI" for code, player in outs)
        lede += f" {who}."
    city_para = city_paragraph(data)
    games = [game_story(preview, data["city_owned"], league_best) for preview in previews]
    lines = ["polysci", headline, "", lede, ""]
    if city_para:
        lines.extend(["THE POLYSCI XI", city_para, ""])
    lines.append("THE GAMES")
    lines.append("")
    for game in games:
        lines.append(game)
        lines.append("")
    lines.extend(["-- MegaBot", "", email_brand.sponsor_cta()])
    return "\n".join(lines), headline, lede, city_para, games


def render_html(data, headline, lede, city_para, games, banner_cid=None, banner_src=None, wordmark_src=None):
    week = data["week"]
    inner = []
    inner.append(
        f'<p style="margin:0 0 8px;font-family:Arial,Helvetica,sans-serif;font-size:13px;letter-spacing:2px;font-weight:700;color:{email_brand.MUTED}">'
        f'GW{week}</p>'
    )
    inner.append(
        f'<p style="margin:0 0 14px;font-family:Arial,Helvetica,sans-serif;font-size:22px;line-height:1.25;font-weight:700;color:{email_brand.INK}">'
        f'{html.escape(headline)}</p>'
    )
    inner.append(
        f'<p style="margin:0 0 16px;font-family:Arial,Helvetica,sans-serif;font-size:15px;line-height:1.55;color:{email_brand.INK}">'
        f'{html.escape(lede)}</p>'
    )
    if city_para:
        inner.append(
            '<p style="margin:18px 0 8px;font-family:Arial,Helvetica,sans-serif;font-size:13px;letter-spacing:1px;font-weight:700">THE POLYSCI XI</p>'
        )
        inner.append(
            f'<p style="margin:0 0 16px;font-family:Arial,Helvetica,sans-serif;font-size:15px;line-height:1.55;color:{email_brand.INK}">'
            f'{html.escape(city_para)}</p>'
        )
    inner.append(
        '<p style="margin:18px 0 8px;font-family:Arial,Helvetica,sans-serif;font-size:13px;letter-spacing:1px;font-weight:700">THE GAMES</p>'
    )
    for game in games:
        inner.append(
            f'<p style="margin:0 0 16px;font-family:Arial,Helvetica,sans-serif;font-size:15px;line-height:1.55;color:{email_brand.INK}">'
            f'{html.escape(game)}</p>'
        )
    inner.append(
        f'<p style="margin:0 0 8px;font-family:Arial,Helvetica,sans-serif;font-size:15px;color:{email_brand.INK}">-- MegaBot</p>'
    )
    footer = email_brand.sponsor_cta_html(include_banner=False)
    mark = email_brand.wordmark_html(wordmark_src)
    return f'''<!doctype html>
<html>
<head><meta charset="utf-8"><title>MEGAVISION GW{week}</title></head>
<body style="margin:0;background:{email_brand.PAPER};font-family:Arial,Helvetica,sans-serif;color:{email_brand.INK}">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:{email_brand.PAPER}">
<tr><td align="center" style="padding:24px 12px">
<table role="presentation" width="600" cellpadding="0" cellspacing="0" style="width:600px;max-width:600px;background:#ffffff;border:1px solid #ddd">
{mark}
<tr><td style="padding:28px 28px 8px">{''.join(inner)}</td></tr>
<tr><td>{footer}</td></tr>
</table>
</td></tr>
</table>
</body>
</html>
'''


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("week", type=int, nargs="?")
    parser.add_argument("--html", type=Path)
    args = parser.parse_args()
    data = build(args.week)
    text, headline, lede, city_para, games = render_email(data)
    print(text)
    if args.html:
        args.html.write_text(render_html(data, headline, lede, city_para, games))
        print(f"wrote {args.html}", file=sys.stderr)


if __name__ == "__main__":
    main()
