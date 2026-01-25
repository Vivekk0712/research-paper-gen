# IEEE Research Paper Generator (Hackathon MVP)

## 1. Product Overview

The IEEE Research Paper Generator is a web-based application that automatically generates a **fully IEEE-formatted research paper** by analyzing uploaded review papers and user-provided metadata. The system leverages **LLMs + RAG + LaTeX automation** to ensure academic tone, citation grounding, and IEEE compliance.

This product is designed primarily for **hackathons, academic demos, and research assistance**, not to replace human authorship.

---

## 2. Problem Statement

Writing an IEEE-compliant research paper is time-consuming and error-prone due to:

* Strict formatting requirements
* Manual extraction of content from review papers
* Citation management
* Iterative rewriting of sections

Existing AI writing tools:

* Do not guarantee IEEE compliance
* Hallucinate citations
* Generate unstructured content

---

## 3. Goals & Objectives

### Primary Goals

* Generate **publication-ready IEEE papers** in PDF format
* Ensure content is **grounded in uploaded review papers**
* Allow **section-wise generation and regeneration**

### Success Metrics

* IEEE template compiles without errors
* Each section generated independently
* Paper generation time < 2 minutes
* Minimal hallucination (RAG-enforced)

---

## 4. Target Users

* Undergraduate & postgraduate students
* Hackathon participants
* Early-stage researchers
* IEEE student members

---

## 5. Core Features (MVP)

### 5.1 Document Upload

* Upload 1–3 review papers (PDF/DOCX)
* File size limit: 10 MB per file

### 5.2 Metadata Input

* Paper title
* Author names & affiliations
* Keywords
* Research domain

### 5.3 Section-wise Generation

Generated sequentially:

1. Abstract
2. Keywords
3. Introduction
4. Related Work
5. Methodology / System Architecture
6. Conclusion & Future Work

Each section:

* Generated via separate LLM call
* Stored independently
* Can be regenerated

### 5.4 IEEE Formatting Engine

* Uses LaTeX (IEEEtran)
* Injects generated sections
* Compiles PDF via pdflatex

### 5.5 Download & Preview

* Preview generated paper
* Download IEEE-compliant PDF

---

## 6. Non-Goals (Out of Scope for MVP)

* Claiming research novelty
* Journal/conference submission
* Automated plagiarism rewriting
* Reviewer acceptance guarantees

---

## 7. Tech Stack

### Frontend

* React (Vite)
* Tailwind CSS
* React Hook Form

### Backend

* FastAPI (Python)
* LangChain

### Database & Storage

* Supabase (Postgres + pgvector)
* Supabase Storage

### AI & NLP

* Gemini 2.5 Flash (LLM)
* Embeddings + RAG

### Formatting

* LaTeX (IEEEtran)
* pdflatex

---

## 8. Data Model (High-Level)

### Papers Table

* paper_id
* title
* domain
* created_at

### Sections Table

* section_id
* paper_id
* section_name
* content

### Files Table

* file_id
* paper_id
* storage_url

---

## 9. Ethical & Academic Safeguards

* Content grounded only in uploaded review papers
* Mandatory citation-based generation
* Disclaimer: AI-assisted drafting tool

---

## 10. Risks & Mitigations

| Risk                 | Mitigation                   |
| -------------------- | ---------------------------- |
| Hallucinated content | RAG enforcement              |
| Formatting errors    | LaTeX IEEE template          |
| Long generation time | Section-wise async calls     |
| Plagiarism concerns  | Similarity checks (optional) |

---

## 11. Future Enhancements

* Multi-author collaboration
* Citation auto-numbering
* DOCX export
* Upgradeable LLM selection

---

## 12. Hackathon Pitch (1-liner)

> "An AI-powered system that converts review literature into **IEEE-compliant, publication-ready research papers** using RAG and LaTeX automation."
