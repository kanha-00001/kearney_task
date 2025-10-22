from flask import Flask, request, jsonify
from flask_cors import CORS
from rag_tool import process_file_and_get_query_engine, query_with_history
import os
import logging
from uuid import uuid4
import sqlite3

app = Flask(__name__)

# Set dynamic database path: Render disk for deployment, local path for development
DATABASE = os.environ.get('DATABASE_PATH', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'chat_history.db'))

# Enable CORS for frontend
CORS(app, resources={r"/*": {"origins": "*"}})

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Su
# 
# press TensorFlow warnings
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'

# --- Database Setup ---
def get_db():
    try:
        db = sqlite3.connect(DATABASE, check_same_thread=False)
        db.row_factory = sqlite3.Row
        logger.info(f"Connected to database at: {DATABASE}")
        return db
    except Exception as e:
        logger.error(f"Failed to connect to database at {DATABASE}: {str(e)}", exc_info=True)
        raise

def init_db():
    with app.app_context():
        logger.info("Initializing SQLite database")
        db = get_db()
        cursor = db.cursor()
        try:
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
            logger.info("Database initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize database: {str(e)}", exc_info=True)
            raise
        finally:
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
        logger.info("RAG index built successfully from default CSV")
    except Exception as e:
        logger.error(f"Error processing CSV or building RAG engine: {str(e)}", exc_info=True)

# Initialize DB and load CSV on startup
logger.info("Starting application initialization")
try:
    init_db()
    load_csv_and_build_engine()
except Exception as e:
    logger.error(f"Startup failed: {str(e)}", exc_info=True)
    raise

@app.route('/query', methods=['POST'])
def query_rag_endpoint():
    global query_engine
    if query_engine is None:
        logger.error("Query engine not initialized")
        return jsonify({"error": "Failed to initialize RAG engine. Check server logs."}), 500
    
    data = request.json
    if 'query' not in data:
        logger.warning("No query provided in request")
        return jsonify({"error": "No query provided"}), 400
    
    user_query = data['query']
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
        return jsonify({"response": response_text, "session_id": session_id})
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}", exc_info=True)
        return jsonify({"error": "An error occurred while processing your request."}), 500
    finally:
        db.close()

@app.route('/health', methods=['GET'])
def health_check():
    logger.info("Health check requested")
    return jsonify({"status": "healthy"}), 200

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    logger.info(f"Starting Flask app on port {port}")
    app.run(host="0.0.0.0", port=port, debug=True)