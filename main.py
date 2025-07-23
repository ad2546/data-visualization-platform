#!/usr/bin/env python3
"""
Main entry point for Google App Engine deployment.
"""

import os
import sys
import logging

# Add the app directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
app_dir = os.path.join(current_dir, 'app')
sys.path.insert(0, app_dir)

# Configure logging for App Engine
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Change to app directory for imports
os.chdir(app_dir)

# Import the FastAPI app from the app directory
from app.main import app

# This is required for App Engine
if __name__ == "__main__":
    import uvicorn
    
    # Get port from environment variable (App Engine sets this)
    port = int(os.environ.get("PORT", 8000))
    
    logger.info(f"Starting server on port {port}")
    
    # Run the FastAPI app
    uvicorn.run(app, host="0.0.0.0", port=port)