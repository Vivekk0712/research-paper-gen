import os
from pathlib import Path
import PyPDF2
from docx import Document
from typing import List, Tuple
import google.generativeai as genai
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer
import numpy as np
from config import get_settings

settings = get_settings()

class FileProcessor:
    """Process uploaded PDF and DOCX files"""
    
    def __init__(self):
        # Initialize the sentence transformer model
        self.embedding_model = SentenceTransformer(settings.embedding_model)
    
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
    
    def generate_embeddings(self, text: str) -> List[float]:
        """Generate embeddings using all-MiniLM-L6-v2 model"""
        try:
            # Generate embedding using sentence transformer
            embedding = self.embedding_model.encode(text, convert_to_tensor=False)
            # Convert to list and ensure it's the right type
            return embedding.tolist() if hasattr(embedding, 'tolist') else list(embedding)
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