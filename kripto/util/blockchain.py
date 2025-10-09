import hashlib
import json
from time import time
from block import Block
from transaction import Transaction


class Blockchain:
    def __init__(self):
        self.chain = []
        self.difficulty = 5
        self.pending_transactions = []
        self.create_genesis_block()

    def create_genesis_block(self):
        genesis_block = Block(0, "0", [])
        self.chain.append(genesis_block)

    def get_last_block(self):
        return self.chain[-1]
    
    def add_transaction(self, sender, receiver, amount, signature):
        transaction = Transaction(sender, receiver, amount, signature)
        self.pending_transactions.append(transaction)

    def mine_block(self):
        if not self.pending_transactions:
            print("No transactions to mine.")
            return

        last_block = self.get_last_block()
        new_block = Block(last_block.number + 1, last_block.calculate_hash(), self.pending_transactions)
        mined_hash = new_block.mine(self.difficulty)
        self.chain.append(new_block)
        self.pending_transactions = []
        print(f"Block {new_block.number} mined with hash: {mined_hash}")

    def validate_chain(self):
        for i in range(1, len(self.chain)):
            current = self.chain[i]
            previous = self.chain[i - 1]

            if current.prev_hash != previous.calculate_hash():
                print(f"Block {current.number} has invalid previous hash.")
                return False

            if not current.validate(self.difficulty):
                print(f"Block {current.number} failed proof of work.")
                return False

        print("Blockchain is valid.")
        return True
    
    def show_block(self, index):
        if 0 <= index < len(self.chain):
            self.chain[index].show_block(only_Header=False)
        else:
            print("Block index out of range.")

    def show_chain(self):
        for block in self.chain:
            block.show_block(only_Header=True)
            print("---------------")

    def show_pending(self):
        if not self.pending_transactions:
            print("No pending transactions.")
            return
        for tx in self.pending_transactions:
            tx.show_transaction()