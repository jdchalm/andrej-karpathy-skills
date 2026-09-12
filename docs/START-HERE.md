# Start here: the whole system in one place

Everything built in this session, what each piece is for, how to run it, how a normal coding day
looks with it, and how to roll it out at work. Read top to bottom once; after that, use the tables.

## 1. What this is, in one paragraph

A small, file-based way to make an AI coding agent (Claude Code) get better at your project over time.
It has three parts, named after the Karpathy ideas they come from. **Graph** is a wiki of linked markdown
pages the agent writes and maintains from your raw documents, so it remembers instead of re-deriving.
**Vector** is search over that wiki, deferred until the wiki is too big to read whole. **Loop** is an
experiment cycle where the agent edits one file, measures one number, and keeps or reverts through git.
The self-improvement comes from wiring them together: what the loop learns gets written into the wiki,
and the wiki feeds the loop's next ideas.

## 2. How it works, plainly

There is no service, no database, no framework. There is a folder:

```
brain/
├── CLAUDE.md    rules the agent follows + four operations it understands: ingest, query, lint, loop
├── raw/         documents you drop in. The agent reads them, never edits them.
├── wiki/        pages the agent writes. index.md lists them all. log.md records every operation.
└── loop/        one file the agent may change, a script that scores it, a table of what was tried.
```

The agent is Claude Code opened in that folder. You type sentences. The CLAUDE.md file tells it what
"ingest", "query", "lint" and "loop" mean, so plain words work.

| You type | The agent does | What changes on disk |
|---|---|---|
| `ingest raw/x.md` | reads x, updates or creates wiki pages, adds links, flags contradictions | wiki pages, index.md, log.md |
| `query: ...` | reads index.md, opens the right pages, answers with citations, saves real work as a page | maybe one new wiki page, log.md |
| `lint` | lists contradictions, stale claims, orphan pages, thin pages | nothing; it reports |
| `follow program.md` | changes the one target file, runs the scorer, logs a row, keeps or reverts | target file, results.tsv, git history |

**Why it improves.** Three mechanisms, in the order you switch them on:

1. **Memory.** Session two reads the wiki that session one wrote. Nothing is re-derived.
2. **Measurement.** The loop cannot keep a change that made the number worse. Git reverts it.
3. **The circuit.** Each morning the loop's results.tsv is ingested into the wiki as a decisions page.
   The next night's loop reads it before proposing, so reverted ideas are not retried.

**Where "vector" fits.** It is how the agent finds the right page. On day one that is reading index.md.
Later, when the index is too long to read, it is keyword search (BM25), embedding search (vectors), or
both (hybrid). The retrieval primer explains each; the search script demonstrates them.

## 3. A day in the life, coding

This is what changes in an ordinary week on a codebase like Rocket.

**Starting a task.** Rocket's CLAUDE.md says: read `brain/wiki/index.md` and the pages for the modules
you will touch before planning. So the agent's plan already knows the retry decision from ADR-003,
the incident that made the queue module fragile, and the test that is flaky on CI. You did not paste
any of that in.

**During the task.** Nothing changes. The agent works as it does today, under the four principles
already in this repo.

**When the PR merges.** One sentence: `ingest raw/pr-1842.md` after dropping the PR description and
review thread into raw. The module and decision pages update. The next person, or the next agent
session, inherits it.

**At night, once a metric exists.** `bash brain/loop/run_loop.sh 30`. The agent runs thirty
experiments against the one target file you chose, say the flakiest test file, scored by the one
number you chose, say pass rate over twenty runs. It commits what helped and reverts what did not.

**Next morning.** Fifteen minutes. Read results.tsv. Read the kept diffs. Open a normal PR with the
ones you agree with. Then `ingest loop/results.tsv as a decisions page`. That closes the circuit.

**Weekly.** `lint`. Read the short report. Fix raw sources, not wiki pages.

**Monthly.** Is the index too long to read comfortably? If yes, turn on search. If no, do nothing.

## 4. What was built

### Pages, for reading and sharing

| Page | What it is for |
|---|---|
| [Rocket Assessment Brain](https://claude.ai/code/artifact/09383a6a-daab-49bd-bdb0-38ad7478303a) | the original proposal, applied to Rocket as an assessment product |
| [Project Brain Template](https://claude.ai/code/artifact/bea40238-08a6-455f-8ff2-1f35da593521) | the same system with five blanks, adaptable to any project |
| [Retrieval Primer](https://claude.ai/code/artifact/c737ff3f-0b17-4392-9a78-6c7145837688) | BM25, embeddings, hybrid search, where the graph fits, RAG vs wiki |
| [Brain Playground](https://claude.ai/code/artifact/9c210958-0eb1-4c42-94b7-d256dc4def80) | operate a complete tiny brain in the browser: browse, search, run the loop |
| [Self-Improving Agent Runbook](https://claude.ai/code/artifact/07f41751-91f2-48c1-b709-c1c65147731a) | when, what, where, how, for a coding project |

### Files in the repo, branch `claude/youthful-ptolemy-3odxmx`

| Path | What it is | How to run it |
|---|---|---|
| `docs/rocket-assessment-system.md` | proposal, Rocket version | read |
| `docs/project-brain-template.md` | proposal, generic version with blanks | copy into a new repo, fill blanks |
| `docs/retrieval-primer.md` | concepts | read |
| `docs/runbook.md` | literal steps for a coding project | follow |
| `docs/START-HERE.md` | this file | read |
| `tools/search.py` | BM25 / vector / hybrid ranker over any folder of markdown, no dependencies | `python3 tools/search.py <folder> "<query>" --mode hybrid` |
| `tools/new_brain.sh` | scaffolds a complete brain in one command | `bash tools/new_brain.sh <folder> "<name>"` |
| `examples/brain/` | a finished brain for essay assessment: 5 raw sources, 10 wiki pages with a flagged contradiction, a working loop | see its README |
| `examples/brain/loop/demo_loop.sh` | replays a seven-experiment loop with real git keep/revert in a throwaway repo | `bash examples/brain/loop/demo_loop.sh` |
| `examples/brain/loop/results.tsv` | the record of that run: 2 kept, 5 reverted, 0.8917 to 0.9250 | read |
| `examples/brain/loop/run_loop.sh` | the unattended driver: N fresh `claude -p` calls, one experiment each | `bash run_loop.sh 20` from inside a loop folder |

### What was verified

- The search script ranks correctly in all three modes over this repo and over the example wiki.
- The demo loop reproduces the committed results.tsv exactly.
- The scaffold script creates a working brain and its driver refuses to run until eval.py has a metric.
- The unattended driver ran one real experiment with `claude -p` against the example brain: see the
  line at the bottom of this file.

## 5. Ten-minute tour

```bash
git fetch origin claude/youthful-ptolemy-3odxmx && git checkout claude/youthful-ptolemy-3odxmx

# graph: read a wiki the agent would produce, including a contradiction it kept visible
cat examples/brain/wiki/index.md
cat examples/brain/wiki/criteria/evidence.md

# vector: rank the wiki three ways, and see BM25 get one wrong
python3 tools/search.py examples/brain/wiki "single source evidence cap" --mode hybrid
python3 tools/search.py examples/brain/wiki "why was essay-003 returned" --mode bm25

# loop: watch keep/revert happen with real commits
bash examples/brain/loop/demo_loop.sh

# make your own
bash tools/new_brain.sh ~/code/rocket/brain "Rocket"
```

## 6. Rolling it out as CTO

**Principle.** This is a habit with a folder, not a platform. Roll it out like a coding convention,
not like a tool purchase. There is nothing to buy, host, or integrate.

**Week 1: one repo, one owner.** Pick the repo with the most tribal knowledge and one engineer who
already uses Claude Code daily. They run `new_brain.sh`, ingest the last twenty PRs and every ADR,
and add the two lines to that repo's CLAUDE.md. Success: a new engineer, or a fresh agent session, can
ask "why is X like this" and get a cited answer.

**Weeks 2 to 4: the cheap loop.** Same engineer picks the flakiest test file or slowest build step,
writes a five-line eval.py, and runs the loop three nights. Success: at least one kept diff merged
through a normal PR, and results.tsv ingested into the wiki. If nothing is kept, that is also a
finding: the target was not where the slack is.

**Month 2: second repo, and the review habit.** A second team copies the pattern. Add "ingest the PR"
to the definition of done. Add "read the wiki" to the PR template's checklist for agent-assisted PRs.
Weekly lint goes on one person's calendar.

**Month 3: the expensive loop, if earned.** Only now, and only if the cheap loops paid off, point the
loop at the agent's own CLAUDE.md or a skill file, scored against ten fixed tasks. This is the literal
self-improving agent and it costs an agent run per task per experiment. Budget it.

**What to measure.** Two numbers, both cheap:

- Time from "new engineer or new session" to a correct answer about a subsystem. Should drop.
- Count of kept diffs merged per month from the loop. Should be nonzero and reviewed.

**Who owns what.**

| Role | Owns |
|---|---|
| one engineer per repo | raw/ hygiene, weekly lint, morning read after loop runs |
| tech lead | which target and metric the loop points at; reads every kept diff |
| CTO | the two lines in CLAUDE.md are non-negotiable; the loop never auto-merges |

**Cost.** The wiki costs agent tokens per ingest, a few cents to a few dollars a day per repo. Cheap
loops cost seconds of compute per experiment plus one agent call. The expensive loop is the only line
item worth a budget conversation.

**Risks and the rule that covers each.**

| Risk | Rule |
|---|---|
| the wiki drifts from the code | hand-edit raw, never wiki; weekly lint |
| the loop games the metric | agent never edits eval.py or evalset/; one metric only |
| a kept diff ships unread | kept diffs are proposals; a human opens the PR |
| secrets in raw/ | raw is source material; treat it like the repo, same access rules |
| people skip ingest | make it a definition-of-done item, not a favour |

**What not to do in the first quarter.** Do not build a vector database. Do not build a dashboard.
Do not run multiple agents. Do not let the loop touch production config. Do not start with the
expensive loop.

## 7. Glossary

| Term | Meaning here |
|---|---|
| graph | the wiki: pages linked to each other; links carry *why* two things relate |
| vector | representing text as numbers so similarity is a distance; used for search |
| loop | change one file, measure one number, keep or revert, repeat |
| BM25 | keyword ranking: rare words in short documents score highest |
| embedding | a vector from a model that puts similar meanings close together |
| hybrid | keyword and vector search merged by rank |
| RAG | search raw docs on every question and paste chunks into the prompt; no memory between questions |
| wiki | the agent-maintained pages; the thing RAG lacks |
| ingest / query / lint | the three wiki operations |
| raw/ | immutable sources the agent reads |
| index.md | one line per wiki page; the agent's first retrieval step |
| log.md | append-only record of every operation |
| target | the one file the loop may edit |
| metric | the one number eval.py prints, higher is better |
| evalset | frozen human-judged examples the metric is computed against |
| program.md | the loop's instructions; the only thing a human edits during a run |
| results.tsv | commit, score, keep/discard/crash, description, one row per experiment |
| keep / revert | git keeps the commit if the metric rose, resets it otherwise |
| CLAUDE.md | the agent's standing instructions; here it also defines the four operations |

## 8. An AI Center of Excellence, Microsoft Scout, and whether to build your own

**What Scout is.** Microsoft's first "Autopilot": an always-on agent with its own governed Entra identity,
grounded in Teams, Outlook, OneDrive and SharePoint, that "builds context powered by Work IQ, learning
how you work." Purview labels and loss prevention are enforced before it reads or writes. It is built
on OpenClaw, an open-source local-agent platform, and needs Frontier enrollment, Intune policy, an opt-in
attestation, and a GitHub Copilot license for the desktop piece.

**How it relates to the brain.** Scout's memory is Work IQ: a graph Microsoft builds from your tenant,
that you cannot read, lint, or move. The brain is memory you own: markdown in git, readable, lintable,
vendor-neutral. They are complementary. Scout is the personal work agent for the office side, calendar,
email, meetings. The brain is project memory for the engineering side. The bridge is simple: keep the
wiki folder somewhere Scout is allowed to read, a SharePoint-synced folder or a repo its GitHub Copilot
license can see, and both agents read the same source of truth. Nothing else needs integrating.

**What the CoE owns.** Not a platform. Four standards and one folder:

| The CoE owns | Concretely |
|---|---|
| the schema | the wiki rules block in CLAUDE.md, versioned, one copy every team uses |
| the scaffold | `tools/new_brain.sh`, so every brain has the same shape |
| the metric catalog | the table of allowed targets and metrics; teams pick, the CoE approves new rows |
| the review rules | never auto-merge, never edit eval.py, one metric, morning read |
| the CoE brain | a brain whose raw/ is every team's decisions pages and lint reports: the graph of graphs |

Memory policy sits with the CoE too: what may enter raw (no secrets, same access rules as the repo),
retention, who may ingest, and which wiki folders Scout is allowed to read.

**Should you build a Claude-based Scout?** Not now, and not as a product. Three reasons:

1. Scout's value is the Microsoft 365 plumbing: identity, Purview, Intune, the data connectors. That is
   a platform play you cannot cheaply replicate and would not want to maintain.
2. The part worth owning is the memory, and that is already vendor-neutral. A brain works with Scout,
   with Claude Code, and with whatever comes next.
3. The always-on behaviour you want on the engineering side is already available: a Claude Code
   Routine that runs `ingest`, `lint`, and `run_loop.sh` on a schedule, reading the same wiki. That is
   a scheduled command, not a product.

So: build the memory, rent the autopilots. Revisit only if Frontier's terms or data residency do not fit,
or if you need the agent to run inside your own environment. In that case the honest option is OpenClaw
itself, which is open source and is what Scout is built on, pointed at Claude. That is a real project,
and it is the CoE's call after the cheap loops have paid for themselves, not before.

Sources: [Introducing Microsoft Scout](https://www.microsoft.com/en-us/microsoft-365/blog/2026/06/02/introducing-microsoft-scout-your-always-on-personal-agent/), Microsoft 365 Blog, June 2026.

## Live test

The unattended driver was run for real against the example brain with `bash run_loop.sh 1`. A fresh `claude -p` session read program.md, tried one change (the wiki's single-source cap, 5 to 3), ran eval.py, found the score unchanged at 0.8917, logged a discard row explaining that the cap never binds under the baseline formula, and reset git to the baseline commit. Total time about three minutes. The agent also flagged that the example's committed results.tsv references commits from a throwaway repo, which is true and is explained in the example's README.
