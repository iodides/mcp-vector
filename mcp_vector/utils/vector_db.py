"""
Vector database management using HNSWLib
"""
import os
import json
import hnswlib
import numpy as np
from typing import Dict, List, Tuple, Optional, Any, Set
from pathlib import Path
import threading
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class VectorDatabase:
    """Vector database for storing and searching document embeddings using HNSWLib"""
    
    def __init__(self, storage_dir: str, embedding_dim: int = 768):
        """
        Initialize the vector database
        
        Args:
            storage_dir: Directory to store vector database files
            embedding_dim: Dimension of the embedding vectors
        """
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        self.index_file = self.storage_dir / "vector_index.bin"
        self.metadata_file = self.storage_dir / "vector_metadata.json"
        
        self.embedding_dim = embedding_dim
        self.index = None
        self.metadata: Dict[int, Dict[str, Any]] = {}
        self.path_to_id: Dict[str, int] = {}
        self.current_id = 0
        self.lock = threading.RLock()
        
        self._load_or_create_index()
    
    def _load_or_create_index(self) -> None:
        """Load existing index or create a new one"""
        with self.lock:
            if self.index_file.exists() and self.metadata_file.exists():
                try:
                    # Load index
                    self.index = hnswlib.Index(space='cosine', dim=self.embedding_dim)
                    self.index.load_index(str(self.index_file), max_elements=100000)
                    
                    # Load metadata
                    with open(self.metadata_file, 'r', encoding='utf-8') as f:
                        loaded_data = json.load(f)
                        self.metadata = {int(k): v for k, v in loaded_data.get('metadata', {}).items()}
                        self.path_to_id = {v['path']: int(k) for k, v in self.metadata.items()}
                        self.current_id = loaded_data.get('current_id', 0)
                    
                    logger.info(f"Loaded vector database with {len(self.metadata)} documents")
                except Exception as e:
                    logger.error(f"Error loading vector database: {e}")
                    self._create_new_index()
            else:
                self._create_new_index()
    
    def _create_new_index(self) -> None:
        """Create a new index"""
        with self.lock:
            self.index = hnswlib.Index(space='cosine', dim=self.embedding_dim)
            self.index.init_index(max_elements=100000, ef_construction=200, M=16)
            self.index.set_ef(50)  # for search
            self.metadata = {}
            self.path_to_id = {}
            self.current_id = 0
            logger.info("Created new vector database")
    
    def save(self) -> None:
        """Save the index and metadata to disk"""
        with self.lock:
            if self.index is not None and len(self.metadata) > 0:
                # Save index
                self.index.save_index(str(self.index_file))
                
                # Save metadata
                with open(self.metadata_file, 'w', encoding='utf-8') as f:
                    json.dump({
                        'metadata': self.metadata,
                        'current_id': self.current_id
                    }, f, ensure_ascii=False, indent=2)
                
                logger.info(f"Saved vector database with {len(self.metadata)} documents")
    
    def add_document(self, path: str, embedding: np.ndarray, metadata: Dict[str, Any]) -> int:
        """
        Add or update a document in the vector database
        
        Args:
            path: Path to the document
            embedding: Document embedding vector
            metadata: Additional metadata for the document
        
        Returns:
            Document ID
        """
        with self.lock:
            # Check if document already exists
            if path in self.path_to_id:
                doc_id = self.path_to_id[path]
                # Update embedding
                self.index.mark_deleted(doc_id)
                self.index.add_items(embedding.reshape(1, -1), np.array([doc_id]))
                # Update metadata
                updated_metadata = {**self.metadata[doc_id], **metadata, 'updated_at': datetime.now().isoformat()}
                self.metadata[doc_id] = updated_metadata
                logger.info(f"Updated document in vector DB: {path}")
                return doc_id
            else:
                # Add new document
                doc_id = self.current_id
                self.current_id += 1
                
                self.index.add_items(embedding.reshape(1, -1), np.array([doc_id]))
                
                # Add metadata
                document_metadata = {
                    'path': path,
                    'created_at': datetime.now().isoformat(),
                    'updated_at': datetime.now().isoformat(),
                    **metadata
                }
                self.metadata[doc_id] = document_metadata
                self.path_to_id[path] = doc_id
                
                logger.info(f"Added document to vector DB: {path}")
                return doc_id
    
    def delete_document(self, path: str) -> bool:
        """
        Delete a document from the vector database
        
        Args:
            path: Path to the document
        
        Returns:
            True if deleted, False if not found
        """
        with self.lock:
            if path in self.path_to_id:
                doc_id = self.path_to_id[path]
                self.index.mark_deleted(doc_id)
                del self.metadata[doc_id]
                del self.path_to_id[path]
                logger.info(f"Deleted document from vector DB: {path}")
                return True
            return False
    
    def search(self, query_embedding: np.ndarray, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Search for similar documents
        
        Args:
            query_embedding: Query embedding vector
            top_k: Number of results to return
        
        Returns:
            List of similar documents with metadata and scores
        """
        with self.lock:
            if self.index is None or len(self.metadata) == 0:
                return []
            
            # Adjust top_k to the actual number of documents
            actual_top_k = min(top_k, len(self.metadata))
            if actual_top_k == 0:
                return []
            
            # Search
            query_vector = query_embedding.reshape(1, -1)
            ids, distances = self.index.knn_query(query_vector, k=actual_top_k)
            
            # Convert distances to similarity scores (cosine)
            scores = 1 - distances[0]
            
            # Get results with metadata
            results = []
            for i, doc_id in enumerate(ids[0]):
                if doc_id in self.metadata:  # Ensure the document exists in metadata
                    result = {
                        'document_id': int(doc_id),
                        'score': float(scores[i]),
                        **self.metadata[doc_id]
                    }
                    results.append(result)
            
            return results
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get database status
        
        Returns:
            Status information
        """
        with self.lock:
            return {
                'document_count': len(self.metadata),
                'embedding_dimension': self.embedding_dim,
                'storage_location': str(self.storage_dir),
                'index_file_exists': self.index_file.exists(),
                'metadata_file_exists': self.metadata_file.exists(),
            }
            
    def get_document_paths(self) -> Set[str]:
        """
        Get all document paths in the database
        
        Returns:
            Set of document paths
        """
        with self.lock:
            return set(self.path_to_id.keys())
