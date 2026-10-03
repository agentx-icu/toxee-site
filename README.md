# toxee-site

Official website for [toxee](https://github.com/agentx-icu/toxee), served at
**https://toxee.agentx.icu**.

A static site (no third-party fonts or trackers) in English and 简体中文:

| URL | Language |
| --- | --- |
| `/` | follows the visitor's browser language, with an EN / 中文 toggle |
| `/en/` | English |
| `/zh/` | 简体中文 |

## Layout

| Path | What |
| --- | --- |
| `index.html` | The single source page. Every text node exists in both languages as `<span class="en">` / `<span class="zh">`; `html[data-lang]` picks one. |
| `en/index.html`, `zh/index.html` | **Generated** language-pinned copies. Never edit by hand; run `python3 tools/build_lang_pages.py` after every change to `index.html`. |
| `tools/build_lang_pages.py` | The generator for the two pages above. |
| `assets/css/site.css` | Styles. |
| `assets/js/site.js` | Language toggle, tabs, OS detection, and the download list. |
| `assets/img/{en,zh}/` | App screenshots per language (copied from `toxee/doc/product/assets`). |
| `CNAME`, `.nojekyll` | GitHub Pages custom domain and raw static serving. |

## Downloads

`site.js` asks the GitHub API for the latest toxee release and fills in the
package links, sizes and SHA-256 digests. If the API is unreachable (rate
limits, blocked network), the page uses the `FALLBACK` block at the top of
`site.js` and the static links in `index.html`. **After each toxee release,
update `FALLBACK` and the hard-coded `0.3.1` links in `index.html`, then regenerate `en/` and `zh/`** so visitors
without API access still get the newest packages.

Package names are expected to follow `toxee-<version>-<Platform>-<arch>.<ext>`,
matching the release workflow.

## Preview locally

```bash
python3 -m http.server 8000
# open http://127.0.0.1:8000/, /en/ or /zh/
```

## Deploy

GitHub Pages → *Deploy from a branch* → `master` / root. Point a DNS `CNAME`
record for `toxee.agentx.icu` to `agentx-icu.github.io`, then enable *Enforce
HTTPS*.
