# ui/load_passport.py

import streamlit as st
from db.manager import DatabaseManager, TableConfig
from dataclasses import fields
from typing import Dict, Any

ENTITY_CONFIGS = {
    'analyte': {
        'label': '🎯 Аналит (TA)',
        'table_config': TableConfig.ANALYTES,
        'session_prefix': 'analyte',
    },
    'bio': {
        'label': '🔴 Биослой (BRE)',
        'table_config': TableConfig.BIO_RECOGNITION,
        'session_prefix': 'bio',
    },
    'immob': {
        'label': '🟡 Иммобилизация (IM)',
        'table_config': TableConfig.IMMOBILIZATION,
        'session_prefix': 'immob',
    },
    'mem': {
        'label': '🟣 Мемристор (MEM)',
        'table_config': TableConfig.MEMRISTIVE,
        'session_prefix': 'mem',
    },
}

def show_load_passport_dialog(db: DatabaseManager):
    """Универсальный диалог загрузки паспорта."""
    st.subheader("📁 Загрузить паспорт из БД")
    
    col1, col2 = st.columns(2)
    
    with col1:
        entity_type = st.selectbox(
            "Выберите тип слоя",
            list(ENTITY_CONFIGS.keys()),
            format_func=lambda x: ENTITY_CONFIGS[x]['label']
        )
    
    with col2:
        entity_id = st.text_input("ID слоя")
    
    if st.button("🔍 Загрузить", use_container_width=True):
        if not entity_id:
            st.error("❌ Введите ID слоя!")
            return
        
        config = ENTITY_CONFIGS[entity_type]
        db_method_name = f"get_{config['table_config']['entity_name'].replace(' ', '_').lower()}_by_id"
        
        # Динамический вызов нужного метода
        db_method = getattr(db, db_method_name, None)
        if not db_method:
            st.error(f"❌ Метод {db_method_name} не найден")
            return
        
        data = db_method(entity_id)
        
        if not data:
            st.error(f"❌ {config['label']} с ID '{entity_id}' не найден")
            return
        
        # Загрузка в session_state
        prefix = config['session_prefix']
        for key, value in data.items():
            # Преобразование имён: TA_ID → analyte_ta_id
            normalized_key = key.lower()
            session_key = f"{prefix}_{normalized_key}"
            st.session_state[session_key] = value
        
        st.success(f"✅ {config['label']} '{data.get(list(data.keys())[1], 'Без названия')}' загружен!")
        st.info(f"💡 Данные загружены в форму '{config['label']}'")
