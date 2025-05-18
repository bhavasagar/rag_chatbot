import os
import glob
import logging
from typing import List

from langchain_community.document_loaders import (
    TextLoader,
    PDFMinerLoader,
    UnstructuredMarkdownLoader,
)
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

from .embeddings import get_embedding_model
from .vector_store import VectorStore

logger = logging.getLogger(__name__)

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
DOCUMENTS_DIR = os.path.join(DATA_DIR, "documents")
EMBEDDINGS_DIR = os.path.join(DATA_DIR, "embeddings")

os.makedirs(DOCUMENTS_DIR, exist_ok=True)
os.makedirs(EMBEDDINGS_DIR, exist_ok=True)


class DocumentLoader:
    """Class for loading, processing, and embedding documents."""

    def __init__(self):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
        )
        self.url = "https://www.angelone.in/support"
        self.embedding_model = get_embedding_model()
        self.vector_store = VectorStore()

    def load_documents(self) -> List[Document]:
        """Load documents from the documents directory."""
        documents = []

        file_paths = []
        for ext in ["*.txt", "*.pdf", "*.md"]:
            file_paths.extend(
                glob.glob(os.path.join(DOCUMENTS_DIR, "**", ext), recursive=True)
            )

        logger.info(f"Found {len(file_paths)} documents")

        for file_path in file_paths:
            try:
                if file_path.endswith(".txt"):
                    loader = TextLoader(file_path, encoding="utf-8")
                elif file_path.endswith(".pdf"):
                    loader = PDFMinerLoader(file_path)
                elif file_path.endswith(".md"):
                    loader = UnstructuredMarkdownLoader(file_path)
                else:
                    logger.warning(f"Unsupported file format: {file_path}")
                    continue

                docs = loader.load()
                documents.extend(docs)
                logger.info(f"Loaded {len(docs)} documents from {file_path}")
            except Exception as e:
                logger.error(f"Error loading {file_path}: {e}")

        return documents

    def split_documents(self, documents: List[Document]) -> List[Document]:
        """Split documents into chunks."""
        return self.text_splitter.split_documents(documents)

    def process_and_embed(self):
        """Process documents, split them, and create embeddings."""
        documents = self.load_documents()
        if not documents:
            logger.warning("No documents found to process")
            return

        chunks = self.split_documents(documents)
        logger.info(f"Split documents into {len(chunks)} chunks")

        self.vector_store.add_documents(chunks)
        logger.info("Documents processed and stored in vector database")


def main():
    logging.basicConfig(level=logging.INFO)
    processor = DocumentLoader()
    processor.process_and_embed()


if __name__ == "__main__":
    main()
