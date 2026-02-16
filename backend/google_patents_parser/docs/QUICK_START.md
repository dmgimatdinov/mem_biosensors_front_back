# 🚀 Быстрый старт Google Patents Parser v2.0

## За 1 минуту

### 1. Проверка установки
```bash
cd /workspaces/memristive_biosensors
python google_patents_parser/google_patents_parser.py --help
```

### 2. Первый парсинг (требует интернет)
```bash
python google_patents_parser/google_patents_parser.py \
  --url "https://patents.google.com/patent/US10200000B2" \
  --verbose
```

### 3. Пакетный парсинг
```bash
# Создаём файл с URL
cat > urls.txt << 'URLS'
https://patents.google.com/patent/US10200000B2
https://patents.google.com/patent/US11000000A1
URLS

# Парсим
python google_patents_parser/google_patents_parser.py \
  --links-file urls.txt \
  --output-dir ./output_patents
```

## Что изменилось?

### ✨ Новое в v2.0

| Функция | Описание |
|---------|---------|
| 📝 **Логирование** | INFO/ERROR/DEBUG уровни (флаг `--verbose`) |
| 🎯 **3 платформы** | Google Patents, USPTO, EPO |
| 🔄 **Fallback селекторы** | Устойчивость к изменениям структуры |
| 📊 **Очистка текста** | Исключены nav/ads/footer |
| 🛡️ **Обработка ошибок** | 404, таймауты, синтаксис |
| 📚 **Документация** | Полное руководство + примеры |
| 💬 **Комментарии** | Docstring для всех функций |

## Важные параметры

```bash
--url URL              # Один патент
--links-file FILE      # Пакетный парсинг
--output-dir DIR       # Директория для PDF
--use-selenium         # Для JavaScript контента
--verbose              # DEBUG лог
--timeout SEC          # Таймаут загрузки (по умолчанию: 20)
```

## Примеры одной строкой

```bash
# Google Patents
python google_patents_parser/google_patents_parser.py --url "https://patents.google.com/patent/US1234567A"

# С Selenium
python google_patents_parser/google_patents_parser.py --url "https://patents.google.com/patent/US1234567A" --use-selenium

# USPTO
python google_patents_parser/google_patents_parser.py --url "https://patents.uspto.gov/patent/US10987654"

# EPO
python google_patents_parser/google_patents_parser.py --url "https://espacenet.com/patent/EP1234567/en" --use-selenium

# Пакетный
python google_patents_parser/google_patents_parser.py --links-file urls.txt --output-dir ./pdfs

# С подробным логом
python google_patents_parser/google_patents_parser.py --url "https://patents.google.com/patent/US1234567A" --verbose
```

## Структура PDF

```
✓ Title (заголовок)
✓ Status & Year (метаданные)
✓ Abstract (реферат)
✓ Description (описание)
✓ Claims (формула изобретения - сохранена нумерация!)
✓ Full Page Content (весь релевантный текст)
```

## Обработка ошибок

Скрипт **не прерывается** при ошибках:
- ❌ 404 Not Found → логирование, пропуск
- ❌ Таймаут → retry с Selenium
- ❌ Изменение селектора → fallback селекторы

## Вывод логирования

```
INFO - === Google Patents Parser ===
INFO - Режим: Requests
INFO - [1/1] ═══════════════════════════════════
INFO - URL: https://patents.google.com/patent/US1234567A
INFO - Загрузка через requests: ...
INFO - Успешно загружено (45231 байт)
INFO - Парсинг HTML...
INFO -   ✓ Title найден
INFO -   ✓ Status: pending
INFO -   ✓ Year: 2024
INFO -   ✓ Abstract найден (342 символов)
INFO -   ✓ Description найден (1856 символов)
INFO -   ✓ Claims собраны (12 пунктов)
INFO - ✓ PDF успешно создан: pending_2024_system_wireless.pdf
INFO - Итого: 1 успешно, 0 ошибок из 1
```

## Файлы в проекте

- **google_patents_parser.py** - Основной скрипт
- **PATENT_PARSER_GUIDE.md** - Полное руководство
- **PARSER_UPDATES.md** - Описание обновлений
- **EXAMPLES.sh** - Примеры использования
- **THIS_CHECKLIST.md** - Чек-лист требований
- **QUICK_START.md** - Этот файл

## Требования

```bash
pip install requests beautifulsoup4 reportlab

# Дополнительно для --use-selenium
pip install selenium webdriver-manager
```

## Поддержка

Если парсинг не работает:
1. Проверьте, доступен ли URL с браузера
2. Запустите с `--verbose` для DEBUG информации
3. Попробуйте `--use-selenium` для JavaScript контента
4. Проверьте, не изменилась ли структура страницы

## ✅ Статус

- ✅ Логирование (INFO/ERROR/DEBUG)
- ✅ 3 платформы (Google, USPTO, EPO)
- ✅ Очистка текста (без nav/ads)
- ✅ Обработка ошибок
- ✅ Документация
- ✅ Примеры
- ✅ Готов к продакшену

**Версия: 2.0 | Статус: ✅ Готов | Python: 3.9+**
