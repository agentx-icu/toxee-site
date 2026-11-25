# Website validation — 2026-11-25

The site now presents toxee as an experimental cross-platform Tox client, uses captured application screens instead of the concept hero, and explains platform, online and mobile background limits before package selection. The screenshot conversations are demonstration data, not proof of public-network or device acceptance.

- Baseline and final `python3 tools/check_site.py` passed.
- Regenerated `en/index.html` and `zh/index.html` with `python3 tools/build_lang_pages.py`; non-release search/social metadata follows the same positioning.
- `node --check assets/js/site.js` passed; no runtime JavaScript feature was added for these static content changes.
- Headless Chrome (via Playwright) visited both languages at 1280, 390 and 320 px, in light/dark and reduced-motion mode, with GitHub API requests blocked. All 12 combinations loaded the captured localized hero, experimental notice and four-platform scope, without page overflow or JavaScript errors. A thirteenth 390 px Chinese run with JavaScript disabled retained the localized screenshot and delivery disclosure.
- Reviewed desktop/phone screenshots. On narrow screens the platform table displays each platform vertically so the call/background limits remain visible without horizontal scrolling.
- Rendered both 1200×630 social-preview JPEGs from `tools/og.html`, using the captured desktop conversation.
- Local browser evidence: `/tmp/toxee-site-qa-20261125/results.json` and screenshots. These temporary files are not deployed or tracked.

No app transport/lifecycle code changed in the website repository. Real Android/iPhone/headset operation, actual installed-package upgrades, formal publisher signatures and public-network reliability need the application acceptance evidence; static-site and browser checks do not establish them.
