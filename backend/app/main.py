"""CodeMorph — Codebase Modernization Platform.

FastAPI application entry point.
"""

import logging
import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database.db import init_db
from app.api import projects, pipeline, reports, artifacts, enhanced_analysis

# Load environment variables from .env file
load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing database...")
    init_db()
    # Validate Groq config
    groq_key = os.environ.get("GROQ_API_KEY", "")
    groq_model = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")
    if groq_key:
        logger.info(f"Groq configured: model={groq_model}")
    else:
        logger.warning("GROQ_API_KEY not set — transformation will use pass-through mode")
    logger.info("CodeMorph API ready")
    yield
    logger.info("Shutting down CodeMorph API")


app = FastAPI(
    title="CodeMorph",
    description="Codebase Modernization Platform — Analyze, detect, and modernize legacy codebases",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — allow local frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(projects.router)
app.include_router(pipeline.router)
app.include_router(reports.router)
app.include_router(artifacts.router)
app.include_router(enhanced_analysis.router)


@app.get("/")
def root():
    return {
        "name": "CodeMorph",
        "version": "1.0.0",
        "description": "Codebase Modernization Platform",
    }


@app.get("/health")
def health():
    return {"status": "healthy"}
