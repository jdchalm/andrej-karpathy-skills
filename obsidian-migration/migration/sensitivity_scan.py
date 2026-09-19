#!/usr/bin/env python3
"""Scan quarantined Markdown pages for sensitive content.

Usage:
    python sensitivity_scan.py quarantine/ --config scan-config.json --report scan-report.md

Each page is classified:
    private  - a hard pattern matched, or the page's section is marked private in the config
    flagged  - a soft pattern or keyword matched; needs LLM review then human approval
    clean    - nothing matched
    skip     - the page's section is marked skip in the config; promote leaves it alone

The verdict is written into the page's frontmatter as `scan: <verdict>` and
summarised in the report. The script never moves or deletes files.
"""

import argparse
import fnmatch
import json
import re
import sys
from pathlib import Path

FRONTMATTER = re.compile(r"\A---\n(.*?)\n---\n", re.S)


def load_config(path):
    cfg = json.loads(Path(path).read_text())
    cfg["hard"] = {k: re.compile(v) for k, v in cfg["hard_patterns"].items()}
    cfg["soft"] = {k: re.compile(v) for k, v in cfg["soft_patterns"].items()}
    cfg["kw"] = re.compile(r"\b(" + "|".join(map(re.escape, cfg["keywords"])) + r")\b", re.I)
    return cfg


def section_of(page, root):
    # quarantine/<notebook>/<section>/<page>.md -> "<notebook>/<section>"
    rel = page.relative_to(root)
    return "/".join(rel.parts[:-1])


def rule_for(section, cfg):
    for pattern, rule in cfg["sections"].items():
        if fnmatch.fnmatch(section, pattern):
            return rule
    return cfg.get("default", "skip")


def classify(text, section, cfg):
    hits = []
    rule = rule_for(section, cfg)
    if rule == "skip":
        return "skip", ["section:skip"]
    if rule == "private":
        hits.append("section:private")
    for name, rx in cfg["hard"].items():
        if rx.search(text):
            hits.append(f"hard:{name}")
    if hits:
        return "private", hits
    for name, rx in cfg["soft"].items():
        if rx.search(text):
            hits.append(f"soft:{name}")
    for m in cfg["kw"].finditer(text):
        hits.append(f"kw:{m.group(1).lower()}")
    return ("flagged" if hits else "clean"), sorted(set(hits))


def write_verdict(page, text, verdict):
    m = FRONTMATTER.match(text)
    if not m:
        return  # no frontmatter; report only
    fm = re.sub(r"^scan:.*\n?", "", m.group(1), flags=re.M).rstrip("\n")
    new = f"---\n{fm}\nscan: {verdict}\n---\n" + text[m.end():]
    page.write_text(new)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("root", type=Path)
    ap.add_argument("--config", required=True)
    ap.add_argument("--report", default="scan-report.md")
    ap.add_argument("--dry-run", action="store_true", help="do not write verdicts into pages")
    args = ap.parse_args()

    cfg = load_config(args.config)
    rows = []
    for page in sorted(args.root.rglob("*.md")):
        text = page.read_text(errors="replace")
        verdict, hits = classify(text, section_of(page, args.root), cfg)
        rows.append((verdict, page.relative_to(args.root), hits))
        if not args.dry_run:
            write_verdict(page, text, verdict)

    counts = {v: sum(1 for r in rows if r[0] == v) for v in ("private", "flagged", "clean", "skip")}
    lines = ["# Sensitivity scan report", "",
             f"private: {counts['private']}  flagged: {counts['flagged']}  clean: {counts['clean']}  skip: {counts['skip']}", ""]
    # private and flagged are listed per page; clean is only counted per section,
    # otherwise the report is thousands of lines at this volume.
    for verdict in ("private", "flagged"):
        lines.append(f"## {verdict}")
        for v, rel, hits in rows:
            if v == verdict:
                lines.append(f"- `{rel}`" + (f" — {', '.join(hits)}" if hits else ""))
        lines.append("")
    lines.append("## clean (count per section)")
    per_section = {}
    for v, rel, _ in rows:
        if v == "clean":
            per_section[rel.parent] = per_section.get(rel.parent, 0) + 1
    for sec, n in sorted(per_section.items()):
        lines.append(f"- `{sec}`: {n}")
    lines.append("")
    Path(args.report).write_text("\n".join(lines))
    print(f"{len(rows)} pages: {counts}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
