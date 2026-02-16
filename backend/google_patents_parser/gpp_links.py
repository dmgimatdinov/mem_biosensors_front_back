import sys
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import time
import re

def search_patents(keyword, start_year, end_year):
    base_url = "https://patents.google.com/"
    links = set()
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    })

    page = 1
    max_pages = 50  # Ограничение на случай бесконечной пагинации

    while page <= max_pages:
        params = {
            'q': keyword,
            'before': f'{end_year}-12-31',
            'after': f'{start_year}-01-01',
            'page': page
        }

        try:
            response = session.get(base_url, params=params, timeout=10)
            if response.status_code == 429:
                print(f"Rate limited on page {page}. Waiting 5 seconds...")
                time.sleep(5)
                continue
            response.raise_for_status()
        except requests.RequestException as e:
            print(f"!Request failed on page {page}: {e}")
            break

        soup = BeautifulSoup(response.content, 'html.parser')
        patent_links = soup.find_all('a', href=re.compile(r'/patent/[A-Z0-9]+'))

        page_has_patents = False
        for link in patent_links:
            href = link['href']
            if href.startswith('http'):
                full_url = href
            else:
                full_url = urljoin(base_url, href)
            if full_url.startswith('https://patents.google.com/patent/'):
                links.add(full_url)
                page_has_patents = True

        if not page_has_patents:
            break  # Нет новых патентов — завершаем


        page += 1
        time.sleep(1)  # Пауза между запросами


    return links

if __name__ == '__main__':
    if len(sys.argv) != 4:
        print("Usage: python gpp_links.py <keyword> <start_year> <end_year>", file=sys.stderr)
        sys.exit(1)

    keyword = sys.argv[1]
    try:
        start_year = int(sys.argv[2])
        end_year = int(sys.argv[3])
    except ValueError:
        print("Error: Years must be integers", file=sys.stderr)
        sys.exit(1)

    if start_year > end_year:
        print("Error: Start year must be <= end year", file=sys.stderr)
        sys.exit(1)

    try:
        links = search_patents(keyword, start_year, end_year)
        if not links:
            print("No patents found", file=sys.stderr)
            sys.exit(1)
        with open('patents_links.txt', 'w', encoding='utf-8') as f:
            for link in sorted(links):
                f.write(link + '\n')
    except Exception as e:
        print(f"!Error: {e}", file=sys.stderr)
        sys.exit(1)
