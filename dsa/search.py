import sys
import os
import time
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


def measure_linear_search(transactions, target_ids):
    """Run linear search for each target ID and return total time in seconds."""
    start = time.perf_counter()
    for target_id in target_ids:
        linear_search(transactions, target_id)
    end = time.perf_counter()
    return end - start


def measure_dictionary_lookup(lookup_dict, target_ids):
    """Run dictionary lookup for each target ID and return total time in seconds."""
    start = time.perf_counter()
    for target_id in target_ids:
        dictionary_lookup(lookup_dict, target_id)
    end = time.perf_counter()
    return end - start


if __name__ == "__main__":
    run_comparison()