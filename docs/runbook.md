# Runbook: starting a self-improving agent, literally

When, what, where, how. Every step is a command or a sentence you type into Claude Code.
Assumes a coding project (Rocket) and Claude Code installed. Total setup is under an hour.
The loop itself is the autoresearch pattern: the agent changes one file, measures one number, keeps or reverts, repeats.

## What "self-improving" means here

There are two loops, and you run them in this order:

1. **The knowledge loop.** Every piece of work the agent does gets written into a wiki it reads next time.
   It gets better because it remembers. This is Karpathy's LLM Wiki. No metric needed.
2. **The quality loop.** The agent edits one file, a metric goes up or down, git keeps or reverts.
   It gets better because it is measured. This is autoresearch. Needs a metric.

"Vector" is the retrieval step inside both: the agent finds the right page by reading the index,
and later by keyword or embedding search when the index gets big. The results of the quality loop
feed the knowledge loop, and the knowledge loop feeds the ideas for the next quality loop.
That circuit is the self-improvement.

## Day 1, hour 1: the knowledge loop

**Where.** A `brain/` folder inside the Rocket repo, or a sibling repo if you'd rather keep it out
of the product's history. One command creates it:

```bash
bash tools/new_brain.sh ~/code/rocket/brain "Rocket"
```

That writes `CLAUDE.md` (the four principles plus the wiki schema and the four operations), empty
`raw/` and `wiki/`, and a `loop/` folder with a program to fill in, an evaluator stub, and a driver.

**What goes in raw.** Ten things, today. Not a hundred. The last ten merged PR descriptions with their
review threads, any ADR or design doc, the last incident write-up, the README. Copy them in as markdown.

**How to run it.** Open Claude Code in the folder and type sentences. The operations are defined in
the brain's CLAUDE.md, so plain words work:

```
cd ~/code/rocket/brain && claude
> ingest raw/pr-1842-billing-retry.md
> ingest raw/adr-003-queue-choice.md
> query: what have we decided about retries, and where is it fragile?
> lint
```

After each ingest, read what changed in `wiki/`. If a page is wrong, correct the raw source or add a
raw note; never hand-edit the wiki, or the agent stops owning it.

**When it is working.** By the end of day 1 `wiki/index.md` lists a page per module you touched and a
page per decision, and a query about a subsystem comes back with citations into `raw/`. Add one line
to Rocket's own CLAUDE.md so every future session starts from the wiki:

```markdown
Before planning any change, read brain/wiki/index.md and the pages for the modules you will touch.
After a PR merges, ingest its description into brain/raw/ and run `ingest`.
```

That last line is the knowledge loop closing. Every PR makes the next one cheaper.

## Week 1: pick the metric

The quality loop needs one file the agent may edit and one number that goes up when it gets better.
Pick from this table. Start with the first row that applies.

| TARGET, the one file | eval.py prints | Cost per experiment |
|---|---|---|
| the flakiest test file | pass rate over 20 repeated runs | seconds |
| one slow module | benchmark time on a fixed workload | seconds to minutes |
| build or lint config | build time, bundle size, warning count | a minute |
| a prompt Rocket sends to a model | agreement with 30 human-graded outputs | API calls per item |
| the agent's own CLAUDE.md or a skill | share of 10 fixed tasks it completes with tests green | one full agent run per task, expensive |

The last row is the literal self-improving agent: the agent editing its own instructions against a
task set. It is also the most expensive per experiment, so do it last, after the loop mechanism has
proved itself on a cheap row.

**Where.** `brain/loop/`. Put the frozen inputs in `evalset/`. Write `eval.py` so it prints one line
containing `score=<number>`. Run it twice by hand and get the same number. Record that as the baseline
row in `results.tsv`. Then fill the blanks in `program.md`: the TARGET path and three to five ideas
worth trying.

## Week 1, night 1: run the quality loop

Two ways. Use the first to watch it, the second to leave it.

**Interactive.** One session, the agent loops itself, you watch:

```
cd ~/code/rocket/brain/loop && claude
> follow program.md until I stop you
```

**Unattended.** Each experiment is a fresh `claude -p` call so a bad turn cannot poison the next:

```bash
cd ~/code/rocket/brain/loop && bash run_loop.sh 30
```

The driver refuses to start until `eval.py` prints a score, tails `results.tsv` after each run, and
stops early if you create a file named `STOP`. Everything goes to `loop.log`.

**Next morning.** Read `results.tsv`. Read every kept commit's diff (`git log -p` on the loop folder).
Merge the kept diffs into Rocket by hand, through a normal PR. Never auto-promote.

## Closing the circuit

This is the step that makes it self-improving rather than just automated. After each overnight run:

```
cd ~/code/rocket/brain && claude
> ingest loop/results.tsv as a decisions page: what was tried on TARGET, what was kept, what was reverted and why
```

Now the next run's program.md line "read the wiki before proposing" points the agent at its own
history. Reverted ideas stop being retried. Kept ideas get generalised. Change TARGET to the next row
of the table and go again.

## Schedule

| When | What | How long |
|---|---|---|
| after every merged PR | ingest its description | one sentence, one minute |
| weekly | lint | one sentence, five minutes to read the report |
| nightly, once a metric exists | `run_loop.sh 30` | hands-off |
| each morning after a run | read kept diffs, ingest results | fifteen minutes |
| monthly | ask whether the index is too big to read; add search then, not before | five minutes |

## When to add vector search

Only when `query` starts missing pages that exist, which usually means `wiki/index.md` is past a few
hundred lines. Then point `tools/search.py` at the wiki and add one line to CLAUDE.md telling the agent
to run it before opening pages. Swapping in real embeddings is a one-function change described in
`retrieval-primer.md`.

## Things that break this

- Two metrics. The agent optimises the easier one.
- Letting the agent edit `eval.py` or `evalset/`. It will make the test easier.
- Hand-editing the wiki. The agent stops trusting it and starts re-deriving.
- Skipping the morning read. Kept diffs are proposals, not merges.
- Starting with the expensive row. Prove the mechanism on a test file first.
