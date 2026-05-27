
from http.server import HTTPServer, BaseHTTPRequestHandler

import json

import base64

# TODO: Will replace this with a real database later. For now, it's just a list of dictionaries for testing.
transactions = [
    {
        "id": 1,
        "external_tx_id": "76662021700",
        "category": "Incoming Money",
        "amount": 2000.00,
        "fee": 0.00,
        "balance_after": 2000.00,
        "transaction_date": "2024-05-10 16:30:51",
        "status": "completed",
        "sender": "Jane Smith",
        "receiver": "Account Owner"
    },
    {
        "id": 2,
        "external_tx_id": "73214484437",
        "category": "Merchant Payment",
        "amount": 1000.00,
        "fee": 0.00,
        "balance_after": 1000.00,
        "transaction_date": "2024-05-10 16:31:39",
        "status": "completed",
        "sender": "Account Owner",
        "receiver": "Jane Smith"
    },
    {
        "id": 3,
        "external_tx_id": "BANK_DEP_001",
        "category": "Bank Deposit",
        "amount": 40000.00,
        "fee": 0.00,
        "balance_after": 40400.00,
        "transaction_date": "2024-05-11 18:43:49",
        "status": "completed",
        "sender": "MTN Bank",
        "receiver": "Account Owner"
    },
    {
        "id": 4,
        "external_tx_id": "17818959211",
        "category": "Merchant Payment",
        "amount": 2000.00,
        "fee": 0.00,
        "balance_after": 38400.00,
        "transaction_date": "2024-05-11 18:48:42",
        "status": "completed",
        "sender": "Account Owner",
        "receiver": "Samuel Carter"
    },
    {
        "id": 5,
        "external_tx_id": "MOB_TRF_001",
        "category": "Mobile Transfer",
        "amount": 10000.00,
        "fee": 100.00,
        "balance_after": 28300.00,
        "transaction_date": "2024-05-11 20:34:47",
        "status": "completed",
        "sender": "Account Owner",
        "receiver": "Samuel Carter"
    },
    {
        "id": 6,
        "external_tx_id": "13913173274",
        "category": "Airtime Purchase",
        "amount": 2000.00,
        "fee": 0.00,
        "balance_after": 25280.00,
        "transaction_date": "2024-05-12 11:41:28",
        "status": "completed",
        "sender": "Account Owner",
        "receiver": "MTN Airtime"
    },
    {
        "id": 7,
        "external_tx_id": "45434420466",
        "category": "Merchant Payment",
        "amount": 10900.00,
        "fee": 0.00,
        "balance_after": 14380.00,
        "transaction_date": "2024-05-12 13:26:13",
        "status": "completed",
        "sender": "Account Owner",
        "receiver": "Jane Smith"
    },
    {
        "id": 8,
        "external_tx_id": "82113964658",
        "category": "Merchant Payment",
        "amount": 3500.00,
        "fee": 0.00,
        "balance_after": 10880.00,
        "transaction_date": "2024-05-12 13:34:25",
        "status": "completed",
        "sender": "Account Owner",
        "receiver": "Alex Doe"
    },
    {
        "id": 9,
        "external_tx_id": "26614842768",
        "category": "Merchant Payment",
        "amount": 1000.00,
        "fee": 0.00,
        "balance_after": 9880.00,
        "transaction_date": "2024-05-12 17:58:15",
        "status": "completed",
        "sender": "Account Owner",
        "receiver": "Robert Brown"
    },
    {
        "id": 10,
        "external_tx_id": "70497610538",
        "category": "Merchant Payment",
        "amount": 5000.00,
        "fee": 0.00,
        "balance_after": 4880.00,
        "transaction_date": "2024-05-12 18:08:58",
        "status": "completed",
        "sender": "Account Owner",
        "receiver": "Linda Green"
    }
]

next_id = 11


# TODO: For simplicity, we're hardcoding the username and password here. We will have to create a dotenv file later to store this kind of sensitive information securely.
#Also we will have to change the credentials to something more secure.
USERNAME = "admin"
PASSWORD = "MOMO123"


# This function checks the Authorization header for valid credentials.
def check_auth(headers):
    """
    This function is the security guard which will be used to restrict access to endpoints.
    It takes the request headers, looks for the Authorization header,
    decodes the base64 credentials, and checks if they match.

    Returns True if the credentials are valid and False if they aren't.
    """

    auth_header = headers.get("Authorization")

    if auth_header is None:
        return False


    try:
        auth_type, auth_value = auth_header.split(" ", 1)

        if auth_type != "Basic":
            return False

        decoded = base64.b64decode(auth_value).decode("utf-8")

        username, password = decoded.split(":", 1)

        if username == USERNAME and password == PASSWORD:
            return True
        else:
            return False

    except Exception:
        return False

