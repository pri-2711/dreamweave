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

# Step 4 : AI Cleanup & Structuring

Pipeline:

```text
Raw Text
↓
LLM / Heuristic Cleaner
↓
Clean Text
```

Features:
* Reconstruct menus and lists
* Remove OCR artifacts & hyphenated line breaks
* Preserve structure & section headers
* Dual Mode: Uses Gemini/OpenAI API if key present, or local NLP heuristic cleaner
* Both `raw_content` and `clean_content` are preserved in `brain/data/knowledge.json`

---

# Step 5 : Embedding Generation

```text
Clean Content (or Raw Fallback)
↓
Text Chunking
↓
Vector Embeddings (TF-IDF / Dense Feature Space)
↓
Normalized Vectors
```

Chunks text into semantic paragraphs and generates vector representations for indexed document segments.

---

# Step 6 : Vector Storage

Embeddings, document IDs, chunk text, and vocabulary metadata are stored locally in:

```text
brain/data/vectors.json
```

Future migration path:
* PostgreSQL + pgvector

---

# Step 7 : Semantic Search

```text
Query
↓
Query Embedding
↓
Cosine Similarity Match
↓
Top-K Relevant Chunks
```

Purpose:
* Fast context search
* Accurate document snippet matching with relevance scoring

---

# Step 8 : Retrieval-Augmented Generation (RAG)

```text
User Query
↓
Vector Search (Top-K Context Chunks)
↓
Grounded Context Prompt Construction
↓
LLM / Grounded Answer Synthesizer
↓
Cited Answer
```

Answers user queries strictly grounded in retrieved document context with source citations.


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
