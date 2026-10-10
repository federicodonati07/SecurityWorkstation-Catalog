#!/usr/bin/env python3
"""Strict validation of catalog.json (stdlib only). Exit code 1 on any problem.

Everything the app will ever pass to a package manager is checked here, and again by the app itself.
"""
import json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._+@-]{0,127}$")
SYMBOL = re.compile(r"^[A-Z][a-z0-9]{1,2}$")
SPEC = re.compile(r"^git\+https://github\.com/[A-Za-z0-9._-]+/[A-Za-z0-9._-]+(@[A-Za-z0-9._/-]+)?$")
HEX = re.compile(r"^#[0-9A-Fa-f]{6}$")
TYPES = {"homebrew_formula": "brew", "homebrew_cask": "cask", "pipx": "pipx"}
PKG_KEYS = {"id", "number", "symbol", "name", "summary", "category", "homepage", "license", "source", "default", "tags", "note"}
TOP_KEYS = {"schema_version", "catalog_version", "generated_at", "name", "categories", "presets", "packages"}


def validate(doc):
    errors = []
    def err(msg): errors.append(msg)

    if not isinstance(doc, dict): return ["catalog must be a JSON object"]
    for k in set(doc) - TOP_KEYS: err(f"unknown top-level key: {k}")
    if doc.get("schema_version") != 2: err("schema_version must be 2")
    if not isinstance(doc.get("catalog_version"), int) or doc["catalog_version"] < 1: err("catalog_version must be an integer >= 1")

    cats = doc.get("categories") or []
    cat_ids = set()
    for c in cats:
        if set(c) - {"id", "name", "symbol", "color"}: err(f"category {c.get('id')}: unknown keys")
        if not re.match(r"^[a-z0-9-]+$", str(c.get("id", ""))): err(f"bad category id {c.get('id')!r}")
        if c.get("id") in cat_ids: err(f"duplicate category {c.get('id')}")
        cat_ids.add(c.get("id"))
        if not c.get("name"): err(f"category {c.get('id')}: missing name")
        if not HEX.match(str(c.get("color", ""))): err(f"category {c.get('id')}: color must be #RRGGBB")
        if not c.get("symbol"): err(f"category {c.get('id')}: missing SF Symbol name")
    if not cats: err("at least one category is required")

    pkgs = doc.get("packages") or []
    ids, numbers, symbols, names = set(), set(), set(), set()
    for p in pkgs:
        pid = p.get("id", "?")
        for k in set(p) - PKG_KEYS: err(f"{pid}: unknown key {k!r}")
        src = p.get("source") or {}
        t, n = src.get("type"), src.get("name", "")
        if t not in TYPES: err(f"{pid}: unsupported source type {t!r}"); continue
        if not NAME.match(n) or ".." in n: err(f"{pid}: invalid source name {n!r}")
        if set(src) - {"type", "name", "spec"}: err(f"{pid}: unknown source keys")
        if "spec" in src:
            if t != "pipx": err(f"{pid}: spec is only allowed for pipx")
            elif not SPEC.match(src["spec"]): err(f"{pid}: spec must be git+https://github.com/<owner>/<repo>[@ref]")
        if pid != f"{TYPES[t]}:{n}": err(f"{pid}: id must be '{TYPES[t]}:{n}'")
        if pid in ids: err(f"duplicate id {pid}")
        ids.add(pid)
        num = p.get("number")
        if num is not None:
            if not isinstance(num, int) or num < 1: err(f"{pid}: number must be a positive integer")
            elif num in numbers: err(f"{pid}: duplicate number {num}")
            numbers.add(num)
        sym = p.get("symbol")
        if sym is not None:
            if not SYMBOL.match(sym): err(f"{pid}: symbol {sym!r} must look like 'Nm' (2-3 chars)")
            elif sym in symbols: err(f"{pid}: duplicate symbol {sym}")
            symbols.add(sym)
        if not p.get("name"): err(f"{pid}: missing name")
        s = p.get("summary", "")
        if not (1 <= len(s) <= 300): err(f"{pid}: summary must be 1..300 characters")
        if p.get("category") not in cat_ids: err(f"{pid}: unknown category {p.get('category')!r}")
        hp = p.get("homepage", "")
        if hp and not hp.startswith("https://"): err(f"{pid}: homepage must be https")
        if "default" in p and not isinstance(p["default"], bool): err(f"{pid}: default must be boolean")

    for pr in doc.get("presets") or []:
        if set(pr) - {"id", "name", "description", "categories", "packages"}: err(f"preset {pr.get('id')}: unknown keys")
        for c in pr.get("categories", []):
            if c not in cat_ids: err(f"preset {pr.get('id')}: unknown category {c}")
        for pid in pr.get("packages", []):
            if pid not in ids: err(f"preset {pr.get('id')}: unknown package {pid}")
    return errors


def main():
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "catalog.json"
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        sys.exit(f"cannot read {path}: {e}")
    errors = validate(doc)
    if errors:
        print("\n".join(f"ERROR {e}" for e in errors)); sys.exit(1)
    print(f"OK: {len(doc['packages'])} packages, {len(doc['categories'])} categories, catalog_version {doc['catalog_version']}")


if __name__ == "__main__":
    main()
