"""Build a Telugu article index from Wikimedia Wikipedia via Hugging Face."""
import argparse
import html
import json
import re
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path
from urllib.request import urlretrieve

import pyarrow as pa
import pyarrow.parquet as pq

ROOT = Path(__file__).parents[1]
WIKIPEDIA_DATASET = "wikimedia/wikipedia"
WIKIPEDIA_CONFIG = "20231101.te"
WIKIPEDIA_PARQUET_ROOT = "https://huggingface.co/datasets/wikimedia/wikipedia/resolve/refs%2Fconvert%2Fparquet/20231101.te/train"
WIKIPEDIA_SHARDS = ("0000.parquet", "0001.parquet")
BENCHMARK_DATASET = "carlfeynman/Bharat_NanoMSMARCO_te"
BENCHMARK_PARQUET = "https://huggingface.co/datasets/carlfeynman/Bharat_NanoMSMARCO_te/resolve/refs%2Fconvert%2Fparquet/{}/train/0000.parquet"
DEFAULT_LIMIT = 6000
SNIPPET_LENGTH = 900
TOKEN_RE = re.compile(r"[\u0C00-\u0C7F]+|[a-z0-9]+", re.I)
HTML_TAG_RE = re.compile(r"<[^>]+>")
TELUGU_RE = re.compile(r"[\u0C00-\u0C7F]")


def clean_text(text):
    decoded = html.unescape(text or "")
    without_tags = HTML_TAG_RE.sub(" ", decoded)
    normalized = unicodedata.normalize("NFC", without_tags)
    return re.sub(r"\s+", " ", normalized).strip()


def preprocess(text):
    return TOKEN_RE.findall(clean_text(text).casefold())


def load_wikipedia_rows(limit=DEFAULT_LIMIT, cache_dir=None):
    cache_dir = cache_dir or ROOT / ".cache" / "wikipedia_te"
    cache_dir.mkdir(parents=True, exist_ok=True)
    tables = []
    for shard in WIKIPEDIA_SHARDS:
        cache = cache_dir / shard
        if not cache.exists():
            url = f"{WIKIPEDIA_PARQUET_ROOT}/{shard}"
            print(f"Downloading {shard} from {WIKIPEDIA_DATASET}…")
            urlretrieve(url, cache)
        tables.append(pq.read_table(cache, columns=["id", "url", "title", "text"]))

    table = pa.concat_tables(tables)
    total = table.num_rows
    sample_size = min(limit, total)
    indices = [round(i * (total - 1) / max(sample_size - 1, 1)) for i in range(sample_size)]
    sampled = table.take(pa.array(indices)).to_pylist()
    return sampled, total


def load_benchmark_rows():
    cache = ROOT / ".corpus.parquet"
    if not cache.exists():
        from urllib.request import urlretrieve
        print("Downloading Bharat-NanoBEIR Telugu corpus…")
        urlretrieve(BENCHMARK_PARQUET.format("corpus"), cache)
    return pq.read_table(cache).to_pylist()


def stopwords():
    path = ROOT / "resources" / "telugu_stopwords.txt"
    return {line.strip() for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.startswith("#")}


def build_index(rows, words, dataset, license_name, source_url, sample_info=None):
    postings = defaultdict(list)
    documents = []
    all_tokens = indexed_tokens = 0
    for row in rows:
        title = clean_text(row.get("title", ""))
        text = clean_text(row.get("text", ""))
        if not text:
            continue
        doc_id = str(row.get("id", row.get("_id", "")))
        tokens = preprocess(f"{title} {text}")
        counts = Counter(tokens)
        searchable_count = sum(count for term, count in counts.items() if term not in words)
        all_tokens += len(tokens)
        indexed_tokens += searchable_count
        document = {"id": doc_id, "title": title, "text": text[:SNIPPET_LENGTH],
                    "length": searchable_count}
        if row.get("url"):
            document["url"] = row["url"]
        documents.append(document)
        for term, frequency in counts.items():
            postings[term].append([doc_id, frequency])

    demo_candidates = ["తెలుగు", "భాష", "ఆంధ్రప్రదేశ్", "భారతదేశం", "స్థానిక", "గుంటూరు"]
    demo_terms = [term for term in demo_candidates if term in postings and term not in words]
    frequent_telugu = sorted(
        (term for term in postings if TELUGU_RE.search(term) and term not in words),
        key=lambda term: len(postings[term]), reverse=True)
    demo_terms.extend(term for term in frequent_telugu if term not in demo_terms)
    demo_terms = demo_terms[:6]
    metadata = {
        "dataset": dataset,
        "source_url": source_url,
        "license": license_name,
        "documents": len(documents),
        "source_documents": sample_info.get("source_documents") if sample_info else len(documents),
        "sample_method": sample_info.get("method") if sample_info else "complete corpus",
        "vocabulary": len(postings),
        "stopword_count": len(words),
        "tokens_before_stopwords": all_tokens,
        "tokens_after_stopwords": indexed_tokens,
        "stopwords_removed": all_tokens - indexed_tokens,
        "average_document_length": round(indexed_tokens / len(documents), 2) if documents else 0,
        "snippet_characters": SNIPPET_LENGTH,
        "preprocessing": "HTML entity/tag cleanup; whitespace collapse; NFC normalization; case folding; Telugu/Latin/digit tokenization; stopwords excluded from ranking; no stemming.",
        "index_type": "term -> [[document_id, term_frequency], ...]",
        "demo_terms": demo_terms,
    }
    return {"metadata": metadata, "stopwords": sorted(words), "documents": documents,
            "postings": postings}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", choices=("wikipedia", "benchmark"), default="wikipedia",
                        help="Use cleaned Telugu Wikipedia articles or the smaller judged IR benchmark.")
    parser.add_argument("--limit", type=int, default=DEFAULT_LIMIT,
                        help=f"Number of evenly sampled Wikipedia articles (default: {DEFAULT_LIMIT}).")
    parser.add_argument("--output", type=Path, default=ROOT / "public" / "index.json",
                        help="Path for the generated browser index.")
    args = parser.parse_args()
    if args.limit < 1:
        parser.error("--limit must be at least 1")

    words = stopwords()
    if args.source == "wikipedia":
        rows, source_count = load_wikipedia_rows(args.limit)
        index = build_index(rows, words, WIKIPEDIA_DATASET,
                            "CC BY-SA 3.0 and GFDL (Wikimedia text; attribution required)",
                            "https://huggingface.co/datasets/wikimedia/wikipedia",
                            {"source_documents": source_count,
                             "method": f"systematic sample across source order, capped at {args.limit}"})
    else:
        index = build_index(load_benchmark_rows(), words, BENCHMARK_DATASET, "CC-BY-4.0",
                            "https://huggingface.co/datasets/carlfeynman/Bharat_NanoMSMARCO_te")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(index, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    target = args.output
    print(f"Created {target} ({target.stat().st_size / 1_000_000:.2f} MB)")
    print(json.dumps(index["metadata"], ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
