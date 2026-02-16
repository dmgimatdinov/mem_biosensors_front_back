"""Frequency word analysis for text files (PDF, DOCX, TXT).

Usage (CLI):
    python -m freq_analysis.freq_analysis --paths data/*.pdf data/*.docx --words glucose,insulin

The script outputs for each file: filename, searched words, frequency counts per word.
"""
from __future__ import annotations

import re
import sys
import csv
import argparse
from pathlib import Path
from typing import List, Dict, Any

try:
    from openpyxl import Workbook
except Exception:
    Workbook = None

try:
    from PyPDF2 import PdfReader
except Exception:
    PdfReader = None

try:
    import docx
except Exception:
    docx = None


def extract_text_from_pdf(path: Path) -> str:
    if PdfReader is None:
        raise RuntimeError("PyPDF2 is not installed. Install with: pip install PyPDF2")
    text_parts: List[str] = []
    reader = PdfReader(str(path))
    for page in reader.pages:
        try:
            text = page.extract_text() or ""
        except Exception:
            text = ""
        text_parts.append(text)
    return "\n".join(text_parts)


def extract_text_from_docx(path: Path) -> str:
    if docx is None:
        raise RuntimeError("python-docx is not installed. Install with: pip install python-docx")
    document = docx.Document(str(path))
    paragraphs = [p.text for p in document.paragraphs]
    return "\n".join(paragraphs)


def extract_text_from_txt(path: Path) -> str:
    # try utf-8 then fallback
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        try:
            return path.read_text(encoding="latin-1")
        except Exception:
            return path.read_text(errors="ignore")


def extract_text(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        return extract_text_from_pdf(path)
    if suffix in (".docx", ".doc"):
        # .doc is not supported by python-docx; would need antiword or textract
        if suffix == ".doc":
            # attempt to read as binary and fallback to empty
            return ""
        return extract_text_from_docx(path)
    # fallback to text-based
    return extract_text_from_txt(path)


def count_words_in_text(text: str, target_words: List[str]) -> Dict[str, int]:
    # Normalize text to lowercase
    text_lower = text.lower()
    counts: Dict[str, int] = {}
    for w in target_words:
        w_norm = w.lower().strip()
        if not w_norm:
            counts[w] = 0
            continue
        # match whole words using word boundaries
        pattern = re.compile(r"\b" + re.escape(w_norm) + r"\b", flags=re.UNICODE)
        matches = pattern.findall(text_lower)
        counts[w] = len(matches)
    return counts


def analyze_files(file_paths: List[Path], target_words: List[str]) -> List[Dict[str, Any]]:
    results: List[Dict[str, Any]] = []
    for p in file_paths:
        try:
            text = extract_text(p)
        except Exception as e:
            results.append({
                "file": str(p),
                "error": str(e),
                "counts": {w: 0 for w in target_words},
            })
            continue
        counts = count_words_in_text(text, target_words)
        total = sum(counts.values())
        results.append({"file": str(p), "counts": counts, "total": total})
    return results


def print_results(results: List[Dict[str, Any]], target_words: List[str]) -> None:
    # Print header
    print("filename\tsearched_words\tcounts\ttotal")
    words_label = ",".join(target_words)
    for r in results:
        full_path = r.get("file")
        fname = Path(full_path).name  # extract basename
        if r.get("error"):
            print(f"{fname}\t{words_label}\tERROR: {r.get('error')}\t0")
            continue
        counts = r.get("counts", {})
        counts_str = ", ".join([f"{w}:{counts.get(w,0)}" for w in target_words])
        total = r.get("total", 0)
        print(f"{fname}\t{words_label}\t{counts_str}\t{total}")


def save_results_to_csv(results: List[Dict[str, Any]], target_words: List[str], output_path: str) -> None:
    """Save analysis results to CSV file.
    
    CSV columns: filename, <word1>, <word2>, ..., total
    """
    try:
        with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['filename'] + target_words + ['total']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for r in results:
                full_path = r.get("file")
                fname = Path(full_path).name
                
                row = {
                    'filename': fname,
                }
                
                if r.get("error"):
                    row['total'] = 0
                    for w in target_words:
                        row[w] = 0
                else:
                    counts = r.get("counts", {})
                    for w in target_words:
                        row[w] = counts.get(w, 0)
                    row['total'] = r.get("total", 0)
                
                writer.writerow(row)
        
        print(f"Results saved to {output_path}", file=sys.stderr)
    except Exception as e:
        print(f"Error saving to CSV: {e}", file=sys.stderr)


def save_results_to_xlsx(results: List[Dict[str, Any]], target_words: List[str], output_path: str) -> None:
    """Save analysis results to XLSX file.
    
    XLSX columns: filename, <word1>, <word2>, ..., total
    """
    if Workbook is None:
        print("openpyxl is not installed. Install with: pip install openpyxl", file=sys.stderr)
        return
    
    try:
        wb = Workbook()
        ws = wb.active
        ws.title = "Results"
        
        # Write header
        header = ['filename'] + target_words + ['total']
        ws.append(header)
        
        # Write data rows
        for r in results:
            full_path = r.get("file")
            fname = Path(full_path).name
            
            if r.get("error"):
                row_data = [fname] + [0] * len(target_words) + [0]
            else:
                counts = r.get("counts", {})
                counts_list = [counts.get(w, 0) for w in target_words]
                row_data = [fname] + counts_list + [r.get("total", 0)]
            
            ws.append(row_data)
        
        wb.save(output_path)
        print(f"Results saved to {output_path}", file=sys.stderr)
    except Exception as e:
        print(f"Error saving to XLSX: {e}", file=sys.stderr)


def gather_paths(patterns: List[str]) -> List[Path]:
    paths: List[Path] = []
    for pat in patterns:
        # allow directories: collect all supported files
        p = Path(pat)
        if p.is_dir():
            for ext in ("*.pdf", "*.docx", "*.doc", "*.txt"):
                paths.extend(sorted(p.rglob(ext)))
            continue
        # glob pattern or literal
        if any(ch in pat for ch in "*?[]"):
            paths.extend(sorted(Path('.').glob(pat)))
        else:
            if p.exists():
                paths.append(p)
    # dedupe while preserving order
    seen = set()
    out: List[Path] = []
    for p in paths:
        if str(p) not in seen:
            seen.add(str(p))
            out.append(p)
    return out


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Frequency word analysis for PDF/DOCX/TXT files")
    parser.add_argument("--paths", "-p", nargs="+", required=True, help="Files, globs or directories to analyze")
    parser.add_argument("--words", "-w", nargs="+", required=False, help="Target words (space separated) or comma-separated if quoted")
    parser.add_argument("--from-file", "-f", help="Path to a file containing target words, one per line")
    parser.add_argument("--output", "-o", help="Path to save results as CSV file")
    parser.add_argument("--xlsx", help="Path to save results as XLSX file")
    args = parser.parse_args(argv)

    # build target words list
    target_words: List[str] = []
    if args.from_file:
        p = Path(args.from_file)
        if p.exists():
            for ln in p.read_text(encoding="utf-8", errors="ignore").splitlines():
                ln = ln.strip()
                if ln:
                    target_words.append(ln)
    if args.words:
        for w in args.words:
            # allow comma-separated lists in single arg
            for sub in w.split(','):
                sub = sub.strip()
                if sub:
                    target_words.append(sub)

    paths = gather_paths(args.paths)
    if not paths:
        print("No files found for the given paths", file=sys.stderr)
        return 2

    results = analyze_files(paths, target_words)
    print_results(results, target_words)
    
    # Save to CSV if requested
    if args.output:
        save_results_to_csv(results, target_words, args.output)
        # Save to XLSX if requested
        if args.xlsx:
            save_results_to_xlsx(results, target_words, args.xlsx)
    
    
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
