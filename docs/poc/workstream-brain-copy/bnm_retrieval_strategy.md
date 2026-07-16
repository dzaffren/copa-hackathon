# Searching BNM Policy Documents: Dense Retrieval & Chunking Strategy

Bank Negara Malaysia (BNM) policy documents are notoriously dense. A single RMiT (Risk Management in Technology) or BCM (Business Continuity Management) framework can contain hundreds of pages, nested hierarchies (Parts, Sections, Paragraphs, Clauses), and highly specific regulatory language. 

Here is a breakdown of how moving to a **Bi-encoder + FAISS/pgvector** architecture fundamentally changes how you process and search this massive corpus.

---

## 1. The "Before" vs. "After"

### The "Before": Keyword Search (Lexical) or Manual Review
Historically, comparing a new policy document against an existing corpus relied on manual reading or traditional search engines (like basic Elasticsearch using TF-IDF or BM25).

*   **How it worked:** You search for a keyword like "disaster recovery site". The engine looks for those exact words.
*   **Why it fails at scale:**
    *   **Vocabulary Mismatch:** If Document A says "disaster recovery site" and Document B says "alternate data centre" or "secondary processing facility", keyword search finds **zero matches**.
    *   **The O(n²) Problem:** If you want to check if *any* of the 5,000 clauses in a new draft conflict with *any* of the 50,000 clauses in the existing corpus, you conceptually have to do 250,000,000 comparisons. Doing this with LLMs (asking GPT-4 to read everything) is impossibly expensive and slow.

### The "After": Bi-Encoder Embeddings + FAISS/pgvector (Dense Retrieval)
We shift from searching for *words* to searching for *meaning (vectors)*.

*   **How it works:** A Bi-encoder (like a fine-tuned BERT model) reads every single clause in the BNM corpus independently and converts it into a dense vector (an array of numbers representing its semantic meaning). These millions of vectors are stored in a specialized vector database like **pgvector** or **FAISS**.
*   **Why it succeeds at scale:**
    *   **Semantic Matching:** The vectors for "disaster recovery site" and "secondary processing facility" will be mathematically very close to each other in the vector space, even though they share no keywords.
    *   **Sub-millisecond Speed:** FAISS (Facebook AI Similarity Search) is optimized to search millions of vectors in milliseconds. Instead of doing O(n²) comparisons, FAISS uses techniques like HNSW (Hierarchical Navigable Small World) to instantly return the "Top-10 most semantically similar clauses" to whatever you are querying.

---

## 2. The Step-by-Step Process at Scale

When dealing with thousands of pages, the pipeline looks like this:

1.  **Ingestion & Parsing:** PDF/Word documents are passed through a layout-aware parser (e.g., Azure Document Intelligence). This extracts the text while preserving the hierarchy (Heading 1, Heading 2, bullet points).
2.  **Structural Chunking (Crucial Step):** The text is broken down into manageable pieces (chunks). *More on this below.*
3.  **Embedding Generation (Bi-encoder):** Each chunk is passed through the Bi-encoder model. The model outputs a high-dimensional vector (e.g., 768 or 1536 dimensions) for that chunk.
4.  **Vector Indexing:** The chunk text, its metadata (document name, page number, clause ID), and its vector are saved into pgvector/FAISS.
5.  **Querying (The Top-K Retrieval):** 
    *   A user (or an automated script analyzing a new document) submits a query clause: *"Banks must conduct penetration testing annually."*
    *   The query is embedded into a vector.
    *   FAISS performs a similarity search and instantly returns the **Top-K** (e.g., top 5) most relevant clauses from the entire BNM corpus.
6.  **Downstream Processing:** Those Top 5 candidate clauses are then passed to a more expensive, precise model (like a Cross-encoder or an LLM) to determine if there is an exact conflict, alignment, or gap.

---

## 3. How to do Chunking (The Best Way for Legal Text)

If you get chunking wrong, the entire Retrieval-Augmented Generation (RAG) pipeline fails.

### What NOT to do: Naive / Fixed-Token Chunking
Standard tutorials tell you to chunk text every 500 tokens with a 50-token overlap. 
**Do not do this for BNM policies.** 
If you randomly slice a policy document every 500 tokens, you might cut a sentence in half, or worse, you separate a sub-clause `(a)` from its parent paragraph `10.1`, completely stripping it of its context. 

### The Best Way: Structural (Hierarchical) Chunking with Metadata Breadcrumbs
Regulatory text is highly structured. You must chunk according to the document's logical structure.

**Rules for Structural Chunking:**
1.  **Keep Clauses Atomic:** A chunk should ideally be a single, complete logical unit (e.g., a specific paragraph or a bulleted clause).
2.  **Inject Hierarchical Breadcrumbs:** Because a sub-clause by itself might lack context, you must append its "lineage" to the chunk before embedding it.

**Example Scenario:**
Imagine this text in the BNM RMiT document:
```text
Part B: Core Requirements
  Section 10: Cyber Security
    10.1 A financial institution must:
      (a) establish a Security Operations Centre (SOC);
      (b) conduct continuous monitoring.
```

If you just chunk `(a) establish a Security Operations Centre (SOC);`, the embedding model has no idea *who* must do this or *what* it pertains to.

**The Correct Chunking Output:**
You create two separate chunks, and you explicitly prepend the context to the text before passing it to the Bi-encoder:

*   **Chunk 1:** `"Document: RMiT | Part B: Core Requirements | Section 10: Cyber Security | Paragraph 10.1. A financial institution must: (a) establish a Security Operations Centre (SOC);"`
*   **Chunk 2:** `"Document: RMiT | Part B: Core Requirements | Section 10: Cyber Security | Paragraph 10.1. A financial institution must: (b) conduct continuous monitoring."`

### Why this is the "Best Way"
By embedding the structural breadcrumbs directly into the chunk:
1.  **High-Quality Embeddings:** The Bi-encoder understands the full context (it knows this chunk is about Cyber Security and applies to a Financial Institution).
2.  **Perfect Citations:** When FAISS retrieves this chunk, you instantly have the exact structural path (`Part B > Sec 10 > 10.1(a)`) to show the user in the UI.
3.  **Parent-Child Context:** You can store the Parent ID in the vector database metadata. If a user finds Chunk 1, your UI can easily fetch the adjacent clauses to provide full reading context.
