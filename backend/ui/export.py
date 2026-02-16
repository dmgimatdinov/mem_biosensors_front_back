# ui/export.py

import streamlit as st
from services.export_service import ExportService
from domain.table_config import TABLE_CONFIGS
from db.manager import DatabaseManager

def show_export_page(db: DatabaseManager):
    """Страница экспорта."""
    st.header("📤 Экспорт данных")
    
    service = ExportService(db)
    
    col1, col2 = st.columns(2)
    
    with col1:
        export_type = st.selectbox(
            "Что экспортировать",
            ["Одна таблица", "Всё"],
        )
    
    with col2:
        fmt = st.radio("Формат", ["csv", "json"], horizontal=True)
    
    if export_type == "Одна таблица":
        table_key = st.selectbox(
            "Выбери таблицу",
            list(TABLE_CONFIGS.keys()),
            format_func=lambda k: TABLE_CONFIGS[k].label
        )
        
        if st.button("📥 Экспортировать", use_container_width=True):
            try:
                payload, filename = service.export_table(table_key, fmt)
                st.download_button(
                    "⬇️ Скачать",
                    data=payload,
                    file_name=filename,
                    mime=f"{'application/json' if fmt == 'json' else 'text/csv'}"
                )
                st.success("✅ Экспорт выполнен")
            except Exception as e:
                st.error(f"❌ Ошибка: {e}")
    
    else:  # Всё
        if st.button("📥 Экспортировать всё", use_container_width=True):
            try:
                payload, filename = service.export_all(fmt)
                st.download_button(
                    "⬇️ Скачать",
                    data=payload,
                    file_name=filename,
                    mime=f"{'application/json' if fmt == 'json' else 'application/zip'}"
                )
                st.success("✅ Экспорт выполнен")
            except Exception as e:
                st.error(f"❌ Ошибка: {e}")
