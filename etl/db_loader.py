import pymysql
from datetime import datetime

from sms_parser import parse_sms
from xml_to_json import load_sms_xml


ACCOUNT_OWNER_NAME = "Account Owner"


def open_db_connection(host: str, user: str, password: str, database: str, port: int = 3306) -> pymysql.Connection:
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


def parse_human_datetime(date_text: str | None) -> datetime | None:
    if not date_text:
        return None
    for fmt in ("%d %b %Y %I:%M:%S %p", "%d %B %Y %I:%M:%S %p"):
        try:
            return datetime.strptime(date_text, fmt)
        except ValueError:
            continue
    return None


def resolve_transaction_timestamp(sms_record: dict, parsed_sms: dict) -> str | None:
    parsed_dt = parse_human_datetime(parsed_sms.get("transaction_date"))
    if parsed_dt is None:
        parsed_dt = parse_human_datetime(sms_record.get("readable_date"))
    if parsed_dt is None:
        timestamp_ms = sms_record.get("date") or sms_record.get("date_sent")
        if timestamp_ms:
            parsed_dt = datetime.fromtimestamp(int(timestamp_ms) / 1000)
    if parsed_dt is None:
        return None
    return parsed_dt.strftime("%Y-%m-%d %H:%M:%S")


def normalize_participant_name(raw_name: str | None) -> str | None:
    if not raw_name:
        return None
    cleaned_name = raw_name.strip()
    if cleaned_name.lower() == "self":
        return ACCOUNT_OWNER_NAME
    return cleaned_name


def derive_user_type(full_name: str, role: str, category_code: str) -> str:
    lowered = full_name.lower()
    if full_name == ACCOUNT_OWNER_NAME:
        return "account_holder"
    if "bank" in lowered:
        return "bank"
    if role == "receiver" and category_code in {"MERCHANT_PAY", "AIRTIME", "UTILITY"}:
        return "merchant"
    return "counterparty"


def is_unknown_participant(full_name: str | None) -> bool:
    if not full_name:
        return True
    lowered = full_name.strip().lower()
    return lowered in {"unknown sender", "unknown receiver", "unknown"}


def build_transaction_notes(parsed_sms: dict) -> str | None:
    raw_sms_text = parsed_sms.get("raw_sms")
    if not raw_sms_text:
        return None
    cleaned_note = raw_sms_text.strip()
    if not cleaned_note:
        return None
    return cleaned_note[:500]


def get_or_create_user_id(db_conn: pymysql.Connection, full_name: str, user_kind: str) -> int:
    with db_conn.cursor() as cursor:
        cursor.execute(
            "SELECT user_id FROM users WHERE full_name = %s AND user_type = %s",
            (full_name, user_kind),
        )
        row = cursor.fetchone()
        if row:
            return row[0]
        cursor.execute(
            "INSERT INTO users (full_name, user_type) VALUES (%s, %s)",
            (full_name, user_kind),
        )
        return cursor.lastrowid


def ensure_sms_record(db_conn: pymysql.Connection, sms_record: dict) -> int:
    with db_conn.cursor() as cursor:
        cursor.execute(
            """
            SELECT sms_id FROM sms_messages
            WHERE date_received = %s AND body = %s AND address = %s
            """,
            (sms_record.get("date"), sms_record.get("body"), sms_record.get("address")),
        )
        row = cursor.fetchone()
        if row:
            return row[0]

        cursor.execute(
            """
            INSERT INTO sms_messages (
                protocol, address, date_received, date_sent, body, service_center,
                read_status, sub_id, readable_date, is_processed
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 0)
            """,
            (
                int(sms_record.get("protocol") or 0),
                sms_record.get("address") or "M-Money",
                int(sms_record.get("date") or 0),
                int(sms_record.get("date_sent") or 0) if sms_record.get("date_sent") else None,
                sms_record.get("body") or "",
                sms_record.get("service_center"),
                int(sms_record.get("read") or 0),
                int(sms_record.get("sub_id") or 0) if sms_record.get("sub_id") else None,
                sms_record.get("readable_date"),
            ),
        )
        return cursor.lastrowid


def fetch_category_id(db_conn: pymysql.Connection, category_code: str) -> int | None:
    with db_conn.cursor() as cursor:
        cursor.execute(
            "SELECT category_id FROM transaction_categories WHERE category_code = %s",
            (category_code,),
        )
        row = cursor.fetchone()
        if row:
            return row[0]
        return None


def ensure_transaction_record(
    db_conn: pymysql.Connection,
    parsed_sms: dict,
    sms_record_id: int,
    transaction_category_id: int,
    transaction_timestamp: str,
) -> int | None:
    external_transaction_id = parsed_sms.get("external_tx_id")
    with db_conn.cursor() as cursor:
        if external_transaction_id:
            cursor.execute(
                "SELECT transaction_id FROM transactions WHERE external_tx_id = %s",
                (external_transaction_id,),
            )
            row = cursor.fetchone()
            if row:
                return row[0]
        else:
            cursor.execute(
                "SELECT transaction_id FROM transactions WHERE sms_id = %s",
                (sms_record_id,),
            )
            row = cursor.fetchone()
            if row:
                return row[0]

        cursor.execute(
            """
            INSERT INTO transactions (
                external_tx_id, category_id, sms_id, amount, fee, balance_after,
                transaction_date, status, notes
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, 'completed', %s)
            """,
            (
                external_transaction_id,
                transaction_category_id,
                sms_record_id,
                parsed_sms.get("amount") or 0.0,
                parsed_sms.get("fee") or 0.0,
                parsed_sms.get("balance_after") or 0.0,
                transaction_timestamp,
                build_transaction_notes(parsed_sms),
            ),
        )
        return cursor.lastrowid


def link_transaction_participant(
    db_conn: pymysql.Connection,
    transaction_record_id: int,
    full_name: str,
    user_kind: str,
    participant_role: str,
) -> None:
    participant_user_id = get_or_create_user_id(db_conn, full_name, user_kind)
    with db_conn.cursor() as cursor:
        cursor.execute(
            """
            INSERT IGNORE INTO transaction_participants (transaction_id, user_id, role)
            VALUES (%s, %s, %s)
            """,
            (transaction_record_id, participant_user_id, participant_role),
        )


def record_log_event(
    db_conn: pymysql.Connection,
    event_type: str,
    log_message: str,
    log_level: str = "INFO",
    sms_record_id: int | None = None,
    transaction_record_id: int | None = None,
) -> None:
    with db_conn.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO system_logs (transaction_id, sms_id, log_level, event_type, message)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (transaction_record_id, sms_record_id, log_level, event_type, log_message),
        )


def mark_sms_as_processed(db_conn: pymysql.Connection, sms_record_id: int) -> None:
    with db_conn.cursor() as cursor:
        cursor.execute(
            "UPDATE sms_messages SET is_processed = 1 WHERE sms_id = %s",
            (sms_record_id,),
        )


def import_sms_to_database(
    xml_path: str,
    host: str,
    user: str,
    password: str,
    database: str,
    port: int = 3306,
) -> dict:
    db_conn = open_db_connection(host=host, user=user, password=password, database=database, port=port)
    sms_records = load_sms_xml(xml_path)
    import_summary = {
        "total_sms": len(sms_records),
        "inserted_transactions": 0,
        "skipped_unknown": 0,
        "skipped_invalid": 0,
        "failed": 0,
    }

    try:
        record_log_event(db_conn, "IMPORT", f"XML import started. Total SMS records: {len(sms_records)}.")
        db_conn.commit()

        for sms_record in sms_records:
            sms_record_id = None
            try:
                sms_record_id = ensure_sms_record(db_conn, sms_record)
                parsed_sms = parse_sms(sms_record)

                transaction_category_code = parsed_sms.get("category_code") or "UNKNOWN"
                if transaction_category_code == "UNKNOWN":
                    import_summary["skipped_unknown"] += 1
                    record_log_event(
                        db_conn,
                        "PARSE",
                        "Unrecognized transaction type; left unprocessed.",
                        log_level="WARNING",
                        sms_record_id=sms_record_id,
                    )
                    db_conn.commit()
                    continue

                transaction_category_id = fetch_category_id(db_conn, transaction_category_code)
                if transaction_category_id is None:
                    import_summary["skipped_unknown"] += 1
                    record_log_event(
                        db_conn,
                        "PARSE",
                        f"Category code {transaction_category_code} missing in DB.",
                        log_level="WARNING",
                        sms_record_id=sms_record_id,
                    )
                    db_conn.commit()
                    continue

                if (parsed_sms.get("amount") or 0.0) <= 0:
                    import_summary["skipped_invalid"] += 1
                    record_log_event(
                        db_conn,
                        "VALIDATE",
                        "Transaction amount missing or invalid; left unprocessed.",
                        log_level="WARNING",
                        sms_record_id=sms_record_id,
                    )
                    db_conn.commit()
                    continue

                transaction_timestamp = resolve_transaction_timestamp(sms_record, parsed_sms)
                if not transaction_timestamp:
                    import_summary["skipped_invalid"] += 1
                    record_log_event(
                        db_conn,
                        "VALIDATE",
                        "Transaction date missing; left unprocessed.",
                        log_level="WARNING",
                        sms_record_id=sms_record_id,
                    )
                    db_conn.commit()
                    continue

                transaction_record_id = ensure_transaction_record(
                    db_conn,
                    parsed_sms,
                    sms_record_id,
                    transaction_category_id,
                    transaction_timestamp,
                )
                if transaction_record_id is None:
                    import_summary["failed"] += 1
                    record_log_event(
                        db_conn,
                        "CRUD",
                        "Failed to insert transaction.",
                        log_level="ERROR",
                        sms_record_id=sms_record_id,
                    )
                    db_conn.commit()
                    continue

                sender_name = normalize_participant_name(parsed_sms.get("sender"))
                receiver_name = normalize_participant_name(parsed_sms.get("receiver"))

                if sender_name and not is_unknown_participant(sender_name):
                    sender_type = derive_user_type(sender_name, "sender", transaction_category_code)
                    link_transaction_participant(
                        db_conn,
                        transaction_record_id,
                        sender_name,
                        sender_type,
                        "sender",
                    )

                if receiver_name and not is_unknown_participant(receiver_name):
                    receiver_type = derive_user_type(receiver_name, "receiver", transaction_category_code)
                    link_transaction_participant(
                        db_conn,
                        transaction_record_id,
                        receiver_name,
                        receiver_type,
                        "receiver",
                    )

                mark_sms_as_processed(db_conn, sms_record_id)
                import_summary["inserted_transactions"] += 1

                record_log_event(
                    db_conn,
                    "CRUD",
                    f"Inserted transaction {parsed_sms.get('external_tx_id') or transaction_record_id}.",
                    sms_record_id=sms_record_id,
                    transaction_record_id=transaction_record_id,
                )
                db_conn.commit()
            except Exception as exc:
                db_conn.rollback()
                import_summary["failed"] += 1
                try:
                    record_log_event(
                        db_conn,
                        "SYSTEM",
                        f"Unhandled error while processing SMS: {exc}",
                        log_level="ERROR",
                        sms_record_id=sms_record_id,
                    )
                    db_conn.commit()
                except Exception:
                    db_conn.rollback()

        record_log_event(db_conn, "IMPORT", "Batch processing complete.")
        db_conn.commit()
    finally:
        db_conn.close()

    return import_summary
