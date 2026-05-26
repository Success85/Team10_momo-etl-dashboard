import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'momo.db')


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
 
    #Transaction Categories Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transaction_categories (
            category_id   INTEGER PRIMARY KEY AUTOINCREMENT,
            category_name TEXT    NOT NULL UNIQUE,
            category_code TEXT    NOT NULL UNIQUE,
            description   TEXT,
            is_debit      INTEGER NOT NULL DEFAULT 1 CHECK (is_debit IN (0, 1)),
            created_at    TEXT    NOT NULL DEFAULT (datetime('now'))
        )
    """)
 
    # The transactions table 
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            transaction_type TEXT    NOT NULL DEFAULT 'UNKNOWN',
            internal_tx_id   TEXT    UNIQUE,
            external_tx_id   TEXT,
            category_id      INTEGER,
            sender           TEXT,
            receiver         TEXT,
            amount           REAL    NOT NULL CHECK (amount > 0),
            fee              REAL    NOT NULL DEFAULT 0.0 CHECK (fee >= 0),
            balance_after    REAL    CHECK (balance_after IS NULL OR balance_after >= 0),
            transaction_date TEXT,
            status           TEXT    NOT NULL DEFAULT 'completed'
                             CHECK (status IN ('completed', 'pending', 'failed', 'reversed', 'unknown')),
            notes            TEXT,
            raw_body         TEXT,
            created_at       TEXT    NOT NULL DEFAULT (datetime('now')),
            updated_at       TEXT    NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (category_id)
                REFERENCES transaction_categories (category_id)
                ON UPDATE CASCADE ON DELETE SET NULL
        )
    """)
 
    conn.commit()
    conn.close()