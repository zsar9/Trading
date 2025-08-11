from cryptography.fernet import Fernet
import os
import streamlit as st


def generate_master_key():
    return Fernet.generate_key()


def encrypt_data(data: bytes, master_key: bytes) -> bytes:
    return Fernet(master_key).encrypt(data)


def decrypt_data(token: bytes, master_key: bytes) -> bytes:
    return Fernet(master_key).decrypt(token)
    

def load_master_key(env_var: str):
    key = os.getenv(env_var)
    if not key and env_var in st.secrets:
        key = st.secrets[env_var]
    if not key:
        raise ValueError(f"Master key not found in environment variable or secrets: {env_var}")
    return key.encode()
