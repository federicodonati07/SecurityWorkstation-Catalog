#!/usr/bin/env python3
"""Print catalog entries (JSON) for Homebrew formulae/casks or PyPI packages, using real metadata.

Usage:
  tools/import_from_homebrew.py formula nmap ffuf
  tools/import_from_homebrew.py cask zap
  tools/import_from_homebrew.py pipx impacket

The output is a starting point: set "category", optionally "default": true, and paste it into
catalog.json -> "packages". `number` and `symbol` are assigned by tools/release.py.
"""
import json, subprocess, sys, urllib.request


def brew_info(kind, names):
    flag = "--formula" if kind == "formula" else "--cask"
    out = subprocess.run(["brew", "info", "--json=v2", flag, *names], capture_output=True, text=True, check=True).stdout
    data = json.loads(out)
    return data["formulae"] if kind == "formula" else data["casks"]


def entry(kind, name, summary, homepage, license_):
    prefix = {"formula": "brew", "cask": "cask", "pipx": "pipx"}[kind]
    src = {"formula": "homebrew_formula", "cask": "homebrew_cask", "pipx": "pipx"}[kind]
    return {
        "id": f"{prefix}:{name}",
        "name": name,
        "summary": summary or "",
        "category": "CHOOSE-A-CATEGORY-ID",
        "homepage": homepage or "",
        "license": license_ or "",
        "source": {"type": src, "name": name},
    }


def main():
    if len(sys.argv) < 3 or sys.argv[1] not in ("formula", "cask", "pipx"):
        sys.exit(__doc__)
    kind, names = sys.argv[1], sys.argv[2:]
    result = []
    if kind == "pipx":
        for n in names:
            with urllib.request.urlopen(f"https://pypi.org/pypi/{n}/json", timeout=15) as r:
                info = json.load(r)["info"]
            result.append(entry(kind, n, info.get("summary"), info.get("home_page") or (info.get("project_urls") or {}).get("Homepage"), info.get("license") if info.get("license") and len(info["license"]) < 40 else ""))
    else:
        for item in brew_info(kind, names):
            if kind == "formula":
                result.append(entry(kind, item["name"], item.get("desc"), item.get("homepage"), item.get("license")))
            else:
                result.append(entry(kind, item["token"], item.get("desc") or (item.get("name") or [""])[0], item.get("homepage"), ""))
    print(json.dumps(result, indent=2, ensure_ascii=False))


main()
