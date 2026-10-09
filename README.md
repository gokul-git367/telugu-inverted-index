# తెలుగు Information Retrieval Positional and Inverted Index interpretation

**Live app:** [తెలుగు Information Retrieval](https://telugu-inverted-index-public-qcdhayypu.vercel.app/)

## 1. Project Overview

The project builds a browser-searchable index from Telugu Wikipedia articles. Search results include both the posting lists for query terms and a ranked list of matching articles with snippets and source links.

The system demonstrates:

- Telugu text normalization and tokenization
- Stopword-aware query processing
- Inverted and positional inverted index construction
- Document IDs, term frequencies, and token positions
- TF-IDF-style ranked retrieval
- A static web interface for inspecting postings and articles

## 2. Objectives

1. Build a reproducible information-retrieval pipeline for Telugu text.
2. Construct a positional inverted index over article titles and bodies.
3. Display the documents associated with each query term.
4. Rank matching documents and show their titles, snippets, and source links.
5. Keep the generated index usable by a static browser application.

## 3. Project Structure

```text
IR/
├── public/
│   ├── app.js                 # Browser query processing and result rendering
│   ├── index.html             # Search interface
│   ├── index.json             # Generated browser index
│   └── styles.css             # Application styles
├── resources/
│   └── telugu_stopwords.txt   # Explicit Telugu stopword list
├── scripts/
│   └── build_index.py         # Dataset loading and index construction
├── tests/
│   └── test_build_index.py    # Preprocessing and index tests
├── plan.md                    # Assignment notes and design decisions
├── requirements.txt
└── vercel.json                # Static deployment configuration
```

Downloaded Parquet files and the Wikipedia cache are kept locally and excluded from Git. The generated `public/index.json` is the data file consumed by the deployed application.

## 4. System Architecture

```text
Telugu Wikipedia Parquet shards
		│
		▼
	scripts/build_index.py
		│
	clean and tokenize text
		│
		▼
 positional postings + document metadata
		│
		▼
	public/index.json
		│
		▼
 browser query → postings and ranked articles
```

## 5. Dataset

The default source is the Telugu configuration `20231101.te` of [Wikimedia Wikipedia](https://huggingface.co/datasets/wikimedia/wikipedia). The prepared source contains 87,854 article rows. The checked-in browser index contains a systematic sample of 6,000 documents to keep the static index practical.

Each indexed document stores its source ID, title, a text preview of up to 900 characters, searchable document length, and source URL when available. The current generated index contains 221,650 distinct terms and 2,504,966 tokens before stopword filtering.

Wikimedia text is distributed under CC BY-SA 3.0 and GFDL. Attribution and share-alike obligations apply when reusing the article text. The index records its dataset and license metadata for display in the app.

The Wikipedia collection has no corresponding query relevance labels. It is used to demonstrate retrieval; benchmark scores are not claimed for this corpus.

## 6. Text Preprocessing

The builder applies the same tokenizer to document text and query text.

### 6.1 Cleaning and Unicode normalization

For documents, HTML entities are decoded, tags are removed, repeated whitespace is collapsed, and text is normalized to Unicode NFC. Text is case-folded before token extraction.

### 6.2 Tokenization

The tokenizer extracts contiguous Telugu-block characters, ASCII Latin letters, and digits. Punctuation and other separators divide tokens. For example:

```text
తెలుగు, AI 2026!
```

becomes:

```text
["తెలుగు", "ai", "2026"]
```

### 6.3 Stopwords

The stopword list is maintained in `resources/telugu_stopwords.txt`. Stopwords remain in index postings and positions, but are excluded from ranked query scoring. This keeps stored positions aligned with the original token sequence while reducing stopword-only matches.

No Telugu stemming or lemmatization is performed; retrieval uses exact normalized token matches.

## 7. Inverted Index

The index maps each term to the documents in which it occurs. Every posting stores the document ID, term frequency, and zero-based positions:

```text
term → [[document_id, term_frequency, [position, ...]], ...]
```

For example, a posting might have this form:

```text
తెలుగు → [[document_id, 3, [0, 14, 28]], ...]
```

Positions are counted across the token sequence formed from the title followed by the article text. Article titles are therefore searchable as well as article bodies.

## 8. Positional Index

The positional index is the posting structure above, with token positions recorded for each document. The interface lets users inspect term frequencies and positions for the first 20 documents in a posting list. Positions are available for future proximity or exact-phrase retrieval, but the current search interface does not use them to enforce phrase adjacency.

## 9. Search System

The browser application is implemented in `public/app.js`. It normalizes and tokenizes a query, shows the posting list for each token, and ranks matching documents.

### Single-term search

For a query such as `తెలుగు`, the interface displays the term's document IDs and ranks matching articles. Up to 100 IDs are shown initially; the full list can be expanded. Posting details show term frequencies and positions for up to the first 20 documents.

### Multi-term search

For a query such as `తెలుగు భాష`, the application displays postings for both terms and scores the union of documents containing either term. Documents matching more query terms can accumulate more score. This is not exact phrase search: consecutive positions are not checked, and a document need not contain every query term to appear in the ranked results.

The interface displays up to ten ranked articles, with a snippet, score, and link to the source article when available. Example Telugu terms are provided as clickable searches.

## 10. Ranking

Each query term contributes a TF-IDF-style score to documents in its posting list. The implementation uses logarithmic term-frequency weighting and inverse document frequency, then sorts documents by their accumulated score and displays the top ten.

This is a small educational ranking function, not a full BM25 implementation. Wikipedia has no matching relevance judgments in this project, so no retrieval-quality metric is reported for the Wikipedia index.

## 11. Build the Index

Create a Python environment, install the single external dependency, and build the default Wikipedia sample:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python scripts/build_index.py
```

The builder downloads the two prepared Telugu Parquet shards and caches them under `.cache/wikipedia_te/`. It writes the browser index to `public/index.json` and prints corpus and index metadata.

To build a smaller sample:

```bash
python scripts/build_index.py --limit 3000
```

To choose another output file:

```bash
python scripts/build_index.py --output /path/to/index.json
```

## 12. Run the Web App Locally

Serve the `public/` directory over HTTP so the browser can load `index.json`:

```bash
cd public
python -m http.server 8000
```

Open [http://localhost:8000](http://localhost:8000). If the browser index has not been generated, the page will ask you to run the build command.

## 13. Optional Benchmark Corpus

The builder can also create an index for the [Bharat-NanoBEIR Telugu IR dataset](https://huggingface.co/datasets/carlfeynman/Bharat_NanoMSMARCO_te):

```bash
python scripts/build_index.py --source benchmark
```

This replaces the default output index with the benchmark corpus index. Its queries and relevance labels apply only to that benchmark corpus, not to Wikipedia. Rebuild with the default command to restore the Wikipedia index. The current web app does not include a benchmark evaluation workflow.

## 14. Tests

Run the preprocessing and index-construction tests with:

```bash
python -m unittest discover -s tests -v
```

The tests cover HTML cleanup, Unicode normalization, tokenization, empty input, posting frequencies and positions, and preservation of benchmark document IDs.

## 15. Deployment

The static application is hosted on Vercel. `vercel.json` configures `public/` as the output directory; no frontend build step is required. The deployed site uses `public/index.json`, so rebuild and include that file when changing the indexed corpus.

## 16. Limitations

- The default index uses only 6,000 articles from a larger source collection.
- Retrieval uses exact token matching without Telugu stemming or lemmatization.
- Multi-term queries rank the union of matching documents; exact phrase matching is not implemented.
- Ranking is TF-IDF-style and has not been evaluated against Wikipedia relevance judgments.
- The static JSON index and browser-side processing are intended for a modest demonstration collection.

## 17. Possible Extensions

- Exact phrase and proximity search using stored token positions
- Telugu stemming or lemmatization
- BM25 ranking and evaluation on a judged corpus
- Query expansion, spelling correction, or fuzzy matching
- Larger collections with an index format suited to server-side retrieval

## 18. Summary

This project demonstrates a complete Telugu retrieval workflow: prepare a Wikipedia sample, normalize and tokenize text, build an inverted index with positions, and search it through a browser interface. It exposes the posting lists as well as ranked article results, making the underlying information-retrieval data structures inspectable.
