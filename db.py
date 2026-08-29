"""Lightweight local SQLite DB for MEGAVISION financial modeling.

No ORM, no server, one file: mega.db. Schema is created on first connect.
"""
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "mega.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS teams (
    code TEXT PRIMARY KEY,
    full_name TEXT NOT NULL,
    owner_display TEXT
);

CREATE TABLE IF NOT EXISTS team_players (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    team_code TEXT NOT NULL REFERENCES teams(code),
    roster_slot INTEGER,
    player_name_raw TEXT NOT NULL,
    player_name TEXT,
    position TEXT,
    real_club TEXT,
    note TEXT,
    needs_review INTEGER NOT NULL DEFAULT 0,
    is_placeholder_gk INTEGER NOT NULL DEFAULT 0,
    resolved_via_override INTEGER NOT NULL DEFAULT 0,
    salary_year1_label TEXT,
    salary_year1 REAL,
    salary_year2_label TEXT,
    salary_year2 REAL,
    salary_year3_label TEXT,
    salary_year3 REAL,
    buyout REAL,
    salary_24_25 REAL,
    salary_24_25_source TEXT,
    fc26_rating REAL,
    fc26_potential REAL,
    fc26_value_eur REAL,
    fc26_rating_updated_at TEXT,
    fpl_starts INTEGER,
    fpl_goals INTEGER,
    fpl_assists INTEGER,
    fpl_minutes INTEGER,
    fpl_tackles INTEGER,
    fpl_cbi INTEGER,
    fpl_xg REAL,
    fpl_stats_updated_at TEXT,
    updated_at TEXT NOT NULL,
    UNIQUE(team_code, player_name_raw)
);

CREATE TABLE IF NOT EXISTS fbref_players (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    player_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    club TEXT,
    games INTEGER,
    games_started INTEGER,
    goals INTEGER,
    assists INTEGER,
    goals_per90 REAL,
    goals_assists_per90 REAL,
    xg_per90 REAL,
    sca_per90 REAL,
    gca_per90 REAL,
    tackles INTEGER,
    clearances INTEGER,
    passes_completed INTEGER,
    updated_at TEXT NOT NULL,
    UNIQUE(player_name, club)
);

CREATE TABLE IF NOT EXISTS team_player_wages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    team_code TEXT NOT NULL,
    player_name TEXT NOT NULL,
    category TEXT NOT NULL,   -- kept, youth_legend, youth_players, drafted
    season TEXT NOT NULL,     -- '25/26', '26/27', '27/28'
    wage REAL,
    source TEXT NOT NULL,     -- team_tab (real 3yr contract), cut_em_sheet (2yr fallback), fpl_price (drafted, single year)
    updated_at TEXT NOT NULL,
    UNIQUE(team_code, player_name, season)
);

CREATE TABLE IF NOT EXISTS transfers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    player_name TEXT NOT NULL,
    from_team TEXT NOT NULL,   -- selling team, receives the fee
    to_team TEXT NOT NULL,     -- buying team, pays the fee
    amount REAL NOT NULL,
    season TEXT NOT NULL,      -- season the fee counts against, e.g. '26/27'
    transfer_date TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS titles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    season TEXT NOT NULL,        -- e.g. '26/27'
    competition TEXT NOT NULL,   -- 'Community Shield', 'Super Cup', ...
    team_code TEXT NOT NULL,
    payout REAL NOT NULL,        -- static fee paid out to the winner from the league pot
    awarded_date TEXT,
    created_at TEXT NOT NULL,
    UNIQUE(season, competition)
);

CREATE TABLE IF NOT EXISTS gw_fans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    week INTEGER NOT NULL,
    team_code TEXT NOT NULL,
    opponent TEXT NOT NULL,
    is_home INTEGER NOT NULL,
    base_score REAL,          -- this team's season-level fan-algo base score that week
    fanbase REAL,              -- this team's share of the total league fan pool that week
    interest REAL,             -- fanbase after this game's matchup bonuses
    attendance REAL,           -- interest, capped at host stadium capacity (home row only)
    ticket_revenue REAL,       -- this team's cut of the gate (80% home / 20% away)
    bonuses TEXT,              -- comma-joined reasons, e.g. "Derby Day (+35%)"
    updated_at TEXT NOT NULL,
    UNIQUE(week, team_code)
);

CREATE TABLE IF NOT EXISTS best11 (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    week INTEGER NOT NULL,       -- displayed GW number
    pos TEXT NOT NULL,           -- GK, D, M, F
    slot_rank INTEGER NOT NULL,  -- 1st, 2nd, ... within that position for this week
    player_name TEXT NOT NULL,
    real_club TEXT,
    team_code TEXT,              -- owning Mega team (Jr rosters folded into Sr code)
    fpts REAL,
    updated_at TEXT NOT NULL,
    UNIQUE(week, pos, slot_rank)
);

CREATE TABLE IF NOT EXISTS team_week_financials (
    team_code TEXT NOT NULL REFERENCES teams(code),
    week INTEGER NOT NULL,
    salary_cost REAL NOT NULL,
    basis TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    PRIMARY KEY (team_code, week)
);

-- Roster edits since the last keeper-sheet/draft-json snapshot (owner
-- add/cut requests, category reassignments) -- applied on top of
-- parse_keeper_roster() + draft_picks_2627.json in update_rosters.py.
-- The DB is the source of truth for anything that changes mid-season;
-- the sheet/json stay frozen as historical inputs.
CREATE TABLE IF NOT EXISTS roster_overrides (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    team_code TEXT NOT NULL,
    player_name TEXT NOT NULL,   -- match key, substring-matched against the sheet/json's raw name
    action TEXT NOT NULL,        -- add, remove, recategorize
    position TEXT,               -- add only
    real_club TEXT,               -- add only
    category TEXT,                -- add/recategorize: kept, youth_legend, youth_players, drafted
    updated_at TEXT NOT NULL,
    UNIQUE(team_code, player_name, action)
);

-- MEGAVISION Rank: every EPL player, season-level bio + ratings. FC 26
-- ratings from fc26_ratings.py (all leagues, filtered to Premier League);
-- position/ROS% from Fantrax's own player pool.
CREATE TABLE IF NOT EXISTS epl_players (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    player_name TEXT NOT NULL,
    real_club TEXT,
    age INTEGER,
    height_cm INTEGER,
    weight_kg INTEGER,
    fc26_overall REAL,
    fc26_speed REAL,
    fc26_potential REAL,
    fantrax_position TEXT,     -- GK, D, M, F
    fantrax_ros_pct REAL,      -- % of Fantrax leagues rostering this player this week
    updated_at TEXT NOT NULL,
    UNIQUE(player_name, real_club)
);

-- One row per player per gameweek: real score, injury/start status, and
-- fantasyfootballscout.co.uk's team-news read for that week.
CREATE TABLE IF NOT EXISTS player_gameweek (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    player_name TEXT NOT NULL,
    real_club TEXT,
    gameweek INTEGER NOT NULL,
    score REAL,                    -- Fantrax fantasy points, this gameweek
    injury_status TEXT,            -- Fantrax injury icon tooltip, blank if healthy
    started_last_week INTEGER,     -- 0/1, Fantrax Games Started for the prior period
    ffs_start INTEGER,             -- 0/1, in FFS's predicted XI this gameweek
    ffs_positive_mention INTEGER,  -- 0/1, favorable keyword hit in FFS's club news blurb
    ffs_negative_mention INTEGER,  -- 0/1, unfavorable keyword hit (also set for Out/Doubt)
    ffs_doubt INTEGER,             -- 0/1, in FFS's fitness-doubt list
    updated_at TEXT NOT NULL,
    UNIQUE(player_name, real_club, gameweek)
);
"""


def connect():
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(SCHEMA)
    # migrate columns added after a DB already existed on disk
    existing = {r[1] for r in conn.execute("PRAGMA table_info(team_players)")}
    for col, decl in (
        ("fc26_rating", "REAL"), ("fc26_rating_updated_at", "TEXT"),
        ("fc26_potential", "REAL"), ("fc26_value_eur", "REAL"),
        ("fpl_starts", "INTEGER"), ("fpl_goals", "INTEGER"), ("fpl_assists", "INTEGER"),
        ("fpl_minutes", "INTEGER"), ("fpl_tackles", "INTEGER"), ("fpl_cbi", "INTEGER"),
        ("fpl_xg", "REAL"), ("fpl_stats_updated_at", "TEXT"),
    ):
        if col not in existing:
            conn.execute(f"ALTER TABLE team_players ADD COLUMN {col} {decl}")
    conn.commit()
    return conn


if __name__ == "__main__":
    connect().close()
    print(f"DB ready at {DB_PATH}")
