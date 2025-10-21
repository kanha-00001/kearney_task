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
import io

def initialize_llm():
    """Initialize and return the Groq LLM."""
    load_dotenv()
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY not found in .env file")
    os.environ["GROQ_API_KEY"] = api_key
    return Groq(model="openai/gpt-oss-20b", temperature=0.1)

def load_document(file_content, file_name):
    """Load a document from file content and return a Document object."""
    if not file_name.lower().endswith('.csv'):
        raise ValueError("Only CSV files are supported for this RAG tool.")
    
    try:
        df = pd.read_csv(io.BytesIO(file_content))
        markdown_table = df.to_markdown(index=False)
        return Document(text=markdown_table)
    except Exception as e:
        raise ValueError(f"Error processing CSV: {str(e)}")

def build_sentence_window_index(documents, collection_name, sentence_window_size=3):
    """Build a sentence window index using Chroma vector store."""
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

    # MODIFICATION: Use an in-memory ChromaDB client for deployment
    chroma_client = chromadb.Client() 
    
    chroma_collection = chroma_client.get_or_create_collection(name=collection_name)
    vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
    index = VectorStoreIndex.from_documents(
        documents,
        vector_store=vector_store
    )
    return index

def get_sentence_window_query_engine(index, similarity_top_k=6, rerank_top_n=2):
    """Create a query engine for the sentence window index."""
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
    """Process an uploaded file and return a query engine."""
    file_hash = hashlib.md5(file_content).hexdigest()
    collection_name = f"doc_{file_hash}"
    document = load_document(file_content, file_name)
    index = build_sentence_window_index([document], collection_name)
    return get_sentence_window_query_engine(index)

def query_with_history(query_engine, query, chat_history):
    """Queries the engine using context from chat history."""
    if not query_engine:
        return "Error: Query engine not initialized."

    # First, get the context from the vector database based on the user's query
    vector_response = query_engine.query(query)

    # Format the history
    history_context = "\n".join(
        [f"{'User' if msg['sender'] == 'human' else 'AI'}: {msg['text']}" for msg in chat_history]
    )

    # Construct the final prompt for the LLM
    full_prompt = (
        f"You are a helpful data assistant. Use the following retrieved context from the data file and the recent conversation history to answer the user's question.\n\n"
        f"Retrieved Context:\n{vector_response}\n\n"
        f"Recent Conversation:\n{history_context}\n\n"
        f"Based on all of the above, answer this question: {query}"
    )

    llm = Settings.llm
    answer = llm.complete(full_prompt)
    return answer.text

