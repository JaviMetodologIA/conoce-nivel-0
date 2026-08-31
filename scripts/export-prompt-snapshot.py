#!/usr/bin/env python3
"""Deterministic snapshot exporter for prompt texts rendered in dist/.

Reads the 12 prompts/workbook pages (3 locales x 2 audiences x 2 surfaces),
extracts the template and demo copy of every prompt level from the
textarea[data-prompt-source] inside each details[data-prompt-level] block,
and writes snapshots/baseline/prompt-snapshot-{locale}.json.

Stdlib only. No timestamps, no filesystem-order dependence.
"""
import hashlib
import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DIST = ROOT / 'dist'
OUT_DIR = ROOT / 'snapshots'

LOCALES = ('es', 'en', 'pt')
AUDIENCES = ('persona', 'empresa')
PAGES = ('prompts', 'workbook')
LEVEL_NAMES = {'1': 'natural', '2': 'parameters', '3': 'spec', '4': 'pair'}

# expected intents per page surface (per locale x audience)
EXPECTED_LIBRARY = ['%02d' % n for n in range(1, 11)] + ['M1', 'M2', 'M3', 'M4']
EXPECTED_WORKBOOK = ['W%02d' % n for n in range(1, 11)]
EXPECTED_BRAIN = ['B1', 'B2', 'B3']


def page_path(locale, audience, page):
    parts = [DIST]
    if locale != 'es':
        parts.append(locale)
    if audience == 'empresa':
        parts.append('empresa')
    parts.append(page)
    return Path(*parts) / 'index.html'


def classify(library_id, locale):
    """Map data-prompt-library id -> (surface, intent_id)."""
    m = re.fullmatch(r'library-%s-(\d{2})' % locale, library_id)
    if m:
        return 'library', m.group(1)
    m = re.fullmatch(r'library-%s-m(\d)' % locale, library_id)
    if m:
        return 'library', 'M' + m.group(1)
    m = re.fullmatch(r'p(\d+)-%s' % locale, library_id)
    if m:
        return 'workbook', 'W%02d' % int(m.group(1))
    m = re.fullmatch(r'brain-prompt-%s-(\d)' % locale, library_id)
    if m:
        return 'workbook_brain', 'B' + m.group(1)
    raise SystemExit(f'UNRECOGNIZED_PROMPT_LIBRARY_ID:{library_id}:{locale}')


class PromptExtractor(HTMLParser):
    """Collects (library_id, level, source_text) triples from a page."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.html_lang = None
        self.html_audience = None
        self.library_id = None
        self.level = None
        self.in_source = False
        self.chunks = []
        self.mode = None
        self.results = []  # (library_id, level, mode, text)

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'html':
            self.html_lang = a.get('lang')
            self.html_audience = a.get('data-audience')
        if 'data-prompt-library' in a:
            self.library_id = a['data-prompt-library']
        if tag == 'details' and 'data-prompt-level' in a:
            self.level = a['data-prompt-level']
        if tag == 'textarea' and 'data-prompt-source' in a:
            if self.library_id is None or self.level is None:
                raise SystemExit('PROMPT_SOURCE_OUTSIDE_CONTEXT')
            self.in_source = True
            self.mode = a.get('data-prompt-mode')
            if self.mode not in ('template', 'demo'):
                raise SystemExit('PROMPT_SOURCE_MODE_MISSING')
            self.chunks = []

    def handle_endtag(self, tag):
        if tag == 'textarea' and self.in_source:
            self.in_source = False
            self.results.append((self.library_id, self.level, self.mode, ''.join(self.chunks)))

    def handle_data(self, data):
        if self.in_source:
            self.chunks.append(data)


def canonical_self(value, field='self_sha256'):
    # same model as scripts/build.py canonical_self
    payload = {key: item for key, item in value.items() if key != field}
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(',', ':')) + '\n'
    return hashlib.sha256(raw.encode('utf-8')).hexdigest()


def export():
    snapshots = {locale: {} for locale in LOCALES}
    for locale in LOCALES:
        for audience in AUDIENCES:
            for page in PAGES:
                path = page_path(locale, audience, page)
                if not path.is_file():
                    raise SystemExit(f'DIST_PAGE_MISSING:{path} (run: python3 scripts/build.py)')
                parser = PromptExtractor()
                parser.feed(path.read_text(encoding='utf-8'))
                if parser.html_lang != locale or parser.html_audience != audience:
                    raise SystemExit(f'PAGE_IDENTITY_MISMATCH:{path}:{parser.html_lang}:{parser.html_audience}')
                expected = set(EXPECTED_LIBRARY) if page == 'prompts' else set(EXPECTED_WORKBOOK + EXPECTED_BRAIN)
                seen = set()
                for library_id, level, mode, text in parser.results:
                    surface, intent = classify(library_id, locale)
                    level_name = LEVEL_NAMES[level]
                    key = f'{surface}/{intent}/{locale}/{audience}/{mode}/{level_name}'
                    if key in snapshots[locale]:
                        raise SystemExit(f'DUPLICATE_SNAPSHOT_KEY:{key}')
                    snapshots[locale][key] = {
                        'chars': len(text),
                        'sha256': hashlib.sha256(text.encode('utf-8')).hexdigest(),
                        'text': text,
                    }
                    seen.add(intent)
                if seen != expected:
                    raise SystemExit(f'INTENT_SET_MISMATCH:{path}:missing={sorted(expected - seen)}:extra={sorted(seen - expected)}')

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    total = 0
    for locale in LOCALES:
        entries = snapshots[locale]
        if len(entries) != 432:
            raise SystemExit(f'ENTRY_COUNT_MISMATCH:{locale}:{len(entries)}')
        total += len(entries)
        document = dict(sorted(entries.items()))
        document['self_sha256'] = canonical_self(document)
        out = OUT_DIR / f'prompt-snapshot-{locale}.json'
        out.write_text(json.dumps(document, ensure_ascii=False, sort_keys=True, indent=2) + '\n', encoding='utf-8')
        print(f'{out.relative_to(ROOT)}: {len(entries)} entries self_sha256={document["self_sha256"]}')
    print(f'TOTAL: {total} entries')
    return 0


if __name__ == '__main__':
    sys.exit(export())
