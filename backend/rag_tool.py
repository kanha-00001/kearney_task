import os
import hashlib
import tempfile
from llama_index.core import SimpleDirectoryReader, VectorStoreIndex, Document
from llama_index.core.node_parser import SentenceWindowNodeParser
from llama_index.core.postprocessor import MetadataReplacementPostProcessor, SentenceTransformerRerank
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.llms.groq import Groq
from llama_index.core.settings import Settings
from llama_index.vector_stores.chroma import ChromaVectorStore
import chromadb
from dotenv import load_dotenv
import pandas as pd
import io  # Added for BytesIO

def initialize_llm():
    """Initialize and return the Groq LLM."""
    load_dotenv()
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY not found in .env file")
    os.environ["GROQ_API_KEY"] = api_key
    return Groq(model="openai/gpt-oss-20b", temperature=0.1)

def load_document(file_content, file_name):
    """
    Load a document from file content and return a Document object.
    Modified to handle CSV specifically by converting to markdown table for better RAG.
    
    Args:
        file_content (bytes): Content of the uploaded file.
        file_name (str): Name of the uploaded file.
        
    Returns:
        Document: LlamaIndex Document object.
    """
    if not file_name.lower().endswith('.csv'):
        raise ValueError("Only CSV files are supported for this RAG tool.")
    
    try:
        # Convert bytes to a file-like object for pandas
        df = pd.read_csv(io.BytesIO(file_content))
        markdown_table = df.to_markdown(index=False)
        return Document(text=markdown_table)
    except Exception as e:
        raise ValueError(f"Error processing CSV: {str(e)}")

def build_sentence_window_index(documents, collection_name, sentence_window_size=3):
    """
    Build a sentence window index using Chroma vector store.
    
    Args:
        documents (list): List of Document objects.
        collection_name (str): Name of the Chroma collection.
        sentence_window_size (int): Size of the sentence window.
        
    Returns:
        VectorStoreIndex: LlamaIndex vector store index.
    """
    node_parser = SentenceWindowNodeParser.from_defaults(
        window_size=sentence_window_size,
        window_metadata_key="window",
        original_text_metadata_key="original_text",
    )
    embedding_model = HuggingFaceEmbedding(model_name="BAAI/bge-small-en-v1.5")
    llm = initialize_llm()
    Settings.llm = llm
    Settings.embed_model = embedding_model
    Settings.node_parser = node_parser
    chroma_client = chromadb.PersistentClient(path="./chroma_db")
    chroma_collection = chroma_client.get_or_create_collection(name=collection_name)
    vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
    index = VectorStoreIndex.from_documents(
        documents,
        vector_store=vector_store
    )
    return index

def get_sentence_window_query_engine(index, similarity_top_k=6, rerank_top_n=2):
    """
    Create a query engine for the sentence window index.
    
    Args:
        index (VectorStoreIndex): LlamaIndex vector store index.
        similarity_top_k (int): Number of top similar nodes to retrieve.
        rerank_top_n (int): Number of nodes to rerank.
        
    Returns:
        QueryEngine: LlamaIndex query engine.
    """
    postproc = MetadataReplacementPostProcessor(target_metadata_key="window")
    rerank = SentenceTransformerRerank(
        top_n=rerank_top_n,
        model="BAAI/bge-reranker-base"
    )
    return index.as_query_engine(
        similarity_top_k=similarity_top_k,
        node_postprocessors=[postproc, rerank]
    )

def process_file_and_get_query_engine(file_content, file_name):
    """
    Process an uploaded file and return a query engine.
    
    Args:
        file_content (bytes): Content of the uploaded file.
        file_name (str): Name of the uploaded file.
        
    Returns:
        QueryEngine: LlamaIndex query engine for the file.
    """
    file_hash = hashlib.md5(file_content).hexdigest()
    collection_name = f"doc_{file_hash}"
    document = load_document(file_content, file_name)
    index = build_sentence_window_index([document], collection_name)
    return get_sentence_window_query_engine(index)