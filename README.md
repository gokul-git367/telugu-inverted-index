# తెలుగు Information Retrieval Positional and Inverted Index interpretation

**Live app:** [తెలుగు Information Retrieval](https://telugu-inverted-index-public-qcdhayypu.vercel.app/)

## Project Overview

This assignment implements a Telugu information-retrieval system over Wikipedia articles. It builds an inverted index, displays the document IDs associated with a Telugu term, and ranks matching articles for a query.

For example, a lookup can display:

```text
తెలుగు → [859, 1138, 1160, 1184, 1224, ...]
```

The live interface also provides clickable Telugu example terms, article previews, and links to the source articles.

## Dataset

The default collection is a systematic sample of 6,000 articles from the Telugu configuration `20231101.te` of [Wikimedia Wikipedia](https://huggingface.co/datasets/wikimedia/wikipedia). The prepared collection contains about 87,900 rows. The project uses a sample to keep the browser index practical. Wikimedia text is available under CC BY-SA 3.0 and GFDL; attribution and share-alike terms apply when reusing article text.

The index contains 221,650 terms and about 2.5 million tokens before stopword filtering. This Wikipedia collection does not include matching query relevance labels, so the app demonstrates retrieval but does not claim benchmark evaluation scores.


## Index and Retrieval

Each posting stores a document ID, term frequency, and the zero-based token positions where the term occurs:

```text
term → [[document_id, term_frequency, [position, ...]], ...]
```

For example, a term might have a posting such as `తెలుగు → [[859, 3, [0, 14, 28]], ...]`. Positions are counted over the token sequence formed from the article title followed by its text; stopwords are included so offsets remain faithful to that sequence. The page displays the posting document IDs directly and separately shows up to ten ranked articles using TF-IDF-style term weighting. Article titles are indexed along with article text. Source IDs are preserved, and each document entry contains a short preview and its source URL.

## Preprocessing

The builder applies the following steps to article text and titles:

1. Decode HTML entities, remove HTML tags, and collapse repeated whitespace.
2. Normalize Unicode to NFC and convert text to lowercase.
3. Extract Telugu, Latin, and numeric tokens; punctuation separates tokens.
4. Keep stopwords in postings, but exclude them from ranked queries.
5. Do not stem or lemmatize Telugu words.

## Optional Benchmark Corpus

The [Bharat-NanoBEIR Telugu IR dataset](https://huggingface.co/datasets/carlfeynman/Bharat_NanoMSMARCO_te) provides a smaller judged corpus with queries and relevance labels. Build its index with:

```bash
python scripts/build_index.py --source benchmark
```

Its labels apply only to that benchmark corpus and must not be used to evaluate the Wikipedia collection.

## Run Locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python scripts/build_index.py
cd public && python -m http.server 8000
```

Open `http://localhost:8000`. The builder downloads and caches the prepared Telugu Parquet shards under `.cache/wikipedia_te/`. To build a smaller sample, run `python scripts/build_index.py --limit 3000`.

## Tests

```bash
python -m unittest discover -s tests -v
```

## Deployment

The live app is hosted on Vercel. To deploy a changed version, import `gokul-git367/telugu-inverted-index` into Vercel; `vercel.json` sets `public/` as the static output directory. No frontend build command is needed. Rebuild and commit `public/index.json` before deployment if the corpus index has changed.
