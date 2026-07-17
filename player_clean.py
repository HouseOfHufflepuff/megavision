"""Parse the messy 'Player' column from the spreadsheet into separate
player_name / real_club / note fields, cross-checked against the sheet's
own Pos column. Handles the observed format zoo:

  'Evanilson - F BOU'                -> name, club, embedded pos stripped
  'White, Ben D - ARS*'              -> 'Last, First POS - CLUB*'
  'Tilemans, Youri, M - AVL'         -> 'Last, First, POS - CLUB' (double comma)
  'Mitoma, Karou, M-BHA'             -> no spaces around dash
  'Colwill, Levi'                    -> 'Last, First' only, no club
  'Lewis, Rico D - MCI (QFC Loan)'   -> parenthetical note stripped out
  'Virgil van Dijk'                  -> already clean, pass through
  'P. Porro' / 'R. Ngumoha'          -> initial + last, flagged for review
  'Gomez' / 'Beto'                   -> single token, flagged for review
  'Arsenal GK' / 'Newcastle'         -> auto-GK placeholder, not a real player
"""
import re

POS_CODES = {"GK", "G", "D", "M", "F"}

# clubs seen in the sheet, used to recognize club-name-only GK placeholder rows
KNOWN_CLUBS = {
    "arsenal", "aston villa", "bournemouth", "brentford", "brighton", "burnley",
    "chelsea", "crystal palace", "everton", "fulham", "leeds", "liverpool",
    "man city", "manchester city", "man united", "manchester united", "newcastle",
    "nottingham forest", "sunderland", "tottenham", "west ham", "wolves",
}

# Manual resolutions for names the sheet only gives as an initial or bare
# surname. Confirmed either from known current EPL rosters or (marked *)
# a live web search done while building this table, since these are real
# identities, not guessable from the spreadsheet alone.
NAME_OVERRIDES = {
    "p. porro": "Pedro Porro",
    "e. konsa": "Ezri Konsa",
    "i. ndiaye": "Iliman Ndiaye",
    "a. onana": "Amadou Onana",
    "b. saka": "Bukayo Saka",
    "m. wieffer": "Mats Wieffer",
    "c. gakpo": "Cody Gakpo",
    "a. semenyo": "Antoine Semenyo",
    "o. marmoush": "Omar Marmoush",
    "e. guessand": "Evann Guessand",       # *web-verified
    "r. ngumoha": "Rio Ngumoha",
    "h barnes": "Harvey Barnes",
    "lavia": "Romeo Lavia",
    "mcatee": "James McAtee",
    "madison": "James Maddison",           # sheet typo for Maddison
    "aina": "Ola Aina",
    "dalot": "Diogo Dalot",
    "truffert": "Adrien Truffert",         # *web-verified
    "kayode": "Michael Kayode",            # *web-verified
    "kerkez": "Milos Kerkez",
    "adli": "Amine Adli",                  # *web-verified
    "stach": "Anton Stach",
    "zinchenko": "Oleksandr Zinchenko",
    "richarilson": "Richarlison",          # sheet typo
    "r dias": "Ruben Dias",
}


def _strip_note(raw):
    m = re.search(r"\(([^)]*)\)", raw)
    note = m.group(1).strip() if m else None
    cleaned = re.sub(r"\([^)]*\)", "", raw).strip()
    return cleaned, note


def clean_player(raw, sheet_pos):
    """Returns dict: player_name, real_club, note, needs_review, is_placeholder_gk"""
    if raw is None:
        return None
    original = str(raw).strip()
    s, note = _strip_note(original)
    s = s.strip().rstrip("*").strip()
    s = re.sub(r"\s+", " ", s)

    if not s:
        return {"player_name": original, "real_club": None, "note": note,
                "needs_review": True, "is_placeholder_gk": False, "resolved_via_override": False}

    # club-name-only "auto GK" placeholder row
    if (sheet_pos or "").upper() in ("GK", "G") and s.lower() in KNOWN_CLUBS:
        return {"player_name": None, "real_club": s, "note": note,
                "needs_review": True, "is_placeholder_gk": True, "resolved_via_override": False}
    if s.upper().endswith(" GK") and s[:-3].strip().lower() in KNOWN_CLUBS:
        return {"player_name": None, "real_club": s[:-3].strip(), "note": note,
                "needs_review": True, "is_placeholder_gk": True, "resolved_via_override": False}

    club = None
    name_part = s

    # split off whatever's after the LAST dash: either "- CLUB" or "- POS CLUB".
    # Greedy left group so a hyphenated surname like "Hudson-Odoi" (no spaces
    # around its internal dash) isn't mistaken for the separator -- the real
    # separator is always the rightmost dash in these rows. Club token can be
    # a short abbreviation (BOU, ARS) or a spelled-out name (Leeds).
    m = re.match(r"^(.*)\s*-\s*(.+)$", s)
    if m:
        left, right = m.group(1).strip(), m.group(2).strip()
        right_tokens = right.split()
        if len(right_tokens) == 1 and re.match(r"^[A-Za-z]{2,15}$", right_tokens[0]) \
                and right_tokens[0].upper() != "ON":
            name_part, club = left, right_tokens[0].upper()
        elif len(right_tokens) == 2 and right_tokens[0].strip(",").upper() in POS_CODES \
                and re.match(r"^[A-Za-z]{2,15}$", right_tokens[1]):
            name_part, club = left, right_tokens[1].upper()

    # strip a trailing embedded position code token (e.g. "... D", "... M")
    tokens = name_part.split(" ")
    if len(tokens) > 1 and tokens[-1].strip(",").upper() in POS_CODES:
        tokens = tokens[:-1]
        name_part = " ".join(tokens).strip()

    needs_review = False

    if "," in name_part:
        # "Last, First" or "Last, First, POS" (extra trailing comma part)
        parts = [p.strip() for p in name_part.split(",") if p.strip()]
        if len(parts) >= 2:
            last, first = parts[0], parts[1]
            # a stray 3rd comma part that's actually a position code
            if len(parts) >= 3 and parts[2].upper() in POS_CODES:
                pass
            name_part = f"{first} {last}"
        else:
            needs_review = True

    name_part = re.sub(r"\s+", " ", name_part).strip().strip(",")

    # flag low-confidence shapes: single token, or "Initial. Last"
    if not needs_review:
        nt = name_part.split(" ")
        if len(nt) == 1:
            needs_review = True
        elif len(nt) == 2 and re.match(r"^[A-Za-z]\.?$", nt[0]):
            needs_review = True

    if not name_part:
        name_part = original
        needs_review = True

    resolved = False
    override = NAME_OVERRIDES.get(name_part.lower())
    if override:
        name_part = override
        needs_review = False
        resolved = True

    return {
        "player_name": name_part,
        "real_club": club,
        "note": note,
        "needs_review": needs_review,
        "is_placeholder_gk": False,
        "resolved_via_override": resolved,
    }


if __name__ == "__main__":
    # Always live -- fetches fresh over HTTP, no cached snapshot, so this
    # self-test reflects whatever is in the sheet at the moment it's run.
    from common import TEAMS, fetch_live_workbook, find_team_sheet
    from datetime import datetime, timezone

    print(f"Fetching live spreadsheet ({datetime.now(timezone.utc).isoformat()}) ...")
    wb = fetch_live_workbook()
    raw = []
    for code, _, _ in TEAMS:
        sn = find_team_sheet(wb, code)
        if not sn:
            continue
        rows = list(wb[sn].iter_rows(min_row=1, max_row=40, values_only=True))
        header_idx = next((i for i, r in enumerate(rows) if r[1] == "Player" and r[2] == "Pos"), None)
        if header_idx is None:
            continue
        for r in rows[header_idx + 1:]:
            if r[0] == "Total":
                break
            if r[1] is not None:
                raw.append((code, r[1], r[2]))

    reviewed = []
    leaked = []
    clean_ct = 0
    for code, player, pos in raw:
        r = clean_player(player, pos)
        if r["player_name"] and " - " in r["player_name"]:
            leaked.append((code, player, pos, r))
        if r["needs_review"] or r["is_placeholder_gk"]:
            reviewed.append((code, player, pos, r))
        else:
            clean_ct += 1
    print(f"clean: {clean_ct}  needs_review: {len(reviewed)}  total: {len(raw)}")
    if leaked:
        print(f"\n!! {len(leaked)} UNPARSED (raw dash string leaked into player_name):")
        for code, player, pos, r in leaked:
            print(f"  {code:5} {player!r} -> {r}")
    print()
    for code, player, pos, r in reviewed:
        print(f"{code:5} {player!r:45} pos={pos!r:4} -> {r}")
