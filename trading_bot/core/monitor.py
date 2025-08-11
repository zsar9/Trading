"""
Monitoring module: dashboard and alerts.
"""
from __future__ import annotations

import logging
from typing import Dict

logger = logging.getLogger(__name__)


def run_dashboard(config: Dict) -> None:
    backend = config.get("monitoring", {}).get("dashboard", {}).get("backend", "streamlit")
    if backend != "streamlit":
        logger.warning("Only Streamlit dashboard backend is supported in this skeleton.")
        return
    try:
        import streamlit as st
    except Exception as exc:
        logger.error("Streamlit not installed: %s", exc)
        return

    st.set_page_config(page_title="Trading Bot Dashboard", layout="wide")
    st.title("Trading Bot Dashboard")
    st.caption("Minimal skeleton dashboard")
    st.write("Edit the dashboard in core/monitor.py to add live metrics, PnL, and risk.")


def send_alert(config: Dict, subject: str, body: str) -> None:
    alerts = config.get("monitoring", {}).get("alerts", {})
    if alerts.get("email", {}).get("enabled"):
        logger.info("Would send email: %s - %s", subject, body)
    if alerts.get("sms", {}).get("enabled"):
        logger.info("Would send SMS: %s - %s", subject, body)