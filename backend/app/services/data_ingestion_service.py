"""
Data ingestion service for processing different data sources.

This service orchestrates the processing of various data sources,
including chunking, embedding, and storing the data in ChromaDB.
"""

import logging
from typing import Dict, Optional, Union

from langchain.text_splitter import (
    RecursiveCharacterTextSplitter,
    TextSplitter,
)
from langchain_community.document_loaders import PyPDFLoader

from app.services.chromadb_service import ChromaDBService
from app.services.embedding_service import (
    EmbeddingFactory,
)

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
            source_type: The type of the data source (e.g., "text", "pdf").
            metadata: Optional metadata to associate with the data.

        Returns:
            True if processing was successful, False otherwise.

        Raises:
            ValueError: If the source_type is unsupported.
        """
        logger.info(f"Processing data source of type: {source_type}")
        if source_type == "text":
            return self._process_text(data_source, metadata)
        elif source_type == "pdf":
            return self._process_pdf(data_source, metadata)
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

    def _process_pdf(self, pdf_path: str, metadata: Optional[Dict] = None) -> bool:
        """
        Process a PDF file using PyPDFLoader.

        Args:
            pdf_path: Path to the PDF file to process.
            metadata: Optional metadata to associate with the PDF content.

        Returns:
            True if processing was successful, False otherwise.
        """
        try:
            # 1. Load PDF using PyPDFLoader
            loader = PyPDFLoader(pdf_path)
            documents = loader.load()

            if not documents:
                logger.warning("PDF loading resulted in no documents.")
                return False

            # 2. Extract text content from documents
            text_content = "\n".join([doc.page_content for doc in documents])

            if not text_content.strip():
                logger.warning("PDF contains no extractable text content.")
                return False

            # 3. Combine metadata from loader with provided metadata
            combined_metadata = metadata or {}
            if documents:
                # Add metadata from the first document (file info)
                pdf_metadata = documents[0].metadata
                combined_metadata.update(pdf_metadata)

            # 4. Chunk the text using existing text splitter
            chunks = self.text_splitter.split_text(text_content)
            if not chunks:
                logger.warning("Text splitting resulted in no chunks.")
                return False

            # 5. Create embeddings
            embedding_model = self.embedding_factory.create_embedding_model()
            embeddings = embedding_model.embed_documents(chunks)

            # 6. Store in ChromaDB
            metadatas = [combined_metadata] * len(chunks)
            self.chromadb_service.add_documents(
                collection_name=self.collection_name,
                documents=chunks,
                embeddings=embeddings,
                metadatas=metadatas,
            )

            logger.info(
                f"Successfully processed and stored {len(chunks)} PDF chunks "
                f"from {pdf_path}."
            )
            return True
        except Exception as e:
            logger.error(f"Error processing PDF file {pdf_path}: {e}", exc_info=True)
            return False
