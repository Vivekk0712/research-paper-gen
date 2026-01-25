from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID

class PaperMetadata(BaseModel):
    title: str
    authors: List[str]
    affiliations: List[str]
    keywords: List[str]
    domain: str

class PaperCreate(BaseModel):
    title: str
    domain: str
    authors: List[str]
    affiliations: List[str]
    keywords: List[str]

class PaperResponse(BaseModel):
    paper_id: UUID
    title: str
    domain: Optional[str]
    authors: List[str]
    affiliations: List[str]
    keywords: List[str]
    status: str
    created_at: datetime

class SectionCreate(BaseModel):
    paper_id: UUID
    section_name: str
    content: str
    order_index: int

class SectionResponse(BaseModel):
    section_id: UUID
    paper_id: UUID
    section_name: str
    content: str
    order_index: int
    created_at: datetime

class FileUploadResponse(BaseModel):
    file_id: UUID
    filename: str
    storage_url: str
    file_size: int

class GenerationRequest(BaseModel):
    paper_id: UUID
    section_name: str

class GenerationResponse(BaseModel):
    section_id: UUID
    section_name: str
    content: str
    status: str
