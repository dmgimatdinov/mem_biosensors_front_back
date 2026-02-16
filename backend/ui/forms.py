# ui/forms.py
import streamlit as st
from domain.config import FORMS_CONFIG
from typing import Optional, Dict, Any

def render_form(form_type: str, service) -> Optional[Dict[str, Any]]:
    """Отображение формы ввода для типа сущности"""
    fields_config = FORMS_CONFIG.get(form_type, [])
    data = {}
    
    st.subheader(f"Добавить новый элемент ({form_type})")
    
    with st.form(f"form_{form_type}"):
        for field_cfg in fields_config:
            if field_cfg.type == 'range':
                cols = st.columns(2)
                with cols[0]:
                    data[field_cfg.min_var] = st.number_input(
                        f"{field_cfg.label} (мин)",
                        help=field_cfg.hint
                    )
                with cols[1]:
                    data[field_cfg.max_var] = st.number_input(
                        f"{field_cfg.label} (макс)",
                        help=field_cfg.hint
                    )
            elif field_cfg.type == 'text':
                data[field_cfg.var_name] = st.text_input(
                    field_cfg.label,
                    help=field_cfg.hint
                )
            else:  # single
                data[field_cfg.var_name] = st.number_input(
                    field_cfg.label,
                    help=field_cfg.hint
                )
        
        submitted = st.form_submit_button("Сохранить")
        if submitted:
            return data
    
    return None
