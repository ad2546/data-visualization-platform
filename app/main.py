"""
Simplified Data Visualization Platform - Main Entry Point
Uses OpenRouter for AI generation
"""

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
import logging
from dotenv import load_dotenv
from app.api.v2_endpoints import router as v2_router

# Load environment variables
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Data Visualization Platform", version="3.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include V2 API routes
app.include_router(v2_router)

# Create directories if they don't exist
os.makedirs("app/static", exist_ok=True)
os.makedirs("app/uploads", exist_ok=True)
os.makedirs("uploads", exist_ok=True)

app.mount("/static", StaticFiles(directory="app/static"), name="static")
app.mount("/uploads", StaticFiles(directory="app/uploads"), name="uploads")
templates = Jinja2Templates(directory="app/templates")

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """Main interface - Dark themed single page app"""
    return templates.TemplateResponse("index_dark.html", {"request": request})

@app.get("/v2", response_class=HTMLResponse)
async def read_v2(request: Request):
    """Legacy V2 interface"""
    return templates.TemplateResponse("v2_index.html", {"request": request})

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": "3.0.0",
        "openrouter_configured": bool(os.getenv('OPENROUTER_API_KEY')),
        "model": os.getenv('OPENROUTER_MODEL', 'not-set')
    }

if __name__ == "__main__":
    # Configure logging
    log_level = os.getenv('LOG_LEVEL', 'INFO')
    logging.basicConfig(level=getattr(logging, log_level.upper()))
    
    # Get port from environment variable
    port = int(os.getenv("PORT", "8000"))
    
    # Check OpenRouter configuration
    api_key = os.getenv('OPENROUTER_API_KEY')
    model = os.getenv('OPENROUTER_MODEL', 'anthropic/claude-3.5-sonnet')
    
    logger.info("=" * 80)
    logger.info("DATA VISUALIZATION PLATFORM - STARTUP")
    logger.info("=" * 80)
    logger.info(f"Server starting on port {port}")
    logger.info(f"OpenRouter API Key: {'✓ Configured' if api_key else '✗ NOT SET'}")
    logger.info(f"OpenRouter Model: {model}")
    
    if not api_key:
        logger.warning("=" * 80)
        logger.warning("WARNING: OPENROUTER_API_KEY not set!")
        logger.warning("The application will use fallback dashboards.")
        logger.warning("To fix: Add OPENROUTER_API_KEY to your .env file")
        logger.warning("Get your key at: https://openrouter.ai/")
        logger.warning("=" * 80)
    else:
        logger.info("✓ OpenRouter is properly configured")
    
    logger.info("=" * 80)
    
    uvicorn.run(app, host="0.0.0.0", port=port)
