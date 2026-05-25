import re

def parse_sms(sms):
    body = sms.get("body", "")

    result = {
        "external_tx_id": extract_tx_id(body),
        "amount": extract_amount(body),
        "fee": extract_fee(body),
        "balance_after": extract_balance(body),
        "transaction_date": sms.get("readable_date"),
        "sender": None,
        "receiver": None,
        "category_code": classify_transaction(body),
        "raw_sms": body
    }

    result.update(extract_parties(body))

    return result

def extract_tx_id(body: str):
    match = re.search(r"TxId[: ]\s*(\d+)", body)
    if match:
        return match.group(1)

    match = re.search(r"Financial Transaction Id[: ]\s*(\d+)", body)
    if match:
        return match.group(1)

    return None

def extract_amount(body: str) -> float:
    match = re.search(r"(\d{1,3}(?:,\d{3})*|\d+)\s*RWF", body)
    if match:
        return float(match.group(1).replace(",", ""))
    return 0.0

def extract_fee(body: str) -> float:
    match = re.search(r"Fee(?: was|:)?\s*(\d{1,3}(?:,\d{3})*|\d+)", body)
    if match:
        return float(match.group(1).replace(",", ""))
    return 0.0

def extract_balance(body: str) -> float:
    
    match = re.search(r"balance[\s:]+(\d+(?:,\d{3})*)", body, re.IGNORECASE)
    if match:
        return float(match.group(1).replace(",", ""))
    return 0.0



