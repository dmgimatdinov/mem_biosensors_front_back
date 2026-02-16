# ui/analysis_page.py

import streamlit as st
from services.combination_synthesis import CombinationSynthesisService
from db.manager import DatabaseManager

def show_analysis_page(db: DatabaseManager, service: CombinationSynthesisService):
    st.header("📈 Анализ и синтез комбинаций")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔬 Синтезировать комбинации", use_container_width=True):
            with st.spinner("Синтез комбинаций... Это может занять время"):
                total, created = service.synthesize_all_combinations(max_combinations=5000)
                st.success(f"✅ Синтез завершён!\n**Проверено**: {total}\n**Создано**: {created}")
    
    with col2:
        if st.button("📊 Лучшие комбинации", use_container_width=True):
            show_best_combinations(db)
    
    with col3:
        if st.button("📈 Статистика", use_container_width=True):
            show_statistics(db)

def show_best_combinations(db: DatabaseManager):
    """Показать топ комбинаций по Score."""
    st.subheader("🏆 Лучшие комбинации")
    
    all_combos = db.list_all_sensor_combinations()
    if not all_combos:
        st.info("Комбинаций не найдено. Сначала запустите синтез.")
        return
    
    # Сортировка по Score
    sorted_combos = sorted(all_combos, key=lambda x: x.get('Score', 0), reverse=True)
    
    top_n = st.slider("Показать топ N комбинаций", 1, min(50, len(sorted_combos)), 10)
    
    import pandas as pd
    df = pd.DataFrame(sorted_combos[:top_n])
    st.dataframe(df, use_container_width=True)
    
    # Детальный просмотр
    selected_idx = st.selectbox("Выбери комбинацию для деталей", range(len(sorted_combos[:top_n])))
    if selected_idx is not None:
        combo = sorted_combos[selected_idx]
        st.json(combo)

def show_statistics(db: DatabaseManager):
    """Показать статистику комбинаций."""
    st.subheader("📊 Статистика")
    
    combos = db.list_all_sensor_combinations()
    if not combos:
        st.info("Нет комбинаций для анализа")
        return
    
    import pandas as pd
    df = pd.DataFrame(combos)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Всего комбинаций", len(df))
    with col2:
        st.metric("Средний Score", f"{df['Score'].mean():.2f}")
    with col3:
        st.metric("Макс Score", f"{df['Score'].max():.2f}")
    
    # График распределения Score
    st.bar_chart(df['Score'].value_counts().sort_index())
