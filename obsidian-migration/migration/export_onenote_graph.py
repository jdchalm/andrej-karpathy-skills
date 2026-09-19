#!/usr/bin/env python3
"""Selectively export OneNote sections to quarantine via the Microsoft Graph API.

Setup (one time):
    1. Register an app at https://entra.microsoft.com → App registrations.
       Platform: "Mobile and desktop applications", redirect URI
       http://localhost. Delegated permission: Notes.Read.
    2. pip install msal requests markdownify
    3. export ONENOTE_CLIENT_ID=<app client id>
       export ONENOTE_TENANT=common     # or your tenant id

Usage:
    python export_onenote_graph.py --list                      # print notebook/section names
    python export_onenote_graph.py --config scan-config.json --out quarantine/

Only sections marked "mine" or "private" in the config are exported.
Output: quarantine/<notebook>/<section>/<page>.md with frontmatter.

Untested against a live tenant in this repo. Expect to adjust pagination or
HTML quirks on first run.
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path

import msal
import requests
from markdownify import markdownify

GRAPH = "https://graph.microsoft.com/v1.0/me/onenote"
SCOPES = ["Notes.Read"]


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
    r = requests.get(url, headers={"Authorization": f"Bearer {tok}"}, timeout=60)
    r.raise_for_status()
    return r.text if raw else r.json()


def paged(url, tok):
    while url:
        data = get(url, tok)
        yield from data.get("value", [])
        url = data.get("@odata.nextLink")


def sections(tok):
    for nb in paged(f"{GRAPH}/notebooks", tok):
        for sec in paged(f"{GRAPH}/notebooks/{nb['id']}/sections", tok):
            yield nb["displayName"], sec["displayName"], sec["id"]


def safe(name):
    return re.sub(r"[^\w\- ]+", "_", name).strip() or "untitled"


def export_section(nb, sec, sec_id, tok, out):
    folder = out / safe(nb) / safe(sec)
    folder.mkdir(parents=True, exist_ok=True)
    n = 0
    for page in paged(f"{GRAPH}/sections/{sec_id}/pages?$select=id,title,createdDateTime,lastModifiedDateTime", tok):
        html = get(f"{GRAPH}/pages/{page['id']}/content", tok, raw=True)
        body = markdownify(html, heading_style="ATX").strip()
        title = page.get("title") or "untitled"
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
        (folder / f"{safe(title)}.md").write_text(fm + f"# {title}\n\n{body}\n")
        n += 1
    print(f"{nb}/{sec}: {n} pages")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--config")
    ap.add_argument("--out", type=Path, default=Path("quarantine"))
    args = ap.parse_args()

    tok = token()
    if args.list:
        for nb, sec, _ in sections(tok):
            print(f"{nb}/{sec}")
        return 0

    if not args.config:
        sys.exit("--config required unless --list")
    wanted = json.loads(Path(args.config).read_text())["sections"]
    for nb, sec, sec_id in sections(tok):
        if wanted.get(f"{nb}/{sec}") in ("mine", "private"):
            export_section(nb, sec, sec_id, tok, args.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
