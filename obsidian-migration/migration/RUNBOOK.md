# Migration runbook

Move one OneNote section at a time. Do the first section by hand end to end before automating anything.

## Pipeline

```
OneNote ──export──▶ quarantine/ ──scan──▶ review queue ──promote──▶ vault/80-migrated/
                                    │                                 or
                                    └──(private)──────────────────▶ vault/90-private/
```

Nothing goes from quarantine to the vault without passing step 3.

## 1. Choose what to mine

List notebooks and sections first. Mark each section one of:

- `mine` — pull it.
- `private` — pull it, but it goes straight to `90-private/` with no agent review.
- `skip` — leave it in OneNote.

Record the decisions in `scan-config.json` under `sections`. The export script refuses sections not listed.

## 2. Export to quarantine

Two paths. Pick one per section; they produce the same layout.

**Path A, Graph API (recommended).** Selective, scriptable, exports page HTML that converts cleanly to Markdown. Needs an Azure app registration with `Notes.Read` delegated permission. See `export_onenote_graph.py`.

**Path B, desktop control.** Cowork drives the OneNote desktop app through File → Export. Use it when Graph is blocked by tenant policy or for a handful of sections where setting up an app registration is not worth it. It is slower and fragile on large sections. See `desktop-export-prompt.md`.

Either way the output is:

```
quarantine/<notebook>/<section>/<page-title>.md
```

with frontmatter `source: "<notebook>/<section>/<page>"` and `visibility: unreviewed`.

## 3. Sensitivity gate

```
python sensitivity_scan.py quarantine/ --config scan-config.json --report scan-report.md
```

The script marks each page `clean`, `flagged`, or `private`:

- `private` — a hard rule matched (card number, credential pattern, or the section is marked private). Goes to `90-private/`. No agent sees it.
- `flagged` — a soft rule matched (person name near a money figure, a keyword from your list). Goes to the review queue.
- `clean` — no hits. Eligible for promotion.

Run the LLM second pass only on `flagged` pages, using `agents/sensitivity-review.md`. The LLM downgrades to `clean` or upgrades to `private`. It never promotes anything itself. You read the report and approve.

## 4. Promote

For each approved page:

1. Set `visibility` to `cleared` or `private`.
2. Move to `vault/80-migrated/<section>/` or `vault/90-private/<section>/`.
3. Commit with message `migrate: <notebook>/<section>`.

Delete the quarantine copy only after the commit is pushed.

## 5. Afterwards

Migrated pages keep their OneNote structure. Do not reorganize them during migration. Reorganize by hand, or ask the formatter to propose moves, once you know what you actually reference.
