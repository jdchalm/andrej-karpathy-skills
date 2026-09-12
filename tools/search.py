#!/usr/bin/env python3
"""Tiny local search over a folder of markdown files. Standard library only.

Three rankers so you can see how each one thinks:

  bm25    keyword ranking. What Karpathy's llm-wiki gist calls "BM25".
  vector  maps every document and the query to a vector, ranks by cosine
          similarity. Uses TF-IDF vectors here so it runs with no model;
          swap in real embeddings and the rest of the code is unchanged.
  hybrid  runs both and fuses the two rank lists (reciprocal rank fusion).

Usage:
  python tools/search.py <folder> "<query>" [--mode bm25|vector|hybrid] [--top 5]
  python tools/search.py wiki "why do we revise criterion 3" --mode hybrid
"""
import math
import re
import sys
from collections import Counter
from pathlib import Path

TOKEN = re.compile(r"[a-z0-9]+")
STOP = set("a an and are as at be by for from has in is it of on or that the to was with".split())


def tokenize(text):
    return [t for t in TOKEN.findall(text.lower()) if t not in STOP]


def load(folder):
    docs = {}
    for path in sorted(Path(folder).rglob("*.md")):
        docs[str(path)] = tokenize(path.read_text(errors="ignore"))
    if not docs:
        sys.exit(f"no .md files under {folder}")
    return docs


# ---------------------------------------------------------------- BM25 ----
# Score a document for each query term: how often the term appears (tf),
# discounted for long documents, weighted by how rare the term is (idf).
# Rare terms in short documents score highest. Exact words only.

def bm25(docs, query, k1=1.5, b=0.75):
    n = len(docs)
    avgdl = sum(len(t) for t in docs.values()) / n
    df = Counter()
    for toks in docs.values():
        df.update(set(toks))
    scores = {}
    for path, toks in docs.items():
        tf = Counter(toks)
        dl = len(toks)
        s = 0.0
        for term in tokenize(query):
            if term not in tf:
                continue
            idf = math.log((n - df[term] + 0.5) / (df[term] + 0.5) + 1)
            s += idf * tf[term] * (k1 + 1) / (tf[term] + k1 * (1 - b + b * dl / avgdl))
        scores[path] = s
    return scores


# -------------------------------------------------------------- VECTOR ----
# "Vector mapping": turn each document into a list of numbers, one per
# vocabulary word (TF-IDF weight), so that documents become points in a
# space and similarity becomes an angle (cosine). A real embedding model
# does the same thing with ~1000 learned dimensions instead of one per
# word, which is what lets it match "car" against "automobile".

def tfidf_vectors(docs):
    n = len(docs)
    df = Counter()
    for toks in docs.values():
        df.update(set(toks))
    idf = {t: math.log(n / df[t]) + 1 for t in df}
    vecs = {}
    for path, toks in docs.items():
        tf = Counter(toks)
        vecs[path] = {t: tf[t] * idf[t] for t in tf}
    return vecs, idf


def cosine(a, b):
    dot = sum(a[t] * b[t] for t in a if t in b)
    na = math.sqrt(sum(v * v for v in a.values()))
    nb = math.sqrt(sum(v * v for v in b.values()))
    return dot / (na * nb) if na and nb else 0.0


def vector(docs, query):
    vecs, idf = tfidf_vectors(docs)
    q = Counter(tokenize(query))
    qvec = {t: q[t] * idf.get(t, 1.0) for t in q}
    return {path: cosine(qvec, v) for path, v in vecs.items()}


# -------------------------------------------------------------- HYBRID ----
# Reciprocal rank fusion: ignore the raw scores (they are on different
# scales) and reward documents that rank well in either list.

def hybrid(docs, query, k=60):
    fused = Counter()
    for scores in (bm25(docs, query), vector(docs, query)):
        ranked = sorted(scores, key=scores.get, reverse=True)
        for rank, path in enumerate(ranked, 1):
            if scores[path] > 0:
                fused[path] += 1 / (k + rank)
    return dict(fused)


MODES = {"bm25": bm25, "vector": vector, "hybrid": hybrid}


def main(argv):
    if len(argv) < 3:
        sys.exit(__doc__)
    folder, query = argv[1], argv[2]
    mode = argv[argv.index("--mode") + 1] if "--mode" in argv else "hybrid"
    top = int(argv[argv.index("--top") + 1]) if "--top" in argv else 5
    docs = load(folder)
    scores = MODES[mode](docs, query)
    ranked = [(p, s) for p, s in sorted(scores.items(), key=lambda x: -x[1]) if s > 0]
    print(f"{mode}: {len(docs)} docs, query={query!r}")
    for path, score in ranked[:top]:
        print(f"  {score:8.4f}  {path}")
    if not ranked:
        print("  no matches")


if __name__ == "__main__":
    main(sys.argv)
