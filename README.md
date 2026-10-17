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
| `tools/build_lang_pages.py` | The generator for the two pages above; it also localizes `og:image` and the `SoftwareApplication` JSON-LD block. |
| `tools/check_site.py` | Fails when `index.html` or `404.html` reference a missing local file or `#anchor`, when an English string has no Chinese counterpart, when a screenshot is missing for one language, when the JSON-LD is invalid, or when `sitemap.xml` does not list `/`, `/en/` and `/zh/`. |
| `tools/check_release.py` | Fails when the checked-in release info (links, file names, sizes and dates in `index.html`, the `FALLBACK` block in `site.js`, the JSON-LD `softwareVersion`) no longer matches the latest release. |
| `tools/og.html` | Template for the 1200×630 social preview images `assets/img/{en,zh}/og.jpg`. |
| `404.html` | Bilingual not-found page with absolute links (GitHub Pages serves it for any missing path). |
| `assets/css/site.css` | Styles. Dark by default, light when the system asks for it (`prefers-color-scheme`); colours that differ between the two are tokens on `:root`, and the app-UI illustrations and terminals keep the dark look in both. |
| `assets/js/site.js` | Language toggle, the phone menu, the full-size screenshot viewer, tabs, OS detection, and the download list. |
| `assets/img/{en,zh}/` | App screenshots per language, from `toxee/doc/product/assets`, converted to WebP (`cwebp -q 82 -m 6 in.png -o out.webp`). Keep the `width` / `height` attributes in `index.html` equal to the image size. |
| `CNAME`, `.nojekyll` | GitHub Pages custom domain and raw static serving. |
| `sitemap.xml`, `robots.txt` | Search-engine sitemap (`/`, `/en/`, `/zh/` with hreflang alternates) and the robots file pointing at it. Update both if pages are added. |
| `.github/workflows/pages.yml` | Deploys the repository root with GitHub Pages on every push to `master`. |
| `.github/workflows/check.yml` | On pushes, pull requests and daily: fails if `en/` / `zh/` were not regenerated, if `tools/check_site.py` finds a broken link or translation, or if `tools/check_release.py` finds stale release info. |

## Downloads

`site.js` asks the GitHub API for the latest toxee release and fills in the
package links, sizes and SHA-256 digests. If the API is unreachable (rate
limits, blocked network), the page uses the `FALLBACK` block at the top of
`site.js` and the static links in `index.html`. **After each toxee release,
update `FALLBACK` and the hard-coded `0.3.1` links in `index.html`, and the JSON-LD `softwareVersion`, then regenerate `en/` and `zh/`** so visitors
without API access still get the newest packages. `python3 tools/check_release.py`
lists anything still out of date; the `check` workflow runs it every day.

Package names are expected to follow `toxee-<version>-<Platform>-<arch>.<ext>`,
matching the release workflow.

## Preview locally

```bash
python3 -m http.server 8000
# open http://127.0.0.1:8000/, /en/ or /zh/
```

## Social preview

`og:image` is `assets/img/{en,zh}/og.jpg` (1200×630), a screenshot of
`tools/og.html?lang=en` / `?lang=zh` at that viewport (for example with
Playwright: `page.setViewportSize({ width: 1200, height: 630 })`, open the file,
`page.screenshot({ type: 'jpeg', quality: 86 })`). Re-render it after changing the
template or `quiet-modern.webp`.

## Deploy

GitHub Pages → Source: **GitHub Actions** (`.github/workflows/pages.yml` uploads
the repository root). Point a DNS `CNAME` record for `toxee.agentx.icu` to
`agentx-icu.github.io`, then enable *Enforce HTTPS*.
