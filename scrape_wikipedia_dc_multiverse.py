#!/usr/bin/env python3
"""
Scrape DC Multiverse (toy line) from Wikipedia with correct rowspan/colspan handling.

McFarlane only: we intentionally extract only the "McFarlane figures (2020–present)"
section. The older "Mattel figures (2016–2019)" / blue box line is not scraped or included.

Fetches wikitext via API, parses tables in "McFarlane figures (2020–present)" and
subsections, expands merged cells, and outputs CSV compatible with parse_wikipedia_csv.py.

Output CSV format:
- Category rows: first column only (e.g. "Standard figures")
- Figure rows: Release, Figure, Accessories, Description
"""

import csv
import re
import sys
from typing import List, Tuple, Optional, Any, Dict

try:
    import requests
except ImportError:
    requests = None

WIKI_API = "https://en.wikipedia.org/w/api.php"
PAGE_TITLE = "DC_Multiverse_(toy_line)"
OUTPUT_CSV = "wikipedia_list.csv"
SECTION_ANCHOR = "McFarlane_figures_(2020–present)"
SECTION_ANCHOR_PAGE_PUNCHERS = "McFarlane_figures_-_DC_Page_Punchers"

# Category hierarchy: (heading_level, name). Dash in user list = subcategory of previous.
# We map wiki === to level 2, ==== to level 3, etc.
CATEGORY_HEADINGS = [
    ("Standard figures", 2),
    ("Build-A", 2),
    ("Theatrical Deluxe Figures", 2),
    ("Box Sets & Vehicles", 3),  # sub of Theatrical Deluxe
    ("Mega Figures", 2),
    ("Mega Figures (12\" Statue)", 2),
    ("Box Sets & Vehicles", 2),
    ("Exclusives (Pre-Gold Label)", 2),
    ("Standard figures", 3),
    ("Build-A", 3),
    ("Box Sets & Vehicles", 3),
    ("Mega Figures", 3),
    ("Fan Vote Winners", 2),
    ("Gold Label Collection", 2),
    ("Standard figures", 3),
    ("Accent Edition", 3),
    ("Anniversary Edition", 3),
    ("Blacklight Edition", 3),
    ("Box Sets & Vehicles", 3),
    ("Build-A", 3),
    ("Frostbite Edition", 3),
    ("Glow in the Dark Edition", 3),
    ("Jokerized Edition", 3),
    ("Mega Figures", 3),
    ("Mega Figures (12\" Statue)", 3),
    ("Knightmare Edition", 3),
    ("Patina Edition", 3),
    ("Sketch Edition", 3),
    ("Chase - Platinum Editions", 2),
    ("Artist Proof", 3),
    ("Variants", 3),
    ("Red Platinum - unique characters", 3),
    ("McFarlane Collector Edition", 2),
    ("Standard figures", 3),
    ("Box Sets", 3),
    ("Chase - Platinum Edition", 3),
    ("Platinum Box Sets", 3),
    ("Chase - Red Platinum", 3),
    ("McFarlane figures - DC Page Punchers", 2),
    ("Single figures", 3),
    ("MegaFigs", 3),
    ("Gold Label Collection", 3),
    ("Chase - Platinum Edition", 3),
    ("McFarlane Figures - Digital", 2),
    ("Digital Only", 3),
    ("Standard figures with digital", 3),
    ("Mega figures (12\" Statue) with digital", 3),
    ("McFarlane Toys Collectors Club Drawing Board", 2),
]


def fetch_wikitext() -> str:
    """Get full page wikitext from Wikipedia API."""
    if not requests:
        raise RuntimeError("Install requests: pip install requests")
    params = {
        "action": "query",
        "titles": PAGE_TITLE,
        "prop": "revisions",
        "rvprop": "content",
        "rvslots": "main",
        "formatversion": "2",
        "format": "json",
    }
    headers = {"User-Agent": "DC-Multiverse-Scraper/1.0 (https://github.com/; Python)"}
    while True:
        r = requests.get(WIKI_API, params=params, headers=headers, timeout=60)
        r.raise_for_status()
        data = r.json()
        if "error" in data:
            raise RuntimeError(data["error"].get("info", "Unknown API error"))
        pages = data.get("query", {}).get("pages", [])
        if not pages:
            raise RuntimeError("Page not found")
        page = pages[0]
        if "missing" in page:
            raise RuntimeError("Page missing")
        revs = page.get("revisions", [])
        if not revs:
            raise RuntimeError("No revisions")
        content = revs[0].get("slots", {}).get("main", {}).get("content", "")
        if not content:
            raise RuntimeError("Empty content")
        # Check for continuation (long pages)
        if "continue" in data:
            params["rvcontinue"] = data["continue"].get("rvcontinue")
            if not params.get("rvcontinue"):
                break
        else:
            break
    return content


def extract_section(wikitext: str, anchor: str) -> str:
    """Extract the section starting at the given anchor until next same-level heading."""
    # Find the section: ## McFarlane figures or === McFarlane figures ===
    # Anchor is McFarlane_figures_(2020–present) - in wikitext it's usually with spaces and =.
    pattern = re.compile(
        r"^(={2,})\s*([^=]+?)\s*\1\s*$",
        re.MULTILINE,
    )
    start = None
    start_level = None
    for m in pattern.finditer(wikitext):
        heading = m.group(2).strip()
        level = len(m.group(1))
        # Normalize: "McFarlane figures (2020–present)" vs anchor "McFarlane_figures_(2020–present)"
        heading_anchor = heading.replace(" ", "_").replace("–", "–")
        if anchor.replace("_", " ").replace("–", "–") in heading or anchor in heading_anchor:
            start = m.end()
            start_level = level
            break
    if start is None:
        # Try finding by line
        for line in wikitext.split("\n"):
            if "McFarlane figures" in line and "2020" in line and line.strip().startswith("="):
                start = wikitext.find(line)
                start_level = len(line) - len(line.lstrip("="))
                break
    if start is None:
        raise ValueError("Section not found: " + anchor)
    # Find next heading of same or higher level
    end = len(wikitext)
    for m in pattern.finditer(wikitext, start):
        level = len(m.group(1))
        if level <= start_level:
            end = m.start()
            break
    return wikitext[start:end]


def parse_cell_attrs_and_content(cell_text: str) -> Tuple[int, int, str]:
    """Parse a cell that may start with rowspan=N and/or colspan=N. Returns (rowspan, colspan, content)."""
    cell_text = cell_text.strip()
    # Strip leading pipe or ! so "| rowspan=2|Content" is parsed correctly
    if cell_text.startswith("|") or cell_text.startswith("!"):
        cell_text = cell_text[1:].strip()
    rowspan = 1
    colspan = 1
    content = cell_text
    # Match optional leading "rowspan=N" and "colspan=N" before a pipe
    m = re.match(r"^(?:\s*rowspan\s*=\s*(\d+))?(?:\s*colspan\s*=\s*(\d+))?\s*\|?\s*(.*)$", cell_text, re.DOTALL)
    if m:
        if m.group(1):
            rowspan = int(m.group(1))
        if m.group(2):
            colspan = int(m.group(2))
        content = (m.group(3) or "").strip()
    return rowspan, colspan, content


def strip_wiki_markup(text: str) -> str:
    """Remove wiki markup for CSV output."""
    if not text:
        return ""
    text = text.strip()
    # Remove [[link|label]] -> label, [[link]] -> link
    text = re.sub(r"\[\[(?:[^|\]]+\|)?([^\]]+)\]\]", r"\1", text)
    # Remove ''italic'' and '''bold'''
    text = re.sub(r"'{2,3}([^']*)'{2,3}", r"\1", text)
    # Remove <br /> etc
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def parse_table_row(row_text: str) -> List[Tuple[int, int, str]]:
    """Parse one table row into list of (rowspan, colspan, content)."""
    row_text = row_text.strip()
    if not row_text:
        return []
    # Cells are separated by newline followed by | or !
    parts = re.split(r"\n\s*[|!]", row_text)
    cells = []
    for i, part in enumerate(parts):
        part = part.strip()
        if not part:
            continue
        # First cell might start with | or ! already consumed
        if i == 0 and part and part[0] not in "|!" and "rowspan" not in part[:20] and "colspan" not in part[:20]:
            # First cell content only
            cells.append((1, 1, strip_wiki_markup(part)))
            continue
        rowspan, colspan, content = parse_cell_attrs_and_content(part)
        content = strip_wiki_markup(content)
        if content or rowspan > 1 or colspan > 1:
            cells.append((rowspan, colspan, content))
    return cells


def expand_table_to_grid(rows_cells: List[List[Tuple[int, int, str]]]) -> List[List[str]]:
    """Expand rowspan/colspan so we get a uniform grid. Returns grid[row][col] = content.

    Uses rowspan carry: when a cell has rowspan=N, its content is carried down to the
    next N-1 rows in that column. When a row has fewer cells (e.g. 2), they are assigned
    to the next free columns after filled-by-carry columns, so e.g. Figure and Accessories
    get the new cells and Description comes from carry. Also repeats previous row's first
    column (Release) when the current row has fewer cells and col 0 is empty.
    """
    if not rows_cells:
        return []
    # Number of columns from first row (sum of colspans)
    num_cols = sum(cs for (_, cs, _) in rows_cells[0])
    if num_cols < 1:
        num_cols = 1

    grid: List[List[Optional[str]]] = []
    # Per-column rowspan carry: (content, rows_remaining). When rows_remaining > 0 we fill that column from above.
    carry: List[Optional[Tuple[str, int]]] = [None] * num_cols

    for row_idx, cells in enumerate(rows_cells):
        row: List[Optional[str]] = [None] * num_cols

        # 1) Fill from rowspan carry
        for c in range(num_cols):
            if carry[c] is not None:
                content, remaining = carry[c]
                row[c] = content
                remaining -= 1
                if remaining <= 0:
                    carry[c] = None
                else:
                    carry[c] = (content, remaining)

        # 2) When row has fewer cells than empty slots and col 0 is empty, repeat previous row's Release (col 0)
        empty_count = sum(1 for c in row if c is None)
        if row_idx > 0 and empty_count > len(cells) and row[0] is None and len(grid) > 0 and len(grid[-1]) > 0:
            row[0] = grid[-1][0]

        # 3) Assign this row's cells to the next free columns; set carry for rowspan > 1
        cell_iter = iter(cells)
        for (rs, cs, content) in cell_iter:
            # Find next column that is still None
            col = 0
            while col < num_cols and row[col] is not None:
                col += 1
            if col >= num_cols:
                break
            # Fill this cell and its colspan (only first column gets content for colspan; rest get "")
            for c in range(col, min(col + cs, num_cols)):
                row[c] = content if c == col else ""
            if rs > 1:
                # Set carry for the first column of this cell so next (rs-1) rows get this content
                carry[col] = (content, rs - 1)
            col += cs

        grid.append(row)

    # Convert None to empty string
    result = []
    for row in grid:
        result.append([(c or "") for c in row])
    return result


def parse_wiki_table(table_text: str) -> List[List[str]]:
    """Parse a full wiki table (content between {| and |}) into a grid."""
    table_text = table_text.strip()
    if not table_text.startswith("{|"):
        return []
    # Remove first line ({| ...) and last line (|})
    lines = table_text.split("\n")
    if lines[0].strip().startswith("{|"):
        lines = lines[1:]
    if lines and lines[-1].strip() == "|}":
        lines = lines[:-1]
    # Rows are separated by |-
    row_texts = re.split(r"\n\s*\|-\s*\n", "\n".join(lines))
    rows_cells: List[List[Tuple[int, int, str]]] = []
    for rt in row_texts:
        rt = rt.strip()
        if not rt:
            continue
        cells = parse_table_row(rt)
        if cells:
            rows_cells.append(cells)
    if not rows_cells:
        return []
    return expand_table_to_grid(rows_cells)


def find_tables_in_section(section_text: str) -> List[str]:
    """Extract raw table strings from section (between {| and |})."""
    tables = []
    i = 0
    while True:
        start = section_text.find("{|", i)
        if start == -1:
            break
        depth = 1
        j = start + 2
        while j < len(section_text) and depth > 0:
            if section_text[j : j + 2] == "{|":
                depth += 1
                j += 2
            elif section_text[j : j + 2] == "|}":
                depth -= 1
                if depth == 0:
                    tables.append(section_text[start : j + 2])
                    i = j + 2
                    break
                j += 2
            else:
                j += 1
        else:
            i = start + 2
    return tables


def infer_table_columns(grid: List[List[str]]) -> Tuple[int, int, int, int, int]:
    """Infer which columns are Release, Figure, Accessories, Description, and optional Set.
    Returns (release_col, figure_col, accessories_col, desc_col, set_col).
    set_col is -1 when there is no 'Set' column (e.g. 4-column tables)."""
    if not grid or len(grid) < 2:
        return 0, 1, 2, 3, -1
    header = [c.strip().lower() for c in grid[0]]
    release_col = 0
    figure_col = 1
    accessories_col = 2
    desc_col = 3
    set_col = -1
    for i, h in enumerate(header):
        if "release" in h or "release" in h.replace(" ", ""):
            release_col = i
        if "figure" in h:
            figure_col = i
        if "accessor" in h:
            accessories_col = i
        if "description" in h or "descript" in h:
            desc_col = i
        if h.strip() == "set" or (len(header) >= 5 and "set" in h and "figure" not in h):
            set_col = i
    # If header has 4 columns and no header row, assume first row is data and order is Release, Figure, Accessories, Description
    if len(header) >= 4 and not any("release" in h or "figure" in h for h in header):
        return 0, 1, 2, min(3, len(header) - 1), -1
    return release_col, figure_col, accessories_col, desc_col, set_col


def section_heading_to_category(line: str) -> Optional[str]:
    """Map a wiki heading line to category name."""
    m = re.match(r"^(={2,})\s*(.+?)\s*\1\s*$", line.strip())
    if not m:
        return None
    return m.group(2).strip()


def main():
    print("Fetching Wikipedia page...")
    wikitext = fetch_wikitext()
    print(f"  Got {len(wikitext)} chars")

    print("Extracting McFarlane section...")
    section = extract_section(wikitext, SECTION_ANCHOR)
    print(f"  Section length: {len(section)} chars")

    # Also extract DC Page Punchers (level-2 section after McFarlane 2020, so it was excluded above)
    try:
        section_pp = extract_section(wikitext, SECTION_ANCHOR_PAGE_PUNCHERS)
        # extract_section returns content after the heading; prepend heading so parser sets current_series
        section_pp_full = "== McFarlane figures - DC Page Punchers ==\n" + section_pp
        section = section + "\n\n" + section_pp_full
        print(f"  Added DC Page Punchers section: {len(section_pp)} chars")
    except ValueError as e:
        print(f"  DC Page Punchers section not found: {e}")

    # Find all subsection headings and tables
    lines = section.split("\n")
    current_category = "Standard figures"
    current_series = "dc-multiverse"
    rows_out: List[List[str]] = []

    # Emit top-level category row
    rows_out.append(["McFarlane figures (2020–present)", "", "", ""])
    rows_out.append(["", "", "", ""])
    rows_out.append(["Standard figures", "", "", ""])

    i = 0
    while i < len(lines):
        line = lines[i]
        # Section heading
        heading_match = re.match(r"^(={2,})\s*(.+?)\s*\1\s*$", line.strip())
        if heading_match:
            level = len(heading_match.group(1))
            name = heading_match.group(2).strip()
            # Map to category
            if "Page Punchers" in name and "DC Page Punchers" in name:
                current_series = "dc-page-punchers"
                current_category = "Page Punchers"
                rows_out.append([line.strip(), "", "", ""])
            elif "Digital" in name and "McFarlane Figures" in name:
                current_category = name
                rows_out.append([name, "", "", ""])
            elif "Drawing Board" in name:
                current_category = name
                rows_out.append([name, "", "", ""])
            elif level >= 2 and name:
                current_category = name
                # Only emit as category row if it's a known section (not a table header)
                if any(
                    name in h for h in [
                        "Standard figures", "Build-A", "Theatrical Deluxe", "Mega Figures",
                        "Box Sets", "Exclusives", "Fan Vote", "Gold Label", "Chase",
                        "McFarlane Collector", "Single figures", "MegaFigs", "Digital Only",
                        "Standard figures with digital", "Mega figures"
                    ]
                ) or "Edition" in name or "Platinum" in name or "Artist Proof" in name or "Variants" in name:
                    rows_out.append([name, "", "", ""])
            i += 1
            continue

        # Table start
        if line.strip().startswith("{|"):
            table_lines = [line]
            j = i + 1
            while j < len(lines) and "|}" not in lines[j]:
                table_lines.append(lines[j])
                j += 1
            if j < len(lines):
                table_lines.append(lines[j])
            table_text = "\n".join(table_lines)
            grid = parse_wiki_table(table_text)
            if grid:
                # Infer columns from header row (includes optional Set column for 5-col tables)
                release_col, figure_col, acc_col, desc_col, set_col = infer_table_columns(grid)
                # Skip header row if it looks like header
                start_row = 1 if len(grid) > 1 and any(
                    "release" in grid[0][k].lower() or "figure" in grid[0][k].lower()
                    for k in range(min(5, len(grid[0])))
                ) else 0
                for r in range(start_row, len(grid)):
                    row = grid[r]
                    if len(row) <= max(release_col, figure_col, acc_col, desc_col):
                        continue
                    release = (row[release_col] or "").strip()
                    figure = (row[figure_col] or "").strip()
                    accessories = (row[acc_col] or "").strip()
                    description = (row[desc_col] or "").strip()
                    # When table has a Set column (e.g. Box Sets & Vehicles), use Set as figure name when Figure is empty
                    if set_col >= 0 and set_col < len(row) and not figure:
                        set_name = (row[set_col] or "").strip()
                        if set_name:
                            figure = set_name
                    # Skip empty rows
                    if not figure and not description and not release and not accessories:
                        continue
                    # Skip pure header rows
                    if figure and figure.lower() in ("release", "figure", "accessories", "description", "build-a piece"):
                        continue
                    rows_out.append([release, figure, accessories, description])
            i = j + 1
            continue

        i += 1
    # Remove duplicate consecutive category rows
    cleaned = []
    for row in rows_out:
        if row[0] and not row[1] and not row[2] and not row[3]:
            if cleaned and cleaned[-1][0] == row[0]:
                continue
        cleaned.append(row)

    print(f"Writing {len(cleaned)} rows to {OUTPUT_CSV}...")
    with open(OUTPUT_CSV, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        for row in cleaned:
            writer.writerow(row)

    # Validate: show sample rows so you can confirm both Batman and Superman have descriptions
    white_knight_count = 0
    superman_count = 0
    for i, row in enumerate(cleaned):
        if len(row) < 4:
            continue
        fig, desc = (row[1] or "").strip(), (row[3] or "")
        if "White Knight" in desc:
            print(f"  Row {i}: Release={row[0]!r}, Figure={fig!r}, Desc={desc[:60]!r}...")
            white_knight_count += 1
        elif fig.startswith("Superman") and desc:
            if superman_count < 8:  # show first 8 Superman figure rows
                print(f"  Row {i}: Release={row[0]!r}, Figure={fig!r}, Desc={desc[:60]!r}...")
            superman_count += 1
    print(f"  (White Knight rows: {white_knight_count}, Superman figure rows: {superman_count})")
    print("Done.")


if __name__ == "__main__":
    main()
