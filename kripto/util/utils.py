import hashlib
from time import time

def hash_transaction_pair(a, b):
    combined = a.calculate_hash() + b.calculate_hash()
    return hashlib.sha256(combined.encode()).hexdigest()

def generate_merkle_root(transactions):
    if not transactions:
        return None

    hashes = [t.calculate_hash() for t in transactions]

    while len(hashes) > 1:
        next_level = []
        for i in range(0, len(hashes), 2):
            if i + 1 < len(hashes):
                combined_hash = hash_transaction_pair(hashes[i], hashes[i + 1])
            else:
                combined_hash = hash_transaction_pair(hashes[i], hashes[i])
            next_level.append(combined_hash)
        hashes = next_level

    return hashes[0]
