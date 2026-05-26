<<<<<<< HEAD
from config import BATCH_SIZE, INITIALIZE_DB, LOG_PATH, OUTPUT_PATH, XML_PATH
from load_db import import_sms_to_database


def main() -> None:
    summary = import_sms_to_database(
        xml_path=XML_PATH,
        output_path=OUTPUT_PATH,
        batch_size=BATCH_SIZE,
        log_path=LOG_PATH,
        initialize_db=INITIALIZE_DB,
    )
    print(summary)


if __name__ == "__main__":
    main()
=======
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'momo.db')


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn
>>>>>>> aa31213 (set up database connection and path)
