
from fastapi import FastAPI, UploadFile, File, Request, BackgroundTasks, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
import uuid
import logging
import shutil
import aiofiles
from datetime import datetime, timedelta
from dotenv import load_dotenv
from app.core.visualization import generate_multiple_visualizations
from app.core.blob_storage import blob_storage
from app.api.v2_endpoints import router as v2_router

# Load environment variables from .env file
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Data Visualization Platform", version="2.0.0")

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

# Global job tracking with file-based persistence
processing_jobs = {}

def save_job_to_file(session_id: str, job_data: dict):
    """Save job data to file for persistence"""
    try:
        # Use absolute path from working directory
        session_dir = f"uploads/{session_id}"
        if not os.path.exists(session_dir):
            os.makedirs(session_dir)
        
        job_file = os.path.join(session_dir, "job_status.json")
        with open(job_file, "w") as f:
            import json
            json.dump(job_data, f)
        logger.info(f"Job saved to file for session {session_id} at {job_file}")
    except Exception as e:
        logger.error(f"Error saving job to file for session {session_id}: {str(e)}")

def load_job_from_file(session_id: str) -> dict:
    """Load job data from file"""
    try:
        # Use absolute path from working directory
        session_dir = f"uploads/{session_id}"
        job_file = os.path.join(session_dir, "job_status.json")
        
        logger.info(f"Attempting to load job from file: {job_file}")
        
        if os.path.exists(job_file):
            with open(job_file, "r") as f:
                import json
                job_data = json.load(f)
            logger.info(f"Job loaded from file for session {session_id}")
            return job_data
        else:
            logger.warning(f"Job file not found: {job_file}")
    except Exception as e:
        logger.error(f"Error loading job from file for session {session_id}: {str(e)}")
    return None

def get_job_status(session_id: str) -> dict:
    """Get job status from memory or file"""
    logger.info(f"Getting job status for session {session_id}")
    
    # First check in-memory
    if session_id in processing_jobs:
        logger.info(f"Found job in memory for session {session_id}")
        return processing_jobs[session_id]
    
    logger.info(f"Job not in memory for session {session_id}, checking file system")
    
    # Then check file system
    job_data = load_job_from_file(session_id)
    if job_data:
        # Restore to memory
        processing_jobs[session_id] = job_data
        logger.info(f"Restored job to memory for session {session_id}")
        return job_data
    
    logger.warning(f"Job not found in memory or file system for session {session_id}")
    return None

# Create directories if they don't exist
os.makedirs("app/static", exist_ok=True)
os.makedirs("uploads", exist_ok=True)

app.mount("/static", StaticFiles(directory="app/static"), name="static")
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
templates = Jinja2Templates(directory="app/templates")

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("powerbi_index.html", {"request": request})

@app.get("/v1", response_class=HTMLResponse)
async def read_root_v1(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/v2", response_class=HTMLResponse)
async def read_root_v2(request: Request):
    return templates.TemplateResponse("v2_index.html", {"request": request})

@app.get("/powerbi", response_class=HTMLResponse)
async def read_powerbi(request: Request):
    return templates.TemplateResponse("powerbi_index.html", {"request": request})

@app.post("/upload-csv/")
async def upload_csv(file: UploadFile = File(...)):
    """Upload CSV file and return session ID for processing."""
    session_id = str(uuid.uuid4())
    
    try:
        # Validate file type
        if not file.filename.endswith('.csv'):
            return JSONResponse(content={"error": "Only CSV files are allowed"}, status_code=400)
        
        # Check file size limits from environment - optimized for batch processing
        MAX_FILE_SIZE_MB = int(os.getenv('MAX_FILE_SIZE_MB', '5120'))  # 5GB for batch processing
        MAX_DIRECT_SIZE_MB = int(os.getenv('MAX_DIRECT_PROCESSING_SIZE_MB', '1024'))  # 1GB direct processing
        
        MAX_FILE_SIZE = MAX_FILE_SIZE_MB * 1024 * 1024  # Convert to bytes
        MAX_DIRECT_SIZE = MAX_DIRECT_SIZE_MB * 1024 * 1024  # Convert to bytes
        
        # Create session directory
        session_dir = f"uploads/{session_id}"
        if not os.path.exists(session_dir):
            os.makedirs(session_dir)
        
        file_path = os.path.join(session_dir, file.filename)
        
        # Save uploaded file using streaming for better memory usage
        file_size = 0
        async with aiofiles.open(file_path, "wb") as buffer:
            while True:
                chunk = await file.read(8192)  # Read in 8KB chunks
                if not chunk:
                    break
                file_size += len(chunk)
                
                # Check file size limit during streaming
                if file_size > MAX_FILE_SIZE:
                    # Delete partial file
                    await buffer.close()
                    if os.path.exists(file_path):
                        os.remove(file_path)
                    return JSONResponse(
                        content={"error": f"File too large. Maximum size is {MAX_FILE_SIZE_MB}MB"}, 
                        status_code=413
                    )
                
                await buffer.write(chunk)
        
        logger.info(f"File uploaded for session {session_id}: {file.filename} ({file_size} bytes)")
        
        # Try to upload to blob storage
        blob_name = await blob_storage.upload_file(file_path, session_id, file.filename)
        
        # Initialize job tracking
        job_data = {
            "status": "uploaded",
            "file_name": file.filename,
            "file_size": file_size,
            "blob_name": blob_name,
            "created_at": datetime.now().isoformat(),
            "progress": 0
        }
        processing_jobs[session_id] = job_data
        save_job_to_file(session_id, job_data)
        
        return JSONResponse(content={
            "session_id": session_id,
            "file_name": file.filename,
            "file_size": file_size,
            "blob_storage_enabled": blob_storage.is_enabled(),
            "blob_name": blob_name,
            "status": "uploaded",
            "message": "File uploaded successfully. Use /generate/{session_id} to start processing."
        })
    
    except Exception as e:
        logger.error(f"Server error for session {session_id}: {str(e)}")
        return JSONResponse(content={"error": f"Internal server error: {str(e)}"}, status_code=500)

@app.post("/generate/{session_id}")
async def generate_visualizations(session_id: str, background_tasks: BackgroundTasks, request: Request):
    """Start visualization generation for uploaded file."""
    # Get optional user focus from request body
    try:
        body = await request.json()
        user_focus = body.get("user_focus", None)
    except:
        user_focus = None
    
    job = get_job_status(session_id)
    if not job:
        return JSONResponse(content={"error": "Session not found"}, status_code=404)
    
    if job["status"] == "processing":
        return JSONResponse(content={"error": "Processing already in progress"}, status_code=400)
    
    # Update job status
    job["status"] = "processing"
    job["progress"] = 0
    job["user_focus"] = user_focus
    processing_jobs[session_id] = job
    save_job_to_file(session_id, job)
    
    # Start background processing
    background_tasks.add_task(process_visualization_job, session_id)
    
    return JSONResponse(content={
        "session_id": session_id,
        "status": "processing",
        "message": "Visualization generation started. Use /status/{session_id} to check progress."
    })

async def process_visualization_job(session_id: str):
    """Background task to process visualization generation."""
    try:
        job = get_job_status(session_id)
        if not job:
            logger.error(f"Job not found for session {session_id}")
            return
        session_dir = f"uploads/{session_id}"
        file_path = os.path.join(session_dir, job["file_name"])
        
        # Update progress
        job["progress"] = 10
        processing_jobs[session_id] = job
        save_job_to_file(session_id, job)
        
        # Check if file exists locally, if not download from blob storage
        if not os.path.exists(file_path) and job.get("blob_name"):
            logger.info(f"Downloading file from blob storage for session {session_id}")
            success = await blob_storage.download_file(job["blob_name"], file_path)
            if not success:
                job["status"] = "error"
                job["error"] = "Failed to download file from blob storage"
                processing_jobs[session_id] = job
                save_job_to_file(session_id, job)
                return
        
        job["progress"] = 20
        processing_jobs[session_id] = job
        save_job_to_file(session_id, job)
        
        # Define progress callback
        def update_progress(progress):
            job["progress"] = progress
            processing_jobs[session_id] = job
            save_job_to_file(session_id, job)
        
        # Generate visualizations with progress callback and user focus
        user_focus = job.get("user_focus", None)
        results = await generate_multiple_visualizations(file_path, session_id, update_progress, user_focus)
        
        # Update job with results
        job["status"] = "completed"
        job["progress"] = 100
        job["results"] = results
        job["completed_at"] = datetime.now().isoformat()
        processing_jobs[session_id] = job
        save_job_to_file(session_id, job)
        
        logger.info(f"Visualization generation completed for session {session_id}")
        
    except Exception as e:
        logger.error(f"Error processing visualization job {session_id}: {str(e)}")
        job = get_job_status(session_id)
        if job:
            job["status"] = "error"
            job["error"] = str(e)
            processing_jobs[session_id] = job
            save_job_to_file(session_id, job)

@app.get("/status/{session_id}")
async def get_processing_status(session_id: str):
    """Get the current processing status of a session."""
    job = get_job_status(session_id)
    if not job:
        return JSONResponse(content={"error": "Session not found"}, status_code=404)
    response = {
        "session_id": session_id,
        "status": job["status"],
        "progress": job["progress"],
        "file_name": job["file_name"],
        "file_size": job["file_size"],
        "created_at": job["created_at"]
    }
    
    if job["status"] == "completed" and "results" in job:
        response["results"] = job["results"]
    elif job["status"] == "error":
        response["error"] = job.get("error", "Unknown error")
    
    return JSONResponse(content=response)

@app.get("/session/{session_id}")
async def get_session_results(session_id: str):
    """Get results for a specific session."""
    # Check job tracking first
    job = get_job_status(session_id)
    if job:
        if job["status"] == "completed" and "results" in job:
            return JSONResponse(content=job["results"])
        elif job["status"] == "processing":
            return JSONResponse(content={"error": "Processing still in progress"}, status_code=202)
        elif job["status"] == "error":
            return JSONResponse(content={"error": job.get("error", "Unknown error")}, status_code=500)
    
    # Fallback to directory scanning for backward compatibility
    session_dir = f"uploads/{session_id}"
    if not os.path.exists(session_dir):
        return JSONResponse(content={"error": "Session not found"}, status_code=404)
    
    try:
        # List all HTML files in the session directory
        html_files = [f for f in os.listdir(session_dir) if f.endswith('.html')]
        
        visualizations = []
        for html_file in html_files:
            viz_name = html_file.replace('.html', '').replace('_', ' ').title()
            visualizations.append({
                "name": viz_name,
                "filename": html_file,
                "path": f"/uploads/{session_id}/{html_file}",
                "status": "success"
            })
        
        return JSONResponse(content={
            "session_id": session_id,
            "visualizations": visualizations
        })
    
    except Exception as e:
        logger.error(f"Error retrieving session {session_id}: {str(e)}")
        return JSONResponse(content={"error": str(e)}, status_code=500)

@app.delete("/session/{session_id}")
async def delete_session(session_id: str):
    """Delete a specific session and all its files."""
    # Delete from blob storage if exists
    job = get_job_status(session_id)
    if job:
        if job.get("blob_name"):
            await blob_storage.delete_file(job["blob_name"])
        # Remove from job tracking
        if session_id in processing_jobs:
            del processing_jobs[session_id]
    
    # Delete local files
    session_dir = f"uploads/{session_id}"
    if os.path.exists(session_dir):
        try:
            shutil.rmtree(session_dir)
            logger.info(f"Session {session_id} deleted successfully")
        except Exception as e:
            logger.error(f"Error deleting local session {session_id}: {str(e)}")
    
    return JSONResponse(content={"message": "Session deleted successfully"})

@app.get("/cleanup")
async def cleanup_old_sessions():
    """Clean up sessions older than configured hours."""
    cleanup_hours = int(os.getenv('SESSION_CLEANUP_HOURS', '24'))
    cutoff_time = datetime.now() - timedelta(hours=cleanup_hours)
    uploads_dir = "uploads"
    
    deleted_count = 0
    blob_deleted_count = 0
    
    try:
        # Clean up blob storage
        if blob_storage.is_enabled():
            blob_deleted_count = await blob_storage.cleanup_old_files(cleanup_hours)
        
        # Clean up local files
        if os.path.exists(uploads_dir):
            for item in os.listdir(uploads_dir):
                item_path = os.path.join(uploads_dir, item)
                if os.path.isdir(item_path):
                    # Check if it's a UUID-like directory (session)
                    try:
                        uuid.UUID(item)
                        # Check creation time
                        creation_time = datetime.fromtimestamp(os.path.getctime(item_path))
                        if creation_time < cutoff_time:
                            shutil.rmtree(item_path)
                            deleted_count += 1
                            logger.info(f"Deleted old session: {item}")
                    except ValueError:
                        # Not a UUID directory, skip
                        continue
        
        # Clean up old job tracking entries
        old_jobs = []
        for session_id, job in processing_jobs.items():
            job_time = datetime.fromisoformat(job["created_at"])
            if job_time < cutoff_time:
                old_jobs.append(session_id)
        
        for session_id in old_jobs:
            del processing_jobs[session_id]
        
        return JSONResponse(content={
            "message": f"Cleanup completed. Deleted {deleted_count} local sessions, {blob_deleted_count} blob files, and {len(old_jobs)} job entries."
        })
    
    except Exception as e:
        logger.error(f"Error during cleanup: {str(e)}")
        return JSONResponse(content={"error": str(e)}, status_code=500)

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "uploads_dir_exists": os.path.exists("uploads"),
        "working_directory": os.getcwd(),
        "python_version": "3.12",
        "blob_storage_enabled": blob_storage.is_enabled(),
        "active_jobs": len(processing_jobs),
        "blob_storage_bucket": blob_storage.bucket_name if blob_storage.is_enabled() else None,
        "configuration": {
            "max_file_size_mb": int(os.getenv('MAX_FILE_SIZE_MB', '1024')),
            "max_direct_processing_size_mb": int(os.getenv('MAX_DIRECT_PROCESSING_SIZE_MB', '100')),
            "session_cleanup_hours": int(os.getenv('SESSION_CLEANUP_HOURS', '24')),
            "log_level": os.getenv('LOG_LEVEL', 'INFO'),
            "google_cloud_project": os.getenv('GOOGLE_CLOUD_PROJECT', 'not-set'),
            "google_cloud_location": os.getenv('GOOGLE_CLOUD_LOCATION', 'not-set')
        }
    }

@app.get("/test")
async def test_endpoint():
    """Simple test endpoint."""
    return {"message": "Test endpoint working!", "app": "data-viz-app"}

@app.get("/data/{session_id}/chunk")
async def get_data_chunk(session_id: str, start: int = 0, limit: int = 1000):
    """Get a chunk of data for a session to load incrementally."""
    try:
        import pandas as pd
        
        job = get_job_status(session_id)
        if not job:
            return JSONResponse(content={"error": "Session not found"}, status_code=404)
        
        session_dir = f"uploads/{session_id}"
        file_path = os.path.join(session_dir, job["file_name"])
        
        # Check if file exists locally, if not download from blob storage
        if not os.path.exists(file_path) and job.get("blob_name"):
            logger.info(f"Downloading file from blob storage for session {session_id}")
            success = await blob_storage.download_file(job["blob_name"], file_path)
            if not success:
                return JSONResponse(content={"error": "Failed to download file"}, status_code=500)
        
        if not os.path.exists(file_path):
            return JSONResponse(content={"error": "Data file not found"}, status_code=404)
        
        # Read the chunk of data
        df = pd.read_csv(file_path, skiprows=range(1, start + 1), nrows=limit)
        
        # Convert to dictionary format
        data_chunk = {}
        for col in df.columns:
            data_chunk[col] = df[col].fillna('').tolist()
        
        # Get total row count for progress tracking
        total_rows = sum(1 for line in open(file_path)) - 1  # -1 for header
        
        return JSONResponse(content={
            "data": data_chunk,
            "start": start,
            "limit": limit,
            "total_rows": total_rows,
            "has_more": (start + limit) < total_rows,
            "chunk_size": len(df)
        })
        
    except Exception as e:
        logger.error(f"Error getting data chunk for session {session_id}: {str(e)}")
        return JSONResponse(content={"error": str(e)}, status_code=500)

@app.get("/data/{session_id}/metadata")
async def get_data_metadata(session_id: str):
    """Get metadata about the dataset for a session."""
    try:
        import pandas as pd
        
        job = get_job_status(session_id)
        if not job:
            return JSONResponse(content={"error": "Session not found"}, status_code=404)
        
        session_dir = f"uploads/{session_id}"
        file_path = os.path.join(session_dir, job["file_name"])
        
        # Check if file exists locally, if not download from blob storage
        if not os.path.exists(file_path) and job.get("blob_name"):
            logger.info(f"Downloading file from blob storage for session {session_id}")
            success = await blob_storage.download_file(job["blob_name"], file_path)
            if not success:
                return JSONResponse(content={"error": "Failed to download file"}, status_code=500)
        
        if not os.path.exists(file_path):
            return JSONResponse(content={"error": "Data file not found"}, status_code=404)
        
        # Read just the first few rows to get metadata
        df_sample = pd.read_csv(file_path, nrows=100)
        total_rows = sum(1 for line in open(file_path)) - 1  # -1 for header
        
        # Get column information
        column_info = {}
        for col in df_sample.columns:
            dtype_str = str(df_sample[col].dtype)
            column_info[col] = {
                "dtype": dtype_str,
                "is_numeric": dtype_str in ['int64', 'float64', 'int32', 'float32'],
                "unique_count": int(df_sample[col].nunique()),
                "null_count": int(df_sample[col].isnull().sum()),
                "sample_values": [str(val) for val in df_sample[col].dropna().head(5).tolist()]
            }
        
        return JSONResponse(content={
            "total_rows": total_rows,
            "total_columns": len(df_sample.columns),
            "columns": list(df_sample.columns),
            "column_info": column_info,
            "dtypes": dict(df_sample.dtypes.astype(str))
        })
        
    except Exception as e:
        logger.error(f"Error getting metadata for session {session_id}: {str(e)}")
        return JSONResponse(content={"error": str(e)}, status_code=500)

@app.get("/test-api")
async def test_api_request():
    """Test API request/response sample."""
    import requests
    import google.auth
    from google.auth.transport.requests import Request
    
    try:
        # Get credentials
        credentials, project = google.auth.default()
        if not credentials.valid:
            credentials.refresh(Request())
        
        project_id = os.environ.get("GOOGLE_CLOUD_PROJECT")
        location = os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1")
        
        url = f"https://{location}-aiplatform.googleapis.com/v1/projects/{project_id}/locations/{location}/publishers/google/models/gemini-2.5-flash:generateContent"
        
        headers = {
            "Authorization": f"Bearer {credentials.token}",
            "Content-Type": "application/json"
        }
        
        # Simple test payload
        test_prompt = """Create a simple HTML page with one Plotly bar chart.

Data: Sales data with columns: Month, Sales
Sample data: January: 100, February: 150, March: 200

Requirements:
- Complete HTML with Plotly CDN
- Dark theme
- One bar chart only
- Keep it simple

Return HTML only."""

        payload = {
            "contents": [{
                "role": "user",
                "parts": [{"text": test_prompt}]
            }],
            "generationConfig": {
                "maxOutputTokens": 8192,
                "temperature": 0.3,
                "topP": 0.95,
                "topK": 10
            }
        }
        
        logger.info(f"TEST API REQUEST:")
        logger.info(f"URL: {url}")
        logger.info(f"Prompt: {test_prompt}")
        logger.info(f"Max tokens: 8192")
        
        response = requests.post(url, json=payload, headers=headers)
        
        logger.info(f"TEST API RESPONSE:")
        logger.info(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            response_data = response.json()
            logger.info(f"Response keys: {list(response_data.keys())}")
            
            if "candidates" in response_data and response_data["candidates"]:
                candidate = response_data["candidates"][0]
                logger.info(f"Finish reason: {candidate.get('finishReason', 'N/A')}")
                
                if "content" in candidate and "parts" in candidate["content"]:
                    total_length = 0
                    for part in candidate["content"]["parts"]:
                        if "text" in part:
                            total_length += len(part["text"])
                    logger.info(f"Generated text length: {total_length} characters")
                    
                    # Return first 500 chars of response
                    sample_text = candidate["content"]["parts"][0]["text"][:500] if candidate["content"]["parts"] else ""
                    
                    return {
                        "status": "success",
                        "response_status": response.status_code,
                        "finish_reason": candidate.get('finishReason', 'N/A'),
                        "text_length": total_length,
                        "sample_text": sample_text,
                        "prompt_length": len(test_prompt)
                    }
        
        return {
            "status": "error",
            "response_status": response.status_code,
            "response_text": response.text[:500]
        }
        
    except Exception as e:
        logger.error(f"Test API error: {str(e)}")
        return {"status": "error", "error": str(e)}

if __name__ == "__main__":
    # Ensure uploads directory exists
    if not os.path.exists("uploads"):
        os.makedirs("uploads")
    
    # Configure logging
    log_level = os.getenv('LOG_LEVEL', 'INFO')
    logging.basicConfig(level=getattr(logging, log_level.upper()))
    
    # Get port from environment variable
    port = int(os.getenv("PORT", "8000"))
    
    logger.info(f"Starting server on port {port}")
    logger.info(f"Blob storage enabled: {blob_storage.is_enabled()}")
    logger.info(f"Blob storage bucket: {blob_storage.bucket_name}")
    
    uvicorn.run(app, host="0.0.0.0", port=port)
