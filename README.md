# DreamWeave Brain 🧠✨

An intelligent document ingestion and retrieval system that forms the AI backbone of the DreamWeave project.

The system accepts multiple content formats, extracts information from them, structures the data, generates embeddings, and eventually enables context-aware conversational retrieval (RAG).

---

# System Architecture

```text
User Upload
     │
     ▼
File Processor
     │
     ├── Image → OCR
     ├── PDF → Text Extraction / OCR Fallback
     ├── Notes → Raw Text
     │
     ▼
Raw Text
     │
     ▼
AI Cleanup / Structuring
     │
     ▼
Clean Text
     │
     ▼
Embedding Generator
     │
     ▼
Vector Store
     │
     ▼
Retriever
     │
     ▼
LLM
     │
     ▼
Answer
```

---

# Supported Upload Types

### Images

* PNG
* JPG / JPEG
* WEBP
* Other PIL-supported image formats

### Documents

* PDF (text PDFs)
* Scanned PDFs (OCR fallback)

### Notes

* Plain text files
* User-entered notes

---

# Current Pipeline

## Step 1 : Upload Content

Supported inputs:

* Images
* PDFs
* Notes

Files are stored locally in:

```text
uploads/
```

---

## Step 2 : Text Extraction

### Images

```text
Image
↓
Tesseract OCR
↓
Raw Text
```

---

### PDFs

#### Text-based PDFs

```text
PDF
↓
Direct Text Extraction
↓
Raw Text
```

#### Scanned PDFs

```text
PDF
↓
No Text Found
↓
Convert Pages To Images
↓
OCR
↓
Raw Text
```

Temporary page images are created in the background using Python's `tempfile` module and automatically deleted after OCR.

---

### Notes

```text
Notes
↓
Raw Text
```

No extraction required.

---

# Step 3 : Document Normalization

All extracted content is stored using a unified document structure.

Example:

```json
{
    "id": 1782210867,
    "source": "image",
    "filename": "test.png",

    "raw_content": "...",
    "clean_content": "",

    "metadata": {
        "ocr_used": true,
        "page_count": 1,
        "language": "en",
        "ocr_engine": "tesseract"
    },

    "timestamp": "2026-06-23 16:04:27"
}
```

---

# Step 4 : AI Cleanup & Structuring (Upcoming)

Pipeline:

```text
Raw Text
↓
LLM Cleanup
↓
Clean Text
```

Examples:

* Reconstruct menus
* Fix OCR errors
* Preserve structure
* Improve formatting
* Enhance semantic quality before embedding generation

Both `raw_content` and `clean_content` are preserved.

---

# Step 5 : Embedding Generation (Upcoming)

```text
Text
↓
SentenceTransformer
↓
Vector Embeddings
```

Embeddings will be generated primarily from:

```text
clean_content
```

with fallback to:

```text
raw_content
```

---

# Step 6 : Vector Storage (Upcoming)

Embeddings and metadata will initially be stored locally.

Future migration:

* PostgreSQL
* pgvector

---

# Step 7 : Semantic Search (Upcoming)

```text
Query
↓
Embedding
↓
Cosine Similarity
↓
Relevant Documents
```

Purpose:

* Intelligent search
* Context retrieval
* Recommendation engine support

---

# Step 8 : Retrieval-Augmented Generation (RAG)

```text
User Query
↓
Semantic Search
↓
Relevant Documents
↓
Prompt Construction
↓
LLM
↓
Answer
```

The LLM answers using only the retrieved context from uploaded data.

---

# OCR Roadmap

## Current OCR Engine

```text
Tesseract OCR
```

Advantages:

* Lightweight
* Fast
* Good for clean screenshots and documents

---

## Future OCR Engine

```text
EasyOCR
```

Potential use cases:

* Stylized fonts
* Menus
* Posters
* Multilingual text
* Symbols and currencies
* Complex backgrounds

Future architecture:

```text
Image
↓
Simple Document?
    ↓ yes → Tesseract
    ↓ no
       EasyOCR
```

---

# Future Features

* Automatic language detection
* Multi-language OCR
* Emoji support
* Document chunking
* Metadata extraction
* Summarization
* Recommendation engine
* Vision boards
* Collaborative AI search
* Full RAG-powered assistant

---

# Final System Flow

```text
UPLOAD
   ↓
TEXT EXTRACTION (RAW TEXT)
   ↓
AI CLEANUP / STRUCTURING
   ↓
CLEAN TEXT
   ↓
EMBEDDINGS
   ↓
VECTOR STORAGE
   ↓
SEMANTIC SEARCH
   ↓
RAG
   ↓
CHAT RESPONSE
```
