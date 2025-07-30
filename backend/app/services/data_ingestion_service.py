"""
Data ingestion service for processing different data sources.

This service orchestrates the processing of various data sources,
including chunking, embedding, and storing the data in ChromaDB.
"""

import logging
import os
import time
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
from app.services.youtube_downloader_service import YouTubeDownloaderService
from app.services.whisper_transcription_service import WhisperTranscriptionService
from app.services.text_correction_service import TextCorrectionService
from app.services.persistence_service import PersistenceManager

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
        youtube_download_dir: str = "downloads/audio",
        whisper_executable: str = "whisper",
        whisper_model: str = "base",
    ):
        """
        Initialize the DataIngestionService.

        Args:
            chromadb_service: Instance of ChromaDBService.
            embedding_factory: Instance of EmbeddingFactory.
            collection_name: Name of the ChromaDB collection to use.
            youtube_download_dir: Directory for YouTube audio downloads.
            whisper_executable: Path to whisper.cpp executable.
            whisper_model: Default whisper model for transcription.
        """
        self.chromadb_service = chromadb_service
        self.embedding_factory = embedding_factory
        self.collection_name = collection_name
        self.text_splitter = self._create_text_splitter()
        self.youtube_downloader = YouTubeDownloaderService(youtube_download_dir)
        self.whisper_service = WhisperTranscriptionService(
            whisper_executable=whisper_executable,
            default_model=whisper_model,
        )
        self.text_correction_service = TextCorrectionService()
        self.persistence_manager = PersistenceManager()

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
                "markdown", "url", "youtube").
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
        elif source_type == "youtube":
            return self._process_youtube(data_source, metadata)
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

    def _process_youtube(
        self, youtube_url: str, metadata: Optional[Dict] = None
    ) -> bool:
        """
        Process a YouTube URL by downloading audio and transcribing it.

        This method downloads the audio file and uses whisper.cpp to
        transcribe the audio content for embedding and storage.
        Additionally, it saves the transcription data to the database.

        Args:
            youtube_url: The YouTube URL to process.
            metadata: Optional metadata to associate with the YouTube content.

        Returns:
            True if processing was successful, False otherwise.
        """
        transcription_record = None

        try:
            # 1. Validate YouTube URL
            if not self.youtube_downloader.is_youtube_url(youtube_url):
                logger.error(f"Invalid YouTube URL: {youtube_url}")
                return False

            # 2. Create initial transcription record in database
            # (if Flask context available)
            try:
                transcription_record = self.persistence_manager.create_transcription(
                    youtube_url=youtube_url, user_settings_id=1  # Default user for now
                )
                if transcription_record:
                    logger.info(
                        f"Created transcription record ID: {transcription_record.id}"
                    )
                else:
                    logger.warning(
                        "Failed to create transcription record - "
                        "continuing without database storage"
                    )

            except Exception as e:
                logger.warning(
                    f"Database error creating transcription record "
                    f"(continuing without DB): {e}"
                )
                transcription_record = None

            # 3. Download audio file
            downloaded_file_path = self.youtube_downloader.download_audio(youtube_url)
            if not downloaded_file_path:
                logger.error(f"Failed to download audio from: {youtube_url}")
                # Update transcription record with error status (if available)
                if transcription_record:
                    self.persistence_manager.update_transcription(
                        transcription_record.id,
                        status="error",
                        error_message="Failed to download audio from YouTube",
                    )
                return False

            logger.info(f"Audio file downloaded: {downloaded_file_path}")

            # 4. Update transcription record with file info (if available)
            if transcription_record:
                try:
                    filename = os.path.basename(downloaded_file_path)

                    self.persistence_manager.update_transcription(
                        transcription_record.id,
                        original_filename=filename,
                        status="processing",
                    )
                except Exception as e:
                    logger.warning(
                        f"Could not update file info in transcription record: {e}"
                    )

            # 5. Transcribe audio using whisper.cpp
            raw_transcription = None
            corrected_transcription = None
            transcription_start_time = None

            try:
                transcription_start_time = time.time()

                raw_transcription = self.whisper_service.transcribe_audio(
                    downloaded_file_path
                )

                processing_duration = time.time() - transcription_start_time

                if raw_transcription:
                    char_count = len(raw_transcription)
                    logger.info(
                        f"YouTube audio transcription completed: "
                        f"{char_count} characters in {processing_duration:.2f}s"
                    )

                    # 6. Apply text correction to raw transcription
                    try:
                        corrected_transcription = (
                            self.text_correction_service.correct_transcription(
                                raw_transcription
                            )
                        )
                        logger.info("Text correction applied successfully")
                    except Exception as e:
                        logger.warning(
                            f"Text correction failed, using raw transcription: {e}"
                        )
                        corrected_transcription = raw_transcription

                    # 7. Update transcription record with results (if available)
                    if transcription_record:
                        self.persistence_manager.update_transcription(
                            transcription_record.id,
                            transcription_text=raw_transcription,
                            corrected_text=corrected_transcription,
                            transcription_engine="whisper",
                            processing_duration=processing_duration,
                            status="completed",
                        )
                else:
                    logger.warning("Transcription returned no text")
                    if transcription_record:
                        self.persistence_manager.update_transcription(
                            transcription_record.id,
                            status="error",
                            error_message="Transcription returned no text",
                            transcription_engine="whisper",
                            processing_duration=(
                                processing_duration
                                if transcription_start_time
                                else None
                            ),
                        )

            except Exception as e:
                logger.error(f"Audio transcription failed: {e}")
                processing_duration = (
                    (time.time() - transcription_start_time)
                    if transcription_start_time
                    else None
                )
                if transcription_record:
                    self.persistence_manager.update_transcription(
                        transcription_record.id,
                        status="error",
                        error_message=f"Transcription failed: {str(e)}",
                        transcription_engine="whisper",
                        processing_duration=processing_duration,
                    )
                # Continue with processing even if transcription fails
                raw_transcription = None

            # 8. Create metadata for the YouTube video
            combined_metadata = metadata or {}
            combined_metadata.update(
                {
                    "source_type": "youtube",
                    "youtube_url": youtube_url,
                    "audio_file_path": downloaded_file_path,
                    "content_type": "audio/mp3",
                    "transcription_available": raw_transcription is not None,
                    "transcription_record_id": (
                        transcription_record.id if transcription_record else None
                    ),
                }
            )

            # 9. Prepare text content for embedding
            if corrected_transcription or raw_transcription:
                # Use corrected text for embeddings if available, otherwise raw
                text_content = corrected_transcription or raw_transcription
            else:
                # Fallback to URL only if transcription fails
                text_content = f"YouTube video: {youtube_url}"
                logger.warning("Using URL only as no transcription was available")

            # 10. Use common method for chunking, embedding, and storing
            success = self._chunk_embed_and_store(
                text_content, combined_metadata, f"YouTube content from {youtube_url}"
            )

            # 11. Clean up audio file after processing
            try:
                if self.youtube_downloader.cleanup_file(downloaded_file_path):
                    logger.info(f"Cleaned up audio file: {downloaded_file_path}")
            except Exception as e:
                logger.warning(f"Failed to clean up audio file: {e}")

            if success:
                logger.info(f"Successfully processed YouTube URL: {youtube_url}")
                if raw_transcription:
                    logger.info("Content includes audio transcription")
                    if transcription_record:
                        logger.info(
                            f"Transcription stored in database with record ID: "
                            f"{transcription_record.id}"
                        )

            return success

        except Exception as e:
            logger.error(
                f"Error processing YouTube URL {youtube_url}: {e}", exc_info=True
            )
            # Update transcription record with error if it exists
            if transcription_record:
                try:
                    self.persistence_manager.update_transcription(
                        transcription_record.id,
                        status="error",
                        error_message=f"Processing failed: {str(e)}",
                    )
                except Exception as db_error:
                    logger.error(
                        f"Failed to update transcription record with error: {db_error}"
                    )
            return False
