"""
Version 2 API Endpoints
New agent-based flow: Data Upload -> Agent 1 (Recommendations) -> Agent 2 (Code Gen) -> Display
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

from app.agents.viz_recommender import VizRecommendationAgent
from app.agents.viz_generator import VizCodeGenerator
from app.core.vertex_database import VertexDatabase
from app.core.blob_storage import blob_storage

logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter(prefix="/api/v2", tags=["v2-agents"])

# Global agents - initialize without vector DB initially
agent1 = VizRecommendationAgent()
agent2 = VizCodeGenerator()

# Session storage for tracking processing status
processing_sessions = {}

@router.post("/upload")
async def upload_data_v2(
    file: UploadFile = File(...),
    user_context: str = None,
    background_tasks: BackgroundTasks = None
):
    """
    V2 Upload endpoint: Handles any size data and triggers agent-based processing
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
            "user_context": user_context,
            "created_at": datetime.now().isoformat(),
            "current_step": "data_validation",
            "progress": 10
        }
        
        # Start background processing
        if background_tasks:
            background_tasks.add_task(process_data_pipeline, session_id, file_path, user_context)
        else:
            # For immediate processing (testing)
            asyncio.create_task(process_data_pipeline(session_id, file_path, user_context))
        
        return {
            "session_id": session_id,
            "status": "processing",
            "message": "Data uploaded successfully. Agent-based analysis started.",
            "filename": file.filename,
            "estimated_completion": "2-5 minutes"
        }
        
    except Exception as e:
        logger.error(f"V2 Upload error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

async def process_data_pipeline(session_id: str, file_path: str, user_context: str = None):
    """
    V2 Processing Pipeline: Agent 1 -> Agent 2 -> Dashboard Generation
    """
    try:
        logger.info(f"Starting V2 processing pipeline for session {session_id}")
        
        # Step 1: Load and validate data
        processing_sessions[session_id].update({
            "status": "processing",
            "current_step": "data_loading",
            "progress": 20
        })
        
        df = await load_data_robust(file_path)
        logger.info(f"Loaded data: {len(df)} rows, {len(df.columns)} columns")
        
        # Step 2: Agent 1 - Visualization Recommendations
        processing_sessions[session_id].update({
            "current_step": "agent1_analysis",
            "progress": 40
        })
        
        recommendations = agent1.analyze_and_recommend(df, user_context, session_id)
        recommendations_json = agent1.get_recommendation_json(recommendations)
        
        logger.info(f"Agent 1 generated {len(recommendations)} recommendations")
        
        # Save recommendations
        rec_path = f"app/uploads/{session_id}/recommendations.json"
        with open(rec_path, 'w') as f:
            f.write(recommendations_json)
        
        # Step 3: Agent 2 - Code Generation
        processing_sessions[session_id].update({
            "current_step": "agent2_generation",
            "progress": 70
        })
        
        dashboard_path = agent2.generate_dashboard(recommendations_json, df, session_id)
        logger.info(f"Agent 2 generated dashboard: {dashboard_path}")
        
        # Step 4: Finalization
        processing_sessions[session_id].update({
            "status": "completed",
            "current_step": "completed",
            "progress": 100,
            "dashboard_path": dashboard_path,
            "recommendations_count": len(recommendations),
            "completed_at": datetime.now().isoformat()
        })
        
        logger.info(f"V2 processing completed for session {session_id}")
        
    except Exception as e:
        logger.error(f"V2 processing error for session {session_id}: {str(e)}")
        processing_sessions[session_id].update({
            "status": "error",
            "error": str(e),
            "failed_at": datetime.now().isoformat()
        })

async def load_data_robust(file_path: str) -> pd.DataFrame:
    """
    Robust data loading that handles any file size
    """
    try:
        # Determine file type and load accordingly
        if file_path.endswith('.csv'):
            # For large CSV files, use chunking if needed
            file_size = os.path.getsize(file_path)
            if file_size > 100 * 1024 * 1024:  # 100MB threshold
                logger.info(f"Large file detected ({file_size/1024/1024:.1f}MB), using chunked loading")
                chunks = []
                chunk_size = 10000
                for chunk in pd.read_csv(file_path, chunksize=chunk_size):
                    chunks.append(chunk)
                    if len(chunks) >= 10:  # Limit total chunks for memory
                        break
                df = pd.concat(chunks, ignore_index=True)
            else:
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
        elif progress >= 70:
            return "< 1 minute"
        elif progress >= 40:
            return "2-3 minutes"
        elif progress >= 20:
            return "3-4 minutes"
        else:
            return "4-5 minutes"
    except:
        return "Unknown"

@router.get("/dashboard/{session_id}")
async def get_dashboard_v2(session_id: str):
    """
    Serve the generated dashboard for opening in new tab
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
        
        # Read HTML content and return as HTMLResponse for new tab opening
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
        
        return {
            "session_id": session_id,
            "recommendations": recommendations,
            "count": len(recommendations),
            "generated_at": processing_sessions[session_id].get("created_at")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting recommendations for session {session_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get recommendations")

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
            import shutil
            shutil.rmtree(session_dir)
        
        return {
            "session_id": session_id,
            "status": "cleaned_up",
            "message": "Session data removed successfully"
        }
        
    except Exception as e:
        logger.error(f"Error cleaning up session {session_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to cleanup session")

@router.get("/sessions")
async def list_active_sessions():
    """
    List all active processing sessions
    """
    try:
        sessions = []
        for session_id, data in processing_sessions.items():
            sessions.append({
                "session_id": session_id,
                "status": data.get("status"),
                "filename": data.get("filename"),
                "created_at": data.get("created_at"),
                "progress": data.get("progress", 0)
            })
        
        return {
            "active_sessions": sessions,
            "count": len(sessions)
        }
        
    except Exception as e:
        logger.error(f"Error listing sessions: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to list sessions")