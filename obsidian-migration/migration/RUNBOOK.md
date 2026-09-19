# Migration runbook

Scale: about 20 years of monthly sections, so roughly 240 sections and likely thousands of pages. Work **one year at a time**, oldest first. Do the first year fully by hand before letting an agent run the loop. Oldest first because old content is least likely to change while you migrate and the least costly to get wrong.

## Pipeline

```
OneNote ──export──▶ quarantine/ ──scan──▶ review queue ──promote──▶ vault/80-migrated/
                                    │                                 or
                                    └──(private)──────────────────▶ vault/90-private/
```

Nothing goes from quarantine to the vault without passing step 3.

## 1. Choose what to mine

Inventory first:

```
python export_onenote_graph.py --list > sections.txt
```

Then write glob rules in `scan-config.json` under `sections`, matched against `Notebook/Section`. First match wins; `default` covers the rest. Values:

- `mine` — pull it.
- `private` — pull it, but it goes straight to `90-private/` with no agent review.
- `skip` — leave it in OneNote.

At 240 sections you will not list each one. Set `default` to `mine` and write a handful of patterns for the private and skip cases. Check the inventory for section names that would surprise the rules.

## 2. Export to quarantine

**Path A, Graph API.** This is the path at this volume. Selective, resumable, throttle-aware, and it can be run per year. Needs an Azure app registration with `Notes.Read` delegated permission. See `export_onenote_graph.py`.

```
python export_onenote_graph.py --config scan-config.json --out quarantine/ --year 2006
```

`--year` matches the year string anywhere in the notebook or section name, so it works for `2006` notebooks with month sections and for `Notes/2006-03` alike. If your naming does not contain the year, drop the flag and run everything; it is resumable.

**Path B, desktop control** (`desktop-export-prompt.md`) is kept for reference but is not viable for 240 sections. Use it only if Graph is blocked by tenant policy, and then only for the sections you need most.

Output is:

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

Expect the soft rules to over-flag on old business notes; money figures and emails are everywhere. After the first year, look at what got flagged and tighten `soft_patterns` and `keywords` before doing the next year. The hard rules stay as they are.

## 4. Promote

```
python promote.py quarantine/ vault/ --dry-run     # shows the moves
python promote.py quarantine/ vault/
```

For each scanned page it sets `visibility` from the scan verdict and moves it:

- `clean` → `vault/80-migrated/<notebook>/<section>/`
- `private` → `vault/90-private/migrated/<notebook>/<section>/`
- `flagged` → left in quarantine until the LLM pass and you change `scan:` to `clean` or `private`.

Commit after each year: `migrate: 2006`. Delete the quarantine copies for that year only after the commit is pushed.

## 5. Loop

Repeat steps 2 to 4 per year. Once the first year is done by hand, the loop is a good job for Claude Code or Scout: the prompt is "run steps 2 to 4 of RUNBOOK.md for year N, stop at the review queue, report counts". The agent must not decide flagged pages.

## 6. Afterwards

Migrated pages keep their OneNote structure under `80-migrated/`. Do not reorganize them during migration. Reorganize by hand, or ask the formatter to propose moves, once you know what you actually reference. Most of 20 years will stay where it lands and that is fine; it is searchable.
