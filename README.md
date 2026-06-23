User Upload
    │
    ▼
File Processor
    │
    ├── Image → OCR
    ├── PDF → Text Extraction
    ├── Note → Raw Text
    │
    ▼
Text Content
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

## STEPS

### Step 1: Upload content

1. Include only : images, pdfs, notes

2. Store locally in uploads

### Step 2: Extract Text

1. Images -> OCR : using tesseract

2. PDF -> text extraction -> plain text: pymupdf or pypdf

3. Notes -> already in text

### Step 3: Normalizing content

Content in same structure : JSON

### Step 4: Creating Embeddings

Using SentenceTransformer : Text -> Vectors

### Step 5: Store knowledge in Json format

### Step 6: Semantic search : cosine similarity

For searching through records

### Step 7: RAG

Retrieving info using uploaded data 

1. Build prompt using uploaded data

2. Send to LLM

3. LLM answers using retrieved context


# FLOW OF SYSTEM :

UPLOAD
   ↓
TEXT EXTRACTION (raw text)
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
