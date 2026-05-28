# Define valid statuses and transaction types for the API

VALID_STATUSES = ["completed", "pending", "failed", "reversed", "unknown"]
 
#Transaction type
VALID_TRANSACTION_TYPES = [
    "INCOMING",
    "MERCHANT_PAY",
    "BANK_DEP",
    "MOB_TRANSFER",
    "TOKEN_PAY",
    "DIRECT_DEBIT",
    "UNKNOWN"
]
 
#Required fields for creating a transaction
REQUIRED_FIELDS = ["amount", "transaction_type", "sender"]

VALID_STATUSES = ["completed", "pending", "failed", "reversed", "unknown"]

# Valid transaction types
VALID_TRANSACTION_TYPES = [
    "INCOMING",
    "MERCHANT_PAY",
    "BANK_DEP",
    "MOB_TRANSFER",
    "TOKEN_PAY",
    "DIRECT_DEBIT",
    "UNKNOWN"
]

# Required fields for creating a transaction
REQUIRED_FIELDS = ["amount", "transaction_type", "sender"]

# Function to validate transaction data before creating or updating a transaction
def validate_transaction(data):
    errors = []

    # check all required fields are present
    for field in REQUIRED_FIELDS:
        if field not in data or data[field] is None or str(data[field]).strip() == "":
            errors.append(f"'{field}' is required and cannot be empty")

    # validate amount
    if "amount" in data:
        try:
            if float(data["amount"]) <= 0:
                errors.append("'amount' must be greater than zero")
        except (ValueError, TypeError):
            errors.append("'amount' must be a valid number")

    # validate fee if provided
    if "fee" in data:
        try:
            if float(data["fee"]) < 0:
                errors.append("'fee' cannot be negative")
        except (ValueError, TypeError):
            errors.append("'fee' must be a valid number")

    # validate balance_after if provided
    if "balance_after" in data and data["balance_after"] is not None:
        try:
            if float(data["balance_after"]) < 0:
                errors.append("'balance_after' cannot be negative")
        except (ValueError, TypeError):
            errors.append("'balance_after' must be a valid number")

    # validate status if provided
    if "status" in data and data["status"] not in VALID_STATUSES:
        errors.append(f"'status' must be one of: {', '.join(VALID_STATUSES)}")

    # validate transaction_type if provided
    if "transaction_type" in data and data["transaction_type"] not in VALID_TRANSACTION_TYPES:
        errors.append(f"'transaction_type' must be one of: {', '.join(VALID_TRANSACTION_TYPES)}")

    return errors