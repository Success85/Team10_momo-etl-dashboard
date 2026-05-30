
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
 
 
def run_comparison():
    print("Loading transactions from database...")
    transactions = load_transactions()
    total = len(transactions)
    print(f"Loaded {total} transactions.\n")
 
    lookup_dict = build_lookup_dict(transactions)
 
    # pick 20 IDs spread across the dataset for a fair comparison
    step = max(1, total // 20)
    target_ids = [transactions[i]["id"] for i in range(0, min(total, step * 20), step)]
 
    print(f"Running search comparison on {len(target_ids)} transaction IDs...\n")
 
    # run each method 100 times for more stable timing
    rounds = 100
    linear_time  = sum(measure_linear_search(transactions, target_ids) for _ in range(rounds)) / rounds
    dict_time    = sum(measure_dictionary_lookup(lookup_dict, target_ids) for _ in range(rounds)) / rounds
 
    print("=" * 55)
    print("  DSA EFFICIENCY COMPARISON — MoMo Transaction Search")
    print("=" * 55)
    print(f"  Dataset size          : {total} transactions")
    print(f"  IDs searched per run  : {len(target_ids)}")
    print(f"  Rounds averaged       : {rounds}")
    print("-" * 55)
    print(f"  Linear Search avg time : {linear_time * 1000:.4f} ms")
    print(f"  Dictionary Lookup time : {dict_time * 1000:.4f} ms")
 
    if dict_time > 0:
        speedup = linear_time / dict_time
        print(f"  Dictionary is {speedup:.1f}x faster than Linear Search")
    print("=" * 55)

    # verify both methods return the same result
    print("VERIFICATION — both methods return identical results:")
    sample_id = target_ids[0]
    result_linear = linear_search(transactions, sample_id)
    result_dict   = dictionary_lookup(lookup_dict, sample_id)
    match = result_linear == result_dict
    print(f"  Sample ID     : {sample_id}")
    print(f"  Results match : {match}")
    if result_linear:
        print(f"  Transaction   : {result_linear['transaction_type']} | "
              f"{result_linear['amount']} RWF | {result_linear['status']}")
 
 
if __name__ == "__main__":
    run_comparison()
 