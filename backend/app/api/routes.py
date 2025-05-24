# backend/app/api/routes.py

from fastapi import APIRouter, UploadFile, File, HTTPException, Form, Depends
from fastapi.responses import JSONResponse
from typing import List, Dict
import logging
import os
import shutil

from app.services.document_processor import DocumentProcessor
from app.services.vector_db_service import VectorDBService
from app.services.chat_service import ChatService
from app.services.theme_identifier import ThemeIdentifierService
from app.core.config import settings
from app.models.responses import DocumentUploadResponse, QueryResponse, DocumentsListResponse, ThemeIdentificationResponse, DocumentInfo

logger = logging.getLogger(__name__)

router = APIRouter()

# --- Dependency Injection Functions ---
def get_vector_db_service() -> VectorDBService:
    """Provides the VectorDBService instance."""
    return VectorDBService(db_path=settings.CHROMA_PERSIST_DIR)

def get_document_processor() -> DocumentProcessor:
    """Provides the DocumentProcessor instance."""
    return DocumentProcessor(upload_dir=settings.UPLOAD_DIR)

#
def get_chat_service() -> ChatService:
    """Provides the ChatService instance."""
    # ChatService now only takes gemini_api_key in its constructor
    return ChatService(gemini_api_key=settings.GEMINI_API_KEY)

def get_theme_identifier_service(
    vector_db_service: VectorDBService = Depends(get_vector_db_service)
) -> ThemeIdentifierService:
    """Provides the ThemeIdentifierService instance."""
    from langchain_google_genai import ChatGoogleGenerativeAI
    llm = ChatGoogleGenerativeAI(model="gemini-pro", google_api_key=settings.GEMINI_API_KEY)
    return ThemeIdentifierService(vector_store=vector_db_service, llm=llm)


# --- API Endpoints ---

@router.post("/upload-documents/", response_model=DocumentUploadResponse)
async def upload_documents(
    files: List[UploadFile] = File(...),
    doc_processor: DocumentProcessor = Depends(get_document_processor),
    vector_db_service: VectorDBService = Depends(get_vector_db_service)
):
    """
    Uploads multiple documents, processes them, and adds their chunks to the vector database.
    """
    if not files:
        raise HTTPException(status_code=400, detail="No files provided for upload.")

    uploaded_doc_ids = []
    processed_files_info = await doc_processor.process_documents(files)

    for doc_info in processed_files_info:
        if "chunks" in doc_info and doc_info["chunks"]:
            vector_db_service.add_documents(doc_info["chunks"])
            uploaded_doc_ids.append(doc_info["document_id"])
            logger.info(f"Added chunks for document ID: {doc_info['document_id']}")
        else:
            logger.warning(f"No chunks generated for {doc_info.get('filename', 'unknown file')}. Status: {doc_info.get('status', 'N/A')}")

    if not uploaded_doc_ids:
        raise HTTPException(status_code=500, detail="No documents were successfully processed and added to the database.")

    return DocumentUploadResponse(
        message="Documents uploaded and processed.",
        document_ids=uploaded_doc_ids
    )

@router.get("/documents/", response_model=DocumentsListResponse)
async def list_documents(
    vector_db_service: VectorDBService = Depends(get_vector_db_service)
):
    """
    Lists all documents currently in the knowledge base.
    """
    try:
        documents = vector_db_service.list_documents()
        document_info_list = [
            DocumentInfo(document_id=doc['document_id'], filename=doc['filename'], uploaded_at="N/A")
            for doc in documents
        ]
        return DocumentsListResponse(documents=document_info_list)
    except Exception as e:
        logger.error(f"Error listing documents: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to retrieve documents: {e}")

@router.post("/query/", response_model=QueryResponse)
async def query_documents(
    query_text: str = Form(...),
    chat_service: ChatService = Depends(get_chat_service),
    vector_db_service: VectorDBService = Depends(get_vector_db_service) # Inject VectorDBService
):
    """
    Answers a query based on the uploaded documents.
    """
    if not query_text.strip():
        raise HTTPException(status_code=400, detail="Query text cannot be empty.")

    try:
        # Pass vector_db_service directly to chat_service.query_documents method
        response_data = await chat_service.query_documents(query_text, vector_db_service)
        return QueryResponse(
            synthesized_response=response_data["synthesized_response"],
            tabular_citations=response_data["tabular_citations"]
        )
    except Exception as e:
        logger.error(f"Error processing query: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get response: {e}")

@router.post("/identify-themes/", response_model=ThemeIdentificationResponse)
async def identify_themes_endpoint(
    theme_identifier_service: ThemeIdentifierService = Depends(get_theme_identifier_service)
):
    """
    Identifies common themes from the uploaded documents.
    """
    try:
        themes = await theme_identifier_service.identify_themes()
        if not themes:
            raise HTTPException(status_code=404, detail="No themes identified. Ensure documents are uploaded.")
        return ThemeIdentificationResponse(message="Themes identified successfully!", themes=themes)
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error identifying themes: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to identify themes: {e}")

@router.post("/clear-data/")
async def clear_data(
    vector_db_service: VectorDBService = Depends(get_vector_db_service),
    doc_processor: DocumentProcessor = Depends(get_document_processor)
):
    """
    Endpoint to clear all uploaded documents and reset the ChromaDB.
    """
    try:
        if os.path.exists(settings.UPLOAD_DIR):
            shutil.rmtree(settings.UPLOAD_DIR)
            os.makedirs(settings.UPLOAD_DIR)
            logger.info(f"Cleared upload directory: {settings.UPLOAD_DIR}")
        
        vector_db_service.delete_all_documents()
        
        return JSONResponse(content={"message": "All data cleared successfully."})
    except Exception as e:
        logger.error(f"Failed to clear data: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to clear data: {e}")
