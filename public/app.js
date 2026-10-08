const tokenPattern = /[\u0C00-\u0C7F]+|[a-z0-9]+/gi;
let index;

function tokenize(value) {
  return (value.normalize("NFC").toLowerCase().match(tokenPattern) || []);
}

function escapeHtml(value) {
  return value.replace(/[&<>'"]/g, char => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;" })[char]);
}

function postingEntries(posting) {
  if (Array.isArray(posting)) return posting.map(([id, tf]) => [String(id), Number(tf)]);
  return Object.entries(posting || {}).map(([id, value]) => [id, Number(value[0])]);
}

function snippet(text, terms) {
  const plain = text.replace(/\s+/g, " ").trim();
  const position = terms.map(term => plain.toLowerCase().indexOf(term)).find(pos => pos >= 0) ?? 0;
  const start = Math.max(0, position - 90);
  const excerpt = `${start ? "…" : ""}${plain.slice(start, start + 260)}${start + 260 < plain.length ? "…" : ""}`;
  if (!terms.length) return escapeHtml(excerpt);
  const pattern = new RegExp(`(${terms.map(term => term.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")).join("|")})`, "gi");
  return escapeHtml(excerpt).replace(pattern, "<mark>$1</mark>");
}

function search(query) {
  const terms = [...new Set(tokenize(query).filter(term => !index.stopwordSet.has(term)))];
  if (!terms.length) return [];
  const scores = new Map();
  const totalDocuments = index.metadata.documents;
  for (const term of terms) {
    const entries = postingEntries(index.postings[term]);
    if (!entries.length) continue;
    const idf = Math.log((totalDocuments + 1) / (entries.length + 1)) + 1;
    for (const [docId, tf] of entries) {
      scores.set(docId, (scores.get(docId) || 0) + (1 + Math.log(tf)) * idf);
    }
  }
  return [...scores.entries()]
    .sort((a, b) => b[1] - a[1])
    .slice(0, 10)
    .map(([id, score]) => ({ ...index.documentMap.get(id), score }));
}

const status = document.querySelector("#status");
const results = document.querySelector("#results");
const postings = document.querySelector("#postings");
const queryInput = document.querySelector("#query");
const demoTerms = document.querySelector("#demo-terms");
const submitButton = document.querySelector(".submit-button");
queryInput.disabled = true;
submitButton.disabled = true;

function showResults(query) {
  const terms = [...new Set(tokenize(query))];
  const termPostings = terms.map(term => ({ term, entries: postingEntries(index.postings[term]) }));
  postings.innerHTML = termPostings.map(({ term, entries }) => {
    if (!entries.length) {
      return `<article class="posting-row"><h3 lang="te">${escapeHtml(term)}</h3><p>No documents found for this term.</p></article>`;
    }
    const ids = entries.map(([id]) => id);
    const visibleIds = ids.slice(0, 100);
    const omitted = ids.length - visibleIds.length;
    const displayed = `[${visibleIds.join(", ")}${omitted ? ", …" : ""}]`;
    return `<article class="posting-row">
      <div class="posting-heading"><h3 lang="te">${escapeHtml(term)}</h3><span>${ids.length.toLocaleString()} documents</span></div>
      <p class="posting-expression"><code lang="te">${escapeHtml(term)} → ${displayed}</code></p>
      ${omitted ? `<details><summary>Show all ${ids.length.toLocaleString()} document IDs</summary><p class="full-id-list"><code>[${ids.join(", ")}]</code></p></details>` : ""}
    </article>`;
  }).join("");

  const searchableTerms = terms.filter(term => !index.stopwordSet.has(term));
  const found = search(query);
  results.innerHTML = found.map((document, number) => `
    <article class="result-row">
      <div class="result-meta">${number + 1} · ${document.url ? `<a href="${escapeHtml(document.url)}" target="_blank" rel="noreferrer">${escapeHtml(document.title || `Document ${document.id}`)}</a>` : `Document ${escapeHtml(document.id)}`} · score ${document.score.toFixed(2)}</div>
      <p lang="te">${snippet(document.text, searchableTerms)}</p>
    </article>`).join("");

  const matched = termPostings.filter(item => item.entries.length).length;
  status.textContent = matched
    ? `${matched} term posting list${matched === 1 ? "" : "s"} · ${found.length} ranked document${found.length === 1 ? "" : "s"}`
    : `No indexed terms found for “${query}”.`;
}

document.querySelector("#search-form").addEventListener("submit", event => {
  event.preventDefault();
  const query = queryInput.value.trim();
  if (!query) {
    status.textContent = "Enter a Telugu word or phrase to search.";
    postings.innerHTML = "";
    results.innerHTML = "";
    return;
  }
  showResults(query);
});

fetch("index.json")
  .then(response => {
    if (!response.ok) throw new Error("index.json is missing");
    return response.json();
  })
  .then(data => {
    index = data;
    queryInput.disabled = false;
    submitButton.disabled = false;
    index.documentMap = new Map(index.documents.map(document => [document.id, document]));
    index.stopwordSet = new Set(index.stopwords);
    status.textContent = `Index ready · ${index.metadata.documents.toLocaleString()} articles · ${index.metadata.vocabulary.toLocaleString()} terms`;
    document.querySelector("#corpus-count").textContent = index.metadata.documents.toLocaleString();
    document.querySelector("#term-count").textContent = index.metadata.vocabulary.toLocaleString();
    document.querySelector("#source-credit").href = index.metadata.source_url;
    document.querySelector("#source-credit").textContent = index.metadata.dataset;
    document.querySelector("#license-credit").textContent = index.metadata.license;
    const terms = index.metadata.demo_terms || Object.keys(index.postings)
      .filter(term => !index.stopwordSet.has(term) && /[\u0C00-\u0C7F]/.test(term))
      .sort((a, b) => postingEntries(index.postings[b]).length - postingEntries(index.postings[a]).length)
      .slice(0, 6);
    demoTerms.innerHTML = terms.map(term => `<button type="button" class="demo-term" lang="te">${escapeHtml(term)}</button>`).join("");
    demoTerms.querySelectorAll("button").forEach(button => {
      button.addEventListener("click", () => {
        queryInput.value = button.textContent;
        showResults(queryInput.value);
      });
    });
  })
  .catch(() => {
    status.textContent = "Index not found. Build it with: python scripts/build_index.py";
  });
