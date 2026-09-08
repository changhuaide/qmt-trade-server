#!/usr/bin/env python
#coding:utf-8
"""
Download QMT official documentation from dict.thinktrader.net
Fast version - directly fetch content chunks.
"""

import os
import re
import json
import urllib.request
import html as html_module
import time

# innerApi pages to download (from navigation)
PAGES = [
    ('start_now', '快速开始'),
    ('variable_convention', '变量约定'),
    ('interface_operation', '接口操作'),
    ('callback_function', '回调函数'),
    ('data_function', '数据函数'),
    ('quote_function', '行情函数'),
    ('trading_function', '交易函数'),
    ('system_function', '系统函数'),
    ('data_structure', '数据结构'),
    ('enum_constants', '枚举常量'),
    ('drawing_function', '绘图函数'),
    ('code_examples', '代码示例'),
    ('user_attention', '注意事项'),
    ('question_answer', '常见问题'),
]

BASE_URL = 'https://dict.thinktrader.net'
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'docs', 'qmt_official')


def fetch(url, retries=2):
    """Fetch URL with retries."""
    for attempt in range(retries + 1):
        try:
            req = urllib.request.Request(url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            with urllib.request.urlopen(req, timeout=10) as resp:
                return resp.read().decode('utf-8', errors='replace')
        except Exception as e:
            if attempt == retries:
                print(f"  FAIL: {e}")
                return None
            time.sleep(0.5)


def get_content_chunk_url(page_name):
    """Get the URL of the JS chunk containing the page content."""
    # Fetch the HTML page
    html_url = f"{BASE_URL}/innerApi/{page_name}.html"
    html = fetch(html_url)
    if not html:
        return None, None

    # Find all JS chunk references for this page
    # Pattern: assets/{page_name}.html-{hash}.js
    chunks = re.findall(rf'assets/{re.escape(page_name)}\.html-([a-f0-9]+)\.js', html)
    if not chunks:
        print(f"  No chunks found in HTML")
        return None, None

    # Try each chunk - the content chunk has import statements and HTML render
    # The metadata chunk has JSON.parse and page metadata
    for hash_val in chunks:
        js_url = f"{BASE_URL}/assets/{page_name}.html-{hash_val}.js"
        js = fetch(js_url)
        if not js:
            continue

        # Skip metadata chunks (they contain JSON.parse)
        if 'JSON.parse' in js:
            continue

        # Content chunk should have:
        # 1. import statement
        # 2. HTML content (h2/h3 tags) - may be in single quotes, backticks, or double quotes
        if 'import' in js and ('<h2' in js or '<h3' in js or '<h4' in js):
            return js_url, js

    return None, None


def extract_html_content(js_content):
    """Extract HTML from VuePress JS chunk.

    VuePress splits content across multiple string literals:
    - t('<h2>...</h2>...<p>text</p>', 6)  - single-quoted HTML
    - l(`<h2>...</h2>`)  - backtick template literals with HTML

    We extract all HTML strings and concatenate them in order.
    """
    # Extract image variable definitions first
    image_vars = {}
    for m in re.finditer(r'([a-z]+)="(/assets/[^"]+\.(?:png|jpg|gif|svg))"', js_content):
        image_vars[m.group(1)] = m.group(2)

    parts = []

    # Find single-quoted and backtick strings that contain HTML
    # Only extract PURE HTML strings (no JS render patterns)
    for pattern, quote_char in [(r"'((?:[^'\\]|\\.){30,})'", "'"),
                                 (r'`((?:[^`\\]|\\.){30,})`', '`')]:
        for m in re.finditer(pattern, js_content, re.DOTALL):
            raw = m.group(1)
            if quote_char == "'":
                unescaped = raw.replace("\\'", "'").replace('\\"', '"').replace('\\n', '\n').replace('\\\\', '\\')
            else:
                unescaped = raw.replace('\\`', '`').replace('\\n', '\n').replace('\\\\', '\\')

            for var_name, img_path in image_vars.items():
                unescaped = unescaped.replace(f'"+{var_name}+"', img_path)
                if quote_char == '`':
                    unescaped = unescaped.replace(f'${{{var_name}}}', img_path)

            # Must contain HTML tags
            if '<' not in unescaped or '</' not in unescaped:
                continue

            # Skip if it contains JS render patterns
            if re.search(r'\b[a-z]\("(?:span|div|pre)",\s*(?:null|\{)', unescaped):
                continue
            if re.search(r'[a-z]=s\(|[a-z]=l\(', unescaped):
                continue

            parts.append((m.start(), unescaped))

    # Sort by position to maintain document order
    parts.sort(key=lambda x: x[0])

    # Also extract text from Vue render calls (for pages where content is in render calls)
    # But filter out syntax highlighting noise
    text_parts = []
    for m in re.finditer(r'[a-z]\("(?:li|p|td|th|h[2-5])",\s*null,\s*"((?:[^"\\]|\\.){5,})"', js_content):
        text = m.group(1).replace('\\"', '"').replace('\\n', '\n')
        # Skip syntax highlighting / CSS-related text
        if text in ('span', 'div', 'pre', 'code', 'line-number', 'shiki dracula', 'line-numbers'):
            continue
        if text.startswith(('#', '.', 'background', 'color:', 'font-')):
            continue
        text_parts.append((m.start(), f'<p>{text}</p>'))

    # Merge text parts with HTML parts, maintaining order
    all_parts = [(pos, content, 'html') for pos, content in parts] + \
                [(pos, content, 'text') for pos, content in text_parts]
    all_parts.sort(key=lambda x: x[0])

    combined = '\n'.join(content for _, content, _ in all_parts)

    return combined if len(combined) > 100 else None

def html_to_markdown(html_content, title=''):
    """Convert HTML to Markdown."""
    if not html_content:
        return ''

    s = html_content

    # Remove header anchor links
    s = re.sub(r'<a class="header-anchor"[^>]*>[^<]*</a>\s*', '', s)

    # Convert code blocks first (before other processing)
    def convert_code_block(m):
        lang = m.group(1) or ''
        code = m.group(2)
        # Remove HTML tags from code
        code = re.sub(r'<[^>]+>', '', code)
        code = html_module.unescape(code)
        return f'\n```{lang}\n{code}\n```\n'

    s = re.sub(r'<div class="language-(\w+)[^"]*"[^>]*><pre[^>]*><code[^>]*>(.*?)</code></pre>',
               convert_code_block, s, flags=re.DOTALL)

    # Headers
    s = re.sub(r'<h1[^>]*>(.*?)</h1>', r'# \1', s, flags=re.DOTALL)
    s = re.sub(r'<h2[^>]*>(.*?)</h2>', r'## \1', s, flags=re.DOTALL)
    s = re.sub(r'<h3[^>]*>(.*?)</h3>', r'## \1', s, flags=re.DOTALL)
    s = re.sub(r'<h4[^>]*>(.*?)</h4>', r'### \1', s, flags=re.DOTALL)
    s = re.sub(r'<h5[^>]*>(.*?)</h5>', r'#### \1', s, flags=re.DOTALL)

    # Bold/Italic
    s = re.sub(r'<strong>(.*?)</strong>', r'**\1**', s, flags=re.DOTALL)
    s = re.sub(r'<b>(.*?)</b>', r'**\1**', s, flags=re.DOTALL)
    s = re.sub(r'<em>(.*?)</em>', r'*\1*', s, flags=re.DOTALL)

    # Inline code (after code blocks)
    s = re.sub(r'<code[^>]*>(.*?)</code>', r'`\1`', s, flags=re.DOTALL)

    # Links
    s = re.sub(r'<a[^>]*href="([^"]*)"[^>]*>(.*?)</a>', r'[\2](\1)', s, flags=re.DOTALL)

    # Images
    s = re.sub(r'<img[^>]*src="([^"]*)"[^>]*alt="([^"]*)"[^>]*/?\s*>', r'![\2](\1)', s)
    s = re.sub(r'<img[^>]*src="([^"]*)"[^>]*/?\s*>', r'![](\1)', s)

    # Lists
    s = re.sub(r'<li[^>]*>(.*?)</li>', r'- \1\n', s, flags=re.DOTALL)
    s = re.sub(r'</?[uo]l[^>]*>', '\n', s)

    # Tables
    s = re.sub(r'<thead[^>]*>', '', s)
    s = re.sub(r'</thead>', '', s)
    s = re.sub(r'<tbody[^>]*>', '', s)
    s = re.sub(r'</tbody>', '', s)
    s = re.sub(r'<tr[^>]*>', '', s)
    s = re.sub(r'</tr>', '\n', s)

    def convert_cell(m):
        content = m.group(1) if m.group(1) else ''
        content = re.sub(r'<[^>]+>', '', content).strip()
        return f'| {content} '

    s = re.sub(r'<t[hd][^>]*>(.*?)</t[hd]>', convert_cell, s, flags=re.DOTALL)
    s = re.sub(r'</?table[^>]*>', '\n', s)

    # Paragraphs and breaks
    s = re.sub(r'<p[^>]*>(.*?)</p>', r'\1\n\n', s, flags=re.DOTALL)
    s = re.sub(r'<br\s*/?>', '\n', s)
    s = re.sub(r'<hr\s*/?>', '\n---\n', s)

    # Blockquotes
    s = re.sub(r'<blockquote[^>]*>(.*?)</blockquote>',
               lambda m: '\n> ' + re.sub(r'\n', '\n> ', m.group(1).strip()) + '\n',
               s, flags=re.DOTALL)

    # Remove all remaining HTML tags
    s = re.sub(r'<[^>]+>', '', s)

    # Unescape HTML entities
    s = html_module.unescape(s)

    # Clean up whitespace
    s = re.sub(r'[ \t]+', ' ', s)
    s = re.sub(r'\n{3,}', '\n\n', s)
    s = s.strip()

    if title:
        s = f'# {title}\n\n> 来源: {BASE_URL}/innerApi/\n\n{s}'

    return s


def download_page(page_name, title):
    """Download a single page."""
    print(f"[{page_name}] Fetching...", end=' ', flush=True)

    js_url, js_content = get_content_chunk_url(page_name)
    if not js_content:
        print("SKIP (no content)")
        return None

    print(f"chunk OK", end=' ', flush=True)

    raw_html = extract_html_content(js_content)
    if not raw_html:
        print("SKIP (no HTML)")
        return None

    markdown = html_to_markdown(raw_html, title)

    output_file = os.path.join(OUTPUT_DIR, f'{page_name}.md')
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(markdown)

    # Also save raw HTML for debugging
    html_file = os.path.join(OUTPUT_DIR, f'{page_name}.html')
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(raw_html)

    print(f"-> {len(markdown)} chars")
    return output_file


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print("=" * 60)
    print("QMT Official Documentation Downloader")
    print(f"Output: {OUTPUT_DIR}")
    print("=" * 60)
    print()

    # Create index file
    index_lines = ['# QMT 内置 Python API 文档\n']
    index_lines.append(f'> 来源: {BASE_URL}/innerApi/\n')
    index_lines.append('## 目录\n')

    success = 0
    for page_name, title in PAGES:
        result = download_page(page_name, title)
        if result:
            index_lines.append(f'- [{title}]({page_name}.md)')
            success += 1

    # Write index
    index_file = os.path.join(OUTPUT_DIR, 'README.md')
    with open(index_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(index_lines))

    print()
    print("=" * 60)
    print(f"Done! {success}/{len(PAGES)} pages saved to {OUTPUT_DIR}")
    print(f"Index: {index_file}")


if __name__ == '__main__':
    main()
