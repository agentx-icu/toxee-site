#!/usr/bin/env python3
"""Check the checked-in release fallback against the latest GitHub release.

index.html carries hard-coded download links, file names, sizes and dates, and
the FALLBACK block in assets/js/site.js carries sizes and SHA-256 sums, so the
page works when the GitHub API is unreachable. This script fails (exit 1) when
any of them no longer matches the latest stable toxee release, so a forgotten
update after a release is caught by CI instead of by visitors.

Usage: python3 tools/check_release.py   (set GITHUB_TOKEN to avoid rate limits)
"""
import json
import os
import re
import sys
import urllib.request
from pathlib import Path

REPO = 'agentx-icu/toxee'
ROOT = Path(__file__).resolve().parent.parent


def fmt_size(n):
    # Same rounding as the size formatter in assets/js/site.js.
    return f'{n / 1048576:.1f} MB' if n >= 1048576 else f'{max(1, round(n / 1024))} KB'


def latest_release():
    req = urllib.request.Request(f'https://api.github.com/repos/{REPO}/releases/latest',
                                 headers={'Accept': 'application/vnd.github+json'})
    token = os.environ.get('GITHUB_TOKEN')
    if token:
        req.add_header('Authorization', f'Bearer {token}')
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def main():
    src = (ROOT / 'index.html').read_text(encoding='utf-8')
    js = (ROOT / 'assets' / 'js' / 'site.js').read_text(encoding='utf-8')
    rel = latest_release()
    tag = rel['tag_name']
    version = tag.lstrip('v')
    date = rel['published_at'][:10]
    assets = {a['name']: a for a in rel['assets']}
    errors = []

    for v in set(re.findall(r'<(?:span|b)[^>]* data-version>([^<]+)<', src)):
        if v != tag:
            errors.append(f'index.html: version {v}, latest release is {tag}')
    for d in set(re.findall(r'<span data-release-date>([^<]+)<', src)):
        if d != date:
            errors.append(f'index.html: release date {d}, {tag} was published {date}')
    m = re.search(r'"softwareVersion": "([^"]+)"', src)
    if not m or m.group(1) != version:
        errors.append(f'index.html: JSON-LD softwareVersion {m and m.group(1)}, latest release is {tag}')

    for url in sorted(set(re.findall(r'https://github\.com/' + re.escape(REPO) + r'/releases/(?:download|tag)/[^"]+', src))):
        m = re.match(r'.*/releases/(download|tag)/([^/]+)(?:/(.+))?$', url)
        if m.group(2) != tag:
            errors.append(f'index.html: link points at {m.group(2)}: {url}')
        elif m.group(1) == 'download' and m.group(3) not in assets:
            errors.append(f'index.html: {tag} has no asset {m.group(3)}')

    # Each package row: file name and size must match the release asset.
    for key, body in re.findall(r'<a class="pkg" data-pkg="([^"]+)"[^>]*>(.*?)</a>', src, re.S):
        name = f'toxee-{version}-{key}'
        if name not in assets:
            errors.append(f'index.html: {tag} has no asset {name}')
            continue
        pf = re.search(r'<span class="pf">([^<]+)<', body)
        ps = re.search(r'<span class="ps">([^<]+)<', body)
        if not pf or pf.group(1) != name:
            errors.append(f'index.html {key}: file name {pf and pf.group(1)}, release has {name}')
        if not ps or ps.group(1) != fmt_size(assets[name]['size']):
            errors.append(f'index.html {key}: size {ps and ps.group(1)}, release has {fmt_size(assets[name]["size"])}')

    for name in re.findall(r'<span data-file="[^"]+">([^<]+)<', src):
        if name not in assets:
            errors.append(f'index.html: install command names {name}, not an asset of {tag}')

    # The FALLBACK block in site.js mirrors the packages of the release.
    fb = re.search(r'var FALLBACK = \{(.*?)\n  \};', js, re.S)
    if not fb:
        errors.append('assets/js/site.js: no FALLBACK block')
    else:
        body = fb.group(1)
        for key, want in (('version', version), ('tag', tag), ('date', date)):
            m = re.search(key + r': "([^"]*)"', body)
            if not m or m.group(1) != want:
                errors.append(f'site.js FALLBACK {key}: {m and m.group(1)}, release has {want}')
        rows = {f'toxee-{version}-{k}': (int(s), h)
                for k, s, h in re.findall(r'"([^"]+)": \[(\d+), "([0-9a-f]*)"\]', body)}
        packages = {n for n in assets if n.startswith(f'toxee-{version}-')}
        for n in sorted(set(rows) | packages):
            if n not in rows:
                errors.append(f'site.js FALLBACK is missing {n}')
            elif n not in assets:
                errors.append(f'site.js FALLBACK lists {n}, which {tag} does not have')
            else:
                digest = assets[n].get('digest') or ''
                want = (assets[n]['size'], digest.split(':', 1)[1] if digest.startswith('sha256:') else '')
                if rows[n] != want:
                    errors.append(f'site.js FALLBACK {n}: {rows[n]}, release has {want}')

    if errors:
        print(f'Checked-in release info is out of date with {REPO} {tag}:')
        for e in errors:
            print('  - ' + e)
        print('Update index.html and the FALLBACK block as described in README "Downloads".')
        return 1
    print(f'Checked-in release info matches {REPO} {tag} ({len(assets)} assets).')
    return 0


if __name__ == '__main__':
    sys.exit(main())
