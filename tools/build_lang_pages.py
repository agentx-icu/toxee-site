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
        "title": "toxee — Serverless, private, peer-to-peer chat",
        "description": None,  # keep the English description from index.html
    },
    "zh": {
        "html_lang": "zh-Hans",
        "title": "toxee — 无服务器、真隐私的点对点聊天",
        "og_title": "toxee — 无服务器。真隐私。属于你。",
        "og_description": "Tox 点对点网络的现代聊天客户端。没有服务器、无需手机号，端到端加密。",
        "description": "toxee 是基于 Tox 点对点网络的免费开源聊天应用。没有服务器、无需手机号，消息、文件、群聊与通话全程端到端加密，支持 Windows、macOS、Linux、Android 与 iOS。",
        "ld_description": "基于 Tox 点对点网络的免费开源聊天应用。没有服务器、无需手机号，消息、文件、群聊与通话全程端到端加密。",
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
        "<title>toxee — Serverless, private, peer-to-peer chat</title>",
        f"<title>{cfg['title']}</title>",
    )
    if cfg["description"]:
        head, rest = out.split('<meta name="description" content="', 1)
        _, rest = rest.split('">', 1)
        out = f'{head}<meta name="description" content="{cfg["description"]}">{rest}'
    if cfg.get("og_title"):
        out = replace_once(out, '<meta property="og:title" content="toxee — Serverless. Private. Yours.">',
                           f'<meta property="og:title" content="{cfg["og_title"]}">')
        out = replace_once(out, '<meta property="og:description" content="A modern chat client for the Tox P2P network. No servers, no phone numbers, end-to-end encrypted.">',
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
