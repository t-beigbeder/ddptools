import base64
import secrets

from cryptography.hazmat.primitives.ciphers.aead import AESGCM


def new_token() -> str:
    return secrets.token_bytes(32).hex()


def encrypt(msg: str, token: str) -> bytes:
    btk = bytes.fromhex(token)
    nonce = secrets.token_bytes(12)
    ciphertext = nonce + AESGCM(btk).encrypt(nonce, msg.encode(), b"")
    return base64.b64encode(ciphertext)


def decrypt(b64: bytes, token: str) -> str:
    btk = bytes.fromhex(token)
    ciphertext = base64.b64decode(b64)
    msg = AESGCM(btk).decrypt(ciphertext[:12], ciphertext[12:], b"")
    return msg.decode()
