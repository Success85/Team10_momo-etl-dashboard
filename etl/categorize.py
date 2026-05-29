def classify_transaction(body: str) -> str:
    body_lower = (body or "").lower()

    if "you have received" in body_lower:
        return "INCOMING"

    if "bank deposit" in body_lower:
        return "BANK_DEP"

    if "deposit" in body_lower:
        return "CASH_DEP"

    if (
        "with token" in body_lower
        or "*162*" in body_lower
        or "bundles and packs" in body_lower
        or "cash power" in body_lower
        or "wasac" in body_lower
    ):
        return "TOKEN_PAY"

    if "transaction of" in body_lower and "on your momo account" in body_lower:
        return "DIRECT_DEBIT"

    if "transaction with amount" in body_lower and " for " in body_lower:
        return "DIRECT_DEBIT"

    if "debit receiver" in body_lower:
        return "DIRECT_DEBIT"

    if "airtime" in body_lower or "bundle" in body_lower:
        return "AIRTIME"

    if "*165*s*" in body_lower:
        return "MOB_TRANSFER"

    if "you have transferred" in body_lower:
        return "MOB_TRANSFER"

    if "your transaction to" in body_lower:
        return "MOB_TRANSFER"

    if "transferred" in body_lower and " to " in body_lower:
        return "MOB_TRANSFER"

    if "your payment of" in body_lower:
        if "to " in body_lower:
            return "MERCHANT_PAY"
        return "UTILITY"

    if "withdraw" in body_lower:
        return "WITHDRAWAL"

    return "UNKNOWN"
