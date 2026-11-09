"""Dashboard presentation helpers."""
import streamlit as st


def metric_card(label: str, value: str | int) -> None:
    st.markdown(f"<div class='metric-card'><div class='metric-label'>{label}</div><div class='metric-value'>{value}</div></div>", unsafe_allow_html=True)
