from cryptography.fernet import Fernet
import os


def generate_master_key():
    return Fernet.generate_key()


def encrypt_data(data: bytes, master_key: bytes) -> bytes:
    return Fernet(master_key).encrypt(data)


def decrypt_data(token: bytes, master_key: bytes) -> bytes:
    return Fernet(master_key).decrypt(token)


def load_master_key(env_var: str):
    key = os.getenv(env_var)
    if not key:
        raise ValueError(f"Master key not found in environment variable {env_var}")
    return key.encode()