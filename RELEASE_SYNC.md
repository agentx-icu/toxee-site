# Release inventory and website synchronization

The checked-in `release-manifest.json` is the input for stable download fallbacks. It contains the application repository, exact tag/publication date, asset names and URLs, sizes, SHA-256 values, platform and signing-evidence status. The application release workflow attaches the same inventory to its release. Old releases without an inventory are bootstrapped from GitHub REST metadata.

Checksums identify exact bytes. `not_verified` does not assert a trusted signature; `unsigned` is used only for an explicitly unsigned asset name. Production distribution and upgrade evidence remain the release owner's responsibility.

## Update a website

Run `python3 tools/release_manifest.py sync` to fetch the newest published stable release. It verifies a published application inventory against the actual release metadata, resolves every required package, and prepares all source updates before writing. Missing/ambiguous packages or missing package hashes fail without partially updating the source. Drafts and prereleases cannot replace stable website downloads.

Then regenerate the language pages:

```sh
python3 tools/build_lang_pages.py
python3 tools/release_manifest.py check --input release-manifest.json
python3 -m unittest discover -s tools -p 'test_release*.py'
```

The offline check verifies the checked-in source and fallback against the manifest without contacting GitHub. Existing weekly release checks still compare the public website source with GitHub. Runtime API access remains optional for visitors; the generated HTML/JavaScript fallback stays usable without it.

For a saved, validated inventory, use `sync --input /absolute/path/release-manifest.json`. The synchronizer updates release labels/date, asset URLs/names/sizes, install commands, checksum lists, JSON-LD where present, and the JavaScript fallback. Historic screenshot captions are deliberately not rewritten as though the images came from a newer build.

## Automatic preparation

`.github/workflows/release-sync.yml` runs weekly and on manual dispatch, synchronizes the published application release, regenerates/checks the site, and opens or updates one `automation/release-vX.Y.Z` PR. Existing bot branches are reused without force-pushes; missing PR creation and check dispatch are retried after partial API failures. It requires repository Actions permissions to create branches and PRs; if organization policy disables PR creation, the run reports that failure and the generated update can be prepared with the command above. Merging remains an explicit repository action.

The application `.github/workflows/release-manifest.yml` refreshes inventories after publication/editing, or on manual dispatch for an existing release tag. Its normal package workflow also attaches an inventory after producing a draft/public release, so publication with the Actions token does not depend on triggering a second workflow.

## Maintaining the shared tool

`tools/release_manifest.py` and its behavior tests are tracked copies shared with the three application and three site repositories. Their only repository-specific setting is `DEFAULT_REPOSITORY`. Apply fixes to all six copies and run the common tests when changing the schema or transformation rules. No private tokens or signer keys belong in the manifest.
