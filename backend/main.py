from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
import uvicorn
import os
import uuid
from pathlib import Path
from typing import List
import google.generativeai as genai
import tempfile

from models import (
    PaperCreate, PaperResponse, SectionCreate, SectionResponse,
    FileUploadResponse, GenerationRequest, GenerationResponse
)
from database import supabase
from services.file_processor import FileProcessor
from services.latex_service import LaTeXService
from services.content_generator import ComprehensiveContentGenerator

from config import get_settings

settings = get_settings()
genai.configure(api_key=settings.gemini_api_key)

# Initialize services
latex_service = LaTeXService()
content_generator = ComprehensiveContentGenerator()

app = FastAPI(title="IEEE Paper Generator API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure upload directory exists
os.makedirs(settings.upload_dir, exist_ok=True)

@app.get("/")
async def root():
    return {"message": "IEEE Paper Generator API"}

@app.post("/api/papers", response_model=PaperResponse)
async def create_paper(paper: PaperCreate):
    """Create a new paper"""
    try:
        result = supabase.table("papers").insert({
            "title": paper.title,
            "domain": paper.domain,
            "authors": paper.authors,
            "affiliations": paper.affiliations,
            "keywords": paper.keywords,
            "status": "draft"
        }).execute()
        
        if result.data:
            return PaperResponse(**result.data[0])
        else:
            raise HTTPException(status_code=400, detail="Failed to create paper")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/papers/{paper_id}", response_model=PaperResponse)
async def get_paper(paper_id: str):
    """Get paper by ID"""
    try:
        result = supabase.table("papers").select("*").eq("paper_id", paper_id).execute()
        
        if result.data:
            return PaperResponse(**result.data[0])
        else:
            raise HTTPException(status_code=404, detail="Paper not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/papers/{paper_id}/upload", response_model=List[FileUploadResponse])
async def upload_files(paper_id: str, files: List[UploadFile] = File(...)):
    """Upload reference files for a paper"""
    try:
        uploaded_files = []
        
        for file in files:
            # Validate file type
            file_ext = Path(file.filename).suffix.lower()
            if file_ext not in settings.allowed_extensions:
                raise HTTPException(
                    status_code=400, 
                    detail=f"File type {file_ext} not allowed"
                )
            
            # Save file
            file_id = str(uuid.uuid4())
            filename = f"{file_id}_{file.filename}"
            file_path = Path(settings.upload_dir) / filename
            
            with open(file_path, "wb") as buffer:
                content = await file.read()
                if len(content) > settings.max_file_size:
                    raise HTTPException(
                        status_code=400,
                        detail="File too large"
                    )
                buffer.write(content)
            
            # Process file and extract text
            text, chunks = FileProcessor.process_file(str(file_path), file_ext)
            
            # Initialize file processor for embeddings
            file_processor = FileProcessor()
            
            # Store file info in database
            file_result = supabase.table("files").insert({
                "file_id": file_id,
                "paper_id": paper_id,
                "filename": file.filename,
                "storage_url": str(file_path),
                "file_size": len(content),
                "file_type": file_ext
            }).execute()
            
            # Store chunks with embeddings
            for i, chunk in enumerate(chunks):
                embedding = file_processor.generate_embeddings(chunk)
                supabase.table("document_chunks").insert({
                    "file_id": file_id,
                    "paper_id": paper_id,
                    "content": chunk,
                    "embedding": embedding,
                    "chunk_index": i,
                    "metadata": {"source": file.filename}
                }).execute()
            
            uploaded_files.append(FileUploadResponse(
                file_id=file_id,
                filename=file.filename,
                storage_url=str(file_path),
                file_size=len(content)
            ))
        
        return uploaded_files
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/papers/{paper_id}/sections", response_model=SectionResponse)
async def create_section(paper_id: str, section: SectionCreate):
    """Create a new section for a paper"""
    try:
        result = supabase.table("sections").insert({
            "paper_id": paper_id,
            "section_name": section.section_name,
            "content": section.content,
            "order_index": section.order_index
        }).execute()
        
        if result.data:
            return SectionResponse(**result.data[0])
        else:
            raise HTTPException(status_code=400, detail="Failed to create section")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/papers/{paper_id}/sections", response_model=List[SectionResponse])
async def get_sections(paper_id: str):
    """Get all sections for a paper"""
    try:
        result = supabase.table("sections").select("*").eq("paper_id", paper_id).order("order_index").execute()
        
        return [SectionResponse(**section) for section in result.data]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/generate", response_model=GenerationResponse)
async def generate_content(request: GenerationRequest):
    """Generate comprehensive content for a specific section using RAG"""
    try:
        # Get paper info
        paper_result = supabase.table("papers").select("*").eq("paper_id", str(request.paper_id)).execute()
        if not paper_result.data:
            raise HTTPException(status_code=404, detail="Paper not found")
        
        paper = paper_result.data[0]
        
        # Generate query embedding
        query = f"{request.section_name} {paper['title']} {paper['domain']}"
        file_processor = FileProcessor()
        query_embedding = file_processor.generate_embeddings(query)
        
        # Retrieve relevant chunks using vector similarity
        chunks_result = supabase.rpc("match_documents", {
            "query_embedding": query_embedding,
            "match_threshold": 0.6,  # Lowered threshold for more context
            "match_count": 10,  # Increased for more comprehensive context
            "paper_id": str(request.paper_id)
        }).execute()
        
        # Prepare comprehensive context from retrieved chunks
        context = ""
        if chunks_result.data:
            context = "\n\n".join([chunk["content"] for chunk in chunks_result.data])
        
        # Generate comprehensive content using enhanced generator
        generated_content = content_generator.generate_section_content(
            section_name=request.section_name,
            paper_title=paper['title'],
            domain=paper['domain'],
            context=context,
            paper_info=paper
        )
        
        # Estimate content metrics
        metrics = content_generator.estimate_content_length(generated_content)
        
        # Save generated section
        section_result = supabase.table("sections").insert({
            "paper_id": str(request.paper_id),
            "section_name": request.section_name,
            "content": generated_content,
            "order_index": 0,  # Will be updated by user
            "metadata": {
                "word_count": metrics["words"],
                "estimated_pages": metrics["estimated_pages"],
                "generation_timestamp": "now()"
            }
        }).execute()
        
        if section_result.data:
            return GenerationResponse(
                section_id=section_result.data[0]["section_id"],
                section_name=request.section_name,
                content=generated_content,
                status="generated"
            )
        else:
            raise HTTPException(status_code=400, detail="Failed to save generated content")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/papers/{paper_id}/export")
async def export_paper(paper_id: str):
    """Export complete paper as formatted text"""
    try:
        # Get paper info
        paper_result = supabase.table("papers").select("*").eq("paper_id", paper_id).execute()
        if not paper_result.data:
            raise HTTPException(status_code=404, detail="Paper not found")
        
        paper = paper_result.data[0]
        
        # Get all sections
        sections_result = supabase.table("sections").select("*").eq("paper_id", paper_id).order("order_index").execute()
        
        # Format paper
        formatted_paper = f"""
{paper['title']}

Authors: {', '.join(paper['authors'])}
Affiliations: {', '.join(paper['affiliations'])}
Keywords: {', '.join(paper['keywords'])}

"""
        
        for section in sections_result.data:
            formatted_paper += f"\n{section['section_name']}\n"
            formatted_paper += "=" * len(section['section_name']) + "\n\n"
            formatted_paper += section['content'] + "\n\n"
        
        return {"paper": formatted_paper}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/papers/{paper_id}/export/latex")
async def export_paper_latex(paper_id: str):
    """Export paper as IEEE-formatted LaTeX"""
    try:
        # Get paper info
        paper_result = supabase.table("papers").select("*").eq("paper_id", paper_id).execute()
        if not paper_result.data:
            raise HTTPException(status_code=404, detail="Paper not found")
        
        paper = paper_result.data[0]
        
        # Get all sections
        sections_result = supabase.table("sections").select("*").eq("paper_id", paper_id).order("order_index").execute()
        
        # Generate LaTeX
        latex_content = latex_service.generate_ieee_paper_latex(paper, sections_result.data)
        
        return {
            "latex": latex_content,
            "filename": f"{paper['title'].replace(' ', '_')}.tex"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/papers/{paper_id}/export/pdf")
async def export_paper_pdf(paper_id: str):
    """Export paper as IEEE-formatted PDF"""
    try:
        # Check if LaTeX is available
        if not latex_service.is_latex_available():
            raise HTTPException(
                status_code=503, 
                detail="LaTeX not available on server. Please install TeX Live or MiKTeX."
            )
        
        # Get paper info
        paper_result = supabase.table("papers").select("*").eq("paper_id", paper_id).execute()
        if not paper_result.data:
            raise HTTPException(status_code=404, detail="Paper not found")
        
        paper = paper_result.data[0]
        
        # Get all sections
        sections_result = supabase.table("sections").select("*").eq("paper_id", paper_id).order("order_index").execute()
        
        # Generate LaTeX
        latex_content = latex_service.generate_ieee_paper_latex(paper, sections_result.data)
        
        # Compile to PDF
        with tempfile.TemporaryDirectory() as temp_dir:
            tex_file, pdf_file = latex_service.compile_to_pdf(latex_content, temp_dir)
            
            # Return PDF file
            filename = f"{paper['title'].replace(' ', '_')}.pdf"
            return FileResponse(
                pdf_file,
                media_type="application/pdf",
                filename=filename
            )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/papers/{paper_id}/generate-complete")
async def generate_complete_paper(paper_id: str):
    """Generate a complete comprehensive IEEE paper with all sections"""
    try:
        # Get paper info
        paper_result = supabase.table("papers").select("*").eq("paper_id", paper_id).execute()
        if not paper_result.data:
            raise HTTPException(status_code=404, detail="Paper not found")
        
        paper = paper_result.data[0]
        
        # Define comprehensive section list for a full paper
        comprehensive_sections = [
            "Abstract",
            "Introduction", 
            "Literature Review",
            "Methodology",
            "System Design",
            "Implementation",
            "Experimental Setup",
            "Results",
            "Discussion",
            "Conclusion",
            "Future Work"
        ]
        
        # Generate query embedding for comprehensive context
        file_processor = FileProcessor()
        query = f"comprehensive research paper {paper['title']} {paper['domain']}"
        query_embedding = file_processor.generate_embeddings(query)
        
        # Retrieve all relevant chunks for comprehensive context
        chunks_result = supabase.rpc("match_documents", {
            "query_embedding": query_embedding,
            "match_threshold": 0.5,  # Lower threshold for more comprehensive context
            "match_count": 20,  # More chunks for comprehensive content
            "paper_id": str(paper_id)
        }).execute()
        
        # Prepare comprehensive context
        context = ""
        if chunks_result.data:
            context = "\n\n".join([chunk["content"] for chunk in chunks_result.data])
        
        generated_sections = []
        total_words = 0
        
        # Generate each section comprehensively
        for section_name in comprehensive_sections:
            try:
                # Generate comprehensive content
                generated_content = content_generator.generate_section_content(
                    section_name=section_name,
                    paper_title=paper['title'],
                    domain=paper['domain'],
                    context=context,
                    paper_info=paper
                )
                
                # Estimate metrics
                metrics = content_generator.estimate_content_length(generated_content)
                total_words += metrics["words"]
                
                # Save generated section
                section_result = supabase.table("sections").insert({
                    "paper_id": str(paper_id),
                    "section_name": section_name,
                    "content": generated_content,
                    "order_index": len(generated_sections),
                    "metadata": {
                        "word_count": metrics["words"],
                        "estimated_pages": metrics["estimated_pages"],
                        "generation_timestamp": "now()"
                    }
                }).execute()
                
                if section_result.data:
                    generated_sections.append({
                        "section_id": section_result.data[0]["section_id"],
                        "section_name": section_name,
                        "word_count": metrics["words"],
                        "estimated_pages": metrics["estimated_pages"]
                    })
                
            except Exception as e:
                print(f"Error generating {section_name}: {str(e)}")
                continue
        
        # Calculate total paper metrics
        total_pages = total_words / 250  # Rough estimate: 250 words per page
        
        return {
            "message": "Complete paper generated successfully",
            "paper_id": paper_id,
            "sections_generated": len(generated_sections),
            "total_words": total_words,
            "estimated_pages": round(total_pages, 1),
            "sections": generated_sections
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

@app.get("/api/latex/status")
async def latex_status():
    """Check LaTeX availability"""
    return {
        "latex_available": latex_service.is_latex_available(),
        "message": "LaTeX is available" if latex_service.is_latex_available() 
                  else "LaTeX not found. Install TeX Live or MiKTeX for PDF export."
    }

@app.get("/api/papers/{paper_id}/metrics")
async def get_paper_metrics(paper_id: str):
    """Get comprehensive metrics for a paper"""
    try:
        # Get all sections for the paper
        sections_result = supabase.table("sections").select("*").eq("paper_id", paper_id).execute()
        
        total_words = 0
        total_sections = len(sections_result.data)
        section_metrics = []
        
        for section in sections_result.data:
            content = section.get('content', '')
            words = len(content.split())
            total_words += words
            
            section_metrics.append({
                "section_name": section.get('section_name', ''),
                "word_count": words,
                "estimated_pages": round(words / 250, 1)
            })
        
        total_pages = round(total_words / 250, 1)
        
        return {
            "paper_id": paper_id,
            "total_sections": total_sections,
            "total_words": total_words,
            "estimated_pages": total_pages,
            "average_words_per_section": round(total_words / max(total_sections, 1)),
            "sections": section_metrics,
            "quality_assessment": {
                "comprehensive": total_pages >= 10,
                "substantial": total_words >= 8000,
                "publication_ready": total_pages >= 8 and total_sections >= 6
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))