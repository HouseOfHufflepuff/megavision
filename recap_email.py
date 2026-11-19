"""
Weekly recap email. The matchday mail is the preview. This is the week
after: the result, the gate that was already set, and what actually
happened on the pitch for each roster.

TEMPLATE (GW9 is the model). Do not mail the skeleton. Write WEEK_COPY[week]
first, then print, then send.

    headline  The week, in human. A building that fell, a wait that ended,
              a Mega score that should not have happened. Not "Three picks
              lost." Not a table.
    lede      The real weekend first (reds, own goals, historic results),
              then what it did in Mega (picks, high score, gate, who is
              first). Fans labeled "fans". Exact numbers, never "about".
    games     One graf per matchup, Away @ Home:
              "{AWAY}, {n} fans @ {HOME}, {n} fans. {attendance} at
              {stadium}, gate ${x}. {winner} {score}, {loser} {score}."
              Then the thing that happened on the pitch that decided it --
              a red, an own goal, a keeper who dropped a corner, a 45-minute
              header, Haaland playing 90 and not scoring. The pick line last.
              Not a G/A list. Not FPL points. Fantrax is the score only.

Fantrax exposes the matchup score. It does not expose a player's points
for one gameweek (the period argument is ignored). The real-match story
comes from FPL's finished gameweek plus match reports. Those are the events.
The Fantrax number is the score. FPL points are never printed as league points.

Run:
    python3 recap_email.py 9
    python3 recap_email.py 9 --html /tmp/gw9-recap.html

Prints the plain-text body. Never sends. A week with WEEK_COPY uses that
copy. A week without it prints the skeleton so you can see scores, then
you write the human grafs before mailing.
"""
import argparse
import html
import json
import re
import sys
import unicodedata
import urllib.request
from pathlib import Path

import email_brand
import fantrax_live as fl
from common import TEAMS, fetch_stadiums
from db import connect
from sync_fpl_stats import build_lookup, match

POLYSCI_URL = email_brand.POLYSCI_URL
FPL_BOOTSTRAP = "https://fantasy.premierleague.com/api/bootstrap-static/"
FPL_LIVE = "https://fantasy.premierleague.com/api/event/{gw}/live/"

# Side named in that week's matchday mail. No entry, no "pick" line.
PREVIEW_PICKS = {
    8: {
        ("FAV", "NAC"): "FAV",
        ("QFC", "HUF"): "HUF",
        ("REN", "DU"): "REN",
        ("TTS", "CRG"): "CRG",
        ("WTF", "BHB"): "WTF",
        ("ASS", "POW"): "ASS",
    },
    9: {
        ("FAV", "HUF"): "HUF",
        ("NAC", "DU"): "DU",
        ("QFC", "CRG"): "CRG",
        ("REN", "BHB"): "BHB",
        ("TTS", "POW"): "POW",
        ("WTF", "ASS"): "ASS",
    },
}

# Human copy for the mailed recap. The auto renderer below is a skeleton
# of scores, gates, and FPL G/A clauses -- it is not the email. Fill this
# before sending. Each game graf opens Away, fans @ Home, fans, then the
# thing that actually happened, not a box score.
WEEK_COPY = {
    9: {
        "headline": "GW9. Anfield after fourteen years. The Etihad after never.",
        "lede": (
            "Halloween weekend. Four red cards. Two own goals, one of them by a goalkeeper. "
            "Liverpool took 17 shots at Arsenal and put zero on target. Brighton had never "
            "won a league game at Manchester City, in 16 visits. They have now. Yasin Ayari "
            "tapped in after Matheus Nunes missed a clearance, Bart Verbruggen made seven "
            "saves, and Erling Haaland played the full 90 for ASS without scoring. The "
            "POLYSCI clip was that match. In Mega, first played second in front of 540 at "
            "Gringott's. HUF held. Three other picks did not. NAC, who were not supposed "
            "to, scored 88. League gate $70.88. HUF is 6-0-1, first. CRG has scored 557.5, "
            "the most in the league, and lost at home to last place."
        ),
        "games": {
            ("FAV", "HUF"): (
                "FAV, 210 fans @ HUF, 290 fans. 540 at Gringott's Counting House, gate $21.60. "
                "HUF 67, FAV 57.5. First versus second, the building full, and HUF did not "
                "need a goal. Lewis Dunk blocked Haaland at the Etihad and kept the clean "
                "sheet on the night Brighton finally won there. Kostoulas, just promoted, "
                "played 71 minutes of the same night. FAV had Manzambi's assist for Jackson "
                "at Villa Park, Pickford's clean sheet at Newcastle, and Iliman Ndiaye "
                "rattling Verbruggen's crossbar. It was not enough. The pick was HUF. It held. "
                "HUF is 6-0-1."
            ),
            ("NAC", "DU"): (
                "NAC, 40 fans @ DU, 150 fans. 190 at West East Enders Park, gate $7.60. "
                "NAC 88, DU 58.5. The pick was DU. NAC won by 29.5, the high score of the "
                "week, with 40 people in the away end. Ayari scored the goal that finally "
                "won Brighton a league game at the Etihad. McBurnie scored and assisted in "
                "Hull's 2-2. Palmer put away the penalty after Lisandro Martinez pushed "
                "Wesley Fofana in the face. Le Fée converted after Ethan Pinnock handled. "
                "DU had Thiago's finish, the first shot on target of Brentford against "
                "Forest, and they also had Zion Suzuki, who dropped Iwobi's corner into "
                "his own net. Unai Emery said that is part of football. DU is 3-0-4."
            ),
            ("QFC", "CRG"): (
                "QFC, 31 fans @ CRG, 220 fans. 271.08 at The CA$E, gate $10.84. "
                "QFC 84, CRG 79.5. Last place went to The CA$E and beat the league's "
                "highest-scoring team. Jean-Philippe Mateta lunged on Micky van de Ven in "
                "the 13th minute, a straight red, and Archie Gray, unmarked at a corner, "
                "headed in. Gray played 45 minutes. Julio Enciso hit a left-footer from "
                "20 yards into the top corner at Hull. CRG's night was van Hecke, still on "
                "the ground, heading in after Dean Henderson spilled it, and Evanilson "
                "scoring after James Trafford passed a goal-kick straight to Kluivert. "
                "The pick was CRG. QFC is 2-0-5."
            ),
            ("REN", "BHB"): (
                "REN, 145 fans @ BHB, 51 fans. 196 at The Great Northern, gate $7.84. "
                "REN 67, BHB 57.5. Kai Havertz scored in the 16th minute at Anfield. Rice "
                "across the face, far post, Arsenal's first league win there since 2012. "
                "Florian Wirtz hit the bar. Liverpool did not put a shot on target. BHB had "
                "that Havertz goal. BHB lost. Thierno Barry tapped in at St James' Park "
                "after Lukáš Horníček let Tyrique George's shot squirm under him. Fofana "
                "was the man Martinez pushed in the face. The pick was BHB, on 51 home fans. "
                "REN won by 9.5."
            ),
            ("TTS", "POW"): (
                "TTS, 140 fans @ POW, 145 fans. 285 at The Stadium of Power, gate $11.40. "
                "POW 57.5, TTS 54.5. Three points. Maxim De Cuyper squared the miss that "
                "became Ayari's winner, and kept the clean sheet, so Brighton's first league "
                "win at the Etihad is on POW's card. Mohamed Belloumi assisted at Hull. "
                "Jaidon Anthony played 18 minutes at Brentford and laid on Thiago. At the "
                "other end Henderson was the keeper Gray and van Hecke beat. Brian Brobbey "
                "played the full 90 in Coventry's 3-1 and did not score. Anthony Elanga hit "
                "the post at St James', Pickford and the woodwork sharing the save. The pick "
                "was POW. It held, just."
            ),
            ("WTF", "ASS"): (
                "WTF, 110 fans @ ASS, 180 fans. 290 at Hinfield, gate $11.60. "
                "ASS 70.5, WTF 60.5. Haaland played 90 at the Etihad. Dunk blocked him. "
                "Verbruggen caught the header. Lisandro Martinez, on this same ASS roster, "
                "was sent off at Stamford Bridge for a second yellow, the VAR catching him "
                "pushing Fofana in the face. ASS still won. Nicolas Jackson rode two tackles "
                "at Villa Park and scored. Jack Rudoni's shot went in off Omar Alderete, who "
                "later got himself sent off. David Raya stood in Anfield's goal while "
                "Liverpool took 17 shots and hit none of them. WTF had Morgan Rogers chipping "
                "Penders after Romeo Lavia won it on halfway, and Eli Kroupi's 94th-minute "
                "ball for Adli. Dominic Calvert-Lewin thought he had one. VAR found his hand. "
                "The pick was ASS."
            ),
        },
    },
    10: {
        "headline": "GW10. Eight at Old Trafford. First lost at The CA$E.",
        "lede": (
            "Thirty goals. Six penalties. United and Villa scored eight of them at Old "
            "Trafford and the game finished 4-4, Patrick Dorgu in the 96th minute. Forest "
            "beat Manchester City 3-1 at the City Ground, Liam Delap scoring twice against "
            "the club that raised him, and City have now lost three league games in a row. "
            "Brighton went second. Thiago was sent off for violent conduct in the 23rd "
            "minute. Sunderland beat Chelsea. Crystal Palace are bottom. In Mega, 688.5 "
            "went to The CA$E to watch first place lose for the first time. REN scored "
            "82.5, the high score. League gate $76.22. HUF is 6-0-2, still first. CRG has "
            "scored 622.5, the most in the league. MegaBot did not run a lineup pass on the "
            "managed sides last week, HUF, NAC, POW, TTS. The commissioner did not kick "
            "that off. That's on him. Three of them still won. HUF did not."
        ),
        "games": {
            ("FAV", "DU"): (
                "FAV, 200 fans @ DU, 120 fans. 320 at West East Enders Park, gate $12.80. "
                "FAV 60.5, DU 55.5. Diego Gómez hit one from 25 yards after Thiago had "
                "already been sent off, and Brighton went second. FAV also had Xaver "
                "Schlager laying on Delap's first at the City Ground. DU had Alexander "
                "Isak finishing at Selhurst Park, and Noah Okafor, on for 13 minutes at "
                "Elland Road, slamming in the only goal of Leeds against Spurs. It was "
                "not enough."
            ),
            ("HUF", "CRG"): (
                "HUF, 290 fans @ CRG, 220 fans. 688.5 at The CA$E, gate $27.54. "
                "CRG 65, HUF 54.5. The biggest building of the week, and first place lost "
                "in it. Alexis Mac Allister opened the scoring at Selhurst Park. Morgan "
                "Gibbs-White broke from halfway, went around Donnarumma, and squared for "
                "Delap's third, a goal that went on ASS's card, not HUF's. Mathys Tel was "
                "caught by Jayden Bogle at Elland Road. The VAR looked for four minutes "
                "and gave nothing. Tel went off in the 43rd. CRG had Evanilson, who has "
                "now scored in five straight, nicking it off Christian Walton in the fifth "
                "minute at Portman Road. HUF is 6-0-2."
            ),
            ("NAC", "BHB"): (
                "NAC, 50 fans @ BHB, 51 fans. 101 at The Great Northern, gate $4.04. "
                "NAC 62.5, BHB 53.5. Enzo Le Fée converted after Colwill and Brobbey "
                "grappled in the box, and Sunderland beat Chelsea. Vitalii Mykolenko "
                "headed the ball Thierno Barry equalised with at Goodison. BHB had Luka "
                "Vuskovic laying on Gómez, and Gianluigi Donnarumma standing behind City's "
                "third straight league loss."
            ),
            ("QFC", "POW"): (
                "QFC, 31 fans @ POW, 155 fans. 200.88 at The Stadium of Power, gate $8.04. "
                "POW 66, QFC 43.5. Florian Wirtz scored and created at Selhurst Park. "
                "Matheus Cunha laid on Tielemans in the 4-4. Brian Brobbey won the penalty "
                "Sunderland beat Chelsea with, then went off. QFC had Senne Lammens in that "
                "same 4-4, and nobody scoring."
            ),
            ("REN", "ASS"): (
                "REN, 160 fans @ ASS, 190 fans. 350 at Hinfield, gate $14.00. "
                "REN 82.5, ASS 75.5. The high score of the week, and still a game. Thierno "
                "Barry scored twice and set up the third as Everton came from behind against "
                "Coventry, David Moyes matching Harry Catterick on 592 games in charge. "
                "Bruno Fernandes converted at Old Trafford and then found Dorgu in the 96th "
                "minute. ASS had Delap's two against City, and Nicolas Jackson scoring in "
                "the fourth minute of the 4-4. Erling Haaland played the full 90 at the "
                "City Ground and did not score."
            ),
            ("TTS", "WTF"): (
                "TTS, 140 fans @ WTF, 105 fans. 245 at Stand of Oaks, gate $9.80. "
                "TTS 67.5, WTF 48. John McGinn converted from the spot at Old Trafford and "
                "had a hand in another. James Trafford kept a clean sheet while Leeds "
                "finally beat Spurs. WTF had Rayan Cherki's half-volley from 25 yards that "
                "made it 2-1 City. Forest scored again. Cherki's goal was the consolation."
            ),
        },
    },
}

# Gates from the matchday mail when gw_fans has no row for the week.
# sync_fans.py recomputes off the live table, so running it after the
# games would not reproduce the gate that was charged.
PUBLISHED_GATES = {
    8: {
        ("FAV", "NAC"): {"away_fans": 185, "home_fans": 50, "attendance": 235, "gate": 9.40},
        ("QFC", "HUF"): {"away_fans": 31, "home_fans": 250, "attendance": 303.48, "gate": 12.14},
        ("REN", "DU"): {"away_fans": 190, "home_fans": 100, "attendance": 324.8, "gate": 12.99},
        ("TTS", "CRG"): {"away_fans": 120, "home_fans": 300, "attendance": 420, "gate": 16.80},
        ("WTF", "BHB"): {"away_fans": 140, "home_fans": 51, "attendance": 191, "gate": 7.64},
        ("ASS", "POW"): {"away_fans": 140, "home_fans": 155, "attendance": 398.25, "gate": 15.93},
    },
    9: {
        ("FAV", "HUF"): {"away_fans": 210, "home_fans": 290, "attendance": 540, "gate": 21.60},
        ("NAC", "DU"): {"away_fans": 40, "home_fans": 150, "attendance": 190, "gate": 7.60},
        ("QFC", "CRG"): {"away_fans": 31, "home_fans": 220, "attendance": 271.08, "gate": 10.84},
        ("REN", "BHB"): {"away_fans": 145, "home_fans": 51, "attendance": 196, "gate": 7.84},
        ("TTS", "POW"): {"away_fans": 140, "home_fans": 145, "attendance": 285, "gate": 11.40},
        ("WTF", "ASS"): {"away_fans": 110, "home_fans": 180, "attendance": 290, "gate": 11.60},
    },
    10: {
        ("FAV", "DU"): {"away_fans": 200, "home_fans": 120, "attendance": 320, "gate": 12.80},
        ("HUF", "CRG"): {"away_fans": 290, "home_fans": 220, "attendance": 688.5, "gate": 27.54},
        ("NAC", "BHB"): {"away_fans": 50, "home_fans": 51, "attendance": 101, "gate": 4.04},
        ("QFC", "POW"): {"away_fans": 31, "home_fans": 155, "attendance": 200.88, "gate": 8.04},
        ("REN", "ASS"): {"away_fans": 160, "home_fans": 190, "attendance": 350, "gate": 14.00},
        ("TTS", "WTF"): {"away_fans": 140, "home_fans": 105, "attendance": 245, "gate": 9.80},
    },
}

# Fantrax opponent codes that are not the FPL short name.
CLUB_ALIAS = {"NOT": "NFO", "BRF": "BRE"}
OPP_RE = re.compile(r"([A-Z]{3}) (\d+) @([A-Z]{3}) (\d+)")


def _get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read().decode())


def num(value):
    value = float(value)
    if value.is_integer():
        return str(int(value))
    text = f"{value:.2f}".rstrip("0").rstrip(".")
    return text


def money(value):
    return f"${float(value):.2f}"


def names(items):
    labels = [item if isinstance(item, str) else item["label"] for item in items]
    if not labels:
        return ""
    if len(labels) == 1:
        return labels[0]
    if len(labels) == 2:
        return f"{labels[0]} and {labels[1]}"
    return ", ".join(labels[:-1]) + ", and " + labels[-1]


def label_for(player):
    web = player.get("web") or ""
    if web and "." not in web:
        return web
    return player["name"].split()[-1]


def fetch_gw_scores(sess, week):
    """Away, fpts, 0, total, home, fpts, 0, total. fetch_gameweek_scores
    reads this row as four cells and is wrong for it."""
    body = {"msgs": [{"method": "getStandings", "data": {"leagueId": fl.LEAGUE_ID}}]}
    resp = sess.post("https://www.fantrax.com/fxpa/req", params={"leagueId": fl.LEAGUE_ID}, json=body, timeout=30)
    resp.raise_for_status()
    data = resp.json()["responses"][0]["data"]
    table = next((t for t in data.get("tableList", []) if t.get("caption") == f"Gameweek {week}"), None)
    if not table:
        raise SystemExit(f"Fantrax has no Gameweek {week} table")
    games = []
    for row in table["rows"]:
        cells = [c.get("content") for c in row["cells"]]
        if len(cells) < 8:
            raise SystemExit(f"Gameweek {week} row is {len(cells)} cells, expected 8: {cells}")
        games.append({
            "away": fl.ALL_TEAM_ID_TO_CODE.get(row["cells"][0].get("teamId")),
            "away_score": float(cells[1]),
            "home": fl.ALL_TEAM_ID_TO_CODE.get(row["cells"][4].get("teamId")),
            "home_score": float(cells[5]),
        })
    return games


def fetch_fpl(week):
    boot = _get(FPL_BOOTSTRAP)
    teams = {t["id"]: t for t in boot["teams"]}
    by_short = {}
    for team in boot["teams"]:
        team["short_name"] = team["short_name"]
        by_short[team["short_name"]] = team["name"]
    for element in boot["elements"]:
        element["club_short"] = teams[element["team"]]["short_name"]
        element["club_name"] = teams[element["team"]]["name"]
    live = {row["id"]: row["stats"] for row in _get(FPL_LIVE.format(gw=week))["elements"]}
    event = next(e for e in boot["events"] if e["id"] == week)
    if not event["finished"]:
        raise SystemExit(f"FPL gameweek {week} is not finished")
    return build_lookup(boot["elements"]), live, by_short


def parse_opp(text):
    plain = text.replace("<br/>", " ").replace("<br>", " ")
    found = OPP_RE.search(plain)
    if not found:
        return None
    away, away_goals, home, home_goals = found.groups()
    return {
        "away": CLUB_ALIAS.get(away, away),
        "away_goals": int(away_goals),
        "home": CLUB_ALIAS.get(home, home),
        "home_goals": int(home_goals),
    }


CLUB_DISPLAY = {
    "Nott'm Forest": "Nottingham Forest",
    "Man City": "Manchester City",
    "Man Utd": "Manchester United",
}


def club_name(code, club_names):
    name = club_names.get(code, code)
    return CLUB_DISPLAY.get(name, name)


def possessive(name):
    return f"{name}'" if name.endswith("s") else f"{name}'s"


def fixture_phrase(opp, club_names):
    if not opp:
        return None
    home = club_name(opp["home"], club_names)
    away = club_name(opp["away"], club_names)
    hg, ag = opp["home_goals"], opp["away_goals"]
    if hg > ag:
        return f"{possessive(home)} {hg}-{ag} over {away}"
    if ag > hg:
        return f"{possessive(away)} {ag}-{hg} at {home}"
    return f"{possessive(home)} {hg}-{ag} with {away}"


def fetch_productions(sess, week, lookup, live, club_names):
    by_code = {}
    for code, team_id in fl.FANTRAX_TEAM_ID.items():
        data = fl._post(sess, "getTeamRosterInfo", teamId=team_id, view="STATS", period=week)
        players = []
        for table in data.get("tables", []):
            for row in table.get("rows", []):
                scorer = row.get("scorer") or {}
                name = scorer.get("name")
                pos_id = row.get("posId")
                if not name or pos_id not in fl.POSITION_MAP:
                    continue
                opp = parse_opp(row["cells"][1]["content"])
                parts = name.split()
                element = match(lookup, parts[-1], parts[0][:1] if parts else None)
                if element is None:
                    continue
                stats = live.get(element["id"]) or {}
                players.append({
                    "name": name,
                    "label": None,
                    "pos": fl.POSITION_MAP[pos_id],
                    "web": element["web_name"],
                    "club": element["club_short"],
                    "mins": stats.get("minutes") or 0,
                    "g": stats.get("goals_scored") or 0,
                    "a": stats.get("assists") or 0,
                    "cs": stats.get("clean_sheets") or 0,
                    "opp": opp,
                })
        for player in players:
            player["label"] = label_for(player)
        by_code[code] = players
    return by_code


def load_gates(week, games):
    published = PUBLISHED_GATES.get(week, {})
    conn = connect()
    rows = conn.execute(
        "SELECT team_code, opponent, is_home, fanbase, attendance, ticket_revenue FROM gw_fans WHERE week=?",
        (week,),
    ).fetchall()
    conn.close()
    stadiums = fetch_stadiums()
    out = {}
    if rows:
        by_code = {row[0]: row for row in rows}
        for game in games:
            home, away = game["home"], game["away"]
            home_row = by_code.get(home)
            away_row = by_code.get(away)
            if not home_row or not away_row:
                continue
            out[(away, home)] = {
                "away_fans": away_row[3],
                "home_fans": home_row[3],
                "attendance": home_row[4],
                "gate": (home_row[5] or 0) + (away_row[5] or 0),
                "stadium": (stadiums.get(home) or {}).get("stadium") or home,
            }
        if len(out) == len(games):
            return out
    for game in games:
        key = (game["away"], game["home"])
        gate = published.get(key)
        if not gate:
            raise SystemExit(f"No gate for GW{week} {game['away']} at {game['home']}. Run sync_fans.py before the games, or add the mailed gate to PUBLISHED_GATES.")
        out[key] = {
            **gate,
            "stadium": (stadiums.get(game["home"]) or {}).get("stadium") or game["home"],
        }
    return out


def goal_clause(player):
    if player["g"] == 2:
        return f"{player['label']} scored both"
    if player["g"] > 2:
        return f"{player['label']} scored {player['g']}"
    return f"{player['label']} scored"


def played_clause(player, club_names):
    played = "the full 90" if player["mins"] >= 89 else f"{player['mins']} minutes"
    where = f" in {fixture_phrase(player['opp'], club_names)}" if player["opp"] else ""
    return f"{player['label']} played {played}{where} and did not score."


def opp_key(opp):
    if not opp:
        return None
    return (opp["away"], opp["home"])


def club_lost(player):
    opp = player["opp"]
    if not opp:
        return False
    if player["club"] == opp["home"]:
        return opp["home_goals"] < opp["away_goals"]
    if player["club"] == opp["away"]:
        return opp["away_goals"] < opp["home_goals"]
    return False


def pick_blank(players, forwards_only=False):
    """One attacker who played a real loss and did not score or assist.
    A clean sheet is a return, so those players are not blanks."""
    positions = ("F",) if forwards_only else ("F", "M")
    candidates = [
        p for p in players
        if p["pos"] in positions and p["mins"] >= 70 and not p["g"] and not p["a"] and not p["cs"]
        and club_lost(p)
    ]
    if not candidates:
        return None
    return sorted(candidates, key=lambda p: (0 if p["pos"] == "F" else 1, -p["mins"], p["label"]))[0]


def describe_side(players, club_names, lost_big, show_blank, forwards_only=False):
    """Goals first. One assist, from a different match, when the side did
    not have two scorers. One blank. A keeper who sat while the other one
    played a blowout loss."""
    goals = sorted((p for p in players if p["g"]), key=lambda p: (-p["g"], -p["mins"]))
    assists = sorted((p for p in players if p["a"] and not p["g"]), key=lambda p: -p["mins"])
    sentences = []
    shown_goals = goals[:2]
    goal_keys = set()
    by_opp = {}
    for player in shown_goals:
        goal_keys.add(opp_key(player["opp"]))
        by_opp.setdefault(id(player["opp"]), {"opp": player["opp"], "goals": []})
        by_opp[id(player["opp"])]["goals"].append(player)
    for bucket in by_opp.values():
        sentences.append(f"{names([goal_clause(p) for p in bucket['goals']])} in {fixture_phrase(bucket['opp'], club_names)}.")
    if len(shown_goals) < 2:
        other = [p for p in assists if opp_key(p["opp"]) not in goal_keys]
        chosen = (other or assists)[:1]
        for player in chosen:
            sentences.append(f"{player['label']} assisted in {fixture_phrase(player['opp'], club_names)}.")
            goal_keys.add(opp_key(player["opp"]))
    keeper_line = None
    if lost_big:
        sat = [p for p in players if p["pos"] == "GK" and p["mins"] == 0]
        played = [p for p in players if p["pos"] == "GK" and p["mins"] >= 60 and not p["cs"]]
        if sat and played:
            keeper = played[0]
            keeper_line = f"{sat[0]['label']} did not play. {keeper['label']} played {fixture_phrase(keeper['opp'], club_names)}."
    blank = pick_blank(players, forwards_only=forwards_only)
    if show_blank and blank and not keeper_line:
        sentences.append(played_clause(blank, club_names))
    if keeper_line:
        sentences.append(keeper_line)
    return sentences, goal_keys


def render(week, games, standings, productions, gates, club_names):
    picks = PREVIEW_PICKS.get(week, {})
    prepared = []
    for game in games:
        key = (game["away"], game["home"])
        gate = gates[key]
        winner = game["home"] if game["home_score"] > game["away_score"] else game["away"]
        margin = abs(game["home_score"] - game["away_score"])
        prepared.append({
            **game,
            **gate,
            "winner": winner,
            "margin": margin,
            "pick": picks.get(key),
        })

    count_word = {1: "One", 2: "Two", 3: "Three", 4: "Four", 5: "Five", 6: "Six"}
    lost = [g for g in prepared if g["pick"] and g["pick"] != g["winner"]]
    high = max(prepared, key=lambda g: max(g["home_score"], g["away_score"]))
    high_side = high["home"] if high["home_score"] >= high["away_score"] else high["away"]
    high_score = max(high["home_score"], high["away_score"])
    blowout = max(prepared, key=lambda g: g["margin"])
    biggest_gate = max(prepared, key=lambda g: g["gate"])
    leader = next(row for row in standings if row["rank"] == 1 and not row["is_junior"])
    scoring_leader = max((row for row in standings if not row["is_junior"]), key=lambda row: row["fpts_for"])
    league_gate = sum(g["gate"] for g in prepared)

    # The real match the league actually played: most rostered minutes.
    # The week sentence names the attackers in it who did not score.
    by_fixture = {}
    for players in productions.values():
        for player in players:
            if player["mins"] >= 60 and player["opp"]:
                opp = player["opp"]
                key = (opp["away"], opp["away_goals"], opp["home"], opp["home_goals"])
                by_fixture.setdefault(key, []).append(player)
    shutout = max(by_fixture.items(), key=lambda item: (len(item[1]), item[0])) if by_fixture else None
    week_keys = set()

    copy = WEEK_COPY.get(week)
    if copy:
        paragraphs = [copy["headline"], copy["lede"]]
        missing = []
        for game in prepared:
            key = (game["away"], game["home"])
            graf = copy["games"].get(key)
            if not graf:
                missing.append(key)
                continue
            paragraphs.append(graf)
        if missing:
            raise SystemExit(f"WEEK_COPY[{week}] missing games: {missing}")
        paragraphs.append("-- MegaBot")
        paragraphs.append(email_brand.sponsor_cta())
        return prepared, paragraphs

    print(
        f"NO WEEK_COPY for GW{week}. This is the skeleton, not the email.\n"
        "Write WEEK_COPY[week] from the GW9 template: headline, lede, one graf\n"
        "per game. Pitch story first. Scores and gates are furniture.",
        file=sys.stderr,
    )

    paragraphs = []
    week_line = f"GW{week}."
    if lost:
        week_line += f" {count_word.get(len(lost), len(lost))} picks lost." if len(lost) != 1 else " One pick lost."
    if shutout:
        key, players = shutout
        week_keys.add((key[0], key[2]))
        opp = {"away": key[0], "away_goals": key[1], "home": key[2], "home_goals": key[3]}
        phrase = fixture_phrase(opp, club_names)
        scorers = sorted((p for p in players if p["g"]), key=lambda p: (-p["g"], p["label"]))[:3]
        week_line += f" {phrase[0].upper()}{phrase[1:]}."
        if scorers:
            week_line += " " + " ".join(f"{goal_clause(p)}." for p in scorers)
    where = "at the biggest gate" if high is biggest_gate else ""
    week_line += f" {high_side} scored {num(high_score)}, the high score{', ' + where if where else ''}."
    if blowout is not high:
        week_line += f" {blowout['winner']} won by {num(blowout['margin'])}."
    week_line += f" {leader['code']} is {leader['record']}, first."
    if scoring_leader["code"] != leader["code"]:
        week_line += f" {scoring_leader['code']} has scored {num(scoring_leader['fpts_for'])}, the most in the league, and is {scoring_leader['record']}."
    week_line += f" League gate {money(league_gate)}."
    paragraphs.append(week_line)

    for game in prepared:
        loser = game["away"] if game["winner"] == game["home"] else game["home"]
        gate_line = (
            f"{game['away']}, {num(game['away_fans'])} fans @ {game['home']}, {num(game['home_fans'])} fans. "
            f"{num(game['attendance'])} at {game['stadium']}, gate {money(game['gate'])}. "
            f"{game['winner']} {num(game['home_score'] if game['winner']==game['home'] else game['away_score'])}, "
            f"{loser} {num(game['away_score'] if game['winner']==game['home'] else game['home_score'])}."
        )
        story = []
        if game["pick"] and game["pick"] != game["winner"]:
            story.append(f"The pick was {game['pick']}. {game['winner']} won by {num(game['margin'])}.")
        elif game["pick"]:
            story.append(f"The pick was {game['pick']}, and it held.")
        if game is biggest_gate and game["winner"] != game["home"]:
            story.append("The biggest building, and the visitors won.")
        winner_story, winner_keys = describe_side(
            productions.get(game["winner"], []), club_names, False, True, forwards_only=True)
        loser_story, _loser_keys = describe_side(
            productions.get(loser, []), club_names, game["margin"] >= 20, True)
        story.extend(winner_story)
        story.extend(loser_story)
        paragraphs.append(gate_line + " " + " ".join(story))

    paragraphs.append("-- MegaBot")
    paragraphs.append(email_brand.sponsor_cta())
    return prepared, paragraphs


def render_html(week, paragraphs):
    body = []
    body.append(f'<p style="margin:0 0 8px;font-family:Arial,Helvetica,sans-serif;font-size:13px;letter-spacing:2px;font-weight:700;">MEGAVISION <span style="color:{email_brand.PINK}">× POLYSCI</span></p>')
    # WEEK_COPY: headline, lede, games. Skeleton: one fat week_line, then games
    # that start "CODE, N fans @".
    if len(paragraphs) > 2 and not re.match(r"^[A-Z]{2,4}, ", paragraphs[1]):
        title, rest, game_paras = paragraphs[0], paragraphs[1], paragraphs[2:-2]
    else:
        bits = paragraphs[0].split(". ")
        title = ". ".join(bits[:2])
        rest = ". ".join(bits[2:]).strip()
        game_paras = paragraphs[1:-2]
    body.append(f'<p style="margin:0 0 14px;font-family:Arial,Helvetica,sans-serif;font-size:22px;line-height:1.25;font-weight:700;">{html.escape(title)}</p>')
    if rest:
        body.append(f'<p style="margin:0 0 16px;font-family:Arial,Helvetica,sans-serif;font-size:15px;line-height:1.55;">{html.escape(rest)}</p>')
    for paragraph in game_paras:
        body.append(f'<p style="margin:0 0 16px;font-family:Arial,Helvetica,sans-serif;font-size:15px;line-height:1.55;">{html.escape(paragraph)}</p>')
    body.append('<p style="margin:0;font-family:Arial,Helvetica,sans-serif;font-size:15px;">-- MegaBot</p>')
    inner = "\n".join(body)
    return f'''<!doctype html>
<html>
<head><meta charset="utf-8"><title>MEGAVISION GW{week}</title></head>
<body style="margin:0;background:#EFEEEE;font-family:Arial,Helvetica,sans-serif;color:#0F0F0F;">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#EFEEEE;">
<tr><td align="center" style="padding:24px 12px;">
<table role="presentation" width="600" cellpadding="0" cellspacing="0" style="width:600px;max-width:600px;background:#ffffff;border:1px solid #ddd;">
<tr><td style="padding:28px 28px 8px;">{inner}</td></tr>
        <tr><td>{email_brand.sponsor_cta_html(include_banner=False)}</td></tr>
</table>
</td></tr>
</table>
</body>
</html>
'''


def build(week):
    print("Fantrax scores...", file=sys.stderr)
    sess = fl._session()
    games = fetch_gw_scores(sess, week)
    standings = fl.fetch_all_standings(sess)
    print("FPL gameweek...", file=sys.stderr)
    lookup, live, club_names = fetch_fpl(week)
    print("Rosters...", file=sys.stderr)
    productions = fetch_productions(sess, week, lookup, live, club_names)
    gates = load_gates(week, games)
    return render(week, games, standings, productions, gates, club_names)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("week", type=int)
    parser.add_argument("--html", type=Path)
    args = parser.parse_args()
    _prepared, paragraphs = build(args.week)
    text = "\n\n".join(paragraphs)
    print(text)
    if args.html:
        args.html.write_text(render_html(args.week, paragraphs))
        print(f"wrote {args.html}", file=sys.stderr)


if __name__ == "__main__":
    main()
