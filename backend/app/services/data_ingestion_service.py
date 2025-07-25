"""
Data ingestion service for processing different data sources.

This service orchestrates the processing of various data sources,
including chunking, embedding, and storing the data in ChromaDB.
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from langchain.text_splitter import RecursiveCharacterTextSplitter, TextSplitter

from app.services.chromadb_service import ChromaDBService
from app.services.embedding_service import EmbeddingFactory

# Configure logger
logger = logging.getLogger(__name__)


class DataIngestionService:
    """
    Service for ingesting data from various sources into ChromaDB.
    """

    def __init__(
        self,
        chromadb_service: ChromaDBService,
        embedding_factory: EmbeddingFactory,
        collection_name: str = "default_collection",
    ):
        """
        Initialize the DataIngestionService.

        Args:
            chromadb_service: Instance of ChromaDBService.
            embedding_factory: Instance of EmbeddingFactory.
            collection_name: Name of the ChromaDB collection to use.
        """
        self.chromadb_service = chromadb_service
        self.embedding_factory = embedding_factory
        self.collection_name = collection_name
        self.text_splitter = self._create_text_splitter()

    def _create_text_splitter(self) -> TextSplitter:
        """
        Create a text splitter for chunking documents.

        Returns:
            An instance of a LangChain TextSplitter.
        """
        return RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
        )

    def process_source(
        self,
        data_source: Union[str, bytes],
        source_type: str,
        metadata: Optional[Dict] = None,
    ) -> bool:
        """
        Process a data source based on its type.

        Args:
            data_source: The data to process (e.g., text, file path).
            source_type: The type of the data source (e.g., "text", "file").
            metadata: Optional metadata to associate with the data.

        Returns:
            True if processing was successful, False otherwise.
        
        Raises:
            ValueError: If the source_type is unsupported.
        """
        logger.info(f"Processing data source of type: {source_type}")
        if source_type == "text":
            return self._process_text(data_source, metadata)
        # Add other source types here (e.g., "file", "url")
        else:
            raise ValueError(f"Unsupported data source type: {source_type}")

    def _process_text(self, text: str, metadata: Optional[Dict] = None) -> bool:
        """
        Process a text data source.

        Args:
            text: The text content to process.
            metadata: Optional metadata to associate with the text.

        Returns:
            True if processing was successful, False otherwise.
        """
        try:
            # 1. Chunk the text
            chunks = self.text_splitter.split_text(text)
            if not chunks:
                logger.warning("Text splitting resulted in no chunks.")
                return False

            # 2. Create embeddings
            embedding_model = self.embedding_factory.create_embedding_model()
            embeddings = embedding_model.embed_documents(chunks)

            # 3. Store in ChromaDB
            metadatas = [metadata or {}] * len(chunks)
            self.chromadb_service.add_documents(
                collection_name=self.collection_name,
                documents=chunks,
                embeddings=embeddings,
                metadatas=metadatas,
            )

            logger.info(f"Successfully processed and stored {len(chunks)} text chunks.")
            return True
        except Exception as e:
            logger.error(f"Error processing text data: {e}", exc_info=True)
            return False

