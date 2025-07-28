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
from langchain_community.document_loaders import (
    PyPDFLoader,
    TextLoader,
    UnstructuredURLLoader,
)

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
            data_source: The data to process (e.g., text, file path, URL).
            source_type: The type of the data source (e.g., "text", "pdf",
                "markdown", "url").
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
        elif source_type == "markdown":
            return self._process_markdown(data_source, metadata)
        elif source_type == "url":
            return self._process_url(data_source, metadata)
        # Add other source types here (e.g., "file")
        else:
            raise ValueError(f"Unsupported data source type: {source_type}")

    def _chunk_embed_and_store(
        self,
        text_content: str,
        metadata: Optional[Dict] = None,
        source_description: str = "data",
    ) -> bool:
        """
        Common method to chunk text, create embeddings, and store in ChromaDB.

        Args:
            text_content: The text content to process
            metadata: Optional metadata to associate with the chunks
            source_description: Description for logging purposes

        Returns:
            True if processing was successful, False otherwise
        """
        # 1. Chunk the text
        chunks = self.text_splitter.split_text(text_content)
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

        logger.info(
            f"Successfully processed and stored {len(chunks)} "
            f"{source_description} chunks."
        )
        return True

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
            return self._chunk_embed_and_store(text, metadata, "text")
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

            # 4. Use common method for chunking, embedding, and storing
            return self._chunk_embed_and_store(
                text_content, combined_metadata, f"PDF chunks from {pdf_path}"
            )
        except Exception as e:
            logger.error(f"Error processing PDF file {pdf_path}: {e}", exc_info=True)
            return False

    def _process_markdown(
        self, markdown_path: str, metadata: Optional[Dict] = None
    ) -> bool:
        """
        Process a Markdown file using TextLoader.

        Args:
            markdown_path: Path to the Markdown file to process.
            metadata: Optional metadata to associate with the Markdown content.

        Returns:
            True if processing was successful, False otherwise.
        """
        try:
            # 1. Load Markdown using TextLoader
            loader = TextLoader(markdown_path)
            documents = loader.load()

            if not documents:
                logger.warning("Markdown loading resulted in no documents.")
                return False

            # 2. Extract text content from documents
            text_content = "\n".join([doc.page_content for doc in documents])

            if not text_content.strip():
                logger.warning("Markdown file contains no extractable text content.")
                return False

            # 3. Combine metadata from loader with provided metadata
            combined_metadata = metadata or {}
            if documents:
                # Add metadata from the first document (file info)
                markdown_metadata = documents[0].metadata
                combined_metadata.update(markdown_metadata)

            # 4. Use common method for chunking, embedding, and storing
            return self._chunk_embed_and_store(
                text_content, combined_metadata, f"Markdown chunks from {markdown_path}"
            )
        except Exception as e:
            logger.error(
                f"Error processing Markdown file {markdown_path}: {e}", exc_info=True
            )
            return False

    def _process_url(self, url: str, metadata: Optional[Dict] = None) -> bool:
        """
        Process a web article URL using UnstructuredURLLoader.

        Args:
            url: The URL to fetch and process.
            metadata: Optional metadata to associate with the URL content.

        Returns:
            True if processing was successful, False otherwise.
        """
        try:
            # 1. Load URL content using UnstructuredURLLoader
            loader = UnstructuredURLLoader(urls=[url])
            documents = loader.load()

            if not documents:
                logger.warning("URL loading resulted in no documents.")
                return False

            # 2. Extract text content from documents
            text_content = "\n".join([doc.page_content for doc in documents])

            if not text_content.strip():
                logger.warning("URL contains no extractable text content.")
                return False

            # 3. Combine metadata from loader with provided metadata
            combined_metadata = metadata or {}
            if documents:
                # Add metadata from the first document (URL info)
                url_metadata = documents[0].metadata
                combined_metadata.update(url_metadata)

            # 4. Use common method for chunking, embedding, and storing
            return self._chunk_embed_and_store(
                text_content, combined_metadata, f"URL chunks from {url}"
            )
        except Exception as e:
            logger.error(f"Error processing URL {url}: {e}", exc_info=True)
            return False
