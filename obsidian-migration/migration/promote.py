#!/usr/bin/env python3
"""Move scanned quarantine pages into the vault by verdict.

Usage:
    python promote.py quarantine/ vault/ [--dry-run]

Reads the `scan:` field the scanner wrote into each page's frontmatter.
    clean   -> vault/80-migrated/<notebook>/<section>/
    private -> vault/90-private/migrated/<notebook>/<section>/
    flagged -> left in place (needs review; edit `scan:` by hand first)
    skip    -> left in place
    missing -> left in place (not scanned yet)

Sets `visibility:` to match and removes the `scan:` line. Never overwrites an
existing vault file; those are reported and skipped.
"""

import argparse
import re
import shutil
import sys
from pathlib import Path

FRONTMATTER = re.compile(r"\A---\n(.*?)\n---\n", re.S)
DEST = {"clean": ("80-migrated", "cleared"), "private": ("90-private/migrated", "private")}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("quarantine", type=Path)
    ap.add_argument("vault", type=Path)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    counts = {"moved": 0, "left": 0, "exists": 0}
    for page in sorted(args.quarantine.rglob("*.md")):
        text = page.read_text(errors="replace")
        m = FRONTMATTER.match(text)
        verdict = re.search(r"^scan:\s*(\w+)", m.group(1), re.M) if m else None
        verdict = verdict.group(1) if verdict else None
        if verdict not in DEST:
            counts["left"] += 1
            continue
        folder, visibility = DEST[verdict]
        target = args.vault / folder / page.relative_to(args.quarantine)
        if target.exists():
            print(f"exists, skipped: {target}")
            counts["exists"] += 1
            continue
        fm = re.sub(r"^scan:.*\n?", "", m.group(1), flags=re.M).rstrip("\n")
        fm = re.sub(r"^visibility:.*$", f"visibility: {visibility}", fm, flags=re.M)
        print(f"{verdict:8} {page.relative_to(args.quarantine)} -> {folder}/")
        if not args.dry_run:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(f"---\n{fm}\n---\n" + text[m.end():])
            page.unlink()
        counts["moved"] += 1
    print(counts)
    return 0


if __name__ == "__main__":
    sys.exit(main())
