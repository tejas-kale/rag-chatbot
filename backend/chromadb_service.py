"""
ChromaDB service for the RAG chatbot application.
Provides a clean interface for managing ChromaDB collections with local persistence.
"""

import os
import logging
from typing import List, Optional, Dict, Any, Union
from flask import current_app
import chromadb
from chromadb import Collection
from chromadb.config import Settings

# Configure logger
logger = logging.getLogger(__name__)


class ChromaDBService:
    """
    Service class that encapsulates ChromaDB operations with local persistence.
    
    Provides methods to manage collections and perform vector operations.
    """
    
    def __init__(self):
        """Initialize the ChromaDB service."""
        self._client = None
        self._collections: Dict[str, Collection] = {}
    
    def _get_client(self) -> chromadb.Client:
        """
        Get or create ChromaDB client with persistent storage.
        
        Returns:
            ChromaDB client instance
        """
        if self._client is None:
            persist_path = current_app.config.get('CHROMADB_PERSIST_PATH', 'db/chroma')
            
            # Ensure the persistence directory exists
            os.makedirs(persist_path, exist_ok=True)
            
            try:
                # Create ChromaDB client with persistent storage
                self._client = chromadb.PersistentClient(
                    path=persist_path,
                    settings=Settings(
                        anonymized_telemetry=False,
                        allow_reset=True
                    )
                )
                logger.info(f"ChromaDB client initialized with persistence path: {persist_path}")
            except Exception as e:
                logger.error(f"Failed to initialize ChromaDB client: {e}")
                raise
        
        return self._client
    
    def get_or_create_collection(
        self, 
        name: str, 
        metadata: Optional[Dict[str, Any]] = None,
        embedding_function: Optional[Any] = None
    ) -> Collection:
        """
        Get an existing collection or create a new one.
        
        Args:
            name: Collection name
            metadata: Optional metadata for the collection
            embedding_function: Optional custom embedding function
            
        Returns:
            ChromaDB Collection instance
        """
        if name in self._collections:
            return self._collections[name]
        
        try:
            client = self._get_client()
            
            # Try to get existing collection first
            try:
                collection = client.get_collection(
                    name=name,
                    embedding_function=embedding_function
                )
                logger.info(f"Retrieved existing collection: {name}")
            except Exception:
                # Collection doesn't exist, create it
                collection = client.create_collection(
                    name=name,
                    metadata=metadata or {},
                    embedding_function=embedding_function
                )
                logger.info(f"Created new collection: {name}")
            
            # Cache the collection
            self._collections[name] = collection
            return collection
            
        except Exception as e:
            logger.error(f"Error getting/creating collection '{name}': {e}")
            raise
    
    def list_collections(self) -> List[str]:
        """
        List all collections in the ChromaDB instance.
        
        Returns:
            List of collection names
        """
        try:
            client = self._get_client()
            collections = client.list_collections()
            return [collection.name for collection in collections]
        except Exception as e:
            logger.error(f"Error listing collections: {e}")
            return []
    
    def delete_collection(self, name: str) -> bool:
        """
        Delete a collection by name.
        
        Args:
            name: Collection name to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            client = self._get_client()
            client.delete_collection(name=name)
            
            # Remove from cache if present
            if name in self._collections:
                del self._collections[name]
            
            logger.info(f"Deleted collection: {name}")
            return True
        except Exception as e:
            logger.error(f"Error deleting collection '{name}': {e}")
            return False
    
    def add_documents(
        self,
        collection_name: str,
        documents: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        ids: Optional[List[str]] = None,
        embeddings: Optional[List[List[float]]] = None
    ) -> bool:
        """
        Add documents to a collection.
        
        Args:
            collection_name: Name of the collection
            documents: List of document texts
            metadatas: Optional list of metadata dicts
            ids: Optional list of document IDs
            embeddings: Optional list of embeddings (if not provided, will be computed)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            collection = self.get_or_create_collection(collection_name)
            
            # Generate IDs if not provided
            if ids is None:
                ids = [f"doc_{i}" for i in range(len(documents))]
            
            collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids,
                embeddings=embeddings
            )
            
            logger.info(f"Added {len(documents)} documents to collection '{collection_name}'")
            return True
        except Exception as e:
            logger.error(f"Error adding documents to collection '{collection_name}': {e}")
            return False
    
    def query_documents(
        self,
        collection_name: str,
        query_texts: Union[str, List[str]],
        n_results: int = 10,
        where: Optional[Dict[str, Any]] = None,
        where_document: Optional[Dict[str, Any]] = None,
        include: Optional[List[str]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Query documents from a collection.
        
        Args:
            collection_name: Name of the collection
            query_texts: Query text(s)
            n_results: Number of results to return
            where: Metadata filter conditions
            where_document: Document filter conditions
            include: What to include in results ['metadatas', 'documents', 'distances']
            
        Returns:
            Query results or None if error
        """
        try:
            collection = self.get_or_create_collection(collection_name)
            
            if isinstance(query_texts, str):
                query_texts = [query_texts]
            
            results = collection.query(
                query_texts=query_texts,
                n_results=n_results,
                where=where,
                where_document=where_document,
                include=include or ['metadatas', 'documents', 'distances']
            )
            
            logger.info(f"Queried collection '{collection_name}' with {len(query_texts)} queries")
            return results
        except Exception as e:
            logger.error(f"Error querying collection '{collection_name}': {e}")
            return None
    
    def get_collection_count(self, collection_name: str) -> int:
        """
        Get the number of documents in a collection.
        
        Args:
            collection_name: Name of the collection
            
        Returns:
            Number of documents in the collection, -1 if error
        """
        try:
            collection = self.get_or_create_collection(collection_name)
            return collection.count()
        except Exception as e:
            logger.error(f"Error getting count for collection '{collection_name}': {e}")
            return -1
    
    def reset_client(self) -> bool:
        """
        Reset the ChromaDB client and clear all data.
        Warning: This will delete all collections and data!
        
        Returns:
            True if successful, False otherwise
        """
        try:
            client = self._get_client()
            client.reset()
            
            # Clear cached collections
            self._collections.clear()
            
            logger.warning("ChromaDB client reset - all data deleted!")
            return True
        except Exception as e:
            logger.error(f"Error resetting ChromaDB client: {e}")
            return False


# Global service instance
chromadb_service = ChromaDBService()