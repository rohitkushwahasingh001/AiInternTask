# backend/app/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router as api_router
from app.core.config import settings
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_app():
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.API_VERSION,
        description=settings.PROJECT_DESCRIPTION,
    )

    # Set up CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Adjust this to specific origins in production, e.g., ["http://localhost:8001"]
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include API router
    app.include_router(api_router, prefix="/api")

    @app.get("/")
    async def root():
        return {"message": "Welcome to Wasserstoff AI Document Chatbot API!"}

    return app

app = create_app()

