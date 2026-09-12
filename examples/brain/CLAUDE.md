# CLAUDE.md for the example brain

The four principles from this repo's root CLAUDE.md apply here unchanged. Below is the schema block
the Graph layer runs on.

## Wiki schema
- raw/ is immutable. Never edit, rename or delete anything in it.
- Page folders: criteria/, cases/, decisions/. Prefer updating an existing page over creating a new one.
- Every page starts with a one-line summary and a `Sources:` line linking into raw/.
- Every factual claim cites a raw/ file or another wiki page.
- When a new source contradicts an existing page, do not overwrite. Add a
  `> Contradiction:` block quoting both sides and list the page in index.md under "Disputed".
- After any ingest: update index.md, append one dated line to log.md.
- Query answers that took real work become a page in decisions/.

## Operations
- **ingest <raw file>**: read it, update the affected pages, cross-link, update index.md, append to log.md.
- **query <question>**: read index.md, open relevant pages, answer with citations. Save real work to decisions/.
- **lint**: list contradictions, stale claims, orphan pages, criteria without examples. Do not fix; report.
