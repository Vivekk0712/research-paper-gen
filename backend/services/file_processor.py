import os
from pathlib import Path
import PyPDF2
from docx import Document
from typing import List, Tuple
import google.generativeai as genai
from langchain.text_splitter import RecursiveCharacterTextSplitter
from config import get_settings

settings = get_settings()

class FileProcessor:
    """Process uploaded PDF and DOCX files"""
    
    @staticmethod
    def extract_text_from_pdf(file_path: str) -> str:
        """Extract text from PDF file"""
        text = ""
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
        except Exception as e:
            raise Exception(f"Error extracting text from PDF: {str(e)}")
        return text
    
    @staticmethod
    def extract_text_from_docx(file_path: str) -> str:
        """Extract text from DOCX file"""
        text = ""
        try:
            doc = Document(file_path)
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
        except Exception as e:
            raise Exception(f"Error extracting text from DOCX: {str(e)}")
        return text
    
    @staticmethod
    def chunk_text(text: str, chunk_size: int = None, chunk_overlap: int = None) -> List[str]:
        """Split text into chunks for RAG processing"""
        chunk_size = chunk_size or settings.chunk_size
        chunk_overlap = chunk_overlap or settings.chunk_overlap
        
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
        )
        
        chunks = text_splitter.split_text(text)
        return chunks
    
    @staticmethod
    def generate_embeddings(text: str) -> List[float]:
        """Generate embeddings using Gemini API"""
        try:
            genai.configure(api_key=settings.gemini_api_key)
            result = genai.embed_content(
                model="models/embedding-001",
                content=text,
                task_type="retrieval_document"
            )
            return result['embedding']
        except Exception as e:
            raise Exception(f"Error generating embeddings: {str(e)}")
    
    @classmethod
    def process_file(cls, file_path: str, file_type: str) -> Tuple[str, List[str]]:
        """Process uploaded file and return text and chunks"""
        if file_type.lower() == '.pdf':
            text = cls.extract_text_from_pdf(file_path)
        elif file_type.lower() == '.docx':
            text = cls.extract_text_from_docx(file_path)
        else:
            raise ValueError(f"Unsupported file type: {file_type}")
        
        chunks = cls.chunk_text(text)
        return text, chunks