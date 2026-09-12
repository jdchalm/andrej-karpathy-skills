# Project Brain: a Graph / Vector / Loop template for any project

The same three-layer system as `rocket-assessment-system.md`, with the Rocket-specific parts pulled out
into five blanks you fill in. Copy this file into a new repo, fill the blanks, delete this paragraph.

## Fill these in first

| Blank | Question it answers | Rocket Assessment example |
|-------|---------------------|---------------------------|
| **PROJECT** | What is this brain for? | Rocket Assessment |
| **UNIT** | What is the one thing the project produces, over and over? | a scored assessment write-up |
| **SOURCES** | What raw material already exists? Where? | past assessments, rubrics, client feedback |
| **NODE TYPES** | What are the 2-4 kinds of thing worth a wiki page each? | criterion, case, decision |
| **METRIC** | One number that goes up when UNIT gets better | agreement with human graders |

If you cannot fill METRIC, you can still run Graph. Loop waits until you can.

## Layout

```
PROJECT-brain/
├── CLAUDE.md                 the four principles + the schema block below
├── raw/                      GRAPH input. Immutable. One subfolder per SOURCES kind.
├── wiki/                     GRAPH. Owned by the agent.
│   ├── index.md              every page, one-line summary each
│   ├── log.md                append-only, dated: ingest | query | lint
│   ├── overview.md           what PROJECT is, current state
│   └── <node-type>/*.md      one folder per NODE TYPE
├── tools/
│   └── search.py             VECTOR. Only wired in once the wiki outgrows index.md.
└── loop/                     LOOP. Only once METRIC exists.
    ├── program.md            experiment instructions. Humans edit this and nothing else during a run.
    ├── eval.py               fixed. Prints one number: METRIC.
    ├── evalset/              frozen. Human-judged examples of UNIT.
    ├── <target>              the ONE file the agent may modify (a prompt, a config, a rubric, a script)
    └── results.tsv           commit  metric  keep|discard|crash  description
```

## Layer 1: Graph

Copy into `CLAUDE.md` under the four principles, replacing the capitals:

```markdown
## Wiki schema
- raw/ is immutable. Never edit, rename or delete anything in it.
- Page folders: NODE TYPES. Prefer updating an existing page over creating a new one.
- Every page starts with a one-line summary and a `Sources:` line linking into raw/.
- Every factual claim cites a raw/ file or another wiki page.
- When a new source contradicts an existing page, do not overwrite. Add a
  `> Contradiction:` block quoting both sides and list the page in index.md under "Disputed".
- After any ingest: update index.md, append one dated line to log.md.
- Query answers that took real work become a page in the most relevant NODE TYPE folder.
```

Operations, unchanged from Karpathy's gist:

- **Ingest**: new file in `raw/`, agent reads it, updates pages, cross-links, index, log.
- **Query**: agent reads `index.md` first, then pages, answers with citations.
- **Lint**: weekly. Contradictions, stale claims, orphans, missing cross-links, thin pages.

## Layer 2: Vector

Do nothing until one of these is true:

- `index.md` is past ~300 lines and queries start missing pages.
- `raw/` holds long documents the wiki only summarises.
- You want to search raw sources, not the wiki.

Then wire in `tools/search.py` (see `retrieval-primer.md`) as a fourth operation the agent may call,
or swap it for a real embedding model or `qmd`. The wiki stays the artifact; search just finds pages.

## Layer 3: Loop

Copy into `loop/program.md`, replacing the capitals:

```markdown
# PROJECT quality loop

Goal: raise METRIC as printed by `python loop/eval.py` (higher is better).

You may modify ONLY `loop/TARGET`. Never touch eval.py, evalset/, raw/ or wiki/.

Before proposing a change, read wiki/index.md and the pages most related to where
evalset/ scores worst. Ideas grounded in the wiki beat guesses.

Loop:
1. Record current commit. Make ONE change to TARGET. Commit with a one-line message.
2. Run `python loop/eval.py > run.log 2>&1`. Extract `score=` from run.log.
3. Append to results.tsv: commit<TAB>score<TAB>keep|discard|crash<TAB>description
4. Improved: keep. Equal or worse: `git reset --hard` to the recorded commit.
5. Go to 1. Do NOT stop to ask if you should continue.

On crash: fix if trivial (typo, import), discard if the idea is fundamentally broken.
Log it with status crash and move on. Only stop on repeated identical crashes.

Ideas worth trying: [3-5 directions specific to PROJECT]
Ideas NOT worth trying: anything that touches evalset/, anything that special-cases one eval item.
```

Rules that make it work, from autoresearch:

- One file the agent may change. Diffs stay reviewable.
- One number. Two metrics and the agent optimises the easier one.
- Fixed cost per experiment, so runs are comparable.
- Keep or revert through git. Nothing else tracks state.
- A human reads every kept diff before it goes anywhere real.

## Three worked adaptations

| Blank | Rocket Assessment | A codebase | A reading list |
|-------|-------------------|------------|----------------|
| UNIT | scored write-up | a merged PR | a written summary of a paper |
| SOURCES | assessments, rubrics, feedback | ADRs, incident reports, PR discussions | PDFs, notes, talks |
| NODE TYPES | criterion, case, decision | module, decision, incident | paper, concept, author |
| METRIC | grader agreement | test pass rate on a fixed suite | (none yet: Graph only) |
| TARGET | prompt.md | one config or one module | n/a |

## Start here, in order

1. Create the repo. Copy in `CLAUDE.md`. Fill the five blanks. Add the schema block.
   Verify: `CLAUDE.md` has no capitals left in the schema.
2. Put 10-20 real SOURCES in `raw/`. Run one ingest.
   Verify: `index.md` has a page per NODE TYPE instance you'd expect. Ask one real question, get citations.
3. Weekly lint for a month before touching Loop.
   Verify: lint output shrinks week over week.
4. Only if METRIC exists: build `evalset/` and `eval.py`. Run it twice, same number.
5. Write `program.md`. Run overnight. Read every kept diff.
