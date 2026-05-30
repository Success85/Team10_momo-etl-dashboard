# MoMo Transactions API Documentation

## Base URL

```txt
http://localhost:8000
```

---

## Authentication

This API uses **Basic Authentication**.

### Credentials

| Username | Password |
| -------- | -------- |
| admin    | MOMO123  |

Example:

```bash
curl -u admin:MOMO123 http://localhost:8000/transactions
```

---

# Endpoints

---

# GET /transactions

Returns all transactions stored in the database.

## Request

```bash
curl -u admin:MOMO123 http://localhost:8000/transactions
```

---

## Successful Response (200 OK)

```json
[
  {
    "id": 1610,
    "transaction_type": "MOB_TRANSFER",
    "internal_tx_id": null,
    "external_tx_id": null,
    "category_id": 4,
    "sender": null,
    "receiver": null,
    "amount": 103000.0,
    "fee": 250.0,
    "balance_after": 737.0,
    "transaction_date": "2025-01-06 13:36:23",
    "status": "completed",
    "notes": "*165*S*103000 RWF transferred to Samuel Carter...",
    "raw_body": "*165*S*103000 RWF transferred to Samuel Carter...",
    "created_at": "2026-05-29 17:07:49",
    "updated_at": "2026-05-29 17:07:49"
  }
]
```

---

## Error Responses

| Status Code | Description                                   |
| ----------- | --------------------------------------------- |
| 401         | Unauthorized (missing or invalid credentials) |


---

# GET /transactions/{id}

Returns a single transaction by ID.

## Request

```bash
curl -u admin:MOMO123 http://localhost:8000/transactions/1610
```

---

## Successful Response (200 OK)

```json
{
  "id": 1610,
  "transaction_type": "MOB_TRANSFER",
  "internal_tx_id": null,
  "external_tx_id": null,
  "category_id": 4,
  "sender": null,
  "receiver": null,
  "amount": 103000.0,
  "fee": 250.0,
  "balance_after": 737.0,
  "transaction_date": "2025-01-06 13:36:23",
  "status": "completed",
  "notes": "*165*S*103000 RWF transferred to Samuel Carter...",
  "raw_body": "*165*S*103000 RWF transferred to Samuel Carter...",
  "created_at": "2026-05-29 17:07:49",
  "updated_at": "2026-05-29 17:07:49"
}
```

---

## Error Responses

| Status Code | Description            |
| ----------- | ---------------------- |
| 400         | Invalid transaction ID |
| 401         | Unauthorized           |
| 404         | Transaction not found  |

---

# POST /transactions

Creates a new transaction.

## Request

```bash
curl -u admin:MOMO123 -X POST http://localhost:8000/transactions \
-H "Content-Type: application/json" \
-d "{\"transaction_type\":\"MERCHANT_PAY\",\"external_tx_id\":\"90877654321\",\"category_id\":2,\"sender\":\"Account Owner\",\"receiver\":\"Jane Smith\",\"amount\":5000.0,\"fee\":0.0,\"balance_after\":45000.0,\"transaction_date\":\"2025-01-09 14:30:00\",\"status\":\"completed\",\"notes\":\"Transaction completed successfully.\",\"raw_body\":\"Transaction completed successfully.\"}"
```

---

## Request Body

**Required fields:** transaction_type, amount, sender

**Optional fields:** external_tx_id, category_id, receiver, fee, balance_after, transaction_date, status, notes, raw_body

```json
{
  "transaction_type": "MERCHANT_PAY",
  "external_tx_id": "90877654321",
  "category_id": 2,
  "sender": "Account Owner",
  "receiver": "Jane Smith",
  "amount": 5000.0,
  "fee": 0.0,
  "balance_after": 45000.0,
  "transaction_date": "2025-01-09 14:30:00",
  "status": "completed",
  "notes": "Transaction completed successfully.",
  "raw_body": "Transaction completed successfully."
}
```

---

## Successful Response (201 Created)

```json
{
  "message": "Transaction created successfully.",
  "transaction_id": 1625
}
```

---

## Error Responses

| Status Code | Description          |
| ----------- | -------------------- |
| 400         | Invalid JSON request |
| 401         | Unauthorized         |

---

# PUT /transactions/{id}

Updates an existing transaction.

Only send the fields you want to modify.

## Request

```bash
curl -u admin:MOMO123 -X PUT http://localhost:8000/transactions/1610 \
-H "Content-Type: application/json" \
-d "{\"status\":\"reversed\",\"notes\":\"Transaction reversed manually.\"}"
```

---

## Request Body

```json
{
  "status": "reversed",
  "notes": "Transaction reversed manually."
}
```

---

## Successful Response (200 OK)

```json
{
  "message": "Transaction 1610 updated successfully."
}
```

---

## Error Responses

| Status Code | Description              |
| ----------- | ------------------------ |
| 400         | No valid fields provided |
| 401         | Unauthorized             |
| 404         | Transaction not found    |

---

# DELETE /transactions/{id}

Deletes a transaction permanently.

## Request

```bash
curl -u admin:MOMO123 -X DELETE http://localhost:8000/transactions/1610
```

---

## Successful Response (200 OK)

```json
{
  "message": "Transaction 1610 deleted successfully."
}
```

---

## Error Responses

| Status Code | Description            |
| ----------- | ---------------------- |
| 400         | Invalid transaction ID |
| 401         | Unauthorized           |
| 404         | Transaction not found  |

---

# Transaction Fields

| Field            | Type        | Description                       |
| ---------------- | ----------- | --------------------------------- |
| id               | Integer     | Unique transaction ID             |
| transaction_type | String      | Type of transaction               |
| internal_tx_id   | String/null | Internal transaction reference    |
| external_tx_id   | String/null | External transaction reference    |
| category_id      | Integer     | Transaction category              |
| sender           | String/null | Sender name                       |
| receiver         | String/null | Receiver name                     |
| amount           | Float       | Transaction amount                |
| fee              | Float       | Transaction fee                   |
| balance_after    | Float       | Account balance after transaction |
| transaction_date | Datetime    | Date and time of transaction      |
| status           | String      | Transaction status                |
| notes            | String      | Additional transaction notes      |
| raw_body         | String      | Original SMS/raw message          |
| created_at       | Datetime    | Record creation timestamp         |
| updated_at       | Datetime    | Record update timestamp           |

---

# Common HTTP Status Codes

| Code | Meaning               |
| ---- | --------------------- |
| 200  | OK                    |
| 201  | Created               |
| 400  | Bad Request           |
| 401  | Unauthorized          |
| 404  | Not Found             |
| 500  | Internal Server Error |

```
```
