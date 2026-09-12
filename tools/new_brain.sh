#!/usr/bin/env bash
# Scaffold a Graph / Vector / Loop brain in one command.
#
#   bash tools/new_brain.sh <folder> "<one-line description of the project>"
#   bash tools/new_brain.sh ~/code/rocket/brain "Rocket: the assessment product"
#
# Creates the folders, the schema, a program.md to fill in, an eval.py stub that
# refuses to run until you give it a real metric, and a loop driver.
set -e
DIR="${1:?folder required}"; DESC="${2:-my project}"
mkdir -p "$DIR"/raw "$DIR"/wiki "$DIR"/loop/evalset
cd "$DIR"

cat > CLAUDE.md <<'EOT'
# Brain

## 1. Think Before Coding
State assumptions. If multiple interpretations exist, present them. If unclear, ask.
## 2. Simplicity First
Minimum change that solves the problem. No speculative features or abstractions.
## 3. Surgical Changes
Touch only what you must. Match existing style. Mention unrelated dead code, do not delete it.
## 4. Goal-Driven Execution
Define success criteria. Loop until verified.

## Wiki schema
- raw/ is immutable. Never edit, rename or delete anything in it.
- Every wiki page starts with a one-line summary and a `Sources:` line linking into raw/.
- Every factual claim cites a raw/ file or another wiki page.
- When a new source contradicts an existing page, do not overwrite. Add a
  `> Contradiction:` block quoting both sides and list the page in wiki/index.md under "Disputed".
- After any ingest: update wiki/index.md, append one dated line to wiki/log.md.
- Prefer updating an existing page over creating a new one.
- Query answers that took real work become a page.

## Operations
- **ingest <raw file>**: read it, update affected pages, cross-link, update index.md, append to log.md.
- **query <question>**: read wiki/index.md first, open relevant pages, answer with citations.
- **lint**: report contradictions, stale claims, orphan pages, thin pages. Do not fix; report.
- **loop**: follow loop/program.md.
EOT

cat > wiki/index.md <<EOT
# Index

$DESC. One line per page. Read this first, then open pages.

## Overview
(none yet: run your first ingest)

## Disputed
(none)
EOT
printf '# Log\n\nAppend-only. One line per operation.\n' > wiki/log.md
printf '# raw/\n\nDrop immutable sources here: docs, PR threads, ADRs, incident reports, past outputs.\nThe agent reads these and never edits them.\n' > raw/README.md

cat > loop/program.md <<'EOT'
# Quality loop

Goal: raise `score=` as printed by `python3 eval.py` (run from this folder). Higher is better.

You may modify ONLY `TARGET`. Never touch eval.py, evalset/, ../raw/ or ../wiki/.

Before proposing a change, read ../wiki/index.md and the pages related to where evalset/ scores worst.
Ideas grounded in the wiki beat guesses.

Loop:
1. Record the current commit (`git rev-parse --short HEAD`). Make ONE change to TARGET. Commit with a one-line message.
2. Run `python3 eval.py > run.log 2>&1`. Extract `score=` from run.log.
3. Append to results.tsv: commit<TAB>score<TAB>keep|discard|crash<TAB>description
4. If score improved on the best so far in results.tsv: keep. Equal or worse: `git reset --hard` to the recorded commit.
5. Go to 1. Do NOT stop to ask if you should continue.

On crash: fix if trivial, discard if the idea is fundamentally broken. Log status crash and move on.

Ideas worth trying: FILL IN 3-5 DIRECTIONS
Ideas NOT worth trying: anything that touches evalset/; special-casing one eval item.
EOT

cat > loop/eval.py <<'EOT'
#!/usr/bin/env python3
"""Fixed evaluator. The agent never edits this file.

Must print exactly one line containing `score=<number>` where higher is better.
Replace the body with your metric. Ideas:
  - tests:     run a frozen test suite against TARGET, score = passed / total
  - agreement: apply TARGET to evalset/ items, score = 1 - mean_abs_error / range
  - speed:     time a fixed workload, score = 1 / seconds
  - agent:     for each task in evalset/, run `claude -p` with TARGET as its
               instructions in a fresh clone, score = tasks whose tests pass / total
"""
import sys
sys.exit("eval.py has no metric yet. Edit it to print score=<number>, then delete this line.")
EOT
printf 'commit\tscore\tstatus\tdescription\n' > loop/results.tsv
printf '# evalset/\n\nFrozen. Human-judged examples the loop is scored against. Never changed mid-run.\n' > loop/evalset/README.md

cat > loop/run_loop.sh <<'EOT'
#!/usr/bin/env bash
# Run the loop unattended: N iterations, each one a fresh `claude -p` call that
# does exactly one experiment. Log goes to loop.log. Stop with ctrl-c or by
# creating a file named STOP in this folder.
#
#   bash run_loop.sh 20        # twenty experiments
set -e
cd "$(dirname "$0")"
N="${1:-10}"
python3 eval.py > run.log 2>&1 || { echo "eval.py does not run yet:"; cat run.log; exit 1; }
grep -q 'score=' run.log || { echo "eval.py must print score=<number>"; exit 1; }
for i in $(seq 1 "$N"); do
  [ -f STOP ] && { echo "STOP file found"; break; }
  echo "=== experiment $i / $N  $(date '+%H:%M:%S') ===" | tee -a loop.log
  claude -p "Read program.md and results.tsv. Run exactly ONE experiment now: one change, commit, eval, log the row, keep or revert. Then stop." \
    --allowedTools "Read,Edit,Write,Bash(python3 *),Bash(git *),Bash(grep *),Bash(cat *)" \
    --permission-mode acceptEdits 2>&1 | tee -a loop.log
  tail -1 results.tsv
done
echo "=== done. best so far: ==="; sort -t$'\t' -k2 -nr results.tsv | head -1
EOT
chmod +x loop/run_loop.sh

git init -q 2>/dev/null || true
echo "created $DIR"
echo "next: put 10 sources in raw/, then:  cd $DIR && claude    and say:  ingest raw/<file>"
