# Assignment plan: Telugu Information Retrieval

## Project

**Title:** *Building a Telugu Inverted Index over Wikipedia Articles*

Build a reproducible retrieval demo that processes Telugu article text, creates a term-to-document posting list, and shows output such as `తెలుగు → [12, 25, 486, ...]` alongside ranked article previews.

## Dataset choice

The default source is [Wikimedia Wikipedia](https://huggingface.co/datasets/wikimedia/wikipedia), configuration `20231101.te`. It contains about 87,900 prepared Telugu article rows with `id`, `url`, `title`, and cleaned `text` fields. The builder downloads the two Telugu-only Parquet shards from Hugging Face, samples 6,000 rows systematically across source order, and caches the shards locally. It does not scrape websites or reuse another project's code.

Wikimedia text is licensed under CC BY-SA 3.0 and GFDL; attribution and share-alike obligations apply. The earlier [Bharat-NanoBEIR Telugu dataset](https://huggingface.co/datasets/carlfeynman/Bharat_NanoMSMARCO_te) remains an optional 5,043-document benchmark with 50 queries and qrels under CC-BY-4.0. Its relevance labels apply only to its own corpus, not the Wikipedia article collection.

The default sample cap keeps the generated static browser index practical. Change it with `python scripts/build_index.py --limit N`; use `--source benchmark` to rebuild the judged baseline.

## Deliverable scope

Keep it modest and demonstrable:

1. A reproducible script that downloads the data and builds the index.
2. A term-frequency inverted index: `term -> [[document_id, term_frequency], ...]`.
3. Ranked keyword search for normal Telugu queries.
4. Exact-phrase search for quoted Telugu queries, if time permits.
5. A command-line interface is sufficient; a web app is **not** required.
6. A short results report with index statistics, example searches, and evaluation.

Suggested layout:

```text
IR/
├── README.md                 # short: setup, run commands, results
├── requirements.txt
├── src/
│   ├── preprocess.py
│   ├── build_index.py
│   ├── search.py
│   └── evaluate.py
├── data/                     # gitignored cache / downloaded data
├── artifacts/                # gitignored index files and statistics
└── report/                   # figures/table for submission
```

## Preprocessing

The same tokenizer is used for document text and queries. The builder decodes HTML entities, removes tags, collapses whitespace, applies NFC and case folding, extracts Telugu/Latin/digit tokens, and splits on punctuation. It indexes article titles as well as article bodies. Stopwords remain in the postings but are omitted from ranked queries. No stemming or lemmatization is applied.

Example output shown by the page:

```text
తెలుగు → [1, 786, 787, ...]
```

## Index and retrieval design

For every document, compute token frequencies and update:

```text
postings[term].append([doc_id, term_frequency])
document_lengths[doc_id] = number_of_non_stopword_tokens
document_frequency[term] = number_of_documents_containing_term
```

The browser JSON stores compact term-frequency postings, document titles, source URLs, and 900-character article previews. The page derives the requested `term → [document IDs]` display from each posting list. Token positions are not currently stored, so exact phrase retrieval is not claimed.

Ranking uses TF-IDF-style term weighting over the union of matching documents. Results link to the original Wikipedia article when a source URL is available.

## Evaluation and evidence

The default Wikipedia source has no matching relevance labels. Demonstrate postings, example terms, corpus statistics, and ranked previews, but do not report benchmark metrics for this source. The optional Bharat-NanoBEIR build can be used with its own queries and qrels only; never combine those judgments with Wikipedia IDs.

## Execution order

1. Install `pyarrow` and run the unit tests.
2. Build the systematic Wikipedia sample and inspect printed source/index metadata.
3. Verify each UI demo term against the generated postings and inspect `term → [IDs]` output.
4. Check ranked previews, source links, unknown terms, and stopword-only queries.
5. If evaluating the benchmark, rebuild with `--source benchmark` and use only its qrels.
6. Keep this README and assignment plan aligned with the selected source and generated index.

## What to submit

- Source code and `requirements.txt`.
- A concise README (about one page): goal, dataset, commands, preprocessing, index format, and sample output.
- `report/results.md` or a PDF with the two metrics, index statistics, and screenshots/terminal output of Telugu queries.
- No dataset files or generated index need be committed; include `.gitignore` entries for `data/` and `artifacts/`.

## Risks and sensible boundaries

- The corpus is translated/adapted Telugu content and may contain occasional English fragments or translation artefacts; describe this as a dataset limitation.
- Because there are only 50 queries and likely one judged relevant document per query, treat results as a small benchmark, not a broad claim of Telugu-search quality.
- Do not use an LLM, embeddings, or a search-engine library to create the core index. The assignment should visibly implement the posting lists and scoring itself.
- The current default artifact is intentionally non-positional and uses TF-IDF-style ranking; do not claim phrase search or transfer benchmark metrics to the Wikipedia corpus.

## Sources to cite

- Bharat-NanoBEIR Telugu dataset card: <https://huggingface.co/datasets/carlfeynman/Bharat_NanoMSMARCO_te>
- Reference project consulted for general architecture only: <https://github.com/vipulchetan25/telugu-wikipedia-positional-index>
