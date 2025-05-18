import os
from os.path import join, dirname
from typing import List, Dict, Any, Tuple

from dotenv import load_dotenv
from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from langchain_anthropic import ChatAnthropic
from langchain.retrievers import ContextualCompressionRetriever
from langchain.retrievers.document_compressors import LLMChainExtractor

from .vector_store import VectorStore


dotenv_path = join(dirname(__file__), "..", ".env")
load_dotenv(dotenv_path)


class RAGRetriever:

    def __init__(self):
        self.vector_store = VectorStore()
        self.llm = ChatAnthropic(
            model_name="claude-3-5-sonnet-20241022",
            api_key=os.environ.get("LLM_API_KEY"),
        )
        base_retriever = self.vector_store.get_retriever({"k": 5})
        compressor = LLMChainExtractor.from_llm(self.llm)
        self.retriever = ContextualCompressionRetriever(
            base_compressor=compressor, base_retriever=base_retriever
        )
        self.response_prompt = ChatPromptTemplate.from_template(
            """
            You are a customer support assistant that helps users with their questions. PHRASE THE RESPONSE in a format of 
            a customer support person is responding to the user query.
            You should only answer based on the provided context. If the answer is not in the context,
            respond with "I don't know" - never make up an answer. DO NOT INCLUDE terms like "Based on the context".
            
            Context information is below:
            ---------------------
            {context}
            ---------------------
            
            Given the context information and not prior knowledge, answer the question: {question}
            """
        )
        self.chain = self.response_prompt | self.llm | StrOutputParser()

    def retrieve_documents(self, query: str) -> List[Document]:
        try:
            return self.retriever.invoke(query)
        except Exception as e:
            print(f"Error retrieving documents: {e}")
            return []

    def generate_response(self, query: str) -> Tuple[str, List[Document]]:
        relevant_docs = self.retrieve_documents(query)
        if not relevant_docs:
            return "I don't know.", []

        context = "\n\n".join([doc.page_content for doc in relevant_docs])
        response = self.chain.invoke({"context": context, "question": query})
        return response, relevant_docs

    def get_sources(self, docs: List[Document]) -> List[Dict[str, Any]]:
        sources = []
        for doc in docs:
            source = {
                "content": (
                    doc.page_content[:200] + "..."
                    if len(doc.page_content) > 200
                    else doc.page_content
                ),
                "metadata": doc.metadata,
            }
            sources.append(source)
        return sources
