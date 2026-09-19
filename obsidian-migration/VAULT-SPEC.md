# Vault spec

The contract between the human and every agent that touches the vault. Keep it to one page. If a rule is not here, it is not a rule.

## Folders

```
vault/
  _templates/     Obsidian templates (this kit's templates/ folder)
  00-inbox/       Raw capture. Anything goes. Formatter cleans nightly.
  10-daily/       One note per day, YYYY-MM-DD.md
  20-meetings/    One note per meeting, YYYY-MM-DD <topic>.md
  30-entities/    People, clients, vendors, products. One note each, by name.
  40-projects/    One note per project or initiative, by name.
  50-reference/   Stable how-to and reference material.
  80-migrated/    Notes promoted from OneNote, as <notebook>/<section>/ (so by year and month). Reorganize by hand over time.
  90-private/     Sensitive. Never shared with cloud agents. Never touched by the formatter.
    migrated/     Private OneNote pages, same <notebook>/<section>/ layout.
  99-archive/     Closed projects, stale entities.
```

Outside the vault, never synced or committed:

```
quarantine/       Raw OneNote exports awaiting the sensitivity gate.
```

## Frontmatter

Every note has this block. The formatter adds it if missing.

```yaml
---
type: daily | meeting | entity | project | reference | inbox
created: 2026-09-19
updated: 2026-09-19
status: active | done | archived
visibility: cleared | private
tags: []
source: ""            # OneNote path if migrated, else empty
---
```

Rules:
- `visibility: private` notes live only in `90-private/`. The folder and the field must agree.
- `updated` is set by whoever last edited the body, human or agent.
- `tags` are lowercase, hyphenated, no nesting deeper than one slash (`client/acme` is fine, `client/acme/2026` is not).

## Links

- Link entities and projects by wikilink on first mention in a note: `[[Acme Corp]]`, `[[Q4 pricing review]]`.
- Do not link dates. The daily note is found by filename.

## Agent roles

| Agent | May write to | May restructure |
|---|---|---|
| End-of-day formatter | everything except `90-private/` | yes |
| Claude Code / Cowork (interactive) | anything the human asks for | only when asked |
| Cursor / Scout | `00-inbox/`, `40-projects/` | no |
| Grok | `00-inbox/` (append only) | no |

Any agent that writes must:
1. Confirm `git status` is clean before starting.
2. Commit with a message starting `agent(<name>):`.
3. Never delete body text. Move it to the bottom under `## Unsorted` if unsure.

## Sensitivity

A note is private if it contains any of: credentials, account or card numbers, a named person or client together with money figures, or anything from a OneNote section matched as private in `migration/scan-config.json`. Private notes go in `90-private/` and nowhere else.

## Migrated content

`80-migrated/` is large (20 years). Agents may read it and link to it but must not reorganize, retag, or template it. The formatter's scope excludes it. Anything worth restructuring gets copied into `30-entities/` or `40-projects/` by the human, with a link back.
