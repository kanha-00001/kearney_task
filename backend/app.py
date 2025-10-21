from flask import Flask, request, jsonify, session
from flask_cors import CORS
from rag_tool import process_file_and_get_query_engine
import os
import logging
from uuid import uuid4  # For session IDs

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Required for session management

# Enable CORS for frontend
CORS(app, resources={r"/query": {"origins": "http://localhost:5173"}}, supports_credentials=True)

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Initialize query engine
query_engine = None

# Store chat history per session
chat_history = {}

def load_csv_and_build_engine():
    """Load CSV and build RAG query engine."""
    global query_engine
    csv_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'assets', 'Sugar_Spend_Data.csv'))
    
    logger.debug(f"Attempting to load CSV from: {csv_path}")
    
    if not os.path.exists(csv_path):
        logger.error(f"CSV file not found at {csv_path}")
        return
    
    try:
        with open(csv_path, 'rb') as file:
            file_content = file.read()
        file_name = 'Sugar_Spend_Data.csv'
        
        logger.debug("CSV file read successfully")
        query_engine = process_file_and_get_query_engine(file_content, file_name)
        logger.info("RAG index built successfully")
    except Exception as e:
        logger.error(f"Error processing CSV or building RAG engine: {str(e)}", exc_info=True)

# Load CSV on startup
load_csv_and_build_engine()

@app.route('/query', methods=['POST'])
def query_rag():
    global query_engine, chat_history
    if query_engine is None:
        logger.error("Query engine not initialized")
        return jsonify({"error": "Failed to initialize RAG engine. Check server logs for details."}), 500
    
    data = request.json
    if 'query' not in data:
        logger.warning("No query provided in request")
        return jsonify({"error": "No query provided"}), 400
    
    user_query = data['query']
    
    # Get or create session ID
    session_id = session.get('session_id')
    if not session_id:
        session_id = str(uuid4())
        session['session_id'] = session_id
        chat_history[session_id] = []
    
    # Prepare context from recent history (last 3 messages)
    history_context = "\n".join(
        [f"{'User' if msg['sender'] == 'human' else 'AI'}: {msg['text']}" 
         for msg in chat_history[session_id][-3:]]
    )
    full_query = f"Context from previous conversation:\n{history_context}\n\nCurrent query: {user_query}" if history_context else user_query
    
    try:
        logger.debug(f"Processing query: {user_query} with session ID: {session_id}")
        response = query_engine.query(full_query)
        response_text = str(response)
        
        # Update chat history
        chat_history[session_id].append({"sender": "human", "text": user_query})
        chat_history[session_id].append({"sender": "ai", "text": response_text})
        
        logger.info("Query processed successfully")
        return jsonify({"response": response_text, "session_id": session_id})
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)