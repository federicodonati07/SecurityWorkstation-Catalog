#!/usr/bin/env python3
"""Prepare and sign a catalog release.

  tools/release.py                # assign number/symbol to new entries, bump version, validate, sign, verify
  tools/release.py --no-bump      # re-sign without changing the version

The private key is read from $CATALOG_SIGNING_KEY (default ~/.config/security-workstation/catalog-signing.key)
and never stored in the repository.
"""
import datetime, json, os, re, subprocess, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import validate as V

ROOT = Path(__file__).resolve().parent.parent
CATALOG, SIG = ROOT / "catalog.json", ROOT / "catalog.json.sig"
KEY = Path(os.environ.get("CATALOG_SIGNING_KEY", Path.home() / ".config/security-workstation/catalog-signing.key"))


def unique_symbol(name, used):
    letters = [c for c in name if c.isalpha()]
    cands = []
    if len(letters) >= 2:
        cands += [letters[0].upper() + letters[j].lower() for j in range(1, len(letters))]
        cands += [letters[0].upper() + letters[j].lower() + letters[k].lower() for j in range(1, len(letters)) for k in range(j + 1, len(letters))]
    for c in cands:
        if c not in used: return c
    i = 2
    while f"{(letters[0] if letters else 'x').upper()}{i}" in used: i += 1
    return f"{(letters[0] if letters else 'x').upper()}{i}"


def main():
    doc = json.loads(CATALOG.read_text(encoding="utf-8"))
    pk = doc["packages"]
    used_sym = {p["symbol"] for p in pk if "symbol" in p}
    nxt = max([p.get("number", 0) for p in pk] + [0]) + 1
    for p in pk:
        if "number" not in p: p["number"] = nxt; nxt += 1
        if "symbol" not in p: p["symbol"] = unique_symbol(p["name"], used_sym); used_sym.add(p["symbol"])
    if "--no-bump" not in sys.argv: doc["catalog_version"] += 1
    doc["generated_at"] = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    errors = V.validate(doc)
    if errors: sys.exit("\n".join("ERROR " + e for e in errors))
    CATALOG.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    if not KEY.exists(): sys.exit(f"signing key not found: {KEY}")
    sig = subprocess.run(["swift", str(ROOT / "tools/keytool.swift"), "sign", str(KEY), str(CATALOG)], capture_output=True, text=True)
    if sig.returncode: sys.exit(sig.stderr)
    SIG.write_text(sig.stdout.strip() + "\n")
    ver = subprocess.run(["swift", str(ROOT / "tools/keytool.swift"), "verify", str(ROOT / "catalog.pub.b64"), str(CATALOG), str(SIG)], capture_output=True, text=True)
    if ver.returncode: sys.exit(ver.stderr)
    print(f"released catalog_version {doc['catalog_version']} with {len(pk)} packages — {ver.stdout.strip()}")
    print("Next: git add -A && git commit -m 'catalog vN' && git push")


if __name__ == "__main__":
    main()
