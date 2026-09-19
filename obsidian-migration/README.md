# OneNote → Obsidian migration kit

Templates, conventions, and runbooks for moving business notes out of OneNote into an Obsidian vault that is shared by a human and several agents (Claude Code, Cowork, Cursor / Scout, Grok).

## What is here

| Path | Purpose |
|---|---|
| `VAULT-SPEC.md` | One-page conventions: folders, frontmatter, tags, visibility. Every agent reads this first. |
| `templates/` | Obsidian note templates. Copy into the vault's `_templates/` folder. |
| `migration/RUNBOOK.md` | Step-by-step migration: export → quarantine → sensitivity gate → promote. |
| `migration/export_onenote_graph.py` | Selective, resumable export via the Microsoft Graph API. The only viable path at 20 years of sections. |
| `migration/desktop-export-prompt.md` | Fallback: drive the OneNote desktop app with Cowork computer use. A few sections only. |
| `migration/sensitivity_scan.py` | Deterministic scan for sensitive patterns. Runs on quarantine before anything enters the vault. |
| `migration/promote.py` | Moves scanned pages into the vault by verdict. |
| `agents/sensitivity-review.md` | Prompt for the LLM second pass over scan hits. |
| `agents/end-of-day-formatter.md` | Prompt for the nightly formatting agent. |

## Assumptions

These are the defaults the kit is built on. Change `VAULT-SPEC.md` if any are wrong.

- The vault lives on local disk and is a git repo. Git is the snapshot mechanism for agents; no agent edits without a clean tree.
- OneNote content is in a Microsoft 365 or personal Microsoft account reachable via Graph.
- Volume is about 20 years of monthly sections. Migration runs one year at a time and most migrated content stays in its original structure.
- "Sensitive" means, at minimum: client and person identities tied to financials, account or card numbers, credentials, and anything in a OneNote section you mark private. The scan config is where you narrow or widen this.
- Agents other than the formatter are read-only or append-only in the vault. Only the formatter restructures notes.
- Cloud agents (Grok, hosted Claude Code, Scout) never see `90-private/`. Give them a copy or a sparse checkout that excludes it.

## Order of operations

1. Create the vault, copy `templates/` into `_templates/`, commit.
2. Run the migration runbook on the oldest year by hand, then let an agent loop over the rest.
3. Live in the vault for two weeks before adding parsers for specific note types.
4. Turn on the end-of-day formatter once the templates have stopped changing.
