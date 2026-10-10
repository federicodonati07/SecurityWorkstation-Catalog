# Security Workstation — Catalog

The signed catalog of installable tools for the **Security Workstation** macOS app. The app ships with a copy and
checks this repository for newer versions; new tools show up in its *Store* as **NEW** (never installed automatically).

```
catalog.json        the catalog (edit this)
catalog.json.sig    Ed25519 signature of the exact bytes of catalog.json (generated)
catalog.pub.b64     public key, raw 32 bytes base64 (embedded in the app)
catalog.pub.pem     the same key as PEM, for OpenSSL / CI
schema/             JSON Schema documenting every field
tools/              validate.py · release.py · import_from_homebrew.py · keytool.swift · verify.sh
```

## Add or change a tool
1. Generate an entry from real metadata (Homebrew / PyPI):
   `tools/import_from_homebrew.py formula ffuf` · `… cask zap` · `… pipx impacket`
2. Paste it into `catalog.json` → `packages`, set `category` (an id from `categories`), optionally `"default": true`
   (preselected on first run). `number` and `symbol` (the periodic-table cell) are assigned automatically for new entries.
3. Release: `tools/release.py` — validates, assigns numbers/symbols, bumps `catalog_version`, signs, verifies.
4. `git add -A && git commit -m "catalog vN" && git push`. Installed apps pick it up on their next check (at launch and at
   most hourly while open).

pipx tools that are not on PyPI can set `source.spec` to `git+https://github.com/<owner>/<repo>[@ref]` (GitHub only).

## Trust model
* HTTPS alone is not trusted. The app verifies `catalog.json.sig` against the public key compiled into the app and
  **rejects the catalog on any failure**, keeping the last good one.
* `catalog_version` must never go backwards (rollback protection). Every identifier is validated again by the app
  (`^[A-Za-z0-9][A-Za-z0-9._+@-]*$`); only Homebrew formulae/casks and pipx are allowed. No scripts, no URLs except the
  GitHub pipx spec above.
* The **private key** is at `~/.config/security-workstation/catalog-signing.key` on the maintainer's Mac (mode 600), never in
  this repository. Back it up. If it is lost or leaked, ship a new app build with a new public key; old apps then
  keep their last good catalog until updated.
* CI (`.github/workflows/validate.yml`) validates the structure and checks that the committed signature matches the
  committed public key, so an unsigned or hand-edited catalog fails the build.

## Pull requests
Contributions are welcome as PRs to `catalog.json`; the maintainer reviews the package, runs `tools/release.py` and pushes
the signed result.
