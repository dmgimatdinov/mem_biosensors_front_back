# ui/sidebar.py
import streamlit as st

def show_sidebar(service) -> str:
    """Боковое меню, возвращает текущую секцию"""
    st.sidebar.title("Меню")
    
    st.sidebar.subheader("📁 Файл")
    col1, col2 = st.sidebar.columns(2)
    with col1:
        if st.button("💾 Сохранить", key="save", width="stretch"):
            st.session_state.action = "save"
    with col2:
        if st.button("📂 Загрузить", key="load", width="stretch"):
            st.session_state.action = "load"
    
    st.sidebar.divider()
    st.sidebar.subheader("🔀 Навигация")
    
    nav_cols = st.sidebar.columns(3)
    buttons = [
        ("🔬 Ввод", "data_entry"),
        ("📊 База", "database"),
        ("📈 Анализ", "analysis")
    ]
    
    for i, (label, section) in enumerate(buttons):
        with nav_cols[i]:
            if st.button(label, key=f"nav_{section}", width="stretch"):
                st.session_state.active_section = section
                st.rerun()
    
    st.sidebar.divider()
    st.sidebar.subheader("🔧 Инструменты")
    
    col3, col4 = st.sidebar.columns(2)
    with col3:
        if st.button("🗑️ Очистить", key="clear", width="stretch"):
            st.session_state.form_data = {}
    with col4:
        if st.button("📊 Экспорт", key="export", width="stretch"):
            st.session_state.action = "export"
    
    return st.session_state.get('active_section', 'data_entry')
