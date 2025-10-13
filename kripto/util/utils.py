import hashlib
from time import time


def hash_transaction_pair(a_hash: str, b_hash: str) -> str:
    combined = a_hash + b_hash
    return hashlib.sha256(combined.encode()).hexdigest()


def generate_merkle_root(transactions: list) -> str | None:
    if not transactions:
        return None

    hashes = [t.calculate_hash() for t in transactions]

    while len(hashes) > 1:
        next_level = []
        i = 0
        while i < len(hashes):
            if i + 1 < len(hashes):
                next_level.append(hash_transaction_pair(hashes[i], hashes[i + 1]))
                i += 2
            else:
                # promote odd hash up unchanged
                next_level.append(hashes[i])
                i += 1
        hashes = next_level

    return hashes[0]
