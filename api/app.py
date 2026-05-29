from http.server import HTTPServer, BaseHTTPRequestHandler

import json

import base64

from db import get_connection, init_db
    
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

        self.wfile.write(json.dumps(data, indent=2, default=str).encode("utf-8"))

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
        /transactions/5 
        /transactions  
        """
        parts = self.path.strip("/").split("/")

        if len(parts) == 2 and parts[1].isdigit():
            return int(parts[1])

        return None

#    The following methods handle the different HTTP endpoints (GET, POST, PUT, DELETE) and implement the logic for each endpoint.
    def do_GET(self):
        """Handle GET requests - reading/fetching data."""

        if not check_auth(self.headers):
            self.send_json_response(401, {"error": "Unauthorized. Valid credentials required."})
            return  

        if self.path == "/transactions" or self.path == "/transactions/":
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM transactions")
            transactions = [dict(row) for row in cursor.fetchall()]
            cursor.close()
            conn.close()
            self.send_json_response(200, transactions)

        elif self.path.startswith("/transactions/"):
            transaction_id = self.get_id_from_path()

            if transaction_id is None:
                self.send_json_response(400, {"error": "Invalid transaction ID. Must be a number."})
                return

            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM transactions WHERE id = ?", (transaction_id,))
            transaction = cursor.fetchone()
            cursor.close()
            conn.close()
            if transaction is not None:
                self.send_json_response(200, dict(transaction))
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


        try:
            body = self.read_body()

            allowed_fields = {"external_tx_id", "amount", "fee", "transaction_date", "status", "notes", "balance_after"}

            update_field = []
            value = []
            for key in allowed_fields:
                if key in body:
                    update_field.append(f"{key} = ?")
                    value.append(body[key])
            if not update_field:
                self.send_json_response(400, {"error": "No valid fields to update. Allowed fields: external_tx_id, amount, fee, transaction_date, status, notes, balance_after."})
                return
            value.append(transaction_id)
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute(f"UPDATE transactions SET {', '.join(update_field)} WHERE id = ?", tuple(value))
            if cursor.rowcount == 0:
                conn.commit()
                cursor.close()
                conn.close()
                self.send_json_response(404, {"error": f"Transaction {transaction_id} not found."})
                return
            conn.commit()
            cursor.close()
            conn.close()
            self.send_json_response(200, {
                "message": f"Transaction {transaction_id} updated successfully.",
                "updated_fields": update_field
            })

        except Exception as e:
            self.send_json_response(400, {"error": f"Bad request: {str(e)}"})

    def do_DELETE(self):
        """Handle DELETE requests - removing data/transaction."""

        if not check_auth(self.headers):
            self.send_json_response(401, {"error": "Unauthorized. Valid credentials required."})
            return

        transaction_id = self.get_id_from_path()

        if transaction_id is None:
            self.send_json_response(400, {"error": "Please provide a transaction ID. Example: /transactions/5"})
            return

        
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM transactions WHERE id = ?", (transaction_id,))
        if cursor.rowcount == 0:
            cursor.close()
            conn.close()
            conn.close()
            self.send_json_response(404, {"error": f"Transaction {transaction_id} not found."})
            return

        conn.commit()
        cursor.close()
        conn.close()

        self.send_json_response(200, {
            "message": f"Transaction {transaction_id} deleted successfully."
        })


#Create the HTTP server and start listening for requests


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
    init_db()
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