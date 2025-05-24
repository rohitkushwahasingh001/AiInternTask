# backend/app/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware # Import CORSMiddleware
from app.api.routes import router as api_router
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Chatbot Theme Identifier API",
    description="API for document upload, query, and theme identification.",
    version="1.0.0",
)

# CORS Middleware (Yeh section add ya update kar)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # <--- Development ke liye "*" rakhte hain, production mein specific Vercel URL dena hota hai
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods (POST, GET, etc.)
    allow_headers=["*"],  # Allow all headers
)

app.include_router(api_router, prefix="/api")

@app.get("/")
async def read_root():
    """
    Root endpoint for the API.
    """
    logger.info("Root endpoint accessed.")
    return {"message": "Welcome to the Chatbot Theme Identifier API!"}

# Baaki ke app-level configurations agar kuch hain toh yahan add kar sakte ho.
