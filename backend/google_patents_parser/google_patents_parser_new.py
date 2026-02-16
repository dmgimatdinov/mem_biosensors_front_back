"""Google Patents parser - extract and save patent information to PDF.

Usage (CLI):
    python google_patents_parser.py --url "https://patents.google.com/patent/US1234567B2" --output patent.pdf

Features added:
- Selenium-based fetching (`--use-selenium`) with webdriver-manager fallback
- Batch parsing from links file (`--links-file`)
- Specify output directory (`--output-dir`)
- Full claims extraction until "similar documents" section
"""
from __future__ import annotations

import sys
import argparse
import re
import time
from pathlib import Path
from typing import Optional, Dict, Any, List

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    requests = None
    BeautifulSoup = None

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
except Exception:
    webdriver = None
    Options = None
    ChromeDriverManager = None


def fetch_with_requests(url: str, timeout: int = 15) -> Optional[str]:
    if requests is None:
        raise RuntimeError("requests is not installed. Install with: pip install requests")
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        r = requests.get(url, headers=headers, timeout=timeout)
        r.raise_for_status()
        return r.text
    except Exception as e:
        print(f"Error fetching with requests: {e}", file=sys.stderr)
        return None


def fetch_with_selenium(url: str, timeout: int = 20, wait: float = 2.0) -> Optional[str]:
    if webdriver is None or ChromeDriverManager is None:
        raise RuntimeError("selenium and webdriver-manager are required for --use-selenium. Install with: pip install selenium webdriver-manager")
    try:
        chrome_options = Options()
        chrome_options.add_argument('--headless=new')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')

        driver = webdriver.Chrome(ChromeDriverManager().install(), options=chrome_options)
        driver.set_page_load_timeout(timeout)
        driver.get(url)
        # small wait to let JS render essential parts
        time.sleep(wait)
        html = driver.page_source
        driver.quit()
        return html
    except Exception as e:
        print(f"Error fetching with selenium: {e}", file=sys.stderr)
        try:
            driver.quit()
        except Exception:
            pass
        return None


def fetch_patent_page(url: str, use_selenium: bool = False, timeout: int = 20) -> Optional[str]:
    """Fetch Google Patents page HTML. Use Selenium if requested, otherwise requests."""
    if use_selenium:
        html = fetch_with_selenium(url, timeout=timeout)
        if html:
            return html
        # fallback
        return fetch_with_requests(url, timeout=timeout)
    return fetch_with_requests(url, timeout=timeout)


def _get_text_by_selectors(soup: BeautifulSoup, selectors: List[str]) -> str:
    for sel in selectors:
        try:
            if sel.startswith('//'):
                # lxml/xpath not available through BeautifulSoup; skip
                continue
            el = soup.select_one(sel)
            if el and el.get_text(strip=True):
                return el.get_text(strip=True)
        except Exception:
            continue
    return ""


def parse_patent_data(html: str) -> Dict[str, Any]:
    if BeautifulSoup is None:
        raise RuntimeError("BeautifulSoup is not installed. Install with: pip install beautifulsoup4")

    soup = BeautifulSoup(html, 'html.parser')
    data: Dict[str, Any] = {'title': '', 'status': '', 'year': '', 'abstract': '', 'description': '', 'claims': ''}

    # Title: try meta tags, itemprop, h1
    title_selectors = [
        'meta[name="DC.title"]',
        'meta[property="og:title"]',
        'h1[itemprop="title"]',
        'h1.title',
        'h1',
        'title'
    ]
    title = ''
    for sel in title_selectors:
        if sel.startswith('meta'):
            meta = soup.select_one(sel)
            if meta and meta.get('content'):
                title = meta.get('content').strip()
                break
        else:
            title = _get_text_by_selectors(soup, [sel])
            if title:
                break
    data['title'] = title or ''

    # Status: look for pending/grant keywords near status labels
    status_text = ''
    possible_status = soup.find_all(string=re.compile(r'pending|granted|published', re.I))
    if possible_status:
        status_text = possible_status[0].lower()
        if 'pending' in status_text:
            data['status'] = 'pending'
        elif 'granted' in status_text:
            data['status'] = 'granted'

    # Year: find date-like strings
    date_elem = soup.find(string=re.compile(r'\d{4}-\d{2}-\d{2}'))
    if date_elem:
        m = re.search(r'(\d{4})', str(date_elem))
        if m:
            data['year'] = m.group(1)
    else:
        # fallback: search for 4-digit year anywhere
        m2 = soup.find(string=re.compile(r'\b(19|20)\d{2}\b'))
        if m2:
            m = re.search(r'(19|20)\d{2}', str(m2))
            if m:
                data['year'] = m.group(0)

    # Abstract: try multiple selectors
    abstract_selectors = [
        'section.abstract',
        'div.abstract',
        'meta[name="DC.description"]',
        'div[itemprop="abstract"]'
    ]
    abstract = ''
    # meta
    meta_abs = soup.select_one('meta[name="DC.description"]')
    if meta_abs and meta_abs.get('content'):
        abstract = meta_abs.get('content').strip()
    if not abstract:
        abstract = _get_text_by_selectors(soup, abstract_selectors)
    data['abstract'] = abstract

    # Description: try itemprop or sections near headings
    desc = ''
    desc = _get_text_by_selectors(soup, ['div[itemprop="description"]', 'section.description', 'div.description'])
    if not desc:
        for heading in soup.find_all(['h2', 'h3']):
            txt = heading.get_text(strip=True).lower()
            if 'description' in txt or 'detailed description' in txt:
                next_p = heading.find_next('p')
                if next_p:
                    desc = next_p.get_text(strip=True)
                    break
    data['description'] = (desc or '')[:2000]

    # Claims: improved extraction to get full section until "similar documents"
    claims_full = ''
    
    # Find claims heading
    claims_heading = None
    for h in soup.find_all(['h1', 'h2', 'h3', 'h4']):
        h_text = h.get_text(strip=True).lower()
        if 'claim' in h_text or 'what is claimed' in h_text:
            claims_heading = h
            break
    
    if claims_heading:
        # Get all content from claims section until we hit "similar documents" or related sections
        all_text = []
        current = claims_heading.find_next()
        
        while current:
            # Get text content
            curr_text = current.get_text(strip=True).lower()
            
            # Stop conditions: "similar documents", "related patents", "prior art", etc.
            if any(stop_word in curr_text for stop_word in 
                   ['similar documents', 'related patents', 'prior art', 'cited by', 'also published']):
                break
            
            # Stop if we hit another major section heading (but not claim numbers)
            if current.name in ['h1', 'h2', 'h3', 'h4'] and current != claims_heading:
                if any(word in curr_text for word in ['abstract', 'description', 'figure', 'inventor', 'applicant']):
                    break
            
            # Collect meaningful content
            if current.name in ['li', 'p', 'div', 'span']:
                text = current.get_text(strip=True)
                # Include claim text (even numbered items like "1.", "2.", etc.)
                if text and len(text) > 5:
                    all_text.append(text)
            
            current = current.find_next()
        
        if all_text:
            claims_full = '\n\n'.join(all_text)
    
    # Fallback: try simple selector approach if not found
    if not claims_full:
        claims_fallback = _get_text_by_selectors(soup, 
                                                  ['section.claims', 'div.claims', 'div[itemprop="claims"]'])
        if claims_fallback:
            claims_full = claims_fallback
    
    data['claims'] = claims_full if claims_full else ''

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
    if SimpleDocTemplate is None:
        print("reportlab is not installed. Install with: pip install reportlab", file=sys.stderr)
        return False
    try:
        doc = SimpleDocTemplate(output_path, pagesize=letter)
        story = []
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'], fontSize=14, textColor=colors.HexColor('#1f4788'), spaceAfter=12, fontName='Helvetica-Bold')
        heading_style = ParagraphStyle('CustomHeading', parent=styles['Heading2'], fontSize=12, textColor=colors.HexColor('#2e5c8a'), spaceAfter=8, spaceBefore=12, fontName='Helvetica-Bold')
        body_style = ParagraphStyle('CustomBody', parent=styles['BodyText'], fontSize=10, alignment=4)

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
        if patent_data.get('abstract'):
            story.append(Paragraph("Abstract", heading_style))
            abstract_text = patent_data['abstract']
            if len(abstract_text) > 2000:
                abstract_text = abstract_text[:2000] + "..."
            story.append(Paragraph(abstract_text, body_style))
            story.append(Spacer(1, 12))
        if patent_data.get('description'):
            story.append(Paragraph("Description", heading_style))
            description_text = patent_data['description']
            if len(description_text) > 2000:
                description_text = description_text[:2000] + "..."
            story.append(Paragraph(description_text, body_style))
            story.append(Spacer(1, 12))
        if patent_data.get('claims'):
            story.append(PageBreak() if len(story) > 10 else Spacer(1, 12))
            story.append(Paragraph("Claims", heading_style))
            claims_text = patent_data['claims']
            # For claims, preserve more content (up to ~5000 chars)
            if len(claims_text) > 5000:
                claims_text = claims_text[:5000] + "..."
            story.append(Paragraph(claims_text, body_style))
        doc.build(story)
        return True
    except Exception as e:
        print(f"Error creating PDF: {e}", file=sys.stderr)
        return False


def _read_links_file(p: Path) -> List[str]:
    if not p.exists():
        print(f"Links file not found: {p}", file=sys.stderr)
        return []
    lines = [l.strip() for l in p.read_text(encoding='utf-8', errors='ignore').splitlines()]
    return [l for l in lines if l]


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Parse Google Patents and save information to PDF")
    parser.add_argument("--url", "-u", help="Google Patents URL (e.g., https://patents.google.com/patent/US1234567B2)")
    parser.add_argument("--links-file", help="Path to file with one Google Patents URL per line (batch mode)")
    parser.add_argument("--output", "-o", help="Output PDF file path (auto-generated if not specified for single URL)")
    parser.add_argument("--output-dir", "-d", help="Directory to save PDFs (defaults to current directory)", default='.')
    parser.add_argument("--use-selenium", action='store_true', help="Use Selenium (headless Chrome) for fetching pages")
    parser.add_argument("--timeout", type=int, default=20, help="Page load timeout seconds")
    args = parser.parse_args(argv)

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    urls: List[str] = []
    if args.links_file:
        urls = _read_links_file(Path(args.links_file))
        if not urls:
            print("No URLs found in links file.", file=sys.stderr)
            return 2
    elif args.url:
        urls = [args.url]
    else:
        parser.error("Either --url or --links-file must be provided")

    for idx, url in enumerate(urls, start=1):
        print(f"[{idx}/{len(urls)}] Fetching: {url}", file=sys.stderr)
        html = fetch_patent_page(url, use_selenium=bool(args.use_selenium), timeout=args.timeout)
        if not html:
            print(f"Failed to fetch: {url}", file=sys.stderr)
            continue
        patent_data = parse_patent_data(html)

        # Determine output path
        if len(urls) == 1 and args.output:
            out_path = Path(args.output)
            if out_path.is_dir():
                filename = generate_filename(patent_data)
                out_path = out_path / filename
        else:
            filename = generate_filename(patent_data)
            out_path = out_dir / filename

        print(f"Creating PDF: {out_path}", file=sys.stderr)
        if create_pdf(patent_data, str(out_path)):
            print(f"Saved: {out_path}", file=sys.stderr)
        else:
            print(f"Failed to create PDF for: {url}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
