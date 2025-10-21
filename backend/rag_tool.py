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
    """
    if not file_name.lower().endswith('.csv'):
        raise ValueError("Only CSV files are supported for this RAG tool.")
    
    try:
        df = pd.read_csv(io.BytesIO(file_content))
        markdown_table = df.to_markdown(index=False)
        return Document(text=markdown_table, metadata={"file_name": file_name})
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
    
    # Using an in-memory client for simplicity, can be changed to PersistentClient
    chroma_client = chromadb.Client() 
    chroma_collection = chroma_client.get_or_create_collection(name=collection_name)
    vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
    
    index = VectorStoreIndex.from_documents(
        documents,
        vector_store=vector_store,
        show_progress=True
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

def query_with_history(query_engine, user_query, chat_history):
    """
    Queries the RAG engine, then combines the result with history for a final answer.
    This "hybrid" approach separates data retrieval from conversational context.
    """
    if not query_engine:
        return "Error: Query engine is not initialized."

    # 1. Query the vector store with the user's direct question to get relevant data
    vector_response = query_engine.query(user_query)

    # 2. Format the conversation history
    history_context = "\n".join(
        [f"User: {msg['text']}" if msg['sender'] == 'human' else f"AI: {msg['text']}" for msg in chat_history]
    )

    # 3. Construct a final, detailed prompt for the LLM
    full_prompt = (
        f"You are a helpful AI assistant. Your task is to answer the user's question based on two sources of information:\n"
        f"1. Retrieved Content: This is factual data retrieved from a database that is highly relevant to the user's question.\n"
        f"2. Conversation History: This provides context about the ongoing dialogue.\n\n"
        f"--- RETRIEVED CONTENT ---\n{vector_response}\n\n"
        f"--- CONVERSATION HISTORY ---\n{history_context}\n\n"
        f"--- INSTRUCTION ---\n"
        f"Please synthesize an answer to the following question using the retrieved content and the conversation history. "
        f"Prioritize the 'RETRIEVED CONTENT' for factual accuracy. Use the 'CONVERSATION HISTORY' to understand the context of the question.\n"
        f"User's Question: {user_query}"
    )

    # 4. Call the LLM directly with the rich prompt
    llm = Settings.llm
    final_answer = llm.complete(full_prompt)
    
    return str(final_answer)

