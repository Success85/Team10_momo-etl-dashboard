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

    #The sms_messages table to store the raw SMS data for processing

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sms_messages (
        sms_id         INTEGER PRIMARY KEY AUTOINCREMENT,
        protocol       INTEGER NOT NULL DEFAULT 0,
        address        TEXT    NOT NULL,
        date_received  INTEGER NOT NULL,
        date_sent      INTEGER,
        body           TEXT    NOT NULL,
        service_center TEXT,
        read_status    INTEGER NOT NULL DEFAULT 0 CHECK (read_status IN (0, 1)),
        sub_id         INTEGER,
        readable_date  TEXT,
        is_processed   INTEGER NOT NULL DEFAULT 0 CHECK (is_processed IN (0, 1)),
        is_transaction INTEGER NOT NULL DEFAULT 1 CHECK (is_transaction IN (0, 1)),
        created_at     TEXT    NOT NULL DEFAULT (datetime('now'))
    )
    """)

    # The system_logs table to store logs related to the processing of transactions and SMS messages
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS system_logs (
            log_id         INTEGER PRIMARY KEY AUTOINCREMENT,
            transaction_id INTEGER,
            sms_id         INTEGER,
            log_level      TEXT NOT NULL DEFAULT 'INFO'
                           CHECK (log_level IN ('INFO', 'WARNING', 'ERROR', 'DEBUG')),
            event_type     TEXT NOT NULL
                           CHECK (event_type IN ('IMPORT', 'PARSE', 'VALIDATE', 'CRUD', 'SYSTEM', 'API')),
            message        TEXT NOT NULL,
            created_at     TEXT NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (transaction_id) REFERENCES transactions (id) ON DELETE SET NULL,
            FOREIGN KEY (sms_id) REFERENCES sms_messages (sms_id) ON DELETE SET NULL
        )
    """)
 
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_tx_type   ON transactions (transaction_type)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_tx_date   ON transactions (transaction_date)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_tx_status ON transactions (status)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_tx_amount ON transactions (amount)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_sms_proc  ON sms_messages (is_processed)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_log_level ON system_logs  (log_level)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_log_event ON system_logs  (event_type)")
 
    categories = [
       ('Incoming Money',   'INCOMING',     'Money received into wallet from another MoMo user',       0),
       ('Merchant Payment', 'MERCHANT_PAY', 'Payment to a registered MoMo merchant or agent code',    1),
       ('Bank Deposit',     'BANK_DEP',     'Cash deposited from a bank account into MoMo wallet',     0),
       ('Mobile Transfer',  'MOB_TRANSFER', 'Direct transfer sent to another mobile number via MoMo',  1),
       ('Airtime Purchase', 'AIRTIME',      'Airtime or data bundle purchased through MoMo wallet',    1),
       ('Token Payment',    'TOKEN_PAY',    'Payment using a token — covers airtime, WASAC, bundles, packs',   1),
       ('Direct Debit',     'DIRECT_DEBIT', 'Transaction debited by a company directly from the MoMo wallet',  1),
       ('Cash Withdrawal',  'WITHDRAWAL',   'Cash withdrawn from MoMo wallet at an agent',             1),
       ('Utility Payment',  'UTILITY',      'Bill payment for utilities such as electricity or water', 1),
       ('Cash Deposit', 'CASH_DEP',          'Cash deposited into MoMo wallet', 0)

    ]

    cursor.executemany("""
        INSERT OR IGNORE INTO transaction_categories
            (category_name, category_code, description, is_debit)
        VALUES (?, ?, ?, ?)
    """, categories)
 
    conn.commit()
    conn.close()
    print("Database initialised.")
 
 
    if __name__ == '__main__':
        init_db()
   