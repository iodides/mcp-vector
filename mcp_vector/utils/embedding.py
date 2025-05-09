"""
Document embedding processing
"""
import os
import logging
import threading
import numpy as np
from typing import Dict, List, Any, Optional, Set
from pathlib import Path
import hashlib
from sentence_transformers import SentenceTransformer

from ..utils.vector_db import VectorDatabase
from ..file_handlers.extractors import extract_file_content
from ..file_handlers.monitor import FileMonitor

logger = logging.getLogger(__name__)

class EmbeddingProcessor:
    """Process documents for embedding and vector search"""
    
    def __init__(self, 
                 model_name: str, 
                 db_path: str,
                 watch_folders: List[str],
                 supported_extensions: Optional[Set[str]] = None):
        """
        Initialize the embedding processor
        
        Args:
            model_name: Name of the sentence-transformers model to use
            db_path: Path to store the vector database
            watch_folders: List of folders to monitor for changes
            supported_extensions: Set of supported file extensions (None for all)
        """
        self.model_name = model_name
        self.db_path = Path(db_path).resolve()
        self.watch_folders = [Path(folder).resolve() for folder in watch_folders]
        
        # Default supported extensions if none provided
        if supported_extensions is None:
            self.supported_extensions = {
                # Text files
                '.txt', '.md', '.log', '.json', '.xml', '.yaml', '.yml',
                # Code files
                '.py', '.js', '.ts', '.java', '.c', '.cpp', '.cs', '.go', '.rb', '.php',
                '.sh', '.html', '.css', '.sql',
                # Office documents
                '.pdf', '.docx', '.xlsx', '.pptx'
            }
        else:
            self.supported_extensions = supported_extensions
        
        # Initialize vector database
        self.vector_db = None
        
        # Initialize embedding model
        self.model = None
        
        # File monitor
        self.file_monitor = None
        
        # Processing lock
        self.lock = threading.RLock()
        
        # Process queue
        self.process_queue = []
        self.queue_lock = threading.RLock()
        self.queue_event = threading.Event()
        self.queue_thread = None
        self.running = False
    
    def initialize(self) -> None:
        """Initialize the embedding processor"""
        logger.info("Initializing embedding processor...")
        
        # Create necessary directories
        self.db_path.mkdir(parents=True, exist_ok=True)
        
        # Load embedding model first to get dimension
        logger.info(f"Loading embedding model: {self.model_name}")
        try:
            self.model = SentenceTransformer(self.model_name)
            self.embedding_dim = self.model.get_sentence_embedding_dimension()
            logger.info(f"Model loaded with embedding dimension: {self.embedding_dim}")
        except Exception as e:
            logger.error(f"Error loading embedding model: {e}")
            raise
        
        # Now load vector database with correct dimension
        logger.info(f"Loading vector database from {self.db_path}")
        try:
            self.vector_db = VectorDatabase(str(self.db_path), embedding_dim=self.embedding_dim)
        except Exception as e:
            logger.error(f"Error loading vector database: {e}")
            raise
        
        # Initialize file monitor
        self.file_monitor = FileMonitor(
            watch_folders=[str(folder) for folder in self.watch_folders],
            on_file_added=self.process_file,
            on_file_modified=self.process_file,
            on_file_deleted=self.delete_file,
            file_extensions=self.supported_extensions
        )
        
        # Start queue processing thread
        self.running = True
        self.queue_thread = threading.Thread(target=self._process_queue_worker, daemon=True)
        self.queue_thread.start()
        
        logger.info("Embedding processor initialized")
        
        # Start queue processing thread
        self.running = True
        self.queue_thread = threading.Thread(target=self._process_queue_worker, daemon=True)
        self.queue_thread.start()
        
        logger.info("Embedding processor initialized")
    
    def start_monitoring(self) -> None:
        """Start file system monitoring"""
        if self.file_monitor:
            self.file_monitor.start()
    
    def stop_monitoring(self) -> None:
        """Stop file system monitoring"""
        if self.file_monitor:
            self.file_monitor.stop()
    
    def _get_content_hash(self, content: str) -> str:
        """Get hash of content to detect changes"""
        return hashlib.md5(content.encode('utf-8')).hexdigest()
    
    def process_file(self, file_path: str) -> None:
        """
        Process a file for embedding
        
        Args:
            file_path: Path to the file
        """
        with self.queue_lock:
            # Add to processing queue
            if file_path not in self.process_queue:
                self.process_queue.append(file_path)
                self.queue_event.set()
    
    def _process_queue_worker(self) -> None:
        """Worker thread for processing queued files"""
        while self.running:
            # Wait for items in the queue
            self.queue_event.wait(timeout=1.0)
            
            # Get next item from queue
            file_path = None
            with self.queue_lock:
                if self.process_queue:
                    file_path = self.process_queue.pop(0)
                
                if not self.process_queue:
                    self.queue_event.clear()
            
            # Process the file
            if file_path:
                try:
                    self._process_file_internal(file_path)
                except Exception as e:
                    logger.error(f"Error processing file {file_path}: {e}")
    
    def _process_file_internal(self, file_path: str) -> None:
        """
        Internal method to process a file for embedding
        
        Args:
            file_path: Path to the file
        """
        file_path = str(Path(file_path).resolve())
        logger.info(f"Processing file: {file_path}")
        
        try:
            # Extract content
            content, metadata = extract_file_content(file_path)
            
            if not content:
                logger.warning(f"No content extracted from file: {file_path}")
                return
            
            # Calculate content hash
            content_hash = self._get_content_hash(content)
            
            # Check if file exists in database with same hash
            existing_docs = self.vector_db.get_document_paths()
            if file_path in existing_docs:
                # Check if we already have this version
                existing_metadata = next((m for i, m in self.vector_db.metadata.items() 
                                         if m['path'] == file_path), {})
                
                if existing_metadata.get('content_hash') == content_hash:
                    logger.info(f"File already processed with same content: {file_path}")
                    return
            
            # Generate embedding
            embedding = self.model.encode(content, show_progress_bar=False)
            
            # Add metadata
            metadata['content_hash'] = content_hash
            metadata['content_length'] = len(content)
            
            # Store in vector database
            self.vector_db.add_document(file_path, embedding, metadata)
            
            # Save database after each update
            self.vector_db.save()
            
            logger.info(f"File processed successfully: {file_path}")
        except Exception as e:
            logger.error(f"Error processing file {file_path}: {e}")
    
    def delete_file(self, file_path: str) -> None:
        """
        Delete a file from the vector database
        
        Args:
            file_path: Path to the file
        """
        file_path = str(Path(file_path).resolve())
        logger.info(f"Deleting file from database: {file_path}")
        
        try:
            # Delete from vector database
            deleted = self.vector_db.delete_document(file_path)
            
            if deleted:
                # Save database after each update
                self.vector_db.save()
                logger.info(f"File deleted from database: {file_path}")
            else:
                logger.info(f"File not found in database: {file_path}")
        except Exception as e:
            logger.error(f"Error deleting file {file_path}: {e}")
    
    def process_all_files(self) -> None:
        """Process all files in watch folders"""
        if not self.file_monitor:
            logger.error("File monitor not initialized")
            return
        
        # Get list of all files
        all_files = self.file_monitor.scan_existing_files()
        
        # Get existing documents in database
        existing_docs = self.vector_db.get_document_paths()
        
        # Add files to queue
        with self.queue_lock:
            for file_path in all_files:
                if file_path not in self.process_queue:
                    self.process_queue.append(file_path)
            
            # Find and delete files that no longer exist
            for doc_path in existing_docs:
                if not os.path.exists(doc_path):
                    self.delete_file(doc_path)
            
            self.queue_event.set()
        
        logger.info(f"Added {len(all_files)} files to processing queue")
    
    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Search for documents matching a query
        
        Args:
            query: Query string
            top_k: Number of results to return
            
        Returns:
            List of matching documents with metadata
        """
        if not self.model or not self.vector_db:
            logger.error("Embedding processor not initialized")
            return []
        
        try:
            # Generate query embedding
            query_embedding = self.model.encode(query, show_progress_bar=False)
            
            # Search vector database
            results = self.vector_db.search(query_embedding, top_k=top_k)
            
            return results
        except Exception as e:
            logger.error(f"Error searching: {e}")
            return []
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get status information
        
        Returns:
            Status information
        """
        status = {
            'model_name': self.model_name,
            'watch_folders': [str(folder) for folder in self.watch_folders],
            'supported_extensions': list(self.supported_extensions),
        }
        
        if self.vector_db:
            status['vector_database'] = self.vector_db.get_status()
        
        if self.model:
            status['embedding_dimension'] = self.embedding_dim
        
        return status
    
    def shutdown(self) -> None:
        """Shutdown the embedding processor"""
        logger.info("Shutting down embedding processor...")
        
        # Stop queue processing
        self.running = False
        if self.queue_thread and self.queue_thread.is_alive():
            self.queue_thread.join(timeout=5.0)
        
        # Stop file monitoring
        self.stop_monitoring()
        
        # Save vector database
        if self.vector_db:
            self.vector_db.save()
        
        logger.info("Embedding processor shut down")
