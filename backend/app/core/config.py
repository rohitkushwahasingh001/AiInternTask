# backend/app/core/config.py

import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Settings(BaseSettings):
    # This will load environment variables from a .env file located at the project root
    # or specified path.
    # It also sets default values if environment variables are not found.
    model_config = SettingsConfigDict(env_file='.env', extra='ignore')

    PROJECT_NAME: str = "THeme AI Document Chatbot"
    API_VERSION: str = "1.0.0"
    PROJECT_DESCRIPTION: str = "An AI chatbot for document research and theme identification."

    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "your_gemini_api_key_here")

    # Directory where ChromaDB will store its persistent data
    CHROMA_PERSIST_DIR: str = "data/chroma_db"

    # Directory for temporarily uploaded documents
    UPLOAD_DIR: str = "data/uploaded_documents"

settings = Settings()

