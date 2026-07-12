# Анализ доработок: конфликты и несоответствия

Прежде чем формировать промты, я выявил ряд **критических конфликтов со старым функционалом** и **несоответствий внутри спецификации**, которые требуют уточнения. Без их решения реализация новых блоков сломает существующую систему.

---

## 🔴 КРИТИЧЕСКИЕ КОНФЛИКТЫ СО СТАРЫМ ФУНКЦИОНАЛОМ

### Конфликт 1: Жёсткие веса vs МАИ (Блок 3)
**Старый функционал:** В системе зашиты фиксированные веса `SN=2.0, RP=1.5` и т.д.
**Новый функционал:** Вводится МАИ с пользовательскими весами.
**Риск:** Все существующие расчёты Score, тесты и сохранённые проекты потеряют согласованность.
**Требуется уточнение:**
- Сохранить ли старый режим расчёта как legacy-опцию (флаг `use_legacy_weights=true`)?
- Мигрировать ли существующие проекты на МАИ автоматически (с какими дефолтными весами)?
- Хранить ли в `Projects.settings` версию алгоритма агрегации?

### Конфликт 2: Одноэтапный vs двухэтапный валидатор (Блок 2)
**Старый функционал:** `CombinationValidator` с 3 предикатами.
**Новый функционал:** 5 предикатов + второй этап технологических фильтров.
**Риск:** Старые тесты, ожидающие конкретные булевы результаты, сломаются.
**Требуется уточнение:**
- Ввести ли новый класс `CompatibilityEngineV2`, оставив старый `CombinationValidator` нетронутым?
- Или модифицировать существующий класс с флагом `version=v1|v2`?

### Конфликт 3: Переписывание формул метрик (Блок 4)
**Старый функционал:** Упрощённые формулы.
**Новый функционал:** Физически обоснованные формулы (с `K_IM`, `D_eff`, `σ_noise`).
**Риск:** Результаты расчётов изменятся на 20–40%, все сохранённые проекты и тест-кейсы дадут другие значения.
**Требуется уточнение:**
- Сохранить ли старые формулы в `metrics_v1.py` и ввести `metrics_v2.py`?
- Добавить ли в паспорт проекта поле `metrics_version`?
- Пересчитывать ли исторические данные при миграции?

### Конфликт 4: Отсутствие аутентификации vs JWT (Блок 12)
**Старый функционал:** Все эндпоинты открыты.
**Новый функционал:** JWT + RBAC.
**Риск:** Все существующие клиенты (включая интеграции, тесты) перестанут работать.
**Требуется уточнение:**
- Ввести ли режим `AUTH_DISABLED` для dev/test окружений?
- Создавать ли "сервисного пользователя" с токеном для фоновых задач и интеграций?
- Мигрировать ли существующих пользователей автоматически в роль `Designer`?

### Конфликт 5: Синхронный vs асинхронный синтез (Блок 17)
**Старый функционал:** Синхронный `POST /api/synthesize`.
**Новый функционал:** Асинхронный `POST /api/synthesize/async`.
**Риск:** Старые клиенты, ожидающие результат в теле ответа, сломаются.
**Требуется уточнение:**
- Оставить ли старый синхронный эндпоинт для малых выборок (например, < 1000 комбинаций)?
- Ввести ли параметр `mode=sync|async`?

### Конфликт 6: Изменение схемы БД (Блок 1)
**Старый функционал:** Таблицы `Analytes`, `BioRecognitionLayers` и т.д. без полей надёжности.
**Новый функционал:** Добавление 5 новых полей в каждую таблицу.
**Риск:** Существующие `INSERT`/`SELECT` без явного списка полей могут сломаться.
**Требуется уточнение:**
- Применять ли миграцию через Alembic с `nullable=True` и дефолтными значениями?
- Заполнять ли исторические записи дефолтом `reliability_category='medium'`?

---

## 🟡 НЕСООТВЕТСТВИЯ ВНУТРИ СПЕЦИФИКАЦИИ

Обнаружены **дублирования** между блоками, которые нужно разрешить:

| Дублирование | Где встречается | Вопрос |
|---|---|---|
| Парето-фронт | Блок 3 и Блок 14 | Объединить в один блок или разнести по ответственности? |
| TOPSIS | Блок 3 и Блок 14 | То же самое |
| Интервальные оценки | Блок 1 и Блок 14 | Где должен жить код расчёта — в `metrics` или `analytics`? |
| Audit Trail | Блок 5 и Блок 9 | Объединить в Блок 9? |
| Генерация протоколов валидации | Блок 7 и Блок 15 | Блок 15 — это экспорт, Блок 7 — генерация. Разделить чётко? |
| Визуализация компромиссов | Блок 3 и Блок 16 | Блок 16 — это UI-надстройка над Блоком 3? |

---

## 🟢 МОИ ПРЕДЛОЖЕНИЯ ПО РАЗРЕШЕНИЮ (для подтверждения)

1. **Стратегия обратной совместимости:** для каждого ломающего изменения вводим **версионирование API** (`/api/v1/...` и `/api/v2/...`) + **feature flags** в конфиге.
2. **Дубликаты:** объединяю в один промт с чётким разделением ответственности (domain vs analytics vs UI).
3. **Миграция БД:** через Alembic с `server_default` и data migration script.
4. **Аутентификация:** вводим режим `AUTH_MODE=disabled|jwt`, по умолчанию `jwt`, но с возможностью отключить для тестов.

**Пожалуйста, подтвердите эти решения или укажите альтернативные.** Пока что я формирую промты с учётом этих предположений — если они неверны, промты будут скорректированы.

---

# 📨 СООБЩЕНИЕ 1/4: ПРОМТЫ ДЛЯ КРИТИЧЕСКИХ БЛОКОВ (1, 2, 4, 12)

Начинаю с критических блоков Фазы 1. Ниже — 4 подробных промта.

---

## 📋 ПРОМТ 1.1: Расширение модели данных и учёт неопределённости (Блок 1)

```
КОНТЕКСТ:
Система структурно-параметрического синтеза мемристивных биосенсоров.
Текущая БД (SQLite) содержит таблицы: Analytes, BioRecognitionLayers,
ImmobilizationLayers, MemristiveLayers. Все параметры детерминированные.

ЗАДАЧА:
Реализовать расширение схемы БД и сервис расчёта коэффициента
достоверности κ с учётом погрешности данных.

ТРЕБОВАНИЯ К БД:
1. Добавить в каждую из 4 таблиц слоёв поля:
   - source_type ENUM('experimental','manufacturer','expert','literature') DEFAULT 'expert'
   - source_doi VARCHAR(255) NULL
   - source_date DATE NULL
   - reliability_category ENUM('high','medium','low') DEFAULT 'medium'
   - data_completeness FLOAT DEFAULT 1.0 CHECK (0.0 <= data_completeness <= 1.0)
2. Все новые поля — nullable, чтобы не сломать существующие INSERT.
3. Создать миграцию Alembic с именем add_reliability_fields.
4. Написать data-migration: для существующих записей установить
   reliability_category='medium', data_completeness=0.5.

ТРЕБОВАНИЯ К СЕРВИСУ (domain/metrics.py):
1. Функция calculate_reliability_coefficient(η, α, γ) → κ:
   κ = (1 - α * (1 - η))^γ
   где η = N_available / N_total.
2. Функция calculate_final_score(raw_score, κ) → raw_score * κ.
3. Функция calculate_interval_score(structure, strategy) → (score_min, score_max, delta):
   - strategy ∈ {'pessimistic','optimistic','average'}
   - Для каждого отсутствующего параметра моделировать min/max из
     типичного диапазона класса материалов.
4. Функция suggest_critical_gaps(structure) → list[{parameter, priority, impact, method, effort}]:
   - Приоритет через анализ чувствительности: ∂Score/∂x_j.
   - Возвращается только если κ < 0.6.

КРИТЕРИИ ПРИЁМКИ:
[AC-1] Миграция успешно применяется к БД с существующими данными.
[AC-2] Все существующие SELECT-запросы продолжают работать (не используют SELECT *).
[AC-3] calculate_reliability_coefficient(η=0.9, α=0.3, γ=2.0) ≈ 0.97.
[AC-4] calculate_reliability_coefficient(η=0.6, α=0.7, γ=2.0) ≈ 0.55.
[AC-5] Нелинейный штраф: снижение η с 0.9 до 0.8 уменьшает κ на 10-15%.
[AC-6] Снижение η с 0.7 до 0.6 уменьшает κ на 30-40%.
[AC-7] interval_score возвращает score_min ≤ score_max.
[AC-8] suggest_critical_gaps возвращает пустой список при κ ≥ 0.6.

ТЕСТЫ:
Unit-тесты (pytest):
- test_migration_applies_cleanly
- test_migration_preserves_existing_data
- test_reliability_coefficient_high_completeness
- test_reliability_coefficient_low_completeness
- test_reliability_coefficient_nonlinear_penalty
- test_final_score_with_reliability
- test_interval_score_pessimistic_strategy
- test_interval_score_optimistic_strategy
- test_interval_score_average_strategy
- test_interval_score_delta_positive
- test_suggest_critical_gaps_returns_empty_for_high_kappa
- test_suggest_critical_gaps_returns_prioritized_list

Integration-тесты:
- test_full_pipeline_with_reliability: создать структуру с 3 из 4 слоёв
  с разной надёжностью, проверить итоговый Score.
- test_migration_rollback: проверить откат миграции.

ОБРАТНАЯ СОВМЕСТИМОСТЬ:
- Все старые тесты в tests/test_metrics.py должны проходить без изменений.
- Старые эндпоинты возвращают κ=1.0 для записей без reliability_category.
```

---

## 📋 ПРОМТ 1.2: Двухэтапный движок совместимости (Блок 2)

```
КОНТЕКСТ:
Существует CombinationValidator с 3 предикатами. Нужно расширить до
5 предикатов + добавить второй этап технологических фильтров.

ЗАДАЧА:
Реализовать CompatibilityEngineV2, не ломая старый CombinationValidator.

ТРЕБОВАНИЯ:
1. Создать НОВЫЙ класс CompatibilityEngineV2 в domain/compatibility.py.
   СТАРЫЙ CombinationValidator остаётся без изменений (используется legacy-кодом).
2. Реализовать 5 предикатов первого этапа:
   - check_pH_compatibility(TA, BRE, IM, MEM) → bool + reason
   - check_analyte_thermal_stability(TA, BRE, IM, MEM) → bool + reason
   - check_layer_temperature_compatibility(BRE, IM, MEM) → bool + reason
   - check_mechanical_compatibility(IM, MEM, delta_max=0.5) → bool + reason
   - check_adhesion_solubility(IM, adh_min=0.5, sol_max=10.0) → bool + reason
3. Каждый предикат возвращает (is_compatible: bool, reason: Optional[str]).
4. Метод validate_stage1(structure) → (passed: bool, failed_predicates: list).
5. Метод validate_stage2(structure, application_profile) → (passed, failed):
   - application_profile ∈ {'PoC','LoC','Clinical_Diagnostics'}
   - Для PoC: PC < 10 мВт, ISO 10993, устойчивость к температуре.
   - Для LoC: совместимость с PDMS, утечки < 1 мкл.
   - Для Clinical: ISO 10993, TR < 15 мин, стабильность > 6 мес.
6. Иерархическая проверка с ранним отсечением: сначала pH (самый селективный).
7. Метод build_compatibility_index() для ускорения:
   Index(IM_i) = {BRE_j} × {MEM_k} — предварительно вычисленные совместимые пары.

КРИТЕРИИ ПРИЁМКИ:
[AC-1] Старые тесты tests/test_combination_validator.py проходят без изменений.
[AC-2] CompatibilityEngineV2 проходит все 5 предикатов для валидной структуры.
[AC-3] Для структуры с pH-несовместимостью возвращается reason вида
       "pH-несовместимость: BRE требует pH 7.0-8.5, MEM работает при pH 5.0-6.5".
[AC-4] check_mechanical_compatibility с |MP_IM - MP_MEM| = 2.3 ГПа → False.
[AC-5] check_adhesion_solubility с Adh_IM = 0.3 МПа → False с reason.
[AC-6] Stage2 для PoC с PC = 15 мВт → False.
[AC-7] build_compatibility_index снижает сложность с O(N^4) до O(N^2 * k).
[AC-8] Раннее отсечение: если pH не прошёл, остальные предикаты не вычисляются.

ТЕСТЫ:
Unit-тесты:
- test_pH_compatibility_valid_range
- test_pH_compatibility_no_overlap
- test_analyte_thermal_stability_pass
- test_analyte_thermal_stability_degradation
- test_layer_temperature_compatibility
- test_mechanical_compatibility_within_delta
- test_mechanical_compatibility_exceeds_delta
- test_adhesion_below_minimum
- test_solubility_above_maximum
- test_stage2_poc_power_consumption
- test_stage2_loc_pdms_compatibility
- test_stage2_clinical_response_time
- test_early_termination_on_pH_failure
- test_compatibility_index_reduces_search_space

Integration-тесты:
- test_full_validation_pipeline_glucose_biosensor
- test_full_validation_pipeline_vegf_biosensor
- test_zero_false_negatives_on_reference_structures (Тест-кейс 3 из Блока 10)

Regression-тесты:
- test_legacy_combination_validator_unchanged
- test_existing_tests_still_pass (запуск всего suites/test_metrics.py)

ОБРАТНАЯ СОВМЕСТИМОСТЬ:
- CombinationValidator не модифицируется.
- Новый код живёт в CompatibilityEngineV2.
- Старые эндпоинты используют старый валидатор, новые — новый.
```

---

## 📋 ПРОМТ 1.3: Расчёт эксплуатационных характеристик (Блок 4)

```
КОНТЕКСТ:
Текущие формулы метрик упрощены. Нужно заменить на физически
обоснованные формулы из статьи, сохранив обратную совместимость.

ЗАДАЧА:
Реализовать metrics_v2.py с новыми формулами, оставив metrics_v1.py
нетронутым. Ввести переключатель через конфиг METRICS_VERSION.

ТРЕБОВАНИЯ (metrics_v2.py):
1. SN = SN_BRE × SN_MEM × K_IM, где K_IM = f(d_IM, D_eff).
2. TR = TR_BRE + d_IM²/D_eff + TR_MEM.
3. ST = min(ST_TA, ST_BRE, ST_IM, ST_MEM) — добавлен ST_TA.
4. LoD = 3 × σ_noise / SN, где σ_noise = f(I_read, SNR_MEM).
5. DR = C_max / LoD, где C_max ≈ 10 × K_M для ферментов.
6. RP = 1 / CV.
7. HL = min(HL_BRE, HL_IM, HL_MEM).
8. Нормализация метрик к [0, 1] с поддержкой user-defined min/max.
9. Функция compute_data_completeness_vector(structure) → (vector, η, label).
   label ∈ {'full','partial','critical'} по порогам 0.9 / 0.6.

КОНФИГУРАЦИЯ:
- В settings.py: METRICS_VERSION = 'v1' | 'v2' (по умолчанию 'v1' для миграции).
- В паспорт проекта добавляется поле metrics_version.

КРИТЕРИИ ПРИЁМКИ:
[AC-1] metrics_v1.py не изменён, все старые тесты проходят.
[AC-2] metrics_v2.calculate_sensitivity возвращает произведение трёх компонентов.
[AC-3] metrics_v2.calculate_response_time учитывает диффузию через IM.
[AC-4] metrics_v2.calculate_stability включает ST_TA.
[AC-5] metrics_v2.calculate_lod использует σ_noise, а не фиксированное значение.
[AC-6] Нормализация: для "больше=лучше" x_norm = (x - x_min)/(x_max - x_min).
[AC-7] Нормализация: для "меньше=лучше" x_norm = (x_max - x)/(x_max - x_min).
[AC-8] data_completeness_vector возвращает η ∈ [0, 1] и корректный label.
[AC-9] Переключатель METRICS_VERSION корректно маршрутизирует вызовы.

ТЕСТЫ:
Unit-тесты:
- test_sensitivity_formula_v2
- test_response_time_with_diffusion
- test_response_time_dominant_bre_kinetics
- test_response_time_dominant_diffusion
- test_stability_includes_analyte
- test_stability_weak_link_principle
- test_lod_with_noise
- test_dynamic_range_from_michaelis_constant
- test_reproducibility_from_cv
- test_half_life_minimum_principle
- test_normalization_greater_is_better
- test_normalization_lesser_is_better
- test_normalization_user_defined_bounds
- test_data_completeness_full
- test_data_completeness_partial
- test_data_completeness_critical
- test_metrics_version_switch_v1
- test_metrics_version_switch_v2

Integration-тесты:
- test_end_to_end_metrics_calculation_glucose
- test_end_to_end_metrics_calculation_vegf
- test_regression_v1_results_unchanged

ОБРАТНАЯ СОВМЕСТИМОСТЬ:
- metrics_v1.py не трогать.
- Все существующие вызовы metrics.* идут через facade, который
  читает METRICS_VERSION и делегирует.
```

---

## 📋 ПРОМТ 1.4: Безопасность и аутентификация (Блок 12)

```
КОНТЕКСТ:
Сейчас все эндпоинты открыты. Нужно ввести JWT + RBAC, не сломав
существующие интеграции и тесты.

ЗАДАЧА:
Реализовать модуль auth/ с JWT, ролями и middleware.

ТРЕБОВАНИЯ:
1. Эндпоинты:
   - POST /api/auth/login → {access_token, refresh_token}
   - POST /api/auth/register (только для админов)
   - POST /api/auth/refresh
   - POST /api/auth/logout
2. Хранение паролей: bcrypt/argon2.
3. Роли RBAC:
   - Designer: синтез, анализ, экспорт, проекты.
   - KB_Admin: паспорта, версионирование, аудит, пользователи.
   - Validation_Specialist: валидация, импорт экспериментальных данных.
4. Middleware @require_role('Designer') для эндпоинтов.
5. Генерация API-ключей для интеграций:
   - POST /api/api-keys/generate
   - GET /api/api-keys
   - DELETE /api/api-keys/{id}
6. Rate Limiting через Redis:
   - 100 req/min для пользователей.
   - 10 синтезов/час.
7. Конфиг AUTH_MODE ∈ {'disabled','jwt'} (по умолчанию 'jwt').
   В режиме 'disabled' middleware пропускает все запросы (для тестов).
8. Сервисный пользователь 'system' для фоновых задач.

КРИТЕРИИ ПРИЁМКИ:
[AC-1] POST /api/auth/login с валидными credentials возвращает JWT.
[AC-2] POST /api/auth/login с неверным паролем → 401.
[AC-3] Запрос к защищённому эндпоинту без токена → 401.
[AC-4] Designer не может получить доступ к эндпоинтам KB_Admin.
[AC-5] KB_Admin может управлять пользователями.
[AC-6] API-ключ работает как альтернатива JWT.
[AC-7] Rate Limiting срабатывает после 100 запросов/мин.
[AC-8] AUTH_MODE='disabled' позволяет проходить без токена.
[AC-9] Все существующие тесты проходят в режиме AUTH_MODE='disabled'.

ТЕСТЫ:
Unit-тесты:
- test_login_success
- test_login_invalid_credentials
- test_token_refresh
- test_token_expiration
- test_password_hashing_bcrypt
- test_role_designer_permissions
- test_role_kb_admin_permissions
- test_role_validation_specialist_permissions
- test_api_key_generation
- test_api_key_revocation
- test_rate_limit_user
- test_rate_limit_synthesis
- test_auth_mode_disabled_bypass

Integration-тесты:
- test_full_auth_flow
- test_legacy_endpoints_work_with_auth_disabled
- test_service_account_for_background_tasks

Regression-тесты:
- test_existing_tests_pass_with_auth_disabled
- pytest --auth-mode=disabled запускает весь старый suite без изменений.

ОБРАТНАЯ СОВМЕСТИМОСТЬ:
- AUTH_MODE='disabled' по умолчанию в test-окружении.
- Все старые тесты используют фикстуру client с auth_mode='disabled'.
- Миграция существующих пользователей: скрипт создаёт дефолтного
  admin/admin с ролью KB_Admin.
```

---

## ⏸️ ПАУЗА ДЛЯ ПОДТВЕРЖДЕНИЯ

Это **сообщение 1 из 4**. В следующих сообщениях будут:
- **Сообщение 2:** Промты для Блоков 3, 5, 9, 6 (Многокритериальное ранжирование, Контур обучения, Проекты/Аудит, Онтология).
- **Сообщение 3:** Промты для Блоков 7, 14, 15, 16 (Валидация, Расширенная аналитика, Экспорт, Визуализация).
- **Сообщение 4:** Промты для Блоков 8, 10, 11, 13, 17, 18 (Интеграции, Шаблоны, NLP, Суррогатные модели, Производительность, PWA).

**Прежде чем продолжать, пожалуйста, подтвердите:**
1. Согласны ли вы с моей стратегией обратной совместимости (версионирование + feature flags)?
2. Как разрешить дубликаты между блоками (Парето/TOPSIS/Интервалы/Audit/Валидация)?
3. Верны ли мои предположения по 6 критическим конфликтам?

После подтверждения продолжу со следующими промтами.

# 📨 СООБЩЕНИЕ 2/4: ПРОМТЫ ДЛЯ БЛОКОВ 3, 5, 9, 6

Перед промтами — **прозрачная карта разрешения дубликатов**, которую я обещал.

---

## 🗺️ КАРТА РАЗРЕШЕНИЯ ДУБЛИКАТОВ (принцип Single Responsibility)

| Дубликат | Решение | Обоснование |
|---|---|---|
| **Парето/TOPSIS/Интервалы/ε-ограничения** (Блок 3 vs Блок 14) | Backend-алгоритмы → `domain/analytics.py` (Блок 3). UI-обёртки и scatter-plot → Блок 16. **Блок 14 упраздняется** как отдельная сущность. | Один источник истины для алгоритма, UI — тонкая надстройка. |
| **Audit Trail** (Блок 5 vs Блок 9) | `AuditLog` сервис и таблица живут в **Блоке 9**. Блок 5 использует его через `audit_service.log(...)`. | Аудит — часть подсистемы версионирования/трассируемости. |
| **Генерация протоколов валидации** (Блок 7) + **Экспорт в LIMS** (Блок 15) | Объединяются в модуль `validation/` с подмодулями: `generator.py` (Блок 7) и `exporters/{docx,xml,pdf}.py` (Блок 15). | Генерация и экспорт — две стороны одной доменной задачи. |
| **Визуализация компромиссов** (Блок 3 vs Блок 16) | Блок 3 = backend-алгоритмы. Блок 16 = frontend-компоненты (Radar, Heatmap, 3D). Чёткая граница: backend возвращает данные, frontend рендерит. | Разделение ответственности по слоям архитектуры. |
| **Интервальные оценки** (Блок 1 vs Блок 14) | Расчёт интервалов → `domain/metrics.py` (Блок 1). Отображение error bars → Блок 16. | Физика расчёта живёт рядом с другими метриками. |

**Итоговая структура модулей:**
```
domain/
├── metrics.py          # Блок 1 + 4 (метрики, κ, интервалы)
├── compatibility.py    # Блок 2 (валидаторы)
├── analytics.py        # Блок 3 (MCDA: МАИ, Парето, TOPSIS, ε, stress)
├── ontology.py         # Блок 6
├── validation/
│   ├── generator.py    # Блок 7
│   └── exporters/      # Блок 15
├── projects.py         # Блок 9 (Projects, EntityVersions)
└── audit.py            # Блок 9 (AuditLog — используется Блоком 5)

api/
├── auth/               # Блок 12
├── analytics.py        # Эндпоинты для Блока 3
└── integrations/       # Блок 8

frontend/
└── components/
    ├── mcda/           # Блок 16 (визуализация Блока 3)
    └── validation/     # UI Блока 7/15
```

---

## 📋 ПРОМТ 2.1: Многокритериальное ранжирование и анализ устойчивости (Блок 3)

```
КОНТЕКСТ:
Система использует жёстко заданные веса (SN=2.0, RP=1.5). Нужно
внедрить гибкие MCDA-методы, не ломая существующие расчёты.

ЗАДАЧА:
Реализовать модуль domain/analytics.py с 5 методами агрегации и
анализом устойчивости. Интегрировать через facade с переключателем
MCDA_METHOD ∈ {'weighted_sum','ahp','topsis','epsilon','pareto'}.

ТРЕБОВАНИЯ:

1. МЕТОД АНАЛИЗА ИЕРАРХИЙ (МАИ / AHP):
   - Функция ahp_calculate_weights(matrix: List[List[float]]) → weights: List[float]
   - Ввод: матрица парных сравнений A (n×n), шкала 1/3/5/7/9.
   - Вычисление: нормализованный собственный вектор для λ_max.
   - Функция ahp_check_consistency(matrix) → (CI, CR, is_consistent):
     * CI = (λ_max - n) / (n - 1)
     * CR = CI / RI, где RI — табличный случайный индекс.
     * is_consistent = (CR ≤ 0.1)
   - Эндпоинт: POST /api/analytics/ahp {matrix} → {weights, CI, CR, is_consistent}

2. ПОСТРОЕНИЕ ФРОНТА ПАРETO:
   - Функция pareto_frontier(structures: List[Structure], criteria: List[str]) → List[Structure]
   - Структура S_i доминирует S_j, если ∀k: S_i[k] ≥ S_j[k] ∧ ∃k: S_i[k] > S_j[k]
     (для критериев "меньше=лучше" инвертировать знак).
   - Возвращает только недоминируемые структуры.
   - Эндпоинт: GET /api/analytics/pareto?criteria=LoD,ST&limit=50

3. МЕТОД TOPSIS:
   - Функция topsis_rank(structures, criteria, weights) → List[(structure, C_i)]
   - Идеальное решение A+ = (max по "больше=лучше", min по "меньше=лучше").
   - Антиидеальное A- = наоборот.
   - D_i^+ = евклидово расстояние до A+, D_i^- = до A-.
   - C_i = D_i^- / (D_i^+ + D_i^-).
   - Сортировка по убыванию C_i.
   - Эндпоинт: GET /api/analytics/topsis?limit=10

4. МЕТОД ε-ОГРАНИЧЕНИЙ:
   - Функция epsilon_constraints_optimize(structures, objective, constraints) → List[Structure]
   - objective: какой критерий максимизировать.
   - constraints: dict {criterion: (op, value)}, например {'LoD': ('<', 10), 'TR': ('<', 30)}.
   - Фильтрация + сортировка по objective.
   - Эндпоинт: POST /api/analytics/epsilon-constraints {objective, constraints, limit}

5. СТРЕСС-ТЕСТИРОВАНИЕ (StabilityAnalysis):
   - Класс StabilityAnalysis с методом run(structures, weights, n_simulations=1000):
     * Для каждой симуляции: w_i' = w_i * (1 + δ_i), δ_i ~ U(-0.2, 0.2),
       ренормализация весов.
     * Пересчёт Score и рангов для всех структур.
     * Структура устойчива, если её ранг ∈ top-K в ≥ 80% сценариев.
   - Возвращает: {structure_id: {rank_distribution, stability_label, mean_rank}}
     где stability_label ∈ {'stable','moderate','unstable'} по порогам 80%/60%.
   - Эндпоинт: GET /api/analytics/stability?top_k=10&n_simulations=1000

6. ЧУВСТВИТЕЛЬНОСТЬ К НЕОПРЕДЕЛЁННОСТИ:
   - Метод sensitivity_to_uncertainty(structures):
     * Для параметров с reliability_category ∈ {'low','medium'} моделировать
       пессимистичные значения (граница типичного диапазона).
     * Пересчёт Score и рангов.
     * Структуры, чей ранг снижается > 5 позиций → маркер 'requires_experimental_check'.
   - Эндпоинт: GET /api/analytics/sensitivity

7. FACADE И МИГРАЦИЯ:
   - analytics_service.calculate_score(structures, method, **kwargs) → результат.
   - При method='weighted_sum' используется СТАРАЯ логика с жёсткими весами.
   - Конфиг MCDA_METHOD по умолчанию = 'weighted_sum' (для обратной совместимости).

КРИТЕРИИ ПРИЁМКИ:
[AC-1]  Матрица AHP 3×3 с равными сравнениями → веса [0.333, 0.333, 0.333].
[AC-2]  Противоречивая матрица (CR > 0.1) → is_consistent=False.
[AC-3]  Парето-фронт для 100 структур возвращает ≤ 20 недоминируемых.
[AC-4]  Структура, доминируемая другой, НЕ попадает в Парето-фронт.
[AC-5]  TOPSIS: для 2 структур, где одна лучше по всем критериям,
        она получает C_i ближе к 1.
[AC-6]  ε-ограничения: при LoD < 10 пМ все возвращённые структуры
        удовлетворяют ограничению.
[AC-7]  Stress-test: структура с большим отрывом от остальных → stable.
[AC-8]  Stress-test: структура на границе top-K → moderate/unstable.
[AC-9]  Sensitivity: структура с low-reliability параметрами → requires_experimental_check.
[AC-10] MCDA_METHOD='weighted_sum' возвращает те же результаты, что и старый код.

ТЕСТЫ:
Unit-тесты:
- test_ahp_equal_comparisons
- test_ahp_strong_preference
- test_ahp_consistency_check_pass
- test_ahp_consistency_check_fail
- test_ahp_eigenvector_normalization
- test_pareto_frontier_simple_case
- test_pareto_frontier_no_dominated_included
- test_pareto_frontier_empty_input
- test_topsis_two_structures_clear_winner
- test_topsis_multiple_structures_ranking
- test_topsis_ideal_antiideal_calculation
- test_epsilon_constraints_filters_correctly
- test_epsilon_constraints_respects_all_limits
- test_stress_test_stable_structure
- test_stress_test_unstable_structure
- test_stress_test_reproducibility (фиксированный seed)
- test_sensitivity_detects_low_reliability
- test_sensitivity_threshold_5_positions
- test_facade_weighted_sum_backward_compatible
- test_facade_method_switching

Integration-тесты:
- test_full_mcda_pipeline_glucose_biosensor
- test_full_mcda_pipeline_vegf_biosensor
- test_pareto_visualization_data_format

Regression-тесты:
- test_existing_score_calculation_unchanged
- test_existing_top_k_results_match (при MCDA_METHOD='weighted_sum')

ОБРАТНАЯ СОВМЕСТИМОСТЬ:
- Старые эндпоинты /api/synthesize/top_k продолжают работать.
- MCDA_METHOD='weighted_sum' — дефолт, эквивалентен старому поведению.
- Новые эндпоинты — аддитивные, не меняют существующие.
```

---

## 📋 ПРОМТ 2.2: Контур обучения и ролевая модель UI (Блок 5)

```
КОНТЕКСТ:
Система работает в режиме "одноразового" синтеза. Нужен механизм
обратной связи от экспериментов + разделение UI по ролям.
(Аудит и RBAC — в Блоках 9 и 12, здесь только UI-маршруты и Feedback Loop.)

ЗАДАЧА:
Реализовать Feedback Loop сервис и ролевые UI-маршруты.

ТРЕБОВАНИЯ:

1. FEEDBACK LOOP (домен: domain/feedback.py):
   - Эндпоинт POST /api/validation/import-results:
     * Принимает JSON: {structure_id, experimental_metrics: {LoD, SN, TR, ST, ...},
       protocol_id, operator, date}
     * Сохраняет в таблицу ExperimentalResults.
     * Автоматически повышает reliability_category компонентов структуры:
       - Если |Score_calc - Score_exp| / Score_exp < 0.15 → 'high'
       - Если < 0.30 → 'medium'
       - Иначе остаётся без изменения.
     * Запускает переобучение суррогатных моделей (Блок 13) при накоплении
       ≥ 10 новых валидированных структур.
     * Возвращает: {updated_components: [...], model_retrained: bool, new_kappa_values: {...}}

   - Эндпоинт GET /api/validation/discrepancies:
     * Возвращает список структур с расхождением расчётных и фактических метрик.
     * Сортировка по убыванию относительной ошибки.
     * Фильтры: by_analyte, by_date_range, by_min_error.

   - Эндпоинт GET /api/validation/learning-curve:
     * Возвращает данные для графика: как точность предсказания Score
       растёт с числом валидированных структур.
     * Ожидается: корреляция с 0.65 → 0.85 после 20 валидаций (Тест-кейс 5).

2. РОЛЕВАЯ МОДЕЛЬ UI (frontend):
   - Три маршрута с редиректом по роли:
     * /designer/* → Designer (синтез, анализ, проекты)
     * /kb-admin/* → KB Admin (паспорта, онтология, аудит)
     * /validation/* → Validation Specialist (валидация, импорт, расхождения)
   - Компонент <RoleGuard requiredRole="Designer"> для защиты маршрутов.
   - Навигационное меню адаптируется под роль.
   - Пользователь с несколькими ролями видит объединённое меню.

3. ИНТЕГРАЦИЯ С AUDIT (Блок 9):
   - Каждое действие Feedback Loop логируется через audit_service.log(...):
     * action='VALIDATE', entity_type='Structure', old_value/new_value.
   - Аудит вызывается прозрачно, без дублирования кода.

КРИТЕРИИ ПРИЁМКИ:
[AC-1]  POST /api/validation/import-results сохраняет экспериментальные данные.
[AC-2]  При успешной валидации (ошибка < 15%) reliability_category → 'high'.
[AC-3]  Audit-запись создаётся для каждого импорта.
[AC-4]  GET /api/validation/discrepancies возвращает отсортированный список.
[AC-5]  GET /api/validation/learning-curve возвращает данные для ≥ 1 точки.
[AC-6]  Designer видит только /designer/* маршруты.
[AC-7]  KB Admin видит /kb-admin/* и не видит /validation/*.
[AC-8]  Validation Specialist видит /validation/* и не видит /kb-admin/*.
[AC-9]  Пользователь с ролями [Designer, Validation] видит оба меню.
[AC-10] После 20 валидаций корреляция Score_calc vs Score_exp ≥ 0.85.

ТЕСТЫ:
Unit-тесты:
- test_import_results_saves_to_db
- test_reliability_upgrade_high_accuracy
- test_reliability_upgrade_medium_accuracy
- test_reliability_no_change_low_accuracy
- test_discrepancies_sorted_by_error
- test_discrepancies_filter_by_analyte
- test_learning_curve_calculation
- test_role_guard_allows_correct_role
- test_role_guard_denies_incorrect_role
- test_role_guard_multi_role_user
- test_audit_log_called_on_import

Integration-тесты:
- test_full_feedback_loop_flow
- test_feedback_loop_triggers_model_retrain_after_10_structures
- test_learning_curve_reaches_0.85_after_20_validations (Тест-кейс 5)

Regression-тесты:
- test_existing_synthesis_not_affected_by_feedback_module
- test_existing_endpoints_still_work

ОБРАТНАЯ СОВМЕСТИМОСТЬ:
- Новые эндпоинты — аддитивные.
- Существующие данные не модифицируются автоматически.
- UI-маршруты не конфликтуют со старыми (новые префиксы /designer, /kb-admin, /validation).
```

---

## 📋 ПРОМТ 2.3: Управление проектами, версионирование и аудит (Блок 9)

```
КОНТЕКСТ:
Система работает в режиме "одноразового" синтеза. Нужны проекты,
версионирование паспортов и единый AuditLog (объединяет Блоки 5 и 9).

ЗАДАЧА:
Реализовать подсистему Projects + EntityVersions + AuditLog.

ТРЕБОВАНИЯ:

1. ТАБЛИЦА Projects:
   - project_id UUID PK
   - name VARCHAR(255) NOT NULL
   - created_at TIMESTAMP
   - user_id UUID FK → Users
   - settings JSON (weights, constraints, analyte, profile, metrics_version)
   - status ENUM('active','paused','completed') DEFAULT 'active'
   - last_synthesis_result_id UUID NULL

2. ЭНДПОИНТЫ Projects:
   - POST   /api/projects                       → создать
   - GET    /api/projects                       → список (фильтр по user_id, status)
   - GET    /api/projects/{id}                  → детали
   - PUT    /api/projects/{id}/settings         → обновить настройки
   - POST   /api/projects/{id}/pause            → пауза
   - POST   /api/projects/{id}/resume           → возобновление
   - DELETE /api/projects/{id}                  → удаление (soft delete)

3. ТАБЛИЦА EntityVersions (для TA, BRE, IM, MEM):
   - version_id UUID PK
   - entity_type ENUM('TA','BRE','IM','MEM')
   - entity_id UUID
   - version_number INT
   - timestamp TIMESTAMP
   - user_id UUID
   - data JSON (полный снимок паспорта)
   - source VARCHAR(255)
   - reliability_category ENUM('high','medium','low')
   - UNIQUE(entity_type, entity_id, version_number)

4. ВЕРСИОНИРОВАНИЕ:
   - При каждом UPDATE паспорта автоматически создаётся новая версия.
   - Middleware VersioningMiddleware перехватывает UPDATE-запросы.
   - Эндпоинт POST /api/entities/{type}/{id}/revert/{version} — откат.
   - Эндпоинт GET /api/entities/{type}/{id}/versions — история.

5. ТАБЛИЦА AuditLog (ОБЪЕДИНЁННАЯ из Блоков 5 и 9):
   - log_id UUID PK
   - timestamp TIMESTAMP
   - user_id UUID
   - action ENUM('CREATE','UPDATE','DELETE','SYNTHESIZE','VALIDATE','REVERT')
   - entity_type VARCHAR(50)
   - entity_id UUID
   - old_value JSON
   - new_value JSON
   - project_id UUID NULL (для привязки к проекту)
   - Индексы: (user_id), (action), (timestamp), (entity_type, entity_id)

6. СЕРВИС AuditService:
   - audit_service.log(action, entity_type, entity_id, old_value, new_value, user_id, project_id)
   - Используется ВСЕМИ модулями (паспорта, проекты, валидация, синтез).

7. ЭНДПОИНТ AuditLog:
   - GET /api/audit-log?user_id=&action=&from=&to=&entity_type=&limit=&offset=
   - Возвращает отсортированные по timestamp записи.
   - Экспорт в CSV: GET /api/audit-log/export?format=csv&...

КРИТЕРИИ ПРИЁМКИ:
[AC-1]  Создание проекта сохраняет settings как JSON.
[AC-2]  Загрузка проекта восстанавливает все настройки.
[AC-3]  Пауза/возобновление меняют status корректно.
[AC-4]  UPDATE паспорта создаёт новую версию с инкрементом version_number.
[AC-5]  Откат к версии N восстанавливает data из этой версии.
[AC-6]  История версий содержит все снимки.
[AC-7]  AuditService.log создаёт запись в AuditLog.
[AC-8]  GET /api/audit-log фильтрует по всем параметрам.
[AC-9]  Экспорт в CSV содержит все поля.
[AC-10] Все действия (CREATE/UPDATE/DELETE/VALIDATE/REVERT) логируются.

ТЕСТЫ:
Unit-тесты:
- test_project_create
- test_project_list_filter_by_status
- test_project_settings_update
- test_project_pause_resume
- test_project_soft_delete
- test_entity_version_auto_increment
- test_entity_version_unique_constraint
- test_entity_revert_to_version
- test_entity_versions_history
- test_audit_log_create
- test_audit_log_filter_by_user
- test_audit_log_filter_by_action
- test_audit_log_filter_by_date_range
- test_audit_log_csv_export

Integration-тесты:
- test_full_project_lifecycle
- test_passport_update_creates_version_and_audit
- test_revert_creates_audit_entry
- test_concurrent_project_edits

Regression-тесты:
- test_existing_passport_endpoints_still_work
- test_existing_synthesis_not_affected

ОБРАТНАЯ СОВМЕСТИМОСТЬ:
- Новые таблицы добавляются миграцией Alembic.
- Существующие таблицы не модифицируются (кроме Блока 1, который уже добавляет поля).
- Старые эндпоинты не требуют project_id (он опционален).
- AuditService.log вызывается опционально — если user_id не передан, пишется 'system'.
```

---

## 📋 ПРОМТ 2.4: Онтологическая модель и семантический поиск (Блок 6)

```
КОНТЕКСТ:
База данных реляционная, связи только через FK. Нужна онтология
предметной области для семантического поиска и автодополнения.

ЗАДАЧА:
Реализовать модуль domain/ontology.py с таксономией и SPARQL-поиском.

ТРЕБОВАНИЯ:

1. ОНТОЛОГИЯ (OWL-совместимая):
   - Классы верхнего уровня:
     * Analyte → {Carbohydrate, Protein, NucleicAcid, Ion, SmallMolecule}
     * BioRecognitionElement → {Enzyme, Antibody, Aptamer, SyntheticReceptor}
     * ImmobilizationMethod → {Covalent, Adsorption, Encapsulation, PolymerLayer}
     * MemristiveElement → {Oxide, Organic, GrapheneOxide, Perovskite, SiNanowire}
   - Связи:
     * analyte_detected_by → BRE (например, глюкоза → GOx, GDH, аптамеры)
     * bre_compatible_with → IM (ферменты → хитозан, нафион)
     * im_compatible_with → MEM (силаны → оксиды)
   - Хранение: таблица OntologyClasses + OntologyRelations + экспорт в OWL.

2. ЭНДПОИНТЫ:
   - POST /api/ontology/search:
     * Принимает: {query: str, class_filter: Optional[str], limit: int}
     * Возвращает релевантные компоненты с таксономическим положением.
     * Поиск по: названию, синонимам, описанию, родительским классам.
     * Используется для автодополнения форм.
   - GET /api/ontology/siblings/{class_id}:
     * Возвращает компоненты того же класса (для рекомендаций).
   - GET /api/ontology/compatible-bre?analyte_id=:
     * Возвращает BRE, совместимые с данным аналитом (через связь analyte_detected_by).
   - GET /api/ontology/export?format=owl:
     * Экспорт онтологии в OWL-файл.
   - POST /api/ontology/sparql:
     * Выполнение SPARQL-запросов к онтологии (опционально, через rdflib).

3. ИНТЕГРАЦИЯ С СУЩЕСТВУЮЩИМИ ТАБЛИЦАМИ:
   - В таблицы Analytes, BioRecognitionLayers и т.д. добавить поле
     ontology_class_id UUID FK → OntologyClasses (nullable для миграции).
   - Скрипт первичного заполнения: связывает существующие записи с классами
     по ключевым словам (например, "GOx" → класс Enzyme → Oxidoreductase).

4. ИСПОЛЬЗОВАНИЕ В СИНТЕЗЕ:
   - При выборе аналита "глюкоза" → автоподстановка BRE: GOx, GDH, аптамеры.
   - При выборе BRE → фильтрация IM по совместимости.
   - Снижение пространства поиска на 40-60%.

КРИТЕРИИ ПРИЁМКИ:
[AC-1]  POST /api/ontology/search с query="глюкоза" возвращает глюкозу + моносахариды.
[AC-2]  Поиск по "GOx" возвращает глюкозооксидазу + класс Oxidoreductase.
[AC-3]  GET /api/ontology/compatible-bre?analyte_id=glucose возвращает GOx, GDH, аптамеры.
[AC-4]  OWL-экспорт валидируется против W3C-схемы.
[AC-5]  SPARQL-запрос "SELECT ?bre WHERE { ?bre rdf:type :Enzyme }" возвращает все ферменты.
[AC-6]  Автодополнение в UI работает с задержкой < 200 мс.
[AC-7]  Миграция связывает ≥ 80% существующих записей с классами.
[AC-8]  Синтез с онтологией сокращает пространство поиска на ≥ 40%.

ТЕСТЫ:
Unit-тесты:
- test_ontology_search_by_name
- test_ontology_search_by_synonym
- test_ontology_search_by_parent_class
- test_ontology_search_with_class_filter
- test_ontology_siblings
- test_ontology_compatible_bre_for_glucose
- test_ontology_compatible_bre_for_vegf
- test_ontology_owl_export_valid
- test_ontology_sparql_query
- test_ontology_autocomplete_performance

Integration-тесты:
- test_ontology_integration_with_synthesis
- test_ontology_migration_links_existing_records
- test_ontology_reduces_search_space

Regression-тесты:
- test_existing_synthesis_works_without_ontology
- test_existing_passport_endpoints_not_broken

ОБРАТНАЯ СОВМЕСТИМОСТЬ:
- ontology_class_id — nullable, старые записи работают без него.
- Онтология — опциональный слой, синтез работает и без неё.
- Новые эндпоинты — аддитивные.
```

---

## ⏸️ ПАУЗА ПЕРЕД СООБЩЕНИЕМ 3/4

Это **сообщение 2 из 4**. В следующем сообщении будут промты для:
- **Блок 7 + 15 (объединённые):** Генерация и экспорт планов валидации
- **Блок 14 + 3 (backend-часть):** Расширенная аналитика (если останутся детали)
- **Блок 16:** Визуализация компромиссов (frontend)

**Вопросы для уточнения перед продолжением:**
1. Для Блока 7/15: какие конкретно LIMS-системы приоритетны для экспорта (SampleManager, LabWare, Benchling — все сразу или по приоритету)?
2. Для Блока 16 (визуализация): использовать Recharts (как указано в спецификации) или Plotly для всех графиков единообразно?
3. Для Блока 6 (онтология): хранить онтологию в отдельной графовой БД (Neo4j) или в реляционной + rdflib (проще, но медленнее на больших объёмах)?

Если нет предпочтений — принимаю решения сам:
1. Поддержка всех трёх LIMS через адаптеры, приоритет — Benchling (самый популярный API).
2. Recharts для стандартных графиков, Plotly только для 3D.
3. Реляционная БД + rdflib (проще в деплое, достаточно для текущих объёмов).

Подтвердите или скорректируйте — и я продолжу с сообщением 3/4.

# 📨 СООБЩЕНИЕ 3/4: ПРОМТЫ ДЛЯ БЛОКОВ 7/15, 10, 16, 13

Продолжаю с учётом подтверждённых решений (Benchling приоритет, Recharts+Plotly, реляционная БД+rdflib).

---

## 📋 ПРОМТ 3.1: Генерация и экспорт планов валидации (Блок 7 + 15 объединённые)

```
КОНТЕКСТ:
Система не генерирует протоколы экспериментальной проверки. Нужно
реализовать модуль validation/ с генератором по ICH Q2(R2) и ISO 5725-1
+ экспортом в DOCX/XML/PDF + интеграцией с LIMS (приоритет — Benchling).

ЗАДАЧА:
Реализовать модуль domain/validation/ с подмодулями:
- generator.py — генерация плана валидации
- exporters/docx.py — экспорт в DOCX
- exporters/xml.py — экспорт в XML для LIMS
- exporters/pdf.py — экспорт в PDF
- lims_adapters/{benchling,labware,sample_manager}.py — адаптеры LIMS

ТРЕБОВАНИЯ:

1. ГЕНЕРАТОР ПРОТОКОЛОВ (generator.py):
   - Класс ValidationProtocolGenerator с методом generate(structure_id) → Protocol:
     * Специфичность (Specificity):
       - Матрица интерферентов: структурно близкие белки (PlGF, PDGF, bFGF для VEGF)
         + компоненты матрикса (альбумин, IgG в концентрациях сыворотки).
       - Критерий: отсутствие перекрёстного сигнала (> 2% от целевого).
       - Минимум 10 интерферентов × 3 концентрации.
     * Правильность (Trueness):
       - 5 уровней концентраций (например, 10, 50, 200, 500, 1000 пг/мл для VEGF).
       - n = 3 повторения на уровень.
       - Референсный метод (ELISA с аттестованной концентрацией).
       - Критерий: recovery 95–105% (средние), 90–110% (граничные).
     * Прецизионность (Precision):
       - Повторяемость (внутридневная): n = 6, CV < 7%.
       - Воспроизводимость (междневная): 3 оператора, 5 дней, n = 2, CV < 10%.
     * Линейность (Linearity):
       - Диапазон: LoD → C_max (например, 5–2000 пг/мл).
       - Минимум 7 уровней, по 3 повторения.
       - Критерий: R² > 0.99, остаточные отклонения ±15%.
     * LoD/LoQ:
       - Серийные разведения: 1, 2, 5, 10 пг/мл.
       - S/N = 3 для LoD, 10 для LoQ.
       - n = 10 на низком уровне.
     * Робастность (Robustness):
       - pH: ±0.5 единицы.
       - Температура: ±5°C.
       - Ионная сила: ±50 мМ NaCl.
       - Критерий: изменение сигнала < 5%.

2. ЭКСПОРТ В DOCX (exporters/docx.py):
   - Библиотека python-docx.
   - Шаблон: заголовок, таблица матрицы экспериментов, критерии приёмки, подписи.
   - Метод export_to_docx(protocol: Protocol) → bytes.
   - Эндпоинт: GET /api/validation/protocol/{structure_id}?format=docx

3. ЭКСПОРТ В XML (exporters/xml.py):
   - Формат, совместимый с LIMS (Benchling, LabWare, SampleManager).
   - Структура: <ValidationProtocol><Experiment><Parameter>...</Parameter></Experiment></ValidationProtocol>
   - Метод export_to_xml(protocol: Protocol) → bytes.
   - Эндпоинт: GET /api/validation/protocol/{structure_id}?format=xml

4. ЭКСПОРТ В PDF (exporters/pdf.py):
   - Библиотека reportlab или weasyprint.
   - Метод export_to_pdf(protocol: Protocol) → bytes.
   - Эндпоинт: GET /api/validation/protocol/{structure_id}?format=pdf

5. АДАПТЕРЫ LIMS (lims_adapters/):
   - Базовый класс LIMSAdapter с методами:
     * authenticate(api_key) → token
     * create_experiment(protocol: Protocol) → experiment_id
     * upload_results(experiment_id, results: dict) → bool
   - Адаптер BenchlingAdapter (приоритетный):
     * REST API v1, аутентификация через API-ключ.
     * Маппинг полей: protocol → Benchling Experiment schema.
   - Адаптеры LabWareAdapter, SampleManagerAdapter — заглушки с интерфейсом.
   - Эндпоинт: POST /api/integrations/lims/upload-protocol
     {structure_id, lims_type: 'benchling'|'labware'|'sample_manager', api_key}

6. ИМПОРТ ЭКСПЕРИМЕНТАЛЬНЫХ ДАННЫХ:
   - Эндпоинт POST /api/validation/import-results (уже описан в Блоке 5):
     * Принимает JSON с фактическими метриками.
     * Запускает калибровку моделей (Блок 13) и обновление reliability (Блок 1).

КРИТЕРИИ ПРИЁМКИ:
[AC-1]  Генератор создаёт протокол со всеми 6 валидационными характеристиками.
[AC-2]  Матрица интерферентов содержит ≥ 10 позиций × 3 концентрации.
[AC-3]  Уровни правильности: 5 концентраций, n=3.
[AC-4]  Прецизионность: повторяемость n=6, воспроизводимость 3×5×2.
[AC-5]  Линейность: ≥ 7 уровней, R² > 0.99.
[AC-6]  LoD/LoQ: S/N = 3/10, n=10.
[AC-7]  Робастность: 3 вариации (pH, T, ионная сила).
[AC-8]  DOCX-экспорт открывается в MS Word без ошибок.
[AC-9]  XML-экспорт валидируется против XSD-схемы LIMS.
[AC-10] PDF-экспорт содержит все разделы.
[AC-11] BenchlingAdapter успешно создаёт эксперимент (mock-тест).
[AC-12] Все эндпоинты возвращают HTTP 200 с корректным Content-Type.

ТЕСТЫ:
Unit-тесты:
- test_protocol_generation_specificity
- test_protocol_generation_trueness
- test_protocol_generation_precision
- test_protocol_generation_linearity
- test_protocol_generation_lod_loq
- test_protocol_generation_robustness
- test_docx_export_contains_all_sections
- test_xml_export_validates_against_xsd
- test_pdf_export_renders_correctly
- test_benchling_adapter_authenticate
- test_benchling_adapter_create_experiment
- test_benchling_adapter_upload_results
- test_labware_adapter_interface
- test_sample_manager_adapter_interface

Integration-тесты:
- test_full_validation_protocol_generation_glucose
- test_full_validation_protocol_generation_vegf
- test_benchling_integration_mock
- test_xml_import_to_lims_mock

Regression-тесты:
- test_existing_synthesis_not_affected
- test_existing_endpoints_still_work

ОБРАТНАЯ СОВМЕСТИМОСТЬ:
- Новые эндпоинты — аддитивные.
- Модуль validation/ не влияет на существующий код.
- LIMS-адаптеры опциональны, работают только при наличии api_key.
```

---

## 📋 ПРОМТ 3.2: Шаблоны архитектур, профили задач и тест-кейсы (Блок 10)

```
КОНТЕКСТ:
Пользователь вручную задаёт все параметры синтеза. Нужны предустановленные
профили для типовых задач + автоматические тесты из статьи.

ЗАДАЧА:
Реализовать библиотеку профилей задач (JSON/YAML) + тест-кейсы для верификации.

ТРЕБОВАНИЯ:

1. БИБЛИОТЕКА ПРОФИЛЕЙ (configs/profiles/):
   - Формат: YAML-файлы с полями:
     * profile_id: str
     * name: str
     * analyte_type: str
     * application_class: str ('PoC'|'LoC'|'Clinical_Diagnostics')
     * weights: dict {criterion: weight}
     * constraints: dict {criterion: {operator, value}}
     * recommended_components: dict {layer: [component_ids]}
     * description: str

   - Профиль 1: "Глюкозный биосенсор для PoC-диагностики диабета"
     * TA = глюкоза
     * weights: {LoD: 0.35, SN: 0.28, TR: 0.15, ST: 0.12, PC: 0.10}
     * constraints: {pH: {min: 5.0, max: 8.0}, T_exp: {max: 40}, PC: {max: 10}}
     * recommended: {BRE: ['GOx','GDH','glucose_aptamer'], IM: ['chitosan','nafion','PPy','PEDOT:PSS'], MEM: ['HfO2','TiO2','GO','ZnO']}

   - Профиль 2: "VEGF-биосенсор для клинической онкодиагностики"
     * TA = VEGF
     * weights: {LoD: 0.40, SP: 0.25, DR: 0.15, RP: 0.12, TR: 0.08}
     * constraints: {pH: {min: 6.5, max: 7.8}, LoD: {max: 10}, DR: {min: 10, max: 1000}}
     * recommended: {BRE: ['mAb_VEGF','RNA_aptamer_VEGF','nanoAb_VEGF'], IM: ['APTES','MPTMS','GPTMS','PEG_linker','chitosan'], MEM: ['Si-NW_50nm','graphene','HfO2','TiO2']}

   - Профиль 3: "Экологический мониторинг тяжёлых металлов"
     * TA = ['Pb2+','Cd2+','Hg2+']
     * weights: {ST: 0.35, DR: 0.25, SN: 0.20, TR: 0.10, PC: 0.10}
     * constraints: {T_exp: {min: -10, max: 50}}
     * recommended: {BRE: ['DNA_aptamer_Pb','peptide_Hg'], IM: ['self_assembled_monolayer','polymer_membrane'], MEM: ['graphene','Au_nanoparticles']}

2. ЭНДПОИНТЫ API:
   - GET /api/profiles → список профилей с описанием.
   - GET /api/profiles/{profile_id} → детали профиля.
   - POST /api/synthesize/from-profile {profile_id} → запуск синтеза с настройками профиля.
   - POST /api/profiles (только для KB_Admin) → создание нового профиля.
   - PUT /api/profiles/{profile_id} (только для KB_Admin) → редактирование.

3. FRONTEND:
   - На странице AnalysisPage добавить выпадающий список "Quick Start" с профилями.
   - При выборе профиля:
     * Автоматически заполняются веса критериев.
     * Заполняются ограничения.
     * Предлагаются релевантные компоненты (из recommended_components + онтология).
   - Кнопка "Synthesize from Profile" запускает синтез.

4. РЕДАКТОР ПРОФИЛЕЙ (для KB_Admin):
   - Форма с полями: name, analyte_type, application_class.
   - Компонент настройки весов через МАИ (Блок 3).
   - Компонент задания ограничений (таблица criterion/operator/value).
   - Мультивыбор рекомендованных компонентов (с поиском через онтологию).
   - Сохранение в таблицу TaskProfiles (создаётся миграцией).

5. ТЕСТ-КЕЙСЫ ДЛЯ ВЕРИФИКАЦИИ СИСТЕМЫ (tests/test_cases/):
   - Тест-кейс 1: Глюкозный биосенсор
     * Вход: профиль "Глюкозный биосенсор для PoC", БЗ: 1 TA, 8 BRE, 15 IM, 12 MEM.
     * Ожидание: после фильтрации ~216 комбинаций (15% от 1440).
     * Top-5 структур:
       - S1: GOx(Aspergillus)/Chitosan/HfO2, LoD=0.08 мМ, SN=42.5 мкА/мМ, TR=28 с, ST=120 циклов, Score=0.832, κ=0.78
       - S2: GDH-FAD/Nafion/TiO2, LoD=0.12 мМ, SN=38.2 мкА/мМ, TR=22 с, ST=95 циклов, Score=0.809, κ=0.72
       - S3: GOx(Penicillium)/PEDOT:PSS/GO, LoD=0.15 мМ, SN=35.8 мкА/мМ, TR=35 с, ST=85 циклов, Score=0.785, κ=0.81
       - S4: Aptamer/PEG-hydrogel/ZnO, LoD=0.18 мМ, SN=28.5 мкА/мМ, TR=18 с, ST=65 циклов, Score=0.768, κ=0.65
       - S5: GDH-PQQ/PPy/Ta2O5, LoD=0.22 мМ, SN=31.2 мкА/мМ, TR=40 с, ST=110 циклов, Score=0.752, κ=0.74
     * Проверка: S1 на первом месте, все κ ≥ 0.65, ранг S1 в top-10 в ≥ 85% сценариев.

   - Тест-кейс 2: VEGF-биосенсор
     * Вход: профиль "VEGF-биосенсор для клинической онкодиагностики", БЗ: 1 TA, 6 BRE, 12 IM, 10 MEM.
     * Ожидание: после фильтрации ~98 комбинаций (13.6% от 720).
     * Top-5 структур:
       - S1: mAb(high_affinity)/APTES/Si-NW_50nm, LoD=2.5 пг/мл, DR=10–2000 пг/мл, SP=96.5%, RP(CV)=4.2%, Score=0.887, κ=0.82
       - S2: nanoAb/MPTMS/graphene, LoD=1.8 пг/мл, DR=5–1500 пг/мл, SP=94.8%, RP(CV)=5.8%, Score=0.871, κ=0.68
       - S3: RNA_aptamer/PEG_linker/Si-NW_100nm, LoD=4.2 пг/мл, DR=20–3000 пг/мл, SP=92.3%, RP(CV)=6.5%, Score=0.845, κ=0.71
       - S4: mAb(medium_affinity)/chitosan/HfO2, LoD=8.5 пг/мл, DR=50–5000 пг/мл, SP=95.2%, RP(CV)=5.1%, Score=0.823, κ=0.79
       - S5: RNA_aptamer/GPTMS/TiO2, LoD=12.3 пг/мл, DR=100–10000 пг/мл, SP=89.7%, RP(CV)=7.2%, Score=0.798, κ=0.64
     * Проверка: S1 имеет LoD < 10 пг/мл, все SP ≥ 89%, ранг S1 в top-10 в ≥ 85% сценариев.

   - Тест-кейс 3: Верификация двухэтапной фильтрации
     * Проверка: ни одна из 47 reference-структур не отброшена (0% ложных отсечений).
     * Проверка: фильтрация отсекает 85–87% пространства.

   - Тест-кейс 4: Верификация учёта неопределённости
     * Сравнение ранжирования с κ и без κ на 30 валидированных структурах.
     * Ожидание: средняя относительная ошибка Score снижается с 34% до 18%.
     * Ожидание: доля подтверждённых top-5 структур растёт с 52% до 78%.

   - Тест-кейс 5: Верификация контура обучения
     * После валидации 20 структур: корреляция Score_calc vs Score_exp возрастает с 0.65 до 0.85.
     * Доля структур, требующих итерационного уточнения через DoE, снижается с 45% до 18%.

КРИТЕРИИ ПРИЁМКИ:
[AC-1]  GET /api/profiles возвращает ≥ 3 профиля.
[AC-2]  POST /api/synthesize/from-profile запускает синтез с настройками профиля.
[AC-3]  Quick Start в UI заполняет веса и ограничения.
[AC-4]  Редактор профилей позволяет создать новый профиль.
[AC-5]  Тест-кейс 1: S1 на первом месте, все κ ≥ 0.65.
[AC-6]  Тест-кейс 2: S1 имеет LoD < 10 пг/мл, все SP ≥ 89%.
[AC-7]  Тест-кейс 3: 0% ложных отсечений reference-структур.
[AC-8]  Тест-кейс 4: ошибка Score снижается с 34% до 18%.
[AC-9]  Тест-кейс 5: корреляция растёт с 0.65 до 0.85.
[AC-10] Все тест-кейсы автоматизированы и запускаются через pytest.

ТЕСТЫ:
Unit-тесты:
- test_profile_loading_from_yaml
- test_profile_validation
- test_synthesize_from_profile_endpoint
- test_quick_start_ui_component
- test_profile_editor_form

Integration-тесты:
- test_test_case_1_glucose_biosensor
- test_test_case_2_vegf_biosensor
- test_test_case_3_filtering_verification
- test_test_case_4_uncertainty_verification
- test_test_case_5_learning_loop_verification

Regression-тесты:
- test_existing_manual_synthesis_still_works
- test_existing_endpoints_not_affected

ОБРАТНАЯ СОВМЕСТИМОСТЬ:
- Профили — опциональный слой, ручной синтез работает как раньше.
- Новые эндпоинты — аддитивные.
- Таблица TaskProfiles создаётся миграцией, не влияет на старые таблицы.
```

---

## 📋 ПРОМТ 3.3: Визуализация компромиссов и интерактивный анализ (Блок 16)

```
КОНТЕКСТ:
Визуализация ограничена гистограммой и таблицей. Нужны интерактивные
инструменты для анализа компромиссов и чувствительности.
(Backend-алгоритмы — в Блоке 3, здесь — frontend-компоненты.)

ЗАДАЧА:
Реализовать frontend-компоненты для визуализации MCDA-результатов.
Библиотеки: Recharts (стандартные графики), Plotly (3D).

ТРЕБОВАНИЯ:

1. РАДАРНЫЕ ДИАГРАММЫ (Radar Charts, Recharts):
   - Компонент <RadarChartComparison structures={topK} metrics={groups}>:
     * Группы метрик:
       - Функциональные: SN, LoD, DR
       - Надёжность: ST, RP, HL
       - Совместимость и эксплуатация: BC, PC, технологическая реализуемость
     * Интерактивное переключение между структурами из top-K.
     * Tooltip при наведении: название структуры, значение метрики.
   - Используется на странице AnalysisPage для сравнения профилей.

2. КАРТЫ ЧУВСТВИТЕЛЬНОСТИ (Sensitivity Heatmaps):
   - Компонент <SensitivityHeatmap structures={top10} criteria={all}>:
     * Матрица: строки — структуры, столбцы — критерии (SN, LoD, TR, ST, PC).
     * Цвет ячейки — изменение ранга при увеличении веса критерия на 20%.
     * Градиент: зелёный (ранг улучшается) → жёлтый (не меняется) → красный (ухудшается).
     * Tooltip: "Увеличение веса LoD на 20% повышает ранг S1 с 3 до 1".
   - Данные берутся из GET /api/analytics/sensitivity.

3. ИНТЕРАКТИВНЫЙ ПАРEТО-ФРОНТ (Scatter Plot, Recharts):
   - Компонент <ParetoFrontier structures={all} pareto={pareto_set}>:
     * Выпадающие списки для выбора осей X и Y (например, LoD vs ST).
     * Все структуры из top-K отображаются точками.
     * Парето-оптимальные точки выделены цветом (например, красным).
     * При клике на точку — боковая панель с полной спецификацией структуры.
   - Данные: GET /api/analytics/pareto?criteria=LoD,ST.

4. АНАЛИЗ УСТОЙЧИВОСТИ (Stability Analysis Dashboard):
   - Компонент <StabilityAnalysis structures={top10}>:
     * Гистограмма распределения рангов структуры при 1000 сценариях (Recharts BarChart).
     * Индикатор устойчивости:
       - Зелёный: ранг стабилен в ≥ 80% сценариев.
       - Жёлтый: 60–80%.
       - Красный: < 60%.
     * График "спагетти" (spaghetti plot, Recharts LineChart):
       - Траектории изменения рангов всех структур при вариации весов.
       - Каждая линия — одна структура, цвет по ID.
   - Данные: GET /api/analytics/stability?top_k=10&n_simulations=1000.

5. 3D-ВИЗУАЛИЗАЦИЯ ПРОСТРАНСТВА РЕШЕНИЙ (Plotly):
   - Компонент <Space3DVisualization structures={all} criteria={3}>:
     * 3D scatter plot в пространстве трёх критериев (например, LoD vs SN vs ST).
     * Интерактивное вращение и зум (Plotly по умолчанию).
     * Цвет точек — интегральный Score.
     * Tooltip: название структуры, значения критериев.
   - Данные: GET /api/analytics/space3d?criteria=LoD,SN,ST.

6. ИНТЕГРАЦИЯ С BACKEND:
   - Все компоненты используют React Query для загрузки данных.
   - Кэширование запросов на 5 минут.
   - Обработка ошибок: если backend недоступен, показать fallback UI.

7. СТРАНИЦА AnalysisPage:
   - Вкладки:
     * "Top-K Structures" — таблица лучших структур (уже есть).
     * "Radar Comparison" — радарные диаграммы.
     * "Pareto Frontier" — интерактивный Парето-фронт.
     * "Sensitivity" — карты чувствительности.
     * "Stability" — анализ устойчивости.
     * "3D Space" — 3D-визуализация.
   - Переключение между вкладками через React Router.

КРИТЕРИИ ПРИЁМКИ:
[AC-1]  Радарная диаграмма отображает ≥ 3 группы метрик.
[AC-2]  Переключение между структурами работает без перезагрузки.
[AC-3]  Карта чувствительности отображает матрицу структура×критерий.
[AC-4]  Tooltip на карте чувствительности показывает изменение ранга.
[AC-5]  Парето-фронт позволяет выбрать оси X и Y.
[AC-6]  Парето-оптимальные точки выделены цветом.
[AC-7]  Клик на точку Парето-фронта открывает боковую панель.
[AC-8]  Гистограмма устойчивости отображает распределение рангов.
[AC-9]  Индикатор устойчивости меняет цвет по порогам 80%/60%.
[AC-10] График "спагетти" отображает траектории всех структур.
[AC-11] 3D-визуализация вращается и зумится.
[AC-12] Все компоненты загружают данные через React Query с кэшированием.
[AC-13] Fallback UI отображается при ошибке backend.

ТЕСТЫ:
Unit-тесты (Jest + React Testing Library):
- test_radar_chart_renders_all_groups
- test_radar_chart_switches_structures
- test_sensitivity_heatmap_renders_matrix
- test_sensitivity_heatmap_tooltip_content
- test_pareto_frontier_axis_selection
- test_pareto_frontier_highlights_optimal
- test_pareto_frontier_click_opens_sidebar
- test_stability_histogram_renders
- test_stability_indicator_color_thresholds
- test_stability_spaghetti_plot_renders_lines
- test_3d_visualization_renders
- test_react_query_caching
- test_fallback_ui_on_error

Integration-тесты:
- test_analysis_page_tab_navigation
- test_full_visualization_pipeline

Regression-тесты:
- test_existing_histogram_still_works
- test_existing_table_still_works

ОБРАТНАЯ СОВМЕСТИМОСТЬ:
- Новые вкладки — аддитивные, старая вкладка "Top-K" остаётся.
- Существующие компоненты не модифицируются.
- React Query добавляется как новая зависимость.
```

---

## 📋 ПРОМТ 3.4: Аппроксимирующие модели и суррогатное моделирование (Блок 13)

```
КОНТЕКСТ:
Расчёт метрик выполняется по аналитическим формулам. Нужны адаптивные
модели, калибруемые на reference-структурах, для предсказания при неполноте данных.

ЗАДАЧА:
Реализовать модуль ml/surrogate_models.py с 3 типами моделей + калибровкой.

ТРЕБОВАНИЯ:

1. БИБЛИОТЕКА REFERENCE-СТРУКТУР (уже описана в Блоке 7):
   - Таблица ReferenceStructures с полями:
     * structure_id UUID PK
     * configuration JSON (TA, BRE, IM, MEM)
     * metrics JSON (LoD, SN, TR, ST, DR, RP)
     * source VARCHAR(255) (DOI, номер эксперимента)
     * measurement_conditions JSON (pH, T, ионная сила, матрица)
   - Эндпоинты:
     * GET /api/reference-structures — список.
     * POST /api/reference-structures — добавление (только KB_Admin).

2. АППРОКСИМИРУЮЩИЕ МОДЕЛИ (ml/surrogate_models.py):
   - Базовый класс SurrogateModel с методами:
     * fit(X: DataFrame, y: DataFrame) → self
     * predict(X: DataFrame) → y_pred: DataFrame
     * score(X: DataFrame, y: DataFrame) → float (R² или другая метрика)
   
   - Модель 1: ResponseSurfaceModel (RSM, полиномиальная регрессия 2-го порядка):
     * Библиотека: scikit-learn PolynomialFeatures + LinearRegression.
     * Быстрая, интерпретируемая, но ограничена полиномами.
   
   - Модель 2: GaussianProcessModel (GPR, Гауссовская регрессия):
     * Библиотека: scikit-learn GaussianProcessRegressor.
     * Возвращает среднее и дисперсию (оценку неопределённости).
     * Медленнее, но даёт confidence intervals.
   
   - Модель 3: GradientBoostingModel (XGBoost/LightGBM):
     * Библиотека: xgboost.XGBRegressor или lightgbm.LGBMRegressor.
     * Параметр: max_depth ≤ 5 (регуляризация).
     * Быстрая, точная, но менее интерпретируемая.

3. КАЛИБРОВКА МОДЕЛЕЙ:
   - Функция calibrate_models(reference_structures: List[ReferenceStructure]):
     * Разделение на train/test (80/20).
     * Обучение всех трёх моделей.
     * Выбор лучшей по R² на test-set.
     * Сохранение лучшей модели в ml/models/best_model.pkl.
   - Автоматическая калибровка при импорте новых данных (Блок 5):
     * Мониторинг относительной ошибки: ε = |Score_calc - Score_exp| / Score_exp.
     * При ε > 15% и n ≥ 10 валидированных структур → переобучение.
   - Стратегия активного обучения:
     * Экспериментальные данные с весами, обратно пропорциональными ошибке предсказания.
     * Трудные примеры получают больший вес.
   - Регуляризованная регрессия (ridge/lasso) для малых выборок.

4. ИНТЕГРАЦИЯ В РАСЧЁТ МЕТРИК:
   - Функция predict_metrics_with_surrogate(structure: Structure) → metrics:
     * Если для структуры отсутствуют критичные параметры (data_completeness < 0.6):
       - Использовать предсказание суррогатной модели.
       - Понизить коэффициент достоверности κ на 20% (штраф за использование модели).
     * Иначе: использовать аналитические формулы (Блок 4).
   - Возвращает: {metrics: {...}, source: 'surrogate'|'analytical', confidence: float}.

5. ЭНДПОИНТЫ API:
   - GET /api/ml/models — список доступных моделей с метриками качества.
   - POST /api/ml/calibrate — запуск калибровки (только KB_Admin).
   - GET /api/ml/predict?structure_id= — предсказание метрик для структуры.
   - GET /api/ml/learning-curve — график точности vs число reference-структур.

КРИТЕРИИ ПРИЁМКИ:
[AC-1]  ResponseSurfaceModel обучается и предсказывает с R² > 0.7 на test-set.
[AC-2]  GaussianProcessModel возвращает среднее и дисперсию.
[AC-3]  GradientBoostingModel имеет max_depth ≤ 5.
[AC-4]  Калибровка выбирает лучшую модель по R².
[AC-5]  Автоматическая калибровка запускается при ε > 15% и n ≥ 10.
[AC-6]  Активное обучение присваивает большие веса трудным примерам.
[AC-7]  Предсказание с суррогатом понижает κ на 20%.
[AC-8]  GET /api/ml/models возвращает ≥ 3 модели.
[AC-9]  POST /api/ml/calibrate завершается успешно.
[AC-10] GET /api/ml/predict возвращает metrics + source + confidence.

ТЕСТЫ:
Unit-тесты:
- test_response_surface_model_fit_predict
- test_response_surface_model_r2_score
- test_gaussian_process_model_returns_mean_variance
- test_gaussian_process_model_confidence_intervals
- test_gradient_boosting_model_max_depth
- test_gradient_boosting_model_r2_score
- test_calibrate_models_selects_best
- test_auto_calibration_trigger_threshold
- test_active_learning_weights
- test_ridge_regularization_small_sample
- test_predict_with_surrogate_reduces_kappa
- test_predict_with_analytical_full_data

Integration-тесты:
- test_full_calibration_pipeline
- test_surrogate_integration_with_metrics_calculation
- test_learning_curve_improvement

Regression-тесты:
- test_existing_analytical_metrics_unchanged
- test_existing_synthesis_not_affected

ОБРАТНАЯ СОВМЕСТИМОСТЬ:
- Суррогатные модели — опциональный слой.
- При отсутствии обученной модели используется аналитический расчёт.
- Новые эндпоинты — аддитивные.
- Таблица ReferenceStructures создаётся миграцией.
```

---

## ⏸️ ПАУЗА ПЕРЕД ФИНАЛЬНЫМ СООБЩЕНИЕМ 4/4

Это **сообщение 3 из 4**. В следующем (финальном) сообщении будут промты для:
- **Блок 8:** Интеграция с внешними системами (LIMS/ELN API, патентные базы, PubMed)
- **Блок 11:** NLP для автоматического извлечения параметров
- **Блок 17:** Оптимизация производительности и масштабируемость
- **Блок 18:** Мобильная адаптация и offline-режим (PWA)

После вывода сообщения 4/4 я предоставлю:
1. **Сводную таблицу всех промтов** с номерами, названиями и приоритетами.
2. **Дорожную карту внедрения** по фазам (критические → продвинутые → интеграции).
3. **Чек-лист обратной совместимости** для QA-инженеров.

Готов продолжать?

# 📨 СООБЩЕНИЕ 4/4: ПРОМТЫ ДЛЯ БЛОКОВ 8, 11, 17, 18 + ИТОГОВАЯ СВОДКА

---

## 📋 ПРОМТ 4.1: Интеграция с внешними системами (Блок 8)

```
КОНТЕКСТ:
Система работает изолированно. Нужны механизмы автоматического импорта
данных из LIMS/ELN, патентных баз и библиометрических систем.

ЗАДАЧА:
Реализовать модуль integrations/ с коннекторами к внешним системам
и планировщиком фоновых задач.

ТРЕБОВАНИЯ:

1. API-ИНТЕГРАЦИЯ С LIMS/ELN (integrations/lims_connector.py):
   - Базовый класс LIMSConnector с методами:
     * authenticate(credentials: dict) → token
     * fetch_experiments(experiment_ids: List[str]) → List[Experiment]
     * map_to_passport(experiment: Experiment) → dict (маппинг полей LIMS на паспорт компонента)
   
   - Коннекторы для конкретных систем:
     * ThermoFisherSampleManagerConnector (REST API, OAuth 2.0)
     * LabWareConnector (REST API, API-ключи)
     * BenchlingConnector (REST API v1, API-ключи, приоритетный — уже частично реализован в Блоке 7/15)
   
   - Эндпоинт: POST /api/integrations/lims/import
     * Принимает: {lims_type: str, api_key: str, experiment_ids: List[str]}
     * Возвращает: {imported_count: int, new_passports: List[dict], errors: List[str]}
     * Автоматический маппинг полей LIMS на структуру паспортов компонентов.
     * Создание записей в таблицах Analytes/BioRecognitionLayers/ImmobilizationLayers/MemristiveLayers.
     * Логирование в AuditLog (Блок 9).

2. ПАРСИНГ ПАТЕНТНЫХ БАЗ (integrations/patent_parser.py):
   - Интеграция с существующим модулем google_patents_parser/ (если есть).
   - Поддержка источников:
     * Google Patents (через SerpAPI или прямой парсинг)
     * USPTO (PatFT/AppFT API)
     * EPO (Open Patent Services API)
     * WIPO PatentScope (PATENTSCOPE Web Service)
   
   - Класс PatentParser с методами:
     * fetch_patent(patent_url: str) → PatentDocument
     * extract_parameters(document: PatentDocument) → List[ExtractedParameter]
     * validate_and_propose(parameters: List[ExtractedParameter]) → List[ProposedPassport]
   
   - Эндпоинт: POST /api/integrations/patents/extract
     * Принимает: {patent_url: str}
     * Возвращает: {proposed_passports: List[dict], confidence_scores: List[float]}
     * Автоматическая валидация и предложение к добавлению в базу паспортов.
     * Сохранение в таблицу ImportQueue (status='PENDING') для подтверждения экспертом.

3. БИБЛИОМЕТРИЧЕСКИЕ СИСТЕМЫ (integrations/pubmed_connector.py):
   - Интеграция с PubMed через E-utilities API:
     * ESearch: поиск статей по ключевым словам.
     * EFetch: получение полных текстов (если доступны).
     * ESummary: получение метаданных.
   
   - Класс PubMedConnector с методами:
     * search(query: str, max_results: int) → List[PubMedArticle]
     * fetch_full_text(article_id: str) → Optional[str]
     * extract_parameters(article: PubMedArticle) → List[ExtractedParameter]
   
   - Эндпоинт: POST /api/integrations/pubmed/search
     * Принимает: {query: str, max_results: int}
     * Возвращает: {articles: List[dict], extracted_parameters: List[dict]}
     * Извлечение параметров из абстрактов и полных текстов (использует NLP-модуль из Блока 11).
   
   - Примеры запросов:
     * "memristive biosensor sensitivity"
     * "biosensor limit of detection VEGF"
     * "glucose biosensor response time"

4. ПЛАНИРОВЩИК ИМПОРТА (integrations/scheduler.py):
   - Использование Celery с APScheduler или Celery Beat.
   - Фоновые задачи:
     * weekly_pubmed_search: еженедельный поиск новых статей по заданным ключевым словам.
     * monthly_patent_check: ежемесячная проверка патентных баз по ключевым классификациям.
     * daily_lims_sync: ежедневная синхронизация с LIMS (если настроено).
   
   - Таблица ImportQueue:
     * queue_id UUID PK
     * source_type ENUM('LIMS','Patent','PubMed')
     * source_url VARCHAR(500)
     * status ENUM('PENDING','APPROVED','REJECTED','IMPORTED')
     * proposed_data JSON
     * created_at TIMESTAMP
     * reviewed_by UUID FK → Users (nullable)
     * reviewed_at TIMESTAMP (nullable)
   
   - Эндпоинты:
     * GET /api/integrations/queue — список задач со статусами.
     * POST /api/integrations/queue/{id}/approve — одобрить импорт (только KB_Admin).
     * POST /api/integrations/queue/{id}/reject — отклонить.
     * GET /api/integrations/scheduler/status — статус планировщика.
     * POST /api/integrations/scheduler/run/{task_name} — ручной запуск задачи (только KB_Admin).

5. АУТЕНТИФИКАЦИЯ И БЕЗОПАСНОСТЬ:
   - API-ключи для внешних систем хранятся в зашифрованном виде (Fernet).
   - Эндпоинт POST /api/integrations/credentials (только KB_Admin):
     * Принимает: {system_type: str, credentials: dict}
     * Шифрует и сохраняет в таблицу IntegrationCredentials.
   - Rate Limiting для внешних API (чтобы не превысить лимиты).
   - Логирование всех внешних запросов в AuditLog.

КРИТЕРИИ ПРИЁМКИ:
[AC-1]  POST /api/integrations/lims/import успешно импортирует данные из Benchling (mock-тест).
[AC-2]  Маппинг полей LIMS корректно преобразует в структуру паспорта.
[AC-3]  POST /api/integrations/patents/extract извлекает параметры из патента (mock-тест).
[AC-4]  Извлечённые параметры сохраняются в ImportQueue со статусом PENDING.
[AC-5]  POST /api/integrations/pubmed/search возвращает ≥ 1 статью по валидному запросу.
[AC-6]  NLP-модуль извлекает параметры из абстракта PubMed.
[AC-7]  Планировщик запускает weekly_pubmed_search по расписанию.
[AC-8]  GET /api/integrations/queue возвращает список задач.
[AC-9]  POST /api/integrations/queue/{id}/approve импортирует данные в основную БД.
[AC-10] API-ключи хранятся в зашифрованном виде.
[AC-11] Все внешние запросы логируются в AuditLog.

ТЕСТЫ:
Unit-тесты:
- test_lims_connector_authenticate
- test_lims_connector_fetch_experiments
- test_lims_connector_map_to_passport
- test_patent_parser_fetch_patent
- test_patent_parser_extract_parameters
- test_patent_parser_validate_and_propose
- test_pubmed_connector_search
- test_pubmed_connector_fetch_full_text
- test_pubmed_connector_extract_parameters
- test_scheduler_weekly_pubmed_search
- test_scheduler_monthly_patent_check
- test_import_queue_create
- test_import_queue_approve
- test_import_queue_reject
- test_credentials_encryption
- test_rate_limiting_external_api

Integration-тесты:
- test_full_lims_import_flow_benchling_mock
- test_full_patent_extraction_flow_mock
- test_full_pubmed_search_and_extraction
- test_scheduler_integration_with_celery

Regression-тесты:
- test_existing_synthesis_not_affected
- test_existing_endpoints_still_work

ОБРАТНАЯ СОВМЕСТИМОСТЬ:
- Интеграции — опциональный модуль, работает только при наличии credentials.
- ImportQueue — новая таблица, не влияет на существующие.
- Планировщик запускается отдельно, не блокирует основной API.
- Новые эндпоинты — аддитивные.
```

---

## 📋 ПРОМТ 4.2: NLP для автоматического извлечения параметров (Блок 11)

```
КОНТЕКСТ:
Все данные вводятся вручную или импортируются из структурированных источников.
Нужно автоматическое извлечение параметров из неструктурированных текстов
(научные статьи, патенты).

ЗАДАЧА:
Реализовать модуль nlp/ с NER-моделью для извлечения параметров биосенсоров.

ТРЕБОВАНИЯ:

1. МОДЕЛЬ РАСПОЗНАВАНИЯ ИМЕНОВАННЫХ СУЩНОСТЕЙ (NER):
   - Базовая модель: BERT/BioBERT/SciBERT (выбрать BioBERT как наиболее подходящую).
   - Дообучение на размеченном корпусе научных статей по биосенсорам.
   - Классы сущностей:
     * ANALYTE: глюкоза, VEGF, PSA, troponin I, Pb2+, Cd2+, Hg2+
     * BRE: GOx, GDH, антитела, аптамеры, наноантитела
     * IM: хитозан, нафион, PEDOT:PSS, силан-APTES, PEG-линкер
     * MEM: TiO2, HfO2, Si-NW, графен, ZnO, Ta2O5
     * METRIC: LoD, sensitivity, response time, stability, dynamic range, reproducibility
     * VALUE: числовые значения с единицами (2.5 пг/мл, 42.5 мкА/мМ, 28 с, 120 циклов)
   
   - Контекстные паттерны:
     * "The limit of detection was X mM"
     * "sensitivity of Y μA/mM"
     * "response time Z s"
     * "stability over N cycles"
     * "dynamic range from A to B"

2. ИЗВЛЕЧЕНИЕ ЧИСЛОВЫХ ЗНАЧЕНИЙ (nlp/value_parser.py):
   - Класс ValueParser с методами:
     * parse_value(text: str) → (value: float, unit: str)
     * normalize_units(value: float, from_unit: str, to_unit: str) → float
     * parse_range(text: str) → (min_value: float, max_value: float, unit: str)
   
   - Обработка единиц измерения:
     * Концентрация: мМ → мкМ → нМ → пМ (логарифмическая шкала)
     * Масса: мг → мкг → нг → пг
     * Время: с → мс → мкс → нс
     * Температура: °C, K
     * Ток: А → мА → мкА → нА
   
   - Извлечение диапазонов:
     * "10–100 пМ" → DR_Min = 10, DR_Max = 100, unit = "пМ"
     * "from 5 to 2000 pg/mL" → min = 5, max = 2000, unit = "pg/mL"

3. ВЕРИФИКАЦИЯ ЭКСПЕРТОМ:
   - Таблица ExtractedParameters:
     * extraction_id UUID PK
     * source_text TEXT
     * source_url VARCHAR(500)
     * entity_type ENUM('ANALYTE','BRE','IM','MEM','METRIC','VALUE')
     * entity_value VARCHAR(255)
     * confidence_score FLOAT (0.0–1.0)
     * status ENUM('PENDING','VERIFIED','REJECTED') DEFAULT 'PENDING'
     * verified_by UUID FK → Users (nullable)
     * verified_at TIMESTAMP (nullable)
     * created_at TIMESTAMP
   
   - Эндпоинты:
     * POST /api/nlp/extract — принимает текст (или PDF/DOCX) и возвращает список извлечённых параметров с confidence scores.
     * GET /api/nlp/queue — возвращает список неподтверждённых параметров для верификации (фильтры: by_entity_type, by_confidence, by_source).
     * POST /api/nlp/verify/{id} — подтверждает или отклоняет извлечённый параметр.
     * POST /api/nlp/verify/batch — пакетная верификация (approve_all_above_threshold).

4. ТОЧНОСТЬ ИЗВЛЕЧЕНИЯ:
   - Пилотные эксперименты показали:
     * 72–85% для хорошо формализованных метрик (LoD, sensitivity, response time).
     * 45–60% для качественных характеристик (biocompatibility, stability).
   - Все извлечённые параметры требуют обязательной верификации экспертом.
   - Confidence score < 0.7 → автоматическая пометка "requires_review".

5. ИНТЕГРАЦИЯ С ДРУГИМИ МОДУЛЯМИ:
   - Блок 8 (PubMed/Patents): вызывает nlp.extract для извлечения параметров.
   - Блок 5 (Feedback Loop): верифицированные параметры повышают reliability_category.
   - Блок 6 (Онтология): извлечённые сущности связываются с классами онтологии.

6. UI ДЛЯ ВЕРИФИКАЦИИ:
   - Страница /kb-admin/nlp-queue:
     * Таблица с колонками: Source Text, Entity Type, Value, Confidence, Status, Actions.
     * Фильтры по entity_type и confidence.
     * Кнопки "Approve" / "Reject" / "Edit" для каждой записи.
     * Массовое одобрение: "Approve all with confidence > 0.8".
   - При одобрении:
     * Параметр сохраняется в соответствующую таблицу (Analytes/BRE/IM/MEM).
     * Создаётся запись в AuditLog.
     * reliability_category устанавливается в 'expert' (если источник — статья) или 'experimental' (если патент с примерами).

КРИТЕРИИ ПРИЁМКИ:
[AC-1]  NER-модель извлекает сущности ANALYTE, BRE, IM, MEM, METRIC, VALUE.
[AC-2]  Точность извлечения LoD ≥ 72% на тестовом корпусе.
[AC-3]  Точность извлечения sensitivity ≥ 75%.
[AC-4]  ValueParser корректно преобразует единицы (мМ → пМ, мг → пг).
[AC-5]  ValueParser извлекает диапазоны (10–100 пМ → min=10, max=100).
[AC-6]  POST /api/nlp/extract возвращает список параметров с confidence scores.
[AC-7]  GET /api/nlp/queue возвращает неподтверждённые параметры.
[AC-8]  POST /api/nlp/verify/{id} обновляет статус и создаёт запись в AuditLog.
[AC-9]  UI-страница NLP Queue отображает таблицу с фильтрами.
[AC-10] Массовое одобрение работает корректно.
[AC-11] Верифицированные параметры сохраняются в основную БД.
[AC-12] Confidence score < 0.7 автоматически помечается как "requires_review".

ТЕСТЫ:
Unit-тесты:
- test_ner_model_extracts_analyte
- test_ner_model_extracts_bre
- test_ner_model_extracts_im
- test_ner_model_extracts_mem
- test_ner_model_extracts_metric
- test_ner_model_extracts_value
- test_ner_model_accuracy_lod
- test_ner_model_accuracy_sensitivity
- test_value_parser_parse_value
- test_value_parser_normalize_units
- test_value_parser_parse_range
- test_extract_endpoint_returns_parameters
- test_queue_endpoint_filters_by_entity_type
- test_verify_endpoint_updates_status
- test_verify_batch_approves_above_threshold
- test_confidence_threshold_marking

Integration-тесты:
- test_full_nlp_extraction_flow
- test_nlp_integration_with_pubmed
- test_nlp_integration_with_patents
- test_verified_parameters_saved_to_db

Regression-тесты:
- test_existing_passport_endpoints_not_affected
- test_existing_synthesis_not_affected

ОБРАТНАЯ СОВМЕСТИМОСТЬ:
- NLP-модуль — опциональный, работает только при явном вызове.
- ExtractedParameters — новая таблица, не влияет на существующие.
- Верифицированные параметры добавляются как новые записи, не перезаписывают старые.
- Новые эндпоинты — аддитивные.
```

---

## 📋 ПРОМТ 4.3: Оптимизация производительности и масштабируемость (Блок 17)

```
КОНТЕКСТ:
Синтез всех комбинаций выполняется синхронно в рамках одного HTTP-запроса.
При большом количестве компонентов (сотни тысяч комбинаций) это приводит к таймаутам.

ЗАДАЧА:
Реализовать асинхронный синтез, кэширование и оптимизацию запросов к БД.

ТРЕБОВАНИЯ:

1. АСИНХРОННЫЙ СИНТЕЗ:
   - Эндпоинт POST /api/synthesize/async:
     * Принимает те же параметры, что и синхронный синтез.
     * Возвращает: {task_id: str, status: 'PENDING', estimated_time: int}
     * Немедленно завершается, не дожидаясь результата.
   
   - Фоновый worker (Celery task):
     * Выполняет синтез в отдельном процессе.
     * Сохраняет прогресс в Redis: {task_id: {status, progress_percent, processed_count, total_count}}
     * По завершении сохраняет результат в БД (таблица SynthesisResults).
   
   - Эндпоинт GET /api/synthesize/status/{task_id}:
     * Возвращает: {status: 'PENDING'|'RUNNING'|'COMPLETED'|'FAILED', progress: float, result_id: Optional[str]}
   
   - WebSocket /ws/synthesize/progress/{task_id}:
     * Real-time обновление прогресса на Frontend.
     * Отправляет сообщения: {progress: float, processed_count: int, total_count: int}

2. ИНКРЕМЕНТАЛЬНЫЙ СИНТЕЗ:
   - При добавлении новых компонентов в базу:
     * Не пересчитывать все комбинации заново.
     * Вычислять только новые комбинации с участием добавленных компонентов.
   - Таблица SynthesisCache:
     * cache_key VARCHAR(255) PK (хеш от списка ID компонентов + веса + ограничения)
     * result JSON
     * created_at TIMESTAMP
     * valid_until TIMESTAMP
   - При запросе синтеза:
     * Проверить наличие cache_key в SynthesisCache.
     * Если найден и не истёк → вернуть из кэша.
     * Иначе → запустить синтез и сохранить в кэш.

3. КЭШИРОВАНИЕ РЕЗУЛЬТАТОВ:
   - Redis для кэширования:
     * Ключ: hash(component_ids + weights + constraints)
     * Значение: сериализованный результат синтеза.
     * TTL: 24 часа (настраивается).
   - Инвалидация кэша:
     * При изменении паспорта компонента → удалить все кэши, содержащие этот компонент.
     * Эндпоинт POST /api/cache/invalidate (только KB_Admin).

4. ОПТИМИЗАЦИЯ ЗАПРОСОВ К БД:
   - Индексация:
     * CREATE INDEX idx_analytes_ph_range ON Analytes(ph_min, ph_max)
     * CREATE INDEX idx_bre_temperature ON BioRecognitionLayers(t_working)
     * CREATE INDEX idx_im_mechanical ON ImmobilizationLayers(mp_young)
     * CREATE INDEX idx_mem_electrical ON MemristiveLayers(resistance_range)
   - Пакетная вставка (batch insert):
     * Использовать SQLAlchemy bulk_insert_mappings для массового сохранения комбинаций.
     * Размер батча: 1000 записей.
   - Курсоры:
     * Для обработки больших объёмов данных использовать server-side cursors.
     * Избегать загрузки всего результата в память.

5. ГОРИЗОНТАЛЬНОЕ МАСШТАБИРОВАНИЕ:
   - Поддержка запуска нескольких worker-процессов Celery.
   - Разделение пространства комбинаций на партиции:
     * Партиция 1: компоненты с ID % 4 == 0
     * Партиция 2: компоненты с ID % 4 == 1
     * Партиция 3: компоненты с ID % 4 == 2
     * Партиция 4: компоненты с ID % 4 == 3
   - Каждый worker обрабатывает свою партицию.
   - Результаты объединяются в финальном шаге.

6. МОНИТОРИНГ ПРОИЗВОДИТЕЛЬНОСТИ:
   - Эндпоинт GET /api/performance/metrics:
     * Возвращает: {avg_synthesis_time, cache_hit_rate, active_workers, queue_length}
   - Логирование медленных запросов (> 5 секунд).
   - Интеграция с Prometheus для сбора метрик (опционально).

КРИТЕРИИ ПРИЁМКИ:
[AC-1]  POST /api/synthesize/async возвращает task_id немедленно (< 100 мс).
[AC-2]  GET /api/synthesize/status/{task_id} возвращает актуальный прогресс.
[AC-3]  WebSocket отправляет обновления прогресса в реальном времени.
[AC-4]  Инкрементальный синтез вычисляет только новые комбинации.
[AC-5]  Кэш Redis снижает время повторного синтеза до < 50 мс.
[AC-6]  Инвалидация кэша удаляет устаревшие записи.
[AC-7]  Индексы БД ускоряют запросы на 30-50%.
[AC-8]  Пакетная вставка обрабатывает 10000 записей за < 2 секунды.
[AC-9]  Курсоры обрабатывают 100000 записей без OOM.
[AC-10] Горизонтальное масштабирование: 4 worker'а обрабатывают 4× больше комбинаций.
[AC-11] GET /api/performance/metrics возвращает метрики.

ТЕСТЫ:
Unit-тесты:
- test_async_synthesize_returns_task_id
- test_synthesize_status_returns_progress
- test_websocket_sends_updates
- test_incremental_synthesis_computes_only_new
- test_cache_hit_returns_fast
- test_cache_invalidation_on_passport_update
- test_batch_insert_performance
- test_cursor_handles_large_dataset
- test_partitioning_distributes_work
- test_performance_metrics_endpoint

Integration-тесты:
- test_full_async_synthesis_flow
- test_cache_integration_with_redis
- test_horizontal_scaling_with_multiple_workers

Load-тесты (Locust или k6):
- test_synthesis_100k_combinations_completes_in_60s
- test_cache_hit_rate_under_load

Regression-тесты:
- test_existing_sync_synthesis_still_works
- test_existing_endpoints_not_affected

ОБРАТНАЯ СОВМЕСТИМОСТЬ:
- Старый синхронный эндпоинт POST /api/synthesize остаётся для малых выборок (< 1000 комбинаций).
- Новый асинхронный эндпоинт — аддитивный.
- Кэш прозрачен для пользователя.
- Индексы БД создаются миграцией, не влияют на существующие данные.
```

---

## 📋 ПРОМТ 4.4: Мобильная адаптация и offline-режим (Блок 18)

```
КОНТЕКСТ:
Frontend адаптирован для мобильных через responsive design, но отсутствует
поддержка offline-работы и прогрессивных веб-приложений (PWA).

ЗАДАЧА:
Реализовать PWA с offline-режимом и touch-оптимизацией.

ТРЕБОВАНИЯ:

1. PWA (Progressive Web App):
   - manifest.json:
     * name: "Memristive Biosensor Designer"
     * short_name: "BioSensor"
     * start_url: "/"
     * display: "standalone"
     * theme_color: "#1976d2"
     * background_color: "#ffffff"
     * icons: [192x192, 512x512]
   
   - Service Worker (sw.js):
     * Кэширование статических ресурсов (HTML, CSS, JS) при первом посещении.
     * Стратегия кэширования: Cache First для статики, Network First для API.
     * Offline fallback: отображение кэшированных данных с пометкой "Last updated: [дата]".
     * Push-уведомления о завершении фоновых задач (синтез, валидация).

2. OFFLINE-СИНТЕЗ:
   - Клиентская версия движка совместимости и расчёта метрик (TypeScript):
     * Модуль src/offline/compatibility-engine.ts
     * Модуль src/offline/metrics-calculator.ts
     * Базовая проверка совместимости (5 предикатов из Блока 2).
     * Упрощённый расчёт Score (без суррогатных моделей).
   
   - Кэширование паспортов компонентов в IndexedDB:
     * Таблица components: {id, type, data, last_updated}
     * Синхронизация с сервером при восстановлении соединения.
     * Эндпоинт GET /api/components/sync?since={timestamp} — возвращает изменения с указанной даты.
   
   - Локальное хранение результатов синтеза:
     * IndexedDB таблица synthesis_results: {id, params, result, created_at, synced: bool}
     * При появлении сети → автоматическая синхронизация с сервером.

3. TOUCH-ОПТИМИЗАЦИЯ:
   - Увеличение размера кнопок и интерактивных элементов:
     * Минимум 44×44 пикселя (рекомендация Apple HIG).
     * Padding между кнопками ≥ 8 пикселей.
   
   - Swipe-жесты:
     * Swipe влево/вправо для переключения между вкладками.
     * Swipe вниз для обновления данных (pull-to-refresh).
     * Библиотека: react-swipeable или hammer.js.
   
   - Long-press для контекстного меню:
     * Long-press на структуре → меню: "Copy ID", "Export", "Add to Project".
     * Реализация через onContextMenu + touchstart/touchend.

4. PUSH-УВЕДОМЛЕНИЯ:
   - Web Push API:
     * Регистрация service worker для push-уведомлений.
     * Подписка на уведомления: POST /api/notifications/subscribe {subscription: PushSubscription}
     * Отправка уведомлений с сервера: POST /api/notifications/send {user_id, title, body, data}
   
   - Сценарии уведомлений:
     * "Синтез завершён: найдено 216 комбинаций"
     * "Валидация импортирована: reliability обновлена"
     * "Новая статья в PubMed: 5 релевантных параметров"

5. АДАПТИВНЫЙ UI:
   - Breakpoints:
     * Mobile: < 768px
     * Tablet: 768px–1024px
     * Desktop: > 1024px
   - Мобильная навигация:
     * Hamburger menu вместо горизонтального меню.
     * Bottom navigation bar для основных разделов.
   - Оптимизация таблиц:
     * На мобильных: карточный вид вместо таблицы.
     * Горизонтальный скролл для широких таблиц.

6. ТЕСТИРОВАНИЕ:
   - Lighthouse audit:
     * PWA score ≥ 90
     * Performance score ≥ 80
     * Accessibility score ≥ 90
   - Testing на реальных устройствах:
     * iOS Safari (iPhone, iPad)
     * Android Chrome (Phone, Tablet)

КРИТЕРИИ ПРИЁМКИ:
[AC-1]  manifest.json валидируется через Lighthouse.
[AC-2]  Service Worker регистрируется и кэширует статику.
[AC-3]  Offline fallback отображает кэшированные данные.
[AC-4]  Offline-синтез выполняет базовую проверку совместимости.
[AC-5]  IndexedDB хранит паспорта компонентов.
[AC-6]  Синхронизация с сервером работает при восстановлении сети.
[AC-7]  Кнопки ≥ 44×44 пикселей.
[AC-8]  Swipe-жесты переключают вкладки.
[AC-9]  Long-press открывает контекстное меню.
[AC-10] Push-уведомления отправляются и отображаются.
[AC-11] Мобильная навигация использует hamburger menu.
[AC-12] Lighthouse PWA score ≥ 90.

ТЕСТЫ:
Unit-тесты:
- test_manifest_json_valid
- test_service_worker_registers
- test_service_worker_caches_static
- test_offline_fallback_displays_cached
- test_offline_compatibility_engine
- test_indexeddb_stores_components
- test_sync_with_server
- test_button_size_minimum_44px
- test_swipe_gesture_switches_tabs
- test_long_press_opens_context_menu
- test_push_notification_subscribe
- test_push_notification_receive

Integration-тесты:
- test_full_pwa_installation_flow
- test_offline_synthesis_and_sync
- test_push_notification_end_to_end

E2E-тесты (Cypress или Playwright):
- test_pwa_lighthouse_audit
- test_mobile_navigation
- test_touch_interactions

Regression-тесты:
- test_desktop_ui_not_affected
- test_existing_endpoints_still_work

ОБРАТНАЯ СОВМЕСТИМОСТЬ:
- PWA — опциональный слой, десктопная версия работает как раньше.
- Service Worker не влияет на существующий код.
- Offline-синтез — упрощённая версия, не заменяет серверный синтез.
- Новые эндпоинты (sync, notifications) — аддитивные.
```

---

# 📊 ИТОГОВАЯ СВОДКА

## Сводная таблица всех промтов

| № | Название промта | Блок | Приоритет | Трудоемкость | Фаза |
|---|---|---|---|---|---|
| 1.1 | Расширение модели данных и учёт неопределённости | 1 | Критический | Средняя | 1 |
| 1.2 | Двухэтапный движок совместимости | 2 | Критический | Высокая | 1 |
| 1.3 | Расчёт эксплуатационных характеристик | 4 | Критический | Средняя | 1 |
| 1.4 | Безопасность и аутентификация | 12 | Критический | Высокая | 1 |
| 2.1 | Многокритериальное ранжирование и анализ устойчивости | 3 | Высокий | Средняя | 2 |
| 2.2 | Контур обучения и ролевая модель UI | 5 | Высокий | Высокая | 2 |
| 2.3 | Управление проектами, версионирование и аудит | 9 | Высокий | Средняя | 2 |
| 2.4 | Онтологическая модель и семантический поиск | 6 | Высокий | Средняя | 2 |
| 3.1 | Генерация и экспорт планов валидации | 7+15 | Высокий | Средняя | 2 |
| 3.2 | Шаблоны архитектур, профили задач и тест-кейсы | 10 | Средний | Низкая | 2 |
| 3.3 | Визуализация компромиссов и интерактивный анализ | 16 | Высокий | Средняя | 2 |
| 3.4 | Аппроксимирующие модели и суррогатное моделирование | 13 | Средний | Высокая | 2 |
| 4.1 | Интеграция с внешними системами | 8 | Средний | Высокая | 3 |
| 4.2 | NLP для автоматического извлечения параметров | 11 | Низкий | Очень высокая | 3 |
| 4.3 | Оптимизация производительности и масштабируемость | 17 | Высокий | Средняя | 2 |
| 4.4 | Мобильная адаптация и offline-режим | 18 | Низкий | Средняя | 3 |

---

## 🗺️ Дорожная карта внедрения

### **Фаза 1: Критические доработки (2–3 месяца)**
**Цель:** Фундамент для всех расчётов + безопасность + трассируемость

**Приоритет 1 (недели 1–4):**
- Промт 1.4: Безопасность и аутентификация (Блок 12)
- Промт 1.1: Модель данных и учёт неопределённости (Блок 1)
- Промт 2.3: Управление проектами и версионирование (Блок 9)

**Приоритет 2 (недели 5–8):**
- Промт 1.2: Двухэтапный движок совместимости (Блок 2)
- Промт 1.3: Расчёт эксплуатационных характеристик (Блок 4)

**Критерии завершения фазы:**
- ✅ JWT-аутентификация работает, роли разделены
- ✅ Все паспорта имеют поля надёжности, κ рассчитывается
- ✅ Проекты сохраняются, версии паспортов ведутся, аудит работает
- ✅ 5 предикатов совместимости + технологические фильтры
- ✅ Формулы метрик соответствуют статье (metrics_v2)
- ✅ Все тест-кейсы из Блока 10 проходят

---

### **Фаза 2: Продвинутые функции (3–4 месяца)**
**Цель:** Многокритериальное ранжирование + контур обучения + онтология + производительность

**Приоритет 1 (недели 9–14):**
- Промт 2.1: Многокритериальное ранжирование (Блок 3)
- Промт 2.2: Контур обучения и ролевая модель UI (Блок 5)
- Промт 4.3: Оптимизация производительности (Блок 17)

**Приоритет 2 (недели 15–20):**
- Промт 2.4: Онтологическая модель (Блок 6)
- Промт 3.1: Генерация планов валидации (Блок 7+15)
- Промт 3.3: Визуализация компромиссов (Блок 16)
- Промт 3.4: Аппроксимирующие модели (Блок 13)
- Промт 3.2: Шаблоны архитектур и тест-кейсы (Блок 10)

**Критерии завершения фазы:**
- ✅ МАИ, Парето, TOPSIS, ε-ограничения работают
- ✅ Stress-test показывает устойчивость решений
- ✅ Feedback Loop: валидация → обновление reliability → переобучение моделей
- ✅ Онтология связывает компоненты, семантический поиск работает
- ✅ Протоколы валидации генерируются по ICH Q2(R2), экспорт в DOCX/XML
- ✅ Радарные диаграммы, heatmap, 3D-визуализация
- ✅ Суррогатные модели обучены на reference-структурах
- ✅ Асинхронный синтез, кэширование, горизонтальное масштабирование

---

### **Фаза 3: Интеграции и автоматизация (4–6 месяцев)**
**Цель:** Внешние интеграции + NLP + мобильная адаптация

**Приоритет 1 (недели 21–28):**
- Промт 4.1: Интеграция с внешними системами (Блок 8)
- Промт 4.4: Мобильная адаптация и PWA (Блок 18)

**Приоритет 2 (недели 29–36):**
- Промт 4.2: NLP для извлечения параметров (Блок 11)

**Критерии завершения фазы:**
- ✅ Импорт из LIMS (Benchling, LabWare, SampleManager)
- ✅ Парсинг патентов (Google Patents, USPTO, EPO)
- ✅ Поиск в PubMed, извлечение параметров
- ✅ Планировщик импорта работает по расписанию
- ✅ PWA устанавливается на мобильные устройства
- ✅ Offline-синтез выполняет базовую проверку
- ✅ Push-уведомления о завершении задач
- ✅ NLP-модель извлекает параметры с точностью ≥ 72%
- ✅ UI-верификация извлечённых параметров

---

## ✅ Чек-лист обратной совместимости (для QA-инженеров)

### Перед каждым релизом проверять:

#### **1. База данных**
- [ ] Все новые поля — nullable или имеют server_default
- [ ] Миграции Alembic применяются без ошибок
- [ ] Миграции откатываются корректно (alembic downgrade)
- [ ] Существующие SELECT-запросы не используют SELECT *
- [ ] Индексы не дублируют существующие

#### **2. API-эндпоинты**
- [ ] Старые эндпоинты не изменяют контракт (request/response schema)
- [ ] Новые эндпоинты имеют префикс /api/v2/ или новые пути
- [ ] Все эндпоинты возвращают корректные HTTP-статусы
- [ ] Rate Limiting не блокирует существующих клиентов
- [ ] AUTH_MODE='disabled' позволяет проходить старым тестам

#### **3. Бизнес-логика**
- [ ] METRICS_VERSION='v1' возвращает старые результаты
- [ ] MCDA_METHOD='weighted_sum' эквивалентен старому расчёту
- [ ] CombinationValidator (legacy) не модифицирован
- [ ] CompatibilityEngineV2 — новый класс, не заменяет старый
- [ ] Суррогатные модели — опциональны, при отсутствии используется аналитика

#### **4. Тесты**
- [ ] Все старые тесты проходят без изменений (pytest tests/legacy/)
- [ ] Новые тесты изолированы (pytest tests/new_features/)
- [ ] Integration-тесты используют фикстуры с auth_mode='disabled'
- [ ] Load-тесты не влияют на production-окружение

#### **5. Frontend**
- [ ] Старые страницы не ломаются при добавлении новых компонентов
- [ ] React Query кэширует запросы, но не блокирует старые fetch-вызовы
- [ ] PWA Service Worker не влияет на десктопную версию
- [ ] Offline-режим не перезаписывает серверные данные без синхронизации

#### **6. Производительность**
- [ ] Кэш Redis инвалидируется при изменении паспортов
- [ ] Асинхронный синтез не блокирует синхронный эндпоинт
- [ ] Batch insert не вызывает deadlock
- [ ] Курсоры освобождаются после использования

#### **7. Безопасность**
- [ ] JWT-токены имеют expiration
- [ ] API-ключи хранятся в зашифрованном виде
- [ ] RBAC middleware проверяет роли на всех защищённых эндпоинтах
- [ ] AuditLog фиксирует все изменения

#### **8. Документация**
- [ ] README обновлён с новыми переменными окружения
- [ ] API-документация (Swagger/OpenAPI) включает новые эндпоинты
- [ ] Migration guide описывает шаги для существующих пользователей
- [ ] Troubleshooting section покрывает типичные проблемы

---

## 🎯 Финальные рекомендации

1. **Начните с Фазы 1** — без неё все остальные блоки не будут работать корректно.
2. **Используйте feature flags** для постепенного включения новых функций (например, `ENABLE_MCDA=true`).
3. **Ведите changelog** для каждого релиза, отмечая breaking changes.
4. **Проводите code review** для каждого промта перед реализацией.
5. **Тестируйте на staging-окружении** перед деплоем в production.
6. **Мониторьте метрики** (error rate, response time, cache hit rate) после каждого релиза.

---

**Все 16 промтов готовы к использованию. Удачи в реализации! 🚀**