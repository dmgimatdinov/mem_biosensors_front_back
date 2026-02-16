# ui/tables.py

import streamlit as st
import pandas as pd
from db.manager import DatabaseManager
from domain.table_config import TABLE_CONFIGS, TableDisplayConfig
from typing import Optional

def render_paginated_table(
    db: DatabaseManager,
    table_key: str,
    page_size: int = 20,
) -> None:
    """
    Универсальный рендер таблицы с пагинацией.
    
    Args:
        db: DatabaseManager instance
        table_key: ключ таблицы из TABLE_CONFIGS
        page_size: количество строк на странице
    """
    if table_key not in TABLE_CONFIGS:
        st.error(f"❌ Таблица '{table_key}' не найдена")
        return
    
    config = TABLE_CONFIGS[table_key]
    
    # Инициализация session_state для таблицы
    if f'page_{table_key}' not in st.session_state:
        st.session_state[f'page_{table_key}'] = 0
    
    current_page = st.session_state[f'page_{table_key}']
    offset = current_page * page_size
    
    # Получение данных
    fetch_method = getattr(db, config.fetch_method, None)
    if not fetch_method:
        st.error(f"❌ Метод {config.fetch_method} не найден в DatabaseManager")
        return
    
    data = fetch_method(page_size, offset)
    
    # Отображение заголовка
    st.subheader(config.label)
    
    # Отображение таблицы
    if data:
        df = pd.DataFrame(data)
        # Фильтруем только нужные колонки
        available_cols = [c for c in config.display_columns if c in df.columns]
        st.dataframe(df[available_cols], use_container_width=True)
    else:
        st.info(f"Нет записей {config.entity_name.lower()}ов для отображения.")
    
    # Пагинация
    st.divider()
    _render_pagination(table_key, current_page, len(data), page_size)

def _render_pagination(table_key: str, current_page: int, data_count: int, page_size: int) -> None:
    """Отрисовка кнопок пагинации."""
    col_prev, col_page, col_next = st.columns([1, 1, 1])
    
    with col_prev:
        if st.button(
            "◀ Предыдущая",
            key=f"prev_{table_key}",
            disabled=(current_page == 0),
            use_container_width=True
        ):
            st.session_state[f'page_{table_key}'] = max(0, current_page - 1)
            st.rerun()
    
    with col_page:
        st.markdown(f"**Страница {current_page + 1}**", unsafe_allow_html=True)
    
    with col_next:
        if st.button(
            "Следующая ▶",
            key=f"next_{table_key}",
            disabled=(data_count < page_size),
            use_container_width=True
        ):
            st.session_state[f'page_{table_key}'] = current_page + 1
            st.rerun()

def show_table_selector(db: DatabaseManager, page_size: int = 20) -> None:
    """
    Отображение выбора таблицы с кнопками.
    
    Args:
        db: DatabaseManager instance
        page_size: количество строк на странице
    """
    st.subheader("📊 База данных")
    
    # Кнопки выбора таблицы
    cols = st.columns(len(TABLE_CONFIGS))
    for i, (key, config) in enumerate(TABLE_CONFIGS.items()):
        with cols[i]:
            if st.button(config.label, use_container_width=True):
                st.session_state['selected_table'] = key
                st.session_state[f'page_{key}'] = 0
                st.rerun()
    
    st.divider()
    
    # Отображение выбранной таблицы
    selected = st.session_state.get('selected_table', 'analytes')
    render_paginated_table(db, selected, page_size)
