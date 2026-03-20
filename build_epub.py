#!/usr/bin/env python3
"""
Build EPUB eBook from For Sale documentary HTML.
Output: ForSale_eBook_2026-03-19.epub
"""

import re
from html.parser import HTMLParser
from ebooklib import epub
from pathlib import Path

OUTPUT = Path(__file__).parent / "ForSale_eBook_2026-03-19.epub"
SOURCE = Path(__file__).parent / "index.html"

# ─── EPUB CSS ───────────────────────────────────────────────────────────────

BOOK_CSS = """
body {
    font-family: Georgia, "Times New Roman", serif;
    line-height: 1.8;
    color: #1a1a1a;
    margin: 1em;
}
h1 {
    font-size: 2.2em;
    font-weight: bold;
    text-align: center;
    margin: 1.5em 0 0.5em;
    color: #111;
}
h2 {
    font-size: 1.6em;
    font-weight: bold;
    margin: 1.5em 0 0.5em;
    color: #222;
    border-bottom: 1px solid #ccc;
    padding-bottom: 0.3em;
}
h3 {
    font-size: 1.3em;
    font-weight: bold;
    margin: 1.2em 0 0.4em;
    color: #333;
}
h4 {
    font-size: 1.1em;
    font-weight: bold;
    margin: 1em 0 0.3em;
    color: #333;
}
p {
    margin: 0.8em 0;
    text-align: justify;
}
blockquote {
    margin: 1.2em 0 1.2em 1em;
    padding: 0.8em 1em;
    border-left: 3px solid #999;
    background: #f5f5f5;
    font-style: italic;
}
blockquote .attribution {
    font-style: normal;
    font-weight: bold;
    margin-top: 0.5em;
    font-size: 0.9em;
    color: #555;
}
blockquote .context {
    font-style: normal;
    font-size: 0.8em;
    color: #777;
}
.hearing-quote {
    margin: 1.2em 0;
    padding: 0.8em 1em;
    border-left: 3px solid #c8a000;
    background: #fafae8;
}
.hearing-label {
    font-size: 0.7em;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: #998800;
    margin-bottom: 0.3em;
}
.hearing-speaker {
    font-weight: bold;
    color: #333;
}
.hearing-role {
    font-size: 0.8em;
    color: #666;
    margin-bottom: 0.5em;
}
.hearing-text {
    font-style: italic;
    line-height: 1.7;
}
.hearing-src {
    font-size: 0.75em;
    color: #888;
    margin-top: 0.5em;
}
.bbc-quote {
    margin: 1.2em 0;
    padding: 0.8em 1em;
    border-left: 3px solid #bb1919;
    background: #faf0f0;
}
.bbc-label {
    font-size: 0.7em;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: #bb1919;
    font-weight: bold;
    margin-bottom: 0.3em;
}
.stat-block {
    margin: 1.5em 0;
    text-align: center;
}
.stat-item {
    display: inline-block;
    margin: 0.5em 1em;
    text-align: center;
}
.stat-num {
    font-family: "Courier New", monospace;
    font-size: 1.4em;
    font-weight: bold;
    color: #c00;
}
.stat-label {
    font-size: 0.75em;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: #666;
}
.timeline-event {
    margin: 1em 0;
    padding-left: 1em;
    border-left: 2px solid #ccc;
}
.timeline-event.crisis {
    border-left-color: #c00;
}
.timeline-event.verdict {
    border-left-color: #c90;
}
.tl-date {
    font-family: "Courier New", monospace;
    font-size: 0.85em;
    font-weight: bold;
    color: #0077cc;
}
.timeline-event.crisis .tl-date {
    color: #c00;
}
.timeline-event.verdict .tl-date {
    color: #c90;
}
.tl-title {
    font-weight: bold;
    font-size: 1.05em;
    margin: 0.2em 0;
}
.tl-desc {
    font-size: 0.95em;
    color: #444;
    line-height: 1.6;
}
table {
    width: 100%;
    border-collapse: collapse;
    margin: 1em 0;
    font-size: 0.9em;
}
th {
    text-align: left;
    padding: 0.6em;
    border-bottom: 2px solid #999;
    font-size: 0.8em;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: #555;
}
td {
    padding: 0.6em;
    border-bottom: 1px solid #ddd;
    vertical-align: top;
}
.mono {
    font-family: "Courier New", monospace;
    font-weight: bold;
}
.card {
    margin: 1em 0;
    padding: 0.8em;
    border: 1px solid #ddd;
    border-radius: 4px;
}
.card h4 {
    margin-top: 0;
}
.callout {
    margin: 1.2em 0;
    padding: 0.8em 1em;
    border-left: 3px solid #c00;
    background: #fafafa;
}
.victim {
    margin: 1em 0;
    padding: 0.8em 1em;
    border-left: 3px solid #c00;
    background: #faf5f5;
}
.victim-name {
    font-weight: bold;
    font-size: 1.05em;
}
.victim-loss {
    font-family: "Courier New", monospace;
    font-weight: bold;
    color: #c00;
    font-size: 1.1em;
}
.dossier {
    margin: 1.5em 0;
    padding: 1em;
    border: 1px solid #ccc;
}
.dossier-name {
    font-size: 1.2em;
    font-weight: bold;
    color: #222;
}
.dossier-title {
    font-size: 0.8em;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: #666;
    margin-bottom: 0.5em;
    padding-bottom: 0.5em;
    border-bottom: 1px solid #ddd;
}
.dossier-links {
    margin: 0;
    padding: 0;
    list-style: none;
}
.dossier-links li {
    padding: 0.3em 0;
    border-bottom: 1px solid #eee;
    font-size: 0.9em;
}
.dossier-links li:before {
    content: "→ ";
    color: #0077cc;
}
.compare-grid {
    margin: 1em 0;
}
.compare-col {
    margin: 0.8em 0;
    padding: 0.8em;
    border: 1px solid #ddd;
}
.compare-col h4 {
    margin-top: 0;
    padding-bottom: 0.3em;
    border-bottom: 1px solid #ddd;
}
.compare-col ul {
    padding-left: 1.2em;
}
.compare-col li {
    margin: 0.3em 0;
    font-size: 0.9em;
}
.bar-item {
    margin: 0.4em 0;
    font-size: 0.9em;
}
.bar-label {
    display: inline;
    font-weight: bold;
}
.bar-value {
    font-family: "Courier New", monospace;
    font-weight: bold;
}
.flow-step {
    margin: 1em 0;
    padding: 0.8em 1em;
    border-left: 3px solid #0077cc;
    background: #f5f9ff;
}
.flow-arrow {
    text-align: center;
    font-size: 1.5em;
    color: #999;
    margin: 0.3em 0;
}
a {
    color: #0066cc;
}
.source-list {
    margin: 0;
    padding: 0;
    list-style: none;
}
.source-list li {
    padding: 0.3em 0;
    font-size: 0.85em;
}
.tag {
    font-size: 0.7em;
    font-weight: bold;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    padding: 0.1em 0.4em;
    border: 1px solid #ccc;
    border-radius: 3px;
}
.cover-page {
    text-align: center;
    padding: 3em 1em;
}
.cover-title {
    font-size: 3em;
    font-weight: bold;
    margin-bottom: 0.5em;
    color: #111;
}
.cover-subtitle {
    font-size: 1.2em;
    color: #666;
    line-height: 1.6;
}
"""

# ─── CONTENT EXTRACTION ────────────────────────────────────────────────────

def read_html():
    with open(SOURCE, 'r', encoding='utf-8') as f:
        return f.read()

def clean_html_entities(text):
    """Convert HTML entities to readable text."""
    replacements = {
        '&mdash;': '—', '&ndash;': '–', '&hellip;': '…',
        '&ldquo;': '"', '&rdquo;': '"', '&lsquo;': ''', '&rsquo;': ''',
        '&amp;': '&', '&lt;': '<', '&gt;': '>', '&quot;': '"',
        '&aacute;': 'á', '&eacute;': 'é', '&uuml;': 'ü',
        '&rarr;': '→', '&larr;': '←', '&darr;': '↓', '&uarr;': '↑',
        '&bull;': '•', '&pound;': '£', '&#10;': '\n',
        '&nbsp;': ' ', '&#8595;': '↓', '&#8734;': '∞',
        '&#9654;': '▶', '&#9646;': '⏸', '&#9197;': '⏭', '&#9198;': '⏮',
        '&#128266;': '🔊', '&#128263;': '🔇',
    }
    for entity, char in replacements.items():
        text = text.replace(entity, char)
    # Handle numeric entities
    text = re.sub(r'&#(\d+);', lambda m: chr(int(m.group(1))), text)
    return text

def strip_tags(html_str):
    """Remove HTML tags but keep text content."""
    text = re.sub(r'<br\s*/?>', '\n', html_str)
    text = re.sub(r'<[^>]+>', '', text)
    text = clean_html_entities(text)
    return text.strip()

def extract_inner(html_str, tag_pattern):
    """Extract content between opening and closing tags."""
    m = re.search(tag_pattern, html_str, re.DOTALL)
    return m.group(1) if m else ''

def build_book():
    html = read_html()

    book = epub.EpubBook()
    book.set_identifier('forsale-documentary-2026')
    book.set_title('For Sale: How Money Bought Power, From the Pyramids to the Blockchain')
    book.set_language('en')
    book.add_author('Dan')

    # Add CSS
    css = epub.EpubItem(uid='style', file_name='style/book.css',
                        media_type='text/css', content=BOOK_CSS.encode('utf-8'))
    book.add_item(css)

    chapters = []
    toc_list = []

    # ─── COVER PAGE ─────────────────────────────────────────────────────
    cover_html = '''<html><head><link rel="stylesheet" href="style/book.css"/></head><body>
    <div class="cover-page" style="background:#111;color:#eee;min-height:100%;padding:4em 2em;">
    <div class="cover-title" style="color:#fff;font-size:3.5em;margin-top:2em;">FOR SALE</div>
    <div class="cover-subtitle" style="color:#aaa;font-size:1.1em;margin-top:1em;">
    How Money Bought Power,<br/>From the Pyramids to the Blockchain</div>
    <div style="margin-top:3em;color:#666;font-size:0.9em;">An Interactive Documentary</div>
    <div style="margin-top:1em;color:#555;font-size:0.8em;">March 2026</div>
    </div></body></html>'''

    ch_cover = epub.EpubHtml(title='Cover', file_name='cover.xhtml', lang='en')
    ch_cover.content = cover_html.encode('utf-8')
    ch_cover.add_item(css)
    book.add_item(ch_cover)
    chapters.append(ch_cover)

    # ─── HELPER: Create chapter HTML ────────────────────────────────────
    def make_chapter(title, filename, content_html):
        ch = epub.EpubHtml(title=title, file_name=filename, lang='en')
        full = f'<html><head><link rel="stylesheet" href="style/book.css"/></head><body>\n{content_html}\n</body></html>'
        ch.content = full.encode('utf-8')
        ch.add_item(css)
        book.add_item(ch)
        chapters.append(ch)
        toc_list.append(ch)
        return ch

    # ─── HELPER: Extract timeline events ────────────────────────────────
    def parse_timeline_events(section_html):
        events = re.findall(
            r'<div class="tl-event([^"]*)"[^>]*>.*?'
            r'<div class="tl-date">(.*?)</div>.*?'
            r'<div class="tl-title">(.*?)</div>.*?'
            r'<div class="tl-desc">(.*?)</div>',
            section_html, re.DOTALL)
        out = ''
        for cls, date, title, desc in events:
            css_class = 'crisis' if 'crisis' in cls else ('verdict' if 'verdict' in cls else '')
            out += f'<div class="timeline-event {css_class}">\n'
            out += f'<p class="tl-date">{clean_html_entities(strip_tags(date))}</p>\n'
            out += f'<p class="tl-title">{clean_html_entities(strip_tags(title))}</p>\n'
            out += f'<p class="tl-desc">{clean_html_entities(desc.strip())}</p>\n'
            out += '</div>\n'
        return out

    # ─── HELPER: Extract hearing quotes ─────────────────────────────────
    def parse_hearing_quotes(section_html):
        quotes = re.findall(
            r'<div class="hearing-quote"[^>]*>.*?'
            r'<div class="speaker">(.*?)</div>.*?'
            r'<div class="speaker-role">(.*?)</div>.*?'
            r'<div class="testimony">(.*?)</div>.*?'
            r'<div class="hearing-src">(.*?)</div>',
            section_html, re.DOTALL)
        out = ''
        for speaker, role, testimony, src in quotes:
            out += '<div class="hearing-quote">\n'
            out += '<p class="hearing-label">HEARING TRANSCRIPT</p>\n'
            out += f'<p class="hearing-speaker">{clean_html_entities(strip_tags(speaker))}</p>\n'
            out += f'<p class="hearing-role">{clean_html_entities(strip_tags(role))}</p>\n'
            out += f'<p class="hearing-text">{clean_html_entities(strip_tags(testimony))}</p>\n'
            out += f'<p class="hearing-src">{clean_html_entities(strip_tags(src))}</p>\n'
            out += '</div>\n'
        return out

    # ─── HELPER: Extract BBC quotes ─────────────────────────────────────
    def parse_bbc_quotes(section_html):
        quotes = re.findall(
            r'<div class="bbc-quote"[^>]*>.*?'
            r'<div class="bbc-text">(.*?)</div>.*?'
            r'<div class="bbc-src">(.*?)</div>',
            section_html, re.DOTALL)
        out = ''
        for text, src in quotes:
            out += '<div class="bbc-quote">\n'
            out += '<p class="bbc-label">BBC NEWS</p>\n'
            out += f'<p>{clean_html_entities(strip_tags(text))}</p>\n'
            out += f'<p class="hearing-src">{clean_html_entities(strip_tags(src))}</p>\n'
            out += '</div>\n'
        return out

    # ─── HELPER: Extract regular quotes ─────────────────────────────────
    def parse_quotes(section_html):
        quotes = re.findall(
            r'<div class="quote"[^>]*>.*?'
            r'<p class="quote-text">(.*?)</p>.*?'
            r'<p class="quote-author">(.*?)</p>.*?'
            r'<p class="quote-ctx">(.*?)</p>',
            section_html, re.DOTALL)
        out = ''
        for text, author, ctx in quotes:
            out += '<blockquote>\n'
            out += f'<p>{clean_html_entities(strip_tags(text))}</p>\n'
            out += f'<p class="attribution">— {clean_html_entities(strip_tags(author))}</p>\n'
            out += f'<p class="context">{clean_html_entities(strip_tags(ctx))}</p>\n'
            out += '</blockquote>\n'
        return out

    # ─── HELPER: Extract stats ──────────────────────────────────────────
    def parse_stats(section_html):
        stats = re.findall(
            r'<div class="stat">.*?<div class="stat-num"[^>]*>(.*?)</div>.*?'
            r'<div class="stat-label">(.*?)</div>',
            section_html, re.DOTALL)
        if not stats:
            return ''
        out = '<div class="stat-block">\n'
        for num, label in stats:
            out += f'<p><span class="stat-num">{clean_html_entities(strip_tags(num))}</span><br/>\n'
            out += f'<span class="stat-label">{clean_html_entities(strip_tags(label))}</span></p>\n'
        out += '</div>\n'
        return out

    # ─── HELPER: Extract cards ──────────────────────────────────────────
    def parse_cards(section_html):
        cards = re.findall(
            r'<div class="card"[^>]*>.*?<h4[^>]*>(.*?)</h4>.*?<p>(.*?)</p>',
            section_html, re.DOTALL)
        out = ''
        for title, content in cards:
            out += f'<div class="card"><h4>{clean_html_entities(strip_tags(title))}</h4>\n'
            out += f'<p>{clean_html_entities(content.strip())}</p></div>\n'
        return out

    # ─── HELPER: Extract tables ─────────────────────────────────────────
    def parse_tables(section_html):
        tables = re.findall(r'<table class="data-table">(.*?)</table>', section_html, re.DOTALL)
        out = ''
        for table_html in tables:
            out += '<table>\n'
            # Headers
            headers = re.findall(r'<th>(.*?)</th>', table_html, re.DOTALL)
            if headers:
                out += '<thead><tr>'
                for h in headers:
                    out += f'<th>{clean_html_entities(strip_tags(h))}</th>'
                out += '</tr></thead>\n'
            # Rows
            rows = re.findall(r'<tr>(.*?)</tr>', table_html, re.DOTALL)
            out += '<tbody>\n'
            for row in rows:
                cells = re.findall(r'<td[^>]*>(.*?)</td>', row, re.DOTALL)
                if cells:
                    out += '<tr>'
                    for cell in cells:
                        out += f'<td>{clean_html_entities(cell.strip())}</td>'
                    out += '</tr>\n'
            out += '</tbody></table>\n'
        return out

    # ─── HELPER: Extract bars ───────────────────────────────────────────
    def parse_bars(section_html):
        bars = re.findall(
            r'<div class="bar-row">.*?<div class="bar-label">(.*?)</div>.*?'
            r'<div class="bar-fill"[^>]*>(.*?)</div>.*?'
            r'<div class="bar-amt">(.*?)</div>',
            section_html, re.DOTALL)
        if not bars:
            return ''
        out = ''
        for label, fill_text, amt in bars:
            label_clean = clean_html_entities(strip_tags(label))
            amt_clean = clean_html_entities(strip_tags(amt))
            out += f'<p class="bar-item"><span class="bar-label">{label_clean}:</span> '
            out += f'<span class="bar-value">{amt_clean}</span></p>\n'
        return out

    # ─── HELPER: Extract compare columns ────────────────────────────────
    def parse_compare(section_html):
        cols = re.findall(
            r'<div class="compare-col"[^>]*>.*?<h4[^>]*>(.*?)</h4>.*?<ul>(.*?)</ul>',
            section_html, re.DOTALL)
        if not cols:
            return ''
        out = '<div class="compare-grid">\n'
        for title, items_html in cols:
            out += f'<div class="compare-col"><h4>{clean_html_entities(strip_tags(title))}</h4>\n<ul>\n'
            items = re.findall(r'<li>(.*?)</li>', items_html, re.DOTALL)
            for item in items:
                # Remove inline positioned spans
                item_clean = re.sub(r'<span style="position:absolute[^"]*"[^>]*></span>', '', item)
                out += f'<li>{clean_html_entities(item_clean.strip())}</li>\n'
            out += '</ul></div>\n'
        out += '</div>\n'
        return out

    # ─── HELPER: Extract callouts ───────────────────────────────────────
    def parse_callouts(section_html):
        callouts = re.findall(r'<div class="callout"[^>]*>\s*<p[^>]*>(.*?)</p>', section_html, re.DOTALL)
        out = ''
        for c in callouts:
            out += f'<div class="callout"><p>{clean_html_entities(c.strip())}</p></div>\n'
        return out

    # ─── HELPER: Extract connection/dossier profiles ────────────────────
    def parse_dossiers(section_html):
        persons = re.findall(
            r'<div class="conn-person[^"]*"[^>]*>.*?'
            r'<div class="cp-name">(.*?)</div>.*?'
            r'<div class="cp-title">(.*?)</div>.*?'
            r'<ul class="cp-links">(.*?)</ul>',
            section_html, re.DOTALL)
        out = ''
        for name, title, links_html in persons:
            out += '<div class="dossier">\n'
            out += f'<p class="dossier-name">{clean_html_entities(strip_tags(name))}</p>\n'
            out += f'<p class="dossier-title">{clean_html_entities(strip_tags(title))}</p>\n'
            items = re.findall(r'<li>(.*?)</li>', links_html, re.DOTALL)
            if items:
                out += '<ul class="dossier-links">\n'
                for item in items:
                    out += f'<li>{clean_html_entities(item.strip())}</li>\n'
                out += '</ul>\n'
            out += '</div>\n'
        return out

    # ─── HELPER: Extract victims ────────────────────────────────────────
    def parse_victims(section_html):
        victims = re.findall(
            r'<div class="victim">.*?'
            r'<div class="name">(.*?)</div>.*?'
            r'<div class="loss">(.*?)</div>.*?'
            r'<div class="story">(.*?)</div>',
            section_html, re.DOTALL)
        out = ''
        for name, loss, story in victims:
            out += '<div class="victim">\n'
            out += f'<p class="victim-name">{clean_html_entities(strip_tags(name))}</p>\n'
            out += f'<p class="victim-loss">{clean_html_entities(strip_tags(loss))}</p>\n'
            out += f'<p>{clean_html_entities(strip_tags(story))}</p>\n'
            out += '</div>\n'
        return out

    # ─── HELPER: Extract paragraphs from section ────────────────────────
    def parse_paragraphs(section_html):
        paras = re.findall(r'<p[^>]*>(.*?)</p>', section_html, re.DOTALL)
        out = ''
        for p in paras:
            text = clean_html_entities(p.strip())
            if text and not any(text.startswith(x) for x in ['<', 'Scroll to begin']):
                # Preserve strong/em
                text = re.sub(r'<strong[^>]*>', '<strong>', text)
                text = re.sub(r'<em[^>]*>', '<em>', text)
                # Remove other tags
                text = re.sub(r'<(?!/?(?:strong|em|br|a)\b)[^>]+>', '', text)
                out += f'<p>{text}</p>\n'
        return out

    # ─── HELPER: Generic section extractor ──────────────────────────────
    def extract_section_content(section_html):
        """Extract all content types from a section."""
        content = ''
        # Paragraphs (body text)
        content += parse_paragraphs(section_html)
        # Stats
        content += parse_stats(section_html)
        # Timeline events
        content += parse_timeline_events(section_html)
        # Hearing quotes
        content += parse_hearing_quotes(section_html)
        # BBC quotes
        content += parse_bbc_quotes(section_html)
        # Regular quotes
        content += parse_quotes(section_html)
        # Bars
        content += parse_bars(section_html)
        # Compare columns
        content += parse_compare(section_html)
        # Tables
        content += parse_tables(section_html)
        # Cards
        content += parse_cards(section_html)
        # Callouts
        content += parse_callouts(section_html)
        # Dossiers/connections
        content += parse_dossiers(section_html)
        # Victims
        content += parse_victims(section_html)
        return content

    # ─── CHAPTER 1: INTRODUCTION ────────────────────────────────────────
    # Hero + intro text
    hero_match = re.search(r'<!-- ===== HERO ===== -->.*?<!-- =+\s*\n<!-- ACT I', html, re.DOTALL)
    hero_html = hero_match.group(0) if hero_match else ''

    ch1_content = '<h1>For Sale</h1>\n'
    ch1_content += '<p style="text-align:center;font-style:italic;">How Money Bought Power, From the Pyramids to the Blockchain</p>\n'
    ch1_content += '<p style="text-align:center;">An Interactive Documentary — March 2026</p>\n<hr/>\n'
    ch1_content += '<p>From the Big Bang to the blockchain, energy has always flowed toward whoever can concentrate it. The only thing that changes is the tool — and the speed.</p>\n'
    ch1_content += '<div class="stat-block">\n'
    ch1_content += '<p><span class="stat-num">13.8 BILLION YEARS</span></p>\n'
    ch1_content += '<p><span class="stat-num">$245M IN PAC SPENDING</span></p>\n'
    ch1_content += '<p><span class="stat-num">$11.6B PRESIDENTIAL CRYPTO</span></p>\n'
    ch1_content += '<p><span class="stat-num">3 PARDONS IN 10 MONTHS</span></p>\n'
    ch1_content += '</div>\n'
    make_chapter('Introduction', 'ch01_intro.xhtml', ch1_content)

    # ─── CHAPTER 2: ACT I — IN THE BEGINNING ───────────────────────────
    act1_match = re.search(r'<!-- ACT I: IN THE BEGINNING.*?<!-- =+\s*\n<!-- ACT II: DOMINANCE', html, re.DOTALL)
    act1_html = act1_match.group(0) if act1_match else ''

    ch2_content = '<h1>Act I: In the Beginning</h1>\n'
    ch2_content += '<p style="text-align:center;font-style:italic;">13.8 BILLION YEARS AGO</p>\n'
    ch2_content += '<p style="text-align:center;">Before corruption, before money, before life — there was only energy looking for structure.</p>\n<hr/>\n'
    ch2_content += extract_section_content(act1_html)
    make_chapter('Act I: In the Beginning', 'ch02_act1.xhtml', ch2_content)

    # ─── CHAPTER 3: ACT II — DOMINANCE ──────────────────────────────────
    act2_match = re.search(r'<!-- ACT II: DOMINANCE.*?<!-- =+\s*\n<!-- ACT II: THE PROMISE', html, re.DOTALL)
    act2_html = act2_match.group(0) if act2_match else ''

    ch3_content = '<h1>Act II: Dominance</h1>\n'
    ch3_content += '<p style="text-align:center;font-style:italic;">252 MYA – 1945 CE</p>\n'
    ch3_content += '<p style="text-align:center;">Every dominant species believes its reign is permanent. None of them are right.</p>\n<hr/>\n'
    ch3_content += extract_section_content(act2_html)
    make_chapter('Act II: Dominance', 'ch03_act2.xhtml', ch3_content)

    # ─── CHAPTER 4: ACT III — THE PROMISE ───────────────────────────────
    act2b_match = re.search(r'<!-- ACT II: THE PROMISE.*?<!-- =+\s*\n<!-- THE AI PATTERN', html, re.DOTALL)
    act2b_html = act2b_match.group(0) if act2b_match else ''

    ch4_content = '<h1>Act III: The Promise</h1>\n'
    ch4_content += '<p style="text-align:center;font-style:italic;">2008 – 2019</p>\n'
    ch4_content += '<p style="text-align:center;">"A purely peer-to-peer version of electronic cash would allow online payments to be sent directly from one party to another without going through a financial institution."</p>\n<hr/>\n'
    ch4_content += extract_section_content(act2b_html)
    make_chapter('Act III: The Promise', 'ch04_act3.xhtml', ch4_content)

    # ─── CHAPTER 5: AI ACROSS THE DECADES ───────────────────────────────
    ai_match = re.search(r'<!-- THE AI PATTERN.*?<!-- =+\s*\n<!-- ACT IV: THE FRAUD', html, re.DOTALL)
    ai_html = ai_match.group(0) if ai_match else ''

    ch5_content = '<h1>The Machine That Learns: AI Across the Decades</h1>\n'
    ch5_content += '<p style="text-align:center;">Every generation promises artificial intelligence will change everything. Every generation is right — just not in the way they promised.</p>\n<hr/>\n'
    ch5_content += extract_section_content(ai_html)
    make_chapter('AI Across the Decades', 'ch05_ai.xhtml', ch5_content)

    # ─── CHAPTER 6: ACT IV — THE $8 BILLION LIE ────────────────────────
    act4_match = re.search(r'<!-- ACT IV: THE FRAUD.*?<!-- =+\s*\n<!-- ACT IV: THE REVOLVING DOOR', html, re.DOTALL)
    act4_html = act4_match.group(0) if act4_match else ''

    ch6_content = '<h1>Act IV: The $8 Billion Lie</h1>\n'
    ch6_content += '<p style="text-align:center;font-style:italic;">2019 – 2023</p>\n'
    ch6_content += '<p style="text-align:center;">Sam Bankman-Fried built a $32 billion empire on stolen customer funds and crashed it in six days.</p>\n<hr/>\n'
    ch6_content += extract_section_content(act4_html)
    make_chapter('Act IV: The $8 Billion Lie', 'ch06_act4.xhtml', ch6_content)

    # ─── CHAPTER 7: ACT V — THE REVOLVING DOOR ─────────────────────────
    act5_match = re.search(r'<!-- ACT IV: THE REVOLVING DOOR.*?<!-- =+\s*\n<!-- ACT V: THE TAKEOVER', html, re.DOTALL)
    act5_html = act5_match.group(0) if act5_match else ''

    ch7_content = '<h1>Act V: The Revolving Door</h1>\n'
    ch7_content += '<p style="text-align:center;font-style:italic;">2021 – 2022</p>\n'
    ch7_content += '<p style="text-align:center;">FTX hired 13 former CFTC officials. One in three members of Congress took FTX money. 73% never gave it back.</p>\n<hr/>\n'
    ch7_content += extract_section_content(act5_html)
    make_chapter('Act V: The Revolving Door', 'ch07_act5.xhtml', ch7_content)

    # ─── CHAPTER 8: ACT VI — THE TAKEOVER ──────────────────────────────
    act6_match = re.search(r'<!-- ACT V: THE TAKEOVER.*?<!-- =+\s*\n<!-- THE RISE AND FALL OF META', html, re.DOTALL)
    act6_html = act6_match.group(0) if act6_match else ''

    ch8_content = '<h1>Act VI: The Takeover</h1>\n'
    ch8_content += '<p style="text-align:center;font-style:italic;">2024 – 2026</p>\n'
    ch8_content += '<p style="text-align:center;">SBF went to prison. The industry took notes — and did it better.</p>\n<hr/>\n'
    ch8_content += extract_section_content(act6_html)
    make_chapter('Act VI: The Takeover', 'ch08_act6.xhtml', ch8_content)

    # ─── CHAPTER 9: FACEBOOK / META ─────────────────────────────────────
    meta_match = re.search(r'<!-- THE RISE AND FALL OF META.*?<!-- =+\s*\n<!-- ACT VII: BIG TECH BUYS IN', html, re.DOTALL)
    meta_html = meta_match.group(0) if meta_match else ''

    ch9_content = '<h1>The Rise and Fall of Facebook</h1>\n'
    ch9_content += '<p style="text-align:center;">Mark Zuckerberg built the most powerful communication platform in human history. Then he learned what power costs.</p>\n<hr/>\n'
    ch9_content += extract_section_content(meta_html)
    make_chapter('The Rise and Fall of Facebook', 'ch09_meta.xhtml', ch9_content)

    # ─── CHAPTER 10: ACT VII — BIG TECH PAYS TRIBUTE ───────────────────
    act7_match = re.search(r'<!-- ACT VII: BIG TECH BUYS IN.*?<!-- =+\s*\n<!-- ACT VII: THE PRESIDENT PROFITS', html, re.DOTALL)
    act7_html = act7_match.group(0) if act7_match else ''

    ch10_content = '<h1>Act VII: Big Tech Pays Tribute</h1>\n'
    ch10_content += '<p style="text-align:center;font-style:italic;">JANUARY 2025</p>\n'
    ch10_content += '<p style="text-align:center;">Every major tech CEO wrote a $1 million check to the inauguration. Then the favors started flowing.</p>\n<hr/>\n'
    ch10_content += extract_section_content(act7_html)
    make_chapter('Act VII: Big Tech Pays Tribute', 'ch10_act7.xhtml', ch10_content)

    # ─── CHAPTER 11: ACT VIII — THE PRESIDENT PROFITS ───────────────────
    act8_match = re.search(r'<!-- ACT VII: THE PRESIDENT PROFITS.*?<!-- =+\s*\n<!-- CONTENT MODERATION', html, re.DOTALL)
    act8_html = act8_match.group(0) if act8_match else ''

    ch11_content = '<h1>Act VIII: The President Profits</h1>\n'
    ch11_content += '<p style="text-align:center;font-style:italic;">2025 – PRESENT</p>\n'
    ch11_content += '<p style="text-align:center;">The president holds $11.6 billion in crypto while signing executive orders that boost its value.</p>\n<hr/>\n'
    ch11_content += extract_section_content(act8_html)
    make_chapter('Act VIII: The President Profits', 'ch11_act8.xhtml', ch11_content)

    # ─── CHAPTER 12: CONTENT MODERATION + THE PATTERN ───────────────────
    pattern_match = re.search(r'<!-- CONTENT MODERATION.*?<!-- =+\s*\n<!-- THE WEB: NAMES', html, re.DOTALL)
    pattern_html = pattern_match.group(0) if pattern_match else ''

    ch12_content = '<h1>The Pattern</h1>\n'
    ch12_content += '<p style="text-align:center;">Same playbook, every era. Just faster.</p>\n<hr/>\n'
    ch12_content += '<h2>What $1 Million Buys</h2>\n'
    ch12_content += '<p>After the inauguration checks cleared, Big Tech changed its tune.</p>\n'
    ch12_content += extract_section_content(pattern_html)
    make_chapter('The Pattern', 'ch12_pattern.xhtml', ch12_content)

    # ─── CHAPTER 13: THE WEB — PAYPAL MAFIA ────────────────────────────
    web_match = re.search(r'<!-- THE WEB: NAMES.*?<!-- Goldman Sachs to Government', html, re.DOTALL)
    web_html = web_match.group(0) if web_match else ''

    ch13_content = '<h1>The Web: The PayPal Mafia</h1>\n'
    ch13_content += '<p style="text-align:center;">These are not separate stories. They are the same people, connected by money, loyalty, and access.</p>\n<hr/>\n'
    ch13_content += '<h2>One Company. Six Billionaires. The Entire Power Structure.</h2>\n'
    ch13_content += '<p>They built PayPal together in 1999. Then they built everything else.</p>\n'
    ch13_content += extract_section_content(web_html)
    make_chapter('The Web: PayPal Mafia', 'ch13_paypal.xhtml', ch13_content)

    # ─── CHAPTER 14: GOLDMAN + CRYPTO PIPELINE ─────────────────────────
    goldman_match = re.search(r'<!-- Goldman Sachs to Government.*?<!-- The AI Power Web', html, re.DOTALL)
    goldman_html = goldman_match.group(0) if goldman_match else ''

    ch14_content = '<h1>The Goldman Pipeline & The Crypto-to-White House Pipeline</h1>\n<hr/>\n'
    ch14_content += '<h2>Goldman Sachs: The Government\'s Farm Team</h2>\n'
    ch14_content += '<p>More Goldman alumni have served in senior government roles than from any other private institution in history.</p>\n'
    ch14_content += extract_section_content(goldman_html)
    make_chapter('Goldman Pipeline & Crypto Pipeline', 'ch14_goldman.xhtml', ch14_content)

    # ─── CHAPTER 15: AI POWER WEB + DEFENSE ─────────────────────────────
    ai_web_match = re.search(r'<!-- The AI Power Web.*?<!-- The SBF Web', html, re.DOTALL)
    ai_web_html = ai_web_match.group(0) if ai_web_match else ''

    ch15_content = '<h1>The AI Power Web & The Defense Revolving Door</h1>\n<hr/>\n'
    ch15_content += '<h2>Who Controls AI</h2>\n'
    ch15_content += '<p>The same names keep appearing. The same money flows between the same nodes.</p>\n'
    ch15_content += extract_section_content(ai_web_html)
    make_chapter('AI Power Web & Defense', 'ch15_ai_defense.xhtml', ch15_content)

    # ─── CHAPTER 16: THE SBF WEB + BILLIONAIRE TABLE ────────────────────
    sbf_web_match = re.search(r'<!-- The SBF Web.*?<!-- The Billionaire Dinner Table -->', html, re.DOTALL)
    sbf_web_html = sbf_web_match.group(0) if sbf_web_match else ''

    dinner_match = re.search(r'<!-- The Billionaire Dinner Table.*?<!-- ===== THE ROTHSCHILD', html, re.DOTALL)
    if not dinner_match:
        dinner_match = re.search(r'<!-- The Billionaire Dinner Table.*?<!-- The Supreme Court', html, re.DOTALL)
    dinner_html = dinner_match.group(0) if dinner_match else ''

    ch16_content = '<h1>The SBF Web & The Billionaire Dinner Table</h1>\n<hr/>\n'
    ch16_content += '<h2>Everyone Who Touched FTX Money</h2>\n'
    ch16_content += '<p>The donations, the meetings, the family connections, the investors who looked the other way.</p>\n'
    ch16_content += extract_section_content(sbf_web_html)
    ch16_content += '<h2>Everyone at the Table</h2>\n'
    ch16_content += '<p>The 2025 inauguration was not a ceremony. It was a shareholder meeting.</p>\n'
    ch16_content += extract_section_content(dinner_html)
    make_chapter('SBF Web & Billionaire Table', 'ch16_sbf_dinner.xhtml', ch16_content)

    # ─── CHAPTER 17: VICTIMS + TETHER + ROTHSCHILDS ─────────────────────
    victims_match = re.search(r'<!-- THE VICTIMS.*?<!-- The Rothschild Thread -->', html, re.DOTALL)
    victims_html = victims_match.group(0) if victims_match else ''

    roth_match = re.search(r'<!-- The Rothschild Thread.*?<!-- =+\s*\n<!-- WARS FOR PROFIT', html, re.DOTALL)
    if not roth_match:
        roth_match = re.search(r'<!-- The Rothschild Thread.*?<!-- =+\s*\n<!-- =+\s*\n<!-- WARS FOR PROFIT', html, re.DOTALL)
    roth_html = roth_match.group(0) if roth_match else ''

    tether_match = re.search(r'<!-- TETHER.*?<!-- The Rothschild Thread', html, re.DOTALL)
    tether_html = tether_match.group(0) if tether_match else ''

    ch17_content = '<h1>The Human Cost</h1>\n<hr/>\n'
    ch17_content += '<h2>Real People, Real Losses</h2>\n'
    ch17_content += '<p>Behind every billion-dollar fraud are thousands of people whose lives were destroyed.</p>\n'
    ch17_content += extract_section_content(victims_html)
    ch17_content += '<h2>Tether: The $100 Billion Mystery</h2>\n'
    ch17_content += '<p>The most important financial institution in crypto has never completed a full audit.</p>\n'
    ch17_content += extract_section_content(tether_html)
    ch17_content += '<h2>The Rothschilds: Five Brothers, Five Countries, Every War</h2>\n'
    ch17_content += '<p>The family that invented modern sovereign debt financing — by funding both sides.</p>\n'
    ch17_content += extract_section_content(roth_html)
    make_chapter('The Human Cost', 'ch17_victims.xhtml', ch17_content)

    # ─── CHAPTER 18: WARS FOR PROFIT ────────────────────────────────────
    wars_match = re.search(r'<!-- WARS FOR PROFIT.*?<!-- ===== THE DOSSIERS', html, re.DOTALL)
    if not wars_match:
        wars_match = re.search(r'Follow the Money Through Every War.*?<!-- ===== THE DOSSIERS', html, re.DOTALL)
    wars_html = wars_match.group(0) if wars_match else ''

    ch18_content = '<h1>Follow the Money Through Every War</h1>\n'
    ch18_content += '<p style="text-align:center;">Every war in history was funded by someone. Every one of them made someone rich. Here is the ledger.</p>\n<hr/>\n'
    ch18_content += extract_section_content(wars_html)
    make_chapter('Wars for Profit', 'ch18_wars.xhtml', ch18_content)

    # ─── CHAPTER 19: THE DOSSIERS ───────────────────────────────────────
    dossiers_match = re.search(r'<!-- ===== THE DOSSIERS.*?<!-- ===== NETWORK VISUALIZATION', html, re.DOTALL)
    if not dossiers_match:
        dossiers_match = re.search(r'<!-- ===== THE DOSSIERS.*?<svg', html, re.DOTALL)
    dossiers_html = dossiers_match.group(0) if dossiers_match else ''

    ch19_content = '<h1>The Dossiers</h1>\n'
    ch19_content += '<p style="text-align:center;">Every name. Every connection. Every dollar.</p>\n<hr/>\n'
    ch19_content += extract_section_content(dossiers_html)
    make_chapter('The Dossiers', 'ch19_dossiers.xhtml', ch19_content)

    # ─── CHAPTER 20: FOLLOW THE MONEY (THE CYCLE) ──────────────────────
    cycle_match = re.search(r'<!-- ===== FOLLOW THE MONEY.*?<!-- ===== REVOLVING DOOR DATABASE', html, re.DOTALL)
    cycle_html = cycle_match.group(0) if cycle_match else ''

    ch20_content = '<h1>Follow the Money: The Cycle</h1>\n'
    ch20_content += '<p style="text-align:center;">Six steps. Endlessly repeating. Each revolution transfers more wealth upward.</p>\n<hr/>\n'

    # Extract flow steps manually
    steps = re.findall(
        r'<h4[^>]*>(.*?)</h4>.*?<p>(.*?)</p>.*?<div class="amount"[^>]*>(.*?)</div>',
        cycle_html, re.DOTALL)
    for title, desc, amt in steps:
        title_clean = clean_html_entities(strip_tags(title))
        desc_clean = clean_html_entities(strip_tags(desc))
        amt_clean = clean_html_entities(strip_tags(amt))
        ch20_content += f'<div class="flow-step"><h4>{title_clean} — {amt_clean}</h4>\n<p>{desc_clean}</p></div>\n'
        ch20_content += '<p class="flow-arrow">↓</p>\n'

    ch20_content += parse_hearing_quotes(cycle_html)
    make_chapter('Follow the Money: The Cycle', 'ch20_cycle.xhtml', ch20_content)

    # ─── CHAPTER 21: REVOLVING DOOR DATABASE ────────────────────────────
    revolving_match = re.search(r'<!-- ===== REVOLVING DOOR DATABASE.*?<!-- ===== WAR PROFITEERS', html, re.DOTALL)
    revolving_html = revolving_match.group(0) if revolving_match else ''

    ch21_content = '<h1>The Full Revolving Door</h1>\n'
    ch21_content += '<p style="text-align:center;">Every door that spun. Every conflict it created. Government to industry. Industry to government.</p>\n<hr/>\n'
    ch21_content += extract_section_content(revolving_html)
    make_chapter('The Revolving Door Database', 'ch21_revolving.xhtml', ch21_content)

    # ─── CHAPTER 22: WAR PROFITEERS ─────────────────────────────────────
    profiteers_match = re.search(r'<!-- ===== WAR PROFITEERS.*?<!-- ===== TOP DONORS', html, re.DOTALL)
    profiteers_html = profiteers_match.group(0) if profiteers_match else ''

    ch22_content = '<h1>War Profiteers: The Modern Era</h1>\n'
    ch22_content += '<p style="text-align:center;">The contracts are in the billions. The consequences are in the body bags.</p>\n<hr/>\n'
    ch22_content += extract_section_content(profiteers_html)
    make_chapter('War Profiteers', 'ch22_profiteers.xhtml', ch22_content)

    # ─── CHAPTER 23: TOP DONORS 2024 ───────────────────────────────────
    donors_match = re.search(r'<!-- ===== TOP DONORS 2024.*?<!-- ===== WHISTLEBLOWERS', html, re.DOTALL)
    donors_html = donors_match.group(0) if donors_match else ''

    ch23_content = '<h1>Top Political Donors: 2024 Cycle</h1>\n'
    ch23_content += '<p style="text-align:center;">The 20 largest individual political donors in American history — all from a single election cycle.</p>\n<hr/>\n'
    ch23_content += extract_section_content(donors_html)
    make_chapter('Top Donors 2024', 'ch23_donors.xhtml', ch23_content)

    # ─── CHAPTER 24: WHISTLEBLOWERS ─────────────────────────────────────
    whistle_match = re.search(r'<!-- ===== WHISTLEBLOWERS.*?<!-- ===== WHAT THEY DON\'T WANT', html, re.DOTALL)
    whistle_html = whistle_match.group(0) if whistle_match else ''

    ch24_content = '<h1>The Whistleblowers & Journalists Who Fought Back</h1>\n'
    ch24_content += '<p style="text-align:center;">While billions flowed to silence truth, these people published it anyway.</p>\n<hr/>\n'
    ch24_content += extract_section_content(whistle_html)
    make_chapter('Whistleblowers', 'ch24_whistleblowers.xhtml', ch24_content)

    # ─── CHAPTER 25: HIDDEN CONNECTIONS ─────────────────────────────────
    hidden_match = re.search(r'<!-- ===== WHAT THEY DON\'T WANT.*?<!-- ===== CLOSING', html, re.DOTALL)
    hidden_html = hidden_match.group(0) if hidden_match else ''

    ch25_content = '<h1>What They Don\'t Want You to See</h1>\n'
    ch25_content += '<p style="text-align:center;">These connections are documented. They are not conspiracy. They are public record.</p>\n<hr/>\n'
    ch25_content += extract_section_content(hidden_html)
    make_chapter('Hidden Connections', 'ch25_hidden.xhtml', ch25_content)

    # ─── CHAPTER 26: CLOSING ────────────────────────────────────────────
    closing_match = re.search(r'<!-- ===== CLOSING ===== -->.*?<!-- ===== CORRECTIONS', html, re.DOTALL)
    closing_html = closing_match.group(0) if closing_match else ''

    ch26_content = '<h1>Closing</h1>\n<hr/>\n'
    ch26_content += extract_section_content(closing_html)

    # Add the closing poetry manually since it's in specific styling
    ch26_content += '<p style="text-align:center;font-size:1.2em;">'
    ch26_content += 'The universe took 13.8 billion years to create life.<br/>'
    ch26_content += 'Dinosaurs dominated for 165 million years.<br/>'
    ch26_content += 'The pyramids took generations.<br/>'
    ch26_content += 'The microchip took a decade to change everything.<br/>'
    ch26_content += 'AI was promised in 20 years. It took 67.<br/>'
    ch26_content += 'Facebook connected 3 billion people. Then sold them.<br/>'
    ch26_content += 'Enron took a decade to build and a week to collapse.<br/>'
    ch26_content += 'Wall Street took decades. Got bailed out in days.<br/>'
    ch26_content += 'FTX took three years. Collapsed in six days.<br/>'
    ch26_content += 'The crypto takeover of the U.S. government took ten months.</p>\n'
    ch26_content += '<p style="text-align:center;font-style:italic;">The only thing that changes is the speed. The game never changes.</p>\n'
    ch26_content += '<p style="text-align:center;font-size:1.1em;margin-top:2em;">'
    ch26_content += 'Everything is for sale.<br/>'
    ch26_content += 'The only question is whether you\'re buying —<br/>'
    ch26_content += 'or being sold.</p>\n'
    ch26_content += '<p style="text-align:center;font-style:italic;">If you\'ve read this far, you already know the answer.</p>\n'
    make_chapter('Closing', 'ch26_closing.xhtml', ch26_content)

    # ─── CHAPTER 27: SOURCES ────────────────────────────────────────────
    ch27_content = '<h1>Sources</h1>\n'
    ch27_content += '<p>All figures from court filings, DOJ press releases, CFTC/SEC filings, FEC disclosures, Congressional records, and investigative journalism.</p>\n<hr/>\n'
    ch27_content += '<ul class="source-list">\n'

    sources = [
        ('C-SPAN', 'Congressional hearings: Senate Banking, House Financial Services, Senate Commerce', 'https://www.c-span.org/search/?query=crypto+hearing'),
        ('BBC', 'FTX, Meta, DOGE, AI, crypto pardons, war economics', 'https://www.bbc.com/news/topics/cz4pr2gd85qt'),
        ('Reuters', 'Clemency history, tech lobbying, arms trade', 'https://www.reuters.com/technology/crypto-currencies/'),
        ('Washington Post', 'FTX donations, CFTC revolving door, Musk contracts, Facebook Papers, Afghanistan Papers', 'https://www.washingtonpost.com/technology/2023/12/14/ftx-political-donations/'),
        ('New York Times', 'Cambridge Analytica, Fairshake PAC, AI lobbying, IBM & Nazi Germany', 'https://www.nytimes.com/topic/subject/cryptocurrency'),
        ('DOJ', 'SBF sentencing, BitMEX plea, CZ conviction', 'https://www.justice.gov/usao-sdny/pr/samuel-bankman-fried-sentenced-25-years'),
        ('SEC/CFTC', 'Enforcement actions, $12.7B judgment, Atkins disclosure', 'https://www.sec.gov/litigation'),
        ('FEC', 'Campaign finance data, PAC filings, individual contributions', 'https://www.fec.gov/data/'),
        ('OpenSecrets', 'Lobbying data, defense contractor spending, crypto PACs', 'https://www.opensecrets.org/'),
        ('CoinDesk', 'Alameda balance sheet leak (the article that started the collapse)', 'https://www.coindesk.com/policy/2022/11/02/divisions-in-sam-bankman-frieds-crypto-empire-blur-on-his-trading-titan-alamedas-balance-sheet/'),
        ('POGO', 'Pentagon revolving door database (674 officials)', 'https://www.pogo.org/database/pentagon-revolving-door'),
        ('Brown University', 'Costs of War Project ($8T, 900K+ killed)', 'https://watson.brown.edu/costsofwar/'),
        ('Better Markets', 'FTX revolving door (13 CFTC officials)', 'https://bettermarkets.org/analysis/the-ftx-revolving-door/'),
        ('Public Citizen', 'Fairshake PAC analysis, corporate conflicts', 'https://www.citizen.org/article/crypto-industry-2024-election-spending/'),
        ('NPR', 'SBF sentencing, CZ pardon, GENIUS Act, Ulbricht', 'https://www.npr.org/sections/money/'),
        ('Fortune', 'Trump crypto empire, DOGE conflicts', 'https://fortune.com/crypto/'),
        ('The Intercept', 'BitMEX corporate pardon (unprecedented)', 'https://theintercept.com/'),
        ('MIT Technology Review', 'OpenAI lobbying, AI history', 'https://www.technologyreview.com/'),
        ('Computer History Museum', 'ENIAC, Dartmouth, AI winters', 'https://computerhistory.org/'),
        ('Gen. Smedley Butler', '"War Is a Racket" (1935, full text, public domain)', 'https://www.gutenberg.org/ebooks/49966'),
        ('Eisenhower Library', 'Military-Industrial Complex farewell address', 'https://www.eisenhowerlibrary.gov/eisenhowers/speeches'),
    ]

    for name, desc, url in sources:
        ch27_content += f'<li><strong>{name}</strong> — {desc}<br/><a href="{url}">{url}</a></li>\n'

    ch27_content += '</ul>\n'
    ch27_content += '<hr/>\n'
    ch27_content += '<p style="text-align:center;">Corrections: <a href="mailto:forsale.documentary@protonmail.com">forsale.documentary@protonmail.com</a></p>\n'
    ch27_content += '<p style="text-align:center;font-size:0.8em;color:#999;">&copy; 2026. All rights reserved.</p>\n'
    make_chapter('Sources', 'ch27_sources.xhtml', ch27_content)

    # ─── ASSEMBLE BOOK ──────────────────────────────────────────────────
    book.toc = toc_list
    book.spine = ['nav'] + chapters
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())

    epub.write_epub(str(OUTPUT), book)
    print(f"EPUB created: {OUTPUT}")
    print(f"Size: {OUTPUT.stat().st_size / 1024:.0f} KB")
    print(f"Chapters: {len(toc_list)}")

if __name__ == '__main__':
    build_book()
