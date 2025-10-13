# https://cryptography.io/en/latest/hazmat/primitives/asymmetric/ec/
# mempool.space erdekes weboldal
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization
import os
import secrets

USERS = ["alice", "bob", "cecil", "dave"]
KEYS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "keys"))

os.makedirs(KEYS_DIR, exist_ok=True)

for user in USERS:
    private_key = ec.generate_private_key(ec.SECP256K1())
    public_key = private_key.public_key()

    private_value = private_key.private_numbers().private_value
    #print(f"{user} private key value: {private_value}")

    private_key_bytes = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )
    public_key_bytes = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )

    #print(f"{user} private key PEM:\n{private_key_bytes.decode()}")
    #print(f"{user} public key PEM:\n{public_key_bytes.decode()}")

    priv_path = os.path.join(KEYS_DIR, f"{user}_private.pem")
    pub_path = os.path.join(KEYS_DIR, f"{user}_public.pem")

    with open(priv_path, "wb") as f:
        f.write(private_key_bytes)
    try:
        os.chmod(priv_path, 0o600)
    except Exception:
        pass

    with open(pub_path, "wb") as f:
        f.write(public_key_bytes)

print("Demo ECC key pairs generated for:", USERS)
