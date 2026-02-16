#!/bin/bash
# Примеры использования Google Patents Parser
# ============================================

echo "=== Google Patents Parser - Примеры ==="
echo ""

# Пример 1: Парсинг одного патента (базовый)
echo "1. Парсинг одного патента (Google Patents, requests):"
echo "   python google_patents_parser.py --url \"https://patents.google.com/patent/US1234567A\" --output patent.pdf"
echo ""

# Пример 2: С Selenium (для сложного JS)
echo "2. С Selenium (для JavaScript контента):"
echo "   python google_patents_parser.py --url \"https://patents.google.com/patent/US5234567B2\" --use-selenium"
echo ""

# Пример 3: Пакетный парсинг
echo "3. Пакетный парсинг из файла urls.txt:"
echo "   python google_patents_parser.py --links-file urls.txt --output-dir ./pdfs"
echo ""

# Пример 4: Пакетный + Selenium + подробный лог
echo "4. Пакетный парсинг с Selenium и DEBUG логом:"
echo "   python google_patents_parser.py --links-file urls.txt --output-dir ./pdfs --use-selenium --verbose"
echo ""

# Пример 5: USPTO патент
echo "5. Парсинг USPTO патента:"
echo "   python google_patents_parser.py --url \"https://patents.uspto.gov/patent/US10987654\" --output-dir ./patents"
echo ""

# Пример 6: EPO (европейский офис патентов)
echo "6. Парсинг EPO (espacenet):"
echo "   python google_patents_parser.py --url \"https://espacenet.com/patent/EP2345678/en\" --use-selenium"
echo ""

# Пример 7: С длительным таймаутом
echo "7. С длительным таймаутом (для медленных соединений):"
echo "   python google_patents_parser.py --url \"https://patents.google.com/patent/WO2023123456A1\" --timeout 60"
echo ""

# ============================================
# Структура файла urls.txt для примера 3:
# ============================================
echo "Пример содержимого файла urls.txt:"
echo "---"
cat << 'EOF'
https://patents.google.com/patent/US10987654B2
https://patents.google.com/patent/EP2345678A1
https://patents.google.com/patent/WO2023123456A1
https://patents.uspto.gov/patent/US5234567
https://espacenet.com/patent/EP1234567A1/en
EOF
echo "---"
echo ""

# Реальные примеры URL
echo "РЕАЛЬНЫЕ ПРИМЕРЫ URL:"
echo ""
echo "Google Patents:"
echo "  https://patents.google.com/patent/US10200000B2 - Беспроводная передача энергии"
echo "  https://patents.google.com/patent/US11000000A1 - Квантовые вычисления"
echo ""
echo "USPTO:"
echo "  https://patents.uspto.gov/patent/US10987654 - Проверенный патент"
echo "  https://patents.uspto.gov/patent/USD1234567 - Дизайн-патент"
echo ""
echo "EPO (espacenet):"
echo "  https://espacenet.com/patent/EP3000000/en - Европейский патент"
echo "  https://espacenet.com/patent/WO2023000000/en - PCT патент"
echo ""

echo "Справка по параметрам:"
echo "  -h, --help              Показать справку"
echo "  --url URL, -u URL       URL патента"
echo "  --links-file FILE       Файл со списком URL (один на строку)"
echo "  --output PDF, -o PDF    Путь к выходному PDF"
echo "  --output-dir DIR, -d    Директория для сохранения (по умолчанию: .)"
echo "  --use-selenium          Использовать Selenium (для JS контента)"
echo "  --timeout SEC           Таймаут загрузки в секундах (по умолчанию: 20)"
echo "  --verbose, -v           DEBUG уровень логирования"
echo ""

echo "Структура выходного PDF:"
echo "  Страница 1:"
echo "    - Title (заголовок)"
echo "    - Status & Year (метаданные)"
echo "    - Abstract (реферат, до 2000 символов)"
echo "    - Description (описание, до 2000 символов)"
echo "    - Claims (формула изобретения, до 5000 символов)"
echo ""
echo "  Страница 2+:"
echo "    - Full Page Content (весь релевантный текст, без навигации/рекламы)"
echo ""
