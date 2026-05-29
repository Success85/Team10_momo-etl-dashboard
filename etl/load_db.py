import json
import logging
import sys
from datetime import datetime
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from api.db import get_connection, init_db
from clean_normilize import parse_sms
from parse_xml import load_sms_xml


ACCOUNT_OWNER_NAME = "Account Owner"


def setup_file_logger(log_path: str) -> logging.Logger:
    Path(log_path).parent.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("etl_logger")
    logger.setLevel(logging.INFO)
    logger.propagate = False

    has_file_handler = any(isinstance(handler, logging.FileHandler) for handler in logger.handlers)
    if not has_file_handler:
        file_handler = logging.FileHandler(log_path, encoding="utf-8")
        formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


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


def derive_status(raw_sms: str | None) -> str:
    if not raw_sms:
        return "completed"
    lowered = raw_sms.lower()
    if "reversed" in lowered:
        return "reversed"
    if "failed" in lowered:
        return "failed"
    return "completed"


def ensure_sms_record(db_conn, sms_record: dict) -> int:
    cursor = db_conn.cursor()
    cursor.execute(
        """
        SELECT sms_id FROM sms_messages
        WHERE date_received = ? AND body = ? AND address = ?
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
            read_status, sub_id, readable_date, is_processed, is_transaction
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0, 1)
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


def update_sms_transaction_flag(db_conn, sms_record_id: int, is_transaction: int) -> None:
    cursor = db_conn.cursor()
    cursor.execute(
        "UPDATE sms_messages SET is_transaction = ? WHERE sms_id = ?",
        (is_transaction, sms_record_id),
    )


def fetch_category_id(db_conn, category_code: str) -> int | None:
    cursor = db_conn.cursor()
    cursor.execute(
        "SELECT category_id FROM transaction_categories WHERE category_code = ?",
        (category_code,),
    )
    row = cursor.fetchone()
    if row:
        return row[0]
    return None


def ensure_transaction_record(
    db_conn,
    parsed_sms: dict,
    transaction_category_id: int,
    transaction_timestamp: str,
) -> int | None:
    external_transaction_id = parsed_sms.get("external_tx_id")
    cursor = db_conn.cursor()
    if external_transaction_id:
        cursor.execute(
            "SELECT id FROM transactions WHERE external_tx_id = ?",
            (external_transaction_id,),
        )
        row = cursor.fetchone()
        if row:
            return row[0]

    sender_name = normalize_participant_name(parsed_sms.get("sender"))
    receiver_name = normalize_participant_name(parsed_sms.get("receiver"))

    cursor.execute(
        """
        INSERT INTO transactions (
            transaction_type, internal_tx_id, external_tx_id, category_id, sender, receiver,
            amount, fee, balance_after, transaction_date, status, notes, raw_body
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            parsed_sms.get("category_code") or "UNKNOWN",
            None,
            external_transaction_id,
            transaction_category_id,
            None if is_unknown_participant(sender_name) else sender_name,
            None if is_unknown_participant(receiver_name) else receiver_name,
            parsed_sms.get("amount") or 0.0,
            parsed_sms.get("fee") or 0.0,
            parsed_sms.get("balance_after"),
            transaction_timestamp,
            derive_status(parsed_sms.get("raw_sms")),
            build_transaction_notes(parsed_sms),
            parsed_sms.get("raw_sms"),
        ),
    )
    return cursor.lastrowid


def record_log_event(
    db_conn,
    event_type: str,
    log_message: str,
    log_level: str = "INFO",
    sms_record_id: int | None = None,
    transaction_record_id: int | None = None,
) -> None:
    cursor = db_conn.cursor()
    cursor.execute(
        """
        INSERT INTO system_logs (transaction_id, sms_id, log_level, event_type, message)
        VALUES (?, ?, ?, ?, ?)
        """,
        (transaction_record_id, sms_record_id, log_level, event_type, log_message),
    )


def mark_sms_as_processed(db_conn, sms_record_id: int) -> None:
    cursor = db_conn.cursor()
    cursor.execute(
        "UPDATE sms_messages SET is_processed = 1 WHERE sms_id = ?",
        (sms_record_id,),
    )


def import_sms_to_database(
    xml_path: str,
    output_path: str = "data/processed/dashboard.json",
    batch_size: int = 200,
    log_path: str = "data/logs/etl.log",
    initialize_db: bool = True,
) -> dict:
    logger = setup_file_logger(log_path)
    if initialize_db:
        init_db()

    db_conn = get_connection()
    sms_records = load_sms_xml(xml_path)
    import_summary = {
        "total_sms": len(sms_records),
        "inserted_transactions": 0,
        "skipped_unknown": 0,
        "skipped_invalid": 0,
        "failed": 0,
    }
    parsed_output: list[dict] = []
    batch_summary = {
        "inserted_transactions": 0,
        "skipped_unknown": 0,
        "skipped_invalid": 0,
        "failed": 0,
    }
    processed_in_batch = 0
    if batch_size <= 0:
        batch_size = 1

    try:
        logger.info("XML import started. Total SMS records: %s", len(sms_records))
        record_log_event(db_conn, "IMPORT", f"XML import started. Total SMS records: {len(sms_records)}.")
        db_conn.commit()

        for sms_index, sms_record in enumerate(sms_records, start=1):
            sms_record_id = None
            savepoint_name = f"sms_{sms_index}"
            db_conn.execute(f"SAVEPOINT {savepoint_name}")
            try:
                sms_record_id = ensure_sms_record(db_conn, sms_record)
                parsed_sms = parse_sms(sms_record)
                parsed_output.append(
                    {
                        "sms_id": sms_record_id,
                        "date_received": sms_record.get("date"),
                        "readable_date": sms_record.get("readable_date"),
                        "address": sms_record.get("address"),
                        **parsed_sms,
                    }
                )

                transaction_category_code = parsed_sms.get("category_code") or "UNKNOWN"
                if transaction_category_code == "UNKNOWN":
                    batch_summary["skipped_unknown"] += 1
                    update_sms_transaction_flag(db_conn, sms_record_id, 0)
                    logger.warning("sms_id=%s unrecognized transaction type", sms_record_id)
                    record_log_event(
                        db_conn,
                        "PARSE",
                        "Unrecognized transaction type; left unprocessed.",
                        log_level="WARNING",
                        sms_record_id=sms_record_id,
                    )
                    db_conn.execute(f"RELEASE SAVEPOINT {savepoint_name}")
                    processed_in_batch += 1
                    continue

                transaction_category_id = fetch_category_id(db_conn, transaction_category_code)
                if transaction_category_id is None:
                    batch_summary["skipped_unknown"] += 1
                    update_sms_transaction_flag(db_conn, sms_record_id, 0)
                    logger.warning(
                        "sms_id=%s category code missing in DB: %s",
                        sms_record_id,
                        transaction_category_code,
                    )
                    record_log_event(
                        db_conn,
                        "PARSE",
                        f"Category code {transaction_category_code} missing in DB.",
                        log_level="WARNING",
                        sms_record_id=sms_record_id,
                    )
                    db_conn.execute(f"RELEASE SAVEPOINT {savepoint_name}")
                    processed_in_batch += 1
                    continue

                if (parsed_sms.get("amount") or 0.0) <= 0:
                    batch_summary["skipped_invalid"] += 1
                    update_sms_transaction_flag(db_conn, sms_record_id, 0)
                    logger.warning("sms_id=%s transaction amount missing or invalid", sms_record_id)
                    record_log_event(
                        db_conn,
                        "VALIDATE",
                        "Transaction amount missing or invalid; left unprocessed.",
                        log_level="WARNING",
                        sms_record_id=sms_record_id,
                    )
                    db_conn.execute(f"RELEASE SAVEPOINT {savepoint_name}")
                    processed_in_batch += 1
                    continue

                transaction_timestamp = resolve_transaction_timestamp(sms_record, parsed_sms)
                if not transaction_timestamp:
                    batch_summary["skipped_invalid"] += 1
                    update_sms_transaction_flag(db_conn, sms_record_id, 0)
                    logger.warning("sms_id=%s transaction date missing", sms_record_id)
                    record_log_event(
                        db_conn,
                        "VALIDATE",
                        "Transaction date missing; left unprocessed.",
                        log_level="WARNING",
                        sms_record_id=sms_record_id,
                    )
                    db_conn.execute(f"RELEASE SAVEPOINT {savepoint_name}")
                    processed_in_batch += 1
                    continue

                transaction_record_id = ensure_transaction_record(
                    db_conn,
                    parsed_sms,
                    transaction_category_id,
                    transaction_timestamp,
                )
                if transaction_record_id is None:
                    batch_summary["failed"] += 1
                    update_sms_transaction_flag(db_conn, sms_record_id, 0)
                    logger.error("sms_id=%s failed to insert transaction", sms_record_id)
                    record_log_event(
                        db_conn,
                        "CRUD",
                        "Failed to insert transaction.",
                        log_level="ERROR",
                        sms_record_id=sms_record_id,
                    )
                    db_conn.execute(f"RELEASE SAVEPOINT {savepoint_name}")
                    processed_in_batch += 1
                    continue

                update_sms_transaction_flag(db_conn, sms_record_id, 1)
                mark_sms_as_processed(db_conn, sms_record_id)
                batch_summary["inserted_transactions"] += 1

                record_log_event(
                    db_conn,
                    "CRUD",
                    f"Inserted transaction {parsed_sms.get('external_tx_id') or transaction_record_id}.",
                    sms_record_id=sms_record_id,
                    transaction_record_id=transaction_record_id,
                )
                logger.info(
                    "sms_id=%s inserted transaction %s",
                    sms_record_id,
                    parsed_sms.get("external_tx_id") or transaction_record_id,
                )
                db_conn.execute(f"RELEASE SAVEPOINT {savepoint_name}")
                processed_in_batch += 1
            except Exception as exc:
                db_conn.execute(f"ROLLBACK TO SAVEPOINT {savepoint_name}")
                db_conn.execute(f"RELEASE SAVEPOINT {savepoint_name}")
                batch_summary["failed"] += 1
                try:
                    logger.error("sms_id=%s unhandled error: %s", sms_record_id, exc)
                    record_log_event(
                        db_conn,
                        "SYSTEM",
                        f"Unhandled error while processing SMS: {exc}",
                        log_level="ERROR",
                        sms_record_id=sms_record_id,
                    )
                except Exception:
                    pass
                processed_in_batch += 1

            if processed_in_batch >= batch_size:
                db_conn.commit()
                logger.info(
                    "Committed batch size=%s inserted=%s skipped_unknown=%s skipped_invalid=%s failed=%s",
                    processed_in_batch,
                    batch_summary["inserted_transactions"],
                    batch_summary["skipped_unknown"],
                    batch_summary["skipped_invalid"],
                    batch_summary["failed"],
                )
                for key, value in batch_summary.items():
                    import_summary[key] += value
                batch_summary = {
                    "inserted_transactions": 0,
                    "skipped_unknown": 0,
                    "skipped_invalid": 0,
                    "failed": 0,
                }
                processed_in_batch = 0

        if processed_in_batch:
            db_conn.commit()
            logger.info(
                "Committed final batch size=%s inserted=%s skipped_unknown=%s skipped_invalid=%s failed=%s",
                processed_in_batch,
                batch_summary["inserted_transactions"],
                batch_summary["skipped_unknown"],
                batch_summary["skipped_invalid"],
                batch_summary["failed"],
            )
            for key, value in batch_summary.items():
                import_summary[key] += value

        logger.info("Batch processing complete")
        record_log_event(db_conn, "IMPORT", "Batch processing complete.")
        db_conn.commit()
    finally:
        db_conn.close()

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as file_handle:
        json.dump(parsed_output, file_handle, ensure_ascii=True, indent=2)
    logger.info("Wrote parsed JSON to %s", output_path)
    logger.info(
        "Summary total=%s inserted=%s skipped_unknown=%s skipped_invalid=%s failed=%s",
        import_summary["total_sms"],
        import_summary["inserted_transactions"],
        import_summary["skipped_unknown"],
        import_summary["skipped_invalid"],
        import_summary["failed"],
    )

    return import_summary
