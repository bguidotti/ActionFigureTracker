#!/usr/bin/env python3
"""
Enrich all_figures.json names from wikipedia_list.csv so each figure
has the most descriptive title (e.g. "Batman (Detective Comics #1000 version)").
Uses CSV columns: Release (wave), Figure (base name), Description -> full name.
"""

import csv
import json
import re
import sys

sys.stdout.reconfigure(line_buffering=True)

CSV_FILE = r'c:\Code\ActionFigureTracker\wikipedia_list.csv'
JSON_FILE = r'c:\Code\ActionFigureTracker\Models\all_figures.json'


def clean_text(text):
    if not text:
        return ''
    text = text.strip()
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'^["\']|["\']$', '', text)
    return text


def create_figure_name(name, description):
    name = clean_text(name)
    description = clean_text(description)
    if not name:
        return description or "Unknown Figure"
    if not description:
        return name
    if any(kw in description.lower() for kw in ['version', 'variant', 'edition', 'redeco', 'retool']):
        return f"{name} ({description})"
    return f"{name} - {description}"


def is_category_header(text):
    if not text:
        return False
    text = text.strip().lower()
    keywords = ['standard figures', 'deluxe', 'gold label', 'build-a', 'vehicles', 'page punchers', 'single figures', 'digital', 'mcfarlane figures']
    return any(kw in text for kw in keywords)


def is_release_date(text):
    if not text:
        return False
    text = text.strip()
    return bool(re.match(r'^(Q\d|Fall|Spring|Summer|Winter|\d{4})', text, re.IGNORECASE))


def parse_csv_figures():
    """Parse CSV and return list of (series, wave, full_name, base_name) in order."""
    rows = []
    current_series = "dc-multiverse"
    current_wave = ""
    page_punchers = False

    with open(CSV_FILE, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        for row in reader:
            while len(row) < 4:
                row.append('')
            col_a, col_b, col_c, col_d = [clean_text(row[i]) for i in range(4)]

            if not col_a and not col_b and not col_c and not col_d:
                continue
            if 'page punchers' in col_a.lower():
                current_series = "dc-page-punchers"
                page_punchers = True
                continue
            if 'mcfarlane figures' in col_a.lower() and 'page punchers' not in col_a.lower():
                current_series = "dc-multiverse"
                page_punchers = False
                continue
            if is_category_header(col_a) and not col_b:
                continue
            if is_release_date(col_a):
                current_wave = col_a.strip()
                if not col_b:
                    continue
            if col_b.lower() in ['figure', 'release', 'name']:
                continue

            # Page Punchers format
            if page_punchers and current_series == "dc-page-punchers":
                while len(row) < 5:
                    row.append('')
                pp_wave, pp_release, pp_figure = clean_text(row[0]), clean_text(row[1]), clean_text(row[2])
                pp_desc = clean_text(row[4]) if len(row) > 4 else ''
                if pp_wave.lower() == 'wave' or not pp_figure:
                    continue
                if is_release_date(pp_release):
                    current_wave = pp_release
                elif is_release_date(pp_wave):
                    current_wave = pp_wave
                full = create_figure_name(pp_figure, pp_desc)
                base = pp_figure or full.split('(')[0].strip()
                rows.append((current_series, current_wave, full, base))
                continue

            # Standard: no figure name
            if not col_b and not col_d:
                continue
            if not col_b and col_d:
                if any(kw in col_d.lower() for kw in ['art card', 'photo card', 'display stand']):
                    continue
                if rows and rows[-1][0] == current_series and rows[-1][1] == current_wave:
                    base = rows[-1][3]
                    full = f"{base} ({col_d})" if base else col_d
                    rows.append((current_series, current_wave, full, base))
                continue

            full = create_figure_name(col_b, col_d)
            base = col_b.strip()
            if any(kw in full.lower() for kw in ['art card', 'photo card', 'display stand and', 'accessories']):
                continue
            rows.append((current_series, current_wave, full, base))

    return rows


def main():
    print("Parsing CSV...")
    csv_rows = parse_csv_figures()
    print(f"  Got {len(csv_rows)} figure rows from CSV")

    # Group by (series, wave) as ordered list of (base_name, full_name)
    from collections import defaultdict
    by_sw = defaultdict(list)
    for series, wave, full_name, base_name in csv_rows:
        by_sw[(series, wave)].append((base_name.strip(), full_name))

    print("Loading JSON...")
    with open(JSON_FILE, 'r', encoding='utf-8') as f:
        figures = json.load(f)

    # For each figure, find first matching CSV row with same base name (consume so order is preserved)
    updated = 0
    for fig in figures:
        series = fig.get('series', '')
        wave = fig.get('wave') or ''
        if series not in ('dc-multiverse', 'dc-page-punchers'):
            continue
        key = (series, wave)
        if key not in by_sw or not by_sw[key]:
            continue
        current_name = fig.get('name', '')
        base = current_name.split('(')[0].strip() if current_name else ''
        if not base:
            continue
        lst = by_sw[key]
        for i, (csv_base, csv_full) in enumerate(lst):
            csv_base_clean = (csv_base or '').split('(')[0].strip()
            if csv_base_clean.lower() == base.lower():
                if csv_full != current_name:
                    fig['name'] = csv_full
                    updated += 1
                lst.pop(i)  # consume so next "Batman" gets next CSV Batman
                break

    print(f"Updated {updated} figure names")

    # Show sample
    batmans = [f for f in figures if f.get('name', '').startswith('Batman')][:8]
    print("\nSample Batman names after enrich:")
    for f in batmans:
        print(f"  {f.get('wave', '')}: {f.get('name', '')[:55]}")

    print(f"\nSaving {JSON_FILE}...")
    with open(JSON_FILE, 'w', encoding='utf-8') as f:
        json.dump(figures, f, indent=2)
    print("Done!")


if __name__ == '__main__':
    main()
