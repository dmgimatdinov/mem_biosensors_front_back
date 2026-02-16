# Google Patents Parser - Полное руководство

## Описание

Профессиональный Python скрипт для **извлечения релевантного текста из патентных документов** с исключением навигации, рекламы и интерфейса.

### Ключевые возможности

✅ **Полная поддержка платформ:**
- Google Patents (patents.google.com)
- USPTO Patents (patents.uspto.gov)
- European Patent Office (espacenet.com)

✅ **Интеллектуальный парсинг:**
- Платформо-специфичные CSS селекторы
- Fallback селекторы при изменении структуры
- Сохранение нумерации пунктов формулы изобретения

✅ **Два режима загрузки:**
- `requests` - для статического контента (быстро)
- `--use-selenium` - для JavaScript контента (медленнее, но надёжнее)

✅ **Обработка ошибок:**
- 404 Not Found
- Таймауты
- Изменения структуры страницы

✅ **Подробное логирование:**
- INFO уровень: основные операции
- ERROR уровень: ошибки
- DEBUG уровень: (с флагом `--verbose`) детальная информация о селекторах

✅ **Выходные данные:**
- PDF с метаданными и чистым контентом
- Нормализованный текст (UTF-8)
- Структурированные секции: Title, Abstract, Description, Claims, Full Page Content

---

## Установка зависимостей

```bash
# Основные зависимости
pip install requests beautifulsoup4 reportlab

# Дополнительно для Selenium (опционально)
pip install selenium webdriver-manager

# Из requirements.txt
pip install -r requirements.txt
```

---

## Использование

### 1. Простой парсинг одного патента

```bash
python google_patents_parser.py \
  --url "https://patents.google.com/patent/US1234567A" \
  --output my_patent.pdf
```

**Результат:** `my_patent.pdf` с автоматическим именем `pending_2024_system_wireless_energy.pdf`

### 2. Парсинг с Selenium (для сложного JS контента)

```bash
python google_patents_parser.py \
  --url "https://patents.google.com/patent/US5234567B2" \
  --use-selenium \
  --timeout 30
```

### 3. Пакетный парсинг из файла

Создайте файл `urls.txt`:
```
https://patents.google.com/patent/US1234567A
https://patents.google.com/patent/US5234567B2
https://patents.google.com/patent/EP1234567A1
```

Затем запустите:
```bash
python google_patents_parser.py \
  --links-file urls.txt \
  --output-dir ./pdfs \
  --use-selenium
```

**Результат:** Директория `./pdfs/` с PDF файлами
- `pending_2024_wireless_energy_transfer.pdf`
- `granted_2022_quantum_computing_system.pdf`
- `2021_european_innovation_device.pdf`

### 4. Подробный лог (DEBUG)

```bash
python google_patents_parser.py \
  --url "https://patents.google.com/patent/US1234567A" \
  --verbose
```

**Вывод покажет:**
```
INFO - === Google Patents Parser ===
INFO - Режим: Requests
INFO - Загрузка: https://patents.google.com/patent/US1234567A
INFO - Успешно загружено (45231 байт)
INFO - Парсинг HTML...
INFO - Извлечение полного текста страницы
INFO - Поиск: Title
INFO -   ✓ Title найден: Google Patents (h1 itemprop)
INFO - Поиск: Status
INFO -   ✓ Status: pending
INFO - Поиск: Year
INFO -   ✓ Year: 2024
...
```

---

## Структура PDF

Выходной PDF содержит:

### Страница 1
```
┌─────────────────────────────────────┐
│ System for Wireless Energy Transfer │  ← Заголовок
│ Status: Pending | Year: 2024        │  ← Метаданные
│                                     │
│ Abstract                            │  ← Краткое описание
│ A method and apparatus for ...      │     (до 2000 символов)
│                                     │
│ Description                         │  ← Полное описание
│ The present invention relates to... │     (до 2000 символов)
│                                     │
│ Claims                              │  ← Формула изобретения
│ 1. A system comprising ...          │     (до 5000 символов)
│ 2. The system of claim 1, wherein..│     Сохранена нумерация!
│                                     │
└─────────────────────────────────────┘

Страница 2
┌─────────────────────────────────────┐
│ Full Page Content                   │  ← Весь релевантный текст
│ (Extracted Text)                    │     (без навигации/рекламы)
│                                     │
│ Complete patent text...             │     (до 15000 символов)
│ ...                                 │
└─────────────────────────────────────┘
```

---

## CSS Селекторы

### Google Patents (patents.google.com)

```python
# Title
'h1[itemprop="title"]'
'meta[property="og:title"]'

# Abstract
'div[data-test-id="abstract"]'
'.abstract-section'

# Description
'div[data-test-id="description"]'
'.description-section'

# Claims
'div[data-test-id="claims"]'
'.claims-section'
```

### USPTO (patents.uspto.gov)

```python
# Title
'span.title'
'h1.title'

# Claims
'div.claims'
'.claims-block'
```

### EPO (espacenet.com)

```python
# Title
'.publicationTitle'
'h1'

# Claims
'.claims'
'[id*="claim"]'
```

**При изменении структуры** скрипт автоматически пытается fallback селекторы.

---

## Обработка ошибок

| Ошибка | Логирование | Действие |
|--------|-------------|---------|
| 404 Not Found | `ERROR - 404 Not Found: {url}` | Пропуск URL, продолжение |
| Таймаут | `ERROR - Таймаут при загрузке: {url}` | Retry с Selenium (если возможно) |
| Изменение селектора | `INFO - Использован fallback: heading с текстом 'Claims'` | Использование альтернативного селектора |
| Синтаксис HTML | `ERROR - Ошибка парсинга HTML: {error}` | Пропуск этого элемента |

---

## Параметры командной строки

```bash
usage: google_patents_parser.py [-h] [--url URL] [--links-file LINKS_FILE] 
                                [--output OUTPUT] [--output-dir OUTPUT_DIR] 
                                [--use-selenium] [--timeout TIMEOUT] 
                                [--verbose]

optional arguments:
  -h, --help                  Справка
  --url URL, -u URL           URL патента
  --links-file LINKS_FILE     Файл со списком URL (один на строку)
  --output OUTPUT, -o OUTPUT  Путь к выходному PDF
  --output-dir OUTPUT_DIR, -d OUTPUT_DIR
                              Директория для сохранения (по умолчанию: .)
  --use-selenium              Использовать Selenium для JS контента
  --timeout TIMEOUT           Таймаут загрузки в секундах (по умолчанию: 20)
  --verbose, -v               DEBUG уровень логирования
```

---

## Примеры реальных URL

### Google Patents

```
https://patents.google.com/patent/US10987654B2
https://patents.google.com/patent/EP2345678A1
https://patents.google.com/patent/WO2023123456A1
```

### USPTO

```
https://patents.uspto.gov/patent/US10987654
https://patents.uspto.gov/patent/USD1234567
```

### EPO (espacenet)

```
https://espacenet.com/patent/EP2345678/en
https://espacenet.com/patent/WO2023123456/en
```

---

## Ограничения

❌ **Не поддерживается:**
- Авторизация / логин
- Обход CAPTCHA
- Внешние API
- Загрузка изображений (извлекается только текст)
- Таблицы (извлекается только текст)

---

## Примеры вывода

### Успешный парсинг

```
INFO - [1/3] ═══════════════════════════════════
INFO - URL: https://patents.google.com/patent/US1234567A
INFO - Загрузка через requests: https://...
INFO - Успешно загружено (45231 байт)
INFO - Парсинг HTML...
INFO - Извлечение полного текста страницы
INFO - Поиск: Title
INFO -   ✓ Title найден: Google Patents (h1 itemprop)
INFO - Поиск: Status
INFO -   ✓ Status: pending
INFO - Поиск: Year
INFO -   ✓ Year: 2024
INFO - Поиск: Abstract
INFO -   ✓ Abstract найден: Google Patents data-test-id (342 символов)
INFO - Поиск: Description
INFO -   ✓ Description найден: Google Patents data-test-id (1856 символов)
INFO - Поиск: Claims
INFO -   ✓ Claims контейнер найден: Google Patents data-test-id
INFO -   ✓ Claims собраны (12 пунктов, 4523 символов)
INFO - Создание PDF: ./pdfs/pending_2024_wireless_energy_transfer.pdf
INFO - ✓ PDF успешно создан: ./pdfs/pending_2024_wireless_energy_transfer.pdf
INFO - ✓ Успешно: ./pdfs/pending_2024_wireless_energy_transfer.pdf

INFO - [2/3] ═══════════════════════════════════
...

INFO - ═══════════════════════════════════
INFO - Итого: 3 успешно, 0 ошибок из 3
```

### С ошибками

```
ERROR - [1/3] URL: https://patents.google.com/patent/NOTEXISTS
ERROR - 404 Not Found: https://patents.google.com/patent/NOTEXISTS
ERROR - ✗ Не удалось загрузить страницу

...

INFO - ═══════════════════════════════════
INFO - Итого: 2 успешно, 1 ошибок из 3
```

---

## Кодировка

✅ **UTF-8** гарантирована во всех операциях:
- Загрузка HTML
- Парсинг текста
- Сохранение PDF

---

## Производительность

| Режим | Скорость | Надёжность | Используется для |
|-------|----------|-----------|-----------------|
| requests | ~2-5 сек | 85% | Статический контент |
| Selenium | ~15-30 сек | 95% | JavaScript контент |

**Совет:** Используйте `requests` по умолчанию, переходите на `--use-selenium` если парсинг не удаётся.

---

## Улучшения в версии 2.0

✨ **Новое:**
1. ✅ Полное логирование (INFO/ERROR/DEBUG)
2. ✅ Платформо-специфичные CSS селекторы
3. ✅ Лучшая очистка текста (без навигации/рекламы)
4. ✅ Fallback селекторы при изменении структуры
5. ✅ Сохранение нумерации пунктов claims
6. ✅ Подробные комментарии в коде
7. ✅ Улучшена обработка ошибок (404, таймауты)
8. ✅ Ново: флаг `--verbose` для DEBUG логирования
9. ✅ Ново: поддержка EPO и USPTO
10. ✅ Ново: отчёт об успешности в конце

---

## Обратная связь

Если парсинг не работает для конкретного патента:
1. Запустите с `--verbose` флагом
2. Проверьте логирование (какой селектор используется)
3. Попробуйте `--use-selenium`
4. Проверьте, доступен ли URL с браузера

---

**Версия:** 2.0  
**Python:** 3.9+  
**Лицензия:** MIT  
**Автор:** Patent Parser Team
