import yaml
import os
import streamlit as st
from core import data_handler, strategy, risk_manager, order_executor, portfolio_manager, backtester, monitor
from core import security

def load_config():
    # Path to config.yaml next to this script
    config_path = os.path.join(os.path.dirname(__file__), "config.yaml")

    if os.path.exists(config_path):
        with open(config_path, "r") as f:
            return yaml.safe_load(f)

    # If config.yaml is missing, try loading from Streamlit secrets
    if hasattr(st, "secrets") and len(st.secrets) > 0:
        # Convert secrets to a regular dictionary
        return dict(st.secrets)

    # If neither method works, raise a descriptive error
    raise FileNotFoundError(
        "No config.yaml found and no Streamlit secrets provided. "
        "Add a config.yaml file locally or define settings in .streamlit/secrets.toml"
    )
    

def init_api_keys(cfg):
    if cfg["security"]["encrypt_keys"]:
        # If keys are in secrets, skip file decryption
        if "API_KEY" in st.secrets and "API_SECRET" in st.secrets:
            cfg["api_key"] = st.secrets["API_KEY"]
            cfg["api_secret"] = st.secrets["API_SECRET"]
            return cfg

        master_key = security.load_master_key(cfg["security"]["key_manager_env_var"])
        with open(cfg["security"]["encrypted_keys_file"], "rb") as f:
            encrypted_data = f.read()
        decrypted = security.decrypt_data(encrypted_data, master_key)
        # parse and inject keys into cfg
    return cfg


def main():
    config = load_config()
    config = init_api_keys(config)

    if config["mode"] == "backtest":
        backtester.run(config)
    elif config["mode"] in ["paper", "live"]:
        data_handler.start_stream(config)
        # event loop for live trading
    else:
        raise ValueError("Invalid mode in config.yaml")


if __name__ == "__main__":
    main()
