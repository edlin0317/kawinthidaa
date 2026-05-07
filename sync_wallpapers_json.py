#!/usr/bin/env python3
"""
Rebuild wallpapers.json from the contents of wallpapers/.

Usage:
  python sync_wallpapers_json.py
  python sync_wallpapers_json.py --dir wallpapers --out wallpapers.json
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


def build_manifest(image_dir: Path) -> list[str]:
    if not image_dir.is_dir():
        raise FileNotFoundError(f"Wallpaper directory not found: {image_dir}")

    files = [p.name for p in image_dir.iterdir() if p.is_file()]
    return sorted(files, key=str.lower)


def write_manifest(output_path: Path, items: list[str]) -> bool:
    payload = json.dumps(items, ensure_ascii=False, separators=(", ", ": "))
    payload += "\n"

    if output_path.exists():
        current = output_path.read_text(encoding="utf-8")
        if current == payload:
            return False

    output_path.write_text(payload, encoding="utf-8")
    return True


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Sync wallpapers.json with wallpapers/")
    parser.add_argument("--dir", dest="image_dir", default="wallpapers", help="Directory to scan")
    parser.add_argument("--out", dest="output", default="wallpapers.json", help="JSON manifest path")
    args = parser.parse_args(argv)

    image_dir = Path(args.image_dir)
    output_path = Path(args.output)

    items = build_manifest(image_dir)
    changed = write_manifest(output_path, items)

    action = "updated" if changed else "already up to date"
    print(f"{output_path} {action} with {len(items)} files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
