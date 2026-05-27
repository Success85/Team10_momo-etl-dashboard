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
    match = re.search(r"RWF\s*(\d{1,3}(?:,\d{3})*|\d+)", body)
    if match:
        return float(match.group(1).replace(",", ""))
    return 0.0

def extract_fee(body: str) -> float:
    match = re.search(r"Fee(?: was|:)?\s*(\d{1,3}(?:,\d{3})*|\d+)", body)
    if match:
        return float(match.group(1).replace(",", ""))
    match = re.search(r"Fee(?: was|:)?\s*RWF\s*(\d{1,3}(?:,\d{3})*|\d+)", body)
    if match:
        return float(match.group(1).replace(",", ""))
    return 0.0

def extract_balance(body: str) -> float:
    
    match = re.search(r"balance[\s:]+(\d+(?:,\d{3})*)", body, re.IGNORECASE)
    if match:
        return float(match.group(1).replace(",", ""))
    return 0.0

def classify_transaction(body: str) -> str:
    body_lower = body.lower()

    if "you have received" in body_lower:
        return "INCOMING"

    if "bank deposit" in body_lower:
        return "BANK_DEP"

    if "deposit" in body_lower:
        return "CASH_DEP"

    if "airtime" in body_lower or "bundle" in body_lower:
        return "AIRTIME"

    if "*165*s*" in body_lower:
        return "MOB_TRANSFER"

    if "you have transferred" in body_lower:
        return "MOB_TRANSFER"

    if "your transaction to" in body_lower:
        return "MOB_TRANSFER"

    if "your payment of" in body_lower:
        if "to " in body_lower:
            return "MERCHANT_PAY"
        return "UTILITY"

    if "a transaction of" in body_lower and "on your momo account" in body_lower:
        return "MERCHANT_PAY"

    if "transaction with amount" in body_lower and " for " in body_lower:
        return "MERCHANT_PAY"

    if "withdraw" in body_lower:
        return "WITHDRAWAL"

    return "UNKNOWN"




def extract_parties(text):
    sender = "Unknown Sender"
    receiver = "Unknown Receiver"

    result = re.search(r"received .*? from ([A-Za-z\s]+) \(", text)

    if result:
        sender = result.group(1).strip()
        receiver = "Self"
        return {"sender": sender, "receiver": receiver}

    if "A bank deposit" in text:
        sender = "Bank"
        receiver = "Self"
        return {"sender": sender, "receiver": receiver}

    if "deposit" in text.lower() and "receiver" in text.lower():
        sender = "Bank"
        receiver = "Self"
        return {"sender": sender, "receiver": receiver}

    result = re.search(r"transferred .*? to ([A-Za-z\s]+) \(", text)
    if result:
        sender = "Self"
        receiver = result.group(1).strip()
        return {"sender": sender, "receiver": receiver}

    result = re.search(r"payment of .*? to ([A-Za-z\s]+) \d+ has been", text)
    if result:
        sender = "Self"
        receiver = result.group(1).strip()
        return {"sender": sender, "receiver": receiver}

    result = re.search(r"payment of .*? to (.*?) with token", text)
    if result:
        sender = "Self"
        receiver = result.group(1).strip()
        return {"sender": sender, "receiver": receiver}

    result = re.search(r"transaction of .*? by (.*?) on your", text)
    if result:
        sender = "Self"
        raw_receiver = result.group(1).strip()
        receiver = re.sub(r'\s+', ' ', raw_receiver) 
        return {"sender": sender, "receiver": receiver}

    result = re.search(r"transaction with amount .*? for ([A-Za-z0-9\s&'.-]+) with message", text, re.IGNORECASE)
    if result:
        sender = "Self"
        receiver = result.group(1).strip()
        return {"sender": sender, "receiver": receiver}

    result = re.search(r"transaction to ([A-Za-z\s]+) \(", text, re.IGNORECASE)
    if result:
        sender = "Self"
        receiver = result.group(1).strip()
        return {"sender": sender, "receiver": receiver}

    return {
        "sender": sender,
        "receiver": receiver
    }


