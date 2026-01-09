import sqlite3
from pathlib import Path

DB_PATH = Path("bourse.db")

def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS watchlist (
        symbol TEXT PRIMARY KEY,
        name TEXT,
        min_price REAL,
        max_price REAL,
        active INTEGER DEFAULT 1,
        cooldown_min INTEGER DEFAULT 30,
        last_price REAL,
        last_update TEXT,
        last_alert_type TEXT,
        last_alert_time TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS alerts_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ts TEXT,
        symbol TEXT,
        price REAL,
        alert_type TEXT,
        message TEXT
    )
    """)

    conn.commit()
    conn.close()
