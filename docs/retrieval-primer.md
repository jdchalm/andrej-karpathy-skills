# Retrieval primer: vectors, BM25, hybrid search, and where the graph fits

A plain-language guide to the retrieval ideas behind Karpathy's LLM Wiki, with a runnable script
(`tools/search.py`, standard library only) so you can watch each idea rank real files.

## The problem every method solves

You have many documents. Someone asks a question. Which documents should the LLM read first?
Every method below is a different answer to "how similar is this document to this question."

## 1. Keyword ranking: BM25

BM25 is the method Karpathy names for the "hybrid BM25/vector search" option in the gist. It is what
most search engines used for twenty years and it is still hard to beat for exact terms.

For each word in the query, a document scores higher when:

- the word appears **more often** in the document (term frequency),
- the word is **rare across the whole collection** (inverse document frequency), so "revert" counts
  for more than "the",
- the document is **short**, so a match is not just luck from length.

Add up the per-word scores. That is the document's BM25 score.

**Strength:** exact matches, names, identifiers, error strings. Fast, no model, fully explainable.
**Weakness:** zero understanding. "car" does not match "automobile". Misspellings score nothing.

## 2. Vector mapping: turn text into points in space

"Vector mapping" (embedding) means: represent each document as a list of numbers, so documents become
points in a space, and similarity becomes distance or angle between points.

The simplest version, which `search.py` uses, is **TF-IDF vectors**: one dimension per vocabulary word,
the value is how much that word matters in the document. Two documents are similar when their vectors
point the same way, measured by **cosine similarity** (1.0 is identical direction, 0.0 is unrelated).

A **real embedding model** does the same thing with a twist: instead of one dimension per word, it has
roughly 400 to 3000 *learned* dimensions that capture meaning. "car" and "automobile" land close
together. So does "the build is broken" and "CI failing". That is the whole reason embeddings exist.

**Strength:** meaning, paraphrase, cross-language, fuzzy questions.
**Weakness:** exact strings and rare identifiers get blurred. Needs a model. Harder to explain why a
result ranked where it did.

In `search.py` the TF-IDF vector and a model embedding are interchangeable: both produce a vector per
document and both are compared with cosine. Swapping in a model changes one function.

## 3. Hybrid: use both

Keyword and vector search fail in opposite ways, so the standard fix is to run both and merge.
`search.py` merges with **reciprocal rank fusion**: ignore the raw scores, which are on different scales,
and give each document points for ranking well in either list (1 / (60 + rank)). Documents that both
methods like float to the top. This is what "hybrid BM25/vector" means and it is what `qmd` and most
modern search stacks do.

## 4. Where the graph fits

None of the above is what the LLM Wiki uses first. The wiki's first retrieval step is `index.md`: a
human-readable catalog of every page with a one-line summary. The agent reads the whole index, picks
pages, follows links. Karpathy: at "~100 sources, ~hundreds of pages" this "works surprisingly well" and
"avoids the need for embedding-based RAG infrastructure."

The wiki-links between pages are the **graph**. They carry something no similarity score can: *why*
two pages are related. A criterion page links to the cases that argued about it; a decision page links
to the sources it drew on. Following links answers "why" questions. Similarity search answers "what
looks like this" questions. You want both, and the index-plus-links layer comes free with the wiki.

| Method | Answers | Needs | Add when |
|--------|---------|-------|----------|
| index.md + links (graph) | what do we know, and why | nothing | day one |
| BM25 (keyword) | where is this exact term | nothing | index too big to read |
| vector (embedding) | what is *about* this | a model | fuzzy questions start failing |
| hybrid | both of the above | a model | you add vector at all |

## 5. RAG versus the wiki

RAG (retrieval-augmented generation) is: on every question, search the raw documents, paste the top
chunks into the prompt, answer. Karpathy's objection: "the LLM is rediscovering knowledge from scratch
on every question. There's no accumulation." The wiki keeps the synthesis. Retrieval, whichever method,
is then just how the agent finds the right page fast.

## Try it

```bash
# rank this repo's markdown three ways
python3 tools/search.py . "surgical changes dead code" --mode bm25
python3 tools/search.py . "surgical changes dead code" --mode vector
python3 tools/search.py . "surgical changes dead code" --mode hybrid

# point it at a wiki
python3 tools/search.py wiki "why do we keep revising criterion 3" --mode hybrid --top 5
```

Things to watch for while experimenting:

- Query a rare word that appears in one file. BM25 nails it; vector is blurrier.
- Query a paraphrase with none of the file's exact words. TF-IDF vector fails too, because it is still
  word-based. That gap is exactly what a learned embedding model closes.
- Look at the hybrid scores: they are tiny numbers near 0.03. That is normal for rank fusion; only the
  order matters.

## Swapping in real embeddings

When you hit the vector trigger in the template, replace `tfidf_vectors` with a call to an embedding
model (a local sentence-transformers model, or an embeddings API) that returns one dense vector per
document, cache the vectors to disk, and keep `cosine` and `hybrid` as they are. That is the entire
upgrade. Everything else in the wiki is unchanged.
