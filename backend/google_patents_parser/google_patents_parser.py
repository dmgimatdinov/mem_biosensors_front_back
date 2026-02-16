"""
Google Patents & Patent Document Parser
=========================================

Компетентный скрипт для извлечения релевантного текста из патентных документов.

ЛОГИКА РАБОТЫ:
  1. Загрузка HTML (requests для статического контента, Selenium для JavaScript)
  2. Парсинг BeautifulSoup с платформо-специфичными CSS селекторами
  3. Извлечение title, abstract, description, claims (без навигации/рекламы)
  4. Нормализация текста: удаление лишних пробелов, сохранение нумерации
  5. Генерация PDF с метаданными и чистым контентом
  6. Логирование всех операций (INFO/ERROR уровни)

ПОДДЕРЖИВАЕМЫЕ ПЛАТФОРМЫ:
  - Google Patents (patents.google.com)
  - USPTO Patents (patents.uspto.gov)
  - European Patent Office (espacenet.com)

ПРИМЕРЫ:
  python google_patents_parser.py --url "https://patents.google.com/patent/US1234567A"
  python google_patents_parser.py --links-file urls.txt --output-dir ./pdfs --use-selenium

ОБРАБОТКА ОШИБОК:
  - 404 Not Found → логирование, пропуск URL
  - Таймауты → автоматический retry с Selenium
  - Изменение структуры → fallback селекторы
"""
from __future__ import annotations

import sys
import argparse
import re
import time
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
    
"""try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    requests = None
    BeautifulSoup = None"""

try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
    from reportlab.lib import colors
except ImportError:
    SimpleDocTemplate = None

# Optional selenium support
try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from webdriver_manager.chrome import ChromeDriverManager
    from selenium.webdriver.chrome.service import Service
    
except Exception:
    webdriver = None
    Options = None
    ChromeDriverManager = None


# ========== ЛОГИРОВАНИЕ ==========
def setup_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """Инициализация логгера с форматом [LEVEL] message."""
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stderr)
        formatter = logging.Formatter('%(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    
    return logger

logger = setup_logger(__name__)


def fetch_with_requests(url: str, timeout: int = 15) -> Optional[str]:
    """Загрузка HTML через requests (для статического контента)."""
    if requests is None:
        logger.error("requests не установлен. Установите: pip install requests")
        raise RuntimeError("requests is not installed. Install with: pip install requests")
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        logger.info(f"Загрузка через requests: {url}")
        r = requests.get(url, headers=headers, timeout=timeout, allow_redirects=True)
        
        if r.status_code == 404:
            logger.error(f"404 Not Found: {url}")
            return None
        
        r.raise_for_status()
        logger.info(f"Успешно загружено ({len(r.text)} байт)")
        return r.text
    except requests.Timeout:
        logger.error(f"Таймаут при загрузке: {url}")
        return None
    except requests.HTTPError as e:
        logger.error(f"HTTP ошибка {r.status_code}: {url}")
        return None
    except Exception as e:
        logger.error(f"Ошибка requests: {e}")
        return None


def fetch_with_selenium(url: str, timeout: int = 20, wait: float = 2.0) -> Optional[str]:
    """
    Загрузка HTML через Selenium (для динамического контента с JavaScript).
    
    Используется для страниц, требующих рендеринга JavaScript:
    - Google Patents (иногда использует AJAX)
    - Сложные UI компоненты
    
    ДИАГНОСТИКА ОШИБОК:
    - "session not created: Chrome instance exited" → несовместимость версий Chrome/ChromeDriver
    - Retry с альтернативными опциями запуска
    - Подробное логирование версий для отладки
    """
    if webdriver is None or ChromeDriverManager is None:
        logger.error("selenium/webdriver-manager не установлены. Установите: pip install selenium webdriver-manager")
        raise RuntimeError("selenium and webdriver-manager are required for --use-selenium. Install with: pip install selenium webdriver-manager")
    
    driver = None
    
    # Попытаемся несколько раз с разными опциями
    chromium_options_variants = [
        # Вариант 1: современный headless режим (Selenium 4.14+)
        {
            'name': 'headless=new (modern)',
            'options': {
                '--headless=new': None,
                '--no-sandbox': None,
                '--disable-dev-shm-usage': None,
                '--disable-gpu': None,
                '--disable-blink-features=AutomationControlled': None,
            },
            'experimental': {'excludeSwitches': ['enable-automation']},
            'prefs': {}
        },
        # Вариант 2: классический headless режим
        {
            'name': 'headless (classic)',
            'options': {
                '--headless': None,  # классический режим
                '--no-sandbox': None,
                '--disable-dev-shm-usage': None,
                '--disable-gpu': None,
                '--disable-blink-features=AutomationControlled': None,
                '--disable-web-resources': None,
            },
            'experimental': {'excludeSwitches': ['enable-automation']},
            'prefs': {}
        },
        # Вариант 3: минимальный набор опций (для критических случаев)
        {
            'name': 'minimal options',
            'options': {
                '--headless': None,
                '--no-sandbox': None,
                '--disable-dev-shm-usage': None,
            },
            'experimental': {},
            'prefs': {}
        },
    ]
    
    for variant_idx, variant in enumerate(chromium_options_variants, 1):
        try:
            logger.info(f"Попытка {variant_idx}: инициализация Chrome с опциями '{variant['name']}'")
            
            # Получаем путь к ChromeDriver и выводим версии
            try:
                chrome_driver_path = ChromeDriverManager().install()
                logger.debug(f"ChromeDriver путь: {chrome_driver_path}")
            except Exception as e:
                logger.error(f"Ошибка при загрузке ChromeDriver: {e}")
                if variant_idx < len(chromium_options_variants):
                    logger.info(f"Пробуем следующий вариант опций...")
                    continue
                else:
                    raise
            
            # Создаём опции
            chrome_options = Options()
            
            # Добавляем основные аргументы
            for arg, value in variant['options'].items():
                if value is None:
                    chrome_options.add_argument(arg)
                else:
                    chrome_options.add_argument(f"{arg}={value}")
            
            # Добавляем экспериментальные опции
            if variant['experimental']:
                for key, val in variant['experimental'].items():
                    chrome_options.add_experimental_option(key, val)
            
            # Добавляем preferences
            if variant['prefs']:
                chrome_options.add_experimental_option("prefs", variant['prefs'])
            
            logger.debug(f"Опции Chrome настроены: {len(variant['options'])} аргументов")
            
            # Создаём Service
            service = Service(chrome_driver_path)
            logger.debug(f"Service создан для {chrome_driver_path}")
            
            # Создаём WebDriver (это обычно самое проблемное место)
            logger.info(f"Создание WebDriver экземпляра...")
            driver = webdriver.Chrome(service=service, options=chrome_options)
            logger.info(f"✓ WebDriver успешно инициализирован с опциями '{variant['name']}'")
            
            # Если дошли сюда - успешно создали драйвер, выходим из цикла
            break
            
        except Exception as e:
            logger.warning(f"Ошибка при попытке {variant_idx} ({variant['name']}): {e}")
            
            # Очищаем драйвер если был создан
            if driver:
                try:
                    driver.quit()
                except Exception:
                    pass
                driver = None
            
            # Если это последняя попытка - выходим с ошибкой
            if variant_idx >= len(chromium_options_variants):
                logger.error(f"Все попытки инициализации Chrome исчерпаны. Последняя ошибка: {e}")
                return None
            
            logger.info(f"Пробуем следующий вариант опций...")
            time.sleep(0.5)  # Небольшая задержка перед следующей попыткой
            continue
    
    # Если не удалось создать драйвер ни одной попыткой
    if driver is None:
        logger.error("Не удалось инициализировать WebDriver ни с одним набором опций")
        return None
    
    try:
        logger.info(f"Загрузка URL через Selenium: {url}")
        driver.set_page_load_timeout(timeout)
        driver.get(url)
        logger.debug(f"Страница загружена, ожидание рендеринга ({wait}с)...")
        time.sleep(wait)  # Ожидание рендеринга JavaScript
        
        html = driver.page_source
        logger.info(f"✓ Успешно загружено через Selenium ({len(html)} байт)")
        return html
    
    except Exception as e:
        logger.error(f"Ошибка при загрузке URL: {e}")
        return None
    
    finally:
        # Безопасное закрытие драйвера
        if driver:
            try:
                driver.quit()
                logger.debug("WebDriver закрыт корректно")
            except Exception as e:
                logger.warning(f"Ошибка при закрытии WebDriver: {e}")


def fetch_patent_page(url: str, use_selenium: bool = False, timeout: int = 20) -> Optional[str]:
    """
    Загрузка страницы патента с автоматическим fallback.
    
    1. Если use_selenium=True: пробуем Selenium, затем fallback на requests
    2. Если use_selenium=False: используем requests напрямую
    """
    if use_selenium:
        logger.info("Режим: Selenium (с fallback на requests)")
        html = fetch_with_selenium(url, timeout=timeout)
        if html:
            return html
        logger.info("Selenium не сработал, пробуем requests...")
        return fetch_with_requests(url, timeout=timeout)
    
    logger.info("Режим: Requests (статический контент)")
    return fetch_with_requests(url, timeout=timeout)


def diagnose_chrome_setup() -> Dict[str, Any]:
    """
    Диагностика окружения Chrome/ChromeDriver.
    Помогает выявить проблемы с совместимостью.
    
    Возвращает информацию о:
    - Наличии Chrome/Chromium
    - Версии ChromeDriver
    - Наличии selenium и webdriver-manager
    - Системных параметрах
    """
    import platform
    import shutil
    
    diagnostics = {
        'python_version': platform.python_version(),
        'platform': platform.system(),
        'platform_release': platform.release(),
        'selenium_installed': webdriver is not None,
        'webdriver_manager_installed': ChromeDriverManager is not None,
    }
    
    # Проверяем наличие Chrome
    chrome_paths = {
        'Windows': [
            r'C:\Program Files\Google\Chrome\Application\chrome.exe',
            r'C:\Program Files (x86)\Google\Chrome\Application\chrome.exe',
        ],
        'Linux': [
            '/usr/bin/google-chrome',
            '/usr/bin/google-chrome-stable',
            '/usr/bin/chromium',
            '/usr/bin/chromium-browser',
        ],
        'Darwin': [  # macOS
            '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
            '/Applications/Chromium.app/Contents/MacOS/Chromium',
        ]
    }
    
    system = platform.system()
    chrome_found = None
    for path in chrome_paths.get(system, []):
        if shutil.which(path.split('/')[0] if '/' in path else path.split('\\')[-1]):
            chrome_found = path
            break
    
    diagnostics['chrome_found'] = chrome_found
    
    # Пробуем получить версию ChromeDriver
    if ChromeDriverManager is not None:
        try:
            driver_path = ChromeDriverManager().install()
            diagnostics['chromedriver_path'] = driver_path
            diagnostics['chromedriver_installed'] = True
        except Exception as e:
            diagnostics['chromedriver_installed'] = False
            diagnostics['chromedriver_error'] = str(e)
    
    logger.info("=== Диагностика Chrome/ChromeDriver ===")
    for key, val in diagnostics.items():
        logger.info(f"  {key}: {val}")
    logger.info("=====================================")
    
    return diagnostics


def extract_full_text(soup: BeautifulSoup) -> str:
    """
    Извлечение ТОЛЬКО релевантного текста патента, исключив:
    - навигационные элементы (header, nav, footer)
    - рекламные блоки (ads, banner)
    - UI элементы (button, script, style)
    - метаданные интерфейса
    
    Сохраняем кодировку UTF-8 и структуру нумерации.
    """
    # Удаляем элементы, не содержащие релевантный контент
    for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
        tag.decompose()
    
    # Удаляем элементы, часто содержащие рекламу/интерфейс
    for tag in soup.find_all(class_=re.compile(r'(nav|menu|footer|ad|banner|cookie|tracking)', re.I)):
        tag.decompose()
    
    # Удаляем элементы с атрибутами, указывающими на интерфейс
    for tag in soup.find_all(id=re.compile(r'(nav|menu|ad|banner|footer|cookie)', re.I)):
        tag.decompose()
    
    # Получаем текст
    text = soup.get_text(separator='\n', strip=True)
    
    # Нормализация пробелов и переносов
    # Сохраняем нумерацию пунктов (1., 2., 1.1., и т.д.)
    lines = []
    for line in text.splitlines():
        line = line.strip()
        if line:
            lines.append(line)
    
    result = '\n'.join(lines)
    
    # Удаляем множественные переносы строк (более 2 подряд)
    result = re.sub(r'\n{3,}', '\n\n', result)
    
    # Кодировка UTF-8 гарантирована
    return result


def parse_patent_data(html: str, url: str = "") -> Dict[str, Any]:
    """
    Парсинг HTML патента с платформо-специфичными селекторами.
    
    СТРАТЕГИЯ:
    1. Пытаемся несколько селекторов для Google Patents
    2. При неудаче — fallback селекторы для USPTO, EPO
    3. Логируем какие селекторы сработали (для отладки)
    
    CSS СЕЛЕКТОРЫ:
    
    Google Patents (patents.google.com):
      title: h1[itemprop="title"], meta[property="og:title"]
      abstract: div[data-test-id="abstract"], .abstract-section
      description: div[data-test-id="description"], .description-section
      claims: div[data-test-id="claims"], .claims-section, [itemprop="description"]
    
    USPTO (patents.uspto.gov):
      title: h1.title, span.title
      abstract: div[role="doc-abstract"], .abstract
      claims: div.claims, .claims-block
    
    EPO (espacenet.com):
      title: .publicationTitle, h1
      abstract: .abstract, [id*="abstract"]
      claims: .claims, [id*="claim"]
    """
    if BeautifulSoup is None:
        logger.error("BeautifulSoup4 не установлена. Установите: pip install beautifulsoup4")
        raise RuntimeError("BeautifulSoup is not installed. Install with: pip install beautifulsoup4")

    try:
        soup = BeautifulSoup(html, 'html.parser')
    except Exception as e:
        logger.error(f"Ошибка парсинга HTML: {e}")
        return {'title': '', 'status': '', 'year': '', 'abstract': '', 'description': '', 'claims': '', 'full_text': ''}

    data: Dict[str, Any] = {
        'title': '',
        'status': '',
        'year': '',
        'abstract': '',
        'description': '',
        'claims': '',
        'full_text': ''
    }

    # Extract full page text first
    logger.info("Извлечение полного текста страницы")
    data['full_text'] = extract_full_text(soup)

    # ========== TITLE (Название патента) ==========
    logger.info("Поиск: Title")
    title_selectors = [
        # Google Patents
        ('h1[itemprop="title"]', 'Google Patents (h1 itemprop)'),
        ('meta[property="og:title"]', 'OG:title meta'),
        ('h1.title', 'h1.title'),
        ('h1', 'Generic h1'),
        # USPTO
        ('span.title', 'USPTO span.title'),
        # EPO
        ('.publicationTitle', 'EPO publicationTitle'),
    ]
    
    for selector, source in title_selectors:
        try:
            if selector.startswith('meta'):
                elem = soup.select_one(selector)
                if elem and elem.get('content'):
                    data['title'] = elem.get('content').strip()
                    logger.info(f"  ✓ Title найден: {source}")
                    break
            else:
                elem = soup.select_one(selector)
                if elem:
                    text = elem.get_text(strip=True)
                    if text:
                        data['title'] = text
                        logger.info(f"  ✓ Title найден: {source}")
                        break
        except Exception as e:
            logger.debug(f"  Селектор {selector} не сработал: {e}")
            continue

    # ========== STATUS (Статус: pending/granted) ==========
    logger.info("Поиск: Status")
    possible_status = soup.find_all(string=re.compile(r'pending|granted|published', re.I))
    if possible_status:
        status_text = possible_status[0].lower()
        if 'pending' in status_text:
            data['status'] = 'pending'
            logger.info("  ✓ Status: pending")
        elif 'granted' in status_text:
            data['status'] = 'granted'
            logger.info("  ✓ Status: granted")

    # ========== YEAR (Год публикации) ==========
    logger.info("Поиск: Year")
    date_elem = soup.find(string=re.compile(r'\d{4}-\d{2}-\d{2}'))
    if date_elem:
        m = re.search(r'(\d{4})', str(date_elem))
        if m:
            data['year'] = m.group(1)
            logger.info(f"  ✓ Year: {data['year']}")
    else:
        m2 = soup.find(string=re.compile(r'\b(19|20)\d{2}\b'))
        if m2:
            m = re.search(r'(19|20)\d{2}', str(m2))
            if m:
                data['year'] = m.group(0)
                logger.info(f"  ✓ Year: {data['year']}")

    # ========== ABSTRACT (Реферат) ==========
    logger.info("Поиск: Abstract")
    abstract_selectors = [
        # Google Patents
        ('div[data-test-id="abstract"]', 'Google Patents data-test-id'),
        ('.abstract-section', 'abstract-section class'),
        ('meta[name="DC.description"]', 'DC.description meta'),
        # Generic
        ('[itemprop="abstract"]', 'itemprop abstract'),
        ('div.abstract', 'Generic div.abstract'),
    ]
    
    for selector, source in abstract_selectors:
        try:
            if selector.startswith('meta'):
                elem = soup.select_one(selector)
                if elem and elem.get('content'):
                    text = elem.get('content').strip()
                    if len(text) > 20:
                        data['abstract'] = text
                        logger.info(f"  ✓ Abstract найден: {source} ({len(text)} символов)")
                        break
            else:
                elem = soup.select_one(selector)
                if elem:
                    text = elem.get_text(separator='\n', strip=True)
                    if len(text) > 20:
                        data['abstract'] = text
                        logger.info(f"  ✓ Abstract найден: {source} ({len(text)} символов)")
                        break
        except Exception as e:
            logger.debug(f"  Селектор {selector} не сработал: {e}")
            continue

    # ========== DESCRIPTION (Полное описание) ==========
    logger.info("Поиск: Description")
    description_selectors = [
        ('div[data-test-id="description"]', 'Google Patents data-test-id'),
        ('.description-section', 'description-section class'),
        ('div.description', 'Generic div.description'),
        ('[itemprop="description"]', 'itemprop description'),
    ]
    
    for selector, source in description_selectors:
        try:
            elem = soup.select_one(selector)
            if elem:
                text = elem.get_text(separator='\n', strip=True)
                if len(text) > 50:
                    data['description'] = text
                    logger.info(f"  ✓ Description найден: {source} ({len(text)} символов)")
                    break
        except Exception as e:
            logger.debug(f"  Селектор {selector} не сработал: {e}")
            continue

    # ========== CLAIMS (Формула изобретения) ==========
    logger.info("Поиск: Claims")
    claims_selectors = [
        ('div[data-test-id="claims"]', 'Google Patents data-test-id'),
        ('.claims-section', 'claims-section class'),
        ('div.claims', 'Generic div.claims'),
        ('[itemprop="claims"]', 'itemprop claims'),
    ]
    
    claims_full = ''
    claims_container = None
    
    for selector, source in claims_selectors:
        try:
            elem = soup.select_one(selector)
            if elem:
                claims_container = elem
                logger.info(f"  ✓ Claims контейнер найден: {source}")
                break
        except Exception as e:
            logger.debug(f"  Селектор {selector} не сработал: {e}")
            continue
    
    if not claims_container:
        # Fallback: ищем heading "Claims" и берём всё после него
        for h in soup.find_all(['h1', 'h2', 'h3', 'h4']):
            h_text = h.get_text(strip=True).lower()
            if 'claim' in h_text or 'what is claimed' in h_text:
                claims_container = h
                logger.info(f"  ℹ Использован fallback: heading с текстом 'Claims'")
                break
    
    if claims_container:
        all_text = []
        if claims_container.name in ['h1', 'h2', 'h3', 'h4']:
            current = claims_container.find_next()
        else:
            current = claims_container.find('li') or claims_container.find('p') or claims_container.find_next()
        
        while current:
            curr_text = current.get_text(strip=True).lower()
            
            # Stop markers для остановки сбора claims
            stop_markers = [
                'similar documents', 'related patents', 'prior art', 
                'cited by', 'also published', 'back to top',
                'references cited', 'examiner signature'
            ]
            
            if any(marker in curr_text for marker in stop_markers):
                logger.debug(f"  Остановка на маркере: {stop_markers[0]}")
                break
            
            # Stop на другие основные секции
            if current.name in ['h1', 'h2', 'h3', 'h4'] and current != claims_container:
                other_sections = ['abstract', 'description', 'figure', 'inventor', 'applicant', 'references']
                if any(word in curr_text for word in other_sections):
                    logger.debug(f"  Остановка на заголовке: {curr_text[:50]}")
                    break
            
            # Сбор текста (сохраняем нумерацию пунктов: 1., 1.1., и т.д.)
            if current.name in ['li', 'p', 'div', 'span', 'div']:
                text = current.get_text(strip=True)
                if text and len(text) > 5:
                    all_text.append(text)
            
            current = current.find_next()
        
        if all_text:
            claims_full = '\n\n'.join(all_text)
            logger.info(f"  ✓ Claims собраны ({len(all_text)} пунктов, {len(claims_full)} символов)")
    
    data['claims'] = claims_full

    return data


def extract_title_words(title: str, num_words: int = 3) -> str:
    stop_words = {'and', 'or', 'the', 'a', 'an', 'of', 'for', 'in', 'on', 'with', 'by', 'to'}
    words = [w.replace(',', '').replace('.', '') for w in (title or '').split()]
    meaningful = [w for w in words if w.lower() not in stop_words and len(w) > 2]
    return '_'.join(meaningful[:num_words]).lower()


def generate_filename(patent_data: Dict[str, Any]) -> str:
    parts: List[str] = []
    if patent_data.get('status') == 'pending':
        parts.append('pending')
    if patent_data.get('year'):
        parts.append(patent_data['year'])
    title_words = extract_title_words(patent_data.get('title', 'patent'), num_words=3)
    parts.append(title_words or 'patent')
    filename = '_'.join(parts) + '.pdf'
    filename = re.sub(r'[<>:\\"/\\|?*]', '', filename)
    filename = filename.replace('__', '_')
    return filename


def create_pdf(patent_data: Dict[str, Any], output_path: str) -> bool:
    """
    Создание PDF с метаданными и чистым контентом.
    
    Структура PDF:
    1. Заголовок + статус + год
    2. Abstract (до 2000 символов)
    3. Description (до 2000 символов)
    4. Claims (до 5000 символов, на отдельной странице)
    5. Full Page Content (релевантный текст, до 15000 символов)
    
    Исключены: навигация, реклама, интерфейс.
    Сохранена нумерация пунктов формулы изобретения.
    """
    if SimpleDocTemplate is None:
        logger.error("reportlab не установлена. Установите: pip install reportlab")
        print("reportlab is not installed. Install with: pip install reportlab", file=sys.stderr)
        return False
    
    try:
        doc = SimpleDocTemplate(output_path, pagesize=letter)
        story = []
        styles = getSampleStyleSheet()
        
        # Custom styles для лучшей читаемости
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=14,
            textColor=colors.HexColor('#1f4788'),
            spaceAfter=12,
            fontName='Helvetica-Bold'
        )
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=12,
            textColor=colors.HexColor('#2e5c8a'),
            spaceAfter=8,
            spaceBefore=12,
            fontName='Helvetica-Bold'
        )
        body_style = ParagraphStyle(
            'CustomBody',
            parent=styles['BodyText'],
            fontSize=10,
            alignment=4  # Justify
        )

        # Title and metadata
        title = patent_data.get('title', 'Patent Document')
        story.append(Paragraph(title, title_style))
        
        metadata = []
        if patent_data.get('status'):
            metadata.append(f"<b>Status:</b> {patent_data['status'].capitalize()}")
        if patent_data.get('year'):
            metadata.append(f"<b>Year:</b> {patent_data['year']}")
        if metadata:
            story.append(Paragraph(" | ".join(metadata), body_style))
            story.append(Spacer(1, 12))

        # Abstract section
        if patent_data.get('abstract'):
            story.append(Paragraph("Abstract", heading_style))
            abstract_text = patent_data['abstract']
            if len(abstract_text) > 2000:
                abstract_text = abstract_text[:2000] + "..."
            story.append(Paragraph(abstract_text, body_style))
            story.append(Spacer(1, 12))

        # Description section
        if patent_data.get('description'):
            story.append(Paragraph("Description", heading_style))
            description_text = patent_data['description']
            if len(description_text) > 2000:
                description_text = description_text[:2000] + "..."
            story.append(Paragraph(description_text, body_style))
            story.append(Spacer(1, 12))

        # Claims section (with page break if needed)
        if patent_data.get('claims'):
            story.append(PageBreak() if len(story) > 10 else Spacer(1, 12))
            story.append(Paragraph("Claims (Formula of Invention)", heading_style))
            claims_text = patent_data['claims']
            if len(claims_text) > 5000:
                claims_text = claims_text[:5000] + "..."
            story.append(Paragraph(claims_text, body_style))
            story.append(Spacer(1, 12))

        # Full page content (clean, without navigation/ads)
        if patent_data.get('full_text'):
            story.append(PageBreak())
            story.append(Paragraph("Full Page Content (Extracted Text)", heading_style))
            full_text = patent_data['full_text']
            # Limit to reasonable size
            if len(full_text) > 15000:
                full_text = full_text[:15000] + "... [truncated]"
            story.append(Paragraph(full_text, body_style))

        doc.build(story)
        logger.info(f"✓ PDF успешно создан: {output_path}")
        return True
    
    except Exception as e:
        logger.error(f"Ошибка создания PDF: {e}")
        return False


def _read_links_file(p: Path) -> List[str]:
    """Чтение файла со списком URL (один URL на строку)."""
    if not p.exists():
        logger.error(f"Файл не найден: {p}")
        return []
    try:
        lines = [l.strip() for l in p.read_text(encoding='utf-8', errors='ignore').splitlines()]
        valid_urls = [l for l in lines if l and (l.startswith('http://') or l.startswith('https://'))]
        logger.info(f"Прочитано {len(valid_urls)} URL из {p}")
        return valid_urls
    except Exception as e:
        logger.error(f"Ошибка чтения файла {p}: {e}")
        return []


def main(argv: List[str] | None = None) -> int:
    """Основная функция CLI."""
    parser = argparse.ArgumentParser(
        description="Извлечение релевантного текста из патентных документов",
        epilog="""
Примеры:
  python google_patents_parser.py --url "https://patents.google.com/patent/US1234567A"
  python google_patents_parser.py --links-file urls.txt --output-dir ./pdfs --use-selenium
  python google_patents_parser.py --url "https://patents.google.com/patent/EP1234567A1" --output patent.pdf
  python google_patents_parser.py --diagnose  # Проверка окружения Chrome/Selenium
        """
    )
    parser.add_argument("--url", "-u", help="URL патента (Google Patents, USPTO, EPO)")
    parser.add_argument("--links-file", help="Файл со списком URL (один на строку)")
    parser.add_argument("--output", "-o", help="Путь к выходному PDF (авто-генерируется, если не указано)")
    parser.add_argument("--output-dir", "-d", help="Директория для сохранения PDF (по умолчанию: .)", default='.')
    parser.add_argument("--use-selenium", action='store_true', help="Использовать Selenium (для JS контента)")
    parser.add_argument("--timeout", type=int, default=20, help="Таймаут загрузки в секундах (по умолчанию: 20)")
    parser.add_argument("--verbose", "-v", action='store_true', help="Подробный лог (DEBUG уровень)")
    parser.add_argument("--diagnose", action='store_true', help="Диагностика окружения Chrome/Selenium и выход")
    
    args = parser.parse_args(argv)
    
    # Устанавливаем уровень логирования
    if args.verbose:
        logger.setLevel(logging.DEBUG)
    
    logger.info("=== Google Patents Parser ===")
    
    # Диагностика если запрошена
    if args.diagnose:
        diagnostics = diagnose_chrome_setup()
        if not diagnostics['selenium_installed']:
            logger.error("❌ selenium не установлен. Установите: pip install selenium")
        if not diagnostics['webdriver_manager_installed']:
            logger.error("❌ webdriver-manager не установлен. Установите: pip install webdriver-manager")
        if not diagnostics['chrome_found']:
            logger.warning("⚠️ Chrome не найден в стандартных местах (может быть установлен в другом месте)")
        if diagnostics.get('chromedriver_installed'):
            logger.info(f"✅ ChromeDriver готов к использованию")
        else:
            logger.error(f"❌ Ошибка ChromeDriver: {diagnostics.get('chromedriver_error', 'неизвестная ошибка')}")
        return 0
    
    logger.info(f"Режим: {'Selenium' if args.use_selenium else 'Requests'}")

    out_dir = Path(args.output_dir)
    try:
        out_dir.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        logger.error(f"Не удалось создать директорию {out_dir}: {e}")
        return 1

    # Формируем список URL для обработки
    urls: List[str] = []
    if args.links_file:
        logger.info(f"Читаем URL из файла: {args.links_file}")
        urls = _read_links_file(Path(args.links_file))
        if not urls:
            logger.error("Файл пуст или не содержит валидных URL")
            return 2
    elif args.url:
        urls = [args.url]
    else:
        logger.error("Необходимо указать --url или --links-file")
        parser.error("Either --url or --links-file must be provided")

    logger.info(f"Начинаем обработку {len(urls)} URL")
    successful = 0
    failed = 0

    for idx, url in enumerate(urls, start=1):
        logger.info(f"\n[{idx}/{len(urls)}] ═══════════════════════════════════")
        logger.info(f"URL: {url}")
        
        # Загружаем страницу
        html = fetch_patent_page(url, use_selenium=bool(args.use_selenium), timeout=args.timeout)
        if not html:
            logger.error(f"✗ Не удалось загрузить страницу")
            failed += 1
            continue
        
        # Парсим данные
        try:
            logger.info("Парсинг HTML...")
            patent_data = parse_patent_data(html, url=url)
        except Exception as e:
            logger.error(f"Ошибка парсинга: {e}")
            failed += 1
            continue

        # Определяем путь выходного файла
        if len(urls) == 1 and args.output:
            out_path = Path(args.output)
            if out_path.is_dir():
                filename = generate_filename(patent_data)
                out_path = out_path / filename
        else:
            filename = generate_filename(patent_data)
            out_path = out_dir / filename

        # Создаём PDF
        logger.info(f"Создание PDF: {out_path}")
        if create_pdf(patent_data, str(out_path)):
            logger.info(f"✓ Успешно: {out_path}")
            successful += 1
        else:
            logger.error(f"✗ Ошибка создания PDF")
            failed += 1

    logger.info(f"\n═══════════════════════════════════")
    logger.info(f"Итого: {successful} успешно, {failed} ошибок из {len(urls)}")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
