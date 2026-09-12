import streamlit as st


def render_kpi_grid(metrics: dict[str, object]) -> None:
    columns = st.columns(len(metrics))
    for column, (label, value) in zip(columns, metrics.items(), strict=False):
        column.metric(label, value)

