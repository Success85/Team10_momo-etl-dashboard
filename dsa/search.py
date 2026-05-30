import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'api'))

from db import get_connection


def load_transactions():
    """Load all transactions from the database into a list."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, transaction_type, sender, receiver, amount, status FROM transactions")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def build_lookup_dict(transactions):
    """
    Build a dictionary mapping transaction ID to transaction record.
    This is a one-time O(n) setup cost.
    """
    return {transaction["id"]: transaction for transaction in transactions}


def linear_search(transactions, target_id):
    """
    Linear Search — scan through every transaction one by one
    until we find the one with the matching ID.

    Time complexity: O(n) — worst case checks every record.
    """
    for transaction in transactions:
        if transaction["id"] == target_id:
            return transaction
    return None


def dictionary_lookup(lookup_dict, target_id):
    """
    Dictionary Lookup — use the transaction ID as a key
    to jump directly to the record.

    Time complexity: O(1) — direct key access, no scanning.
    """
    return lookup_dict.get(target_id, None)