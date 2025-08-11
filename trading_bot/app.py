import streamlit as st
import threading
import time
import yaml
import os
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

"""
Trading Bot Control Panel
=========================
A Streamlit app for local desktop use to control and monitor your trading bot.

Features:
- Dashboard: real-time price charts, positions, portfolio allocation, recent orders.
- Strategies: edit params, enable/disable, run backtest with metrics and charts.
- Portfolio: holdings, risk metrics, correlation heatmap, manual rebalance (mock).
- Logs: real-time log streaming with filtering and CSV export.
- Settings: interactive config editor, secure API keys input, save/apply.

Run locally:
pip install streamlit plotly pyyaml pandas
streamlit run app.py

Replace mock backend functions with your real trading bot data and control logic.

Integration notes:
- Replace get_active_symbols, get_real_time_prices, get_current_positions, get_orders,
  get_strategies, run_backtest, get_logs, load_config, save_config with calls to your backend.
- For live streaming, integrate your data handler or broker websocket events.
- For backtests, wire to core.backtester.run with in-memory outputs.
"""

# === MOCK/PLACEHOLDER DATA AND FUNCTIONS ===
# Replace these with your actual trading bot imports and methods

def get_active_symbols():
    return ["AAPL", "TSLA", "GOOG"]


def get_real_time_prices(symbol):
    import random
    # Mock price stream
    base = {"AAPL": 150, "TSLA": 700, "GOOG": 2800}
    return base[symbol] + random.uniform(-1, 1)


def get_current_positions():
    return [
        {"symbol": "AAPL", "quantity": 10, "avg_price": 148, "current_price": 150.5, "unrealized_pnl": 25},
        {"symbol": "TSLA", "quantity": 5, "avg_price": 690, "current_price": 700, "unrealized_pnl": 50},
    ]


def get_orders():
    return [
        {"id": 1, "symbol": "AAPL", "side": "buy", "qty": 10, "status": "filled"},
        {"id": 2, "symbol": "TSLA", "side": "sell", "qty": 2, "status": "pending"},
    ]


def get_strategies():
    # Normally load from config or backend
    return {
        "EMA Crossover": {"fast_period": 12, "slow_period": 26, "enabled": True},
        "RSI Mean Reversion": {"rsi_period": 14, "threshold_low": 30, "threshold_high": 70, "enabled": False},
    }


def run_backtest(strategy_name, params):
    # Mock backtest result
    import numpy as np
    import pandas as pd
    np.random.seed(42)
    returns = np.random.normal(0.001, 0.02, 252)
    equity_curve = (1 + returns).cumprod()
    metrics = {
        "Total Return": f"{equity_curve[-1]-1:.2%}",
        "Max Drawdown": "-10.5%",
        "Sharpe Ratio": "1.25",
    }
    df = pd.DataFrame({"Date": pd.date_range("2023-01-01", periods=252), "Equity": equity_curve})
    return metrics, df


def get_logs():
    # Dummy logs
    return [
        {"time": "12:00:01", "level": "INFO", "message": "Bot started."},
        {"time": "12:00:05", "level": "WARNING", "message": "Order delayed."},
        {"time": "12:01:00", "level": "ERROR", "message": "API connection lost."},
    ]


def load_config():
    config_path = Path("config.yaml")
    if config_path.exists():
        with open(config_path, "r") as f:
            return yaml.safe_load(f)
    else:
        # Default config
        return {
            "mode": "paper",
            "strategies": {
                "EMA Crossover": {"enabled": True, "fast_period": 12, "slow_period": 26},
                "RSI Mean Reversion": {"enabled": False, "rsi_period": 14, "threshold_low": 30, "threshold_high": 70},
            },
            "risk": {}
        }


def save_config(config):
    with open("config.yaml", "w") as f:
        yaml.dump(config, f)


# === END MOCK FUNCTIONS ===

# App State Initialization
if "bot_running" not in st.session_state:
    st.session_state.bot_running = False

if "logs" not in st.session_state:
    st.session_state.logs = get_logs()

if "config" not in st.session_state:
    st.session_state.config = load_config()


# --- Helper functions ---

def stream_prices(symbol, price_container):
    # Dummy price stream updating every second
    while st.session_state.bot_running and st.session_state.get("stream_symbol") == symbol:
        price = get_real_time_prices(symbol)
        price_container.append(price)
        if len(price_container) > 300:
            price_container.pop(0)
        time.sleep(1)


def append_log(level, message):
    timestamp = time.strftime("%H:%M:%S")
    st.session_state.logs.append({"time": timestamp, "level": level, "message": message})
    # Limit logs size
    if len(st.session_state.logs) > 2000:
        st.session_state.logs = st.session_state.logs[-2000:]


# --- UI ---

st.set_page_config(page_title="Trading Bot Control Panel", layout="wide")

st.sidebar.title("Trading Bot")

page = st.sidebar.radio("Navigate", ["Dashboard", "Strategies", "Portfolio", "Logs", "Settings"], help="Navigate the control panel")

# --- DASHBOARD ---
if page == "Dashboard":
    st.title("📊 Dashboard")

    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("Live Price Charts")
        symbols = get_active_symbols()
        selected_symbol = st.selectbox("Select symbol", symbols, help="Pick a symbol to stream its price")
        price_key = f"price_data_{selected_symbol}"
        price_data = st.session_state.get(price_key, [])
        if not price_data:
            price_data = [get_real_time_prices(selected_symbol)]
            st.session_state[price_key] = price_data

        # Start price streaming thread if not running or different symbol
        should_start = (
            "price_thread" not in st.session_state
            or not st.session_state.price_thread.is_alive()
            or st.session_state.get("stream_symbol") != selected_symbol
        )

        if should_start:
            st.session_state.bot_running = True
            st.session_state.stream_symbol = selected_symbol
            st.session_state.price_thread = threading.Thread(
                target=stream_prices,
                args=(selected_symbol, price_data),
                daemon=True,
            )
            st.session_state.price_thread.start()

        fig = go.Figure()
        fig.add_trace(go.Scatter(y=price_data, mode="lines+markers", name=selected_symbol))
        fig.update_layout(height=350, margin=dict(l=0, r=0, t=20, b=0), template="plotly_white")
        st.plotly_chart(fig, use_container_width=True)

        st.markdown("---")
        st.subheader("Recent Orders")
        orders = get_orders()
        df_orders = pd.DataFrame(orders)
        st.dataframe(df_orders, use_container_width=True)

    with col2:
        st.subheader("Current Positions")
        positions = get_current_positions()
        df_positions = pd.DataFrame(positions)
        st.dataframe(df_positions, use_container_width=True)

        st.subheader("Portfolio Allocation")
        if not df_positions.empty:
            pie_fig = px.pie(df_positions, names="symbol", values="quantity", title="Positions Allocation")
            pie_fig.update_layout(margin=dict(l=0, r=0, t=30, b=0))
            st.plotly_chart(pie_fig, use_container_width=True)
        else:
            st.info("No positions currently.")

        st.markdown("---")
        st.subheader("Bot Controls")
        status = "Running" if st.session_state.bot_running else "Stopped"
        st.write(f"**Bot Status:** {status}")

        c1, c2 = st.columns(2)
        with c1:
            if st.session_state.bot_running:
                if st.button("Stop Bot", help="Stop streaming and trading loop"):
                    st.session_state.bot_running = False
                    append_log("INFO", "Bot stopped by user.")
            else:
                if st.button("Start Bot", help="Start streaming and trading loop"):
                    st.session_state.bot_running = True
                    append_log("INFO", "Bot started by user.")
        with c2:
            st.write(f"**Mode:** {st.session_state.config.get('mode', 'paper')}")

# --- STRATEGIES ---
elif page == "Strategies":
    st.title("⚙️ Strategies")

    strategies = get_strategies()
    strategy_names = list(strategies.keys())

    selected_strategy = st.selectbox("Select Strategy", strategy_names)
    params = strategies[selected_strategy]

    st.markdown("### Parameters")
    param_widgets = {}
    for k, v in params.items():
        if k == "enabled":
            param_widgets[k] = st.checkbox("Enabled", value=v)
        elif isinstance(v, int) or isinstance(v, float):
            param_widgets[k] = st.number_input(k.replace("_", " ").title(), value=v)
        else:
            param_widgets[k] = st.text_input(k.replace("_", " ").title(), value=str(v))

    colA, colB = st.columns(2)
    with colA:
        if st.button("Save Parameters", help="Save to config.yaml and apply"):
            # Integration point: persist to backend/config
            if "strategies" not in st.session_state.config:
                st.session_state.config["strategies"] = {}
            if selected_strategy not in st.session_state.config["strategies"]:
                st.session_state.config["strategies"][selected_strategy] = {}
            st.session_state.config["strategies"][selected_strategy].update(param_widgets)
            save_config(st.session_state.config)
            st.success("Parameters saved.")
    with colB:
        run_bt = st.button("Run Backtest", help="Run a quick backtest with current params")

    if run_bt:
        with st.spinner("Running backtest..."):
            metrics, equity_df = run_backtest(selected_strategy, param_widgets)
        st.markdown("#### Performance Metrics")
        mcols = st.columns(len(metrics))
        for (metric, val), col in zip(metrics.items(), mcols):
            col.metric(metric, val)

        st.markdown("#### Equity Curve")
        fig = px.line(equity_df, x="Date", y="Equity", title="Equity Curve")
        fig.update_layout(template="plotly_white")
        st.plotly_chart(fig, use_container_width=True)

# --- PORTFOLIO ---
elif page == "Portfolio":
    st.title("📁 Portfolio")

    positions = get_current_positions()
    df_positions = pd.DataFrame(positions)

    st.subheader("Holdings")
    st.dataframe(df_positions, use_container_width=True)

    st.subheader("Risk Metrics (Mock Data)")
    k1, k2, k3 = st.columns(3)
    k1.metric("Total Value", "$50,000")
    k2.metric("Max Drawdown", "12%")
    k3.metric("Volatility", "8%")

    st.subheader("Correlation Heatmap (Mock)")
    import numpy as np
    corr_matrix = pd.DataFrame(
        np.array([[1, 0.2, -0.1], [0.2, 1, 0.3], [-0.1, 0.3, 1]]),
        index=["AAPL", "TSLA", "GOOG"],
        columns=["AAPL", "TSLA", "GOOG"],
    )
    fig = px.imshow(corr_matrix, text_auto=True, color_continuous_scale="RdBu_r", origin="lower")
    fig.update_layout(height=400, template="plotly_white")
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Manual Rebalance")
    if not df_positions.empty:
        rebalance_symbol = st.selectbox("Select symbol to rebalance", df_positions["symbol"], help="Choose which position to change")
        cur_qty = int(df_positions[df_positions["symbol"] == rebalance_symbol]["quantity"].values[0])
        rebalance_qty = st.number_input("New quantity", min_value=0, value=cur_qty)
        if st.button("Apply Rebalance"):
            # Integration point: call portfolio manager rebalance
            append_log("INFO", f"Rebalanced {rebalance_symbol} to {rebalance_qty} units.")
            st.success(f"Rebalanced {rebalance_symbol} to {rebalance_qty} units.")
    else:
        st.info("No positions to rebalance.")

# --- LOGS ---
elif page == "Logs":
    st.title("📜 Logs")

    levels = ["INFO", "WARNING", "ERROR"]
    selected_levels = st.multiselect("Filter levels", levels, default=levels)

    logs = [log for log in st.session_state.logs if log["level"] in selected_levels]
    df_logs = pd.DataFrame(logs)

    st.dataframe(df_logs, use_container_width=True)

    c1, c2 = st.columns(2)
    with c1:
        if st.button("Export Logs to CSV"):
            st.session_state["_logs_csv_ready"] = True
    with c2:
        if st.session_state.get("_logs_csv_ready"):
            csv = df_logs.to_csv(index=False).encode()
            st.download_button("Download Logs CSV", data=csv, file_name="bot_logs.csv", mime="text/csv")

# --- SETTINGS ---
elif page == "Settings":
    st.title("⚙️ Settings")

    config = st.session_state.config

    st.subheader("Bot Mode")
    mode = st.selectbox("Select mode", ["paper", "live"], index=["paper", "live"].index(config.get("mode", "paper")), help="Choose trading mode")
    config["mode"] = mode

    st.markdown("### API Keys")
    api_key = st.text_input("API Key", type="password", value=os.getenv("API_KEY", ""), help="Keys are not persisted by the app; set via env or encryption helper")
    api_secret = st.text_input("API Secret", type="password", value=os.getenv("API_SECRET", ""))

    if st.button("Save Settings"):
        # Save config and environment vars (in real deployment, not via app)
        save_config(config)
        append_log("INFO", "Settings saved.")
        st.success("Settings saved. Please restart the app for API keys to take effect.")

    st.markdown("### Raw Config Editor")
    raw_config = st.text_area("Edit config.yaml", value=yaml.dump(config), height=300)

    if st.button("Save Config"):
        try:
            new_config = yaml.safe_load(raw_config)
            st.session_state.config = new_config
            save_config(new_config)
            st.success("Config saved successfully.")
        except Exception as e:
            st.error(f"Error parsing YAML: {e}")