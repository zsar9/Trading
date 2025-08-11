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
    if cfg.get("security", {}).get("encrypt_keys", False):
        # Safely access nested keys inside key_management
        key_management = cfg["security"].get("key_management", {})
        if key_management.get("use_env_master_key", False):
            env_var_name = key_management.get("env_master_key_var")
            if not env_var_name:
                raise ValueError("Missing 'env_master_key_var' in security.key_management section")
            
            # Load the master key from environment variable
            master_key = security.load_master_key(env_var_name)
            
            encrypted_keys_file = cfg["security"].get("encrypted_keys_file")
            if not encrypted_keys_file:
                raise ValueError("Missing 'encrypted_keys_file' in security section")
            
            with open(encrypted_keys_file, "rb") as f:
                encrypted_data = f.read()
            
            decrypted = security.decrypt_data(encrypted_data, master_key)
            # Here you should parse decrypted data and update cfg accordingly
            # For example, assuming decrypted is a dict of keys:
            # cfg.update(decrypted)
            
            return cfg
        else:
            # If not using env master key, handle other key management options here
            raise NotImplementedError("Only env master key usage is implemented")
    else:
        # If encryption not enabled, load keys from Streamlit secrets or env vars
        import streamlit as st
        cfg["api_key"] = st.secrets.get("API_KEY", "")
        cfg["api_secret"] = st.secrets.get("API_SECRET", "")
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
