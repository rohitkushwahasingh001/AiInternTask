# backend/app/models/responses.py

from pydantic import BaseModel
from typing import List, Optional, Dict

class DocumentInfo(BaseModel):
    document_id: str
    filename: str
    uploaded_at: str

class DocumentUploadResponse(BaseModel):
    message: str
    document_ids: List[str]

class DocumentsListResponse(BaseModel):
    documents: List[DocumentInfo]

class Citation(BaseModel):
    document_id: str
    filename: str
    page: int
    paragraph: int
    text_content: str

class QueryResponse(BaseModel):
    synthesized_response: str
    tabular_citations: List[Citation] 

class Theme(BaseModel): 
    theme_name: str
    description: str
    documents: List[str] # List of document IDs relevant to this theme

class ThemeIdentificationResponse(BaseModel): # New Response Model
    message: str
    themes: List[Theme]

