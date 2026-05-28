API Documentation

Base URL: http://localhost:8000
Authentication: Basic Auth — admin / MOMO123


GET /transactions
Returns all transactions from the database.

Request:
    curl -u admin:MOMO123 http://localhost:8000/transactions

Response (200):
[
  {
    "transaction_id": 1,
    "external_tx_id": "76662021700",
    "category_id": 1,
    "sms_id": 1,
    "amount": "2000.00",
    "fee": "0.00",
    "balance_after": "2000.00",
    "transaction_date": "2024-05-10 16:30:51",
    "status": "completed",
    "notes": null,
    "created_at": "2026-05-16 16:57:06",
    "updated_at": "2026-05-16 16:57:06"
  },
  {
    "transaction_id": 2,
    "external_tx_id": "73214484437",
    "category_id": 2,
    "sms_id": 2,
    "amount": "1000.00",
    "fee": "0.00",
    "balance_after": "1000.00",
    "transaction_date": "2024-05-10 16:31:39",
    "status": "completed",
    "notes": null,
    "created_at": "2026-05-16 16:57:06",
    "updated_at": "2026-05-16 16:57:06"
  }
]

Error Codes:
    401 — Unauthorized (missing or wrong credentials)


GET /transactions/{id}
Returns a single transaction by ID.

Request:
    curl -u admin:MOMO123 http://localhost:8000/transactions/1

Response (200):
{
  "transaction_id": 1,
  "external_tx_id": "76662021700",
  "category_id": 1,
  "sms_id": 1,
  "amount": "2000.00",
  "fee": "0.00",
  "balance_after": "2000.00",
  "transaction_date": "2024-05-10 16:30:51",
  "status": "completed",
  "notes": null,
  "created_at": "2026-05-16 16:57:06",
  "updated_at": "2026-05-16 16:57:06"
}

Error Codes:
    400 — Invalid ID format
    401 — Unauthorized
    404 — Transaction not found


POST /transactions
Creates a new transaction.

Request:
    curl -u admin:MOMO123 -X POST http://localhost:8000/transactions -H "Content-Type: application/json" -d "{\"external_tx_id\": \"NEW_TX_001\", \"category\": \"Incoming Money\", \"amount\": 7500.00, \"fee\": 0.00, \"balance_after\": 12380.00, \"transaction_date\": \"2024-05-13 10:00:00\", \"status\": \"completed\"}"

Request Body:
{
  "external_tx_id": "NEW_TX_001",
  "category": "Incoming Money",
  "amount": 7500.00,
  "fee": 0.00,
  "balance_after": 12380.00,
  "transaction_date": "2024-05-13 10:00:00",
  "status": "completed"
}

Response (201):
{
  "message": "Transaction created successfully.",
  "transaction_id": 11
}

Error Codes:
    400 — Invalid JSON or unknown category
    401 — Unauthorized


PUT /transactions/{id}
Updates an existing transaction. Only send the fields you want to change.

Request:
    curl -u admin:MOMO123 -X PUT http://localhost:8000/transactions/1 -H "Content-Type: application/json" -d "{\"status\": \"reversed\", \"notes\": \"Reversed via API\"}"

Request Body:
{
  "status": "reversed",
  "notes": "Reversed via API"
}

Response (200):
{
  "message": "Transaction 1 updated successfully."
}

Error Codes:
    400 — No valid fields provided
    401 — Unauthorized
    404 — Transaction not found


DELETE /transactions/{id}
Deletes a transaction permanently.

Request:
    curl -u admin:MOMO123 -X DELETE http://localhost:8000/transactions/10

Response (200):
{
  "message": "Transaction 10 deleted successfully."
}

Error Codes:
    400 — Invalid ID format
    401 — Unauthorized
    404 — Transaction not found