"""
Paper→Podcast: Agentic + Verified
Complete FastAPI Backend for Hackathon Demo

This is the core application for the AWS & NVIDIA Hackathon submission.
Transforms research papers into verified, engaging podcast episodes.
"""

import os
import asyncio
from pathlib import Path
from typing import Dict, Any, List, Optional
import json
import logging
from datetime import datetime

from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

# Add project root to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.test_end_to_end import PodcastAgentOrchestrator

# Templates setup
templates = Jinja2Templates(directory="app/templates")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global orchestrator instance
orchestrator = None

# Request/Response models
class PaperUploadResponse(BaseModel):
    paper_id: str
    title: str
    status: str
    message: str

class OutlineResponse(BaseModel):
    paper_id: str
    episode_title: str
    target_duration_minutes: int
    segments: List[Dict[str, Any]]

class SegmentRequest(BaseModel):
    segment_index: int
    
class SegmentResponse(BaseModel):
    segment_index: int
    title: str
    script_lines: List[Dict[str, str]]
    citations: List[str]
    estimated_duration_s: int

class FactCheckRequest(BaseModel):
    segment_index: int
    script_lines: List[Dict[str, str]]

class FactCheckResponse(BaseModel):
    segment_index: int
    coverage_ratio: float
    factcheck_score: float
    needs_source_idx: List[int]
    verification_notes: List[str]

class RewriteRequest(BaseModel):
    segment_index: int
    script_lines: List[Dict[str, str]]
    needs_idx: List[int]

class TTSRequest(BaseModel):
    segment_index: int
    script_lines: List[Dict[str, str]]

class ReportResponse(BaseModel):
    paper_id: str
    factuality: str
    coverage_pct: int
    duration_target_s: int
    duration_est_s: int
    segments_completed: int

# FastAPI app initialization
app = FastAPI(
    title="Paper→Podcast: Agentic + Verified",
    description="""
    🏆 **AWS & NVIDIA Hackathon Submission**
    
    Transform dense research papers into engaging, fact-checked podcast episodes 
    with autonomous planning, dual-memory RAG, and inline verification.
    
    ## Key Features
    - 🤖 **Agentic State Machine**: Autonomous planning and execution
    - 📚 **NVIDIA NIM Integration**: llama-3.1-nemotron-nano-8B-v1 + Retrieval NIM
    - ☁️ **AWS Infrastructure**: SageMaker, OpenSearch, S3, Polly
    - ✅ **Fact Verification**: Citation-backed content generation
    - 🎙️ **High-Quality Audio**: Two-host conversational format
    
    ## Demo Workflow
    1. Upload research paper (PDF)
    2. Auto-generate episode outline
    3. Create verified script with citations
    4. Render studio-quality audio
    5. Export complete podcast package
    """,
    version="1.0.0",
    contact={
        "name": "Kesav N",
        "url": "https://github.com/kesavn-13/Podcast_Gen",
        "email": "kesavn13@example.com",
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT",
    },
    lifespan=lifespan
)

# CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=settings.ALLOWED_METHODS,
    allow_headers=["*"],
)


# Health check endpoint
@app.get("/", tags=["Health"])
async def root():
    """Root endpoint with hackathon submission info"""
    return {
        "message": "Paper→Podcast: Agentic + Verified",
        "status": "healthy",
        "hackathon": "AWS & NVIDIA Agentic AI Unleashed",
        "demo": "Transform research papers → verified podcasts",
        "version": "1.0.0",
        "endpoints": {
            "upload": "/api/v1/upload",
            "generate": "/api/v1/generate",
            "playback": "/api/v1/playback",
            "monitoring": "/api/v1/monitoring",
            "docs": "/docs"
        }
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """Detailed health check for monitoring"""
    try:
        # TODO: Add actual health checks for AWS services
        return {
            "status": "healthy",
            "timestamp": "2025-10-15T12:00:00Z",
            "services": {
                "nvidia_nim": "connected",
                "aws_sagemaker": "ready", 
                "opensearch": "indexed",
                "s3": "accessible",
                "polly": "available"
            },
            "resources": {
                "budget_remaining": "$85.50",  # Mock data for demo
                "endpoints_running": 2,
                "processing_queue": 0
            }
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Health check failed: {str(e)}")


# Include API routes
app.include_router(
    upload.router,
    prefix="/api/v1/upload",
    tags=["File Upload"]
)

app.include_router(
    generation.router,
    prefix="/api/v1/generate",
    tags=["Podcast Generation"]
)

app.include_router(
    playback.router,
    prefix="/api/v1/playback",
    tags=["Audio Playback"]
)

app.include_router(
    monitoring.router,
    prefix="/api/v1/monitoring",
    tags=["Cost & Performance Monitoring"]
)


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler with structured logging"""
    import structlog
    logger = structlog.get_logger()
    
    logger.error(
        "Unhandled exception",
        exc_type=type(exc).__name__,
        exc_message=str(exc),
        request_url=str(request.url),
        request_method=request.method
    )
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": "An unexpected error occurred",
            "type": type(exc).__name__,
            "hackathon_note": "This is a demo - error handling is simplified"
        }
    )


def main():
    """Main entry point for CLI execution"""
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.RELOAD and settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )


if __name__ == "__main__":
    main()