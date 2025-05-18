import os
from typing import List, Optional, Dict, Any

from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_core.vectorstores import VectorStoreRetriever

from .embeddings import get_embedding_model


DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
FAISS_INDEX_PATH = os.path.join(DATA_DIR, "embeddings", "faiss_index")


class VectorStore:

    def __init__(self):
        self.embedding_model = get_embedding_model()
        self._vector_store = None

    @property
    def vector_store(self) -> Optional[FAISS]:
        if self._vector_store is None:
            self._load_vector_store()
        return self._vector_store

    def _load_vector_store(self) -> None:
        if os.path.exists(FAISS_INDEX_PATH):
            try:
                self._vector_store = FAISS.load_local(
                    FAISS_INDEX_PATH,
                    self.embedding_model,
                    allow_dangerous_deserialization=True,
                )
            except Exception as e:
                print(f"Error loading vector store: {e}")
                self._vector_store = None

    def add_documents(self, documents: List[Document]) -> None:
        if not documents:
            return

        if self._vector_store is None:
            self._vector_store = FAISS.from_documents(documents, self.embedding_model)
        else:
            self._vector_store.add_documents(documents)

        self._save_vector_store()

    def _save_vector_store(self) -> None:
        if self._vector_store is None:
            return

        os.makedirs(os.path.dirname(FAISS_INDEX_PATH), exist_ok=True)
        self._vector_store.save_local(FAISS_INDEX_PATH)

    def get_retriever(
        self, search_kwargs: Dict[str, Any] = None
    ) -> VectorStoreRetriever:
        if self.vector_store is None:
            raise ValueError("Vector store is not initialized")

        if search_kwargs is None:
            search_kwargs = {"k": 4}

        return self.vector_store.as_retriever(
            search_type="similarity", search_kwargs=search_kwargs
        )

    def similarity_search(self, query: str, k: int = 4) -> List[Document]:
        if self.vector_store is None:
            return []

        return self.vector_store.similarity_search(query, k=k)
