"""Text-run extraction from PDFs, ported from modules/ats/parser/extract.ts.

pdf.js is a browser engine, so the same job falls to pdfminer here: every text
run (consecutive glyphs in one font on one baseline) becomes one TextItem with
the coordinates the layout analysis needs. y is measured down from the page
top, like the browser pipeline the TS code was written against. Word gaps
inside a line split the run, the same way toLine later inserts spaces between
items.
"""

from __future__ import annotations

import re
from io import BytesIO

from pdfminer.high_level import extract_pages
from pdfminer.layout import LTChar, LTTextContainer
from pypdf import PdfReader

BOLD_FONT = re.compile(r"bold|black|heavy|semibold|demi", re.IGNORECASE)
SUBSET_PREFIX = re.compile(r"^[A-Z]{6}\+")
ICON_FONT = re.compile(
    r"awesome|icon|glyph|material|dingbat|marvosym|wasy|academicons", re.IGNORECASE
)


def font_name(char: LTChar) -> str:
    return SUBSET_PREFIX.sub("", char.fontname)


def _runs(line) -> list[list[LTChar]]:
    """Chars of one visual line, cut where the font or the baseline moves."""
    chars = [c for c in line if isinstance(c, LTChar)]
    runs: list[list[LTChar]] = []
    for char in chars:
        run = runs[-1] if runs else None
        if run is not None:
            previous = run[-1]
            same_font = font_name(previous) == font_name(char)
            word_gap = char.x0 - previous.x1 > char.size * 0.15
            drifted = abs(previous.matrix[5] - char.matrix[5]) > char.size * 0.2
            if same_font and not word_gap and not drifted:
                run.append(char)
                continue
        runs.append([char])
    return runs


def _item(chars: list[LTChar], page_height: float, page: int) -> dict | None:
    text = "".join(c.get_text() for c in chars)
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return None
    size = max(c.size for c in chars)
    baseline = chars[0].matrix[5]
    return {
        "text": text,
        "x": chars[0].x0,
        "y": page_height - baseline - size,
        "width": chars[-1].x1 - chars[0].x0,
        "height": size,
        "page": page,
        "fontName": font_name(chars[0]),
        "bold": bool(BOLD_FONT.search(font_name(chars[0]))),
    }


def extract_text_items(pdf: bytes, max_pages: int = 4) -> dict:
    """Text items with coordinates from the first pages of a compiled PDF."""
    page_count = len(PdfReader(BytesIO(pdf)).pages)
    items: list[dict] = []
    page_width = 0.0
    page_height = 0.0
    for number, page_layout in enumerate(extract_pages(BytesIO(pdf), maxpages=max_pages), start=1):
        if number == 1:
            page_width, page_height = page_layout.width, page_layout.height
        for element in page_layout:
            if not isinstance(element, LTTextContainer):
                continue
            for line in element:
                for chars in _runs(line):
                    item = _item(chars, page_height, number)
                    if item:
                        items.append(item)
    return {
        "items": items,
        "pageCount": page_count,
        "pageHeight": page_height,
        "pageWidth": page_width,
    }
