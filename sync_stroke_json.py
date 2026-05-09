#!/usr/bin/env python3
"""
Sync character stroke JSON files from hanzi-writer-data repository.

This script extracts all unique Chinese characters from vocab-data.json
and downloads their stroke data from:
  https://github.com/chanind/hanzi-writer-data

Usage:
  python sync_stroke_json.py                          # Sync both Traditional and Simplified
  python sync_stroke_json.py --variants tw           # Traditional only
  python sync_stroke_json.py --variants cn           # Simplified only
  python sync_stroke_json.py --variants tw,cn        # Both (explicit)
  python sync_stroke_json.py --vocab vocab-data.json --out stroke
"""

from __future__ import annotations

import argparse
import json
import urllib.request
import urllib.error
import urllib.parse
from pathlib import Path
from typing import Set
import sys


HANZI_WRITER_BASE = "https://raw.githubusercontent.com/chanind/hanzi-writer-data/master/data"


def extract_characters(vocab_path: Path, variants: list[str] | None = None) -> Set[str]:
    """Extract all unique Chinese characters from vocabulary data.
    
    Args:
        vocab_path: Path to vocabulary data file
        variants: List of variants to extract ('tw' for Traditional, 'cn' for Simplified).
                 Defaults to ['tw', 'cn'] (both variants).
    """
    if variants is None:
        variants = ["tw", "cn"]
    
    if not vocab_path.exists():
        raise FileNotFoundError(f"Vocabulary file not found: {vocab_path}")

    with open(vocab_path, "r", encoding="utf-8") as f:
        vocab_data = json.load(f)

    characters = set()

    # Extract from beginner and main lists
    for level in ["beginner", "main"]:
        if level in vocab_data:
            for entry in vocab_data[level]:
                # Extract characters from specified variants
                for variant in variants:
                    if variant in entry:
                        for char in entry[variant]:
                            if ord(char) > 0x4E00 and ord(char) < 0x9FFF:
                                characters.add(char)

    return sorted(characters, key=lambda x: (ord(x), x))


def fetch_stroke_data(character: str, output_dir: Path, force: bool = False) -> bool:
    """
    Fetch stroke data for a character from hanzi-writer-data.
    Returns True if successful or already cached, False if failed.
    """
    output_file = output_dir / f"{character}.json"

    # Check if already cached
    if output_file.exists() and not force:
        return True

    # URL-encode the character
    encoded_char = urllib.parse.quote(character, safe='')
    url = f"{HANZI_WRITER_BASE}/{encoded_char}.json"

    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            data = response.read()
            output_file.write_bytes(data)
            return True
    except urllib.error.HTTPError as e:
        if e.code == 404:
            # Character not found in stroke database
            return False
        raise
    except Exception as e:
        print(f"Error fetching {character}: {e}", file=sys.stderr)
        return False


def sync_strokes(vocab_path: Path, output_dir: Path, force: bool = False, variants: list[str] | None = None) -> None:
    """Sync all character stroke data from vocabulary.
    
    Args:
        vocab_path: Path to vocabulary data file
        output_dir: Output directory for stroke JSON files
        force: Re-download all files even if cached
        variants: List of variants to sync ('tw' for Traditional, 'cn' for Simplified).
                 Defaults to ['tw', 'cn'] (both variants).
    """
    if variants is None:
        variants = ["tw", "cn"]
    
    output_dir.mkdir(parents=True, exist_ok=True)

    variant_str = ", ".join({"tw": "Traditional", "cn": "Simplified"}.get(v, v) for v in variants)
    print(f"Extracting {variant_str} characters from {vocab_path}...")
    characters = extract_characters(vocab_path, variants)
    print(f"Found {len(characters)} unique characters")

    successful = 0
    failed = 0
    skipped = 0

    print(f"Fetching stroke data to {output_dir}...")
    for i, char in enumerate(characters, 1):
        output_file = output_dir / f"{char}.json"

        if output_file.exists() and not force:
            skipped += 1
            status = "cached"
        else:
            if fetch_stroke_data(char, output_dir, force):
                successful += 1
                status = "downloaded"
            else:
                failed += 1
                status = "not found"

        # Print progress every 10 characters
        if i % 10 == 0 or i == len(characters):
            print(f"  [{i:4d}/{len(characters)}] {char} - {status}")

    print(f"\nResults:")
    print(f"  Downloaded: {successful}")
    print(f"  Cached:     {skipped}")
    print(f"  Not found:  {failed}")
    print(f"  Total:      {len(characters)}")


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description="Sync character stroke data from hanzi-writer-data"
    )
    parser.add_argument(
        "--vocab",
        dest="vocab_path",
        default="vocab-data.json",
        help="Path to vocabulary data file",
    )
    parser.add_argument(
        "--out", dest="output_dir", default="stroke", help="Output directory for stroke JSON files"
    )
    parser.add_argument(
        "--force",
        dest="force",
        action="store_true",
        help="Re-download all files even if cached",
    )
    parser.add_argument(
        "--variants",
        dest="variants",
        default="tw,cn",
        help="Character variants to sync: 'tw' (Traditional), 'cn' (Simplified), or comma-separated list (default: tw,cn)",
    )

    args = parser.parse_args(argv)

    vocab_path = Path(args.vocab_path)
    output_dir = Path(args.output_dir)
    variants = [v.strip() for v in args.variants.split(",") if v.strip()]

    try:
        sync_strokes(vocab_path, output_dir, args.force, variants)
        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
