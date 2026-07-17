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
    fc26_rating_updated_at TEXT,
    updated_at TEXT NOT NULL,
    UNIQUE(team_code, player_name_raw)
);

CREATE TABLE IF NOT EXISTS team_week_financials (
    team_code TEXT NOT NULL REFERENCES teams(code),
    week INTEGER NOT NULL,
    salary_cost REAL NOT NULL,
    basis TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    PRIMARY KEY (team_code, week)
);
"""


def connect():
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(SCHEMA)
    # migrate columns added after a DB already existed on disk
    existing = {r[1] for r in conn.execute("PRAGMA table_info(team_players)")}
    for col, decl in (("fc26_rating", "REAL"), ("fc26_rating_updated_at", "TEXT")):
        if col not in existing:
            conn.execute(f"ALTER TABLE team_players ADD COLUMN {col} {decl}")
    conn.commit()
    return conn


if __name__ == "__main__":
    connect().close()
    print(f"DB ready at {DB_PATH}")
