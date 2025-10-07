from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization
import os

USERS = ["alice", "bob", "cecil", "dave"]
KEYS_DIR = os.path.join(os.path.dirname(__file__), "../keys")

os.makedirs(KEYS_DIR, exist_ok=True)

for user in USERS:
    private_key = ec.generate_private_key(ec.SECP256K1())
    public_key = private_key.public_key()

    with open(os.path.join(KEYS_DIR, f"{user}_private.pem"), "wb") as f:
        f.write(private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        ))

    with open(os.path.join(KEYS_DIR, f"{user}_public.pem"), "wb") as f:
        f.write(public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ))

print("Demo ECC key pairs generated for:", USERS)
