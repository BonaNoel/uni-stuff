import hashlib
import json
import os
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization

KEYS_DIR = os.path.join(os.path.dirname(__file__), "../keys")
    
class Transaction:
    def __init__(self, sender, receiver, amount):
        self.sender = sender
        self.receiver = receiver
        self.amount = amount
        self.signature = self.sign_transaction()

    def calculate_hash(self):
        transaction_dict = {
            "sender": self.sender,
            "receiver": self.receiver,
            "amount": self.amount,
        }
        transaction_string = json.dumps(transaction_dict, sort_keys=True)
        return hashlib.sha256(transaction_string.encode()).hexdigest()

    def sign_transaction(self):
        private_key = serialization.load_pem_private_key(
            open(f"{KEYS_DIR}/{self.sender}_private.pem", "rb").read(),
            password=None,
        )
        signature = private_key.sign(
            self.calculate_hash().encode(),
            ec.ECDSA(hashes.SHA256())
        )
        return signature

    def verify_signature(self):
        public_key = serialization.load_pem_public_key(
            open(f"{KEYS_DIR}/{self.sender}_public.pem", "rb").read()
        )
        try:
            public_key.verify(
                self.signature,
                self.calculate_hash().encode(),
                ec.ECDSA(hashes.SHA256())
            )
            return True
        except Exception as e:
            print(f"Signature verification failed: {e}")
            return False
        
    def show_transaction(self):
        print("Transaction Details:")
        print(f"  Sender: {self.sender}")
        print(f"  Receiver: {self.receiver}")
        print(f"  Amount: {self.amount}")
        print(f"  Signature: {self.signature.hex()}")
        print(f"  Transaction Hash: {self.calculate_hash()}")
        print("  " + "-" * 40)
