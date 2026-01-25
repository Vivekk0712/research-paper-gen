from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import os
import uuid
from pathlib import Path
from typing import List
import google.generativeai as genai

from models import (
    PaperCreate, PaperResponse, SectionCreate, SectionResponse,
    FileUploadResponse, GenerationRequest, GenerationResponse
)
from database import supabase
from services.file_processor import FileProcessor
from config import get_settings

settings = get_settings()
genai.configure(api_key=settings.gemini_api_key)

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
    """Generate content for a specific section using RAG"""
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
            "match_threshold": 0.7,
            "match_count": settings.top_k_results,
            "paper_id": str(request.paper_id)
        }).execute()
        
        # Prepare context from retrieved chunks
        context = ""
        if chunks_result.data:
            context = "\n\n".join([chunk["content"] for chunk in chunks_result.data])
        
        # Generate content using Gemini 2.5 Flash
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        
        prompt = f"""
        You are an expert academic writer specializing in IEEE format papers.
        
        Paper Title: {paper['title']}
        Domain: {paper['domain']}
        Section: {request.section_name}
        
        Context from uploaded reference papers:
        {context}
        
        Generate a comprehensive {request.section_name} section for this IEEE paper.
        Follow IEEE formatting guidelines and academic writing standards.
        Include proper citations where appropriate (use [1], [2], etc. format).
        Make sure the content is relevant to the domain and builds upon the provided context.
        
        The section should be well-structured, technically accurate, and suitable for publication.
        """
        
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                max_output_tokens=settings.max_tokens,
                temperature=settings.temperature,
            )
        )
        
        generated_content = response.text
        
        # Save generated section
        section_result = supabase.table("sections").insert({
            "paper_id": str(request.paper_id),
            "section_name": request.section_name,
            "content": generated_content,
            "order_index": 0  # Will be updated by user
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

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
