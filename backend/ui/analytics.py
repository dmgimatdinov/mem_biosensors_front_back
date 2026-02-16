# ui/analytics.py

import streamlit as st
import pandas as pd
from services.analytics_service import AnalyticsService
from db.manager import DatabaseManager

def show_statistics_page(db: DatabaseManager):
    """Страница со статистикой БД."""
    st.header("📊 Статистика")
    
    service = AnalyticsService(db)
    stats = service.get_database_statistics()
    
    if not stats:
        st.warning("⚠️ Нет данных для статистики")
        return
    
    # Метрики
    cols = st.columns(len(stats))
    for i, (key, stat) in enumerate(stats.items()):
        with cols[i]:
            st.metric(stat['label'], stat['count'])
    
    # График распределения
    st.subheader("Распределение записей по типам")
    chart_data = {s['label']: s['count'] for s in stats.values()}
    st.bar_chart(chart_data)

def show_best_combinations_page(db: DatabaseManager):
    """Страница с лучшими комбинациями."""
    st.header("🏆 Лучшие комбинации")
    
    service = AnalyticsService(db)
    
    top_n = st.slider("Показать топ N", 1, 50, 10)
    combos = service.get_best_combinations(top_n)
    
    if not combos:
        st.info("Комбинаций не найдено. Сначала синтезируйте комбинации.")
        return
    
    # Таблица
    df = pd.DataFrame(combos)
    st.dataframe(df, use_container_width=True)
    
    # Детальный просмотр
    if st.checkbox("Показать детали"):
        selected_idx = st.selectbox("Выбери комбинацию", range(len(combos)))
        st.json(combos[selected_idx])

def show_comparative_analysis_page(db: DatabaseManager):
    """Страница со сравнительным анализом."""
    st.header("📊 Сравнительный анализ")
    
    service = AnalyticsService(db)
    analysis = service.get_comparative_analysis()
    
    # Аналиты
    st.subheader("📋 Аналиты")
    if analysis['analytes']:
        df = pd.DataFrame(analysis['analytes'])
        st.dataframe(df)
    else:
        st.info("Нет аналитов")
    
    # Биослои
    st.subheader("🔴 Биораспознающие слои")
    if analysis['bio_layers']:
        df = pd.DataFrame(analysis['bio_layers'])
        st.dataframe(df)
    else:
        st.info("Нет биослоёв")
    
    # И так далее...
