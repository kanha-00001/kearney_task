from flask import Flask, request, jsonify
from flask_cors import CORS
from rag_tool import process_file_and_get_query_engine, query_with_history
import os
import logging
from uuid import uuid4
import sqlite3
import datetime

app = Flask(__name__)
# MODIFICATION: secret_key is no longer needed for stateless session handling
DATABASE = 'chat_history.db'

# MODIFICATION: credentials are no longer needed
CORS(app, resources={r"/*": {"origins": "http://localhost:5173"}})

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Database Setup ---
def get_db():
    db = sqlite3.connect(DATABASE, check_same_thread=False) # check_same_thread added for safety
    db.row_factory = sqlite3.Row
    return db

def init_db():
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        cursor.execute(
            '''
            CREATE TABLE IF NOT EXISTS chat_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                sender TEXT NOT NULL,
                text TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            '''
        )
        db.commit()
        logger.info("Database initialized.")
        db.close()

# --- RAG Engine Setup ---
query_engine = None

def load_csv_and_build_engine():
    global query_engine
    base_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(base_dir, '..', 'assets', 'Sugar_Spend_Data.csv')
    
    logger.info(f"Attempting to load CSV from: {csv_path}")
    if not os.path.exists(csv_path):
        logger.error(f"FATAL: CSV file not found at {csv_path}")
        return
    
    try:
        with open(csv_path, 'rb') as f:
            file_content = f.read()
        query_engine = process_file_and_get_query_engine(file_content, 'Sugar_Spend_Data.csv')
        logger.info("RAG index built successfully from default CSV.")
    except Exception as e:
        logger.error(f"Error processing CSV or building RAG engine: {str(e)}", exc_info=True)

# Initialize DB and load CSV on startup
init_db()
load_csv_and_build_engine()

@app.route('/query', methods=['POST'])
def query_rag_endpoint():
    global query_engine
    if query_engine is None:
        logger.error("Query engine not initialized")
        return jsonify({"error": "Failed to initialize RAG engine. Check server logs."}), 500
    
    data = request.json
    if 'query' not in data:
        return jsonify({"error": "No query provided"}), 400
    
    user_query = data['query']
    # MODIFICATION: Get session_id from the request body, not Flask's session
    session_id = data.get('session_id') or str(uuid4())
    
    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute(
            "SELECT sender, text FROM chat_history WHERE session_id = ? ORDER BY timestamp DESC LIMIT 3",
            (session_id,)
        )
        history_rows = cursor.fetchall()
        history_rows.reverse()
        
        chat_history_list = [dict(row) for row in history_rows]

        response_text = query_with_history(query_engine, user_query, chat_history_list)
        
        cursor.execute(
            "INSERT INTO chat_history (session_id, sender, text) VALUES (?, ?, ?)",
            (session_id, 'human', user_query)
        )
        cursor.execute(
            "INSERT INTO chat_history (session_id, sender, text) VALUES (?, ?, ?)",
            (session_id, 'ai', response_text)
        )
        db.commit()
        
        logger.info(f"Successfully processed query for session {session_id}")
        # MODIFICATION: Always return the session_id in the response
        return jsonify({"response": response_text, "session_id": session_id})
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}", exc_info=True)
        return jsonify({"error": "An error occurred while processing your request."}), 500
    finally:
        db.close()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

