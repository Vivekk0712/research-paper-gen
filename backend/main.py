from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse, Response
import uvicorn
import os
import uuid
import shutil
from pathlib import Path
from typing import List
import google.genai as genai
import tempfile

from models import (
    PaperCreate, PaperResponse, SectionCreate, SectionResponse,
    FileUploadResponse, GenerationRequest, GenerationResponse
)
from database import supabase
from services.file_processor import FileProcessor
from services.latex_service_v2 import latex_service
from services.background_tasks import background_task_manager

from config import get_settings

settings = get_settings()

# Initialize services with lazy loading
_file_processor = None
content_generator = background_task_manager.content_generator

def get_file_processor():
    """Get file processor instance with lazy loading"""
    global _file_processor
    if _file_processor is None:
        print("🔄 Initializing file processor...")
        _file_processor = FileProcessor()
    return _file_processor

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
    """Root endpoint with system status"""
    return {
        "message": "IEEE Paper Generator API",
        "status": "running",
        "version": "1.0.0",
        "features": {
            "paper_generation": True,
            "file_upload": True,
            "latex_export": True,
            "pdf_export": latex_service.is_latex_available(),
            "background_tasks": True
        }
    }

@app.get("/api/papers", response_model=List[PaperResponse])
async def list_papers():
    """List all papers"""
    try:
        result = supabase.table("papers").select("*").order("created_at", desc=True).execute()
        
        return [PaperResponse(**paper) for paper in result.data]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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

@app.get("/api/papers/{paper_id}/files", response_model=List[FileUploadResponse])
async def get_files(paper_id: str):
    """Get all files for a paper"""
    try:
        result = supabase.table("files").select("*").eq("paper_id", paper_id).execute()
        
        return [FileUploadResponse(
            file_id=file["file_id"],
            filename=file["filename"],
            storage_url=file["storage_url"],
            file_size=file["file_size"]
        ) for file in result.data]
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
            
            # Store file info in database first (quick response)
            file_result = supabase.table("files").insert({
                "file_id": file_id,
                "paper_id": paper_id,
                "filename": file.filename,
                "storage_url": str(file_path),
                "file_size": len(content),
                "file_type": file_ext
            }).execute()
            
            uploaded_files.append(FileUploadResponse(
                file_id=file_id,
                filename=file.filename,
                storage_url=str(file_path),
                file_size=len(content)
            ))
        
        # Process files asynchronously in background
        import asyncio
        asyncio.create_task(process_files_background(paper_id, uploaded_files))
        
        return uploaded_files
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def process_files_background(paper_id: str, uploaded_files: List[FileUploadResponse]):
    """Process files in background to avoid timeout"""
    try:
        file_processor = get_file_processor()
        
        for file_info in uploaded_files:
            # Process file and extract text
            file_path = file_info.storage_url
            file_ext = Path(file_info.filename).suffix.lower()
            
            text, chunks = FileProcessor.process_file(file_path, file_ext)
            
            # Store chunks with embeddings
            for i, chunk in enumerate(chunks):
                try:
                    embedding = file_processor.generate_embeddings(chunk)
                    supabase.table("document_chunks").insert({
                        "file_id": file_info.file_id,
                        "paper_id": paper_id,
                        "content": chunk,
                        "embedding": embedding,
                        "chunk_index": i,
                        "metadata": {"source": file_info.filename}
                    }).execute()
                except Exception as e:
                    print(f"Error processing chunk {i} for file {file_info.filename}: {e}")
                    continue
                    
    except Exception as e:
        print(f"Background processing error: {e}")

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
        file_processor = get_file_processor()
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
        
        # Save generated section (with metadata if column exists)
        section_data = {
            "paper_id": str(request.paper_id),
            "section_name": request.section_name,
            "content": generated_content,
            "order_index": 0,  # Will be updated by user
            "metadata": {
                "word_count": metrics["words"],
                "estimated_pages": metrics["estimated_pages"],
                "generation_timestamp": "now()"
            }
        }
        
        try:
            section_result = supabase.table("sections").insert(section_data).execute()
        except Exception as db_error:
            # If metadata column doesn't exist, try without it
            if "metadata" in str(db_error):
                print("⚠️  Metadata column not found, saving without metadata")
                section_data.pop("metadata", None)
                section_result = supabase.table("sections").insert(section_data).execute()
            else:
                raise db_error
        
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
    """Export paper as IEEE-formatted PDF using LaTeX/MiKTeX"""
    try:
        # Check if LaTeX is available
        if not latex_service.is_latex_available():
            raise HTTPException(
                status_code=503, 
                detail="LaTeX not available. Please install MiKTeX from https://miktex.org/"
            )
        
        # Get paper info
        paper_result = supabase.table("papers").select("*").eq("paper_id", paper_id).execute()
        if not paper_result.data:
            raise HTTPException(status_code=404, detail="Paper not found")
        
        paper = paper_result.data[0]
        
        # Get all sections
        sections_result = supabase.table("sections").select("*").eq("paper_id", paper_id).order("order_index").execute()
        
        if not sections_result.data:
            raise HTTPException(status_code=400, detail="No sections found. Please generate some content first.")
        
        # Generate LaTeX
        latex_content = latex_service.generate_ieee_paper_latex(paper, sections_result.data)
        
        # Compile to PDF
        tex_file, pdf_file = latex_service.compile_to_pdf(latex_content)
        
        # Read PDF content into memory
        with open(pdf_file, 'rb') as f:
            pdf_content = f.read()
        
        # Clean up temp files
        try:
            os.unlink(tex_file)
            os.unlink(pdf_file)
            # Also clean up the temp directory
            temp_dir = os.path.dirname(pdf_file)
            if temp_dir and os.path.exists(temp_dir):
                import shutil
                shutil.rmtree(temp_dir, ignore_errors=True)
        except:
            pass  # Ignore cleanup errors
        
        # Return PDF content as response
        filename = f"{paper['title'].replace(' ', '_').replace('/', '_')}.pdf"
        
        from fastapi.responses import Response
        return Response(
            content=pdf_content,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "Content-Length": str(len(pdf_content))
            }
        )
        
    except Exception as e:
        print(f"PDF export error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {str(e)}")

@app.post("/api/papers/{paper_id}/resume-generation")
async def resume_paper_generation(paper_id: str):
    """Resume paper generation from where it left off"""
    try:
        # Get paper info
        paper_result = supabase.table("papers").select("*").eq("paper_id", paper_id).execute()
        if not paper_result.data:
            raise HTTPException(status_code=404, detail="Paper not found")
        
        paper = paper_result.data[0]
        
        # Check current status
        if paper.get("status") == "completed":
            return {"message": "Paper generation already completed", "paper_id": paper_id}
        
        # Test API connection first
        if not content_generator.test_api_connection():
            raise HTTPException(status_code=503, detail="Gemini API quota exceeded or unavailable. Please wait and try again later.")
        
        # Start background generation (it will resume from where it left off)
        task_id = background_task_manager.start_paper_generation(paper_id)
        
        return {
            "message": "Paper generation resumed in background",
            "paper_id": paper_id,
            "task_id": task_id,
            "status": "resumed"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/papers/{paper_id}/generate-complete")
async def generate_complete_paper(paper_id: str):
    """Start generating a complete comprehensive IEEE paper in the background"""
    try:
        # Test API connection first
        if not content_generator.test_api_connection():
            raise HTTPException(status_code=503, detail="Gemini API quota exceeded or unavailable. Please wait and try again later.")
        
        # Get paper info
        paper_result = supabase.table("papers").select("*").eq("paper_id", paper_id).execute()
        if not paper_result.data:
            raise HTTPException(status_code=404, detail="Paper not found")
        
        # Start background generation
        task_id = background_task_manager.start_paper_generation(paper_id)
        
        return {
            "message": "Paper generation started in background",
            "paper_id": paper_id,
            "task_id": task_id,
            "status": "started",
            "note": "Use the processing-status endpoint to check progress"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/papers/{paper_id}/generation-status")
async def get_generation_status(paper_id: str):
    """Get detailed generation status for a paper"""
    try:
        # Get paper status
        paper_result = supabase.table("papers").select("*").eq("paper_id", paper_id).execute()
        if not paper_result.data:
            raise HTTPException(status_code=404, detail="Paper not found")
        
        paper = paper_result.data[0]
        
        # Get sections count
        sections_result = supabase.table("sections").select("section_id").eq("paper_id", paper_id).execute()
        sections_count = len(sections_result.data)
        
        # Check if there's an active background task
        task_id = f"generate_paper_{paper_id}"
        task_status = background_task_manager.get_task_status(task_id)
        
        return {
            "paper_id": paper_id,
            "paper_status": paper.get("status", "draft"),
            "sections_generated": sections_count,
            "background_task": task_status,
            "metadata": paper.get("metadata", {}) if "metadata" in paper else {}
        }
        
    except Exception as e:
        return {
            "paper_id": paper_id,
            "error": str(e),
            "paper_status": "unknown",
            "sections_generated": 0,
            "background_task": {"status": "not_found"},
            "metadata": {}
        }

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

@app.get("/api/latex/test")
async def test_latex():
    """Test LaTeX compilation with a simple document"""
    if not latex_service.is_latex_available():
        raise HTTPException(
            status_code=503, 
            detail="LaTeX not available. Please install TeX Live or MiKTeX."
        )
    
    try:
        # Create a minimal test document
        test_latex = r"""
\documentclass[conference]{IEEEtran}
\begin{document}
\title{LaTeX Test Document}
\author{\IEEEauthorblockN{Test Author}\IEEEauthorblockA{Test University\\Email: test@university.edu}}
\maketitle

\begin{abstract}
This is a test document to verify LaTeX compilation is working correctly.
\end{abstract}

\section{Introduction}
This is a test section to verify that the LaTeX installation is working properly.

\section{Conclusion}
LaTeX compilation is working successfully.

\end{document}
"""
        
        # Compile test document
        with tempfile.TemporaryDirectory() as temp_dir:
            tex_file, pdf_file = latex_service.compile_to_pdf(test_latex, temp_dir)
            
            return {
                "status": "success",
                "message": "LaTeX compilation test passed",
                "tex_file": tex_file,
                "pdf_generated": os.path.exists(pdf_file)
            }
    
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"LaTeX test failed: {str(e)}"
        )

@app.get("/api/latex/test-pdf")
async def test_pdf_download():
    """Test PDF download with a simple document"""
    if not latex_service.is_latex_available():
        raise HTTPException(
            status_code=503, 
            detail="LaTeX not available. Please install TeX Live or MiKTeX."
        )
    
    try:
        # Create a simple test document
        simple_latex = r"""
\documentclass{article}
\begin{document}
\title{Test PDF Download}
\author{Test Author}
\maketitle

\section{Introduction}
This is a test PDF to verify the download functionality is working.

\section{Conclusion}
If you can download this PDF, the system is working correctly.

\end{document}
"""
        
        # Compile test document
        tex_file, pdf_file = latex_service.compile_to_pdf(simple_latex)
        
        # Read PDF content into memory
        with open(pdf_file, 'rb') as f:
            pdf_content = f.read()
        
        # Clean up temp files
        try:
            os.unlink(tex_file)
            os.unlink(pdf_file)
            temp_dir = os.path.dirname(pdf_file)
            if temp_dir and os.path.exists(temp_dir):
                shutil.rmtree(temp_dir, ignore_errors=True)
        except:
            pass
        
        # Return PDF content as response
        return Response(
            content=pdf_content,
            media_type="application/pdf",
            headers={
                "Content-Disposition": "attachment; filename=test.pdf",
                "Content-Length": str(len(pdf_content))
            }
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Test PDF generation failed: {str(e)}"
        )

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

@app.get("/api/papers/{paper_id}/processing-status")
async def get_processing_status(paper_id: str):
    """Check file processing and paper generation status"""
    try:
        # Get paper info with current status
        paper_result = supabase.table("papers").select("*").eq("paper_id", paper_id).execute()
        if not paper_result.data:
            raise HTTPException(status_code=404, detail="Paper not found")
        
        paper = paper_result.data[0]
        
        # Get files for this paper
        files_result = supabase.table("files").select("*").eq("paper_id", paper_id).execute()
        
        # Get chunks for this paper
        chunks_result = supabase.table("document_chunks").select("file_id").eq("paper_id", paper_id).execute()
        
        # Get sections for this paper
        sections_result = supabase.table("sections").select("*").eq("paper_id", paper_id).execute()
        
        total_files = len(files_result.data)
        processed_files = len(set(chunk["file_id"] for chunk in chunks_result.data))
        total_sections = len(sections_result.data)
        
        # File processing status
        file_processing = {
            "total_files": total_files,
            "processed_files": processed_files,
            "processing_complete": processed_files == total_files,
            "progress_percentage": round((processed_files / max(total_files, 1)) * 100)
        }
        
        # Paper generation status (handle missing metadata column gracefully)
        paper_status = paper.get("status", "draft")
        paper_metadata = paper.get("metadata", {}) if "metadata" in paper else {}
        
        generation_status = {
            "status": paper_status,
            "sections_generated": total_sections,
            "current_section": paper_metadata.get("current_section", ""),
            "progress_percentage": paper_metadata.get("progress_percentage", 0),
            "total_words": paper_metadata.get("total_words", 0),
            "estimated_pages": paper_metadata.get("estimated_pages", 0)
        }
        
        return {
            "paper_id": paper_id,
            "file_processing": file_processing,
            "generation_status": generation_status,
            "overall_status": paper_status
        }
        
    except Exception as e:
        print(f"Processing status error: {str(e)}")
        # Return basic status if there's an error
        return {
            "paper_id": paper_id,
            "file_processing": {
                "total_files": 0,
                "processed_files": 0,
                "processing_complete": True,
                "progress_percentage": 100
            },
            "generation_status": {
                "status": "unknown",
                "sections_generated": 0,
                "current_section": "",
                "progress_percentage": 0,
                "total_words": 0,
                "estimated_pages": 0
            },
            "overall_status": "unknown",
            "error": str(e)
        }