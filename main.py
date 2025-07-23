"""
Power BI Data Visualization Platform - Main Entry Point
"""
import sys
import os

# Add app directory to path
sys.path.insert(0,  os.path.join(os.path.dirname(__file__), 'app'))

# Import the full FastAPI app
from app.main import app