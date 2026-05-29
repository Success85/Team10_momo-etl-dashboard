
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



class MoMoHandler(BaseHTTPRequestHandler):
    """
    This class is a waiter. Each time a customer (client) sends
    When a request comes into Python, it allocates an instance of this class to deal with it.

    We define four methods — one for each of the HTTP endpoints::
      This includes the following methods: do_GET, do_POST, do_PUT, or do_DELETE
    """

# This helper method is used to structure and send JSON responses back to the client.
    def send_json_response(self, status_code, data):
        """Send a JSON response with the given status code and data."""

        self.send_response(status_code)

        self.send_header("Content-Type", "application/json")

        self.end_headers()

        self.wfile.write(json.dumps(data, indent=2).encode("utf-8"))

# This helper method is used to read the JSON body from incoming POST and PUT requests, parse it, and return it as a Python dictionary.
    def read_body(self):
        """Read and parse the JSON body from the request."""

        content_length = int(self.headers.get("Content-Length", 0))
        body_bytes = self.rfile.read(content_length)
        body_string = body_bytes.decode("utf-8")
        return json.loads(body_string)
    
# This helper method is used to extract the numeric ID from the URL path for endpoints that include an ID parameter 
    def get_id_from_path(self):
        """
        Extract the numeric ID from the URL path.
        /transactions/5 → returns 5
        /transactions   → returns None
        """
        parts = self.path.strip("/").split("/")

        if len(parts) == 2 and parts[1].isdigit():
            return int(parts[1])

        return None
# This helper method is used to search through the transactions list for a transaction with a specific ID. It returns the transaction dictionary if found or None if no transaction with that ID exists.
    def find_transaction(self, transaction_id):
        """Search the transactions list for one with the given ID."""

        for transaction in transactions:
            if transaction["id"] == transaction_id:
                return transaction

        return None
#    The following methods handle the different HTTP endpoints (GET, POST, PUT, DELETE) and implement the logic for each endpoint.
    def do_GET(self):
        """Handle GET requests - reading/fetching data."""

        if not check_auth(self.headers):
            self.send_json_response(401, {"error": "Unauthorized. Valid credentials required."})
            return  

        if self.path == "/transactions" or self.path == "/transactions/":
            self.send_json_response(200, transactions)

        elif self.path.startswith("/transactions/"):
            transaction_id = self.get_id_from_path()

            if transaction_id is None:
                self.send_json_response(400, {"error": "Invalid transaction ID. Must be a number."})
                return

            transaction = self.find_transaction(transaction_id)

            if transaction is not None:
                self.send_json_response(200, transaction)
            else:
                self.send_json_response(404, {"error": f"Transaction {transaction_id} not found."})

        else:
            self.send_json_response(404, {"error": "Endpoint not found. Try /transactions"})

# The following methods handle the different HTTP endpoints ( PUT, DELETE) and implement the logic for each endpoint.
    def do_PUT(self):
        """Handle PUT requests - updating existing data."""

        if not check_auth(self.headers):
            self.send_json_response(401, {"error": "Unauthorized. Valid credentials required."})
            return

        transaction_id = self.get_id_from_path()

        if transaction_id is None:
            self.send_json_response(400, {"error": "Please provide a transaction ID. Example: /transactions/5"})
            return

        transaction = self.find_transaction(transaction_id)

        if transaction is None:
            self.send_json_response(404, {"error": f"Transaction {transaction_id} not found."})
            return

        try:
            body = self.read_body()

            for key in body:
                if key != "id":
                    transaction[key] = body[key]

            self.send_json_response(200, {
                "message": "Transaction updated successfully.",
                "transaction": transaction
            })

        except Exception as e:
            self.send_json_response(400, {"error": f"Bad request: {str(e)}"})

    def do_DELETE(self):
        """Handle DELETE requests - removing data."""

        if not check_auth(self.headers):
            self.send_json_response(401, {"error": "Unauthorized. Valid credentials required."})
            return

        transaction_id = self.get_id_from_path()

        if transaction_id is None:
            self.send_json_response(400, {"error": "Please provide a transaction ID. Example: /transactions/5"})
            return

        transaction = self.find_transaction(transaction_id)

        if transaction is None:
            self.send_json_response(404, {"error": f"Transaction {transaction_id} not found."})
            return

        transactions.remove(transaction)

        self.send_json_response(200, {
            "message": f"Transaction {transaction_id} deleted successfully."
        })


# TODO: Implement the POST method here(SUCCESS)  
#  This method will handle the creation of new transactions
def do_POST(self):
        """Handle POST requests - creating new transactions."""
 
        if not check_auth(self.headers):
            self.send_json_response(401, {"error": "Unauthorized. Valid credentials required."})
            return
 
        try:
            body = self.read_body()
        except Exception as e:
            self.send_json_response(400, {"error": f"Invalid JSON body: {str(e)}"})
            return

# Validate the incoming data using the validate_transaction function defined in schemas.py
def do_POST(self):
        """Handle POST requests - creating new transactions."""

        if not check_auth(self.headers):
            self.send_json_response(401, {"error": "Unauthorized. Valid credentials required."})
            return

        try:
            body = self.read_body()
        except Exception as e:
            self.send_json_response(400, {"error": f"Invalid JSON body: {str(e)}"})
            return

        errors = validate_transaction(body)
        if errors:
            self.send_json_response(400, {"errors": errors})
            return

        transaction_type = body["transaction_type"]
        amount           = float(body["amount"])
        fee              = float(body.get("fee", 0.0))
        sender           = body["sender"]
        receiver         = body.get("receiver", None)
        balance_after    = body.get("balance_after", None)
        transaction_date = body.get("transaction_date", None)
        status           = body.get("status", "completed")
        notes            = body.get("notes", None)
        internal_tx_id   = body.get("internal_tx_id", None)
        external_tx_id   = body.get("external_tx_id", None)
        raw_body         = body.get("raw_body", None)

#Create a new transaction record in the database using the validated data
def do_POST(self):
        """Handle POST requests - creating new transactions."""

        if not check_auth(self.headers):
            self.send_json_response(401, {"error": "Unauthorized. Valid credentials required."})
            return

        try:
            body = self.read_body()
        except Exception as e:
            self.send_json_response(400, {"error": f"Invalid JSON body: {str(e)}"})
            return

        errors = validate_transaction(body)
        if errors:
            self.send_json_response(400, {"errors": errors})
            return

        transaction_type = body["transaction_type"]
        amount           = float(body["amount"])
        fee              = float(body.get("fee", 0.0))
        sender           = body["sender"]
        receiver         = body.get("receiver", None)
        balance_after    = float(body["balance_after"]) if body.get("balance_after") is not None else None
        transaction_date = body.get("transaction_date", None)
        status           = body.get("status", "completed")
        notes            = body.get("notes", None)
        internal_tx_id   = body.get("internal_tx_id", None)
        external_tx_id   = body.get("external_tx_id", None)
        raw_body         = body.get("raw_body", None)

        try:
            conn   = get_connection()
            cursor = conn.cursor()

            # look up category_id from transaction_type code
            cursor.execute(
                "SELECT category_id FROM transaction_categories WHERE category_code = ?",
                (transaction_type,)
            )
            category_row = cursor.fetchone()
            category_id  = category_row["category_id"] if category_row else None

            cursor.execute("""
                INSERT INTO transactions (
                    transaction_type, internal_tx_id, external_tx_id,
                    category_id, sender, receiver, amount, fee,
                    balance_after, transaction_date, status, notes, raw_body
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                transaction_type, internal_tx_id, external_tx_id,
                category_id, sender, receiver, amount, fee,
                balance_after, transaction_date, status, notes, raw_body
            ))

            conn.commit()
            new_id = cursor.lastrowid
            conn.close()

            self.send_json_response(201, {
                "message": "Transaction created successfully.",
                "transaction": {
                    "id":               new_id,
                    "transaction_type": transaction_type,
                    "internal_tx_id":   internal_tx_id,
                    "external_tx_id":   external_tx_id,
                    "category_id":      category_id,
                    "sender":           sender,
                    "receiver":         receiver,
                    "amount":           amount,
                    "fee":              fee,
                    "balance_after":    balance_after,
                    "transaction_date": transaction_date,
                    "status":           status,
                    "notes":            notes
                }
            })

        except Exception as e:
            self.send_json_response(500, {"error": f"Database error: {str(e)}"})



# TODO: We will have to change the host and port later to make it accessible over the network. For now, it's just for local testing.

# This is the entry point of the application. It sets up and starts the HTTP server.
# Its for  local testing.
if __name__ == "__main__":
    server_address = ("localhost", 8000)

    server = HTTPServer(server_address, MoMoHandler)

    print("=" * 50)
    print("  MoMo API Server is running!")
    print("  Address: http://localhost:8000")
    print("=" * 50)
    print("  Endpoints:")
    print("    GET    /transactions      - List all")
    print("    GET    /transactions/{id} - View one")
    print("    POST   /transactions      - Add new")
    print("    PUT    /transactions/{id} - Update")
    print("    DELETE /transactions/{id} - Remove")
    print("=" * 50)

    server.serve_forever()
