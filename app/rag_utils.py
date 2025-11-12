import os
from langchain_community.vectorstores import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings

CHROMA_PATH = "./chroma_db"

def create_rag_vectorstore(code_texts: list):
    """Create embeddings for repo code files."""
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1200, chunk_overlap=200)
    docs = [Document(page_content=t) for t in code_texts]
    split_docs = text_splitter.split_documents(docs)

    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    vectordb = Chroma.from_documents(split_docs, embeddings, persist_directory=CHROMA_PATH)
    # vectordb.persist()
    return vectordb

def load_rag_vectorstore():
    """Load existing vector DB."""
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    return Chroma(persist_directory=CHROMA_PATH, embedding_function=embeddings)

def retrieve_rag_context(vectordb, query: str, k: int = 5):
    """Retrieve top-k relevant chunks from vectorstore."""
    results = vectordb.similarity_search(query, k=k)
    return "\n\n".join([r.page_content for r in results])