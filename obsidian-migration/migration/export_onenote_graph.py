#!/usr/bin/env python3
"""Selectively export OneNote sections to quarantine via the Microsoft Graph API.

Built for volume: hundreds of sections, thousands of pages. Resumable (skips
pages already on disk), throttled, and filterable by year so you can migrate
one year at a time.

Setup (one time):
    1. Register an app at https://entra.microsoft.com → App registrations.
       Platform: "Mobile and desktop applications", redirect URI
       http://localhost. Delegated permission: Notes.Read.
    2. pip install msal requests markdownify
    3. export ONENOTE_CLIENT_ID=<app client id>
       export ONENOTE_TENANT=common     # or your tenant id

Usage:
    python export_onenote_graph.py --list > sections.txt      # inventory first
    python export_onenote_graph.py --config scan-config.json --out quarantine/ --year 2019
    python export_onenote_graph.py --config scan-config.json --out quarantine/   # everything

Section rules come from scan-config.json ("sections" patterns + "default").
Output: quarantine/<notebook>/<section>/<page>.md with frontmatter.
Re-run after any failure; existing files are skipped.

Untested against a live tenant in this repo. Expect to adjust the HTML
conversion on first run.
"""

import argparse
import fnmatch
import json
import os
import re
import sys
import time
from pathlib import Path

import msal
import requests
from markdownify import markdownify

GRAPH = "https://graph.microsoft.com/v1.0/me/onenote"
SCOPES = ["Notes.Read"]
PAUSE = 0.25  # seconds between page fetches; Graph throttles OneNote hard


def token():
    app = msal.PublicClientApplication(
        os.environ["ONENOTE_CLIENT_ID"],
        authority=f"https://login.microsoftonline.com/{os.environ.get('ONENOTE_TENANT', 'common')}",
    )
    flow = app.initiate_device_flow(scopes=SCOPES)
    print(flow["message"])
    result = app.acquire_token_by_device_flow(flow)
    if "access_token" not in result:
        sys.exit(f"auth failed: {result.get('error_description')}")
    return result["access_token"]


def get(url, tok, raw=False):
    for attempt in range(6):
        r = requests.get(url, headers={"Authorization": f"Bearer {tok}"}, timeout=60)
        if r.status_code in (429, 503):
            wait = int(r.headers.get("Retry-After", 2 ** attempt))
            print(f"  throttled, waiting {wait}s", file=sys.stderr)
            time.sleep(wait)
            continue
        r.raise_for_status()
        return r.text if raw else r.json()
    sys.exit(f"gave up on {url}")


def paged(url, tok):
    while url:
        data = get(url, tok)
        yield from data.get("value", [])
        url = data.get("@odata.nextLink")


def sections(tok):
    for nb in paged(f"{GRAPH}/notebooks", tok):
        for sec in paged(f"{GRAPH}/notebooks/{nb['id']}/sections", tok):
            yield nb["displayName"], sec["displayName"], sec["id"]


def rule_for(path, cfg):
    """First matching glob in cfg['sections'] wins, else cfg['default']."""
    for pattern, rule in cfg["sections"].items():
        if fnmatch.fnmatch(path, pattern):
            return rule
    return cfg.get("default", "skip")


def safe(name):
    return re.sub(r"[^\w\- ]+", "_", name).strip() or "untitled"


def export_section(nb, sec, sec_id, tok, out):
    folder = out / safe(nb) / safe(sec)
    folder.mkdir(parents=True, exist_ok=True)
    done = skipped = 0
    for page in paged(f"{GRAPH}/sections/{sec_id}/pages?$select=id,title,createdDateTime,lastModifiedDateTime&$top=100", tok):
        title = page.get("title") or "untitled"
        target = folder / f"{safe(title)}--{page['id'][-8:]}.md"  # id suffix: duplicate titles are common
        if target.exists():
            skipped += 1
            continue
        html = get(f"{GRAPH}/pages/{page['id']}/content", tok, raw=True)
        body = markdownify(html, heading_style="ATX").strip()
        fm = "\n".join([
            "---",
            "type: inbox",
            f"created: {page['createdDateTime'][:10]}",
            f"updated: {page['lastModifiedDateTime'][:10]}",
            "status: active",
            "visibility: unreviewed",
            "tags: [migrated]",
            f'source: "{nb}/{sec}/{title}"',
            "---",
            "",
        ])
        target.write_text(fm + f"# {title}\n\n{body}\n")
        done += 1
        time.sleep(PAUSE)
    print(f"{nb}/{sec}: {done} exported, {skipped} already present")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--config")
    ap.add_argument("--out", type=Path, default=Path("quarantine"))
    ap.add_argument("--year", help="only sections whose notebook or section name contains this year")
    args = ap.parse_args()

    tok = token()
    if args.list:
        for nb, sec, _ in sections(tok):
            print(f"{nb}/{sec}")
        return 0

    if not args.config:
        sys.exit("--config required unless --list")
    cfg = json.loads(Path(args.config).read_text())
    for nb, sec, sec_id in sections(tok):
        path = f"{nb}/{sec}"
        if args.year and args.year not in path:
            continue
        if rule_for(path, cfg) in ("mine", "private"):
            export_section(nb, sec, sec_id, tok, args.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
