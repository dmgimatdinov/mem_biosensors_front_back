# ui/data_entry.py

import streamlit as st
from typing import Dict, Any, Tuple
from domain.fields import ALL_FIELDS, UIField

def render_field(field: UIField, prefix: str) -> Any:
    """Отрисовка одного поля по конфигу."""
    key = f"{prefix}_{field.group}_{field.name}"
    
    if field.type == "text":
        return st.text_input(
            field.label,
            key=key,
            help=field.help,
        )
    elif field.type == "number":
        return st.number_input(
            field.label,
            min_value=field.min_value,
            max_value=field.max_value,
            key=key,
            help=field.help,
        )
    elif field.type == "select":
        return st.selectbox(
            field.label,
            options=field.options or [],
            key=key,
            help=field.help,
        )
    else:
        # на будущее для range/complex
        return st.text_input(field.label, key=key, help=field.help)

def create_data_entry_tab() -> Tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any], Dict[str, Any]]:
    """Создание вкладки ввода паспорта с декларативной схемой."""
    st.header("🔬 Ввод паспорта биосенсора v2.0")
    
    # Контейнер с двумя колонками
    with st.container():
        col1, col2 = st.columns(2)
        
        # Группы значений
        analyte_vars: Dict[str, Any] = {}
        bio_vars: Dict[str, Any] = {}
        immob_vars: Dict[str, Any] = {}
        mem_vars: Dict[str, Any] = {}
        
        # Левая колонка: analyte + bio
        with col1:
            st.subheader("🎯 Целевой аналит (TA)")
            for field in [f for f in ALL_FIELDS if f.group == "analyte"]:
                analyte_vars[field.name] = render_field(field, prefix="form")
            
            st.divider()
            st.subheader("🔴 Биораспознающий слой (BRE)")
            for field in [f for f in ALL_FIELDS if f.group == "bio"]:
                bio_vars[field.name] = render_field(field, prefix="form")
        
        # Правая колонка: immob + mem
        with col2:
            st.subheader("🟡 Иммобилизационный слой (IM)")
            for field in [f for f in ALL_FIELDS if f.group == "immob"]:
                immob_vars[field.name] = render_field(field, prefix="form")
            
            st.divider()
            st.subheader("🟣 Мемристивный слой (MEM)")
            for field in [f for f in ALL_FIELDS if f.group == "mem"]:
                mem_vars[field.name] = render_field(field, prefix="form")
    
    st.divider()
    btn_col1, btn_col2, btn_col3 = st.columns(3)
    
    save_clicked = clear_clicked = load_clicked = False
    
    with btn_col1:
        save_clicked = st.button("💾 Сохранить паспорт", key="save_btn", use_container_width=True)
    with btn_col2:
        clear_clicked = st.button("🗑️ Очистить форму", key="clear_btn", use_container_width=True)
    with btn_col3:
        load_clicked = st.button("📁 Загрузить паспорт", key="load_btn", use_container_width=True)

    # Здесь возвращаем данные + флаги нажатий, чтобы обработать их снаружи
    return analyte_vars, bio_vars, immob_vars, mem_vars, save_clicked, clear_clicked, load_clicked
