# ui/passport_forms.py

import streamlit as st
from domain.fields import ALL_FIELDS, UIField
from domain.models import (
    Analyte, BioRecognitionLayer, ImmobilizationLayer,
    MemristiveLayer, SensorCombination
)
from typing import Optional

def render_field(field: UIField, prefix: str) -> any:
    """Рендер одного поля"""
    key = f"{prefix}_{field.group}_{field.name}"
    
    if field.type == "text":
        return st.text_input(field.label, key=key, help=field.help)
    elif field.type == "number":
        return st.number_input(
            field.label, min_value=field.min_value, max_value=field.max_value,
            key=key, help=field.help
        )
    elif field.type == "select":
        return st.selectbox(field.label, options=field.options or [], key=key, help=field.help)
    return None

def render_data_entry_form() -> tuple[Optional[Analyte], Optional[BioRecognitionLayer], Optional[ImmobilizationLayer], Optional[MemristiveLayer]]:
    """Отрисовка формы ввода и сбор данных в модели."""
    
    st.header("🔬 Ввод паспорта биосенсора v2.0")
    
    with st.container():
        col1, col2 = st.columns(2)
        
        # === ЛЕВАЯ КОЛОНКА: Аналит + БиоСлой ===
        with col1:
            st.subheader("🎯 Целевой аналит (TA)")
            analyte_data = {}
            for field in [f for f in ALL_FIELDS if f.group == "analyte"]:
                analyte_data[field.name] = render_field(field, "form")
            
            st.divider()
            st.subheader("🔴 Биораспознающий слой (BRE)")
            bio_data = {}
            for field in [f for f in ALL_FIELDS if f.group == "bio"]:
                bio_data[field.name] = render_field(field, "form")
        
        # === ПРАВАЯ КОЛОНКА: Иммобилизация + Мемристор ===
        with col2:
            st.subheader("🟡 Иммобилизационный слой (IM)")
            immob_data = {}
            for field in [f for f in ALL_FIELDS if f.group == "immob"]:
                immob_data[field.name] = render_field(field, "form")
            
            st.divider()
            st.subheader("🟣 Мемристивный слой (MEM)")
            mem_data = {}
            for field in [f for f in ALL_FIELDS if f.group == "mem"]:
                mem_data[field.name] = render_field(field, "form")
    
    # Создание объектов модели
    analyte = Analyte(**analyte_data)
    bio_layer = BioRecognitionLayer(**bio_data)
    immob_layer = ImmobilizationLayer(**immob_data)
    mem_layer = MemristiveLayer(**mem_data)
    
    return analyte, bio_layer, immob_layer, mem_layer

def show_duplicate_dialog(duplicates: list[tuple[str, str]]) -> Optional[str]:
    """Диалог при обнаружении дубликатов."""
    st.warning(f"⚠️ Обнаружены дубликаты: {', '.join([f'{e[0]} {e[1]}' for e in duplicates])}")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("✅ Перезаписать", key="overwrite_confirmed"):
            return "OVERWRITE"
    with col2:
        if st.button("❌ Отмена", key="cancel_confirmed"):
            return "CANCEL"
    
    return None
