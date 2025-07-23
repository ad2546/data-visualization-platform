"""
Blob storage utilities for handling large datasets.
"""

import os
import uuid
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from google.cloud import storage
from google.cloud.exceptions import NotFound
import aiofiles
import asyncio

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BlobStorageManager:
    """Manager for handling blob storage operations."""
    
    def __init__(self):
        self.bucket_name = os.getenv('STORAGE_BUCKET_NAME', 'data-viz-uploads')
        self.client = None
        self.bucket = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize the storage client and bucket."""
        try:
            self.client = storage.Client()
            self.bucket = self.client.bucket(self.bucket_name)
            logger.info(f"Initialized blob storage with bucket: {self.bucket_name}")
        except Exception as e:
            logger.error(f"Failed to initialize blob storage: {str(e)}")
            # Fallback to local storage
            self.client = None
            self.bucket = None
    
    def is_enabled(self) -> bool:
        """Check if blob storage is properly configured."""
        return self.client is not None and self.bucket is not None
    
    async def upload_file(self, file_path: str, session_id: str, file_name: str) -> Optional[str]:
        """
        Upload a file to blob storage.
        
        Args:
            file_path: Local path to the file
            session_id: Session identifier
            file_name: Original filename
            
        Returns:
            Blob name if successful, None otherwise
        """
        if not self.is_enabled():
            logger.warning("Blob storage not configured, skipping upload")
            return None
            
        try:
            blob_name = f"{session_id}/{file_name}"
            blob = self.bucket.blob(blob_name)
            
            # Upload file asynchronously
            await asyncio.to_thread(blob.upload_from_filename, file_path)
            
            # Set metadata
            blob.metadata = {
                'session_id': session_id,
                'upload_time': datetime.now().isoformat(),
                'original_filename': file_name
            }
            await asyncio.to_thread(blob.patch)
            
            logger.info(f"Successfully uploaded {file_name} to blob storage as {blob_name}")
            return blob_name
            
        except Exception as e:
            logger.error(f"Failed to upload file to blob storage: {str(e)}")
            return None
    
    async def download_file(self, blob_name: str, local_path: str) -> bool:
        """
        Download a file from blob storage.
        
        Args:
            blob_name: Name of the blob to download
            local_path: Local path to save the file
            
        Returns:
            True if successful, False otherwise
        """
        if not self.is_enabled():
            return False
            
        try:
            blob = self.bucket.blob(blob_name)
            await asyncio.to_thread(blob.download_to_filename, local_path)
            logger.info(f"Successfully downloaded {blob_name} to {local_path}")
            return True
            
        except NotFound:
            logger.error(f"Blob not found: {blob_name}")
            return False
        except Exception as e:
            logger.error(f"Failed to download blob: {str(e)}")
            return False
    
    async def delete_file(self, blob_name: str) -> bool:
        """
        Delete a file from blob storage.
        
        Args:
            blob_name: Name of the blob to delete
            
        Returns:
            True if successful, False otherwise
        """
        if not self.is_enabled():
            return False
            
        try:
            blob = self.bucket.blob(blob_name)
            await asyncio.to_thread(blob.delete)
            logger.info(f"Successfully deleted blob: {blob_name}")
            return True
            
        except NotFound:
            logger.warning(f"Blob not found for deletion: {blob_name}")
            return True  # Consider it successful if already deleted
        except Exception as e:
            logger.error(f"Failed to delete blob: {str(e)}")
            return False
    
    async def cleanup_old_files(self, hours: int = 24) -> int:
        """
        Clean up old files from blob storage.
        
        Args:
            hours: Files older than this many hours will be deleted
            
        Returns:
            Number of files deleted
        """
        if not self.is_enabled():
            return 0
            
        try:
            cutoff_time = datetime.now() - timedelta(hours=hours)
            deleted_count = 0
            
            # List all blobs
            blobs = self.bucket.list_blobs()
            
            for blob in blobs:
                try:
                    # Check if blob is old enough to delete
                    if blob.time_created.replace(tzinfo=None) < cutoff_time:
                        await asyncio.to_thread(blob.delete)
                        deleted_count += 1
                        logger.info(f"Deleted old blob: {blob.name}")
                except Exception as e:
                    logger.error(f"Failed to delete old blob {blob.name}: {str(e)}")
            
            logger.info(f"Cleaned up {deleted_count} old files from blob storage")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Failed to cleanup old files: {str(e)}")
            return 0
    
    async def get_file_info(self, blob_name: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a file in blob storage.
        
        Args:
            blob_name: Name of the blob
            
        Returns:
            File information dict or None if not found
        """
        if not self.is_enabled():
            return None
            
        try:
            blob = self.bucket.blob(blob_name)
            await asyncio.to_thread(blob.reload)
            
            return {
                'name': blob.name,
                'size': blob.size,
                'created': blob.time_created.isoformat() if blob.time_created else None,
                'updated': blob.updated.isoformat() if blob.updated else None,
                'content_type': blob.content_type,
                'metadata': blob.metadata or {}
            }
            
        except NotFound:
            logger.warning(f"Blob not found: {blob_name}")
            return None
        except Exception as e:
            logger.error(f"Failed to get blob info: {str(e)}")
            return None


# Global instance
blob_storage = BlobStorageManager()