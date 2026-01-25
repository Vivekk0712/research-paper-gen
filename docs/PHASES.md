# Development Phases – IEEE Research Paper Generator

This document outlines the **phase-wise development plan** for building the IEEE Research Paper Generator during a hackathon or short sprint. Each phase is designed to be **independently demoable**, allowing partial completion without breaking the overall product.

---

## Phase 0: Planning & Setup (Pre-Hackathon / Hour 0–2)

### Objectives

* Finalize scope (MVP only)
* Lock tech stack
* Prepare templates and credentials

### Tasks

* Decide LLM: Gemini 2.5 Flash
* Create Supabase project (DB + Storage)
* Prepare IEEE LaTeX template (IEEEtran)
* Setup Git repository & branches

### Deliverables

* Repo initialized
* Environment variables configured
* IEEE LaTeX template ready

---

## Phase 1: Frontend Skeleton (Hour 2–6)

### Objectives

* User can interact with UI
* Metadata input captured

### Features

* Landing page
* Paper metadata form:

  * Title
  * Authors
  * Affiliations
  * Keywords
* File upload UI (PDF/DOCX)

### Tech

* React + Vite
* Tailwind CSS
* React Hook Form

### Deliverables

* Functional UI
* Metadata submission endpoint connected

---

## Phase 2: Backend Core & File Processing (Hour 6–12)

### Objectives

* Backend API functional
* Uploaded files processed

### Features

* FastAPI project structure
* File upload endpoint
* PDF/DOCX text extraction
* Chunking & preprocessing

### Libraries

* FastAPI
* PyMuPDF / pdfplumber
* python-docx

### Deliverables

* Extracted text available in backend
* Files stored in Supabase Storage

---

## Phase 3: Embeddings & RAG Pipeline (Hour 12–18)

### Objectives

* Enable grounded generation
* Prevent hallucinations

### Features

* Text chunking
* Embedding generation
* Vector storage using pgvector
* Retrieval by semantic similarity

### Tech

* LangChain
* Supabase pgvector
* Gemini / embedding model

### Deliverables

* Review-paper knowledge base ready
* Retrieval queries returning relevant chunks

---

## Phase 4: Section-wise Paper Generation (Hour 18–26)

### Objectives

* Generate IEEE paper content

### Generation Order

1. Abstract
2. Keywords
3. Introduction
4. Related Work
5. Methodology
6. Conclusion & Future Work

### Key Rules

* One section = one LLM call
* Each section stored independently
* Regeneration supported

### Deliverables

* All paper sections generated
* Stored in database

---

## Phase 5: IEEE Formatting & PDF Generation (Hour 26–32)

### Objectives

* Produce publication-ready output

### Features

* Inject generated text into IEEE LaTeX template
* Compile using pdflatex
* Handle compile errors gracefully

### Deliverables

* IEEE-compliant PDF generated
* Download functionality

---

## Phase 6: Similarity Analysis & Safeguards (Hour 32–36)

### Objectives

* Address plagiarism concerns

### Features

* Semantic similarity scoring
* Compare generated sections vs source papers
* Flag high similarity content

### Tech

* Embeddings + cosine similarity

### Deliverables

* Similarity score per section
* Academic integrity disclaimer

---

## Phase 7: Final Polish & Demo Prep (Hour 36–48)

### Objectives

* Make demo smooth and impressive

### Tasks

* UI polishing
* Loading states & progress indicators
* Error handling
* Prepare pitch & screenshots

### Deliverables

* Demo-ready product
* Clear explanation flow for judges

---

## Phase Dependency Graph (Simplified)

Phase 1 → Phase 2 → Phase 3 → Phase 4 → Phase 5
↓
Phase 6

---

## Key Hackathon Strategy

* Even if stopped at Phase 4, demo is strong
* Phase 5 makes it stand out
* Phase 6 answers judge ethics questions

---

## Final Note

This phased approach ensures **incremental value**, **clear ownership**, and **low risk**, making it ideal for hackathons and short development cycles.
