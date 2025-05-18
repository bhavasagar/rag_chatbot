import os
import glob
import logging
from typing import List

from bs4 import BeautifulSoup
from langchain_community.document_loaders import (
    TextLoader,
    PDFMinerLoader,
    UnstructuredMarkdownLoader,
)
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import WebBaseLoader
from langchain_core.documents import Document
import requests

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

        chunks = self.split_documents(documents) + self.process_all_sources(self.url)
        logger.info(f"Split documents into {len(chunks)} chunks")

        self.vector_store.add_documents(chunks)
        logger.info("Documents processed and stored in vector database")

    def extract_content(self, url):
        """Extract all text content from the web page"""
        loader = WebBaseLoader(url)
        documents = loader.load()
        return documents

    def extract_sources(self, url):
        """Extract all links/sources from the web page"""
        response = requests.get(url)
        soup = BeautifulSoup(response.text, "html.parser")

        links = []
        for a_tag in soup.find_all("a", href=True):
            href = a_tag["href"]
            if href.startswith("/"):
                base_url = "/".join(url.split("/")[:3])
                href = base_url + href
            elif not href.startswith(("http://", "https://")):
                href = url + ("/" if not url.endswith("/") else "") + href

            if href.startswith(("http://", "https://")):
                links.append(href)

        return list(set(links))

    def process_all_sources(self, url, max_depth=2, visited=None):
        """Process the main page and all linked sources up to max_depth"""
        if visited is None:
            visited = set()

        if max_depth < 0 or url in visited:
            return []

        urls_list = [url]
        new_urls_list = []
        chunks = []

        while urls_list and max_depth > 0:
            url = urls_list.pop()
            if url in visited:
                continue

            visited.add(url)
            logger.info(f"Processing URL: {url}")
            try:
                documents = self.extract_content(url)
                chunks += self.split_documents(documents)
                if max_depth > 0:
                    sources = self.extract_sources(url)
                    new_urls_list += sources
            except:
                continue

            if len(urls_list) == 0:
                urls_list = new_urls_list
                new_urls_list = []
                max_depth -= 1

        return chunks


def main():
    logging.basicConfig(level=logging.INFO)
    processor = DocumentLoader()
    processor.process_and_embed()


if __name__ == "__main__":
    main()
