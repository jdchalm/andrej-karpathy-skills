# Essay assessment quality loop

Goal: raise `score=` as printed by `python eval.py` (run from this folder). Higher is better.
The score is agreement between the rule-based scorer in weights.json and human scores on the frozen eval set.

You may modify ONLY `weights.json`. Never touch eval.py, evalset/, ../raw/ or ../wiki/.

Before proposing a change, read `../wiki/index.md` and the criteria pages. The wiki already records
rules the humans apply (for example the single-source cap on evidence, and that sentence length
drags clarity down). Ideas grounded in the wiki beat guesses.

Loop:
1. Record the current commit. Make ONE change to weights.json. Commit with a one-line message.
2. Run `python eval.py > run.log 2>&1`. Extract `score=` from run.log.
3. Append to results.tsv: commit<TAB>score<TAB>keep|discard|crash<TAB>description
4. Improved: keep. Equal or worse: `git reset --hard` to the recorded commit.
5. Go to 1. Do NOT stop to ask if you should continue.

On crash: fix if trivial (a typo in the JSON), discard if the idea is fundamentally broken.
Log it with status crash and move on.

Ideas worth trying: apply the wiki's single-source cap; steepen the sentence-length slope; reward a
conclusion; change the evidence base so zero citations scores 1.
Ideas NOT worth trying: anything that touches evalset/; special-casing a single item id.
