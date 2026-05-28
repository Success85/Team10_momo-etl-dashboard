# Define valid statuses and transaction types for the API

VALID_STATUSES = ["completed", "pending", "failed", "reversed", "unknown"]
 
VALID_TRANSACTION_TYPES = [
    "INCOMING",
    "MERCHANT_PAY",
    "BANK_DEP",
    "MOB_TRANSFER",
    "TOKEN_PAY",
    "DIRECT_DEBIT",
    "UNKNOWN"
]
 
REQUIRED_FIELDS = ["amount", "transaction_type", "sender"]
 