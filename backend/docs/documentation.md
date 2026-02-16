
# Документация к системе паспортов мемристивных биосенсоров (DB_6.py)

## 1. Архитектура системы

Система состоит из двух основных классов:

- **DatabaseManager** — управление операциями с базой данных SQLite для приложения паспортов биосенсоров.
- **BiosensorGUI** — графический интерфейс пользователя на базе Streamlit для ввода, просмотра, анализа и экспорта данных.

Основные компоненты:

```text
DB_6.py
├── DatabaseManager (работа с БД)
│   ├── Создание таблиц
│   ├── CRUD-операции для каждого типа слоя
│   ├── Кэширование запросов (lru_cache)
│   └── Пагинация данных
│
└── BiosensorGUI (пользовательский интерфейс)
    ├── Ввод паспортов
    ├── Просмотр базы данных
    ├── Анализ характеристик
    └── Экспорт данных
```


***

## 2. Структура базы данных

База данных `memristive_biosensor.db` содержит 5 таблиц.

### 2.1 Таблица Analytes

```sql
CREATE TABLE IF NOT EXISTS Analytes (
    TA_ID    VARCHAR PRIMARY KEY,
    TA_Name  VARCHAR NOT NULL,
    PH_Min   REAL,
    PH_Max   REAL,
    T_Max    REAL,
    ST       REAL,
    HL       REAL,
    PC       REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```


### 2.2 Таблица BioRecognitionLayers

```sql
CREATE TABLE IF NOT EXISTS BioRecognitionLayers (
    BRE_ID   VARCHAR PRIMARY KEY,
    BRE_Name VARCHAR NOT NULL,
    PH_Min   REAL,
    PH_Max   REAL,
    T_Min    REAL,
    T_Max    REAL,
    SN       REAL,
    DR_Min   REAL,
    DR_Max   REAL,
    RP       REAL,
    TR       REAL,
    ST       REAL,
    LOD      REAL,
    HL       REAL,
    PC       REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```


### 2.3 Таблица ImmobilizationLayers

```sql
CREATE TABLE IF NOT EXISTS ImmobilizationLayers (
    IM_ID   VARCHAR PRIMARY KEY,
    IM_Name VARCHAR NOT NULL,
    PH_Min  REAL,
    PH_Max  REAL,
    T_Min   REAL,
    T_Max   REAL,
    MP      REAL,
    Adh     VARCHAR,
    Sol     VARCHAR,
    K_IM    REAL,
    RP      REAL,
    TR      REAL,
    ST      REAL,
    HL      REAL,
    PC      REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```


### 2.4 Таблица MemristiveLayers

```sql
CREATE TABLE IF NOT EXISTS MemristiveLayers (
    MEM_ID  VARCHAR PRIMARY KEY,
    MEM_Name VARCHAR NOT NULL,
    PH_Min  REAL,
    PH_Max  REAL,
    T_Min   REAL,
    T_Max   REAL,
    MP      REAL,
    SN      REAL,
    DR_Min  REAL,
    DR_Max  REAL,
    RP      REAL,
    TR      REAL,
    ST      REAL,
    LOD     REAL,
    HL      REAL,
    PC      REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```


### 2.5 Таблица SensorCombinations

```sql
CREATE TABLE IF NOT EXISTS SensorCombinations (
    Combo_ID  VARCHAR PRIMARY KEY,
    TA_ID     VARCHAR NOT NULL,
    BRE_ID    VARCHAR NOT NULL,
    IM_ID     VARCHAR NOT NULL,
    MEM_ID    VARCHAR NOT NULL,
    SN_total  REAL,
    TR_total  REAL,
    ST_total  REAL,
    RP_total  REAL,
    LOD_total REAL,
    DR_total  VARCHAR,
    HL_total  REAL,
    PC_total  REAL,
    Score     REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (TA_ID)  REFERENCES Analytes (TA_ID),
    FOREIGN KEY (BRE_ID) REFERENCES BioRecognitionLayers (BRE_ID),
    FOREIGN KEY (IM_ID)  REFERENCES ImmobilizationLayers (IM_ID),
    FOREIGN KEY (MEM_ID) REFERENCES MemristiveLayers (MEM_ID)
);
```


***

## 5. Классы и методы

### 5.1 Класс DatabaseManager

**Назначение:** инкапсулирует всю работу с SQLite: создание таблиц, вставку, получение и кэширование данных.

Основные методы:

- `__init__(self, db_name="memristive_biosensor.db")` — инициализация, включение `PRAGMA foreign_keys=ON`, создание таблиц.
- `create_tables(self)` — выполняет SQL `CREATE TABLE IF NOT EXISTS` для всех таблиц.

Методы вставки (Create):

- `insert_analyte(self, data: Dict[str, Any]) -> bool | str`
- `insert_bio_recognition_layer(self, data: Dict[str, Any]) -> bool | str`
- `insert_immobilization_layer(self, data: Dict[str, Any]) -> bool | str`
- `insert_memristive_layer(self, data: Dict[str, Any]) -> bool | str`
- `insert_sensor_combination(self, data: Dict[str, Any]) -> bool | str`

Каждый метод:

1) проверяет наличие записи с тем же ID;
2) при дубликате возвращает `"DUPLICATE"`;
3) иначе выполняет `INSERT OR REPLACE` и очищает кэш.

Методы чтения (Read) с кэшированием:

- `@lru_cache(maxsize=32) list_all_analytes(self) -> List[Dict[str, Any]]`
- `@lru_cache(maxsize=32) list_all_bio_recognition_layers(self) -> List[Dict[str, Any]]`
- `@lru_cache(maxsize=32) list_all_immobilization_layers(self)`
- `@lru_cache(maxsize=32) list_all_memristive_layers(self)`
- `@lru_cache(maxsize=32) list_all_sensor_combinations(self)`

Каждый формирует SQL `SELECT`, мапит строки в словари по именам колонок и логирует количество записей.

Методы с пагинацией:

- `list_all_*_paginated(self, limit: int, offset: int)` — аналогичные запросы с `LIMIT ? OFFSET ?`.

Методы получения по ID:

- `get_analyte_by_id(self, ta_id: str)`
- `get_bio_recognition_layer_by_id(self, bre_id: str)`
- `get_immobilization_layer_by_id(self, im_id: str)`
- `get_memristive_layer_by_id(self, mem_id: str)`

Возвращают словарь с полями или `None`, если запись не найдена.

Служебный метод:

- `clear_cache(self)` — вызывает `.cache_clear()` для всех list_all* методов и пишет в лог `"Кэш очищен"`.

***

### 5.2 Класс BiosensorGUI

**Назначение:** реализует интерфейс Streamlit и бизнес-логику вокруг ввода, анализа и экспорта данных.

Ключевые части:

- `__init__(self)` — конфигурирует страницу (`st.set_page_config`), создает `DatabaseManager`, инициализирует `st.session_state` (`active_section`, `page_size`, `current_page`, `current_data_type`) и загружает `field_constraints` и `config`.
- `get_default_config()` (staticmethod) — возвращает схему полей для:
    - `analyte`, `bio_recognition`, `immobilization`, `memristive`
с `label`, `var_name`, подсказкой и типом (`range` и т.п.).

UI‑методы:

- `create_menu(self)` — боковое меню с разделами:
    - «Файл» (сохранить/загрузить паспорт),
    - «Навигация» (Ввод, База, Анализ),
    - «Инструменты» (Очистить, Экспорт),
    - «Справка» (О программе).
- `create_data_entry_tab()` — создает формы ввода для всех четырех сущностей (TA, BRE, IM, MEM) в двух колонках, использует `st.text_input`, `st.number_input`, `st.selectbox`.
- `create_database_tab(self)` — отображает таблицу выбранного типа (TA/BRE/IM/MEM) с кнопками выбора и пагинацией (`Записей на странице`, «Предыдущая/Следующая»).
- `create_analysis_tab(self)` — три кнопки:
    - «🏆 Лучшие комбинации» → `show_best_combinations()`
    - «📊 Сравнительный анализ» → `comparative_analysis()`
    - «📈 Статистика» → `show_statistics()`
и текстовое поле для результатов в `st.session_state.analysisresult`.

Работа с данными через UI:

- `save_passport_to_db_streamlit(self)` — собирает данные из `st.session_state` для всех слоев, вызывает методы `insert_*`, обрабатывает `"DUPLICATE"` через диалог перезаписи (удаление и повторная вставка).
- `load_passport_from_db_streamlit(self)` — по введенному ID загружает слой из БД и заполняет `st.session_state` для соответствующих полей формы.
- `clear_form_streamlit()` (staticmethod) — сбрасывает значения в `st.session_state` и перерисовывает интерфейс.

Просмотр конкретных таблиц:

- `show_analytes(self)`, `show_bio_layers(self)`, `show_immobilization_layers(self)`, `show_memristive_layers(self)` — используют `list_all_*_paginated`, строят `pandas.DataFrame` и показывают только ключевые колонки.

Анализ:

- `comparative_analysis(self)` — собирает списки аналитов и слоев, считает их количество и формирует текстовый отчет с примерами первых трех элементов каждого типа.
- `show_best_combinations(self)` — получает все `SensorCombinations` и формирует текст с перечислением комбинаций и их `Score`.
- `show_statistics()` (staticmethod) — выполняет `SELECT COUNT(*)` по каждой таблице и записывает статистику в `analysisresult`.

Экспорт:

- `export_data(self)` — позволяет выбрать таблицу (`analytes`, `biorecognition`, `immobilization`, `memristive`, `sensorcombinations`, `all`) и формат (`csv` или `json`); при выборе `all` создает ZIP с несколькими файлами.

Главный цикл:

- `run(self)` — создает меню, смотрит на `st.session_state.active_section` и рисует нужную вкладку (ввод, база, анализ, о программе).

***

## 6. Пользовательский интерфейс

### 6.1 Навигация

В `create_menu` боковая панель делится на блоки «Файл», «Навигация», «Инструменты», «Справка» с кнопками для смены `active_section` в `st.session_state`.

### 6.2 Ввод паспортов

`create_data_entry_tab` строит две колонки:

- левая: «Целевой аналит (TA)» и «Биораспознающий слой (BRE)»;
- правая: «Иммобилизационный слой (IM)» и «Мемристивный слой (MEM)».

Каждый параметр вводится через `st.number_input` или `st.selectbox` с жесткими пределами, соответствующими `field_constraints`.

### 6.3 Просмотр базы

`create_database_tab` отображает:

- кнопки выбора типа данных (TA/BRE/IM/MEM);
- число записей на странице (5–100);
- таблицу с выбранным типом данных;
- навигацию по страницам через `current_page` в `session_state`.


### 6.4 Анализ и экспорт

Аналитические функции выводят текстовый результат в `st.textarea`, привязанный к `st.session_state.analysisresult`.
Экспорт использует `pandas` и, для ZIP, модуль `zipfile` и `io.BytesIO` для формирования архива в памяти.

***

## 7. Соответствие обозначений (ключевые поля)

Небольшая сводка по соответствию БД–UI для основных характеристик слоев.


| В БД | В форме/состоянии (пример) | Логическое имя |
| :-- | :-- | :-- |
| `PH_Min` / `PH_Max` | `*_ph_min` / `*_ph_max` | pH диапазон |
| `T_Min` / `T_Max` | `*_t_min` / `*_t_max` | температурный диапазон |
| `MP` | `immob_young_modulus`, `mem_young_modulus` | модуль Юнга (механическая совместимость) |
| `SN` | `bio_sensitivity`, `mem_sensitivity` | чувствительность |
| `DR_Min` / `DR_Max` | `*_dr_min` / `*_dr_max` | диапазон измерений |
| `RP` | `*_reproducibility` | воспроизводимость |
| `TR` | `*_response_time` | время отклика |
| `ST` | `*_stability` | стабильность |
| `LOD` | `*_lod` | предел обнаружения |
| `HL` | `*_durability` или `half_life` | долговечность / T½ |
| `PC` | `*_power_consumption` | энергопотребление |


