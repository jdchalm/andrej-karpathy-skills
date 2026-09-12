#!/usr/bin/env python3
"""Fixed evaluator. The agent never edits this file.

Scores every item in evalset/ with the rules in weights.json, compares to the
human scores, and prints ONE number: agreement = 1 - (mean absolute error / 4).
1.0 means every predicted score matched the human. Higher is better.

Run from the loop/ folder:  python eval.py
"""
import json
from pathlib import Path

HERE = Path(__file__).parent
items = json.loads((HERE / "evalset" / "items.json").read_text())
w = json.loads((HERE / "weights.json").read_text())


def clamp(x):
    return max(1, min(5, round(x)))


def predict(f):
    c = w["clarity"]
    e = w["evidence"]
    s = w["structure"]
    clarity = clamp(c["base"] + c["per_word_per_sentence"] * f["words_per_sentence"])
    evidence = clamp(e["base"] + e["per_citation"] * f["citations"])
    if f["citations"] <= 1:
        evidence = min(evidence, e["single_source_cap"])
    structure = clamp(
        s["base"]
        + s["per_paragraph"] * f["paragraphs"]
        + s["per_transition"] * f["transitions"]
        + s["conclusion_bonus"] * f["has_conclusion"]
    )
    return {"clarity": clarity, "evidence": evidence, "structure": structure}


errors = []
for item in items:
    p = predict(item["features"])
    for k in ("clarity", "evidence", "structure"):
        errors.append(abs(p[k] - item["human"][k]))

mae = sum(errors) / len(errors)
print(f"items={len(items)} mae={mae:.3f} score={1 - mae / 4:.4f}")
