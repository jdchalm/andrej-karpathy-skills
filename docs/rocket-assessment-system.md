# A simple Graph / Vector / Loop system for Rocket Assessment

A proposal for one small git repo that turns Rocket Assessment work into knowledge that compounds and a
quality loop that runs unattended. It combines three Karpathy patterns with the four principles already in
this repo's `CLAUDE.md`.

## Assumptions (say if any are wrong)

1. **Rocket Assessment** is your own assessment product or process: it takes some input (a submission,
   a candidate, a company, a document), applies criteria, and produces a scored write-up. It has no public
   footprint, so this doc treats it as a black box with three things we can point at: raw material,
   criteria, and finished assessments.
2. **Graph** means Karpathy's *LLM Wiki* pattern (April 2026 gist): an LLM-maintained set of linked
   markdown pages compiled from immutable raw sources.
3. **Vector** means embedding-based retrieval (RAG). Karpathy's position is that you do not need it until
   the wiki is large; the index file is the retrieval layer at moderate scale.
4. **Loop** means his *autoresearch* pattern (March 2026): an agent changes one file, runs a fixed-budget
   experiment, keeps the change if one metric improves, reverts otherwise, and never stops to ask.
5. "Help us in the future" means the payoff is accumulation, so everything below is designed to be
   appended to, not rebuilt.

## The system in one picture

```
rocket-assessment-brain/            one git repo, plain files, no services
├── CLAUDE.md                       the schema: this repo's 4 principles + the rules below
├── raw/                            GRAPH input. Immutable. Never edited by the agent.
│   ├── assessments/                finished Rocket Assessments (the good, the bad, the revised)
│   ├── criteria/                   rubrics, scoring guides, versioned
│   └── feedback/                   client pushback, reviewer notes, post-mortems
├── wiki/                           GRAPH. Owned entirely by the agent.
│   ├── index.md                    catalog of every page with a one-line summary
│   ├── log.md                      append-only: every ingest / query / lint, dated
│   ├── overview.md                 what Rocket Assessment is, current state of play
│   ├── criteria/<criterion>.md     one page per criterion: intent, examples, edge cases, disputes
│   ├── cases/<assessment>.md       one page per assessment: what was decided and why
│   └── decisions/<topic>.md        synthesised answers that were worth keeping
└── loop/                           LOOP. Autoresearch, aimed at assessment quality.
    ├── program.md                  the experiment instructions (humans edit this, nothing else)
    ├── eval.py                     fixed. Scores a frozen set and prints ONE number.
    ├── evalset/                    frozen: ~30 human-graded items. Never changes mid-run.
    ├── prompt.md                   the thing under test. The ONLY file the agent may modify.
    └── results.tsv                 commit, metric, status (keep/discard/crash), description
```

No vector database. No orchestration framework. No dashboard. Three folders and four operations.

## Layer 1: Graph (the wiki)

**Why.** Today each assessment is re-derived from scratch. The wiki makes the second assessment cheaper
than the first because, in Karpathy's words, "the cross-references are already there. The contradictions
have already been flagged."

**What the pages are.** For an assessment business the graph has three natural node types:

| Page type | One page per | What it holds |
|-----------|--------------|---------------|
| `criteria/` | scoring criterion | plain-language intent, 2-3 real examples per score band, known edge cases, links to cases that argued about it |
| `cases/` | finished assessment | inputs, final scores, the reasoning that mattered, what got revised after feedback |
| `decisions/` | recurring question | a synthesised answer with citations back to `raw/` and to the criteria/cases it drew on |

Pages link to each other with ordinary markdown links. `index.md` lists every page with a one-line
summary. That index, not an embedding search, is the first thing the agent reads on any question.

**Three operations, run by the agent under the schema in CLAUDE.md:**

- **Ingest.** Drop a new file into `raw/`, ask the agent to ingest it. It reads the source, updates or
  creates the affected criteria, case and decision pages, adds cross-links, notes where the new source
  contradicts an existing page, updates `index.md`, appends to `log.md`.
- **Query.** Ask a question. The agent reads `index.md`, opens the relevant pages, answers with citations.
  If the answer took real work, it becomes a `decisions/` page so nobody derives it again.
- **Lint.** Weekly. The agent looks for contradictions between pages, stale claims, orphan pages with no
  inbound links, criteria with no examples. Output is a short list for a human to act on.

**Schema rules to put in CLAUDE.md** (add below the four principles):

```markdown
## Wiki schema
- raw/ is immutable. Never edit, rename or delete anything in it.
- Every wiki page starts with a one-line summary and a `Sources:` line linking into raw/.
- Every claim about a criterion or a score cites a raw/ file or a cases/ page.
- When a new source contradicts an existing page, do not silently overwrite. Add a
  `> Contradiction:` block quoting both and link the page from index.md under "Disputed".
- After any ingest: update index.md, append one dated line to log.md.
- Prefer updating an existing page over creating a new one.
```

## Layer 2: Vector (retrieval), deliberately deferred

Karpathy is explicit: "at moderate scale (~100 sources, ~hundreds of pages)" the index file "works
surprisingly well" and "avoids the need for embedding-based RAG infrastructure." Rocket Assessment will
be well under that for a long time.

**Trigger to add it.** Any one of these:

- `index.md` passes roughly 300 entries and the agent starts missing relevant pages on queries.
- `raw/` fills with long PDFs whose content is not adequately summarised into the wiki.
- You want to search the raw sources themselves, not the wiki.

**What to add when triggered.** A local hybrid search over markdown, nothing more. Karpathy points to
`qmd` (local BM25 + vector over markdown files). A 40-line script over SQLite with an embeddings column
does the same job. Either way it plugs in as a fourth operation the agent can call. It does not replace
the wiki; the wiki stays the compiled artifact and vector search is just a faster way to find pages.

Applying this repo's Simplicity First principle: building this on day one is the classic speculative
feature. Do not.

## Layer 3: Loop (autoresearch for assessment quality)

**Why.** This is the part that improves Rocket Assessment while you sleep, and it is where this repo's
Goal-Driven Execution principle ("define success criteria, loop until verified") becomes a mechanism
instead of advice.

**The five parts, copied from autoresearch and renamed:**

| autoresearch | Rocket Assessment loop | Rule |
|--------------|------------------------|------|
| `train.py` | `loop/prompt.md` | the only file the agent may change: the assessment prompt, rubric wording, few-shot examples |
| `prepare.py` | `loop/eval.py` + `loop/evalset/` | fixed. Runs the prompt over the frozen set and prints one number |
| 5-minute budget | N items from the eval set | fixed cost per experiment, so results are comparable |
| `val_bpb` | your one metric | see below |
| `program.md` | `loop/program.md` | the instructions; the only thing humans touch during a run |

**The metric is the whole design decision.** Pick one number that goes up when Rocket Assessment gets
better. Candidates, best first:

1. **Agreement with human graders** on the frozen set (weighted kappa or mean absolute score error).
   Directly measures "is the assessment right."
2. **Revision rate**: share of items whose automated write-up a human accepts without edits.
3. **Rubric coverage**: share of criteria the write-up addresses with a cited reason.

Start with 1 if you have human-graded assessments. If you do not, building 30 of them is the first
task, and it is worth more than any tooling.

**The loop, per experiment.** Verbatim from autoresearch, adapted:

1. Note the current commit.
2. Edit `prompt.md` with one idea. Commit.
3. Run `python loop/eval.py > run.log 2>&1`.
4. Grep the metric out of the log.
5. On crash: fix if trivial, discard if the idea is fundamentally broken. Log status `crash`.
6. Append one row to `results.tsv`: commit, metric, status, one-line description.
7. If the metric improved, keep the commit. If equal or worse, `git reset` to the noted commit.
8. Repeat. Do not pause to ask whether to continue.

**Starter `loop/program.md`:**

```markdown
# Rocket Assessment quality loop

Goal: raise the score printed by `python loop/eval.py` (higher is better).

You may modify ONLY `loop/prompt.md`. Never touch eval.py, evalset/, raw/ or wiki/.

Before proposing a change, read `wiki/index.md` and the `wiki/criteria/` pages for the
criteria the eval set scores worst on. Ideas grounded in the wiki beat guesses.

Loop:
1. Record current commit. Make ONE change to prompt.md. Commit with a one-line message.
2. Run `python loop/eval.py > run.log 2>&1`. Extract `score=` from run.log.
3. Append to results.tsv: commit<TAB>score<TAB>keep|discard|crash<TAB>description
4. Improved: keep. Equal or worse: `git reset --hard` to the recorded commit.
5. Go to 1. Do NOT stop to ask if you should continue.

Ideas worth trying: reorder criteria, add a worked example from wiki/cases, tighten a
score-band definition, ask for evidence before verdict, remove instructions that never
change the output.

Ideas NOT worth trying: anything that changes the eval set, anything that special-cases
a specific eval item.
```

## How the three layers feed each other

- **Wiki feeds the loop.** `program.md` tells the agent to read `wiki/criteria/` before proposing a change,
  so experiments come from accumulated understanding of where assessments go wrong.
- **Loop feeds the wiki.** After each overnight run, ingest `results.tsv` and the kept diffs into
  `wiki/decisions/prompt-changes.md`: what worked, what did not, why. Discarded ideas are knowledge too.
- **Finished assessments feed both.** Every real assessment goes into `raw/assessments/`, gets ingested
  into `wiki/cases/`, and the human-graded ones become candidates for the next frozen eval set.
- **Vector search, when added, just speeds up the reads** in all three of the above.

## Three-week start plan, with verification

Following this repo's Goal-Driven Execution format:

1. **Week 1: Graph.** Create the repo, copy this repo's `CLAUDE.md` in, add the wiki schema block.
   Put 10-20 past assessments and the current criteria into `raw/`. Run one ingest.
   Verify: `index.md` lists a page per criterion and per case. Ask "which criterion do we revise most
   often and why?" and get an answer with citations into `raw/`.
2. **Week 2: Metric.** Build `evalset/` from 30 human-graded items. Write `eval.py` to print one
   number. Verify: run it twice on the same `prompt.md` and get the same number. Record that
   baseline in `results.tsv`.
3. **Week 3: Loop.** Write `program.md` from the starter above. Run the agent overnight.
   Verify: `results.tsv` has at least 10 rows and at least one `keep`. Read every kept diff.
4. **Ongoing.** Weekly lint. Ingest each loop run. Add the metric to whatever you already report.
   Verify: the kept-commit metric is higher than the week-2 baseline a month later.

## What not to build

- A vector database or RAG pipeline before the trigger in Layer 2 fires.
- A UI. Markdown in git, read through Claude Code, is the UI.
- Multi-agent orchestration. One agent, one file it may change, one metric.
- Multiple metrics. The moment there are two, the agent optimises the easier one.
- Automatic promotion of a kept `prompt.md` to production. A human reads the diff.

## Open questions for you

None of these block starting Week 1, but they shape Weeks 2 and 3:

1. What is the concrete unit of a Rocket Assessment, and where do finished ones live today?
2. Do human-graded assessments already exist, or does the eval set need to be built?
3. Which of the three metric candidates matches how you already judge quality?
4. Who owns `program.md`? Autoresearch works because exactly one person edits it.

## Sources

- Karpathy, *llm-wiki* gist (April 2026): https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f
- Karpathy, *autoresearch* (March 2026): https://github.com/karpathy/autoresearch
- This repo's `CLAUDE.md`: the four principles the schema and program build on.
