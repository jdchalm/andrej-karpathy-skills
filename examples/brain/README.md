# Example brain: essay assessment

A complete, tiny Graph / Vector / Loop system you can read in five minutes and run in one.
Domain is essay assessment on a three-criterion rubric. Swap the domain and the shape holds.

```
examples/brain/
├── CLAUDE.md          schema + the three operations
├── raw/               5 immutable sources: rubric, 3 assessments, 1 calibration note
├── wiki/              10 pages the agent maintains: index, log, overview, 3 criteria, 3 cases, 1 decision
└── loop/              eval.py (fixed), evalset/ (frozen), weights.json (the ONE file the agent edits),
                       program.md, results.tsv (a real run), demo_loop.sh (replay it)
```

## See each layer work

**Graph.** Read `wiki/index.md`, then `wiki/criteria/evidence.md`. The `> Contradiction` block is what
ingesting `raw/feedback/reviewer-note-2026-08.md` produced: it disagrees with `raw/assessments/essay-002.md`,
and the wiki kept both sides and linked the decision that resolved it. `wiki/log.md` shows the five ingests
and one lint that built this.

**Vector.** Rank the wiki three ways with the stdlib search script:

```bash
python3 tools/search.py examples/brain/wiki "single source evidence cap" --mode hybrid
python3 tools/search.py examples/brain/wiki "why was essay-003 returned" --mode bm25
```

The second query is a good lesson: BM25 ranks essay-001 first because "returned" appears there twice.
Reading `index.md` gets it right immediately. That is why the index is the first retrieval step and
search is the later speed-up.

**Loop.** Replay a seven-experiment run in a throwaway git repo:

```bash
bash examples/brain/loop/demo_loop.sh
```

Two of seven ideas are kept, five are reverted, agreement rises from 0.8917 to 0.9250. `results.tsv`
is the record of the run that produced those numbers. Note the first idea, applying the wiki's
single-source cap, changed nothing on its own: the baseline weights already scored one citation at 2.
The loop tells you that in one line instead of a meeting.

## Play with it

- **Ingest.** Add a file to `raw/assessments/` describing a fourth essay. Open Claude Code in this folder
  and say: `ingest raw/assessments/essay-004.md`. Watch which wiki pages change and what lands in log.md.
- **Query.** `query: which criterion do we dispute most, and what did we decide?` Expect citations.
- **Lint.** `lint`. Expect the open question in overview.md and nothing else.
- **Loop, by hand.** Edit one number in `loop/weights.json`, run `python3 loop/eval.py`, decide keep or revert.
  Then let the agent do it: open Claude Code in `loop/` and say `follow program.md`.

## Adapt it

Replace the five raw files with ten of your own, rewrite the three criteria pages, and change
`eval.py` to compute your metric. Everything else, including `program.md`, is reusable as-is.
