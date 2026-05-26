import pymysql
from datetime import datetime

from sms_parser import parse_sms
from xml_to_json import load_sms_xml


ACCOUNT_OWNER_NAME = "Account Owner"


def get_connection(host: str, user: str, password: str, database: str, port: int = 3306) -> pymysql.Connection:
    return pymysql.connect(
        host=host,
        user=user,
        password=password,
        database=database,
        port=port,
        autocommit=False,
        charset="utf8mb4",
        cursorclass=pymysql.cursors.Cursor,
    )


def parse_readable_date(date_str: str | None) -> datetime | None:
    if not date_str:
        return None
    for fmt in ("%d %b %Y %I:%M:%S %p", "%d %B %Y %I:%M:%S %p"):
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    return None


def get_transaction_date(sms: dict, parsed: dict) -> str | None:
    dt = parse_readable_date(parsed.get("transaction_date"))
    if dt is None:
        dt = parse_readable_date(sms.get("readable_date"))
    if dt is None:
        timestamp_ms = sms.get("date") or sms.get("date_sent")
        if timestamp_ms:
            dt = datetime.fromtimestamp(int(timestamp_ms) / 1000)
    if dt is None:
        return None
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def get_user_name(name: str | None) -> str | None:
    if not name:
        return None
    trimmed = name.strip()
    if trimmed.lower() == "self":
        return ACCOUNT_OWNER_NAME
    return trimmed


def get_user_type(name: str, role: str, category_code: str) -> str:
    lowered = name.lower()
    if name == ACCOUNT_OWNER_NAME:
        return "account_holder"
    if "bank" in lowered:
        return "bank"
    if role == "receiver" and category_code in {"MERCHANT_PAY", "AIRTIME", "UTILITY"}:
        return "merchant"
    return "counterparty"


def get_notes(parsed: dict) -> str | None:
    raw_sms = parsed.get("raw_sms")
    if not raw_sms:
        return None
    trimmed = raw_sms.strip()
    if not trimmed:
        return None
    return trimmed[:500]


def fetch_or_create_user(conn: pymysql.Connection, full_name: str, user_type: str) -> int:
    with conn.cursor() as cursor:
        cursor.execute(
            "SELECT user_id FROM users WHERE full_name = %s AND user_type = %s",
            (full_name, user_type),
        )
        row = cursor.fetchone()
        if row:
            return row[0]
        cursor.execute(
            "INSERT INTO users (full_name, user_type) VALUES (%s, %s)",
            (full_name, user_type),
        )
        return cursor.lastrowid


