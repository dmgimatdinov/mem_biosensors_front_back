import streamlit as st
from typing import Optional

def show_table_selector() -> Optional[str]:
    """
    Простой селектор таблицы для app.py.
    Возвращает имя выбранной таблицы или None.
    """
    tables = [
        "analytes",
        "biosensor_readings",
        "experiments",
        "calibrations",
    ]
    selected = st.sidebar.selectbox("Выберите таблицу", ["— не выбрано —"] + tables)
    if selected == "— не выбрано —":
        return None
    return selected
