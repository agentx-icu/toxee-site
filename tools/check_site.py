#!/usr/bin/env python3
"""Static checks for the site: links, translations and structured data.

Fails (exit 1) when index.html or 404.html reference a local file or
``#anchor`` that does not exist, when an English string has no Chinese
counterpart (or the reverse), when a screenshot named by ``data-shot`` is
missing for one language, when a ``data-alt-*`` / ``data-aria-*`` pair is
incomplete, when the JSON-LD block is not valid JSON, or when sitemap.xml
does not list exactly ``/``, ``/en/`` and ``/zh/``.

Usage: python3 tools/check_site.py
"""
import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = 'https://toxee.agentx.icu/'
PAGES = ('index.html', '404.html')
LANGS = ('en', 'zh')


class Page(HTMLParser):
    def __init__(self):
        super().__init__()
        self.refs, self.ids, self.anchors = [], set(), []
        self.langs = []      # one entry per element carrying class en / zh
        self.shots = []      # data-shot values
        self.unpaired = []   # data-alt-* / data-aria-* with only one language

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if 'id' in a:
            self.ids.add(a['id'])
        for key in ('href', 'src'):
            v = a.get(key)
            if not v:
                continue
            if v.startswith('#'):
                self.anchors.append(v[1:])
            elif not re.match(r'[a-z][a-z0-9+.-]*:|//', v, re.I):
                self.refs.append(v)
        cls = a.get('class', '').split()
        for lang in LANGS:
            if lang in cls:
                self.langs.append(lang)
        if 'data-shot' in a:
            self.shots.append(a['data-shot'])
        for prefix in ('data-alt-', 'data-aria-'):
            present = [lang for lang in LANGS if prefix + lang in a]
            if present and len(present) != len(LANGS):
                self.unpaired.append(f'{prefix}{present[0]}="{a[prefix + present[0]]}"')


def exists(ref):
    """True when a local href/src (query and fragment stripped) resolves to a file."""
    path = ref.split('#')[0].split('?')[0]
    if path in ('', '.', './'):
        return True
    target = ROOT / path.lstrip('/')
    if path.endswith('/') or target.is_dir():
        target = target / 'index.html'
    return target.is_file()


def check(name, errors):
    src = (ROOT / name).read_text(encoding='utf-8')
    page = Page()
    page.feed(src)
    # Absolute URLs into this site (og:image, JSON-LD, 404 links) must exist too.
    page.refs += ['/' + p for p in re.findall(re.escape(SITE) + r'([^"\s<)]*)', src)]
    for ref in page.refs:
        if not exists(ref):
            errors.append(f'{name}: missing file {ref}')
    for anchor in page.anchors:
        if anchor and anchor not in page.ids:
            errors.append(f'{name}: no element with id "{anchor}"')
    en = page.langs.count('en')
    zh = page.langs.count('zh')
    if en != zh:
        errors.append(f'{name}: {en} English elements but {zh} Chinese elements')
    for shot in sorted(set(page.shots)):
        for lang in LANGS:
            if not (ROOT / 'assets' / 'img' / lang / shot).is_file():
                errors.append(f'{name}: data-shot {shot} has no assets/img/{lang}/ image')
    for attr in page.unpaired:
        errors.append(f'{name}: {attr} has no counterpart in the other language')
    return src


def check_sitemap(errors):
    path = ROOT / 'sitemap.xml'
    if not path.is_file():
        errors.append('sitemap.xml: missing')
        return
    locs = set(re.findall(r'<loc>([^<]+)</loc>', path.read_text(encoding='utf-8')))
    want = {SITE, SITE + 'en/', SITE + 'zh/'}
    if locs != want:
        errors.append(f'sitemap.xml: lists {sorted(locs)}, expected {sorted(want)}')
    robots = ROOT / 'robots.txt'
    if not robots.is_file() or f'Sitemap: {SITE}sitemap.xml' not in robots.read_text(encoding='utf-8'):
        errors.append(f'robots.txt: must point at {SITE}sitemap.xml')


def main():
    errors = []
    src = check('index.html', errors)
    check('404.html', errors)
    check_sitemap(errors)

    m = re.search(r'<script type="application/ld\+json">(.*?)</script>', src, re.S)
    if m is None:
        errors.append('index.html: no JSON-LD block')
    else:
        try:
            json.loads(m.group(1))
        except ValueError as e:
            errors.append(f'index.html: JSON-LD is not valid JSON: {e}')

    if errors:
        print('Site check failed:')
        for e in errors:
            print('  - ' + e)
        return 1
    print('Site check passed.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
