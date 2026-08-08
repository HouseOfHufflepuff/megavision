"""
Sync the Fantrax 26/27 league's rosters to match the "CUT EM IF YA GOT EM"
sheet's Kept Contracts / Youth Legend of the Club / Youth Players boxes, one
team at a time.

Run:
    python3 sync_fantrax_keepers.py            # apply changes
    python3 sync_fantrax_keepers.py --dry-run   # just print the plan

Always fetches the sheet live. Policy: each team's live Fantrax roster should
end up exactly matching its Kept + Youth Legend + Youth Players names --
anyone in that list who isn't rostered gets added (via commissioner claim),
anyone rostered who isn't in that list gets dropped. MS8 is always skipped
(team is being removed from Fantrax; its sheet tab is ignored).

Player names on the sheet are messy (typos, "Last, First" order, missing
accents, club-code suffixes) so matching against real Fantrax player names
uses token-subset + Levenshtein fuzzy matching, not a literal string match.
Anything that can't be matched with confidence is reported and skipped --
never guessed.
"""
import re
import sys
import time
import uuid

import fantrax_live
from common import fetch_live_workbook

LEAGUE_ID = "9rv5verjmrz6rjuo"  # 26/27 season
SKIP_CODES = {"MS8"}

# sheet code -> Fantrax team id, cross-referenced by name against fantrax_live's
# old-league mapping (team names are stable across the league copy)
CODE_TO_TEAM_NAME = {
    "FAV": "5th Ave Argyle", "POW": "Battersea Power", "CRG": "CRG McGovern",
    "DU": "Divided United", "HUF": "House of Hufflepuff", "NAC": "NFC Andover City",
    "QFC": "Quidpool FC", "RNE": "Real News", "BHB": "Bookhouse Boys",
    "TTS": "Thottenham Thotspur", "WTF": "What The FC", "ASS": "Wholeassed United FC",
}

POS_MAP = {"F": "701", "M": "702", "D": "703", "GK": "704", "G": "704"}


def norm(s):
    return re.sub(r"[^a-z]", "", s.lower())


def lev(a, b):
    if a == b:
        return 0
    la, lb = len(a), len(b)
    prev = list(range(lb + 1))
    for i in range(1, la + 1):
        cur = [i] + [0] * lb
        for j in range(1, lb + 1):
            cost = 0 if a[i - 1] == b[j - 1] else 1
            cur[j] = min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + cost)
        prev = cur
    return prev[lb]


def extract_team_boxes(wb):
    """sheet code -> {kept: [...], youth_legend: [...], youth_players: [...]},
    each a list of {name, pos} straight off the sheet."""
    ws = wb["CUT EM IF YA GOT EM"]
    rows = list(ws.iter_rows(min_row=1, max_row=101, values_only=True))
    label_row = rows[4]
    blocks = {}
    for i, v in enumerate(label_row):
        if v in ("BHB", "DU", "RNE", "QFC", "ASS", "CRG", "FAV", "HUF", "NAC", "POW", "WTF", "MS8", "TTS"):
            blocks[v] = i

    def box(col, start, end):
        out = []
        for r in range(start, end + 1):
            row = rows[r - 1]
            if row[col]:
                out.append({"name": row[col], "pos": row[col + 1]})
        return out

    data = {}
    for code, col in blocks.items():
        if code in SKIP_CODES:
            continue
        data[code] = {
            "kept": box(col, 22, 29),
            "youth_legend": box(col, 31, 31),
            "youth_players": box(col, 34, 40),
        }
    return data


# sheet club-code -> real Fantrax teamShortName, for the handful that differ
# ("CPY" is a sheet typo for Crystal Palace's real short name "CRY")
CLUB_CODE_ALIASES = {"CPY": "CRY"}
CLUB_CODES = {"ARS", "MCI", "CHE", "LIV", "TOT", "MUN", "NEW", "AVL", "BOU", "BRE", "BRF",
              "BHA", "BUR", "CRY", "CPY", "EVE", "FUL", "LEE", "NOT", "SUN", "WHU"}


def tokenize(raw):
    """Returns (name_tokens, club_code_or_None)."""
    s = raw.strip().rstrip("*").strip()
    s = re.sub(r"\(.*?\)", "", s)
    s = s.replace(",", " ")
    s = re.sub(r"[-–]", " ", s)
    pos_tokens = {"D", "M", "F", "G", "GK"}
    out = []
    club = None
    for p in re.split(r"\s+", s):
        if not p:
            continue
        pu = p.upper().rstrip(".")
        if pu in CLUB_CODES:
            club = CLUB_CODE_ALIASES.get(pu, pu)
            continue
        if pu in pos_tokens:
            continue
        out.append(p.rstrip("."))
    return out, club


def _post_retry(sess, url, params, body, timeout=25, retries=3):
    last_exc = None
    for attempt in range(retries):
        try:
            return sess.post(url, params=params, json=body, timeout=timeout)
        except Exception as e:
            last_exc = e
            time.sleep(1.5 * (attempt + 1))
    raise last_exc


def _pool_from_league(sess, league_id):
    r = sess.get("https://www.fantrax.com/fxea/general/getStandings", params={"leagueId": league_id}, timeout=20)
    pool = {}
    for row in r.json():
        body = {"msgs": [{"method": "getTeamRosterInfo", "data": {
            "leagueId": league_id, "teamId": row["teamId"], "view": "STATS"}}]}
        resp = _post_retry(sess, "https://www.fantrax.com/fxpa/req", {"leagueId": league_id}, body)
        data = resp.json()["responses"][0].get("data", {})
        for t in data.get("tables", []):
            for rrow in t.get("rows", []):
                sc = rrow.get("scorer")
                if sc and sc.get("name") and sc.get("scorerId"):
                    pool.setdefault(sc["name"], (sc["scorerId"], sc.get("posShortNames"), sc.get("teamShortName")))
    return pool


def build_name_pool(sess):
    """name -> (scorerId, posShortNames, teamShortName), pulled from every
    team's current 26/27 roster PLUS the old 25/26 league's rosters (a much
    bigger pool, catches free agents that aren't owned by anyone yet this
    season -- the same real player keeps the same scorerId across league
    copies). The 26/27 pool is checked/preferred first since it's the
    current source of truth; the old league only fills in names missing
    from it."""
    pool = _pool_from_league(sess, LEAGUE_ID)
    old_pool = _pool_from_league(sess, fantrax_live.LEAGUE_ID)
    for name, val in old_pool.items():
        pool.setdefault(name, val)
    return pool


def match_name(raw, sheet_pos, name_pool):
    """Returns (scorerId, matched_name, how) or (None, None/candidates, reason)."""
    tokens, club = tokenize(raw)
    if not tokens:
        return None, None, "no_tokens"
    joined = norm("".join(tokens))
    joined_rev = norm("".join(reversed(tokens)))
    for full, (sid, pos, team) in name_pool.items():
        nf = norm(full)
        if nf == joined or nf == joined_rev:
            return sid, full, "exact"
    candidates = [(full, sid, pos, team) for full, (sid, pos, team) in name_pool.items()
                  if all(norm(t) in norm(full) for t in tokens if len(norm(t)) > 1)]
    if len(candidates) == 1:
        return candidates[0][1], candidates[0][0], "token_subset"
    if len(candidates) > 1:
        # disambiguate by sheet club code first (most specific), then position
        if club:
            by_club = [c for c in candidates if c[3] == club]
            if len(by_club) == 1:
                return by_club[0][1], by_club[0][0], "token_subset+club"
            if len(by_club) > 1:
                candidates = by_club
        want_pos = {"F": "F", "M": "M", "D": "D", "GK": "G", "G": "G"}.get((sheet_pos or "").strip().upper())
        by_pos = [c for c in candidates if want_pos and c[2] == want_pos]
        if len(by_pos) == 1:
            return by_pos[0][1], by_pos[0][0], "token_subset+pos"
        return None, [c[0] for c in candidates], "ambiguous"
    # fuzzy fallback: edit distance against the full concatenated name, trying
    # both token orders (handles "Last, First" sheet formatting).
    scored = []
    for full, (sid, pos, team) in name_pool.items():
        nf = norm(full)
        d1 = min(lev(joined, nf), lev(joined_rev, nf))
        scored.append((d1, full, sid))
    scored.sort(key=lambda x: x[0])
    if scored and scored[0][0] <= 2 and (len(scored) == 1 or scored[1][0] - scored[0][0] >= 2):
        return scored[0][2], scored[0][1], "fuzzy"

    # single-token sheet entries (surname only, no first name given) get a
    # second chance matched against just each candidate's last word -- this
    # signal is too noisy to use when the sheet gave a first name too (a
    # short first name like "Hugo" can spuriously tie against an unrelated
    # surname like "Hato"), so it's restricted to the surname-only case.
    if len(tokens) == 1:
        scored2 = []
        for full, (sid, pos, team) in name_pool.items():
            last = norm(full.split()[-1])
            scored2.append((lev(joined, last), full, sid, team))
        scored2.sort(key=lambda x: x[0])
        if scored2 and scored2[0][0] <= 2:
            # a matching club code independently confirms the top candidate,
            # so a close runner-up (e.g. an unrelated surname of similar
            # length) doesn't have to be ruled out by distance alone
            if club and scored2[0][3] == club:
                return scored2[0][2], scored2[0][1], "fuzzy_surname+club"
            if len(scored2) == 1 or scored2[1][0] - scored2[0][0] >= 2:
                return scored2[0][2], scored2[0][1], "fuzzy_surname"

    return None, None, "no_match"


def get_claim_defaults(sess, team_id, scorer_id):
    body = {"msgs": [{"method": "getClaimDropCommissionerConfirmInfo", "data": {
        "leagueId": LEAGUE_ID, "adminMode": True,
        "transactionSets": [{"transactions": [{"type": "CLAIM", "teamId": team_id, "scorerId": scorer_id}]}],
    }}]}
    resp = sess.post("https://www.fantrax.com/fxpa/req", params={"leagueId": LEAGUE_ID}, json=body, timeout=30)
    d = resp.json()["responses"][0]
    if "pageError" in d:
        return None, d["pageError"].get("text", d["pageError"].get("code"))
    return d["data"]["confirmResponses"][0], None


def do_claim(sess, team_id, scorer_id, info):
    txn = {
        "type": "CLAIM", "teamId": team_id, "scorerId": scorer_id,
        "positionId": info["defaultPosId"], "claimToStatusId": info["defaultStatusId"], "bid": 0,
    }
    if info.get("defaultContractSmallId") is not None:
        txn["contractSmallId"] = info["defaultContractSmallId"]
    body = {"msgs": [{"method": "createClaimDropCommissioner", "data": {
        "leagueId": LEAGUE_ID, "adminMode": True, "adminModeClaimImmediate": True,
        "transactionSets": [{"transactions": [txn]}],
    }}]}
    resp = sess.post("https://www.fantrax.com/fxpa/req", params={"leagueId": LEAGUE_ID}, json=body, timeout=30)
    d = resp.json()["responses"][0]
    if "pageError" in d:
        return False, d["pageError"].get("text", d["pageError"].get("code"))
    tx = d["data"]["txResponses"][0]
    if tx.get("code") == "EXECUTED":
        return True, None
    return False, tx.get("detailMessages") or tx.get("genericMessage")


def do_drop(sess, team_id, scorer_id):
    body = {"msgs": [{"method": "createClaimDropCommissioner", "data": {
        "leagueId": LEAGUE_ID, "adminMode": True, "adminModeClaimImmediate": True,
        "transactionSets": [{"transactions": [{"type": "DROP", "teamId": team_id, "scorerId": scorer_id}]}],
    }}]}
    resp = sess.post("https://www.fantrax.com/fxpa/req", params={"leagueId": LEAGUE_ID}, json=body, timeout=30)
    d = resp.json()["responses"][0]
    if "pageError" in d:
        return False, d["pageError"].get("text", d["pageError"].get("code"))
    tx = d["data"]["txResponses"][0]
    if tx.get("code") == "EXECUTED":
        return True, None
    return False, tx.get("detailMessages") or tx.get("genericMessage")


def main():
    dry_run = "--dry-run" in sys.argv

    print("Fetching live spreadsheet...")
    wb = fetch_live_workbook()
    boxes = extract_team_boxes(wb)

    sess = fantrax_live._session()

    print("Building name pool from current 26/27 + 25/26 rosters...")
    name_pool = build_name_pool(sess)
    print(f"  {len(name_pool)} distinct player names in pool")

    r = sess.get("https://www.fantrax.com/fxea/general/getStandings", params={"leagueId": LEAGUE_ID}, timeout=20)
    team_name_to_id = {row["teamName"]: row["teamId"] for row in r.json()}

    unresolved = []
    plan = {}  # code -> {"add": [(name, scorerId)], "drop": [(name, scorerId)]}

    for code, d in boxes.items():
        team_name = CODE_TO_TEAM_NAME.get(code)
        team_id = team_name_to_id.get(team_name)
        if not team_id:
            print(f"WARN: no Fantrax team id for {code} ({team_name}), skipping", file=sys.stderr)
            continue

        target = {}
        for box_name in ("kept", "youth_legend", "youth_players"):
            for p in d[box_name]:
                sid, matched_name, how = match_name(p["name"], p["pos"], name_pool)
                if sid is None:
                    unresolved.append((code, box_name, p["name"], how))
                    continue
                target[sid] = matched_name

        body = {"msgs": [{"method": "getTeamRosterInfo", "data": {
            "leagueId": LEAGUE_ID, "teamId": team_id, "view": "STATS"}}]}
        resp = _post_retry(sess, "https://www.fantrax.com/fxpa/req", {"leagueId": LEAGUE_ID}, body)
        current = resp.json()["responses"][0].get("data", {})
        current_ids = {}
        for t in current.get("tables", []):
            for row in t.get("rows", []):
                sc = row.get("scorer")
                if sc and sc.get("scorerId"):
                    current_ids[sc["scorerId"]] = sc["name"]

        to_add = [(name, sid) for sid, name in target.items() if sid not in current_ids]
        to_drop = [(name, sid) for sid, name in current_ids.items() if sid not in target]

        if to_add or to_drop:
            plan[code] = {"team_id": team_id, "add": to_add, "drop": to_drop}

    print("\n=== PLAN ===")
    for code, p in plan.items():
        print(f"{code}:")
        for name, sid in p["add"]:
            print(f"  + add  {name} ({sid})")
        for name, sid in p["drop"]:
            print(f"  - drop {name} ({sid})")
    if unresolved:
        print("\n=== UNRESOLVED (skipped, need manual review) ===")
        for code, box_name, raw, how in unresolved:
            print(f"  {code} {box_name}: {raw!r} ({how})")

    if dry_run:
        print("\n(dry run, no changes made)")
        return

    print("\n=== EXECUTING ===")
    for code, p in plan.items():
        team_id = p["team_id"]
        for name, sid in p["drop"]:
            ok, err = do_drop(sess, team_id, sid)
            print(f"{code} DROP {name} -> {'OK' if ok else 'FAIL: ' + str(err)}")
            time.sleep(0.4)
        for name, sid in p["add"]:
            info, err = get_claim_defaults(sess, team_id, sid)
            if info is None:
                print(f"{code} ADD {name} -> FAIL (confirm): {err}")
                continue
            ok, err = do_claim(sess, team_id, sid, info)
            print(f"{code} ADD {name} -> {'OK' if ok else 'FAIL: ' + str(err)}")
            time.sleep(0.4)

    print("\nDone.")


if __name__ == "__main__":
    main()
