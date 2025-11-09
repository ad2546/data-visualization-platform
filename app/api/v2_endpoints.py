"""
Version 2 API Endpoints - 3-Stage Pipeline
Stage 0: Business Context Agent (free LLM)
Stage 1: Visualization Recommender
Stage 2: Code Generator (qwen3-coder)
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import HTMLResponse, FileResponse
import pandas as pd
import uuid
import os
import json
import logging
from typing import Dict, List, Any
import asyncio
from datetime import datetime
import shutil

from app.agents.business_context_agent import BusinessContextAgent
from app.agents.viz_recommender import VizRecommendationAgent
from app.agents.viz_generator import VizCodeGenerator

logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter(prefix="/api/v2", tags=["v2-agents"])

# Global agents
business_context_agent = BusinessContextAgent()
agent1 = VizRecommendationAgent()
agent2 = VizCodeGenerator()

# Session storage
processing_sessions = {}

@router.post("/upload")
async def upload_data_v2(
    file: UploadFile = File(...),
    user_context: str = None,
    background_tasks: BackgroundTasks = None
):
    """
    V2 Upload endpoint: Handles file upload and triggers 3-stage pipeline
    """
    try:
        session_id = str(uuid.uuid4())
        logger.info(f"V2 Upload started - Session: {session_id}, File: {file.filename}")
        
        # Validate file
        if not file.filename.endswith(('.csv', '.xlsx', '.json')):
            raise HTTPException(status_code=400, detail="Unsupported file format. Use CSV, XLSX, or JSON.")
        
        # Create session directory
        session_dir = f"app/uploads/{session_id}"
        os.makedirs(session_dir, exist_ok=True)
        
        # Save uploaded file
        file_path = f"{session_dir}/{file.filename}"
        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)
        
        # Initialize session tracking
        processing_sessions[session_id] = {
            "status": "uploaded",
            "filename": file.filename,
            "file_path": file_path,
            "user_context": user_context,
            "created_at": datetime.now().isoformat(),
            "current_step": "data_validation",
            "progress": 5
        }
        
        # Start background processing
        if background_tasks:
            background_tasks.add_task(process_data_pipeline, session_id, file_path, user_context)
        else:
            asyncio.create_task(process_data_pipeline(session_id, file_path, user_context))
        
        return {
            "session_id": session_id,
            "status": "processing",
            "message": "Data uploaded successfully. 3-stage AI pipeline started.",
            "filename": file.filename,
            "estimated_completion": "2-4 minutes",
            "pipeline_stages": [
                "Stage 0: Business Context Analysis (free LLM)",
                "Stage 1: Visualization Recommendations",
                "Stage 2: Code Generation (qwen3-coder)"
            ]
        }
        
    except Exception as e:
        logger.error(f"V2 Upload error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

async def process_data_pipeline(session_id: str, file_path: str, user_context: str = None):
    """
    3-Stage Processing Pipeline:
    Stage 0: Business Context Agent (free LLM) → Business Context
    Stage 1: Visualization Recommender → Recommendations
    Stage 2: Code Generator (qwen3-coder) → Dashboard
    """
    try:
        logger.info(f"Starting 3-stage pipeline for session {session_id}")
        
        # Stage 0: Load and validate data
        processing_sessions[session_id].update({
            "status": "processing",
            "current_step": "data_loading",
            "progress": 10
        })
        
        df = await load_data_robust(file_path)
        logger.info(f"Loaded data: {len(df)} rows, {len(df.columns)} columns")
        
        # Stage 0: Business Context Analysis (free LLM)
        processing_sessions[session_id].update({
            "current_step": "business_context_analysis",
            "progress": 25
        })
        
        logger.info("\n" + "="*80)
        logger.info(f"SESSION {session_id}: Starting Stage 0 - Business Context Analysis")
        logger.info("="*80)
        business_context = business_context_agent.analyze_business_context(df, user_context)
        logger.info(f"Business context extracted: Domain={business_context.get('domain')}")
        logger.info("="*80 + "\n")
        
        # Save business context
        context_path = f"app/uploads/{session_id}/business_context.json"
        with open(context_path, 'w') as f:
            json.dump(business_context, f, indent=2)
        
        # Stage 1: Visualization Recommendations
        processing_sessions[session_id].update({
            "current_step": "agent1_analysis",
            "progress": 50
        })
        
        logger.info("\n" + "="*80)
        logger.info(f"SESSION {session_id}: Starting Stage 1 - Visualization Recommendations")
        logger.info("="*80)
        recommendations = agent1.analyze_and_recommend(df, business_context, session_id)
        recommendations_json = agent1.get_recommendation_json(recommendations)
        
        logger.info(f"Agent 1 generated {len(recommendations)} recommendations")
        logger.info("="*80 + "\n")
        
        # Save recommendations
        rec_path = f"app/uploads/{session_id}/recommendations.json"
        with open(rec_path, 'w') as f:
            f.write(recommendations_json)
        
        # Stage 2: Code Generation (qwen3-coder)
        processing_sessions[session_id].update({
            "current_step": "agent2_code_generation",
            "progress": 75
        })
        
        logger.info("\n" + "="*80)
        logger.info(f"SESSION {session_id}: Starting Stage 2 - Code Generation")
        logger.info("="*80)
        dashboard_path = agent2.generate_dashboard(recommendations_json, df, business_context, session_id)
        logger.info(f"Agent 2 generated dashboard: {dashboard_path}")
        logger.info("="*80 + "\n")
        
        # Finalization
        processing_sessions[session_id].update({
            "status": "completed",
            "current_step": "completed",
            "progress": 100,
            "dashboard_path": dashboard_path,
            "recommendations_count": len(recommendations),
            "business_domain": business_context.get('domain'),
            "completed_at": datetime.now().isoformat()
        })
        
        logger.info(f"3-stage pipeline completed for session {session_id}")
        
    except Exception as e:
        logger.error(f"Pipeline error for session {session_id}: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        processing_sessions[session_id].update({
            "status": "error",
            "error": str(e),
            "failed_at": datetime.now().isoformat()
        })

async def load_data_robust(file_path: str) -> pd.DataFrame:
    """
    Robust data loading that handles different file types
    """
    try:
        # Determine file type and load accordingly
        if file_path.endswith('.csv'):
            df = pd.read_csv(file_path)
        elif file_path.endswith('.xlsx'):
            df = pd.read_excel(file_path)
        elif file_path.endswith('.json'):
            df = pd.read_json(file_path)
        else:
            raise ValueError("Unsupported file format")
        
        # Basic data validation
        if df.empty:
            raise ValueError("Dataset is empty")
        
        if len(df.columns) == 0:
            raise ValueError("No columns found in dataset")
        
        # Limit dataset size for processing (can be adjusted)
        if len(df) > 50000:
            logger.info(f"Large dataset ({len(df)} rows), sampling to 50k rows for analysis")
            df = df.sample(n=50000, random_state=42)
        
        return df
        
    except Exception as e:
        logger.error(f"Error loading data from {file_path}: {str(e)}")
        raise

@router.get("/status/{session_id}")
async def get_processing_status(session_id: str):
    """
    Get processing status for a session
    """
    try:
        if session_id not in processing_sessions:
            raise HTTPException(status_code=404, detail="Session not found")
        
        session_data = processing_sessions[session_id]
        
        return {
            "session_id": session_id,
            "status": session_data.get("status"),
            "current_step": session_data.get("current_step"),
            "progress": session_data.get("progress", 0),
            "filename": session_data.get("filename"),
            "created_at": session_data.get("created_at"),
            "completed_at": session_data.get("completed_at"),
            "error": session_data.get("error"),
            "recommendations_count": session_data.get("recommendations_count"),
            "business_domain": session_data.get("business_domain"),
            "estimated_time_remaining": calculate_estimated_time(session_data)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting status for session {session_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get session status")

def calculate_estimated_time(session_data: Dict) -> str:
    """Calculate estimated time remaining based on progress"""
    try:
        progress = session_data.get("progress", 0)
        if progress >= 100:
            return "Completed"
        elif progress >= 75:
            return "< 1 minute"
        elif progress >= 50:
            return "1-2 minutes"
        elif progress >= 25:
            return "2-3 minutes"
        else:
            return "3-4 minutes"
    except:
        return "Unknown"

@router.get("/dashboard/{session_id}")
async def get_dashboard_v2(session_id: str):
    """
    Serve the generated dashboard
    """
    try:
        if session_id not in processing_sessions:
            raise HTTPException(status_code=404, detail="Session not found")
        
        session_data = processing_sessions[session_id]
        
        if session_data.get("status") != "completed":
            return {
                "status": session_data.get("status"),
                "current_step": session_data.get("current_step"),
                "progress": session_data.get("progress"),
                "message": "Dashboard not ready yet. Please check status."
            }
        
        dashboard_path = session_data.get("dashboard_path")
        if not dashboard_path or not os.path.exists(dashboard_path):
            raise HTTPException(status_code=404, detail="Dashboard file not found")
        
        # Read HTML content and return as HTMLResponse
        with open(dashboard_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        return HTMLResponse(
            content=html_content,
            headers={
                "Cache-Control": "no-cache",
                "Content-Type": "text/html; charset=utf-8"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error serving dashboard for session {session_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to serve dashboard")

@router.get("/recommendations/{session_id}")
async def get_recommendations(session_id: str):
    """
    Get visualization recommendations from Agent 1
    """
    try:
        if session_id not in processing_sessions:
            raise HTTPException(status_code=404, detail="Session not found")
        
        rec_path = f"app/uploads/{session_id}/recommendations.json"
        if not os.path.exists(rec_path):
            raise HTTPException(status_code=404, detail="Recommendations not found")
        
        with open(rec_path, 'r') as f:
            recommendations = json.load(f)
        
        # Also get business context if available
        business_context = None
        context_path = f"app/uploads/{session_id}/business_context.json"
        if os.path.exists(context_path):
            with open(context_path, 'r') as f:
                business_context = json.load(f)
        
        return {
            "session_id": session_id,
            "recommendations": recommendations,
            "count": len(recommendations),
            "business_context": business_context,
            "generated_at": processing_sessions[session_id].get("created_at")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting recommendations for session {session_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get recommendations")

@router.get("/business-context/{session_id}")
async def get_business_context(session_id: str):
    """
    Get business context from Stage 0
    """
    try:
        if session_id not in processing_sessions:
            raise HTTPException(status_code=404, detail="Session not found")
        
        context_path = f"app/uploads/{session_id}/business_context.json"
        if not os.path.exists(context_path):
            raise HTTPException(status_code=404, detail="Business context not found")
        
        with open(context_path, 'r') as f:
            business_context = json.load(f)
        
        return {
            "session_id": session_id,
            "business_context": business_context
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting business context for session {session_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get business context")

@router.delete("/session/{session_id}")
async def cleanup_session(session_id: str):
    """
    Clean up session data and files
    """
    try:
        # Remove from processing sessions
        if session_id in processing_sessions:
            del processing_sessions[session_id]

        # Remove session directory
        session_dir = f"app/uploads/{session_id}"
        if os.path.exists(session_dir):
            shutil.rmtree(session_dir)

        return {
            "session_id": session_id,
            "status": "cleaned_up",
            "message": "Session data removed successfully"
        }

    except Exception as e:
        logger.error(f"Error cleaning up session {session_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to cleanup session")

@router.get("/sample-data/list")
async def list_sample_datasets():
    """
    List available sample datasets for testing
    """
    try:
        sample_data_dir = "sample_data"

        if not os.path.exists(sample_data_dir):
            return {"samples": []}

        sample_files = []
        for filename in os.listdir(sample_data_dir):
            if filename.endswith(('.csv', '.xlsx', '.json')):
                file_path = os.path.join(sample_data_dir, filename)

                # Get file info
                file_stats = os.stat(file_path)

                # Read first few rows to get info
                try:
                    if filename.endswith('.csv'):
                        df = pd.read_csv(file_path, nrows=5)
                    elif filename.endswith('.xlsx'):
                        df = pd.read_excel(file_path, nrows=5)
                    elif filename.endswith('.json'):
                        df = pd.read_json(file_path)
                        df = df.head(5)

                    row_count = len(pd.read_csv(file_path)) if filename.endswith('.csv') else len(df)

                    sample_files.append({
                        "filename": filename,
                        "name": filename.replace('_', ' ').replace('.csv', '').replace('.xlsx', '').replace('.json', '').title(),
                        "size": file_stats.st_size,
                        "rows": row_count,
                        "columns": len(df.columns),
                        "column_names": list(df.columns),
                        "description": _get_sample_description(filename)
                    })
                except Exception as e:
                    logger.error(f"Error reading sample file {filename}: {str(e)}")
                    continue

        return {
            "samples": sample_files,
            "count": len(sample_files)
        }

    except Exception as e:
        logger.error(f"Error listing sample datasets: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to list sample datasets")

def _get_sample_description(filename: str) -> str:
    """Get description for sample dataset"""
    descriptions = {
        "sales_performance.csv": "E-commerce sales data with revenue, profit, and customer satisfaction metrics by region and product category",
        "hr_metrics.csv": "Human resources data with employee performance, salary, training hours, and satisfaction scores by department",
        "website_analytics.csv": "Website traffic and conversion metrics including page views, bounce rate, and revenue by traffic source and device type"
    }
    return descriptions.get(filename, "Sample dataset for testing")

@router.get("/sample-data/download/{filename}")
async def download_sample_dataset(filename: str):
    """
    Download a specific sample dataset
    """
    try:
        # Validate filename (security check)
        if '..' in filename or '/' in filename or '\\' in filename:
            raise HTTPException(status_code=400, detail="Invalid filename")

        file_path = f"sample_data/{filename}"

        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="Sample dataset not found")

        return FileResponse(
            path=file_path,
            filename=filename,
            media_type='application/octet-stream'
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading sample dataset {filename}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to download sample dataset")

@router.post("/sample-data/load/{filename}")
async def load_sample_dataset(filename: str, background_tasks: BackgroundTasks = None):
    """
    Load a sample dataset and start processing pipeline
    """
    try:
        # Validate filename (security check)
        if '..' in filename or '/' in filename or '\\' in filename:
            raise HTTPException(status_code=400, detail="Invalid filename")

        source_path = f"sample_data/{filename}"

        if not os.path.exists(source_path):
            raise HTTPException(status_code=404, detail="Sample dataset not found")

        # Create new session
        session_id = str(uuid.uuid4())
        logger.info(f"Loading sample dataset: {filename} - Session: {session_id}")

        # Create session directory
        session_dir = f"app/uploads/{session_id}"
        os.makedirs(session_dir, exist_ok=True)

        # Copy sample file to session directory
        dest_path = f"{session_dir}/{filename}"
        shutil.copy2(source_path, dest_path)

        # Get sample description for context
        user_context = _get_sample_description(filename)

        # Initialize session tracking
        processing_sessions[session_id] = {
            "status": "uploaded",
            "filename": filename,
            "file_path": dest_path,
            "user_context": user_context,
            "created_at": datetime.now().isoformat(),
            "current_step": "data_validation",
            "progress": 5,
            "is_sample": True
        }

        # Start background processing
        if background_tasks:
            background_tasks.add_task(process_data_pipeline, session_id, dest_path, user_context)
        else:
            asyncio.create_task(process_data_pipeline(session_id, dest_path, user_context))

        return {
            "session_id": session_id,
            "status": "processing",
            "message": f"Sample dataset '{filename}' loaded successfully. 3-stage AI pipeline started.",
            "filename": filename,
            "estimated_completion": "2-4 minutes",
            "pipeline_stages": [
                "Stage 0: Business Context Analysis (free LLM)",
                "Stage 1: Visualization Recommendations",
                "Stage 2: Code Generation (qwen3-coder)"
            ]
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error loading sample dataset {filename}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to load sample dataset: {str(e)}")
