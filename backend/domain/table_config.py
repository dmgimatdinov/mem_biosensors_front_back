# domain/table_config.py

from dataclasses import dataclass
from typing import List, Callable, Dict, Any

@dataclass
class TableDisplayConfig:
    """Конфигурация для отображения таблицы в БД."""
    key: str                           # 'analytes', 'bio_layers', etc.
    label: str                         # '📋 Аналиты'
    emoji: str                         # '📋'
    fetch_method: str                  # Имя метода в DatabaseManager
    display_columns: List[str]         # Какие колонки показывать
    entity_name: str                   # 'Аналит' для логирования

# Конфигурация всех таблиц
TABLE_CONFIGS = {
    'analytes': TableDisplayConfig(
        key='analytes',
        label='📋 Аналиты',
        emoji='📋',
        fetch_method='list_all_analytes_paginated',
        display_columns=['TA_ID', 'TA_Name', 'PH_Min', 'PH_Max', 'T_Max', 'ST'],
        entity_name='Аналит',
    ),
    'bio_layers': TableDisplayConfig(
        key='bio_layers',
        label='🔴 Биораспознающие слои',
        emoji='🔴',
        fetch_method='list_all_bio_recognition_layers_paginated',
        display_columns=['BRE_ID', 'BRE_Name', 'PH_Min', 'PH_Max', 'T_Min', 'T_Max', 'SN'],
        entity_name='Биослой',
    ),
    'immobilization_layers': TableDisplayConfig(
        key='immobilization_layers',
        label='🟡 Иммобилизационные слои',
        emoji='🟡',
        fetch_method='list_all_immobilization_layers_paginated',
        display_columns=['IM_ID', 'IM_Name', 'PH_Min', 'PH_Max', 'T_Min', 'T_Max', 'MP'],
        entity_name='Иммобилизация',
    ),
    'memristive_layers': TableDisplayConfig(
        key='memristive_layers',
        label='🟣 Мемристивные слои',
        emoji='🟣',
        fetch_method='list_all_memristive_layers_paginated',
        display_columns=['MEM_ID', 'MEM_Name', 'PH_Min', 'PH_Max', 'T_Min', 'T_Max', 'SN'],
        entity_name='Мемристор',
    ),
    'sensor_combinations': TableDisplayConfig(
        key='sensor_combinations',
        label='⚙️  Комбинации сенсоров',
        emoji='⚙️',
        fetch_method='list_all_sensor_combinations_paginated',
        display_columns=['Combo_ID', 'TA_ID', 'BRE_ID', 'IM_ID', 'MEM_ID', 'Score'],
        entity_name='Комбинация',
    ),
}
