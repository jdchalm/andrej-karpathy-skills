#!/usr/bin/env bash
# Replays the loop mechanism in a throwaway git repo so you can watch keep/revert work.
# In real use the agent proposes the ideas by reading program.md and the wiki; here the
# seven ideas are scripted so the run takes two seconds and is reproducible.
#
#   bash examples/brain/loop/demo_loop.sh
set -e
SRC="$(cd "$(dirname "$0")" && pwd)"
WORK="$(mktemp -d)"
cp -r "$SRC"/. "$WORK" && cd "$WORK"
git init -q && git config user.email loop@example.com && git config user.name loop
git add -A && git commit -qm "baseline"

printf 'commit\tscore\tstatus\tdescription\n' > results.tsv
run() { python3 eval.py > run.log 2>&1 || true; grep -o 'score=[0-9.]*' run.log | cut -d= -f2; }
best=$(run)
printf '%s\t%s\tbaseline\tstarting weights\n' "$(git rev-parse --short HEAD)" "$best" >> results.tsv

experiment() {  # $1 = description, $2 = one-line python edit of dict w
  start=$(git rev-parse --short HEAD)
  python3 -c "import json; w=json.load(open('weights.json')); $2; json.dump(w,open('weights.json','w'),indent=2)"
  git commit -qam "$1"
  s=$(run)
  if [ -z "$s" ]; then status=crash; s=0; git reset -q --hard "$start"
  elif python3 -c "import sys; sys.exit(0 if $s > $best else 1)"; then status=keep; best=$s
  else status=discard; git reset -q --hard "$start"; fi
  printf '%s\t%s\t%s\t%s\n' "$(git rev-parse --short HEAD)" "$s" "$status" "$1" >> results.tsv
}

experiment "apply wiki single-source cap: evidence capped at 3 for <=1 citation" 'w["evidence"]["single_source_cap"]=3'
experiment "steepen sentence-length slope to -0.15, base 6.5" 'w["clarity"]["base"]=6.5; w["clarity"]["per_word_per_sentence"]=-0.15'
experiment "reward a conclusion: +1.0" 'w["structure"]["conclusion_bonus"]=1.0'
experiment "raise per_citation to 1.5" 'w["evidence"]["per_citation"]=1.5'
experiment "per_paragraph 0.5, per_transition 0.3" 'w["structure"]["per_paragraph"]=0.5; w["structure"]["per_transition"]=0.3'
experiment "clarity slope -0.2, base 7.5" 'w["clarity"]["base"]=7.5; w["clarity"]["per_word_per_sentence"]=-0.2'
experiment "evidence base 0.5" 'w["evidence"]["base"]=0.5'

echo "=== results.tsv ==="; cat results.tsv
echo; echo "=== kept commits ==="; git log --oneline
echo; echo "=== final weights.json ==="; cat weights.json
echo; echo "(throwaway repo: $WORK)"
