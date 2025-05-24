# backend/app/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware 
from app.api.routes import router as api_router
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Chatbot Theme Identifier API",
    description="API for document upload, query, and theme identification.",
    version="1.0.0",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins, including your Render frontend
    allow_credentials=True,
    allow_methods=["*"],  # Allows all HTTP methods (POST, GET, etc.)
    allow_headers=["*"],  # Allows all headers
)
# -----------------------------------------------------------------------------

app.include_router(api_router, prefix="/api")

@app.get("/")
async def read_root():
    logger.info("Root endpoint accessed.")
    return {"message": "Welcome to the Chatbot Theme Identifier API!"}
