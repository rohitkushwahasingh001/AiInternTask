    # backend/app/services/document_processor.py

    import os
    import pytesseract
    from PIL import Image
    from pypdf import PdfReader
    from typing import List, Dict, Tuple
    import uuid
    import io
    from pdf2image import convert_from_path
    from docx import Document
    from fastapi import UploadFile
    import logging

    logger = logging.getLogger(__name__)

    class DocumentProcessor:
        """
        Handles document processing, including saving uploaded files,
        extracting text (with OCR for images and DOCX), and chunking the text.
        It does NOT interact directly with the vector database.
        """
        def __init__(self, upload_dir: str):
            self.upload_dir = upload_dir
            os.makedirs(self.upload_dir, exist_ok=True)
            logger.info(f"DocumentProcessor initialized. Upload directory: {self.upload_dir}")

            # --- Poppler Path Configuration ---
            # FIX: Set poppler_path to None or ensure it's not hardcoded if system-wide install is used
            # Render's apt-get install will put poppler-utils in system PATH.
            self.poppler_path = None # <--- Changed to None
            # You can keep the old detection logic if you also test locally, but for Render, None is fine.
            # if os.path.exists("/opt/homebrew/bin/pdfinfo"):
            #     self.poppler_path = "/opt/homebrew/bin"
            # elif os.path.exists("/usr/local/bin/pdfinfo"):
            #     self.poppler_path = "/usr/local/bin"
            # else:
            #     logger.warning("Poppler not found in common Homebrew paths. Ensure it's installed and in PATH, or set poppler_path manually.")

        async def process_document(self, file_path: str, filename: str) -> Tuple[str, List[Dict]]:
            """
            Processes a single document, extracting text and returning chunks with citations.
            Supports PDF, DOCX, and common image formats (PNG, JPG, JPEG, TIFF, TXT).
            Returns the document ID and a list of text chunks with metadata.
            """
            file_extension = filename.split('.')[-1].lower()
            document_id = f"DOC{uuid.uuid4().hex[:8].upper()}"
            document_content = []

            logger.info(f"Processing document: {filename} (ID: {document_id})")

            if file_extension == "pdf":
                try:
                    reader = PdfReader(file_path)
                    for i, page in enumerate(reader.pages):
                        text = page.extract_text()
                        if text:
                            document_content.append(text)
                        else:
                            logger.info(f"Text not extracted from page {i+1} of PDF '{filename}'. Attempting OCR...")
                            try:
                                # Ensure poppler_path is passed here, even if it's None.
                                # pdf2image will then look in system PATH.
                                images = convert_from_path(
                                    file_path,
                                    first_page=i+1,
                                    last_page=i+1,
                                    poppler_path=self.poppler_path # Pass self.poppler_path (which is now None)
                                )
                                if images:
                                    img = images[0]
                                    ocr_text = pytesseract.image_to_string(img)
                                    document_content.append(ocr_text)
                                    logger.info(f"OCR successful for page {i+1} of PDF '{filename}'.")
                                else:
                                    document_content.append("")
                                    logger.warning(f"Could not convert page {i+1} of PDF '{filename}' to image for OCR.")
                            except Exception as ocr_e:
                                document_content.append("")
                                logger.error(f"Error during OCR for page {i+1} of PDF '{filename}': {ocr_e}", exc_info=True)
                except Exception as e:
                    logger.error(f"Error processing PDF {filename}: {e}", exc_info=True)
                    raise

            elif file_extension == "docx":
                try:
                    doc = Document(file_path)
                    full_text = []
                    for para in doc.paragraphs:
                        full_text.append(para.text)
                    document_content.append("\n\n".join(full_text))
                    logger.info(f"Successfully extracted text from DOCX: {filename}")
                except Exception as e:
                    logger.error(f"Error processing DOCX {filename}: {e}", exc_info=True)
                    raise

            elif file_extension in ["png", "jpg", "jpeg", "tiff"]:
                try:
                    img = Image.open(file_path)
                    extracted_text = pytesseract.image_to_string(img)
                    document_content.append(extracted_text)
                    logger.info(f"Successfully extracted text from image: {filename}")
                except Exception as e:
                    logger.error(f"Error during OCR for image {filename}: {e}", exc_info=True)
                    raise

            elif file_extension == "txt":
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        text = f.read()
                        document_content.append(text)
                    logger.info(f"Successfully extracted text from TXT: {filename}")
                except Exception as e:
                    logger.error(f"Error reading text file {filename}: {e}", exc_info=True)
                    raise
            else:
                raise ValueError(f"Unsupported file type: {file_extension}. Supported types: PDF, DOCX, PNG, JPG, JPEG, TIFF, TXT.")

            chunks = []
            paragraph_global_idx = 0
            for page_num, text_block in enumerate(document_content):
                paragraphs = [p.strip() for p in text_block.split('\n\n') if p.strip()]
                if not paragraphs and text_block.strip():
                    paragraphs = [s.strip() for s in text_block.split('\n') if s.strip()]
                if not paragraphs and text_block.strip():
                    paragraphs = [text_block.strip()]

                for para_idx, paragraph in enumerate(paragraphs):
                    paragraph_global_idx += 1
                    chunks.append({
                        "content": paragraph,
                        "metadata": {
                            "document_id": document_id,
                            "filename": filename,
                            "page": page_num + 1,
                            "paragraph_on_page": para_idx + 1,
                            "paragraph_global": paragraph_global_idx,
                            "source": f"Document ID: {document_id}, Filename: {filename}, Page: {page_num + 1}, Paragraph: {paragraph_global_idx}"
                        }
                    })
            
            logger.info(f"Document {filename} processed into {len(chunks)} chunks.")
            return document_id, chunks

        async def save_document(self, file_content: bytes, filename: str) -> str:
            """
            Saves the uploaded file content to the specified directory.
            Returns the full path to the saved file.
            """
            file_location = os.path.join(self.upload_dir, filename)
            try:
                with open(file_location, "wb") as file_object:
                    file_object.write(file_content)
                logger.info(f"File saved to: {file_location}")
                return file_location
            except Exception as e:
                logger.error(f"Error saving file {filename}: {e}", exc_info=True)
                raise

        async def process_documents(self, files: List[UploadFile]) -> List[Dict]:
            """
            Processes multiple uploaded files.
            """
            processed_docs_info = []
            for file in files:
                try:
                    file_content = await file.read()
                    file_location = await self.save_document(file_content, file.filename)
                    document_id, chunks = await self.process_document(file_location, file.filename)
                    
                    processed_docs_info.append({
                        "document_id": document_id,
                        "filename": file.filename,
                        "chunks": chunks
                    })
                    os.remove(file_location)
                except Exception as e:
                    logger.error(f"Failed to process {file.filename}: {e}", exc_info=True)
                    processed_docs_info.append({"filename": file.filename, "status": f"failed: {str(e)}"})
            return processed_docs_info
    
