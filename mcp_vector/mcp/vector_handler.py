"""
MCP Implementation for vector search
"""
import os
import json
import logging
import threading
from typing import Dict, List, Any, Optional, Union, Set
from pathlib import Path

from ..utils.embedding import EmbeddingProcessor

logger = logging.getLogger(__name__)

class MCPVectorHandler:
    """MCP Vector handler for Model Context Protocol"""
    
    def __init__(self, 
                 model_name: str,
                 db_path: str,
                 watch_folders: List[str],
                 supported_extensions: Optional[Set[str]] = None):
        """
        Initialize the MCP Vector handler
        
        Args:
            model_name: Name of the sentence-transformers model to use
            db_path: Path to store the vector database
            watch_folders: List of folders to monitor for changes
            supported_extensions: Set of supported file extensions (None for all)
        """
        self.processor = EmbeddingProcessor(
            model_name=model_name,
            db_path=db_path,
            watch_folders=watch_folders,
            supported_extensions=supported_extensions
        )
        
        # Initialize the processor
        self.processor.initialize()
        
        # Start monitoring
        self.processor.start_monitoring()
        
        # Initial processing of existing files
        threading.Thread(target=self.processor.process_all_files, daemon=True).start()
    
    async def vector_search(self, query: str, top_k: int = 5, paths: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        MCP method for vector search
        
        Args:
            query: Query string
            top_k: Number of results to return
            paths: Optional list of specific paths to search within
            
        Returns:
            Search results
        """
        logger.info(f"Vector search: '{query}', top_k={top_k}")
        
        # Perform the search
        results = self.processor.search(query, top_k=top_k)
        
        # Filter by paths if specified
        if paths and results:
            filtered_results = []
            for result in results:
                file_path = result.get('path', '')
                for path in paths:
                    if file_path.startswith(path):
                        filtered_results.append(result)
                        break
            results = filtered_results
        
        # Format the response
        response = {
            'query': query,
            'top_k': top_k,
            'results_count': len(results),
            'results': results
        }
        
        return response
    
    async def vector_status(self) -> Dict[str, Any]:
        """
        MCP method for getting vector database status
        
        Returns:
            Status information
        """
        logger.info("Getting vector status")
        
        # Get status from processor
        status = self.processor.get_status()
        
        return status
    
    async def vector_run(self, paths: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        MCP method for running embedding on all files
        
        Args:
            paths: Optional list of specific paths to process
            
        Returns:
            Status information
        """
        logger.info("Running vector processing for all files")
        
        # Process all files
        threading.Thread(target=self.processor.process_all_files, daemon=True).start()
        
        return {
            'status': 'processing',
            'message': 'Started processing all files in watched folders'
        }
    
    def shutdown(self) -> None:
        """Shutdown the handler"""
        logger.info("Shutting down MCP Vector handler")
        
        # Shutdown the processor
        self.processor.shutdown()
