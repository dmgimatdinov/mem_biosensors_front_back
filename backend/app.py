# app.py
import streamlit as st
from db.manager import DatabaseManager
from services.biosensor_service import BiosensorService
from ui.sidebar import show_sidebar
from ui.forms import render_form
from ui.tables import show_table_selector
from ui.analytics import (
    show_statistics_page,
    show_best_combinations_page,
    show_comparative_analysis_page
)
from ui.export import show_export_page
from domain.config import FORMS_CONFIG

from db.exceptions import DatabaseConnectionError

from ui.data_entry import create_data_entry_tab

from ui.passport_forms import render_data_entry_form, show_duplicate_dialog
from services.passport_service import PassportService

from utils.logging_config import setup_logging
import logging


def init_session():
    """Инициализация session_state один раз"""
    if "db" not in st.session_state:
        try:
            st.session_state.db = DatabaseManager()
        except DatabaseConnectionError as e:
            st.error(f"❌ Не удалось подключиться к БД: {e}")
            st.stop()
    if "service" not in st.session_state:
        st.session_state.service = BiosensorService(st.session_state.db)
    if "active_section" not in st.session_state:
        st.session_state.active_section = "data_entry"
    if "form_data" not in st.session_state:
        st.session_state.form_data = {}

def show_data_entry_page(service: PassportService):
    analyte, bio_layer, immob_layer, mem_layer = render_data_entry_form()
    
    st.divider()
    btn_col1, btn_col2, btn_col3 = st.columns(3)
    
    with btn_col1:
        save_clicked = st.button("💾 Сохранить паспорт", use_container_width=True)
    with btn_col2:
        clear_clicked = st.button("🗑️ Очистить форму", use_container_width=True)
    with btn_col3:
        load_clicked = st.button("📁 Загрузить паспорт", use_container_width=True)
    
    if save_clicked:
        ok, result = service.save_passport(
            analyte=analyte,
            bio_layer=bio_layer,
            immobilization_layer=immob_layer,
            memristive_layer=mem_layer,
        )
        
        if ok:
            st.success(result)
        elif isinstance(result, tuple) and result[0] == "DUPLICATE":
            # Есть дубликаты
            action = show_duplicate_dialog(result[1])
            if action == "OVERWRITE":
                for entity_name, entity_id in result[1]:
                    service.overwrite_entity(entity_name.lower(), entity_id)
                
                # Повторная попытка сохранения
                ok, msg = service.save_passport(
                    analyte=analyte,
                    bio_layer=bio_layer,
                    immobilization_layer=immob_layer,
                    memristive_layer=mem_layer,
                )
                if ok:
                    st.success(msg)
                    st.rerun()
                else:
                    st.error(msg)
        else:
            st.error(result)
    
    if clear_clicked:
        for k in list(st.session_state.keys()):
            if k.startswith("form_"):
                del st.session_state[k]
        st.info("✅ Форма очищена")
        st.rerun()
    
    if load_clicked:
        st.info("📂 Загрузка паспорта (реализуется далее)")

def show_sidebar(db: DatabaseManager):
    st.sidebar.title("Меню")
    
    # Навигация
    st.sidebar.subheader("🔀 Навигация")
    section = st.sidebar.radio(
        "Раздел",
        ["Ввод", "База данных", "Статистика", "Анализ", "Экспорт", "О программе"],
        label_visibility="collapsed"
    )
    
    return section.lower() if section else "ввод"
        
def main():
    setup_logging(log_file="logs/biosensor.log", level=logging.INFO)
    
    # Конфигурация страницы — один раз
    st.set_page_config(
        page_title="Паспорта мемристивных биосенсоров v2.0",
        page_icon="🧪", 
        layout="wide",
        menu_items={ # Меню "Help"
            'About': '# Это крутое приложение!'
        }
    )
    st.title("Паспорта мемристивных биосенсоров v2.0")
    
    init_session()
    db = st.session_state.db
    
    service = st.session_state.service
    active = show_sidebar(db)

    
    st.divider()
    
    # Роутинг по секциям
    if active == "ввод":
        st.header("Ввод данных")
        
        form_type = st.selectbox(
            "Выбери тип данных",
            list(FORMS_CONFIG.keys())
        )
        
        form_data = render_form(form_type, service)
        if form_data:
            is_saved, message = service.save_analyte(form_data)
            if is_saved:
                st.success(message)
                st.session_state.form_data = {}
            else:
                st.error(message)
            
    elif active == "база данных":
        st.header("База данных")
        form_type = st.selectbox(
            "Выбери тип данных",
            list(FORMS_CONFIG.keys())
        )
        entities = service.get_all_entities(form_type)
        st.dataframe(entities)
    
    elif active == "анализ":
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("🏆 Лучшие комбинации", use_container_width=True):
                st.session_state.analysis_type = "best"
        with col2:
            if st.button("📊 Сравнительный анализ", use_container_width=True):
                st.session_state.analysis_type = "comparative"
        with col3:
            if st.button("📈 Статистика", use_container_width=True):
                st.session_state.analysis_type = "stats"
        
        st.divider()
        
        analysis_type = st.session_state.get("analysis_type", "best")
        if analysis_type == "best":
            show_best_combinations_page(db)
        elif analysis_type == "comparative":
            show_comparative_analysis_page(db)
        elif analysis_type == "stats":
            show_statistics_page(db)
    
    elif active == "экспорт":
        show_export_page(db)
    
    elif active == "о программе":
        st.info("Паспорта мемристивных биосенсоров v2.0\n© 2025")

if __name__ == "__main__":
    main()


# old version
# import streamlit as st
# from DB_6 import BiosensorGUI

# @st.cache_resource
# def initialize_app():
#     """Инициализирует приложение один раз и сохраняет в кэш."""
#     return BiosensorGUI()

# if __name__ == "__main__":
#     app = initialize_app()
#     app.run()