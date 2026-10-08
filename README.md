# తెలుగు Information Retrieval

## Deploy to Vercel

Import `gokul-git367/telugu-inverted-index` into Vercel and select the **Other** framework preset. Leave the build command empty and use `public` as the output directory; these settings are already declared in `vercel.json`. Vercel serves the static files directly, so `public/index.json` must be present and up to date before deployment. To refresh the corpus, run `python scripts/build_index.py` locally and commit the generated index. Once the repository is connected, pushing to `main` triggers a deployment.

A browser-based Telugu information-retrieval assignment. The default build indexes a deterministic, evenly spread sample of 6,000 cleaned Telugu Wikipedia articles from Wikimedia's 2023-11-01 snapshot. The full 87,900-row source is available through Hugging Face; this project samples it to keep the static index practical.

## Index and retrieval

- Inverted index: `term → [[document_id, term_frequency], ...]`; the page displays each term's document IDs directly.
- Ranked results use TF-IDF-style term weighting and show article title, source link, and a short preview.
- Source document IDs are retained as strings. Article titles are indexed with article text.
- The browser artifact stores 900-character previews; the builder tokenizes the full article text.
- This Wikipedia corpus has no matching query relevance labels, so the interface demonstrates retrieval but does not report benchmark metrics.

Example from the generated sample: `తెలుగు → [859, 1138, 1160, 1184, 1224, ...]` (1,132 matching articles in the current build).

## Source and preprocessing

Default source: [Wikimedia Wikipedia](https://huggingface.co/datasets/wikimedia/wikipedia), configuration `20231101.te` (87,900 rows), derived from Wikimedia dumps. Text is licensed under CC BY-SA 3.0 and GFDL; retain attribution and share-alike obligations when reusing article text.

The builder downloads the two Telugu-only prepared Parquet shards from the Hugging Face dataset mirror, caches them under `.cache/wikipedia_te/`, and samples 6,000 rows systematically across source order. For indexing and query handling it applies HTML entity decoding and tag removal, whitespace collapse, NFC Unicode normalization, case folding, Telugu/Latin/digit tokenization, and punctuation removal. Stopwords remain in the postings but are excluded from ranked queries. Stemming is not applied.

The previous [Bharat-NanoBEIR Telugu IR dataset](https://huggingface.co/datasets/carlfeynman/Bharat_NanoMSMARCO_te) remains available as the smaller judged benchmark (5,043 corpus documents, CC-BY-4.0):

```bash
python scripts/build_index.py --source benchmark
```

Its query/relevance labels are not interchangeable with Wikipedia documents.

## Run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python scripts/build_index.py
cd public && python -m http.server 8000
```

Optional: `python scripts/build_index.py --limit 3000` creates a smaller systematic sample. Then open `http://localhost:8000`.

## Tests

```bash
python -m unittest discover -s tests -v
```

## Deploy

[telugu-inverted-index](telugu-inverted-index-public-7n52fhqdf.vercel.app)
