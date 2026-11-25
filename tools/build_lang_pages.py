#!/usr/bin/env python3
"""Generate the language-pinned pages en/index.html and zh/index.html.

index.html is the single source: it carries both languages and auto-detects
one at the site root. The pages under /en/ and /zh/ are the same page pinned
to one language, so each language has its own shareable, indexable URL.
Re-run after every edit to index.html:  python3 tools/build_lang_pages.py
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = "https://toxee.agentx.icu/"

LANGS = {
    "en": {
        "html_lang": "en",
        "title": "toxee — Experimental cross-platform Tox chat",
        "description": None,  # keep the English description from index.html
    },
    "zh": {
        "html_lang": "zh-Hans",
        "title": "toxee — 实验性的跨平台 Tox 聊天",
        "og_title": "toxee — 手机与桌面上的实验性 Tox 聊天",
        "og_description": "实验性的跨平台 Tox 客户端。本地身份、加密会话与清楚的平台范围。",
        "description": "toxee 是手机与桌面上的实验性开源 Tox 客户端。消息、文件与一对一通话端到端加密，双方需要同时运行且网络可达。",
        "ld_description": "实验性的开源 Tox 点对点客户端，本地身份、加密消息、文件与一对一通话。",
    },
}


def replace_once(text, old, new):
    if text.count(old) != 1:
        raise SystemExit(f"expected exactly one occurrence of: {old[:70]!r}")
    return text.replace(old, new)


def build(src, lang, cfg):
    out = src
    out = replace_once(
        out,
        '<html lang="en" data-lang="en">',
        f'<html lang="{cfg["html_lang"]}" data-lang="{lang}" data-page-lang="{lang}" data-base="../">',
    )
    out = replace_once(
        out,
        "<title>toxee — Experimental cross-platform Tox chat</title>",
        f"<title>{cfg['title']}</title>",
    )
    if cfg["description"]:
        head, rest = out.split('<meta name="description" content="', 1)
        _, rest = rest.split('">', 1)
        out = f'{head}<meta name="description" content="{cfg["description"]}">{rest}'
    if cfg.get("og_title"):
        out = replace_once(out, '<meta property="og:title" content="toxee — Experimental Tox chat for phone and desktop">',
                           f'<meta property="og:title" content="{cfg["og_title"]}">')
        out = replace_once(out, '<meta property="og:description" content="An experimental cross-platform Tox client. Local identities, encrypted conversations, and clear platform limits.">',
                           f'<meta property="og:description" content="{cfg["og_description"]}">')
        out = out.replace('<meta property="og:type" content="website">', '<meta property="og:type" content="website">\n<meta property="og:locale" content="zh_CN">')
    out = replace_once(
        out,
        f'<link rel="canonical" href="{SITE}">',
        f'<link rel="canonical" href="{SITE}{lang}/">',
    )
    out = replace_once(out, f'<meta property="og:url" content="{SITE}">', f'<meta property="og:url" content="{SITE}{lang}/">')
    out = replace_once(out, f'content="{SITE}assets/img/en/og.jpg"', f'content="{SITE}assets/img/{lang}/og.jpg"')
    # Structured data: this page's URL, language and screenshot.
    out = replace_once(out, f'"url": "{SITE}"', f'"url": "{SITE}{lang}/"')
    out = replace_once(out, '"inLanguage": "en"', f'"inLanguage": "{cfg["html_lang"]}"')
    out = replace_once(out, f'"screenshot": "{SITE}assets/img/en/og.jpg"', f'"screenshot": "{SITE}assets/img/{lang}/og.jpg"')
    if cfg.get("ld_description"):
        out = re.sub(r'("description": ")[^"]*(")', lambda m: m[1] + cfg["ld_description"] + m[2], out, count=1)
    # Relative URLs move one directory down.
    for attr in ("href", "src"):
        out = out.replace(f'{attr}="assets/', f'{attr}="../assets/')
    out = out.replace('href="en/"', 'href="../en/"').replace('href="zh/"', 'href="../zh/"')
    # Ship the right screenshots in the HTML itself so there is no swap after load.
    out = out.replace('src="../assets/img/en/', f'src="../assets/img/{lang}/')
    banner = "<!-- Generated from ../index.html by tools/build_lang_pages.py. Do not edit. -->\n"
    return replace_once(out, "<!DOCTYPE html>\n", "<!DOCTYPE html>\n" + banner)


def main():
    src = (ROOT / "index.html").read_bytes().decode("utf-8")
    for lang, cfg in LANGS.items():
        dest = ROOT / lang / "index.html"
        dest.parent.mkdir(exist_ok=True)
        dest.write_bytes(build(src, lang, cfg).encode("utf-8"))
        print(f"wrote {dest.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
