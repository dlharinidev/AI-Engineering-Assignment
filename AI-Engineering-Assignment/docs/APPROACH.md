# Approach Document — CT-200 AI Engineering Assignment

## Overview

This document describes the engineering decisions made while building the **CardioTrack CT-200 Manual Parser & Test Case Generator** — a FastAPI backend that ingests versioned product manuals, detects changed sections, and generates structured QA test cases using an LLM.

---

## 1. Document Parsing Strategy

### Hybrid OCR + Direct Text Extraction

The `DocumentParser` uses a two-stage approach to handle a wide range of PDF types:

1. **OCR-first (pytesseract + pdf2image):** Attempted first to handle scanned or image-based PDFs.
2. **Direct text fallback (pypdf):** Used when OCR binaries (Tesseract, Poppler) are not installed — which is common on Windows dev machines.

This approach ensures the parser **never crashes** even without OCR binaries installed.

### Hierarchy Reconstruction

Sections are identified using regex matching against numbered section patterns:

| Pattern | Level | Example |
|---|---|---|
| All-uppercase, length > 10 | 0 (Document Title) | `CARDIOTRACK CT-200 USER MANUAL` |
| `N.0 Heading` | 1 (Major Section) | `1.0 Introduction` |
| `N.M Heading` | 2 (Subsection) | `2.1 Pressure Safety Limits` |

Parent-child relationships are maintained using an `active_nodes` dict that tracks the last-seen node at each level.

### Content Hashing

Each node's `content_hash` is computed as **SHA-256 of `heading + content`**. This provides:
- Cheap change detection without storing full diffs.
- Deterministic hashing — same input always yields the same hash.

---

## 2. Versioning & Staleness Detection

### Node Matching Strategy

When a new document version is ingested, nodes from the previous version are matched using a **(level, heading)** composite key:

```python
v1_map = {(n.level, n.heading): n for n in v1_nodes}
```

- **Matched node:** The `logical_node_id` (a UUID) is **preserved** from v1, ensuring traceability across versions.
- **New node:** A fresh UUID is generated as the `logical_node_id`.
- **Staleness:** A node is marked stale if its `content_hash` has changed between versions.

### Staleness Check API

The `GET /staleness/{selection_id}` endpoint:
1. Retrieves the stored generation snapshot (which includes hashes at the time of generation) from the NoSQL store.
2. Looks up the **latest** version of the same logical node by `logical_node_id`.
3. Compares the stored hash with the current hash to detect changes.

---

## 3. NoSQL Storage

### MongoDB with JSON Fallback

LLM-generated test cases and generation metadata are stored in a NoSQL collection (unstructured, schema-free):

- **Primary:** MongoDB via `pymongo` if a local instance is running.
- **Fallback:** A file-based `JSONCollectionFallback` class that mimics the MongoDB `insert_one` / `find_one` / `find` interface using a local JSON file (`nosql_fallback.json`).

This means the system works **out of the box with no dependencies on a running MongoDB instance**.

---

## 4. LLM Integration

### OpenAI gpt-4o with Structured JSON Output

The LLM module calls OpenAI's `chat.completions.create` with `response_format={"type": "json_object"}` to enforce structured output. Each generated test case contains:
- `title`: Short description of the test.
- `steps`: Ordered list of actions.
- `expected_result`: What should happen.

### Graceful Degradation

If `OPENAI_API_KEY` is not set, or if the API call fails, the module returns a set of **mock test cases** pre-filled with CT-200-relevant scenarios. This ensures the API is always functional and testable without an OpenAI account.

---

## 5. Database Design

| Store | Technology | Used For |
|---|---|---|
| Relational | SQLite (via SQLAlchemy) | Documents, Nodes, Selections |
| NoSQL | MongoDB / JSON file | LLM Generations, Test Cases |

### Why This Split?

- **Structured data** (document hierarchy, versioning) benefits from relational queries with joins and ordering.
- **Unstructured data** (LLM output, which varies in shape) is best stored schema-free in a document store.

---

## 6. Tradeoffs & Limitations

| Decision | Rationale | Tradeoff |
|---|---|---|
| (level, heading) matching | Simple, no extra metadata needed | Fails if a heading is renamed between versions |
| SHA-256 hash of heading+content | Cheap and deterministic | Cannot detect which part of content changed |
| pypdf fallback over OCR | Works on all Windows systems | Loses OCR capability for scanned PDFs |
| JSON file as NoSQL fallback | Zero-dependency NoSQL | Not scalable for production use |

---

## 7. If I Had One More Day

The weakest part of this submission is the **absence of a CI pipeline**. The first thing I would add is a GitHub Actions workflow that:
1. Runs `pytest` on every push and pull request.
2. Validates the app starts up cleanly via `uvicorn`.
3. Reports test coverage.
